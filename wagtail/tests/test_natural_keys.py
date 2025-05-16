import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image as PILImage

from wagtail.images.models import Image
from wagtail.models import Collection, Page, Site


@pytest.mark.django_db
def test_image_natural_key():
    # creating a small picture
    img_io = io.BytesIO()
    image = PILImage.new("RGB", (100, 100), color="red")
    image.save(img_io, format="JPEG")
    img_io.seek(0)

    # change to upload file for use in imageField
    uploaded_file = SimpleUploadedFile(
        "test.jpeg", img_io.read(), content_type="image/jpeg"
    )

    # create image part
    wagtail_image = Image.objects.create(title="Test Image", file=uploaded_file)

    assert wagtail_image.natural_key() == (wagtail_image.file.name)


@pytest.mark.django_db
def test_page_natural_key():
    root_page = Page.objects.get(depth=1)
    new_page = root_page.add_child(instance=Page(title="Child Page"))
    assert new_page.natural_key() == (new_page.url_path,)


@pytest.mark.django_db
def test_site_natural_key():
    site = Site.objects.create(hostname="localhost", port=8000, root_page_id=1)
    assert site.natural_key() == ("localhost", 8000)


@pytest.mark.django_db
def test_collection_natural_key():
    root = Collection.get_first_root_node()
    child = root.add_child(name="Sub Collection")
    assert child.natural_key() == ("Root", "Sub Collection")
