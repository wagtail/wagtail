from django import forms


class BaseFormSetMixin:
    """
    A mixin for formsets that adds the necessary attributes for the w-formset and
    w-orderable controllers. This adds JavaScript behavior to the formset for dynamic
    addition, deletion, and reordering of child forms. See:
    - ``client/src/controllers/FormsetController.ts``
    - ``client/src/controllers/OrderableController.ts``
    """

    deletion_widget = forms.HiddenInput(attrs={"data-w-formset-target": "deleteInput"})
    ordering_widget = forms.HiddenInput(attrs={"data-w-formset-target": "orderInput"})

    @property
    def attrs(self):
        controllers = ["w-formset"]
        if self.can_order:
            controllers.append("w-orderable")
        return {
            "data-controller": " ".join(controllers),
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
