from django.conf import settings
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
            _("Tag(s) %(value_too_long)s are over %(max_tag_length)d characters.")
            % {
                "value_too_long": value_too_long,
                "max_tag_length": max_tag_length,
            }
        )


def validate_tag_spaces(value, tag_model=Tag):
    """
    Reject new tags containing whitespace when WAGTAIL_TAG_SPACES_ALLOWED is False.

    The tag widget only blocks typing a space; pasted or quoted multi-word tags
    still reach the server, so the setting is enforced here.
    Tags that already exist are allowed, so objects carrying multi-word tags
    created before the setting was turned off can still be saved. Existing tags
    are matched the same way django-taggit matches them when saving, which is
    case-insensitively if TAGGIT_CASE_INSENSITIVE is True.
    """
    if not value or getattr(settings, "WAGTAIL_TAG_SPACES_ALLOWED", True):
        return
    tags_with_spaces = [tag for tag in value if any(char.isspace() for char in tag)]
    if not tags_with_spaces:
        return
    if getattr(settings, "TAGGIT_CASE_INSENSITIVE", False):
        new_tags_with_spaces = [
            tag
            for tag in tags_with_spaces
            if not tag_model.objects.filter(name__iexact=tag).exists()
        ]
    else:
        existing = set(
            tag_model.objects.filter(name__in=tags_with_spaces).values_list(
                "name", flat=True
            )
        )
        new_tags_with_spaces = [tag for tag in tags_with_spaces if tag not in existing]
    if new_tags_with_spaces:
        raise ValidationError(
            _("Tag(s) %(tags_with_spaces)s contain spaces, which are not allowed.")
            % {"tags_with_spaces": ", ".join(new_tags_with_spaces)}
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

        validate_tag_spaces(value, self.tag_model)

        return value
