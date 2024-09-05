from django.utils.translation import gettext_lazy as _

from wagtail import blocks


class FormFieldBlock(blocks.StructBlock):
    label = blocks.CharBlock(help_text=_("Text describing the field."))
    help_text = blocks.CharBlock(
        required=False,
        help_text=_(
            "Text displayed below the label used to add more information, like this one."
        ),
    )
    required = blocks.BooleanBlock(
        required=False,
        help_text=_("If checked, this field must be filled to validate the form."),
    )

    class Meta:
        form_classname = "field-block"


class ChoiceBlock(blocks.StructBlock):
    label = blocks.CharBlock(label=_("Label"))
    initial = blocks.BooleanBlock(label=_("Selected"), required=False)

    class Meta:
        label = _("Choice")


class SinglelineFormFieldBlock(FormFieldBlock):
    initial = blocks.CharBlock(
        label=_("Default value"),
        required=False,
        help_text=_("Text used to pre-fill the field."),
    )
    min_length = blocks.IntegerBlock(
        help_text=_("Minimum amount of characters allowed in the field."),
        default=0,
    )
    max_length = blocks.IntegerBlock(
        help_text=_("Maximum amount of characters allowed in the field."),
        default=255,
    )

    class Meta:
        icon = "pilcrow"
        label = _("Single line text")


class MultilineFormFieldBlock(FormFieldBlock):
    initial = blocks.TextBlock(
        label=_("Default value"),
        required=False,
        help_text=_("Multi-line text used to pre-fill the text area."),
    )
    min_length = blocks.IntegerBlock(
        help_text=_("Minimum amount of characters allowed in the text area."),
        default=0,
    )
    max_length = blocks.IntegerBlock(
        help_text=_("Maximum amount of characters allowed in the text area."),
        default=1024,
    )

    class Meta:
        icon = "pilcrow"
        label = _("Multi-line text")


class EmailFormFieldBlock(FormFieldBlock):
    initial = blocks.EmailBlock(
        label=_("Default value"),
        required=False,
        help_text=_("E-mail used to pre-fill the field."),
    )

    class Meta:
        icon = "mail"
        label = _("Email")


class NumberFormFieldBlock(FormFieldBlock):
    initial = blocks.DecimalBlock(
        label=_("Default value"),
        required=False,
        help_text=_("Number used to pre-fill the field."),
    )
    min_value = blocks.IntegerBlock(
        help_text=_("Minimum number allowed in the field."),
        required=False,
    )
    max_value = blocks.IntegerBlock(
        help_text=_("Maximum number allowed in the field."),
        required=False,
    )

    class Meta:
        icon = "decimal"
        label = _("Number")


class URLFormFieldBlock(FormFieldBlock):
    initial = blocks.URLBlock(
        label=_("Default value"),
        required=False,
        help_text=_("URL used to pre-fill the field."),
    )

    class Meta:
        icon = "link-external"
        label = _("URL")


class CheckBoxFormFieldBlock(FormFieldBlock):
    initial = blocks.BooleanBlock(
        label=_("Checked"),
        required=False,
        help_text=_("If checked, the checkbox will be checked by default."),
    )

    class Meta:
        icon = "tick-inverse"
        label = _("Checkbox")


class CheckBoxesFormFieldBlock(FormFieldBlock):
    choices = blocks.ListBlock(
        ChoiceBlock(
            [("initial", blocks.BooleanBlock(label=_("Checked"), required=False))]
        ),
        label=_("Choices"),
    )

    class Meta:
        icon = "tick-inverse"
        label = _("Checkboxes")


class DropDownFormFieldBlock(FormFieldBlock):
    choices = blocks.ListBlock(ChoiceBlock(), label=_("Choices"))

    class Meta:
        icon = "list-ul"
        label = _("Drop down")


class MultiSelectFormFieldBlock(FormFieldBlock):
    choices = blocks.ListBlock(ChoiceBlock(), label=_("Choices"))

    class Meta:
        icon = "list-ul"
        label = _("Multiple select")


class RadioFormFieldBlock(FormFieldBlock):
    choices = blocks.ListBlock(ChoiceBlock(), label=_("Choices"))

    class Meta:
        icon = "radio-empty"
        label = _("Radio buttons")


class DateFormFieldBlock(FormFieldBlock):
    initial = blocks.DateBlock(
        label=_("Default value"),
        required=False,
        help_text=_("Date used to pre-fill the field."),
    )

    class Meta:
        icon = "date"
        label = _("Date")


class DateTimeFormFieldBlock(FormFieldBlock):
    initial = blocks.DateTimeBlock(
        label=_("Default value"),
        required=False,
        help_text=_("Date/time used to pre-fill the field."),
    )

    class Meta:
        icon = "time"
        label = _("Date/time")


class HiddenFormFieldBlock(FormFieldBlock):
    initial = blocks.CharBlock(
        label=_("Default value"),
        required=False,
        help_text=_("Text used to pre-fill the field."),
    )

    class Meta:
        icon = "no-view"
        label = _("Hidden field")


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
