import pytest

from housegallery.artworks.models import Artwork
from housegallery.exhibitions.models import ExhibitionPhoto


@pytest.mark.django_db
class TestExhibitionPhoto:
    """Tests for the ExhibitionPhoto (unified photo) model."""

    def test_create_with_required_fields(self, exhibition_page, make_image):
        image = make_image(title="Required Fields Image")
        photo = ExhibitionPhoto.objects.create(
            page=exhibition_page, image=image,
        )
        assert photo.pk is not None
        assert photo.page == exhibition_page
        assert photo.image == image

    def test_caption_optional(self, exhibition_page, make_image):
        image = make_image(title="No Caption Image")
        photo = ExhibitionPhoto.objects.create(
            page=exhibition_page, image=image,
        )
        assert photo.caption == ""

    def test_caption_stored(self, exhibition_page, make_image):
        image = make_image(title="Captioned Image")
        photo = ExhibitionPhoto.objects.create(
            page=exhibition_page, image=image, caption="A custom caption",
        )
        assert photo.caption == "A custom caption"

    def test_related_artwork_optional(self, exhibition_page, make_image):
        image = make_image(title="No Artwork Image")
        photo = ExhibitionPhoto.objects.create(
            page=exhibition_page, image=image,
        )
        assert photo.related_artwork is None

    def test_related_artwork_set_null_on_delete(self, exhibition_page, make_image):
        image = make_image(title="Artwork Link Image")
        artwork = Artwork.objects.create(title="Temporary Artwork")
        photo = ExhibitionPhoto.objects.create(
            page=exhibition_page, image=image, related_artwork=artwork,
        )
        assert photo.related_artwork == artwork

        # Delete the artwork; the photo should survive with null FK
        artwork.delete()
        photo.refresh_from_db()
        assert photo.related_artwork is None
