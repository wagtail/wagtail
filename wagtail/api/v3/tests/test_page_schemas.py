import json
from types import UnionType
from typing import Any, Union, cast, get_origin

from django.test import TestCase

from wagtail.api import APIField
from wagtail.api.v3.fields import FieldSerializer
from wagtail.api.v3.schemas import BasePageSchema, read_generator
from wagtail.images.api.v3.fields import ImageRenditionDict, ImageRenditionErrorDict
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.test.demosite.models import BlogEntryPage, BlogIndexPage, HomePage
from wagtail.test.testapp.models import StreamPage
from wagtail.test.utils import Page


class TestGeneratePageSchema(TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(depth=1)

    def test_plain_fields_and_reverse_relations(self):
        """
        HomePage.api_fields = ("body", "carousel_items", "related_links").
        Covers: a real field (RichTextField), and two reverse relations whose
        item models themselves mix real fields with a plain property.
        """
        home = HomePage(title="Home", slug="home-schema-test", body="<p>hi</p>")
        home = cast(Any, home)
        self.root_page.add_child(instance=home)
        home.carousel_items.create(
            embed_url="http://example.com/video",
            caption="c1",
            link_external="http://example.com/link",
        )
        home.related_links.create(title="Related", link_external="http://example.com")

        schema = read_generator.generate_schema(HomePage, base_class=BasePageSchema)
        fields = schema.model_fields
        self.assertIn("body", fields)
        self.assertIn("carousel_items", fields)
        self.assertIn("related_links", fields)
        # Inherited from BasePageSchema.
        self.assertIn("id", fields)
        self.assertIn("title", fields)
        self.assertIn("meta", fields)

        instance = cast(Any, schema.from_orm(home, context={"request": None}))
        self.assertEqual(instance.body, "<p>hi</p>")

        [carousel_item] = instance.carousel_items
        self.assertEqual(carousel_item.embed_url, "http://example.com/video")
        self.assertEqual(carousel_item.caption, "c1")
        # "link" is a plain @property on AbstractLinkFields, not a real field.
        self.assertEqual(carousel_item.link, "http://example.com/link")

        [related_link] = instance.related_links
        self.assertEqual(related_link.title, "Related")
        self.assertEqual(related_link.link, "http://example.com")

        # Must be JSON-serializable end to end.
        json.loads(instance.model_dump_json())

    def test_stream_field_uses_get_api_representation(self):
        """
        StreamPage.api_fields = ("body",) where body is a StreamField.
        create_schema can't safely introspect StreamField (it would surface
        the raw StreamValue, which isn't JSON-serializable), so this must be
        resolved via the block's own get_api_representation.
        """
        stream_page = StreamPage(
            title="Stream",
            slug="stream-schema-test",
            body=json.dumps([{"type": "text", "value": "hello"}]),
        )
        stream_page = cast(Any, stream_page)
        self.root_page.add_child(instance=stream_page)

        schema = read_generator.generate_schema(StreamPage, base_class=BasePageSchema)
        instance = cast(Any, schema.from_orm(stream_page, context={"request": None}))

        self.assertIsInstance(instance.body, list)
        self.assertEqual(instance.body[0]["type"], "text")
        self.assertEqual(instance.body[0]["value"], "hello")
        json.loads(instance.model_dump_json())

    def test_custom_serializer_field_uses_compat_shim(self):
        """
        BlogEntryPage.api_fields includes an APIField with a custom
        ImageRenditionField serializer ("feed_image_thumbnail", source
        "feed_image"). This is resolved via a temporary compat shim that
        binds a private copy of the DRF serializer field and defers to its
        own to_representation(), rather than v3 reimplementing it.
        """
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        blog_index = BlogIndexPage(title="Blog", slug="blog-schema-test-2")
        self.root_page.add_child(instance=blog_index)
        entry = BlogEntryPage(
            title="Entry",
            slug="entry-schema-test-2",
            body="<p>body</p>",
            date="2020-01-01",
            feed_image=image,
        )
        blog_index.add_child(instance=entry)

        schema = read_generator.generate_schema(
            BlogEntryPage, base_class=BasePageSchema
        )
        self.assertIn("feed_image_thumbnail", schema.model_fields)

        instance = cast(Any, schema.from_orm(entry, context={"request": None}))
        self.assertEqual(
            instance.feed_image_thumbnail["width"],
            image.get_rendition("fill-300x300").width,
        )
        json.loads(instance.model_dump_json())

    def test_custom_serializer_field_is_none_when_source_is_none(self):
        """
        DRF skips to_representation() entirely when the source attribute is
        None (mirroring API v2's own Serializer.to_representation), rather
        than calling a serializer with no value to work with.
        """
        entry = BlogEntryPage(
            title="Entry",
            slug="entry-schema-test-3",
            body="<p>body</p>",
            date="2020-01-01",
        )
        self.root_page.add_child(instance=entry)

        schema = read_generator.generate_schema(
            BlogEntryPage, base_class=BasePageSchema
        )
        instance = cast(Any, schema.from_orm(entry, context={"request": None}))
        self.assertIsNone(instance.feed_image_thumbnail)

    def test_foreign_key_field(self):
        """
        BlogEntryPage.api_fields includes a real ForeignKey ("feed_image"),
        resolved to a minimal schema exposing the related model's primary
        key and a meta.type label, rather than a full nested schema.
        """
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        blog_index = BlogIndexPage(title="Blog", slug="blog-schema-test")
        self.root_page.add_child(instance=blog_index)
        entry = BlogEntryPage(
            title="Entry",
            slug="entry-schema-test",
            body="<p>body</p>",
            date="2020-01-01",
            feed_image=image,
        )
        blog_index.add_child(instance=entry)

        schema = read_generator.generate_schema(
            BlogEntryPage, base_class=BasePageSchema
        )
        instance = cast(Any, schema.from_orm(entry, context={"request": None}))

        self.assertEqual(instance.feed_image.id, image.pk)
        self.assertEqual(instance.feed_image.meta.type, "wagtailimages.Image")
        json.loads(instance.model_dump_json())

    def test_tag_field_resolves_to_tag_names(self):
        """
        BlogEntryPage.api_fields includes a taggit-backed manager ("tags").
        """
        blog_index = BlogIndexPage(title="Blog", slug="blog-schema-test-tags")
        self.root_page.add_child(instance=blog_index)
        entry = BlogEntryPage(
            title="Entry",
            slug="entry-schema-test-tags",
            body="<p>body</p>",
            date="2020-01-01",
        )
        blog_index.add_child(instance=entry)
        entry.tags.add("wagtail", "python")

        schema = read_generator.generate_schema(
            BlogEntryPage, base_class=BasePageSchema
        )
        self.assertEqual(schema.model_fields["tags"].annotation, list[str])

        instance = cast(Any, schema.from_orm(entry, context={"request": None}))
        self.assertEqual(sorted(instance.tags), ["python", "wagtail"])
        json.loads(instance.model_dump_json())

    def test_tag_field_is_empty_list_when_untagged(self):
        """
        A page with no tags should resolve to an empty list rather than
        None or a lookup error.
        """
        blog_index = BlogIndexPage(title="Blog", slug="blog-schema-test-no-tags")
        self.root_page.add_child(instance=blog_index)
        entry = BlogEntryPage(
            title="Entry",
            slug="entry-schema-test-no-tags",
            body="<p>body</p>",
            date="2020-01-01",
        )
        blog_index.add_child(instance=entry)

        schema = read_generator.generate_schema(
            BlogEntryPage, base_class=BasePageSchema
        )
        instance = cast(Any, schema.from_orm(entry, context={"request": None}))
        self.assertEqual(instance.tags, [])

    def test_field_serializer_uses_to_representation(self):
        """
        BlogEntryPage.api_fields includes an APIField with a v3
        ImageRenditionField serializer ("feed_image_thumbnail_serializer",
        source "feed_image"). Resolved directly via the field serializer's own
        to_representation(), without DRF.
        """
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        blog_index = BlogIndexPage(title="Blog", slug="blog-schema-test-3")
        self.root_page.add_child(instance=blog_index)
        entry = BlogEntryPage(
            title="Entry",
            slug="entry-schema-test-4",
            body="<p>body</p>",
            date="2020-01-01",
            feed_image=image,
        )
        blog_index.add_child(instance=entry)

        schema = read_generator.generate_schema(
            BlogEntryPage, base_class=BasePageSchema
        )
        self.assertIn("feed_image_thumbnail_serializer", schema.model_fields)

        instance = cast(Any, schema.from_orm(entry, context={"request": None}))
        self.assertEqual(
            instance.feed_image_thumbnail_serializer["width"],
            image.get_rendition("fill-300x300").width,
        )
        json.loads(instance.model_dump_json())

    def test_field_serializer_is_none_when_source_is_none(self):
        entry = BlogEntryPage(
            title="Entry",
            slug="entry-schema-test-5",
            body="<p>body</p>",
            date="2020-01-01",
        )
        self.root_page.add_child(instance=entry)

        schema = read_generator.generate_schema(
            BlogEntryPage, base_class=BasePageSchema
        )
        instance = cast(Any, schema.from_orm(entry, context={"request": None}))
        self.assertIsNone(instance.feed_image_thumbnail_serializer)

    def test_field_serializer_annotation_from_return_type(self):
        """
        The schema annotation is derived from to_representation()'s return
        type hint, unioned with None since the source may resolve to None.
        """
        schema = read_generator.generate_schema(
            BlogEntryPage, base_class=BasePageSchema
        )
        annotation = schema.model_fields["feed_image_thumbnail_serializer"].annotation
        args = {
            arg for arg in getattr(annotation, "__args__", ()) if arg is not type(None)
        }
        self.assertIn(get_origin(annotation), (Union, UnionType))
        self.assertEqual(args, {ImageRenditionDict, ImageRenditionErrorDict})

    def test_unannotated_field_serializer_annotation_falls_back_to_any(self):
        class UnannotatedFieldSerializer(FieldSerializer):
            def to_representation(self, value):
                return str(value)

        field = UnannotatedFieldSerializer(source="title")
        field_schema = type(read_generator)._field_serializer_schema(
            APIField("title", serializer=field)
        )
        annotation, default, resolver = field_schema
        self.assertIn(get_origin(annotation), (Union, UnionType))
        self.assertIn(Any, getattr(annotation, "__args__", ()))
        self.assertIsNone(default)
        obj = type("Obj", (), {"title": "Hi"})()
        resolve = cast(Any, resolver)
        self.assertEqual(resolve(obj, {}), "Hi")
