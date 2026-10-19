from typing import Any, cast, get_args
from unittest import mock

from django.test import SimpleTestCase
from ninja import Schema
from pydantic import TypeAdapter

from wagtail.api.v3.schemas import BasePageSchema
from wagtail.api.v3.schemas.generators import read, write
from wagtail.api.v3.schemas.generators.blocks import (
    BlockSchemaBuilder,
    register_default_block_schemas,
)
from wagtail.blocks import (
    CharBlock,
    ChoiceBlock,
    IntegerBlock,
    ListBlock,
    MultipleChoiceBlock,
    StreamBlock,
    StructBlock,
)
from wagtail.contrib.table_block.blocks import TableBlock
from wagtail.images.blocks import ImageBlock, ImageChooserBlock
from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail.test.testapp.models import (
    AdvertWithCustomUUIDPrimaryKey,
    ExtendedImageChooserBlock,
    StreamPage,
)

NULLABLE_STRING = {"anyOf": [{"type": "string"}, {"type": "null"}]}
NULLABLE_INTEGER = {"anyOf": [{"type": "integer"}, {"type": "null"}]}


class PersonBlock(StructBlock):
    name = CharBlock()


class BlockSchemaTestMixin:
    for_input = False

    def json_schema(self, block):
        builder = BlockSchemaBuilder(for_input=self.for_input)
        register_default_block_schemas(builder)
        return TypeAdapter(builder.get_type(block, "Test")).json_schema(
            mode="validation" if self.for_input else "serialization"
        )

    def value_schema(self, block):
        schema = self.json_schema(StreamBlock([("block", block)]))
        suffix = "Input" if self.for_input else ""
        value = schema["$defs"][f"TestBlockItem{suffix}"]["properties"]["value"]
        value.pop("title")
        return value


class TestBlockSchema(BlockSchemaTestMixin, SimpleTestCase):
    def test_struct_block(self):
        schema = self.json_schema(
            StructBlock([("name", CharBlock()), ("count", IntegerBlock())])
        )
        self.assertEqual(schema["title"], "Test")
        self.assertEqual(schema["required"], ["name", "count"])
        self.assertEqual(
            schema["properties"]["name"]["anyOf"], NULLABLE_STRING["anyOf"]
        )
        self.assertEqual(
            schema["properties"]["count"]["anyOf"], NULLABLE_INTEGER["anyOf"]
        )

    def test_stream_block(self):
        schema = self.json_schema(
            StreamBlock([("heading", CharBlock()), ("person", PersonBlock())])
        )
        self.assertEqual(schema["type"], "array")
        self.assertEqual(
            schema["items"]["discriminator"]["mapping"],
            {
                "heading": "#/$defs/TestHeadingItem",
                "person": "#/$defs/TestPersonItem",
            },
        )
        item = schema["$defs"]["TestPersonItem"]
        self.assertEqual(item["required"], ["type", "value", "id"])
        self.assertEqual(item["properties"]["type"]["const"], "person")
        self.assertEqual(item["properties"]["value"], {"$ref": "#/$defs/PersonBlock"})

    def test_stream_block_with_one_child(self):
        schema = self.json_schema(StreamBlock([("heading", CharBlock())]))
        self.assertEqual(schema["items"], {"$ref": "#/$defs/TestHeadingItem"})

    def test_list_block(self):
        self.assertEqual(
            self.value_schema(ListBlock(CharBlock())),
            {"type": "array", "items": NULLABLE_STRING},
        )

    def test_nested_anonymous_blocks_are_named_by_path(self):
        schema = self.json_schema(
            StreamBlock(
                [("card", StructBlock([("links", ListBlock(StructBlock([])))]))]
            )
        )
        self.assertEqual(
            set(schema["$defs"]), {"TestCardItem", "TestCard", "TestCardLinksItem"}
        )

    def test_block_subclass_is_named_after_its_class_and_shared(self):
        schema = self.json_schema(
            StreamBlock(
                [
                    ("author", PersonBlock()),
                    ("editors", ListBlock(PersonBlock())),
                    ("nested", StreamBlock([("person", PersonBlock())])),
                ]
            )
        )
        self.assertEqual(
            set(schema["$defs"]),
            {
                "PersonBlock",
                "TestAuthorItem",
                "TestEditorsItem",
                "TestNestedItem",
                "TestNestedPersonItem",
            },
        )

    def test_different_blocks_with_the_same_name_get_unique_names(self):
        class OtherPersonBlock(StructBlock):
            age = IntegerBlock()

        OtherPersonBlock.__name__ = "PersonBlock"

        schema = self.json_schema(
            StreamBlock([("a", PersonBlock()), ("b", OtherPersonBlock())])
        )
        self.assertEqual(
            schema["$defs"]["TestAItem"]["properties"]["value"],
            {"$ref": "#/$defs/PersonBlock"},
        )
        self.assertEqual(
            schema["$defs"]["TestBItem"]["properties"]["value"],
            {"$ref": "#/$defs/PersonBlock2"},
        )

    def test_overridden_api_representation_is_any(self):
        self.assertEqual(self.value_schema(ExtendedImageChooserBlock()), {})

    def test_unknown_block_is_any(self):
        self.assertEqual(self.value_schema(TableBlock()), {})

    def test_choice_block(self):
        self.assertEqual(
            self.value_schema(
                ChoiceBlock(choices=[("a", "A"), ("Group", [("b", "B"), ("c", "C")])])
            ),
            {"anyOf": [{"enum": ["a", "b", "c"], "type": "string"}, {"type": "null"}]},
        )

    def test_multiple_choice_block(self):
        self.assertEqual(
            self.value_schema(MultipleChoiceBlock(choices=[(1, "One"), (2, "Two")])),
            {
                "anyOf": [
                    {"type": "array", "items": {"enum": [1, 2], "type": "integer"}},
                    {"type": "null"},
                ]
            },
        )

    def test_callable_choices_are_not_evaluated(self):
        choices = mock.Mock(return_value=[("a", "A")])
        self.assertEqual(
            self.value_schema(ChoiceBlock(choices=choices)), NULLABLE_STRING
        )
        choices.assert_not_called()

    def test_chooser_block_uses_target_pk_type(self):
        self.assertEqual(self.value_schema(ImageChooserBlock()), NULLABLE_INTEGER)
        self.assertEqual(
            self.value_schema(SnippetChooserBlock(AdvertWithCustomUUIDPrimaryKey)),
            NULLABLE_STRING,
        )

    def test_image_block(self):
        schema = self.json_schema(StreamBlock([("image", ImageBlock())]))
        self.assertEqual(
            schema["$defs"]["ImageBlock"]["properties"]["image"]["anyOf"],
            NULLABLE_INTEGER["anyOf"],
        )
        self.assertEqual(
            schema["$defs"]["ImageBlock"]["required"],
            ["image", "decorative", "alt_text"],
        )


class TestInputBlockSchema(BlockSchemaTestMixin, SimpleTestCase):
    for_input = True

    def test_struct_block_fields_are_optional(self):
        schema = self.json_schema(PersonBlock())
        self.assertEqual(schema["title"], "PersonBlockInput")
        self.assertNotIn("required", schema)

    def test_stream_block_item_id_is_optional(self):
        schema = self.json_schema(StreamBlock([("heading", CharBlock())]))
        self.assertEqual(schema["items"], {"$ref": "#/$defs/TestHeadingItemInput"})
        self.assertEqual(
            schema["$defs"]["TestHeadingItemInput"]["required"], ["type", "value"]
        )

    def test_overridden_api_representation_is_still_typed(self):
        self.assertEqual(
            self.value_schema(ExtendedImageChooserBlock()), NULLABLE_INTEGER
        )


class TestStreamFieldSchema(SimpleTestCase):
    def test_read_schema(self):
        schema = read.read_generator.generate_schema(
            StreamPage, base_class=BasePageSchema
        )
        self.assertEqual(get_args(schema.model_fields["body"].annotation)[0], Any)

        json_schema = schema.model_json_schema(mode="serialization")
        self.assertEqual(
            json_schema["properties"]["body"]["items"]["discriminator"]["mapping"][
                "text"
            ],
            "#/$defs/StreamPageBodyTextItem",
        )

    def test_input_schema(self):
        schema = write.create_generator.generate_schema(
            StreamPage, base_class=Schema, fields=()
        )
        json_schema = schema.model_json_schema()
        rich_text_item = json_schema["$defs"]["StreamPageBodyRichTextItemInput"]
        self.assertIn(
            {"$ref": "#/$defs/RichTextInputSchema"},
            rich_text_item["properties"]["value"]["anyOf"],
        )

    def test_input_value_is_not_validated_against_schema(self):
        schema = write.create_generator.generate_schema(
            StreamPage, base_class=Schema, fields=()
        )
        body = [
            {"type": "unknown", "value": {"x": 1}},
            {"type": "text", "value": {"not": "a string"}},
            {
                "type": "title_list",
                "value": [{"type": "item", "value": "a", "id": "1"}],
            },
        ]
        instance = cast(Any, schema.model_validate({"body": body}))
        self.assertEqual(instance.body, body)

    def test_block_schema_is_built_lazily(self):
        with mock.patch.object(
            read.block_schema_builder,
            "get_type",
            wraps=read.block_schema_builder.get_type,
        ) as get_type:
            schema = read.read_generator.generate_schema(
                StreamPage, base_class=BasePageSchema
            )
            get_type.assert_not_called()

            schema.model_json_schema(mode="serialization")
            get_type.assert_called()
