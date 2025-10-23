from django import forms


class BaseFormSetMixin:
    """
    A mixin for formsets that adds the necessary attributes for the w-formset controller.
    So that JavaScript behavior can be added to the formset for dynamic addition and deletion of child forms.
    See client/src/controllers/FormsetController.ts
    """

    deletion_widget = forms.HiddenInput(attrs={"data-w-formset-target": "deleteInput"})

    @property
    def attrs(self):
        return {
            "data-controller": "w-formset",
            "data-w-formset-deleted-class": "w-transition-opacity w-duration-300 w-ease-out w-opacity-0",
        }

    @property
    def management_form(self):
        form = super().management_form

        for field in form:
            if field.name.endswith(forms.formsets.TOTAL_FORM_COUNT):
                field.field.widget.attrs["data-w-formset-target"] = "totalFormsInput"
            if field.name.endswith(forms.formsets.MIN_NUM_FORM_COUNT):
                field.field.widget.attrs["data-w-formset-target"] = "minFormsInput"
            if field.name.endswith(forms.formsets.MAX_NUM_FORM_COUNT):
                field.field.widget.attrs["data-w-formset-target"] = "maxFormsInput"

        return form
