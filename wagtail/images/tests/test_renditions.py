import pytest


@pytest.mark.django_db
def test_rendition_does_not_leak_file(image):
    # image fixture already exists in wagtail tests
    rendition = image.get_rendition("fill-50x50")

    assert rendition is not None