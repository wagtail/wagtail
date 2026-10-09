from django.test import TestCase

from wagtail.api.v3.fields import FieldSerializer
from wagtail.test.testapp.models import EventPage
from wagtail.test.utils import Page


class IdentityFieldSerializer(FieldSerializer):
    def to_representation(self, value):
        return value


class TestFieldSerializerGetAttribute(TestCase):
    def get_attribute(self, source, instance):
        field = IdentityFieldSerializer(source=source)
        field.bind("field")
        return field.get_attribute(instance)

    def test_dotted_source(self):
        page = Page.objects.get(depth=1)
        self.assertEqual(
            self.get_attribute("content_type.app_label", page), "wagtailcore"
        )

    def test_dotted_source_stops_at_none(self):
        class Obj:
            child = None

        self.assertIsNone(self.get_attribute("child.title", Obj()))

    def test_unknown_attribute_raises(self):
        page = Page.objects.get(depth=1)
        with self.assertRaises(AttributeError):
            self.get_attribute("titel", page)

    def test_callable_is_not_called(self):
        page = Page.objects.get(depth=1)
        self.assertEqual(self.get_attribute("get_url_parts", page), page.get_url_parts)

    def test_nonexistent_reverse_one_to_one(self):
        page = Page.objects.get(depth=1)
        self.assertFalse(EventPage.objects.filter(pk=page.pk).exists())
        self.assertIsNone(self.get_attribute("eventpage", page))
