from django.utils.translation import gettext_lazy as _

from wagtail.admin.ui.tables import Column, StatusFlagColumn, TitleColumn
from wagtail.admin.views import generic
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.models import Site
from wagtail.permissions import site_permission_policy
from wagtail.sites.forms import SiteForm


class IndexView(generic.IndexView):
    page_title = _("Sites")
    add_item_label = _("Add a site")
    context_object_name = "sites"
    default_ordering = "hostname"
    columns = [
        TitleColumn(
            "hostname",
            label=_("Site"),
            sort_key="hostname",
            url_name="wagtailsites:edit",
        ),
        Column("port", sort_key="port"),
        Column("site_name"),
        Column("root_page"),
        StatusFlagColumn(
            "is_default_site", label=_("Default?"), true_label=_("Default")
        ),
    ]

    def get_base_queryset(self):
        return super().get_base_queryset().select_related("root_page")


class CreateView(generic.CreateView):
    page_title = _("Add site")
    success_message = _("Site '%(object)s' created.")
    error_message = _("The site could not be saved due to errors.")


class EditView(generic.EditView):
    success_message = _("Site '%(object)s' updated.")
    error_message = _("The site could not be saved due to errors.")
    context_object_name = "site"


class DeleteView(generic.DeleteView):
    success_message = _("Site '%(object)s' deleted.")
    page_title = _("Delete site")
    confirmation_message = _("Are you sure you want to delete this site?")


class SiteViewSet(ModelViewSet):
    icon = "site"
    model = Site
    permission_policy = site_permission_policy
    add_to_reference_index = False

    index_view_class = IndexView
    add_view_class = CreateView
    edit_view_class = EditView
    delete_view_class = DeleteView

    template_prefix = "wagtailsites/"

    def get_common_view_kwargs(self, **kwargs):
        return super().get_common_view_kwargs(
            **{
                "history_url_name": None,
                "usage_url_name": None,
                **kwargs,
            }
        )

    def get_form_class(self, for_update=False):
        return SiteForm
