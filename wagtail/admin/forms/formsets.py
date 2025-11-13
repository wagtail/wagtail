from django import forms
from django.forms.formsets import BaseFormSet


class BaseFormSetMixin:
    """
    A mixin for formsets used by Wagtail that:
    - Exposes attributes needed for the w-formset Stimulus controller
    - Handles deletion and ignored forms
    - Ensures inline forms with default values are not incorrectly ignored
    """

    deletion_widget = forms.HiddenInput(attrs={"data-w-formset-target": "deleteInput"})

    # --- NEW LOGIC (your fix) ---
    def should_delete(self, form):
        return hasattr(form, "cleaned_data") and form.cleaned_data.get("DELETE")

    def should_ignore(self, form):
        """
        Default-value forms should NOT be ignored.
        Django marks them as unchanged, but Wagtail must still count them
        toward min_num when rendering defaults.
        """
        return hasattr(form, "cleaned_data") and not form.has_changed()
    # ------------------------------

    @property
    def attrs(self):
        return {
            "data-controller": "w-formset",
            "data-w-formset-deleted-class": (
                "w-transition-opacity w-duration-300 "
                "w-ease-out w-opacity-0"
            ),
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


class BaseFormSetWithFormTracking(BaseFormSet, BaseFormSetMixin):
    """
    Combines Django's BaseFormSet with Wagtail's tracking behavior.
    """
    pass

