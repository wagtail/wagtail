import pytest
from wagtail.serializers.page_serializer import PageSerializer
from wagtail.test.testapp.models import SimplePage
from wagtail.models import Page,ContentType

@pytest.mark.django_db
def test_page_serializer():
    content_type = ContentType.objects.create(
        app_label = "test",
        model = "test model",
    )
    root = Page.get_first_root_node()
    page = root.add_child(instance = SimplePage(
        title = "test",
        draft_title = "test",
        slug = "test",
        content = "this is a test page",
        content_type = content_type
    ))

    serializer = PageSerializer(page)
    assert serializer.data['title'] == "test"
    assert serializer.data['draft_title'] == "test"