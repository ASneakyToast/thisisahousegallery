from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import StreamField
from wagtail.search import index

from housegallery.core.mixins import Page
from housegallery.kiosk.blocks import KioskBodyBlock, KioskImageSourceBlock


CAROUSEL_TRANSITION_CHOICES = [
    ('crossfade', 'Crossfade'),
    ('fade-black', 'Fade to Black'),
    ('zoom-fade', 'Zoom Fade'),
    ('soft-focus', 'Soft Focus'),
    ('drift', 'Drift (Ken Burns)'),
]


class KioskPage(Page):
    """
    Unified kiosk display page with configurable template and background.

    Supports multiple display layouts (split two-column, single center column)
    with composable content blocks (headings, QR codes, mailing list signups).
    Routed at /display/<slug>/ using the inherited Wagtail page slug.
    """

    TEMPLATE_CHOICES = [
        ('split', 'Content with Image(s)'),
        ('center', 'Single Center Column'),
    ]

    BACKGROUND_CHOICES = [
        ('particles', 'Floating Image Particles'),
        ('static_image', 'Full Screen Photo'),
        ('solid_color', 'Solid Color'),
    ]

    # --- Template Selection ---
    display_template = models.CharField(
        max_length=20,
        choices=TEMPLATE_CHOICES,
        default='split',
        help_text="Controls the layout and positioning of content",
    )

    # --- Display Images ---
    display_images = StreamField(KioskImageSourceBlock(), blank=True)

    # --- Background ---
    background_style = models.CharField(
        max_length=20,
        choices=BACKGROUND_CHOICES,
        default='particles',
        help_text="Controls the visual background behind content",
    )
    background_gallery = StreamField(
        KioskImageSourceBlock(),
        blank=True,
        help_text="Background image(s) (for Full Screen Photo style)",
    )
    background_color = models.CharField(
        max_length=7,
        default='#111111',
        blank=True,
        help_text="Background color hex code (for Solid Color style)",
    )

    # --- Body Content (composable blocks) ---
    body = StreamField(KioskBodyBlock(), blank=True)

    # --- Particle Animation Settings ---
    max_particles = models.PositiveIntegerField(
        default=8,
        help_text="Maximum number of floating particles on screen at once",
    )
    spawn_interval_min = models.PositiveIntegerField(
        default=1500,
        help_text="Minimum milliseconds between spawning new particles",
    )
    spawn_interval_max = models.PositiveIntegerField(
        default=4000,
        help_text="Maximum milliseconds between spawning new particles",
    )

    # --- Carousel Animation Settings ---
    carousel_interval = models.PositiveIntegerField(
        default=5000,
        help_text="Milliseconds between slide transitions",
    )
    carousel_transition_duration = models.PositiveIntegerField(
        default=1200,
        help_text="Milliseconds for the transition between slides",
    )
    carousel_transition = models.CharField(
        max_length=20,
        choices=CAROUSEL_TRANSITION_CHOICES,
        default='crossfade',
        help_text="Visual effect used when transitioning between slides",
    )

    parent_page_types = ['home.HomePage']
    subpage_types = []

    TEMPLATE_MAP = {
        'split': 'pages/kiosk/kiosk_split.html',
        'center': 'pages/kiosk/kiosk_center.html',
    }

    def get_template(self, request=None, *args, **kwargs):
        return self.TEMPLATE_MAP.get(
            self.display_template,
            'pages/kiosk/kiosk_split.html',
        )

    search_fields = Page.search_fields + [
        index.SearchField('body'),
        index.SearchField('display_images'),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('display_template'),
            FieldPanel('display_images'),
        ], heading="Display Template"),
        MultiFieldPanel([
            FieldPanel('background_style'),
            FieldPanel('background_gallery'),
            FieldPanel('background_color'),
        ], heading="Background"),
        FieldPanel('body'),
        MultiFieldPanel([
            FieldPanel('max_particles'),
            FieldPanel('spawn_interval_min'),
            FieldPanel('spawn_interval_max'),
        ], heading="Particle Animation Settings", classname="collapsible collapsed"),
        MultiFieldPanel([
            FieldPanel('carousel_interval'),
            FieldPanel('carousel_transition_duration'),
            FieldPanel('carousel_transition'),
        ], heading="Carousel Animation Settings", classname="collapsible collapsed"),
    ]

    class Meta:
        verbose_name = "Kiosk"
        verbose_name_plural = "Kiosks"
