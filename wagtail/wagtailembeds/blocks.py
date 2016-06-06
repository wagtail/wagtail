from __future__ import absolute_import, unicode_literals

from django.utils.encoding import python_2_unicode_compatible

from wagtail.wagtailcore import blocks
from wagtail.wagtailembeds.format import embed_to_frontend_html


@python_2_unicode_compatible
class EmbedValue(object):
    """
    Native value of an EmbedBlock. Should, at minimum, have a 'url' property
    and render as the embed HTML when rendered in a template.
    NB We don't use a wagtailembeds.model.Embed object for this, because
    we want to be able to do {{ value.url|embed:max_width=500 }} without
    doing a redundant fetch of the embed at the default width.
    """
    def __init__(self, url):
        self.url = url

    def __str__(self):
        return embed_to_frontend_html(self.url)


class EmbedBlock(blocks.URLBlock):
    def get_default(self):
        # Allow specifying the default for an EmbedBlock as either an EmbedValue or a string (or None).
        if not self.meta.default:
            return None
        elif isinstance(self.meta.default, EmbedValue):
            return self.meta.default
        else:
            # assume default has been passed as a string
            return EmbedValue(self.meta.default)

    def to_python(self, value):
        # The JSON representation of an EmbedBlock's value is a URL string;
        # this should be converted to an EmbedValue (or None).
        if not value:
            return None
        else:
            return EmbedValue(value)

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
            return EmbedValue(value)

    class Meta:
        icon = "media"
