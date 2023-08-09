import json

from django.apps import apps
from django.db import connection, models
from django.template import Context, Template, engines
from django.test import TestCase, skipUnlessDBFeature
from django.utils.safestring import SafeString

from wagtail import blocks
from wagtail.blocks import StreamBlockValidationError, StreamValue
from wagtail.fields import StreamField
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.rich_text import RichText
from wagtail.signal_handlers import disable_reference_index_auto_update
from wagtail.test.testapp.models import (
    JSONBlockCountsStreamModel,
    JSONMinMaxCountStreamModel,
    JSONStreamModel,
)


class TestLazyStreamField(TestCase):
    model = JSONStreamModel

    def setUp(self):
        self.image = Image.objects.create(
            title="Test image", file=get_test_image_file()
        )
        self.with_image = self.model.objects.create(
            body=json.dumps(
                [
                    {"type": "image", "value": self.image.pk},
                    {"type": "text", "value": "foo"},
                ]
            )
        )
        self.no_image = self.model.objects.create(
            body=json.dumps([{"type": "text", "value": "foo"}])
        )
        self.three_items = self.model.objects.create(
            body=json.dumps(
                [
                    {"type": "text", "value": "foo"},
                    {"type": "image", "value": self.image.pk},
                    {"type": "text", "value": "bar"},
                ]
            )
        )

    def test_lazy_load(self):
        """
        Getting a single item should lazily load the StreamField, only
        accessing the database once the StreamField is accessed
        """
        with self.assertNumQueries(1):
            # Get the instance. The StreamField should *not* load the image yet
            instance = self.model.objects.get(pk=self.with_image.pk)

        with self.assertNumQueries(0):
            # Access the body. The StreamField should still not get the image.
            body = instance.body

        with self.assertNumQueries(1):
            # Access the image item from the stream. The image is fetched now
            body[0].value

        with self.assertNumQueries(0):
            # Everything has been fetched now, no further database queries.
            self.assertEqual(body[0].value, self.image)
            self.assertEqual(body[1].value, "foo")

    def test_slice(self):
        with self.assertNumQueries(1):
            instance = self.model.objects.get(pk=self.three_items.pk)

        with self.assertNumQueries(1):
            # Access the image item from the stream. The image is fetched now
            instance.body[1].value

        with self.assertNumQueries(0):
            # taking a slice of a StreamValue should re-use already-fetched values
            values = [block.value for block in instance.body[1:3]]
            self.assertEqual(values, [self.image, "bar"])

        with self.assertNumQueries(0):
            # test slicing with negative indexing
            values = [block.value for block in instance.body[-2:]]
            self.assertEqual(values, [self.image, "bar"])

        with self.assertNumQueries(0):
            # test slicing with skips
            values = [block.value for block in instance.body[0:3:2]]
            self.assertEqual(values, ["foo", "bar"])

    def test_lazy_load_no_images(self):
        """
        Getting a single item whose StreamField never accesses the database
        should behave as expected.
        """
        with self.assertNumQueries(1):
            # Get the instance, nothing else
            instance = self.model.objects.get(pk=self.no_image.pk)

        with self.assertNumQueries(0):
            # Access the body. The StreamField has no images, so nothing should
            # happen
            body = instance.body
            self.assertEqual(body[0].value, "foo")

    def test_lazy_load_queryset(self):
        """
        Ensure that lazy loading StreamField works when gotten as part of a
        queryset list
        """
        with self.assertNumQueries(1):
            instances = self.model.objects.filter(
                pk__in=[self.with_image.pk, self.no_image.pk]
            )
            instances_lookup = {instance.pk: instance for instance in instances}

        with self.assertNumQueries(1):
            instances_lookup[self.with_image.pk].body[0]

        with self.assertNumQueries(0):
            instances_lookup[self.no_image.pk].body[0]

    def test_lazy_load_queryset_bulk(self):
        """
        Ensure that lazy loading StreamField works when gotten as part of a
        queryset list
        """
        file_obj = get_test_image_file()
        image_1 = Image.objects.create(title="Test image 1", file=file_obj)
        image_3 = Image.objects.create(title="Test image 3", file=file_obj)

        with_image = self.model.objects.create(
            body=json.dumps(
                [
                    {"type": "image", "value": image_1.pk},
                    {"type": "image", "value": None},
                    {"type": "image", "value": image_3.pk},
                    {"type": "text", "value": "foo"},
                ]
            )
        )

        with self.assertNumQueries(1):
            instance = self.model.objects.get(pk=with_image.pk)

        # Prefetch all image blocks
        with self.assertNumQueries(1):
            instance.body[0]

        # 1. Further image block access should not execute any db lookups
        # 2. The blank block '1' should be None.
        # 3. The values should be in the original order.
        with self.assertNumQueries(0):
            assert instance.body[0].value.title == "Test image 1"
            assert instance.body[1].value is None
            assert instance.body[2].value.title == "Test image 3"

    def test_lazy_load_get_prep_value(self):
        """
        Saving a lazy StreamField that hasn't had its data accessed should not
        cause extra database queries by loading and then re-saving block values.
        Instead the initial JSON stream data should be written back for any
        blocks that have not been accessed.
        """
        with self.assertNumQueries(1):
            instance = self.model.objects.get(pk=self.with_image.pk)

        # Expect a single UPDATE to update the model, without any additional
        # SELECT related to the image block that has not been accessed.
        with disable_reference_index_auto_update():
            with self.assertNumQueries(1):
                instance.save()


class TestSystemCheck(TestCase):
    def tearDown(self):
        # unregister InvalidStreamModel from the overall model registry
        # so that it doesn't break tests elsewhere
        for package in ("wagtailcore", "wagtail.tests"):
            try:
                del apps.all_models[package]["invalidstreammodel"]
            except KeyError:
                pass
        apps.clear_cache()

    def test_system_check_validates_block(self):
        class InvalidStreamModel(models.Model):
            body = StreamField(
                [
                    ("heading", blocks.CharBlock()),
                    ("rich text", blocks.RichTextBlock()),
                ],
                use_json_field=True,
            )

        errors = InvalidStreamModel.check()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].id, "wagtailcore.E001")
        self.assertEqual(errors[0].hint, "Block names cannot contain spaces")
        self.assertEqual(errors[0].obj, InvalidStreamModel._meta.get_field("body"))


class TestStreamValueAccess(TestCase):
    def setUp(self):
        self.json_body = JSONStreamModel.objects.create(
            body=json.dumps([{"type": "text", "value": "foo"}])
        )

    def test_can_assign_as_list(self):
        self.json_body.body = [("rich_text", RichText("<h2>hello world</h2>"))]
        self.json_body.save()

        # the body should now be a stream consisting of a single rich_text block
        fetched_body = JSONStreamModel.objects.get(id=self.json_body.id).body
        self.assertIsInstance(fetched_body, StreamValue)
        self.assertEqual(len(fetched_body), 1)
        self.assertIsInstance(fetched_body[0].value, RichText)
        self.assertEqual(fetched_body[0].value.source, "<h2>hello world</h2>")

    def test_can_append(self):
        self.json_body.body.append(("text", "bar"))
        self.json_body.save()

        fetched_body = JSONStreamModel.objects.get(id=self.json_body.id).body
        self.assertIsInstance(fetched_body, StreamValue)
        self.assertEqual(len(fetched_body), 2)
        self.assertEqual(fetched_body[0].block_type, "text")
        self.assertEqual(fetched_body[0].value, "foo")
        self.assertEqual(fetched_body[1].block_type, "text")
        self.assertEqual(fetched_body[1].value, "bar")


class TestStreamFieldRenderingBase(TestCase):
    model = JSONStreamModel

    def setUp(self):
        self.image = Image.objects.create(
            title="Test image", file=get_test_image_file()
        )

        self.instance = self.model.objects.create(
            body=json.dumps(
                [
                    {"type": "rich_text", "value": "<p>Rich text</p>"},
                    {"type": "rich_text", "value": "<p>Привет, Микола</p>"},
                    {"type": "image", "value": self.image.pk},
                    {"type": "text", "value": "Hello, World!"},
                ]
            )
        )

        img_tag = self.image.get_rendition("original").img_tag()
        self.expected = "".join(
            [
                '<div class="block-rich_text"><p>Rich text</p></div>',
                '<div class="block-rich_text"><p>Привет, Микола</p></div>',
                f'<div class="block-image">{img_tag}</div>',
                '<div class="block-text">Hello, World!</div>',
            ]
        )


class TestStreamFieldRendering(TestStreamFieldRenderingBase):
    def test_to_string(self):
        rendered = str(self.instance.body)
        self.assertHTMLEqual(rendered, self.expected)
        self.assertIsInstance(rendered, SafeString)

    def test___html___access(self):
        rendered = self.instance.body.__html__()
        self.assertHTMLEqual(rendered, self.expected)
        self.assertIsInstance(rendered, SafeString)


class TestStreamFieldDjangoRendering(TestStreamFieldRenderingBase):
    def render(self, string, context):
        return Template(string).render(Context(context))

    def test_render(self):
        rendered = self.render("{{ instance.body }}", {"instance": self.instance})
        self.assertHTMLEqual(rendered, self.expected)


class TestStreamFieldJinjaRendering(TestStreamFieldRenderingBase):
    def setUp(self):
        super().setUp()
        self.engine = engines["jinja2"]

    def render(self, string, context):
        return self.engine.from_string(string).render(context)

    def test_render(self):
        rendered = self.render("{{ instance.body }}", {"instance": self.instance})
        self.assertHTMLEqual(rendered, self.expected)


class TestRequiredStreamField(TestCase):
    def test_non_blank_field_is_required(self):
        # passing a block list
        field = StreamField(
            [("paragraph", blocks.CharBlock())],
            blank=False,
            use_json_field=True,
        )
        self.assertTrue(field.stream_block.required)
        with self.assertRaises(StreamBlockValidationError):
            field.stream_block.clean([])

        class MyStreamBlock(blocks.StreamBlock):
            paragraph = blocks.CharBlock()

            class Meta:
                required = False

        # passing a block instance
        field = StreamField(MyStreamBlock(), blank=False, use_json_field=True)
        self.assertTrue(field.stream_block.required)
        with self.assertRaises(StreamBlockValidationError):
            field.stream_block.clean([])

        field = StreamField(
            MyStreamBlock(required=False),
            blank=False,
            use_json_field=True,
        )
        self.assertTrue(field.stream_block.required)
        with self.assertRaises(StreamBlockValidationError):
            field.stream_block.clean([])

        # passing a block class
        field = StreamField(MyStreamBlock, blank=False, use_json_field=True)
        self.assertTrue(field.stream_block.required)
        with self.assertRaises(StreamBlockValidationError):
            field.stream_block.clean([])

    def test_blank_false_is_implied_by_default(self):
        # passing a block list
        field = StreamField([("paragraph", blocks.CharBlock())], use_json_field=True)
        self.assertTrue(field.stream_block.required)
        with self.assertRaises(StreamBlockValidationError):
            field.stream_block.clean([])

        class MyStreamBlock(blocks.StreamBlock):
            paragraph = blocks.CharBlock()

            class Meta:
                required = False

        # passing a block instance
        field = StreamField(MyStreamBlock(), use_json_field=True)
        self.assertTrue(field.stream_block.required)
        with self.assertRaises(StreamBlockValidationError):
            field.stream_block.clean([])

        field = StreamField(MyStreamBlock(required=False), use_json_field=True)
        self.assertTrue(field.stream_block.required)
        with self.assertRaises(StreamBlockValidationError):
            field.stream_block.clean([])

        # passing a block class
        field = StreamField(MyStreamBlock, use_json_field=True)
        self.assertTrue(field.stream_block.required)
        with self.assertRaises(StreamBlockValidationError):
            field.stream_block.clean([])

    def test_blank_field_is_not_required(self):
        # passing a block list
        field = StreamField(
            [("paragraph", blocks.CharBlock())],
            blank=True,
            use_json_field=True,
        )
        self.assertFalse(field.stream_block.required)
        field.stream_block.clean([])  # no validation error on empty stream

        class MyStreamBlock(blocks.StreamBlock):
            paragraph = blocks.CharBlock()

            class Meta:
                required = True

        # passing a block instance
        field = StreamField(MyStreamBlock(), blank=True, use_json_field=True)
        self.assertFalse(field.stream_block.required)
        field.stream_block.clean([])  # no validation error on empty stream

        field = StreamField(
            MyStreamBlock(required=True), blank=True, use_json_field=True
        )
        self.assertFalse(field.stream_block.required)
        field.stream_block.clean([])  # no validation error on empty stream

        # passing a block class
        field = StreamField(MyStreamBlock, blank=True, use_json_field=True)
        self.assertFalse(field.stream_block.required)
        field.stream_block.clean([])  # no validation error on empty stream


class TestStreamFieldCountValidation(TestCase):
    def setUp(self):
        self.image = Image.objects.create(
            title="Test image", file=get_test_image_file()
        )

        self.rich_text_body = {"type": "rich_text", "value": "<p>Rich text</p>"}
        self.image_body = {"type": "image", "value": self.image.pk}
        self.text_body = {"type": "text", "value": "Hello, World!"}

    def test_minmax_pass_to_block(self):
        instance = JSONMinMaxCountStreamModel.objects.create(body=json.dumps([]))
        internal_block = instance.body.stream_block

        self.assertEqual(internal_block.meta.min_num, 2)
        self.assertEqual(internal_block.meta.max_num, 5)

    def test_counts_pass_to_block(self):
        instance = JSONBlockCountsStreamModel.objects.create(body=json.dumps([]))
        block_counts = instance.body.stream_block.meta.block_counts

        self.assertEqual(block_counts.get("text"), {"min_num": 1})
        self.assertEqual(block_counts.get("rich_text"), {"max_num": 1})
        self.assertEqual(block_counts.get("image"), {"min_num": 1, "max_num": 1})

    def test_minimum_count(self):
        # Single block should fail validation
        body = [self.rich_text_body]
        instance = JSONMinMaxCountStreamModel.objects.create(body=json.dumps(body))
        with self.assertRaises(StreamBlockValidationError) as catcher:
            instance.body.stream_block.clean(instance.body)
        self.assertEqual(
            catcher.exception.as_json_data(),
            {"messages": ["The minimum number of items is 2"]},
        )

        # 2 blocks okay
        body = [self.rich_text_body, self.text_body]
        instance = JSONMinMaxCountStreamModel.objects.create(body=json.dumps(body))
        self.assertTrue(instance.body.stream_block.clean(instance.body))

    def test_maximum_count(self):
        # 5 blocks okay
        body = [self.rich_text_body] * 5
        instance = JSONMinMaxCountStreamModel.objects.create(body=json.dumps(body))
        self.assertTrue(instance.body.stream_block.clean(instance.body))

        # 6 blocks should fail validation
        body = [self.rich_text_body, self.text_body] * 3
        instance = JSONMinMaxCountStreamModel.objects.create(body=json.dumps(body))
        with self.assertRaises(StreamBlockValidationError) as catcher:
            instance.body.stream_block.clean(instance.body)
        self.assertEqual(
            catcher.exception.as_json_data(),
            {"messages": ["The maximum number of items is 5"]},
        )

    def test_block_counts_minimums(self):
        JSONBlockCountsStreamModel.objects.create(body=json.dumps([]))

        # Zero blocks should fail validation (requires one text, one image)
        instance = JSONBlockCountsStreamModel.objects.create(body=json.dumps([]))
        with self.assertRaises(StreamBlockValidationError) as catcher:
            instance.body.stream_block.clean(instance.body)
        errors = catcher.exception.as_json_data()["messages"]
        self.assertIn("This field is required.", errors)
        self.assertIn("Text: The minimum number of items is 1", errors)
        self.assertIn("Image: The minimum number of items is 1", errors)
        self.assertEqual(len(errors), 3)

        # One plain text should fail validation
        body = [self.text_body]
        instance = JSONBlockCountsStreamModel.objects.create(body=json.dumps(body))
        with self.assertRaises(StreamBlockValidationError) as catcher:
            instance.body.stream_block.clean(instance.body)
        self.assertEqual(
            catcher.exception.as_json_data(),
            {"messages": ["Image: The minimum number of items is 1"]},
        )

        # One text, one image should be okay
        body = [self.text_body, self.image_body]
        instance = JSONBlockCountsStreamModel.objects.create(body=json.dumps(body))
        self.assertTrue(instance.body.stream_block.clean(instance.body))

    def test_block_counts_maximums(self):
        JSONBlockCountsStreamModel.objects.create(body=json.dumps([]))

        # Base is one text, one image
        body = [self.text_body, self.image_body]
        instance = JSONBlockCountsStreamModel.objects.create(body=json.dumps(body))
        self.assertTrue(instance.body.stream_block.clean(instance.body))

        # Two rich text should error
        body = [
            self.text_body,
            self.image_body,
            self.rich_text_body,
            self.rich_text_body,
        ]
        instance = JSONBlockCountsStreamModel.objects.create(body=json.dumps(body))

        with self.assertRaises(StreamBlockValidationError):
            instance.body.stream_block.clean(instance.body)

        # Two images should error
        body = [self.text_body, self.image_body, self.image_body]
        instance = JSONBlockCountsStreamModel.objects.create(body=json.dumps(body))

        with self.assertRaises(StreamBlockValidationError) as catcher:
            instance.body.stream_block.clean(instance.body)
        self.assertEqual(
            catcher.exception.as_json_data(),
            {"messages": ["Image: The maximum number of items is 1"]},
        )

        # One text, one rich, one image should be okay
        body = [self.text_body, self.image_body, self.rich_text_body]
        instance = JSONBlockCountsStreamModel.objects.create(body=json.dumps(body))
        self.assertTrue(instance.body.stream_block.clean(instance.body))

    def test_streamfield_count_argument_precedence(self):
        class TestStreamBlock(blocks.StreamBlock):
            heading = blocks.CharBlock()
            paragraph = blocks.RichTextBlock()

            class Meta:
                min_num = 2
                max_num = 5
                block_counts = {"heading": {"max_num": 1}}

        # args being picked up from the class definition
        field = StreamField(TestStreamBlock, use_json_field=True)
        self.assertEqual(field.stream_block.meta.min_num, 2)
        self.assertEqual(field.stream_block.meta.max_num, 5)
        self.assertEqual(field.stream_block.meta.block_counts["heading"]["max_num"], 1)

        # args being overridden by StreamField
        field = StreamField(
            TestStreamBlock,
            min_num=3,
            max_num=6,
            block_counts={"heading": {"max_num": 2}},
            use_json_field=True,
        )
        self.assertEqual(field.stream_block.meta.min_num, 3)
        self.assertEqual(field.stream_block.meta.max_num, 6)
        self.assertEqual(field.stream_block.meta.block_counts["heading"]["max_num"], 2)

        # passing None from StreamField should cancel limits set at the block level
        field = StreamField(
            TestStreamBlock,
            min_num=None,
            max_num=None,
            block_counts=None,
            use_json_field=True,
        )
        self.assertIsNone(field.stream_block.meta.min_num)
        self.assertIsNone(field.stream_block.meta.max_num)
        self.assertIsNone(field.stream_block.meta.block_counts)


class TestJSONStreamField(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.instance = JSONStreamModel.objects.create(
            body=[{"type": "text", "value": "foo"}],
        )

    def test_internal_type(self):
        json = StreamField([("paragraph", blocks.CharBlock())], use_json_field=True)
        self.assertEqual(json.get_internal_type(), "JSONField")

    def test_json_body_equals_to_text_body(self):
        instance_text = JSONStreamModel.objects.create(
            body=json.dumps([{"type": "text", "value": "foo"}]),
        )
        self.assertEqual(
            instance_text.body.render_as_block(), self.instance.body.render_as_block()
        )

    def test_json_body_create_preserialised_value(self):
        instance_preserialised = JSONStreamModel.objects.create(
            body=json.dumps([{"type": "text", "value": "foo"}]),
        )
        self.assertEqual(
            instance_preserialised.body.render_as_block(),
            self.instance.body.render_as_block(),
        )

    @skipUnlessDBFeature("supports_json_field_contains")
    def test_json_contains_lookup(self):
        value = {"value": "foo"}
        if connection.features.json_key_contains_list_matching_requires_list:
            value = [value]
        instance = JSONStreamModel.objects.filter(body__contains=value).first()
        self.assertIsNotNone(instance)
        self.assertEqual(instance.id, self.instance.id)
