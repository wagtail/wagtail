from django.test import TestCase

from wagtail.snippets.widgets import (
    AdminSnippetChooser,
    SnippetChooserAdapter,
)
from wagtail.test.testapp.models import (
    Advert,
    SnippetWithFKToSlug,
    SnippetWithSlugPrimaryKey,
)
from wagtail.test.utils import WagtailTestUtils


class TestAdminSnippetChooserWidget(WagtailTestUtils, TestCase):
    def test_adapt(self):
        widget = AdminSnippetChooser(Advert)

        js_args = SnippetChooserAdapter().js_args(widget)

        self.assertEqual(len(js_args), 3)
        self.assertInHTML(
            '<input type="hidden" name="__NAME__" id="__ID__">', js_args[0]
        )
        self.assertIn("Choose advert", js_args[0])
        self.assertEqual(js_args[1], "__ID__")


class TestAdminSnippetChooserWidgetToField(WagtailTestUtils, TestCase):
    """
    Regression tests for https://github.com/wagtail/wagtail/issues/13116
    SnippetViewSet should handle ForeignKey with to_field pointing to a non-pk field.
    """

    def setUp(self):
        self.target = SnippetWithSlugPrimaryKey.objects.create(
            slug="test-slug", name="Test Category"
        )
        self.instance = SnippetWithFKToSlug.objects.create(
            title="Test Post", related=self.target
        )

    def test_get_instance_by_to_field(self):
        """Widget should resolve a slug value to the correct instance."""
        widget = AdminSnippetChooser(SnippetWithSlugPrimaryKey)
        widget.to_field_name = "slug"
        instance = widget.get_instance("test-slug")
        self.assertEqual(instance, self.target)

    def test_get_value_data_from_instance_uses_to_field(self):
        """get_value_data_from_instance should return the to_field value as id, not pk."""
        widget = AdminSnippetChooser(SnippetWithSlugPrimaryKey)
        widget.to_field_name = "slug"
        data = widget.get_value_data_from_instance(self.target)
        self.assertEqual(data["id"], "test-slug")

    def test_get_instance_without_to_field_uses_pk(self):
        """Without to_field_name, widget should still resolve by pk as before."""
        widget = AdminSnippetChooser(SnippetWithSlugPrimaryKey)
        instance = widget.get_instance(self.target.pk)
        self.assertEqual(instance, self.target)
