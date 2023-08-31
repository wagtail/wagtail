from functools import lru_cache

from django import forms
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import (
    get_password_validators,
    password_changed,
    validate_password,
)
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from wagtail.models import BaseViewRestriction


@lru_cache(maxsize=None)
def get_wagtail_password_validators():
    wagtail_password_validators = getattr(
        settings, "WAGTAIL_PRIVATE_PAGES_PASSWORD_VALIDATORS", settings.AUTH_PASSWORD_VALIDATORS
    )
    return get_password_validators(wagtail_password_validators)


class BaseViewRestrictionForm(forms.ModelForm):
    restriction_type = forms.ChoiceField(
        label=gettext_lazy("Visibility"),
        choices=BaseViewRestriction.RESTRICTION_CHOICES,
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not getattr(settings, "WAGTAIL_ALLOW_PASSWORD_PAGE_PRIVACY", True):
            self.fields["restriction_type"].choices = (
                choice
                for choice in BaseViewRestriction.RESTRICTION_CHOICES
                if choice[0] != BaseViewRestriction.PASSWORD
            )

            del self.fields["password"]

        else:
            self.fields["password"].help_text = mark_safe(
                "<ul>"
                + format_html_join(
                    "\n",
                    "<li>{}</li>",
                    [
                        [validator.get_help_text()]
                        for validator in get_wagtail_password_validators()
                    ],
                )
                + "</ul>"
            )

        self.fields["groups"].widget = forms.CheckboxSelectMultiple()
        self.fields["groups"].queryset = Group.objects.all()

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if (
            self.cleaned_data.get("restriction_type") == BaseViewRestriction.PASSWORD
            and not password
        ):
            raise forms.ValidationError(_("This field is required."), code="invalid")

        if password:
            validate_password(password, get_wagtail_password_validators())

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

    def save(self, *args, **kwargs):
        restriction = super().save(*args, **kwargs)

        if password := self.cleaned_data.get("password"):
            password_changed(password, get_wagtail_password_validators())

        return restriction

    class Meta:
        model = BaseViewRestriction
        fields = ("restriction_type", "password", "groups")
