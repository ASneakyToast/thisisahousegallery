from wagtail.images.views.multiple import AddView as BaseAddView
from wagtail.images.views.multiple import (
    CreateFromUploadedImageView as BaseCreateFromUploadedImageView,
)


class CustomAddView(BaseAddView):
    """
    Custom multi-upload view that captures preserve_original preference
    and applies it to all images in the batch.
    """

    def post(self, request, *args, **kwargs):
        # Capture the preserve_original preference from the form
        preserve_original = request.POST.get("preserve_original") == "1"

        # Store it in the session for this upload batch
        request.session["batch_preserve_original"] = preserve_original

        # Continue with the standard multi-upload flow
        return super().post(request, *args, **kwargs)

    def save_object(self, form):
        """
        Override save_object to apply the batch preserve_original preference
        to each uploaded image.
        """
        # Get the preserve_original preference for this batch
        preserve_original = self.request.session.get("batch_preserve_original", False)

        # Create the image object but don't save yet
        image = form.save(commit=False)

        # Apply the batch preference
        image.preserve_original = preserve_original

        # Set the uploaded_by_user field
        image.uploaded_by_user = self.request.user

        # Now save the image (our custom save logic will run)
        image.save()

        return image


class CustomCreateFromUploadedImageView(BaseCreateFromUploadedImageView):
    """
    Custom view for creating images from uploaded files that applies
    the batch preserve_original preference.
    """

    def save_object(self, form):
        """
        Override save_object to apply the batch preserve_original preference
        when creating an image from an uploaded file.
        """
        # Get the preserve_original preference for this batch
        preserve_original = self.request.session.get("batch_preserve_original", False)

        # Assign the file content from uploaded_image to the image object
        self.object.file.save(
            self.upload.file.name, self.upload.file.file, save=False,
        )

        # Apply the batch preference
        self.object.preserve_original = preserve_original

        # Set the uploaded_by_user field
        self.object.uploaded_by_user = self.request.user

        # Set image file metadata (Wagtail requirement)
        self.object._set_image_file_metadata()

        # Save the form (our custom save logic will run)
        form.save()

