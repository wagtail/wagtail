from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import Http404
from django.template.response import TemplateResponse
from django.views.generic import View

from wagtail.admin.views import generic
from wagtail.models import Page


class ContentTypeUseView(View):
    def get(self, request, content_type_app_name, content_type_model_name):
        try:
            content_type = ContentType.objects.get_by_natural_key(
                content_type_app_name, content_type_model_name
            )
        except ContentType.DoesNotExist:
            raise Http404

        page_class = content_type.model_class()

        # page_class must be a Page type and not some other random model
        if not issubclass(page_class, Page):
            raise Http404

        pages = page_class.objects.all().specific(defer=True)

        paginator = Paginator(pages, per_page=10)
        pages = paginator.get_page(request.GET.get("p"))

        return TemplateResponse(
            request,
            "wagtailadmin/pages/content_type_use.html",
            {
                "pages": pages,
                "app_name": content_type_app_name,
                "content_type": content_type,
                "page_class": page_class,
            },
        )


class UsageView(generic.UsageView):
    model = Page
    pk_url_kwarg = "page_id"
    header_icon = "doc-empty-inverse"

    def dispatch(self, request, *args, **kwargs):
        if not self.object.permissions_for_user(request.user).can_edit():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
