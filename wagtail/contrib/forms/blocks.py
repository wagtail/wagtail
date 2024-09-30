from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from wagtail import blocks


class FormFieldBlock(blocks.StructBlock):
    label = blocks.CharBlock(
        label=_("Label"),
        help_text=_("Short text describing the field."),
        form_classname="formbuilder-field-block-label",
    )
    help_text = blocks.CharBlock(
        label=_("Help text"),
        required=False,
        help_text=_("Text displayed below the label to add more information."),
    )


class RequiredBlock(blocks.BooleanBlock):
    def __init__(self, condition=None):
        super().__init__(
            required=False,
            help_text=format_lazy(
                _("If checked, {condition} to validate the form."),
                condition=condition or _("this field must be filled"),
            ),
            label=_("Required"),
        )


class ChoiceBlock(blocks.StructBlock):
    label = blocks.CharBlock(
        label=_("Label"),
        form_classname="formbuilder-choice-label",
    )
    initial = blocks.BooleanBlock(
        label=_("Selected"),
        required=False,
    )

    class Meta:
        label = _("Choice")


class ChoicesList(blocks.ListBlock):
    def __init__(self, child_block=None, **kwargs):
        super().__init__(child_block or ChoiceBlock(), search_index=True, **kwargs)

    label = _("Choices")
    form_classname = "formbuilder-choices"


def init_options(field_type):
    return {
        "label": _("Default value"),
        "required": False,
        "help_text": format_lazy(
            _("{field_type} used to pre-fill the field."),
            field_type=field_type,
        ),
    }


class SinglelineFormFieldBlock(FormFieldBlock):
    required = RequiredBlock()
    initial = blocks.CharBlock(**init_options(_("Single line text")))
    min_length = blocks.IntegerBlock(
        label=_("Min length"),
        help_text=_("Minimum amount of characters allowed in the field."),
        default=0,
    )
    max_length = blocks.IntegerBlock(
        label=_("Max length"),
        help_text=_("Maximum amount of characters allowed in the field."),
        default=255,
    )

    class Meta:
        icon = "pilcrow"
        label = _("Single line text")
        form_classname = "formbuilder-field-block formbuilder-field-block-singleline"


class MultilineFormFieldBlock(FormFieldBlock):
    required = RequiredBlock()
    initial = blocks.TextBlock(**init_options(_("Multi-line text")))
    min_length = blocks.IntegerBlock(
        label=_("Min length"),
        help_text=_("Minimum amount of characters allowed in the field."),
        default=0,
    )
    max_length = blocks.IntegerBlock(
        label=_("Max length"),
        help_text=_("Maximum amount of characters allowed in the field."),
        default=1024,
    )

    class Meta:
        icon = "pilcrow"
        label = _("Multi-line text")
        form_classname = "formbuilder-field-block formbuilder-field-block-multiline"


class EmailFormFieldBlock(FormFieldBlock):
    required = RequiredBlock()
    initial = blocks.EmailBlock(**init_options(_("E-mail")))

    class Meta:
        icon = "mail"
        label = _("E-mail")
        form_classname = "formbuilder-field-block formbuilder-field-block-email"


class NumberFormFieldBlock(FormFieldBlock):
    required = RequiredBlock()
    initial = blocks.DecimalBlock(**init_options(_("Number")))
    min_value = blocks.IntegerBlock(
        label=_("Min value"),
        help_text=_("Minimum number allowed in the field."),
        required=False,
    )
    max_value = blocks.IntegerBlock(
        label=_("Max value"),
        help_text=_("Maximum number allowed in the field."),
        required=False,
    )

    class Meta:
        icon = "decimal"
        label = _("Number")
        form_classname = "formbuilder-field-block formbuilder-field-block-number"


class URLFormFieldBlock(FormFieldBlock):
    required = RequiredBlock()
    initial = blocks.URLBlock(**init_options(_("URL")))

    class Meta:
        icon = "link-external"
        label = _("URL")
        form_classname = "formbuilder-field-block formbuilder-field-block-url"


class CheckBoxFormFieldBlock(FormFieldBlock):
    required = RequiredBlock(_("the box must be checked"))
    initial = blocks.BooleanBlock(
        label=_("Checked"),
        required=False,
        help_text=_("If checked, the box will be checked by default."),
    )

    class Meta:
        icon = "tick-inverse"
        label = _("Checkbox")
        form_classname = "formbuilder-field-block formbuilder-field-block-checkbox"


class CheckBoxesFormFieldBlock(FormFieldBlock):
    required = RequiredBlock(_("at least one box must be checked"))
    choices = ChoicesList(
        ChoiceBlock(
            [("initial", blocks.BooleanBlock(label=_("Checked"), required=False))]
        )
    )

    class Meta:
        icon = "tick-inverse"
        label = _("Checkboxes")
        form_classname = "formbuilder-field-block formbuilder-field-block-checkboxes"


class DropDownFormFieldBlock(FormFieldBlock):
    required = RequiredBlock(_("an item must be selected"))
    choices = ChoicesList()

    class Meta:
        icon = "list-ul"
        label = _("Drop down")
        form_classname = "formbuilder-field-block formbuilder-field-block-dropdown"


class MultiSelectFormFieldBlock(FormFieldBlock):
    required = RequiredBlock(_("at least one item must be selected"))
    choices = ChoicesList()

    class Meta:
        icon = "list-ul"
        label = _("Multiple select")
        form_classname = "formbuilder-field-block formbuilder-field-block-multiselect"


class RadioFormFieldBlock(FormFieldBlock):
    required = RequiredBlock(_("an item must be selected"))
    choices = ChoicesList()

    class Meta:
        icon = "radio-empty"
        label = _("Radio buttons")
        form_classname = "formbuilder-field-block formbuilder-field-block-radio"


class DateFormFieldBlock(FormFieldBlock):
    required = RequiredBlock()
    initial = blocks.DateBlock(**init_options(_("Date")))

    class Meta:
        icon = "date"
        label = _("Date")
        form_classname = "formbuilder-field-block formbuilder-field-block-date"


class DateTimeFormFieldBlock(FormFieldBlock):
    required = RequiredBlock()
    initial = blocks.DateTimeBlock(**init_options(_("Date and time")))

    class Meta:
        icon = "time"
        label = _("Date and time")
        form_classname = "formbuilder-field-block formbuilder-field-block-datetime"


class HiddenFormFieldBlock(FormFieldBlock):
    required = RequiredBlock()
    initial = blocks.CharBlock(**init_options(_("Hidden text")))

    class Meta:
        icon = "no-view"
        label = _("Hidden text")
        form_classname = "formbuilder-field-block formbuilder-field-block-hidden"


class FormFieldsBlock(blocks.StreamBlock):
    singleline = SinglelineFormFieldBlock()
    multiline = MultilineFormFieldBlock()
    email = EmailFormFieldBlock()
    number = NumberFormFieldBlock()
    url = URLFormFieldBlock()
    checkbox = CheckBoxFormFieldBlock()
    checkboxes = CheckBoxesFormFieldBlock()
    dropdown = DropDownFormFieldBlock()
    multiselect = MultiSelectFormFieldBlock()
    radio = RadioFormFieldBlock()
    date = DateFormFieldBlock()
    datetime = DateTimeFormFieldBlock()
    hidden = HiddenFormFieldBlock()

    class Meta:
        form_classname = "formbuilder-fields-block"
