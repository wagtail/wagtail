from types import UnionType
from typing import Literal

from django.db import models
from django.test import SimpleTestCase
from django.test.utils import isolate_apps
from modelcluster.fields import ParentalKey
from ninja import Schema

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
        from pydantic import ValidationError as PydanticValidationError

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
