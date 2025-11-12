from django.forms.formsets import BaseFormSet

class BaseFormSetMixin:
    def should_delete(self, form):
        return hasattr(form, "cleaned_data") and form.cleaned_data.get("DELETE")

    def should_ignore(self, form):
        return hasattr(form, "cleaned_data") and not form.has_changed()

class BaseFormSetWithFormTracking(BaseFormSet, BaseFormSetMixin):
    pass

