from django import forms
from django.utils.translation import gettext_lazy as _

from wagtail.coreutils import get_content_languages
from wagtail.models import Locale


class LocaleForm(forms.ModelForm):
    required_css_class = "required"
    language_code = forms.ChoiceField(
        label=_("Language"), choices=get_content_languages().items()
    )

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")
        super().__init__(*args, **kwargs)

        # Get language codes that are already used
        used_language_codes = Locale.objects.values_list("language_code", flat=True)

        self.fields["language_code"].choices = [
            (language_code, display_name)
            for language_code, display_name in get_content_languages().items()
            if language_code not in used_language_codes
            or (instance and instance.language_code == language_code)
        ]

        # If the existing language code is invalid, add an empty value so Django doesn't automatically select a random language
        if instance and not instance.language_code_is_valid():
            self.fields["language_code"].choices.insert(
                0, (None, _("Select a new language"))
            )

    class Meta:
        model = Locale
        fields = ["language_code"]
