import pytest
from .utils import Image, get_test_image_file


@pytest.fixture
def image():
    return Image.objects.create(
        title="Test image",
        file=get_test_image_file(),
    )
