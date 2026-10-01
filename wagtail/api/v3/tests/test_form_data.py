from django import forms
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from django.utils.datastructures import MultiValueDict

from wagtail import blocks
from wagtail.api.v3.form_data import to_prep_block_value


class UpperCaseInput(forms.TextInput):
    def value_from_datadict(self, data, files, name):
        return super().value_from_datadict(data, files, name).upper()


class UpperCaseBlock(blocks.FieldBlock):
    def __init__(self, **kwargs):
        self.field = forms.CharField(widget=UpperCaseInput())
        super().__init__(**kwargs)


class LocationBlock(blocks.Block):
    def value_from_datadict(self, data, files, prefix):
        return {
            "latitude": float(data[f"{prefix}-latitude"]),
            "longitude": float(data[f"{prefix}-longitude"]),
        }


class TestToPrepBlockValue(SimpleTestCase):
    def test_field_block_value_goes_through_its_widget(self):
        block = blocks.StreamBlock([("shout", UpperCaseBlock())])
        value = to_prep_block_value(
            block, [{"type": "shout", "value": "hello"}], "body", MultiValueDict()
        )
        self.assertEqual(value, [{"type": "shout", "value": "HELLO"}])

    def test_multiple_choice_block_value_is_a_list(self):
        block = blocks.StreamBlock(
            [
                (
                    "tags",
                    blocks.MultipleChoiceBlock(
                        choices=[("a", "A"), ("b", "B"), ("c", "C")]
                    ),
                )
            ]
        )
        value = to_prep_block_value(
            block, [{"type": "tags", "value": ["a", "c"]}], "body", MultiValueDict()
        )
        self.assertEqual(value, [{"type": "tags", "value": ["a", "c"]}])

    def test_static_block_is_accepted(self):
        block = blocks.StreamBlock([("divider", blocks.StaticBlock())])
        value = to_prep_block_value(
            block, [{"type": "divider", "value": None}], "body", MultiValueDict()
        )
        self.assertEqual(value, [{"type": "divider", "value": None}])

    def test_custom_block_not_based_on_a_known_block_is_rejected(self):
        block = blocks.StreamBlock([("location", LocationBlock())])
        with self.assertRaisesMessage(
            ValidationError,
            "body-0-value: LocationBlock can't be written through the API",
        ):
            to_prep_block_value(
                block,
                [{"type": "location", "value": {"latitude": 1, "longitude": 2}}],
                "body",
                MultiValueDict(),
            )
