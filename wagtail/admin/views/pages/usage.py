from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.urls import reverse
from django.utils.functional import cached_property, classproperty
from django.utils.text import capfirst
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from wagtail.admin.views import generic
from wagtail.admin.views.generic.base import BaseListingView
from wagtail.admin.views.generic.permissions import PermissionCheckedMixin
from wagtail.admin.views.pages.listing import PageFilterSet, PageListingMixin
from wagtail.admin.views.pages.utils import (
    GenericPageBreadcrumbsMixin,
)
from wagtail.models import Page
from wagtail.permissions import page_permission_policy


class ContentTypeUseView(PageListingMixin, PermissionCheckedMixin, BaseListingView):
    permission_policy = page_permission_policy
    any_permission_required = {
        "add",
        "change",
        "publish",
        "bulk_delete",
        "lock",
        "unlock",
    }
    index_url_name = "wagtailadmin_pages:type_use"
    index_results_url_name = "wagtailadmin_pages:type_use_results"
    page_title = _("Pages using")
    header_icon = "doc-empty-inverse"
    paginate_by = 50
    filterset_class = PageFilterSet

    @classproperty
    def columns(cls):
        return [col for col in PageListingMixin.columns if col.name != "type"]

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

    @cached_property
    def verbose_name_plural(self):
        return self.page_class._meta.verbose_name_plural

    def get_base_queryset(self):
        queryset = self.page_class._default_manager.all().filter(
            pk__in=self.permission_policy.explorable_instances(
                self.request.user
            ).values_list("pk", flat=True)
        )
        return self.annotate_queryset(queryset)

    def get_index_url(self):
        return reverse(
            self.index_url_name,
            args=[
                self.kwargs["content_type_app_name"],
                self.kwargs["content_type_model_name"],
            ],
        )

    def get_index_results_url(self):
        return reverse(
            self.index_results_url_name,
            args=[
                self.kwargs["content_type_app_name"],
                self.kwargs["content_type_model_name"],
            ],
        )

    def get_breadcrumbs_items(self):
        return self.breadcrumbs_items + [
            # Initially, this page was only accessible via the "choose page type"
            # step of the page creation flow. However, that view might be skipped
            # if there's only one valid page type. Since then, we've introduced
            # the "page types usage" report, which always provides a link to this
            # view for all page types. Use that as the parent link.
            {
                "url": reverse("wagtailadmin_reports:page_types_usage"),
                "label": gettext("Page types usage"),
            },
            {
                "url": self.get_index_url(),
                "label": capfirst(self.page_class._meta.verbose_name_plural),
            },
        ]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_class"] = self.page_class
        return context


class UsageView(GenericPageBreadcrumbsMixin, generic.UsageView):
    model = Page
    pk_url_kwarg = "page_id"
    header_icon = "doc-empty-inverse"
    usage_url_name = "wagtailadmin_pages:usage"
    edit_url_name = "wagtailadmin_pages:edit"

    def dispatch(self, request, *args, **kwargs):
        if not self.object.permissions_for_user(request.user).can_edit():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
