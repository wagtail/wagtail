from typing import Any, Dict

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.views.generic import ListView

from wagtail.admin.views import generic
from wagtail.models import Page


class ContentTypeUseView(ListView):
    template_name = "wagtailadmin/pages/content_type_use.html"
    page_kwarg = "p"
    paginate_by = 50
    context_object_name = "pages"

    def get(self, request, content_type_app_name, content_type_model_name):
        try:
            content_type = ContentType.objects.get_by_natural_key(
                content_type_app_name, content_type_model_name
            )
        except ContentType.DoesNotExist:
            raise Http404

        self.page_class = content_type.model_class()
        self.content_type_app_name = content_type_app_name
        self.page_content_type = content_type

        # page_class must be a Page type and not some other random model
        if not issubclass(self.page_class, Page):
            raise Http404

        return super().get(request)

    def get_queryset(self):
        return self.page_class.objects.all().specific(defer=True)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "app_name": self.content_type_app_name,
                "content_type": self.page_content_type,
                "page_class": self.page_class,
            }
        )
        return context


class UsageView(generic.UsageView):
    model = Page
    pk_url_kwarg = "page_id"
    header_icon = "doc-empty-inverse"

    def dispatch(self, request, *args, **kwargs):
        if not self.object.permissions_for_user(request.user).can_edit():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
