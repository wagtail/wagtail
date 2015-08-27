from __future__ import absolute_import, unicode_literals

from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
from django.utils.safestring import mark_safe
from django.utils.encoding import force_text
from django.core.exceptions import ImproperlyConfigured

from wagtail.wagtailadmin.edit_handlers import BaseChooserPanel
from wagtail.wagtailcore.utils import resolve_model_string
from .widgets import AdminSnippetChooser


class BaseSnippetChooserPanel(BaseChooserPanel):
    object_type_name = 'item'

    _target_content_type = None

    @classmethod
    def widget_overrides(cls):
        return {cls.field_name: AdminSnippetChooser(
            content_type=cls.target_content_type(), snippet_type_name=cls.snippet_type_name)}

    @classmethod
    def target_content_type(cls):
        if cls._target_content_type is None:
            if cls.snippet_type:
                try:
                    model = resolve_model_string(cls.snippet_type)
                except LookupError:
                    raise ImproperlyConfigured("{0}.snippet_type must be of the form 'app_label.model_name', given {1!r}".format(
                        cls.__name__, cls.snippet_type))
                except ValueError:
                    raise ImproperlyConfigured("{0}.snippet_type refers to model {1!r} that has not been installed".format(
                        cls.__name__, cls.snippet_type))

                cls._target_content_type = ContentType.objects.get_for_model(model)
            else:
                target_model = cls.model._meta.get_field(cls.field_name).rel.to
                cls._target_content_type = ContentType.objects.get_for_model(target_model)

        return cls._target_content_type

    def render_as_field(self):
        instance_obj = self.get_chosen_item()
        return mark_safe(render_to_string(self.field_template, {
            'field': self.bound_field,
            self.object_type_name: instance_obj,
            'snippet_type_name': self.snippet_type_name,
        }))

    @property
    def snippet_type_name(self):
        return force_text(self.target_content_type()._meta.verbose_name)


class SnippetChooserPanel(object):
    def __init__(self, field_name, snippet_type):
        self.field_name = field_name
        self.snippet_type = snippet_type

    def bind_to_model(self, model):
        return type(str('_SnippetChooserPanel'), (BaseSnippetChooserPanel,), {
            'model': model,
            'field_name': self.field_name,
            'snippet_type': self.snippet_type,
        })
