from .views import SiteModule


urlpatterns = SiteModule('wagtailsites').get_urlpatterns()
