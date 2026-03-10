import uuid

from django.db import models
from django.utils import timezone
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import StreamField
from wagtail.models import PreviewableMixin, RevisionMixin

from .blocks import NewsletterStreamBlock
from .pages import NewsletterSignupPage  # noqa: F401 - Required for migration discovery


class CampaignSource(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Traffic source (e.g., 'Instagram', 'Poster', 'Email').")

    panels = [FieldPanel("name")]

    class Meta:
        ordering = ["name"]
        verbose_name = "Campaign Source"
        verbose_name_plural = "Campaign Sources"

    def __str__(self):
        return self.name


class CampaignMedium(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Marketing medium (e.g., 'Social', 'Print', 'Email', 'Referral').")

    panels = [FieldPanel("name")]

    class Meta:
        ordering = ["name"]
        verbose_name = "Campaign Medium"
        verbose_name_plural = "Campaign Media"

    def __str__(self):
        return self.name


class SubscriberTag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    panels = [
        FieldPanel("name"),
        FieldPanel("description"),
    ]

    class Meta:
        ordering = ["name"]
        verbose_name = "Subscriber Tag"
        verbose_name_plural = "Subscriber Tags"

    def __str__(self):
        return self.name


class SubscriberTagThrough(models.Model):
    subscriber = models.ForeignKey("newsletter.Subscriber", on_delete=models.CASCADE)
    tag = models.ForeignKey(SubscriberTag, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("subscriber", "tag")]
        verbose_name = "Subscriber Tag Assignment"
        verbose_name_plural = "Subscriber Tag Assignments"

    def __str__(self):
        return f"{self.subscriber.email} → {self.tag.name}"


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    confirmed = models.BooleanField(default=False, db_index=True)
    confirmation_token = models.UUIDField(default=uuid.uuid4, unique=True)
    unsubscribe_token = models.UUIDField(default=uuid.uuid4, unique=True)
    signup_page = models.ForeignKey(
        "newsletter.NewsletterSignupPage", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="newsletter_subscribers",
    )
    tags = models.ManyToManyField(
        SubscriberTag, blank=True, through=SubscriberTagThrough,
        related_name="subscribers",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True, db_index=True)
    bounce_count = models.PositiveIntegerField(default=0, db_index=True)
    last_bounced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        status = "confirmed" if self.confirmed else "pending"
        if self.unsubscribed_at:
            status = "unsubscribed"
        return f"{self.email} ({status})"

    @property
    def is_suppressed(self):
        return self.bounce_count >= 3

    @property
    def is_active(self):
        return self.confirmed and self.unsubscribed_at is None and not self.is_suppressed

    def record_bounce(self):
        self.bounce_count += 1
        self.last_bounced_at = timezone.now()
        self.save(update_fields=["bounce_count", "last_bounced_at"])

    def clear_bounces(self):
        self.bounce_count = 0
        self.last_bounced_at = None
        self.save(update_fields=["bounce_count", "last_bounced_at"])

    def confirm(self):
        self.confirmed = True
        self.confirmed_at = timezone.now()
        self.save(update_fields=["confirmed", "confirmed_at"])

    def unsubscribe(self):
        self.unsubscribed_at = timezone.now()
        self.save(update_fields=["unsubscribed_at"])


class Newsletter(PreviewableMixin, RevisionMixin, models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SENT = "sent", "Sent"

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    subject = models.CharField(
        max_length=255,
        help_text="Email subject line. Defaults to title if blank.",
        blank=True,
    )
    preheader = models.CharField(
        max_length=255,
        blank=True,
        help_text="Preview text shown in email clients before opening.",
    )
    body = StreamField(NewsletterStreamBlock(), blank=True)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    # Targeting fields — if none set, sends to all (backwards compatible)
    target_tags = models.ManyToManyField(
        SubscriberTag, blank=True, related_name="newsletters",
        help_text="If set, only subscribers with ANY of these tags receive this newsletter.",
    )
    panels = [
        FieldPanel("title"),
        FieldPanel("slug"),
        FieldPanel("subject"),
        FieldPanel("preheader"),
        FieldPanel("body"),
        MultiFieldPanel(
            [
                FieldPanel("target_tags"),
            ],
            heading="Targeting",
            help_text="Optional filters to target specific subscribers. If no targets are set, the newsletter is sent to all active subscribers.",
        ),
        FieldPanel("status"),
    ]

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    @property
    def targeting_summary(self):
        tag_names = [t.name for t in self.target_tags.all()]
        return ", ".join(tag_names) if tag_names else ""

    @property
    def effective_subject(self):
        return self.subject or self.title

    @property
    def template_path(self):
        return f"newsletter/editions/{self.slug}.html"

    def _get_dummy_headers(self, original_request=None):
        headers = super()._get_dummy_headers(original_request)
        # Wagtail's dummy request omits QUERY_STRING, which querycount middleware requires
        headers.setdefault("QUERY_STRING", "")
        return headers

    def get_preview_template(self, request, mode_name):
        return "newsletter/preview.html"

    def get_preview_context(self, request, mode_name):
        return {
            "newsletter": self,
            "unsubscribe_url": "#",
            "preferences_url": "#",
            "preview_mode": True,
        }


@register_setting(icon="mail")
class NewsletterEmailSettings(BaseSiteSetting):
    confirmation_subject = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Subject line for the subscription confirmation email.",
    )
    confirmation_heading = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Heading shown in the confirmation email.",
    )
    confirmation_body = models.TextField(
        blank=True,
        default="",
        help_text="Body text for the confirmation email. Use {email} for the subscriber's address.",
    )
    confirmation_button_text = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Button text in the confirmation email.",
    )

    unsubscribe_subject = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Subject line for the unsubscribe confirmation email.",
    )
    unsubscribe_heading = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Heading shown in the unsubscribe email.",
    )
    unsubscribe_body = models.TextField(
        blank=True,
        default="",
        help_text="Body text for the unsubscribe email. Use {email} for the subscriber's address.",
    )
    unsubscribe_button_text = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Button text in the unsubscribe email.",
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("confirmation_subject"),
                FieldPanel("confirmation_heading"),
                FieldPanel("confirmation_body"),
                FieldPanel("confirmation_button_text"),
            ],
            heading="Subscription Confirmation Email",
        ),
        MultiFieldPanel(
            [
                FieldPanel("unsubscribe_subject"),
                FieldPanel("unsubscribe_heading"),
                FieldPanel("unsubscribe_body"),
                FieldPanel("unsubscribe_button_text"),
            ],
            heading="Unsubscribe Confirmation Email",
        ),
    ]

    class Meta:
        verbose_name = "Newsletter Email Settings"
