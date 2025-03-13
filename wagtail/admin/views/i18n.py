from django.views.i18n import JavaScriptCatalog

from wagtail.admin.localization import get_localized_response

js_catalog = JavaScriptCatalog.as_view(packages=["wagtail.admin"])


def localized_js_catalog(request, *args, **kwargs):
    """
    Django's JavaScriptCatalog that has been decorated to ensure it is localized
    in the user's preferred language.
    https://github.com/wagtail/wagtail/issues/11074
    """
    return get_localized_response(js_catalog, request, *args, **kwargs)
