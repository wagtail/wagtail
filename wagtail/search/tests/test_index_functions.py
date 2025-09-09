from unittest import mock

from django.test import TestCase, override_settings

from wagtail.models import Page
from wagtail.search import index
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import WagtailTestUtils


@mock.patch("wagtail.search.tests.DummySearchBackend", create=True)
@override_settings(
    WAGTAILSEARCH_BACKENDS={
        "default": {"BACKEND": "wagtail.search.tests.DummySearchBackend"}
    }
)
class TestInsertOrUpdateObject(WagtailTestUtils, TestCase):
    def test_converts_to_specific_page(self, backend):
        root_page = Page.objects.get(id=1)
        page = root_page.add_child(
            instance=SimplePage(title="test", slug="test", content="test")
        )

        # Convert page into a generic "Page" object and add it into the index
        unspecific_page = page.page_ptr

        backend().reset_mock()

        index.insert_or_update_object(unspecific_page)

        # It should be automatically converted back to the specific version
        backend().add.assert_called_with(page)
