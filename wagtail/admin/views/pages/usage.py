from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils.text import capfirst
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from wagtail.admin.views import generic
from wagtail.admin.views.pages.listing import IndexView
from wagtail.admin.views.pages.utils import (
    GenericPageBreadcrumbsMixin,
)
from wagtail.models import Page


class ContentTypeUseView(IndexView):
    index_url_name = "wagtailadmin_pages:type_use"
    index_results_url_name = "wagtailadmin_pages:type_use_results"
    page_title = _("Pages using")
    header_icon = "doc-empty-inverse"

    def get_table(self, object_list):
        return self.table_class(
            [col for col in self.columns if col.name != "type"],
            object_list,
            **self.get_table_kwargs(),
        )

    def get(self, request, *, content_type_app_name, content_type_model_name):
        # A viewset may assign the "model" attribute to a superclass page model,
        # so look up the most specific model class again based on the app_label
        # and model_name in the URL kwargs.
        content_type = ContentType.objects.get_by_natural_key(
            content_type_app_name, content_type_model_name
        )
        self.model = content_type.model_class()
        return super().get(request)

    def get_page_subtitle(self):
        return self.model._meta.verbose_name

    def get_add_url(self):
        return reverse(
            "wagtailadmin_pages:choose_parent",
            args=[self.model._meta.app_label, self.model._meta.model_name],
        )

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
                "label": capfirst(self.model._meta.verbose_name_plural),
            },
        ]


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
