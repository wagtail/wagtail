import json

from django.conf import settings
from django.urls import reverse
from taggit.forms import TagWidget
from taggit.models import Tag


class AdminTagWidget(TagWidget):
    template_name = 'wagtailadmin/widgets/tag_widget.html'

    def __init__(self, *args, **kwargs):
        self.tag_model = kwargs.pop('tag_model', Tag)
        # free_tagging = None means defer to the tag model's setting
        self.free_tagging = kwargs.pop('free_tagging', None)
        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        if self.tag_model == Tag:
            autocomplete_url = reverse('wagtailadmin_tag_autocomplete')
        else:
            autocomplete_url = reverse(
                'wagtailadmin_tag_model_autocomplete',
                args=(self.tag_model._meta.app_label, self.tag_model._meta.model_name)
            )

        if self.free_tagging is None:
            free_tagging = getattr(self.tag_model, 'free_tagging', True)
        else:
            free_tagging = self.free_tagging

        context['widget']['autocomplete_url'] = autocomplete_url
        context['widget']['options_json'] = json.dumps({
            'allowSpaces': getattr(settings, 'TAG_SPACES_ALLOWED', True),
            'tagLimit': getattr(settings, 'TAG_LIMIT', None),
            'autocompleteOnly': not free_tagging,
        })

        return context
