from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from taggit.forms import TagField as TaggitTagField
from taggit.models import Tag, TagBase

from wagtail.admin.widgets import AdminTagWidget


def validate_tag_length(
    value, max_tag_length=TagBase._meta.get_field("name").max_length
):
    if not value:
        return
    value_too_long = ""
    for val in value:
        if len(val) > max_tag_length:
            if value_too_long:
                value_too_long += ", "
            value_too_long += val
    if value_too_long:
        raise ValidationError(
            _("Tag(s) %(value_too_long)s are over %(max_tag_length)d characters")
            % {
                "value_too_long": value_too_long,
                "max_tag_length": max_tag_length,
            }
        )


class TagField(TaggitTagField):
    """
    Extends taggit's TagField with the option to prevent creating tags that do not already exist
    """

    widget = AdminTagWidget

    def __init__(self, *args, **kwargs):
        self.tag_model = kwargs.pop("tag_model", None)
        self.free_tagging = kwargs.pop("free_tagging", None)

        super().__init__(*args, **kwargs)

        # pass on tag_model and free_tagging kwargs to the widget,
        # if (and only if) they have been passed explicitly here.
        # Otherwise, set default values for clean() to use
        if self.tag_model is None:
            self.tag_model = Tag
        else:
            self.widget.tag_model = self.tag_model

        if self.free_tagging is None:
            self.free_tagging = getattr(self.tag_model, "free_tagging", True)
        else:
            self.widget.free_tagging = self.free_tagging

    def clean(self, value):
        value = super().clean(value)
        validate_tag_length(value, self.tag_model.name.field.max_length)

        if not self.free_tagging:
            # filter value to just the tags that already exist in tag_model
            value = list(
                self.tag_model.objects.filter(name__in=value).values_list(
                    "name", flat=True
                )
            )

        return value
