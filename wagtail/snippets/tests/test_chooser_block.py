from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.test import TestCase

from wagtail.blocks.field_block import FieldBlockAdapter
from wagtail.models import Locale
from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail.snippets.widgets import AdminSnippetChooser
from wagtail.test.testapp.models import Advert, AdvertWithCustomPrimaryKey


class TestSnippetChooserBlock(TestCase):
    fixtures = ["test.json"]

    def test_serialize(self):
        """The value of a SnippetChooserBlock (a snippet instance) should serialize to an ID"""
        block = SnippetChooserBlock(Advert)
        test_advert = Advert.objects.get(text="test_advert")

        self.assertEqual(block.get_prep_value(test_advert), test_advert.id)

        # None should serialize to None
        self.assertIsNone(block.get_prep_value(None))

    def test_deserialize(self):
        """The serialized value of a SnippetChooserBlock (an ID) should deserialize to a snippet instance"""
        block = SnippetChooserBlock(Advert)
        test_advert = Advert.objects.get(text="test_advert")

        self.assertEqual(block.to_python(test_advert.id), test_advert)

        # None should deserialize to None
        self.assertIsNone(block.to_python(None))

    def test_reference_model_by_string(self):
        block = SnippetChooserBlock("tests.Advert")
        test_advert = Advert.objects.get(text="test_advert")
        self.assertEqual(block.to_python(test_advert.id), test_advert)

    def test_adapt(self):
        block = SnippetChooserBlock(
            Advert,
            help_text="pick an advert, any advert",
            description="An advert to be displayed on the sidebar.",
        )

        block.set_name("test_snippetchooserblock")
        js_args = FieldBlockAdapter().js_args(block)

        self.assertEqual(js_args[0], "test_snippetchooserblock")
        self.assertIsInstance(js_args[1], AdminSnippetChooser)
        self.assertEqual(js_args[1].model, Advert)
        self.assertEqual(
            js_args[2],
            {
                "label": "Test snippetchooserblock",
                "description": "An advert to be displayed on the sidebar.",
                "required": True,
                "icon": "snippet",
                "blockDefId": block.definition_prefix,
                "isPreviewable": block.is_previewable,
                "helpText": "pick an advert, any advert",
                "classname": "w-field w-field--model_choice_field w-field--admin_snippet_chooser",
                "attrs": {},
                "showAddCommentButton": True,
                "strings": {"ADD_COMMENT": "Add Comment"},
            },
        )

    def test_form_response(self):
        block = SnippetChooserBlock(Advert)
        test_advert = Advert.objects.get(text="test_advert")

        value = block.value_from_datadict({"advert": str(test_advert.id)}, {}, "advert")
        self.assertEqual(value, test_advert)

        empty_value = block.value_from_datadict({"advert": ""}, {}, "advert")
        self.assertIsNone(empty_value)

    def test_clean(self):
        required_block = SnippetChooserBlock(Advert)
        nonrequired_block = SnippetChooserBlock(Advert, required=False)
        test_advert = Advert.objects.get(text="test_advert")

        self.assertEqual(required_block.clean(test_advert), test_advert)
        with self.assertRaises(ValidationError):
            required_block.clean(None)

        self.assertEqual(nonrequired_block.clean(test_advert), test_advert)
        self.assertIsNone(nonrequired_block.clean(None))

    def test_deconstruct(self):
        block = SnippetChooserBlock(Advert, required=False)
        path, args, kwargs = block.deconstruct()
        self.assertEqual(path, "wagtail.snippets.blocks.SnippetChooserBlock")
        self.assertEqual(args, (Advert,))
        self.assertEqual(kwargs, {"required": False})

    def test_extract_references(self):
        block = SnippetChooserBlock(Advert)
        test_advert = Advert.objects.get(text="test_advert")

        self.assertListEqual(
            list(block.extract_references(test_advert)),
            [(Advert, str(test_advert.id), "", "")],
        )

        # None should not yield any references
        self.assertListEqual(list(block.extract_references(None)), [])

    def test_exception_on_non_snippet_model(self):
        with self.assertRaises(ImproperlyConfigured):
            block = SnippetChooserBlock(Locale)
            block.widget


class TestSnippetChooserBlockWithCustomPrimaryKey(TestCase):
    fixtures = ["test.json"]

    def test_serialize(self):
        """The value of a SnippetChooserBlock (a snippet instance) should serialize to an ID"""
        block = SnippetChooserBlock(AdvertWithCustomPrimaryKey)
        test_advert = AdvertWithCustomPrimaryKey.objects.get(pk="advert/01")

        self.assertEqual(block.get_prep_value(test_advert), test_advert.pk)

        # None should serialize to None
        self.assertIsNone(block.get_prep_value(None))

    def test_deserialize(self):
        """The serialized value of a SnippetChooserBlock (an ID) should deserialize to a snippet instance"""
        block = SnippetChooserBlock(AdvertWithCustomPrimaryKey)
        test_advert = AdvertWithCustomPrimaryKey.objects.get(pk="advert/01")

        self.assertEqual(block.to_python(test_advert.pk), test_advert)

        # None should deserialize to None
        self.assertIsNone(block.to_python(None))

    def test_adapt(self):
        block = SnippetChooserBlock(
            AdvertWithCustomPrimaryKey,
            help_text="pick an advert, any advert",
            description="An advert to be displayed on the footer.",
        )

        block.set_name("test_snippetchooserblock")
        js_args = FieldBlockAdapter().js_args(block)

        self.assertEqual(js_args[0], "test_snippetchooserblock")
        self.assertIsInstance(js_args[1], AdminSnippetChooser)
        self.assertEqual(js_args[1].model, AdvertWithCustomPrimaryKey)
        self.assertEqual(
            js_args[2],
            {
                "label": "Test snippetchooserblock",
                "description": "An advert to be displayed on the footer.",
                "required": True,
                "icon": "snippet",
                "blockDefId": block.definition_prefix,
                "isPreviewable": block.is_previewable,
                "helpText": "pick an advert, any advert",
                "classname": "w-field w-field--model_choice_field w-field--admin_snippet_chooser",
                "attrs": {},
                "showAddCommentButton": True,
                "strings": {"ADD_COMMENT": "Add Comment"},
            },
        )

    def test_form_response(self):
        block = SnippetChooserBlock(AdvertWithCustomPrimaryKey)
        test_advert = AdvertWithCustomPrimaryKey.objects.get(pk="advert/01")

        value = block.value_from_datadict(
            {"advertwithcustomprimarykey": str(test_advert.pk)},
            {},
            "advertwithcustomprimarykey",
        )
        self.assertEqual(value, test_advert)

        empty_value = block.value_from_datadict(
            {"advertwithcustomprimarykey": ""}, {}, "advertwithcustomprimarykey"
        )
        self.assertIsNone(empty_value)

    def test_clean(self):
        required_block = SnippetChooserBlock(AdvertWithCustomPrimaryKey)
        nonrequired_block = SnippetChooserBlock(
            AdvertWithCustomPrimaryKey, required=False
        )
        test_advert = AdvertWithCustomPrimaryKey.objects.get(pk="advert/01")

        self.assertEqual(required_block.clean(test_advert), test_advert)
        with self.assertRaises(ValidationError):
            required_block.clean(None)

        self.assertEqual(nonrequired_block.clean(test_advert), test_advert)
        self.assertIsNone(nonrequired_block.clean(None))
