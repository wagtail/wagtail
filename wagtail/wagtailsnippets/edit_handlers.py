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

    _target_model = None
    _target_content_type = None

    @classmethod
    def widget_overrides(cls):
        return {cls.field_name: AdminSnippetChooser(
            content_type=cls.target_content_type(), snippet_type_name=cls.get_snippet_type_name())}

    @classmethod
    def target_model(cls):
        if cls._target_model is None:
            if cls.snippet_type:
                try:
                    cls._target_model = resolve_model_string(cls.snippet_type)
                except LookupError:
                    raise ImproperlyConfigured("{0}.snippet_type must be of the form 'app_label.model_name', given {1!r}".format(
                        cls.__name__, cls.snippet_type))
                except ValueError:
                    raise ImproperlyConfigured("{0}.snippet_type refers to model {1!r} that has not been installed".format(
                        cls.__name__, cls.snippet_type))
            else:
                cls._target_model = cls.model._meta.get_field(cls.field_name).rel.to

        return cls._target_model

    @classmethod
    def target_content_type(cls):
        if cls._target_content_type is None:
            cls._target_content_type = ContentType.objects.get_for_model(cls.target_model())
        return cls._target_content_type

    def render_as_field(self):
        instance_obj = self.get_chosen_item()
        return mark_safe(render_to_string(self.field_template, {
            'field': self.bound_field,
            self.object_type_name: instance_obj,
            'snippet_type_name': self.get_snippet_type_name(),
        }))

    @classmethod
    def get_snippet_type_name(cls):
        return force_text(cls.target_model()._meta.verbose_name)


class SnippetChooserPanel(object):
    def __init__(self, field_name, snippet_type=None):
        self.field_name = field_name
        self.snippet_type = snippet_type

    def bind_to_model(self, model):
        return type(str('_SnippetChooserPanel'), (BaseSnippetChooserPanel,), {
            'model': model,
            'field_name': self.field_name,
            'snippet_type': self.snippet_type,
        })
