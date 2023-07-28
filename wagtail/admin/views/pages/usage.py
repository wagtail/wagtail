from typing import Any, Dict

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from wagtail.admin.ui.tables import Column, DateColumn
from wagtail.admin.ui.tables.pages import (
    PageStatusColumn,
    PageTable,
    PageTitleColumn,
    ParentPageColumn,
)
from wagtail.admin.views import generic
from wagtail.admin.views.generic.base import BaseListingView
from wagtail.models import Page


class ContentTypeUseView(BaseListingView):
    results_template_name = "wagtailadmin/pages/usage_results.html"
    page_title = _("Pages using")
    header_icon = "doc-empty-inverse"
    page_kwarg = "p"
    paginate_by = 50
    columns = [
        PageTitleColumn("title", label=_("Title")),
        ParentPageColumn("parent", label=_("Parent")),
        DateColumn("latest_revision_created_at", label=_("Updated"), width="12%"),
        Column("type", label=_("Type"), accessor="page_type_display_name", width="12%"),
        PageStatusColumn("status", label=_("Status"), width="12%"),
    ]
    table_class = PageTable
    table_classname = "listing align-top"

    def get(self, request, *, content_type_app_name, content_type_model_name):
        try:
            content_type = ContentType.objects.get_by_natural_key(
                content_type_app_name, content_type_model_name
            )
        except ContentType.DoesNotExist:
            raise Http404

        self.page_class = content_type.model_class()

        # page_class must be a Page type and not some other random model
        if not issubclass(self.page_class, Page):
            raise Http404

        return super().get(request)

    def get_page_subtitle(self):
        return self.page_class.get_verbose_name()

    def get_queryset(self):
        return self.page_class.objects.all().specific(defer=True)

    def get_index_url(self):
        return reverse(
            "wagtailadmin_pages:type_use",
            args=[
                self.kwargs["content_type_app_name"],
                self.kwargs["content_type_model_name"],
            ],
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "index_url": self.get_index_url(),
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
