import re

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

WHITESPACE_RE = re.compile(r'^\s+$')


def validate_not_whitespace(value):
    """
    Validate that a value isn't all whitespace, for example in title and
    seo_title
    """
    if value and WHITESPACE_RE.match(value):
        raise ValidationError(_('Value cannot be entirely whitespace characters'))
