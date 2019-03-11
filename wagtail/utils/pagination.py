from warnings import warn

from django.core.paginator import Paginator

from wagtail.utils.deprecation import RemovedInWagtail27Warning


warn('wagtail.utils.pagination is deprecated. '
     'Use django.core.paginator.Paginator directly with get_page instead',
     category=RemovedInWagtail27Warning)


DEFAULT_PAGE_KEY = 'p'


def paginate(request, items, page_key=DEFAULT_PAGE_KEY, per_page=20):
    paginator = Paginator(items, per_page)
    page = paginator.get_page(request.GET.get(page_key))
    return paginator, page
