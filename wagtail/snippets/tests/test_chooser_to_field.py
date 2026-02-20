from django.contrib.admin.utils import quote
from django.test import TestCase
from django.urls import reverse

from wagtail.test.testapp.models import ToFieldCategory, ToFieldPost
from wagtail.test.utils import WagtailTestUtils


class TestChooserToField(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()
        self.category = ToFieldCategory.objects.create(name="Recipes", slug="recipes")
        self.post = ToFieldPost.objects.create(title="My Post", category=self.category)

    def test_edit_view_loads(self):
        url = reverse(
            ToFieldPost.snippet_viewset.get_url_name("edit"), args=[quote(self.post.pk)]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "recipes")
        self.assertContains(response, "Recipes")

    def test_chooser_viewset_registration(self):
        from wagtail.admin.forms.models import registry

        db_field = ToFieldPost._meta.get_field("category")
        overrides = registry.get(db_field)
        self.assertIsNotNone(overrides)

        widget = overrides["widget"]
        self.assertEqual(widget.to_field_name, "slug")

    def test_chooser_widget_renders_correctly(self):
        url = reverse(
            ToFieldPost.snippet_viewset.get_url_name("edit"), args=[quote(self.post.pk)]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="recipes"')
        self.assertContains(response, 'id="id_category"')
