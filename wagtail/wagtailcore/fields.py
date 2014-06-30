from django.db import models
from django.forms import Textarea
from south.modelsinspector import add_introspection_rules

from wagtail.wagtailcore.rich_text import DbWhitelister, expand_db_html


class RichTextArea(Textarea):
    def get_panel(self):
        from wagtail.wagtailadmin.edit_handlers import RichTextFieldPanel
        return RichTextFieldPanel

class RichTextField(models.TextField):
    def formfield(self, **kwargs):
        defaults = {'widget': RichTextArea}
        defaults.update(kwargs)
        return super(RichTextField, self).formfield(**defaults)

add_introspection_rules([], ["^wagtail\.wagtailcore\.fields\.RichTextField"])
