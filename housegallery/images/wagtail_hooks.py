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
def hide_default_documents_menu(request, menu_items):
    """Hide the default Documents menu item since we're reorganizing it under Assets."""
    # Remove the default documents menu item
    menu_items[:] = [item for item in menu_items if getattr(item, 'name', None) != 'documents']


@hooks.register('construct_main_menu')
def add_assets_menu(request, menu_items):
    """Add custom Assets menu with Images and Documents submenus."""
    
    # Create submenu items
    images_menu_item = MenuItem(
        'Images',
        reverse('wagtailimages:index'),  # Use default Wagtail images URL
        icon_name='image',
        order=100
    )
    
    documents_menu_item = MenuItem(
        'Documents',
        reverse('wagtaildocs:index'),  # Use default Wagtail documents URL
        icon_name='doc-full',
        order=200
    )
    
    # Create Menu object containing the menu items
    assets_submenu = Menu(items=[images_menu_item, documents_menu_item])
    
    # Create the main Assets menu with submenus
    assets_menu = SubmenuMenuItem(
        'Assets',
        assets_submenu,
        icon_name='folder-open-inverse',
        order=300  # Position in main menu
    )
    
    # Insert the Assets menu at the appropriate position
    # Find a good spot after "Pages" but before "Settings"
    insert_position = 1  # After "Pages"
    for i, item in enumerate(menu_items):
        if hasattr(item, 'name') and item.name == 'settings':
            insert_position = i
            break
    
    menu_items.insert(insert_position, assets_menu)


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
                reverse('wagtailadmin_explore', args=[exhibitions_page.id]),
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
        order=400  # Position in main menu after Assets
    )
    
    # Insert the Art menu at the appropriate position
    insert_position = 2  # After "Pages" and "Assets"
    for i, item in enumerate(menu_items):
        if hasattr(item, 'name') and item.name == 'settings':
            insert_position = i
            break
    
    menu_items.insert(insert_position, art_menu)


@hooks.register('construct_main_menu')
def add_menu_management_menu(request, menu_items):
    """Add hierarchical Menu management with Menu Lists, Header, Navigation Settings, and Footer submenus."""
    
    # Create submenu items for menu management
    menu_lists_item = MenuItem(
        'Menu Lists',
        reverse('wagtailsnippets_core_navigationmenu:list'),
        icon_name='list-ul',
        order=100
    )
    
    header_menu_item = MenuItem(
        'Header',
        reverse('wagtailsettings:edit', args=['core', 'navigationsettings']),
        icon_name='arrow-up',
        order=200
    )
    
    navigation_settings_item = MenuItem(
        'Hamburger',
        reverse('wagtailsettings:edit', args=['core', 'navigationsettings']),
        icon_name='cogs',
        order=250
    )
    
    footer_menu_item = MenuItem(
        'Footer',
        '#',  # Placeholder URL for future footer menu settings
        icon_name='arrow-down',
        order=300
    )
    
    # Create Menu object containing the menu management items
    menu_submenu = Menu(items=[menu_lists_item, header_menu_item, navigation_settings_item, footer_menu_item])
    
    # Create the main Menu management menu with submenus
    menu_management_menu = SubmenuMenuItem(
        'Menus',
        menu_submenu,
        icon_name='list-ul',
        order=500  # Position in main menu
    )
    
    # Insert after Art menu
    insert_position = 3  # After "Pages", "Assets", and "Art"
    for i, item in enumerate(menu_items):
        if hasattr(item, 'name') and item.name == 'settings':
            insert_position = i
            break
    
    menu_items.insert(insert_position, menu_management_menu)


@hooks.register('construct_settings_menu')
def hide_navigation_settings_from_main_settings(request, menu_items):
    """Hide Navigation Settings from the main Settings menu since it's now under Menus."""
    # Remove NavigationSettings from the main settings menu
    menu_items[:] = [
        item for item in menu_items 
        if not (hasattr(item, 'url') and 'navigationsettings' in str(item.url))
    ]


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
    insert_position = 4  # After "Pages", "Assets", "Art", and "Menu Lists"
    for i, item in enumerate(menu_items):
        if hasattr(item, 'name') and item.name == 'settings':
            insert_position = i
            break
    
    menu_items.insert(insert_position, events_menu)