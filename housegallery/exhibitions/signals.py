from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib import messages
from django.utils import timezone
from wagtail.models import Page
from .models import ExhibitionPage, EventPage


@receiver(post_save, sender=ExhibitionPage)
def create_opening_event(sender, instance, created, **kwargs):
    """
    Create an opening reception event when the create_opening_event checkbox is checked.
    
    This signal handler runs after an ExhibitionPage is saved and:
    1. Checks if create_opening_event is True
    2. Checks if an opening event already exists for this exhibition
    3. Creates a new EventPage with exhibition details if none exists
    4. Links the created event back to the exhibition
    """
    
    # Only proceed if create_opening_event is checked
    if not instance.create_opening_event:
        return
    
    # Check if we already have an auto-created event for this exhibition
    if instance.auto_created_opening_event:
        return
    
    # Check if there's already an opening event for this exhibition
    existing_opening_events = EventPage.objects.filter(
        related_exhibition=instance,
        event_type='exhibition_opening'
    )
    
    if existing_opening_events.exists():
        # There's already an opening event - link it and uncheck the box
        instance.auto_created_opening_event = existing_opening_events.first()
        instance.create_opening_event = False
        instance.save(update_fields=['auto_created_opening_event', 'create_opening_event'])
        return
    
    # Find the schedule page to create the event under
    try:
        from .models import SchedulePage
        schedule_page = SchedulePage.objects.live().first()
        if not schedule_page:
            # Can't create event without a schedule page
            return
    except:
        return
    
    # Create the opening event
    event_title = f"{instance.title} - Opening Reception"
    event_slug = f"{instance.slug}-opening-reception"
    
    # Ensure unique slug
    base_slug = event_slug
    counter = 1
    while Page.objects.filter(slug=event_slug).exists():
        event_slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Create the event page
    event_page = EventPage(
        title=event_title,
        slug=event_slug,
        event_type='exhibition_opening',
        tagline=f"Opening reception for {instance.title}",
        related_exhibition=instance,
        start_date=instance.start_date or timezone.now().date(),
        description=f"Join us for the opening reception of {instance.title}. {instance.description[:200]}..." if instance.description else f"Join us for the opening reception of {instance.title}.",
        featured_image=instance.get_first_showcard_image(),
        live=True,
        featured_on_schedule=True,
    )
    
    # Add the event as a child of the schedule page
    schedule_page.add_child(instance=event_page)
    
    # Link the exhibition to the created event
    instance.auto_created_opening_event = event_page
    instance.create_opening_event = False  # Reset the checkbox
    instance.save(update_fields=['auto_created_opening_event', 'create_opening_event'])
    
    # Copy exhibition artists to the event
    for exhibition_artist in instance.exhibition_artists.all():
        from .models import EventArtist
        EventArtist.objects.create(
            event=event_page,
            artist=exhibition_artist.artist,
            role='featured',
            is_featured=True
        )