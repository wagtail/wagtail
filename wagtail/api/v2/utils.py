from urllib.parse import urlparse

from django.conf import settings
from django.utils.encoding import force_str

from wagtail.core.models import Page, Site
from wagtail.core.utils import resolve_model_string


class BadRequestError(Exception):
    pass


def get_base_url(request=None):
    base_url = getattr(settings, 'WAGTAILAPI_BASE_URL', None)

    if base_url is None and request:
        site = Site.find_for_request(request)
        if site:
            base_url = site.root_url

    if base_url:
        # We only want the scheme and netloc
        base_url_parsed = urlparse(force_str(base_url))

        return base_url_parsed.scheme + '://' + base_url_parsed.netloc


def get_full_url(request, path):
    base_url = get_base_url(request) or ''
    return base_url + path


def get_object_detail_url(router, request, model, pk):
    url_path = router.get_object_detail_urlpath(model, pk)

    if url_path:
        return get_full_url(request, url_path)


def page_models_from_string(string):
    page_models = []

    for sub_string in string.split(','):
        page_model = resolve_model_string(sub_string)

        if not issubclass(page_model, Page):
            raise ValueError("Model is not a page")

        page_models.append(page_model)

    return tuple(page_models)


def filter_page_type(queryset, page_models):
    qs = queryset.none()

    for model in page_models:
        qs |= queryset.type(model)

    return qs


class FieldsParameterParseError(ValueError):
    pass


def parse_fields_parameter(fields_str):
    """
    Parses the ?fields= GET parameter. As this parameter is supposed to be used
    by developers, the syntax is quite tight (eg, not allowing any whitespace).
    Having a strict syntax allows us to extend the it at a later date with less
    chance of breaking anyone's code.

    This function takes a string and returns a list of tuples representing each
    top-level field. Each tuple contains three items:
     - The name of the field (string)
     - Whether the field has been negated (boolean)
     - A list of nested fields if there are any, None otherwise

    Some examples of how this function works:

    >>> parse_fields_parameter("foo")
    [
        ('foo', False, None),
    ]

    >>> parse_fields_parameter("foo,bar")
    [
        ('foo', False, None),
        ('bar', False, None),
    ]

    >>> parse_fields_parameter("-foo")
    [
        ('foo', True, None),
    ]

    >>> parse_fields_parameter("foo(bar,baz)")
    [
        ('foo', False, [
            ('bar', False, None),
            ('baz', False, None),
        ]),
    ]

    It raises a FieldsParameterParseError (subclass of ValueError) if it
    encounters a syntax error
    """

    def get_position(current_str):
        return len(fields_str) - len(current_str)

    def parse_field_identifier(fields_str):
        first_char = True
        negated = False
        ident = ""

        while fields_str:
            char = fields_str[0]

            if char in ['(', ')', ',']:
                if not ident:
                    raise FieldsParameterParseError("unexpected char '%s' at position %d" % (char, get_position(fields_str)))

                if ident in ['*', '_'] and char == '(':
                    # * and _ cannot have nested fields
                    raise FieldsParameterParseError("unexpected char '%s' at position %d" % (char, get_position(fields_str)))

                return ident, negated, fields_str

            elif char == '-':
                if not first_char:
                    raise FieldsParameterParseError("unexpected char '%s' at position %d" % (char, get_position(fields_str)))

                negated = True

            elif char in ['*', '_']:
                if ident and char == '*':
                    raise FieldsParameterParseError("unexpected char '%s' at position %d" % (char, get_position(fields_str)))

                ident += char

            elif char.isalnum() or char == '_':
                if ident == '*':
                    # * can only be on its own
                    raise FieldsParameterParseError("unexpected char '%s' at position %d" % (char, get_position(fields_str)))

                ident += char

            elif char.isspace():
                raise FieldsParameterParseError("unexpected whitespace at position %d" % get_position(fields_str))
            else:
                raise FieldsParameterParseError("unexpected char '%s' at position %d" % (char, get_position(fields_str)))

            first_char = False
            fields_str = fields_str[1:]

        return ident, negated, fields_str

    def parse_fields(fields_str, expect_close_bracket=False):
        first_ident = None
        is_first = True
        fields = []

        while fields_str:
            sub_fields = None
            ident, negated, fields_str = parse_field_identifier(fields_str)

            # Some checks specific to '*' and '_'
            if ident in ['*', '_']:
                if not is_first:
                    raise FieldsParameterParseError("'%s' must be in the first position" % ident)

                if negated:
                    raise FieldsParameterParseError("'%s' cannot be negated" % ident)

            if fields_str and fields_str[0] == '(':
                if negated:
                    # Negated fields cannot contain subfields
                    raise FieldsParameterParseError("unexpected char '(' at position %d" % get_position(fields_str))

                sub_fields, fields_str = parse_fields(fields_str[1:], expect_close_bracket=True)

            if is_first:
                first_ident = ident
            else:
                # Negated fields can't be used with '_'
                if first_ident == '_' and negated:
                    # _,foo is allowed but _,-foo is not
                    raise FieldsParameterParseError("negated fields with '_' doesn't make sense")

                # Additional fields without sub fields can't be used with '*'
                if first_ident == '*' and not negated and not sub_fields:
                    # *,foo(bar) and *,-foo are allowed but *,foo is not
                    raise FieldsParameterParseError("additional fields with '*' doesn't make sense")

            fields.append((ident, negated, sub_fields))

            if fields_str and fields_str[0] == ')':
                if not expect_close_bracket:
                    raise FieldsParameterParseError("unexpected char ')' at position %d" % get_position(fields_str))

                return fields, fields_str[1:]

            if fields_str and fields_str[0] == ',':
                fields_str = fields_str[1:]

                # A comma can not exist immediately before another comma or the end of the string
                if not fields_str or fields_str[0] == ',':
                    raise FieldsParameterParseError("unexpected char ',' at position %d" % get_position(fields_str))

            is_first = False

        if expect_close_bracket:
            # This parser should've exited with a close bracket but instead we
            # hit the end of the input. Raise an error
            raise FieldsParameterParseError("unexpected end of input (did you miss out a close bracket?)")

        return fields, fields_str

    fields, _ = parse_fields(fields_str)

    return fields


def parse_boolean(value):
    """
    Parses strings into booleans using the following mapping (case-sensitive):

    'true'   => True
    'false'  => False
    '1'      => True
    '0'      => False
    """
    if value in ['true', '1']:
        return True
    elif value in ['false', '0']:
        return False
    else:
        raise ValueError("expected 'true' or 'false', got '%s'" % value)
