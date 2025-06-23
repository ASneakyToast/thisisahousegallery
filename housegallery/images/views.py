from wagtail.images.views.multiple import AddView as BaseAddView
from wagtail.images.views.multiple import (
    CreateFromUploadedImageView as BaseCreateFromUploadedImageView,
)


class CustomAddView(BaseAddView):
    """
    Custom multi-upload view that captures preserve_original, title, alt_text, 
    credit, description, and tags preferences and applies them to all images in the batch.
    """

    def post(self, request, *args, **kwargs):
        # Capture the preferences from the form
        preserve_original = request.POST.get("preserve_original") == "1"
        title = request.POST.get("title", "").strip()
        alt_text = request.POST.get("alt_text", "").strip()
        credit = request.POST.get("credit", "").strip()
        description = request.POST.get("description", "").strip()
        tags = request.POST.get("tags", "").strip()

        # Store them in the session for this upload batch
        request.session["batch_preserve_original"] = preserve_original
        request.session["batch_title"] = title
        request.session["batch_alt_text"] = alt_text
        request.session["batch_credit"] = credit
        request.session["batch_description"] = description
        request.session["batch_tags"] = tags

        # Continue with the standard multi-upload flow
        return super().post(request, *args, **kwargs)

    def save_object(self, form):
        """
        Override save_object to apply the batch preferences (preserve_original,
        title, alt_text, credit, description, and tags) to each uploaded image.
        """
        # Get the batch preferences for this upload
        preserve_original = self.request.session.get("batch_preserve_original", False)
        title = self.request.session.get("batch_title", "")
        alt_text = self.request.session.get("batch_alt_text", "")
        credit = self.request.session.get("batch_credit", "")
        description = self.request.session.get("batch_description", "")
        tags_string = self.request.session.get("batch_tags", "")

        # Create the image object but don't save yet
        image = form.save(commit=False)

        # Apply the batch preferences
        image.preserve_original = preserve_original
        if title:
            image.title = title
        if alt_text:
            image.alt = alt_text
        if credit:
            image.credit = credit
        if description:
            image.description = description

        # Set the uploaded_by_user field
        image.uploaded_by_user = self.request.user

        # Now save the image (our custom save logic will run)
        image.save()

        # Apply tags after saving (tags require the object to have a primary key)
        if tags_string:
            # Parse comma-separated tags and add them
            tag_names = [tag.strip() for tag in tags_string.split(",") if tag.strip()]
            for tag_name in tag_names:
                image.tags.add(tag_name)

        return image


class CustomCreateFromUploadedImageView(BaseCreateFromUploadedImageView):
    """
    Custom view for creating images from uploaded files that applies
    the batch preserve_original, title, alt_text, credit, description, and tags preferences.
    """

    def save_object(self, form):
        """
        Override save_object to apply the batch preferences (preserve_original,
        title, alt_text, credit, description, and tags) when creating an image from an uploaded file.
        """
        # Get the batch preferences for this upload
        preserve_original = self.request.session.get("batch_preserve_original", False)
        title = self.request.session.get("batch_title", "")
        alt_text = self.request.session.get("batch_alt_text", "")
        credit = self.request.session.get("batch_credit", "")
        description = self.request.session.get("batch_description", "")
        tags_string = self.request.session.get("batch_tags", "")

        # Assign the file content from uploaded_image to the image object
        self.object.file.save(
            self.upload.file.name, self.upload.file.file, save=False,
        )

        # Apply the batch preferences
        self.object.preserve_original = preserve_original
        if title:
            self.object.title = title
        if alt_text:
            self.object.alt = alt_text
        if credit:
            self.object.credit = credit
        if description:
            self.object.description = description

        # Set the uploaded_by_user field
        self.object.uploaded_by_user = self.request.user

        # Set image file metadata (Wagtail requirement)
        self.object._set_image_file_metadata()

        # Save the form (our custom save logic will run)
        form.save()

        # Apply tags after saving (tags require the object to have a primary key)
        if tags_string:
            # Parse comma-separated tags and add them
            tag_names = [tag.strip() for tag in tags_string.split(",") if tag.strip()]
            for tag_name in tag_names:
                self.object.tags.add(tag_name)

