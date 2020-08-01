import os

from django import forms
from django.utils.translation import gettext_lazy as _

from wagtail.admin.widgets import AdminPageChooser
from wagtail.contrib.redirects.models import Redirect
from wagtail.core.models import Site


class RedirectForm(forms.ModelForm):
    site = forms.ModelChoiceField(
        label=_("From site"), queryset=Site.objects.all(), required=False, empty_label=_("All sites")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['redirect_page'].widget = AdminPageChooser()

    required_css_class = "required"

    def clean(self):
        """
        The unique_together condition on the model is ignored if site is None, so need to
        check for duplicates manually
        """
        cleaned_data = super().clean()

        if cleaned_data.get('site') is None:
            old_path = cleaned_data.get('old_path')
            if old_path is None:
                # cleaned_data['old_path'] is empty because it has already failed validation,
                # so don't bother with our duplicate test
                return

            old_path = Redirect.normalise_path(old_path)
            duplicates = Redirect.objects.filter(old_path=old_path, site__isnull=True)
            if self.instance.pk:
                duplicates = duplicates.exclude(id=self.instance.pk)

            if duplicates:
                raise forms.ValidationError(_("A redirect with this path already exists."))

    class Meta:
        model = Redirect
        fields = ('old_path', 'site', 'is_permanent', 'redirect_page', 'redirect_link')


class ImportForm(forms.Form):
    import_file = forms.FileField(
        label=_("File to import"),
    )

    def __init__(self, allowed_extensions, *args, **kwargs):
        super().__init__(*args, **kwargs)

        accept = ",".join(
            [".{}".format(x) for x in allowed_extensions]
        )
        self.fields["import_file"].widget = forms.FileInput(
            attrs={"accept": accept}
        )

        uppercased_extensions = [x.upper() for x in allowed_extensions]
        allowed_extensions_text = ", ".join(uppercased_extensions)
        help_text = _(
            "Supported formats: %(supported_formats)s."
        ) % {
            'supported_formats': allowed_extensions_text,
        }
        self.fields["import_file"].help_text = help_text


class ConfirmImportForm(forms.Form):
    from_index = forms.ChoiceField(label=_("From field"), choices=(),)
    to_index = forms.ChoiceField(label=_("To field"), choices=(),)
    site = forms.ModelChoiceField(
        label=_("From site"),
        queryset=Site.objects.all(),
        required=False,
        empty_label=_("All sites"),
    )
    permanent = forms.BooleanField(initial=True, required=False)
    import_file_name = forms.CharField(widget=forms.HiddenInput())
    original_file_name = forms.CharField(widget=forms.HiddenInput())
    input_format = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, headers, *args, **kwargs):
        super().__init__(*args, **kwargs)

        choices = []
        for i, f in enumerate(headers):
            choices.append([str(i), f])
        if len(headers) > 1:
            choices.insert(0, ("", "---"))

        self.fields["from_index"].choices = choices
        self.fields["to_index"].choices = choices

    def clean_import_file_name(self):
        data = self.cleaned_data["import_file_name"]
        data = os.path.basename(data)
        return data
