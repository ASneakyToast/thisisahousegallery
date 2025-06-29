import logging
from django.forms import Media
from wagtail.admin.panels import FieldPanel
from wagtail.admin.staticfiles import versioned_static
from wagtail.images.widgets import AdminImageChooser

logger = logging.getLogger(__name__)


class ExhibitionImageChooserWidget(AdminImageChooser):
    """
    Enhanced image chooser widget that uses the exhibition image chooser viewset
    with advanced filtering capabilities and larger inline image previews.
    """
    
    # Override the chooser URL name to use our custom chooser
    chooser_url_name = 'exhibition_image_chooser:choose'
    
    # Explicitly specify our custom template
    template_name = 'wagtailimages/widgets/image_chooser.html'
    
    
    def render(self, name, value, attrs=None, renderer=None):
        """Override render to add debug logging."""
        print(f"🔥 ENHANCED CHOOSER WIDGET CALLED: {name} = {value}")
        logger.error(f"🔥 ExhibitionImageChooserWidget.render called with value: {value}")
        logger.error(f"🔥 Template name: {self.template_name}")
        logger.error(f"🔥 Widget class: {self.__class__.__name__}")
        result = super().render(name, value, attrs, renderer)
        logger.error(f"🔥 Rendered HTML length: {len(result)}")
        print(f"🔥 RENDERED HTML PREVIEW: {result[:200]}...")
        
        return result
    
    @property
    def media(self):
        """
        Include required CSS and JavaScript for the enhanced chooser.
        """
        return Media(
            css={
                'all': [
                    'css/components/admin-chooser.css',
                ]
            },
            js=[
                versioned_static('wagtailadmin/js/modal-workflow.js'),
                versioned_static('wagtailimages/js/image-chooser-modal.js'),
                versioned_static('wagtailimages/js/image-chooser.js'),
            ]
        )


class ExhibitionImageChooserPanel(FieldPanel):
    """
    Custom field panel that uses the ExhibitionImageChooserWidget
    for enhanced image selection with filtering.
    """
    
    def get_form_options(self):
        """Override to inject our custom widget."""
        opts = super().get_form_options()
        opts['widget'] = ExhibitionImageChooserWidget()
        return opts
    
    class Meta:
        # Inherit all parent meta options
        pass