from types import UnionType
from typing import Annotated, Any, Literal, get_args, get_origin

from django.db import models
from django.test import SimpleTestCase
from django.test.utils import isolate_apps
from modelcluster.fields import ParentalKey
from ninja import Schema
from pydantic import ValidationError as PydanticValidationError

from wagtail.api import APIField
from wagtail.api.v3.schemas.generators.write import (
    InputSchemaGenerator,
    register_default_field_schemas,
)
from wagtail.api.v3.schemas.pages import (
    BASE_PAGE_FIELDS,
    PageCreateBaseSchema,
    PageCreateMetaSchema,
    PageUpdateBaseSchema,
)
from wagtail.blocks import (
    BooleanBlock,
    CharBlock,
    ChoiceBlock,
    ListBlock,
    RichTextBlock,
    StaticBlock,
    StreamBlock,
    StructBlock,
)
from wagtail.contrib.table_block.blocks import TableBlock
from wagtail.fields import StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.test.demosite.models import HomePage, HomePageCarouselItem
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import Page


class TestSchemaGenerator(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.create_generator = InputSchemaGenerator()
        cls.patch_generator = InputSchemaGenerator(for_update=True)
        register_default_field_schemas(cls.create_generator)
        register_default_field_schemas(cls.patch_generator)

    @classmethod
    def generate_page_create_schema(cls, model):
        return cls.create_generator.generate_schema(
            model,
            base_class=PageCreateBaseSchema,
            fields=BASE_PAGE_FIELDS,
            required_fields=("title",),
        )

    @classmethod
    def generate_page_patch_schema(cls, model):
        return cls.patch_generator.generate_schema(
            model,
            base_class=PageUpdateBaseSchema,
            fields=BASE_PAGE_FIELDS,
            required_fields=("title",),
        )


class TestInputSchemaGeneratorIsGeneric(TestSchemaGenerator):
    """
    InputSchemaGenerator itself has no knowledge of pages, ``meta``, or
    ``parent_id``/``type`` - those are supplied by the caller via
    ``base_class``/``fields``/``required_fields``. A plain ``base_class``
    with no ``meta`` field (e.g. a hypothetical non-page model) should build
    a schema with no ``meta`` field at all, rather than assuming one exists.
    """

    def test_generate_schema_without_meta_field_on_base_class(self):
        schema = self.create_generator.generate_schema(
            SimplePage,
            base_class=Schema,
            fields=("title", "slug"),
            required_fields=("title",),
        )

        self.assertNotIn("meta", schema.model_fields)
        self.assertIn("title", schema.model_fields)
        self.assertIn("slug", schema.model_fields)
        self.assertTrue(schema.model_fields["title"].is_required())
        self.assertFalse(schema.model_fields["slug"].is_required())


class TestSchemaMetaNamespacing(TestSchemaGenerator):
    """
    parent_id and type are control fields the create endpoint needs to pick
    a parent page and a page model, not part of any page's own writable
    fields. They're nested under "meta" (mirroring the read-side response's
    own meta.type/meta.slug) specifically so a page model field that happens
    to share one of those names - e.g. a CharField choice literally called
    "type" - can't be silently shadowed by them: "meta" always resolves to
    its own dedicated schema, in a separate namespace from the model's own
    fields, regardless of what those fields are called.
    """

    def test_meta_is_a_dedicated_schema_separate_from_model_fields(self):
        schema = self.generate_page_create_schema(SimplePage)

        meta_annotation = schema.model_fields["meta"].annotation
        self.assertTrue(issubclass(meta_annotation, PageCreateMetaSchema))
        self.assertIn("parent_id", meta_annotation.model_fields)
        self.assertIn("type", meta_annotation.model_fields)

        # The model's own fields live entirely outside "meta" - nothing
        # merges the two namespaces, so a same-named model field (were one
        # to exist) would never be shadowed by parent_id/type.
        self.assertNotIn("parent_id", schema.model_fields)

    def test_create_meta_type_is_narrowed_per_model(self):
        home_schema = self.generate_page_create_schema(HomePage)
        simple_schema = self.generate_page_create_schema(SimplePage)

        home_meta = home_schema.model_fields["meta"].annotation
        simple_meta = simple_schema.model_fields["meta"].annotation

        self.assertEqual(
            home_meta.model_fields["type"].annotation.__args__, ("demosite.HomePage",)
        )
        self.assertEqual(
            simple_meta.model_fields["type"].annotation.__args__, ("tests.SimplePage",)
        )

    def test_patch_meta_type_is_narrowed_per_model_and_optional(self):
        home_schema = self.generate_page_patch_schema(HomePage)
        simple_schema = self.generate_page_patch_schema(SimplePage)

        home_meta = home_schema.model_fields["meta"].annotation
        simple_meta = simple_schema.model_fields["meta"].annotation
        self.assertIsInstance(home_meta, UnionType)
        self.assertIsInstance(simple_meta, UnionType)
        home_meta_schema, home_meta_none = home_meta.__args__
        simple_meta_schema, simple_meta_none = simple_meta.__args__
        self.assertIs(home_meta_none, type(None))
        self.assertIs(simple_meta_none, type(None))

        self.assertEqual(
            home_meta_schema.model_fields["type"].annotation.__args__,
            (Literal["demosite.HomePage"], type(None)),
        )
        self.assertEqual(
            simple_meta_schema.model_fields["type"].annotation.__args__,
            (Literal["tests.SimplePage"], type(None)),
        )


class TestChildRelationSchemaExcludesParentalKey(TestSchemaGenerator):
    """
    A child-relation model's own ``api_fields`` might list its ParentalKey
    field name (e.g. to expose the parent link when reading). The create
    schema must still never accept it as a writable field: the association
    to the page being created is implicit from nesting the item under the
    page's own payload, not something a client should (or even could
    sensibly) supply directly.
    """

    def setUp(self):
        self.original_api_fields = getattr(HomePageCarouselItem, "api_fields", ())
        HomePageCarouselItem.api_fields = (
            "page",
            APIField("caption", writable=True),
            APIField("embed_url", writable=True),
        )
        self.create_generator._child_relation_schema_cache.pop(
            HomePageCarouselItem, None
        )

    def tearDown(self):
        HomePageCarouselItem.api_fields = self.original_api_fields
        self.create_generator._child_relation_schema_cache.pop(
            HomePageCarouselItem, None
        )

    def test_parental_key_listed_in_api_fields_is_not_reintroduced(self):
        schema = self.create_generator.get_child_relation_schema(HomePageCarouselItem)
        self.assertNotIn("page", schema.model_fields)
        self.assertIn("caption", schema.model_fields)
        self.assertIn("embed_url", schema.model_fields)


class TestPatchSchemaPreservesRequiredForeignKeyAlias(TestSchemaGenerator):
    """
    Ensure a writable, non-nullable ``ForeignKey`` on a child relation preserves
    its alias in the patch schema when making it optional, i.e.
    ``related_thing_id`` not ``related_thing``.
    """

    @isolate_apps("wagtail.test.testapp", "wagtail")
    def test_required_foreign_key_alias_survives_in_patch_schema(self):
        class RelatedThing(models.Model):
            class Meta:
                app_label = "tests"

        class PageWithRequiredForeignKeyChild(Page):
            api_fields = (APIField("children", writable=True),)

            class Meta:
                app_label = "tests"

        class InlineChildWithRequiredForeignKey(models.Model):
            page = ParentalKey(
                PageWithRequiredForeignKeyChild,
                on_delete=models.CASCADE,
                related_name="children",
            )
            related_thing = models.ForeignKey(RelatedThing, on_delete=models.CASCADE)

            api_fields = (APIField("related_thing", writable=True),)

            class Meta:
                app_label = "tests"

        create_schema = self.create_generator.generate_schema(
            PageWithRequiredForeignKeyChild,
            base_class=Schema,
            fields=("title",),
        )
        patch_schema = self.patch_generator.generate_schema(
            PageWithRequiredForeignKeyChild,
            base_class=Schema,
            fields=("title",),
        )

        create_children_annotation = create_schema.model_fields["children"].annotation
        patch_children_annotation = patch_schema.model_fields["children"].annotation
        create_child_schema = create_children_annotation.__args__[0]
        create_json_schema = create_child_schema.model_json_schema()
        patch_child_schema = patch_children_annotation.__args__[0]
        patch_json_schema = patch_child_schema.model_json_schema()

        self.assertEqual(
            create_json_schema["properties"]["related_thing_id"]["title"],
            "Related Thing",
        )
        self.assertEqual(
            patch_json_schema["properties"]["related_thing_id"]["title"],
            "Related Thing",
        )


class TestRichTextFieldInputSchema(TestSchemaGenerator):
    @isolate_apps("wagtail.test.testapp", "wagtail")
    def make_model(self, **field_kwargs):
        from wagtail.fields import RichTextField

        class RichTextModel(models.Model):
            body = RichTextField(**field_kwargs)

            api_fields = (APIField("body", writable=True),)

            class Meta:
                app_label = "tests"

        return RichTextModel

    def generate(self, model):
        return self.create_generator.generate_schema(
            model, base_class=Schema, fields=()
        )

    def test_annotation_is_str_or_envelope(self):
        from wagtail.api.v3.schemas.generators.write import RichTextInputSchema

        schema = self.generate(self.make_model())
        annotation = schema.model_fields["body"].annotation
        self.assertIn(str, annotation.__args__)
        self.assertIn(RichTextInputSchema, annotation.__args__)

    def test_plain_string_validates(self):
        schema = self.generate(self.make_model())
        instance = schema(body="<p>x</p>")
        # Normalizes into an envelope
        self.assertEqual(instance.body.format, "db_html")
        self.assertEqual(instance.body.content, "<p>x</p>")

    def test_envelope_validates(self):
        schema = self.generate(self.make_model())
        instance = schema(body={"format": "db_html", "content": "<p>x</p>"})
        self.assertEqual(instance.body.format, "db_html")
        self.assertEqual(instance.body.content, "<p>x</p>")

    def test_normalizes_other_format_into_db_html_envelope(self):
        schema = self.generate(self.make_model())
        instance = schema(body={"format": "db_markdown", "content": "**Hi**"})
        self.assertEqual(instance.body.format, "db_html")
        self.assertEqual(instance.body.content, "<p><b>Hi</b></p>")

    def test_unknown_format_rejected(self):
        schema = self.generate(self.make_model())
        with self.assertRaises(PydanticValidationError):
            schema(body={"format": "markdown", "content": "# Hi"})

    def test_features_in_json_schema_extra(self):
        schema = self.generate(self.make_model(features=["bold", "link"]))
        extra = schema.model_fields["body"].json_schema_extra
        self.assertEqual(extra, {"features": ["bold", "link"]})

    def test_features_default_to_registry_defaults(self):
        from wagtail.rich_text import features as feature_registry

        schema = self.generate(self.make_model())
        extra = schema.model_fields["body"].json_schema_extra
        self.assertEqual(extra, {"features": feature_registry.get_default_features()})


class TestStreamFieldInputSchema(TestSchemaGenerator):
    """Best-effort, advisory-only per-block-type shapes for StreamField.

    Unlike RichTextField's input schema, this never rejects malformed
    input - every generated type is unioned with a bare Any fallback (see
    blocks_write.py) purely for OpenAPI/codegen consumers.
    """

    @isolate_apps("wagtail.test.testapp", "wagtail")
    def make_model(self, block_list, name="StreamModel"):
        attrs = {
            "body": StreamField(block_list, use_json_field=True),
            "api_fields": (APIField("body", writable=True),),
            "__module__": __name__,
            "Meta": type("Meta", (), {"app_label": "tests"}),
        }
        return type(name, (models.Model,), attrs)

    def generate(self, model):
        return self.create_generator.generate_schema(
            model, base_class=Schema, fields=()
        )

    def body_annotation(self, schema):
        return schema.model_fields["body"].annotation

    def item_union_members(self, schema):
        # Union[list[ItemUnion], list[Any]] (top-level annotation is a plain
        # Union, not Annotated - only the outer list carries union_mode via
        # Field(), which isn't part of the type itself).
        annotation = self.body_annotation(schema)
        list_of_items = get_args(annotation)[0]
        # list[ItemUnion]
        item_union = get_args(list_of_items)[0]
        # ItemUnion is Annotated[Item1 | Item2 | ..., Field(discriminator=...)]
        # for more than one block, or a bare Item class for exactly one.
        if get_origin(item_union) is Annotated:
            item_union = get_args(item_union)[0]
        members = get_args(item_union)
        return members if members else (item_union,)

    def test_struct_block_shape(self):
        schema = self.generate(
            self.make_model(
                [
                    (
                        "product",
                        StructBlock([("name", CharBlock()), ("price", CharBlock())]),
                    ),
                ]
            )
        )
        [item_cls] = self.item_union_members(schema)
        value_cls = item_cls.model_fields["value"].annotation
        self.assertIn("name", value_cls.model_fields)
        self.assertIn("price", value_cls.model_fields)

        instance = schema(body=[{"type": "product", "value": {"name": "Widget"}}])
        [item] = instance.body
        self.assertIsInstance(item, item_cls)
        self.assertEqual(item.value.name, "Widget")

    def test_list_block_shape_is_bare_list_not_wrapped(self):
        schema = self.generate(
            self.make_model([("title_list", ListBlock(CharBlock()))])
        )
        instance = schema(body=[{"type": "title_list", "value": ["a", "b"]}])
        [item] = instance.body
        self.assertEqual(list(item.value), ["a", "b"])

    def test_nested_stream_block_shape(self):
        schema = self.generate(
            self.make_model(
                [
                    (
                        "books",
                        StreamBlock([("title", CharBlock()), ("author", CharBlock())]),
                    ),
                ]
            )
        )
        instance = schema(
            body=[
                {
                    "type": "books",
                    "value": [
                        {"type": "title", "value": "Dune"},
                        {"type": "author", "value": "Frank Herbert"},
                    ],
                }
            ]
        )
        [item] = instance.body
        self.assertEqual(item.value[0].value, "Dune")
        self.assertEqual(item.value[1].value, "Frank Herbert")

    def test_richtext_block_reuses_rich_text_input_schema(self):
        from wagtail.api.v3.schemas.generators.write import RichTextInputSchema

        schema = self.generate(self.make_model([("rich_text", RichTextBlock())]))
        [item_cls] = self.item_union_members(schema)
        value_annotation = item_cls.model_fields["value"].annotation
        self.assertIn(RichTextInputSchema, value_annotation.__args__)

        instance = schema(
            body=[
                {
                    "type": "rich_text",
                    "value": {"format": "db_html", "content": "<p>x</p>"},
                }
            ]
        )
        [item] = instance.body
        self.assertEqual(item.value.content, "<p>x</p>")

    def test_chooser_block_maps_to_int(self):
        schema = self.generate(self.make_model([("image", ImageChooserBlock())]))
        instance = schema(body=[{"type": "image", "value": 5}])
        [item] = instance.body
        self.assertEqual(item.value, 5)

    def test_table_block_falls_back_to_any(self):
        schema = self.generate(self.make_model([("table", TableBlock())]))
        [item_cls] = self.item_union_members(schema)
        self.assertIs(item_cls.model_fields["value"].annotation, Any)

        instance = schema(
            body=[{"type": "table", "value": {"data": [[1, 2]], "anything": "goes"}}]
        )
        [item] = instance.body
        self.assertEqual(item.value, {"data": [[1, 2]], "anything": "goes"})

    def test_static_block_shape(self):
        schema = self.generate(self.make_model([("static", StaticBlock())]))
        instance = schema(body=[{"type": "static", "value": None}])
        [item] = instance.body
        self.assertIsNone(item.value)

    def test_choice_block_static_choices_becomes_literal(self):
        schema = self.generate(
            self.make_model([("choice", ChoiceBlock(choices=[("a", "A"), ("b", "B")]))])
        )
        instance = schema(body=[{"type": "choice", "value": "a"}])
        [item] = instance.body
        self.assertEqual(item.value, "a")
        self.assertIsInstance(item, self.item_union_members(schema)[0])

    def test_choice_block_callable_choices_falls_back_to_str_no_db_hit(self):
        def get_choices():
            raise AssertionError("choices callable should not be evaluated")

        schema = self.generate(
            self.make_model([("choice", ChoiceBlock(choices=get_choices))])
        )
        instance = schema(body=[{"type": "choice", "value": "anything"}])
        [item] = instance.body
        self.assertEqual(item.value, "anything")

    def test_malformed_block_type_still_validates(self):
        schema = self.generate(self.make_model([("text", CharBlock())]))
        instance = schema(body=[{"type": "totally_unknown", "value": {"x": 1}}])
        [item] = instance.body
        self.assertEqual(item, {"type": "totally_unknown", "value": {"x": 1}})

    def test_malformed_block_value_still_validates(self):
        schema = self.generate(self.make_model([("text", CharBlock())]))
        instance = schema(body=[{"type": "text", "value": {"nested": "not-a-string"}}])
        [item] = instance.body
        self.assertEqual(item, {"type": "text", "value": {"nested": "not-a-string"}})

    def test_valid_shape_is_still_typed(self):
        schema = self.generate(
            self.make_model([("text", CharBlock()), ("flag", BooleanBlock())])
        )
        instance = schema(
            body=[
                {"type": "text", "value": "hello"},
                {"type": "flag", "value": True},
            ]
        )
        for item in instance.body:
            self.assertNotIsInstance(item, dict)

    def test_class_names_are_unique_per_field(self):
        model_a = self.make_model([("text", CharBlock())], name="StreamModelA")
        model_b = self.make_model([("text", CharBlock())], name="StreamModelB")
        schema_a = self.generate(model_a)
        schema_b = self.generate(model_b)
        [item_a] = self.item_union_members(schema_a)
        [item_b] = self.item_union_members(schema_b)
        self.assertNotEqual(item_a.__name__, item_b.__name__)

    def test_advisory_marker_present_on_body_field(self):
        schema = self.generate(self.make_model([("text", CharBlock())]))
        field_info = schema.model_fields["body"]
        self.assertIn("not enforced", field_info.description.lower())
        self.assertEqual(
            field_info.json_schema_extra, {"x-wagtail-schema-advisory": True}
        )
