from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
from django.utils.safestring import mark_safe
from django.utils.encoding import force_text

from wagtail.wagtailadmin.edit_handlers import BaseChooserPanel


class BaseSnippetChooserPanel(BaseChooserPanel):
    field_template = "wagtailsnippets/edit_handlers/snippet_chooser_panel.html"
    object_type_name = 'item'

    _content_type = None

    @classmethod
    def content_type(cls):
        if cls._content_type is None:
            # TODO: infer the content type by introspection on the foreign key rather than having to pass it explicitly
            cls._content_type = ContentType.objects.get_for_model(cls.snippet_type)

        return cls._content_type

    def render_as_field(self, show_help_text=True):
        instance_obj = self.get_chosen_item()
        return mark_safe(render_to_string(self.field_template, {
            'field': self.bound_field,
            self.object_type_name: instance_obj,
            'snippet_type_name': self.snippet_type_name,
            'is_chosen': bool(instance_obj),
            'show_help_text': show_help_text,
        }))

    def render_js(self):
        content_type = self.__class__.content_type()

        return mark_safe("createSnippetChooser(fixPrefix('%s'), '%s/%s');" % (
            self.bound_field.id_for_label,
            content_type.app_label,
            content_type.model,
        ))


def SnippetChooserPanel(field_name, snippet_type):
    return type('_SnippetChooserPanel', (BaseSnippetChooserPanel,), {
        'field_name': field_name,
        'snippet_type_name': force_text(snippet_type._meta.verbose_name),
        'snippet_type': snippet_type,
    })
