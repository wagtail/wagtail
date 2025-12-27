from django import forms

from wagtail.blocks import ChoiceBlock


class IntChoiceBlock(ChoiceBlock):
    def get_field(self, **kwargs):
        choices = kwargs.pop("choices")
        return forms.TypedChoiceField(
            choices=choices,
            coerce=int,
            **kwargs,
        )

    def to_python(self, value):
        if value is None:
            return None
        return int(value)
