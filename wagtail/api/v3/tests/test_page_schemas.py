import json
from typing import Annotated, Any, cast, get_args, get_origin

from django.db import models
from django.test import RequestFactory, TestCase
from django.test.utils import isolate_apps

from wagtail.api import APIField
from wagtail.api.v3.schemas import BasePageSchema, read_generator
from wagtail.blocks import Block, CharBlock, StructBlock
from wagtail.fields import StreamField
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
        resolved via the block's own get_api_representation. The schema
        itself is a best-effort per-block-type shape (see blocks_read.py),
        not a bare Any - a well-formed "text" block resolves to a real typed
        item instance, not a plain dict.
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
        self.assertEqual(instance.body[0].type, "text")
        self.assertEqual(instance.body[0].value, "hello")
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


class TestStreamFieldReadSchema(TestCase):
    """Accurate (non-advisory) per-block-type shapes on read - see blocks_read.py.

    Unlike the write side's advisory schema, there's no Any-fallback safety
    net needed here: every case below asserts the resolved value is a real
    typed instance, because the value already came from get_api_representation,
    not untrusted client input.
    """

    def setUp(self):
        self.root_page = Page.objects.get(depth=1)

    def make_stream_page(self, body, slug="stream-read-schema-test"):
        page = StreamPage(title="Stream", slug=slug, body=body)
        self.root_page.add_child(instance=page)
        return page

    def item_union_members(self, schema):
        # list[ItemUnion] where ItemUnion is Annotated[Item1 | Item2 | ...,
        # Field(discriminator=...)] for more than one block, or a bare Item
        # class for exactly one.
        list_of_items = schema.model_fields["body"].annotation
        item_union = get_args(list_of_items)[0]
        if get_origin(item_union) is Annotated:
            item_union = get_args(item_union)[0]
        members = get_args(item_union)
        return members if members else (item_union,)

    def test_container_types_resolve_to_typed_instances(self):
        """
        StreamPage.body covers text/rich_text/product/raw_html/books/
        title_list/image_with_alt in one model - each should resolve to a
        real typed item, not a plain dict.
        """
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        page = self.make_stream_page(
            [
                {"type": "text", "value": "hello"},
                {"type": "product", "value": {"name": "Widget", "price": "9.99"}},
                {"type": "raw_html", "value": "<hr>"},
                {
                    "type": "books",
                    "value": [
                        {"type": "title", "value": "Dune"},
                        {"type": "author", "value": "Frank Herbert"},
                    ],
                },
                {"type": "title_list", "value": ["a", "b"]},
                {
                    "type": "image_with_alt",
                    "value": {
                        "image": image.pk,
                        "decorative": False,
                        "alt_text": "Alt",
                    },
                },
            ]
        )
        schema = read_generator.generate_schema(StreamPage, base_class=BasePageSchema)
        instance = cast(Any, schema.from_orm(page, context={"request": None}))

        text, product, raw_html, books, title_list, image_with_alt = instance.body
        self.assertNotIsInstance(text, dict)
        self.assertEqual(text.value, "hello")
        self.assertEqual(product.value.name, "Widget")
        self.assertEqual(product.value.price, "9.99")
        self.assertEqual(raw_html.value, "<hr>")
        self.assertEqual(books.value[0].value, "Dune")
        self.assertEqual(books.value[1].value, "Frank Herbert")
        self.assertEqual(list(title_list.value), ["a", "b"])
        self.assertEqual(image_with_alt.value.image, image.pk)
        self.assertEqual(image_with_alt.value.alt_text, "Alt")
        json.loads(instance.model_dump_json())

    def test_rich_text_block_respects_rich_text_format(self):
        page = self.make_stream_page(
            [
                {
                    "type": "rich_text",
                    "value": f'<p><a linktype="page" id="{self.root_page.pk}">home</a></p>',
                }
            ],
            slug="stream-read-schema-richtext",
        )
        schema = read_generator.generate_schema(StreamPage, base_class=BasePageSchema)

        rf = RequestFactory()
        db_html_instance = cast(
            Any, schema.from_orm(page, context={"request": rf.get("/")})
        )
        self.assertIn("linktype", db_html_instance.body[0].value)

        html_instance = cast(
            Any,
            schema.from_orm(
                page, context={"request": rf.get("/?rich_text_format=html")}
            ),
        )
        self.assertIn("<a href=", html_instance.body[0].value)
        self.assertNotIn("linktype", html_instance.body[0].value)

    def test_chooser_block_resolves_to_pk(self):
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        page = self.make_stream_page(
            [{"type": "image", "value": image.pk}],
            slug="stream-read-schema-chooser",
        )
        schema = read_generator.generate_schema(StreamPage, base_class=BasePageSchema)
        rf = RequestFactory()

        # StreamPage's "image" block is ExtendedImageChooserBlock, which
        # overrides get_api_representation to branch on a query param - its
        # shape genuinely varies per-request, so the schema types it as Any
        # rather than a bare int, and both request contexts below must
        # resolve correctly through that same Any-typed field.
        plain = cast(Any, schema.from_orm(page, context={"request": rf.get("/")}))
        self.assertEqual(plain.body[0].value, image.pk)

        extended = cast(
            Any,
            schema.from_orm(page, context={"request": rf.get("/?extended=true")}),
        )
        self.assertEqual(extended.body[0].value, {"id": image.pk, "title": image.title})

    def test_table_block_falls_back_to_any(self):
        """
        StreamPage etc. don't cover table_block, so build a throwaway model
        to exercise it directly. TableBlock is a FieldBlock wrapping a plain
        CharField, but its real value is a structured dict - a case that
        can't be modeled precisely, unlike StaticBlock below (whose value is
        always None, a real, precise type, not a fallback).
        """
        from wagtail.contrib.table_block.blocks import TableBlock

        with isolate_apps("wagtail.test.testapp", "wagtail"):
            model = type(
                "TableModel",
                (models.Model,),
                {
                    "body": StreamField([("table", TableBlock())], use_json_field=True),
                    "api_fields": (APIField("body", writable=True),),
                    "__module__": __name__,
                    "Meta": type("Meta", (), {"app_label": "tests"}),
                },
            )
            schema = read_generator.generate_schema(model, base_class=BasePageSchema)
            [item_cls] = self.item_union_members(schema)
            self.assertIs(item_cls.model_fields["value"].annotation, Any)

    def test_static_block_value_is_none_type(self):
        """
        StaticBlock's value is always None - a precisely known type, not an
        Any fallback (unlike TableBlock above).
        """
        from wagtail.blocks import StaticBlock

        with isolate_apps("wagtail.test.testapp", "wagtail"):
            model = type(
                "StaticModel",
                (models.Model,),
                {
                    "body": StreamField(
                        [("static", StaticBlock())], use_json_field=True
                    ),
                    "api_fields": (APIField("body", writable=True),),
                    "__module__": __name__,
                    "Meta": type("Meta", (), {"app_label": "tests"}),
                },
            )
            schema = read_generator.generate_schema(model, base_class=BasePageSchema)
            [item_cls] = self.item_union_members(schema)
            self.assertIs(item_cls.model_fields["value"].annotation, type(None))

    def test_unrecognized_custom_block_falls_back_to_any(self):
        """
        A block class whose get_api_representation we haven't inspected
        must type as Any, not a guessed shape - even a plain leaf Block
        subclass with an arbitrary override.
        """

        class MadeUpBlock(Block):
            def get_api_representation(self, value, context=None):
                return {"totally": "arbitrary", "shape": 123}

        with isolate_apps("wagtail.test.testapp", "wagtail"):
            model = type(
                "UnrecognizedBlockModel",
                (models.Model,),
                {
                    "body": StreamField(
                        [("made_up", MadeUpBlock())], use_json_field=True
                    ),
                    "api_fields": (APIField("body", writable=True),),
                    "__module__": __name__,
                    "Meta": type("Meta", (), {"app_label": "tests"}),
                },
            )
            schema = read_generator.generate_schema(model, base_class=BasePageSchema)
            body_annotation = schema.model_fields["body"].annotation
            item_cls = body_annotation.__args__[0]
            self.assertIs(item_cls.model_fields["value"].annotation, Any)

    def test_plain_custom_struct_subclass_recurses_normally(self):
        """
        A project-defined StructBlock subclass that only adds child blocks
        and doesn't override get_api_representation must still recurse into
        its children normally, not fall back to Any just for being a
        subclass.
        """

        class MyProductBlock(StructBlock):
            def __init__(self, **kwargs):
                super().__init__(
                    [("name", CharBlock()), ("price", CharBlock())], **kwargs
                )

        with isolate_apps("wagtail.test.testapp", "wagtail"):
            model = type(
                "PlainStructSubclassModel",
                (models.Model,),
                {
                    "body": StreamField(
                        [("product", MyProductBlock())], use_json_field=True
                    ),
                    "api_fields": (APIField("body", writable=True),),
                    "__module__": __name__,
                    "Meta": type("Meta", (), {"app_label": "tests"}),
                },
            )
            schema = read_generator.generate_schema(model, base_class=BasePageSchema)
            body_annotation = schema.model_fields["body"].annotation
            item_cls = body_annotation.__args__[0]
            value_cls = item_cls.model_fields["value"].annotation
            self.assertIn("name", value_cls.model_fields)
            self.assertIn("price", value_cls.model_fields)

    def test_class_names_are_unique_per_field(self):
        def make(name):
            return type(
                name,
                (models.Model,),
                {
                    "body": StreamField([("text", CharBlock())], use_json_field=True),
                    "api_fields": (APIField("body", writable=True),),
                    "__module__": __name__,
                    "Meta": type("Meta", (), {"app_label": "tests"}),
                },
            )

        with isolate_apps("wagtail.test.testapp", "wagtail"):
            model_a = make("ReadModelA")
            model_b = make("ReadModelB")
            schema_a = read_generator.generate_schema(
                model_a, base_class=BasePageSchema
            )
            schema_b = read_generator.generate_schema(
                model_b, base_class=BasePageSchema
            )
            item_a = schema_a.model_fields["body"].annotation.__args__[0]
            item_b = schema_b.model_fields["body"].annotation.__args__[0]
            self.assertNotEqual(item_a.__name__, item_b.__name__)
