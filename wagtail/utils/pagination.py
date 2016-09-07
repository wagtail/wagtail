from __future__ import absolute_import, unicode_literals

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.utils.http import urlencode
from django.utils.six.moves.urllib.parse import parse_qs


DEFAULT_PAGE_KEY = 'p'


def paginate(request, items, page_key=DEFAULT_PAGE_KEY, per_page=20):
    page = request.GET.get(page_key, 1)

    paginator = Paginator(items, per_page)
    try:
        page = paginator.page(page)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    return paginator, page


def replace_page_in_query(query, page_number, page_key=DEFAULT_PAGE_KEY):
    """
    Replaces ``page_key`` from query string with ``page_number``.

    >>> replace_page_in_query("p=1&key=value", 2)
    'p=2&key=value'
    >>> replace_page_in_query("p=1&key=value", None)
    'key=value'
    """
    getvars = parse_qs(query)
    if page_number is None:
        getvars.pop(page_key, None)
    else:
        getvars[page_key] = page_number
    return urlencode(getvars, True)
