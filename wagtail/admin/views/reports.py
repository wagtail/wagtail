from django.core.paginator import Paginator
from django.shortcuts import render
from wagtail.core.models import UserPagePermissionsProxy


def locked_pages(request):
    pages = UserPagePermissionsProxy(request.user).editable_pages().filter(locked=True)

    paginator = Paginator(pages, per_page=10)
    pages = paginator.get_page(request.GET.get('p'))

    return render(request, 'wagtailadmin/reports/locked_pages.html', {
        'pages': pages,
    })
