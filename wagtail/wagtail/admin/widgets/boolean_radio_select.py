from django import forms
from django.utils.translation import gettext_lazy as _


class BooleanRadioSelect(forms.RadioSelect):
    """
    A radio select widget for boolean fields. Displays as three options; "All", "Yes" and "No".
    """

    input_type = "radio"

    def __init__(self, attrs=None):
        choices = (
            ("", _("All")),
            ("true", _("Yes")),
            ("false", _("No")),
        )
        super().__init__(attrs, choices)

    def format_value(self, value):
        try:
            return {
                True: ["true"],
                False: ["false"],
                "true": ["true"],
                "false": ["false"],
            }[value]
        except KeyError:
            return ""

    def value_from_datadict(self, data, files, name):
        value = data.get(name)
        return {
            True: True,
            "True": True,
            "False": False,
            False: False,
            "true": True,
            "false": False,
        }.get(value)
