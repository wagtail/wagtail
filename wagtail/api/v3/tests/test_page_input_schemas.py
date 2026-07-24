from django.db import models
from django.db.models import ForeignKey
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.test import SimpleTestCase
from django.test.utils import isolate_apps
from modelcluster.fields import ParentalKey
from ninja import Schema

from wagtail.api import APIField
from wagtail.api.v3.schemas import create_generator
from wagtail.api.v3.schemas.generators.write import (
    InputSchemaGenerator,
    child_relation_schema,
    foreign_key_schema,
)
from wagtail.api.v3.schemas.pages import (
    BASE_PAGE_FIELDS,
    PageCreateBaseSchema,
    PageCreateMetaSchema,
)
from wagtail.models import Page
from wagtail.test.demosite.models import HomePage, HomePageCarouselItem
from wagtail.test.testapp.models import SimplePage


def generate_page_input_schema(model):
    return create_generator.generate_schema(
        model,
        base_class=PageCreateBaseSchema,
        fields=BASE_PAGE_FIELDS,
        required_fields=("title",),
    )


class TestInputSchemaGeneratorIsGeneric(SimpleTestCase):
    """
    InputSchemaGenerator itself has no knowledge of pages, ``meta``, or
    ``parent_id``/``type`` - those are supplied by the caller via
    ``base_class``/``fields``/``required_fields``. A plain ``base_class``
    with no ``meta`` field (e.g. a hypothetical non-page model) should build
    a schema with no ``meta`` field at all, rather than assuming one exists.
    """

    def test_generate_schema_without_meta_field_on_base_class(self):
        schema = create_generator.generate_schema(
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


class TestPageCreateSchemaMetaNamespacing(SimpleTestCase):
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
        schema = generate_page_input_schema(SimplePage)

        meta_annotation = schema.model_fields["meta"].annotation
        self.assertTrue(issubclass(meta_annotation, PageCreateMetaSchema))
        self.assertIn("parent_id", meta_annotation.model_fields)
        self.assertIn("type", meta_annotation.model_fields)

        # The model's own fields live entirely outside "meta" - nothing
        # merges the two namespaces, so a same-named model field (were one
        # to exist) would never be shadowed by parent_id/type.
        self.assertNotIn("parent_id", schema.model_fields)

    def test_meta_type_is_narrowed_per_model(self):
        home_schema = generate_page_input_schema(HomePage)
        simple_schema = generate_page_input_schema(SimplePage)

        home_meta = home_schema.model_fields["meta"].annotation
        simple_meta = simple_schema.model_fields["meta"].annotation

        self.assertEqual(
            home_meta.model_fields["type"].annotation.__args__, ("demosite.HomePage",)
        )
        self.assertEqual(
            simple_meta.model_fields["type"].annotation.__args__, ("tests.SimplePage",)
        )


class TestChildRelationSchemaExcludesParentalKey(SimpleTestCase):
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
        create_generator._child_relation_schema_cache.pop(HomePageCarouselItem, None)

    def tearDown(self):
        HomePageCarouselItem.api_fields = self.original_api_fields
        create_generator._child_relation_schema_cache.pop(HomePageCarouselItem, None)

    def test_parental_key_listed_in_api_fields_is_not_reintroduced(self):
        schema = create_generator.get_child_relation_schema(HomePageCarouselItem)

        self.assertNotIn("page", schema.model_fields)
        self.assertIn("caption", schema.model_fields)
        self.assertIn("embed_url", schema.model_fields)


class TestPatchSchemaPreservesRequiredForeignKeyAlias(SimpleTestCase):
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

        # Fresh generator instances to avoid polluting the global instance
        create_gen = InputSchemaGenerator()
        create_gen.register_field_schema(ForeignObjectRel, child_relation_schema)
        create_gen.register_field_schema(ForeignKey, foreign_key_schema)
        patch_gen = InputSchemaGenerator(for_update=True)
        patch_gen.register_field_schema(ForeignObjectRel, child_relation_schema)
        patch_gen.register_field_schema(ForeignKey, foreign_key_schema)

        create_schema = create_gen.generate_schema(
            PageWithRequiredForeignKeyChild,
            base_class=Schema,
            fields=("title",),
        )
        patch_schema = patch_gen.generate_schema(
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
