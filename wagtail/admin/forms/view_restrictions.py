from django import forms
from django.contrib.auth.models import Group
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from wagtail.models import BaseViewRestriction


class BaseViewRestrictionForm(forms.ModelForm):
    restriction_type = forms.ChoiceField(
        label=gettext_lazy("Visibility"),
        choices=BaseViewRestriction.RESTRICTION_CHOICES,
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["groups"].widget = forms.CheckboxSelectMultiple()
        self.fields["groups"].queryset = Group.objects.all()

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if (
            self.cleaned_data.get("restriction_type") == BaseViewRestriction.PASSWORD
            and not password
        ):
            raise forms.ValidationError(_("This field is required."), code="invalid")
        return password

    def clean_groups(self):
        groups = self.cleaned_data.get("groups")
        if (
            self.cleaned_data.get("restriction_type") == BaseViewRestriction.GROUPS
            and not groups
        ):
            raise forms.ValidationError(
                _("Please select at least one group."), code="invalid"
            )
        return groups

    class Meta:
        model = BaseViewRestriction
        fields = ("restriction_type", "password", "groups")
