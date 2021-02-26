from django.core.exceptions import ValidationError
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.core import blocks
from wagtail.embeds.format import embed_to_frontend_html


class EmbedValue:
    """
    Native value of an EmbedBlock. Should, at minimum, have a 'url' property
    and render as the embed HTML when rendered in a template.
    NB We don't use a wagtailembeds.model.Embed object for this, because
    we want to be able to do {% embed value.url 500 %} without
    doing a redundant fetch of the embed at the default width.
    """
    def __init__(self, url, max_width=None, max_height=None):
        self.url = url
        self.max_width = max_width
        self.max_height = max_height

    @cached_property
    def html(self):
        return embed_to_frontend_html(self.url, self.max_width, self.max_height)

    def __str__(self):
        return self.html


class EmbedBlock(blocks.URLBlock):
    def get_default(self):
        # Allow specifying the default for an EmbedBlock as either an EmbedValue or a string (or None).
        if not self.meta.default:
            return None
        elif isinstance(self.meta.default, EmbedValue):
            return self.meta.default
        else:
            # assume default has been passed as a string
            return EmbedValue(self.meta.default, getattr(self.meta, 'max_width', None), getattr(self.meta, 'max_height', None))

    def to_python(self, value):
        # The JSON representation of an EmbedBlock's value is a URL string;
        # this should be converted to an EmbedValue (or None).
        if not value:
            return None
        else:
            return EmbedValue(value, getattr(self.meta, 'max_width', None), getattr(self.meta, 'max_height', None))

    def get_prep_value(self, value):
        # serialisable value should be a URL string
        if value is None:
            return ''
        else:
            return value.url

    def value_for_form(self, value):
        # the value to be handled by the URLField is a plain URL string (or the empty string)
        if value is None:
            return ''
        else:
            return value.url

    def value_from_form(self, value):
        # convert the value returned from the form (a URL string) to an EmbedValue (or None)
        if not value:
            return None
        else:
            return EmbedValue(value, getattr(self.meta, 'max_width', None), getattr(self.meta, 'max_height', None))

    def clean(self, value):
        if isinstance(value, EmbedValue) and not value.html:
            raise ValidationError(_("Cannot find an embed for this URL."))
        return super().clean(value)

    class Meta:
        icon = "media"
