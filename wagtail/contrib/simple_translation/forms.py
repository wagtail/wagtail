from django import forms
from django.utils.translation import gettext_lazy, ngettext

from wagtail.core.models import Locale, Page


class SubmitTranslationForm(forms.Form):
    # Note: We don't actually use select_all in Python, it is just the
    # easiest way to add the widget to the form. It's controlled in JS.
    select_all = forms.BooleanField(label=gettext_lazy("Select all"), required=False)
    locales = forms.ModelMultipleChoiceField(
        label=gettext_lazy("Locales"),
        queryset=Locale.objects.none(),
        widget=forms.CheckboxSelectMultiple,
    )
    include_subtree = forms.BooleanField(
        required=False, help_text=gettext_lazy("All child pages will be created.")
    )

    def __init__(self, instance, *args, **kwargs):
        super().__init__(*args, **kwargs)

        hide_include_subtree = True

        if isinstance(instance, Page):
            descendant_count = instance.get_descendants().count()

            if descendant_count > 0:
                hide_include_subtree = False
                self.fields["include_subtree"].label = ngettext(
                    "Include subtree ({} page)",
                    "Include subtree ({} pages)",
                    descendant_count,
                ).format(descendant_count)

        if hide_include_subtree:
            self.fields["include_subtree"].widget = forms.HiddenInput()

        self.fields["locales"].queryset = Locale.objects.exclude(
            id__in=instance.get_translations(inclusive=True).values_list(
                "locale_id", flat=True
            )
        )

        # Using len() instead of count() here as we're going to evaluate this queryset
        # anyway and it gets cached so it'll only have one query in the end.
        if len(self.fields["locales"].queryset) < 2:
            self.fields["select_all"].widget = forms.HiddenInput()
