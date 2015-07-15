from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


def paginate(request, items, page_key='p', per_page=20):
    page = request.GET.get(page_key, 1)

    paginator = Paginator(items, per_page)
    try:
        page = paginator.page(page)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    return paginator, page
