from django.core.paginator import Paginator

DEFAULT_PAGE_KEY = 'p'


def paginate(request, items, page_key=DEFAULT_PAGE_KEY, per_page=20):
    paginator = Paginator(items, per_page)
    page = paginator.get_page(request.GET.get(page_key))
    return paginator, page
