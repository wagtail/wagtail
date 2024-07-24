from django.test import TestCase

from wagtail.templatetags.wagtailcore_tags import richtext


class TestTemplateTag(TestCase):
    def test_no_contrib_legacy_richtext_no_wrapper(self):
        self.assertEqual(richtext("Foo"), "Foo")

    def test_contrib_legacy_richtext_renders_wrapper(self):
        with self.modify_settings(
            INSTALLED_APPS={"prepend": "wagtail.contrib.legacy.richtext"}
        ):
            self.assertEqual(richtext("Foo"), """<div class="rich-text">Foo</div>""")
