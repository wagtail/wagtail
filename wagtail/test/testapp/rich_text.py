from django.forms import Media, widgets
from django.utils.safestring import mark_safe


class CustomRichTextArea(widgets.Textarea):
    def render(self, name, value, attrs=None, renderer=None):
        # mock rendering for individual custom widget

        return mark_safe(
            '<template data-controller="custom-editor" data-id="{}">{}</template>'.format(
                attrs["id"],
                super().render(name, value, attrs),
            )
        )

    @property
    def media(self):
        return Media(js=["vendor/custom_editor.js"])


class LegacyRichTextArea(widgets.Textarea):
    def render(self, name, value, attrs=None, renderer=None):
        # mock rendering for individual custom widget
        return mark_safe(
            '<template data-controller="legacy-editor" data-id="{}">{}</template>'.format(
                attrs["id"],
                super().render(name, value, attrs),
            )
        )

    @property
    def media(self):
        return Media(js=["vendor/legacy_editor.js"])
