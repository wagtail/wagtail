import unittest.mock

from django.apps import apps
from django.test import TestCase
from django.utils.safestring import SafeString

from wagtail.admin import compare
from wagtail.blocks.stream_block import StreamValue
from wagtail.blocks.struct_block import StructBlockValidationError
from wagtail.images.blocks import ImageBlock, ImageChooserBlock
from wagtail.telepath import JSContext
from wagtail.test.testapp.models import StreamPage
from wagtail.test.utils.wagtail_tests import WagtailTestUtils

from .utils import (
    Image,
    get_test_bad_image,
    get_test_image_file,
    get_test_image_filename,
)


class TestImageChooserBlock(TestCase):
    def setUp(self):
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        self.bad_image = get_test_bad_image()
        self.bad_image.save()

    def test_render(self):
        block = ImageChooserBlock()
        html = block.render(self.image)
        expected_html = (
            '<img alt="Test image" src="{}" width="640" height="480">'.format(
                get_test_image_filename(self.image, "original")
            )
        )

        self.assertHTMLEqual(html, expected_html)

    def test_render_with_custom_default_attrs(self):
        block = ImageChooserBlock()
        with unittest.mock.patch.object(
            apps.get_app_config("wagtailimages"),
            "default_attrs",
            new={"decoding": "async", "loading": "lazy"},
        ):
            html = block.render(self.bad_image)
        self.assertHTMLEqual(
            html,
            '<img alt="missing image" src="/media/not-found" width="0" height="0" decoding="async" loading="lazy">',
        )

    def test_render_missing(self):
        block = ImageChooserBlock()
        html = block.render(self.bad_image)
        expected_html = (
            '<img alt="missing image" src="/media/not-found" width="0" height="0">'
        )

        self.assertHTMLEqual(html, expected_html)

    def test_deconstruct(self):
        block = ImageChooserBlock(required=False)
        path, args, kwargs = block.deconstruct()
        self.assertEqual(path, "wagtail.images.blocks.ImageChooserBlock")
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {"required": False})

    def test_extract_references(self):
        block = ImageChooserBlock()

        self.assertListEqual(
            list(block.extract_references(self.image)),
            [(Image, str(self.image.id), "", "")],
        )

        # None should not yield any references
        self.assertListEqual(list(block.extract_references(None)), [])


class TestImageChooserBlockComparison(TestCase):
    comparison_class = compare.StreamFieldComparison

    def setUp(self):
        self.image_1 = Image.objects.create(
            title="Test image 1",
            file=get_test_image_file(),
        )

        self.image_2 = Image.objects.create(
            title="Test image 2",
            file=get_test_image_file(),
        )

        self.field = StreamPage._meta.get_field("body")

    def test_hasnt_changed(self):
        field = StreamPage._meta.get_field("body")

        comparison = self.comparison_class(
            field,
            StreamPage(
                body=StreamValue(
                    field.stream_block,
                    [
                        ("image", self.image_1, "1"),
                    ],
                )
            ),
            StreamPage(
                body=StreamValue(
                    field.stream_block,
                    [
                        ("image", self.image_1, "1"),
                    ],
                )
            ),
        )

        self.assertTrue(comparison.is_field)
        self.assertFalse(comparison.is_child_relation)
        self.assertEqual(comparison.field_label(), "Body")
        htmldiff = comparison.htmldiff()
        self.assertIsInstance(htmldiff, SafeString)
        self.assertIn('class="comparison__child-object"', htmldiff)
        self.assertIn('class="preview-image"', htmldiff)
        self.assertNotIn("deletion", htmldiff)
        self.assertNotIn("addition", htmldiff)
        self.assertFalse(comparison.has_changed())

    def test_has_changed(self):
        field = StreamPage._meta.get_field("body")

        comparison = self.comparison_class(
            field,
            StreamPage(
                body=StreamValue(
                    field.stream_block,
                    [
                        ("image", self.image_1, "1"),
                    ],
                )
            ),
            StreamPage(
                body=StreamValue(
                    field.stream_block,
                    [
                        ("image", self.image_2, "1"),
                    ],
                )
            ),
        )

        self.assertTrue(comparison.is_field)
        self.assertFalse(comparison.is_child_relation)
        self.assertEqual(comparison.field_label(), "Body")
        htmldiff = comparison.htmldiff()
        self.assertIsInstance(htmldiff, SafeString)
        self.assertIn('class="comparison__child-object"', htmldiff)
        self.assertIn('class="preview-image deletion"', htmldiff)
        self.assertIn('class="preview-image addition"', htmldiff)
        self.assertTrue(comparison.has_changed())


class TestImageBlock(TestImageChooserBlock):
    def test_render(self):
        block = ImageBlock()
        value = {
            "image": self.image.id,  # An id is expected
            "alt_text": "Sample alt text",
            "decorative": False,
        }
        html = block.render(block.to_python(value))
        soup = WagtailTestUtils.get_soup(html)
        img_tag = soup.find("img")

        # check specific attributes
        self.assertEqual(img_tag["alt"], value.get("alt_text"))
        self.assertIn("/media/images/test", img_tag["src"])

    def test_render_basic(self):
        block = ImageBlock()
        value = {
            "image": self.image.id,  # An id is expected
            "alt_text": "Sample alt text",
            "decorative": False,
        }
        html = block.render_basic(block.to_python(value))
        soup = WagtailTestUtils.get_soup(html)
        img_tag = soup.find("img")

        # check specific attributes
        self.assertEqual(img_tag["alt"], value.get("alt_text"))
        self.assertIn("/media/images/test", img_tag["src"])

    def test_render_as_decorative(self):
        block = ImageBlock()
        value = {
            "image": self.image.id,  # An id is expected
            "alt_text": "Sample alt text",
            "decorative": True,
        }
        html = block.render(block.to_python(value))
        soup = WagtailTestUtils.get_soup(html)
        img_tag = soup.find("img")

        # check specific attributes
        self.assertEqual(img_tag["alt"], "")
        self.assertIn("/media/images/test", img_tag["src"])

    def test_no_alt_text(self):
        block = ImageBlock()
        value = {
            "image": self.image.id,  # An id is expected
            "alt_text": None,  # No alt text passed
            "decorative": False,
        }

        # Invalid state when no alt text is given, and image not marked as decorative
        # Should raise a StructBlock validation error
        with self.assertRaises(StructBlockValidationError) as context:
            block.clean(block.to_python(value))

        # Check the error message
        self.assertIn(
            "Please add some alt text for your image or mark it as decorative",
            str(context.exception.block_errors["alt_text"]),
        )

    def test_to_python_with_int(self):
        block = ImageBlock()
        value = block.to_python(self.image.id)

        self.assertEqual(value.id, self.image.id)
        self.assertEqual(value.contextual_alt_text, "Test image")  # Defaulted to title
        self.assertFalse(value.decorative)

    def test_to_python_with_dict(self):
        block = ImageBlock()
        value = {"image": self.image.id, "alt_text": "Sample text", "decorative": False}
        result = block.to_python(value)

        self.assertEqual(result.id, self.image.id)
        self.assertEqual(result.contextual_alt_text, "Sample text")
        self.assertFalse(result.decorative)

    def test_to_python_with_none(self):
        # Like the test_to_python_with_int case, this can occur when a non-required
        # ImageChooserBlock has been changed to an ImageBlock
        block = ImageBlock(required=False)
        value = block.to_python(None)
        self.assertIsNone(value)

    def test_bulk_to_python_with_empty_list(self):
        block = ImageBlock(required=False)
        result = block.bulk_to_python([])
        self.assertEqual(result, [])

    def test_bulk_to_python_with_list_of_none(self):
        block = ImageBlock(required=False)
        result = block.bulk_to_python([None])
        self.assertEqual(result, [None])

    def test_bulk_to_python_with_list_of_ints(self):
        block = ImageBlock(required=False)
        single_image = block.to_python(self.image.id)
        result = block.bulk_to_python([None, self.image.id, self.image.id])
        self.assertEqual(result, [None, single_image, single_image])

    def test_bulk_to_python_with_list_of_dicts(self):
        block = ImageBlock(required=False)
        result = block.bulk_to_python(
            [
                # This is the representation of a non-required ImageBlock left blank,
                # as per test_get_prep_value_for_null_value
                {"image": None, "alt_text": None, "decorative": None},
                {
                    "image": self.image.id,
                    "alt_text": "Custom alt text",
                    "decorative": False,
                },
                {
                    "image": self.image.id,
                    "alt_text": "Different alt text",
                    "decorative": False,
                },
            ]
        )
        self.assertEqual(len(result), 3)
        self.assertIsNone(result[0])
        self.assertEqual(result[1].id, self.image.id)
        self.assertEqual(result[1].contextual_alt_text, "Custom alt text")
        self.assertEqual(result[2].id, self.image.id)
        self.assertEqual(result[2].contextual_alt_text, "Different alt text")

    def test_get_prep_value(self):
        block = ImageBlock()

        self.image.contextual_alt_text = "Custom alt text"
        self.image.decorative = False

        value = block.get_prep_value(self.image)
        self.assertEqual(
            value,
            {
                "image": self.image.id,
                "alt_text": "Custom alt text",
                "decorative": False,
            },
        )

    def test_get_prep_value_for_null_value(self):
        block = ImageBlock(required=False)

        value = block.get_prep_value(None)
        self.assertEqual(
            value,
            {"image": None, "alt_text": None, "decorative": None},
        )

    def test_get_searchable_content(self):
        block = ImageBlock()
        value = {
            "image": self.image.id,  # An id is expected
            "alt_text": "Sample alt text",
            "decorative": False,
        }
        result = block.get_searchable_content(block.to_python(value))

        # check specific attributes
        self.assertEqual(result, ["Sample alt text"])

    def test_required_true(self):
        block = ImageBlock()

        # the inner ImageChooserBlock should appear as required
        image_block_def = JSContext().pack(block)
        image_chooser_block_def = image_block_def["_args"][1][0]
        self.assertTrue(image_chooser_block_def["_args"][2]["required"])

        value = block.to_python(
            {
                "image": None,
                "alt_text": "",
                "decorative": False,
            }
        )
        with self.assertRaises(StructBlockValidationError) as context:
            block.clean(value)

        self.assertIn(
            "This field is required",
            str(context.exception.block_errors["image"]),
        )

    def test_required_false(self):
        block = ImageBlock(required=False)

        # the inner ImageChooserBlock should appear as non-required
        image_block_def = JSContext().pack(block)
        image_chooser_block_def = image_block_def["_args"][1][0]
        self.assertFalse(image_chooser_block_def["_args"][2]["required"])

        value = block.to_python(
            {
                "image": None,
                "alt_text": "",
                "decorative": False,
            }
        )
        self.assertIsNone(block.clean(value))

    def test_get_block_by_content_path(self):
        field = StreamPage._meta.get_field("body")
        page = StreamPage(
            body=field.stream_block.to_python(
                [
                    {
                        "id": "123",
                        "type": "image_with_alt",
                        "value": {
                            "image": self.image.id,
                            "alt_text": "Sample alt text",
                            "decorative": False,
                        },
                    },
                ]
            )
        )
        bound_block = field.get_block_by_content_path(page.body, ["123"])
        self.assertEqual(bound_block.block.name, "image_with_alt")
        self.assertIsInstance(bound_block.value, Image)
        self.assertEqual(bound_block.value.id, self.image.id)

        bound_block = field.get_block_by_content_path(page.body, ["123", "alt_text"])
        self.assertEqual(bound_block.block.name, "alt_text")
        self.assertEqual(bound_block.value, "Sample alt text")

        bound_block = field.get_block_by_content_path(
            page.body, ["123", "does_not_exist"]
        )
        self.assertIsNone(bound_block)


class TestImageBlockComparison(TestCase):
    comparison_class = compare.StreamFieldComparison

    def setUp(self):
        self.image_1 = Image.objects.create(
            title="Test image 1",
            file=get_test_image_file(),
        )

        self.image_2 = Image.objects.create(
            title="Test image 2",
            file=get_test_image_file(),
        )

        self.field = StreamPage._meta.get_field("body")

    def test_hasnt_changed(self):
        field = StreamPage._meta.get_field("body")

        page_1 = StreamPage()
        page_1.body = [
            {
                "type": "image_with_alt",
                "value": {
                    "image": self.image_1.id,
                    "decorative": False,
                    "alt_text": "Some alt text",
                },
                "id": "1",
            },
        ]
        page_2 = StreamPage()
        page_2.body = [
            {
                "type": "image_with_alt",
                "value": {
                    "image": self.image_1.id,
                    "decorative": False,
                    "alt_text": "Some alt text",
                },
                "id": "1",
            },
        ]

        comparison = self.comparison_class(field, page_1, page_2)

        self.assertTrue(comparison.is_field)
        self.assertFalse(comparison.is_child_relation)
        self.assertEqual(comparison.field_label(), "Body")
        htmldiff = comparison.htmldiff()
        self.assertIsInstance(htmldiff, SafeString)
        self.assertIn('class="comparison__child-object"', htmldiff)
        self.assertIn('class="preview-image"', htmldiff)
        self.assertNotIn("deletion", htmldiff)
        self.assertNotIn("addition", htmldiff)
        self.assertFalse(comparison.has_changed())

    def test_has_changed(self):
        field = StreamPage._meta.get_field("body")

        page_1 = StreamPage()
        page_1.body = [
            {
                "type": "image_with_alt",
                "value": {
                    "image": self.image_1.id,
                    "decorative": False,
                    "alt_text": "Some alt text",
                },
                "id": "1",
            },
        ]
        page_2 = StreamPage()
        page_2.body = [
            {
                "type": "image_with_alt",
                "value": {
                    "image": self.image_2.id,
                    "decorative": False,
                    "alt_text": "Some alt text",
                },
                "id": "1",
            },
        ]

        comparison = self.comparison_class(field, page_1, page_2)

        self.assertTrue(comparison.is_field)
        self.assertFalse(comparison.is_child_relation)
        self.assertEqual(comparison.field_label(), "Body")
        htmldiff = comparison.htmldiff()
        self.assertIsInstance(htmldiff, SafeString)
        self.assertIn('class="comparison__child-object"', htmldiff)
        self.assertIn('class="preview-image deletion"', htmldiff)
        self.assertIn('class="preview-image addition"', htmldiff)
        self.assertTrue(comparison.has_changed())

    def test_alt_text_has_changed(self):
        field = StreamPage._meta.get_field("body")

        page_1 = StreamPage()
        page_1.body = [
            {
                "type": "image_with_alt",
                "value": {
                    "image": self.image_1.id,
                    "decorative": False,
                    "alt_text": "a cat playing with some string",
                },
                "id": "1",
            },
        ]
        page_2 = StreamPage()
        page_2.body = [
            {
                "type": "image_with_alt",
                "value": {
                    "image": self.image_1.id,
                    "decorative": False,
                    "alt_text": "a kitten playing with some string",
                },
                "id": "1",
            },
        ]

        comparison = self.comparison_class(field, page_1, page_2)

        self.assertTrue(comparison.is_field)
        self.assertFalse(comparison.is_child_relation)
        self.assertEqual(comparison.field_label(), "Body")
        htmldiff = comparison.htmldiff()
        self.assertIsInstance(htmldiff, SafeString)
        self.assertIn('class="comparison__child-object"', htmldiff)
        self.assertIn(
            '<dd>a <span class="deletion">cat</span><span class="addition">kitten</span> playing with some string</dd>',
            htmldiff,
        )
        self.assertTrue(comparison.has_changed())
