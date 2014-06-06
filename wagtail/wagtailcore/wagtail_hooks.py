from wagtail.wagtailcore import hooks

def check_view_restrictions(page, request):
    return page.check_view_restrictions(request)
hooks.register('before_serve_page', check_view_restrictions)
