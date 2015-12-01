from wagtail.api.shared.router import WagtailAPIRouter
from wagtail.api.shared.utils import BadRequestError, page_models_from_string, filter_page_type
from wagtail.api.v2.endpoints import PagesAPIEndpoint, ImagesAPIEndpoint, DocumentsAPIEndpoint

from wagtail.wagtailcore.models import Page


class PagesAdminAPIEndpoint(PagesAPIEndpoint):
    def get_queryset(self):
        request = self.request

        # Allow pages to be filtered to a specific type
        try:
            models = page_models_from_string(request.GET.get('type', 'wagtailcore.Page'))
        except (LookupError, ValueError):
            raise BadRequestError("type doesn't exist")

        if not models:
            models = [Page]

        if len(models) == 1:
            queryset = models[0].objects.all()
        else:
            queryset = Page.objects.all()

            # Filter pages by specified models
            queryset = filter_page_type(queryset, models)

        # Hide root page
        # TODO: Add "include_root" flag
        queryset = queryset.exclude(depth=1)

        return queryset


class ImagesAdminAPIEndpoint(ImagesAPIEndpoint):
    pass


class DocumentsAdminAPIEndpoint(DocumentsAPIEndpoint):
    pass


admin_api_v1 = WagtailAPIRouter('wagtailadmin_api_v1')
admin_api_v1.register_endpoint('pages', PagesAdminAPIEndpoint)
admin_api_v1.register_endpoint('images', ImagesAdminAPIEndpoint)
admin_api_v1.register_endpoint('documents', DocumentsAdminAPIEndpoint)
