from django.utils.six.moves.urllib.parse import urlparse
from django.http import HttpResponseRedirect
from django.core.urlresolvers import resolve, Resolver404


class ModelAdminMiddleware(object):
    """
    Whenever loading wagtail's wagtailadmin_explore or wagtailsnippets_list
    urls, we check the session for a 'return_to_list_url' value (set by an
    AppModelAdmin, PageModelAdmin or SnippetModelAdmin instance via the
    'construct_main_menu' webhook)

    If it looks like we should be returned to a listing page that isn't the
    wagtailadmin_explore or wagtailsnippets_list, we hijack the request and
    redirect to our listing page.
    """

    def process_request(self, request):
        referer_url = request.META.get('HTTP_REFERER')
        return_to_index_url = request.session.get('return_to_index_url')

        """
        There's no point doing anything unless we have a referer_url,
        and return_to_index_url has been set
        """
        if referer_url and return_to_index_url:

            try:
                resolver_match = resolve(request.path)
                if resolver_match.url_name in ['wagtailadmin_explore',
                                               'wagtailsnippets_list']:
                    referer_match = resolve(urlparse(referer_url).path)
                    if referer_match.url_name in (
                        'wagtailadmin_pages_create',
                        'wagtailadmin_pages_edit',
                        'wagtailadmin_pages_delete',
                        'wagtailadmin_pages_unpublish',
                        'wagtailsnippets_create',
                        'wagtailsnippets_edit',
                        'wagtailsnippets_delete',
                    ):
                        del request.session['return_to_index_url']
                        return HttpResponseRedirect(return_to_index_url)
            except Resolver404:
                pass

        return None
