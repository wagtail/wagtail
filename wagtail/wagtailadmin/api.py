from wagtail.api.shared.router import WagtailAPIRouter
from wagtail.api.v2.endpoints import PagesAPIEndpoint, ImagesAPIEndpoint, DocumentsAPIEndpoint


class PagesAdminAPIEndpoint(PagesAPIEndpoint):
    pass


class ImagesAdminAPIEndpoint(ImagesAPIEndpoint):
    pass


class DocumentsAdminAPIEndpoint(DocumentsAPIEndpoint):
    pass


admin_api_v1 = WagtailAPIRouter('wagtailadmin_api_v1')
admin_api_v1.register_endpoint('pages', PagesAdminAPIEndpoint)
admin_api_v1.register_endpoint('images', ImagesAdminAPIEndpoint)
admin_api_v1.register_endpoint('documents', DocumentsAdminAPIEndpoint)
