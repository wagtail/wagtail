import pytest

from wagtail.models import ContentType
from wagtail.models.pages import Page
from wagtail.models.sites import Site
from wagtail.serializers.site_serializer import SiteSerializer
from wagtail.test.testapp.models import SimplePage


@pytest.mark.django_db
def test_site_serializer():
    content_type = ContentType.objects.create(app_label="test", model="test")
    root = Page.get_first_root_node()
    page = root.add_child(
        instance=SimplePage(
            title="test",
            draft_title="test",
            slug="test",
            content="this is a test page",
            content_type=content_type,
        )
    )
    site = Site.objects.create(
        hostname="test",
        site_name="test",
        root_page=page,
        is_default_site=True,
    )

    serializer = SiteSerializer(site)
    assert serializer.data["hostname"] == "test"
    assert serializer.data["site_name"] == "test"
