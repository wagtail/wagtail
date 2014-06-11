from wagtail.wagtailcore import hooks

def check_view_restrictions(page, request, serve_args, serve_kwargs):
    return page.check_view_restrictions(request)
hooks.register('before_serve_page', check_view_restrictions)
