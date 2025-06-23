from wagtail import hooks
from wagtail.admin.menu import MenuItem, SubmenuMenuItem, Menu
from django.urls import reverse


@hooks.register('construct_main_menu')
def hide_default_images_menu(request, menu_items):
    """Hide the default Images menu item since we're replacing it."""
    # Remove the default images menu item
    menu_items[:] = [item for item in menu_items if getattr(item, 'name', None) != 'images']


@hooks.register('construct_main_menu') 
def hide_snippets_menu(request, menu_items):
    """Hide the default Snippets menu since we're reorganizing."""
    # Remove the default snippets menu item
    menu_items[:] = [item for item in menu_items if getattr(item, 'name', None) != 'snippets']


@hooks.register('construct_main_menu')
def add_photos_menu(request, menu_items):
    """Add custom Photos menu with Images and Galleries submenus."""
    
    # Create submenu items
    images_menu_item = MenuItem(
        'Images',
        reverse('wagtailimages:index'),  # Use default Wagtail images URL
        icon_name='image',
        order=100
    )
    
    galleries_menu_item = MenuItem(
        'Galleries', 
        reverse('wagtailsnippets_artworks_gallery:list'),  # Use specific gallery snippet URL
        icon_name='image',
        order=200
    )
    
    # Create Menu object containing the menu items
    photos_submenu = Menu(items=[images_menu_item, galleries_menu_item])
    
    # Create the main Photos menu with submenus
    photos_menu = SubmenuMenuItem(
        'Photos',
        photos_submenu,
        icon_name='image',
        order=300  # Position in main menu
    )
    
    # Insert the Photos menu at the appropriate position
    # Find a good spot after "Pages" but before "Settings"
    insert_position = 1  # After "Pages"
    for i, item in enumerate(menu_items):
        if hasattr(item, 'name') and item.name == 'settings':
            insert_position = i
            break
    
    menu_items.insert(insert_position, photos_menu)


@hooks.register('construct_main_menu')
def add_art_menu(request, menu_items):
    """Add custom Art menu with Exhibitions page link, Artworks and Artists submenus."""
    
    # Create submenu items for art-related content
    art_menu_items = []
    
    # Try to find and link to Exhibitions index page edit view
    try:
        from housegallery.exhibitions.models import ExhibitionsIndexPage
        exhibitions_page = ExhibitionsIndexPage.objects.first()
        if exhibitions_page:
            exhibitions_menu_item = MenuItem(
                'Exhibitions',
                reverse('wagtailadmin_pages:edit', args=[exhibitions_page.id]),
                icon_name='folder-open-inverse',
                order=50
            )
            art_menu_items.append(exhibitions_menu_item)
    except:
        pass  # Skip if page doesn't exist or there's an import error
    
    artworks_menu_item = MenuItem(
        'Artworks',
        reverse('wagtailsnippets_artworks_artwork:list'),
        icon_name='image',
        order=100
    )
    art_menu_items.append(artworks_menu_item)
    
    artists_menu_item = MenuItem(
        'Artists',
        reverse('wagtailsnippets_artists_artist:list'),
        icon_name='user',
        order=200
    )
    art_menu_items.append(artists_menu_item)
    
    # Create Menu object containing the art menu items
    art_submenu = Menu(items=art_menu_items)
    
    # Create the main Art menu with submenus
    art_menu = SubmenuMenuItem(
        'Art',
        art_submenu,
        icon_name='image',
        order=400  # Position in main menu after Photos
    )
    
    # Insert the Art menu at the appropriate position
    insert_position = 2  # After "Pages" and "Photos"
    for i, item in enumerate(menu_items):
        if hasattr(item, 'name') and item.name == 'settings':
            insert_position = i
            break
    
    menu_items.insert(insert_position, art_menu)


@hooks.register('construct_main_menu')
def add_menu_lists_item(request, menu_items):
    """Add direct Menu Lists menu item for navigation management."""
    
    menu_lists_item = MenuItem(
        'Menu Lists',
        reverse('wagtailsnippets_core_navigationmenu:list'),
        icon_name='list-ul',
        order=500
    )
    
    # Insert after Art menu
    insert_position = 3  # After "Pages", "Photos", and "Art"
    for i, item in enumerate(menu_items):
        if hasattr(item, 'name') and item.name == 'settings':
            insert_position = i
            break
    
    menu_items.insert(insert_position, menu_lists_item)


@hooks.register('construct_main_menu')
def add_events_menu(request, menu_items):
    """Add custom Events menu with Schedule page link and Events snippet management."""
    
    # Create submenu items for events-related content
    events_menu_items = []
    
    # Try to find and link to Schedule page edit view
    try:
        from housegallery.exhibitions.models import SchedulePage
        schedule_page = SchedulePage.objects.first()
        if schedule_page:
            schedule_menu_item = MenuItem(
                'Schedule',
                reverse('wagtailadmin_pages:edit', args=[schedule_page.id]),
                icon_name='date',
                order=50
            )
            events_menu_items.append(schedule_menu_item)
    except:
        pass  # Skip if page doesn't exist or there's an import error
    
    events_snippet_item = MenuItem(
        'Events',
        reverse('wagtailsnippets_exhibitions_event:list'),
        icon_name='snippet',
        order=100
    )
    events_menu_items.append(events_snippet_item)
    
    # Create Menu object containing the events menu items
    events_submenu = Menu(items=events_menu_items)
    
    # Create the main Events menu with submenus
    events_menu = SubmenuMenuItem(
        'Events',
        events_submenu,
        icon_name='date',
        order=600  # Position in main menu after Menu Lists
    )
    
    # Insert after Menu Lists
    insert_position = 4  # After "Pages", "Photos", "Art", and "Menu Lists"
    for i, item in enumerate(menu_items):
        if hasattr(item, 'name') and item.name == 'settings':
            insert_position = i
            break
    
    menu_items.insert(insert_position, events_menu)