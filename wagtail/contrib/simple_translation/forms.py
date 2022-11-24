from django import forms
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy, ngettext

from wagtail.models import Locale, Page


class CheckboxSelectMultipleWithDisabledOptions(forms.CheckboxSelectMultiple):
    option_template_name = "simple_translation/admin/input_option.html"
    disabled_values = []

    def create_option(self, *args, **kwargs):
        option = super().create_option(*args, **kwargs)
        if option["value"] in self.disabled_values:
            option["attrs"]["disabled"] = True
        return option


class SubmitTranslationForm(forms.Form):
    # Note: We don't actually use select_all in Python, it is just the
    # easiest way to add the widget to the form. It's controlled in JS.
    select_all = forms.BooleanField(label=gettext_lazy("Select all"), required=False)
    locales = forms.ModelMultipleChoiceField(
        label=gettext_lazy("Locales"),
        queryset=Locale.objects.none(),
        widget=CheckboxSelectMultipleWithDisabledOptions,
    )
    include_subtree = forms.BooleanField(
        required=False, help_text=gettext_lazy("All child pages will be created.")
    )

    def __init__(self, instance, *args, **kwargs):
        super().__init__(*args, **kwargs)

        hide_include_subtree = True
        self.show_submit = True

        if isinstance(instance, Page):
            descendant_count = instance.get_descendants().count()

            if descendant_count > 0:
                hide_include_subtree = False
                self.fields["include_subtree"].label = ngettext(
                    "Include subtree (%(descendant_count)s page)",
                    "Include subtree (%(descendant_count)s pages)",
                    descendant_count,
                ) % {"descendant_count": descendant_count}

        if hide_include_subtree:
            self.fields["include_subtree"].widget = forms.HiddenInput()

        untranslated_locales = Locale.objects.exclude(
            id__in=instance.get_translations(inclusive=True).values_list(
                "locale_id", flat=True
            )
        )
        self.fields["locales"].queryset = untranslated_locales

        # For snippets, hide select all if there is one option.
        # Using len() instead of count() here as we're going to evaluate this queryset
        # anyway and it gets cached so it'll only have one query in the end.
        hide_select_all = len(untranslated_locales) < 2

        if isinstance(instance, Page):
            parent = instance.get_parent()

            # Find allowed locale options.
            if parent.is_root():
                # All locale options are allowed.
                allowed_locale_ids = Locale.objects.all().values_list("id", flat=True)
            else:
                # Only the locale options that have a translated parent are allowed.
                allowed_locale_ids = (
                    instance.get_parent()
                    .get_translations(inclusive=True)
                    .values_list("locale_id", flat=True)
                )

            # Get and set the locale options that are disabled.
            disabled_locales = Locale.objects.exclude(
                id__in=allowed_locale_ids
            ).values_list("id", flat=True)
            self.fields["locales"].widget.disabled_values = disabled_locales

            if disabled_locales:
                # Display a help text.
                url = reverse(
                    "simple_translation:submit_page_translation", args=[parent.id]
                )
                help_text = ngettext(
                    "A locale is disabled because a parent page is not translated.",
                    "Some locales are disabled because some parent pages are not translated.",
                    len(disabled_locales),
                )
                help_text += "<br>"
                help_text += '<a href="{}">'.format(url)
                help_text += ngettext(
                    "Translate the parent page.",
                    "Translate the parent pages.",
                    len(disabled_locales),
                )
                help_text += "</a>"
                self.fields["locales"].help_text = mark_safe(help_text)

            # For pages, if there is one locale or all locales are disabled.
            hide_select_all = (
                len(untranslated_locales) == 1
                or len(untranslated_locales) - len(disabled_locales) == 0
            )

            # Hide the submit if all untranslated locales are disabled.
            # This property is used in the template.
            if len(untranslated_locales) == len(disabled_locales):
                self.show_submit = False

        if hide_select_all:
            self.fields["select_all"].widget = forms.HiddenInput()
