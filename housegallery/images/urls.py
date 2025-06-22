from django.urls import path

from .views import CustomAddView
from .views import CustomCreateFromUploadedImageView

app_name = "custom_images"

urlpatterns = [
    # Override the wagtail multi-upload URLs with our custom views
    path("multiple/add/", CustomAddView.as_view(), name="add_multiple"),
    path(
        "multiple/create_from_uploaded_image/<int:uploaded_file_id>/",
        CustomCreateFromUploadedImageView.as_view(),
        name="create_multiple_from_uploaded_image",
    ),
]

