from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from .models import Newsletter, Subscriber
from .services import send_newsletter_edition


class SendNewsletterView(View):
    template_name = "newsletter/admin/send_confirm.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.newsletter = get_object_or_404(Newsletter, pk=kwargs["pk"])

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_active_subscriber_count(self):
        return Subscriber.objects.filter(
            confirmed=True, unsubscribed_at__isnull=True, bounce_count__lt=3
        ).count()

    def get_context_data(self):
        breadcrumbs_items = [
            {
                "url": reverse("wagtailsnippets_newsletter_newsletter:list"),
                "label": "Newsletters",
            },
            {
                "url": reverse(
                    "wagtailsnippets_newsletter_newsletter:edit",
                    args=[self.newsletter.pk],
                ),
                "label": str(self.newsletter.title),
            },
            {"url": "", "label": "Send"},
        ]
        return {
            "newsletter": self.newsletter,
            "subscriber_count": self.get_active_subscriber_count(),
            "preview_url": reverse(
                "newsletter:preview", args=[self.newsletter.slug]
            ),
            "already_sent": self.newsletter.status == Newsletter.Status.SENT,
            "edit_url": reverse(
                "wagtailsnippets_newsletter_newsletter:edit",
                args=[self.newsletter.pk],
            ),
            "breadcrumbs_items": breadcrumbs_items,
            "header_icon": "mail",
            "page_title": "Send Newsletter",
            "page_subtitle": self.newsletter.title,
            "header_title": f"Send Newsletter: {self.newsletter.title}",
        }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")

        if action == "test":
            test_email = request.POST.get("test_email", "").strip()
            if not test_email:
                messages.error(request, "Please enter a test email address.")
                return render(request, self.template_name, self.get_context_data())

            try:
                result = send_newsletter_edition(
                    self.newsletter, test_email=test_email
                )
                if result["sent"]:
                    messages.success(
                        request, f"Test email sent to {test_email}."
                    )
                else:
                    messages.error(
                        request,
                        f"Failed to send test email: {result['error_details']}",
                    )
            except Exception as e:
                messages.error(request, f"Error sending test email: {e}")

            return redirect(
                reverse(
                    "wagtailsnippets_newsletter_newsletter:send",
                    args=[self.newsletter.pk],
                )
            )

        elif action == "send":
            already_sent = self.newsletter.status == Newsletter.Status.SENT
            force = request.POST.get("force") == "on"

            if already_sent and not force:
                messages.error(
                    request,
                    "This newsletter was already sent. Check the force checkbox to send again.",
                )
                return render(request, self.template_name, self.get_context_data())

            confirm = request.POST.get("confirm") == "on"
            if not confirm:
                messages.error(
                    request, "Please check the confirmation checkbox to send."
                )
                return render(request, self.template_name, self.get_context_data())

            try:
                result = send_newsletter_edition(
                    self.newsletter, force=force
                )
                if result.get("no_recipients"):
                    messages.warning(request, "No active subscribers found.")
                else:
                    messages.success(
                        request,
                        f"Newsletter sent to {result['sent']} subscribers."
                        + (
                            f" {result['errors']} errors."
                            if result["errors"]
                            else ""
                        ),
                    )
            except ValueError as e:
                messages.error(request, str(e))
                return render(request, self.template_name, self.get_context_data())
            except Exception as e:
                messages.error(request, f"Error sending newsletter: {e}")
                return render(request, self.template_name, self.get_context_data())

            return redirect(
                reverse(
                    "wagtailsnippets_newsletter_newsletter:edit",
                    args=[self.newsletter.pk],
                )
            )

        messages.error(request, "Invalid action.")
        return render(request, self.template_name, self.get_context_data())
