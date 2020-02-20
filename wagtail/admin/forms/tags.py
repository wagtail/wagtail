from taggit.forms import TagField as TaggitTagField
from taggit.models import Tag

from wagtail.admin.widgets import AdminTagWidget


class TagField(TaggitTagField):
    """
    Extends taggit's TagField with the option to prevent creating tags that do not already exist
    """
    widget = AdminTagWidget

    def __init__(self, *args, **kwargs):
        self.tag_model = kwargs.pop('tag_model', None)
        self.free_tagging = kwargs.pop('free_tagging', None)

        super().__init__(*args, **kwargs)

        # pass on tag_model and free_tagging kwargs to the widget,
        # if (and only if) they have been passed explicitly here.
        # Otherwise, set default values for clean() to use
        if self.tag_model is None:
            self.tag_model = Tag
        else:
            self.widget.tag_model = self.tag_model

        if self.free_tagging is None:
            self.free_tagging = getattr(self.tag_model, 'free_tagging', True)
        else:
            self.widget.free_tagging = self.free_tagging

    def clean(self, value):
        value = super().clean(value)

        if not self.free_tagging:
            # filter value to just the tags that already exist in tag_model
            value = list(
                self.tag_model.objects.filter(name__in=value).values_list('name', flat=True)
            )

        return value
