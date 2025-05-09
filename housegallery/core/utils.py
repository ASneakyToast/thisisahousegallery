from django.core.exceptions import ValidationError
from django.utils.functional import cached_property

from wagtail import blocks
from wagtail.blocks.struct_block import StructValue
from wagtail.documents.blocks import DocumentChooserBlock


class LinkBlockStructValue(StructValue):
    """
    A unified StructValue class for resolving URLs and link text
    for all types of links (pages, external URLs, documents, emails).
    """
    @cached_property
    def link_url(self):
        link_type = self.get('link_type')

        if link_type == 'page' and self.get('page'):
            # Return page URL, handling case where page might be deleted
            page = self.get('page')
            return page.url if page else None
        elif link_type == 'external' and self.get('external_url'):
            return self.get('external_url')
        elif link_type == 'document' and self.get('document'):
            # Handle case where document might be deleted
            document = self.get('document')
            return document.url if document else None
        elif link_type == 'email' and self.get('email'):
            return f"mailto:{self.get('email')}"
        return None

    @cached_property
    def link_text(self):
        # Use custom link_text if provided, otherwise use resource title
        if self.get('link_text'):
            return self.get('link_text')

        link_type = self.get('link_type')

        if link_type == 'page' and self.get('page'):
            page = self.get('page')
            return page.title if page else "Page no longer exists"
        elif link_type == 'document' and self.get('document'):
            document = self.get('document')
            return document.title if document else "Document no longer exists"
        elif link_type == 'email' and self.get('email'):
            return self.get('email')
        elif link_type == 'external' and self.get('external_url'):
            return self.get('external_url')

        return "Link"


class LinkBlock(blocks.StructBlock):
    """
    A unified link block that can handle page links, external URLs,
    document links, and email links. Uses a dropdown to select the link type
    for a cleaner UI experience.
    """
    link_type = blocks.ChoiceBlock(
        choices=[
            ('page', 'Page'),
            ('external', 'External URL'),
            ('document', 'Document'),
            ('email', 'Email Address'),
        ],
        default='page',
        required=True,
        help_text='Select the type of link you want to create'
    )

    link_text = blocks.CharBlock(
        required=False,
        help_text="Optional custom link text. Leave blank to use the page/document title or URL"
    )

    # Link destination fields - only one will be used based on link_type
    page = blocks.PageChooserBlock(required=False)
    external_url = blocks.URLBlock(required=False)
    document = DocumentChooserBlock(required=False)
    email = blocks.EmailBlock(required=False)

    class Meta:
        icon = 'link'
        value_class = LinkBlockStructValue

    def clean(self, value):
        result = super().clean(value)
        errors = {}

        link_type = value.get('link_type')

        # Validate that the appropriate field for the selected link type is filled
        if link_type == 'page' and not value.get('page'):
            errors['page'] = ['Please select a page.']
        elif link_type == 'external' and not value.get('external_url'):
            errors['external_url'] = ['Please enter a URL.']
        elif link_type == 'document' and not value.get('document'):
            errors['document'] = ['Please select a document.']
        elif link_type == 'email' and not value.get('email'):
            errors['email'] = ['Please enter an email address.']

        # If external URL is selected, link_text is required
        if link_type == 'external' and value.get('external_url') and not value.get('link_text'):
            errors['link_text'] = ['Link text is required for external URLs.']

        if errors:
            raise ValidationError(
                'Validation error in LinkBlock: {}'.format(dict(errors)),
                params=errors
            )

        return result
