from bs4 import BeautifulSoup
from django.utils.encoding import force_str


def text_from_html(val):
    # Return the unescaped text content of an HTML string
    return BeautifulSoup(force_str(val), "html.parser").getText().strip()
