from django.utils.six import string_types
import antispam


def is_spam(data):
    text_content = ""

    for value in data.itervalues():
        if isinstance(value, string_types):
            text_content += " " + value

    return antispam.is_spam(text_content) if text_content else False
