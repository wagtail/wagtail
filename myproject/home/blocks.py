from django import forms
from wagtail.blocks import ChoiceBlock


class IntChoiceBlock(ChoiceBlock):
    """
    A Wagtail ChoiceBlock that stores integers instead of strings.
    """

    def get_field(self, **kwargs):
        """
        Return a Django form field for this block.
        """
        # Ensure choices is an iterable of (int, label) tuples
        choices = kwargs.pop("choices", [])
        return forms.TypedChoiceField(
            choices=choices,
            coerce=int,
            **kwargs,
        )

    def to_python(self, value):
        """
        Convert stored value to an integer.
        """
        if value is None:
            return None
        return int(value)
