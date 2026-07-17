from django.test import SimpleTestCase

from wagtail.api.v3.schemas.input_generator import PageCreateMetaSchema, input_generator
from wagtail.test.demosite.models import HomePage
from wagtail.test.testapp.models import SimplePage


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
        schema = input_generator.generate_schema(SimplePage)

        meta_annotation = schema.model_fields["meta"].annotation
        self.assertTrue(issubclass(meta_annotation, PageCreateMetaSchema))
        self.assertIn("parent_id", meta_annotation.model_fields)
        self.assertIn("type", meta_annotation.model_fields)

        # The model's own fields live entirely outside "meta" - nothing
        # merges the two namespaces, so a same-named model field (were one
        # to exist) would never be shadowed by parent_id/type.
        self.assertNotIn("parent_id", schema.model_fields)

    def test_meta_type_is_narrowed_per_model(self):
        home_schema = input_generator.generate_schema(HomePage)
        simple_schema = input_generator.generate_schema(SimplePage)

        home_meta = home_schema.model_fields["meta"].annotation
        simple_meta = simple_schema.model_fields["meta"].annotation

        self.assertEqual(
            home_meta.model_fields["type"].annotation.__args__, ("demosite.HomePage",)
        )
        self.assertEqual(
            simple_meta.model_fields["type"].annotation.__args__, ("tests.SimplePage",)
        )
