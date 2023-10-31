from django.contrib.auth.models import Group
from django.urls import re_path
from django.utils.translation import gettext_lazy as _

from wagtail import hooks
from wagtail.admin.ui.tables import TitleColumn
from wagtail.admin.views import generic
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.users.forms import GroupForm, GroupPagePermissionFormSet
from wagtail.users.views.users import Index

_permission_panel_classes = None


def get_permission_panel_classes():
    global _permission_panel_classes
    if _permission_panel_classes is None:
        _permission_panel_classes = [GroupPagePermissionFormSet]
        for fn in hooks.get_hooks("register_group_permission_panel"):
            _permission_panel_classes.append(fn())

    return _permission_panel_classes


class PermissionPanelFormsMixin:
    def get_permission_panel_form_kwargs(self, cls):
        kwargs = {}

        if self.request.method in ("POST", "PUT"):
            kwargs.update(
                {
                    "data": self.request.POST,
                    "files": self.request.FILES,
                }
            )

        if hasattr(self, "object"):
            kwargs.update({"instance": self.object})

        return kwargs

    def get_permission_panel_forms(self):
        return [
            cls(**self.get_permission_panel_form_kwargs(cls))
            for cls in get_permission_panel_classes()
        ]

    def get_context_data(self, **kwargs):
        if "permission_panels" not in kwargs:
            kwargs["permission_panels"] = self.get_permission_panel_forms()

        return super().get_context_data(**kwargs)


class IndexView(generic.IndexView):
    page_title = _("Groups")
    add_item_label = _("Add a group")
    search_box_placeholder = _("Search groups")
    search_fields = ["name"]
    context_object_name = "groups"
    paginate_by = 20

    columns = [
        TitleColumn(
            "name",
            label=_("Name"),
            sort_key="name",
            url_name="wagtailusers_groups:edit",
        ),
    ]


class CreateView(PermissionPanelFormsMixin, generic.CreateView):
    page_title = _("Add group")
    success_message = _("Group '%(object)s' created.")

    def get_page_subtitle(self):
        return ""

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        # Create an object now so that the permission panel forms have something to link them against
        self.object = Group()

        form = self.get_form()
        permission_panels = self.get_permission_panel_forms()
        if form.is_valid() and all(panel.is_valid() for panel in permission_panels):
            response = self.form_valid(form)

            for panel in permission_panels:
                panel.save()

            return response
        else:
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # add a 'form_media' variable for the collected js/css media from the form and all formsets
        form_media = context["form"].media
        for panel in context["permission_panels"]:
            form_media += panel.media
        context["form_media"] = form_media

        return context


class EditView(PermissionPanelFormsMixin, generic.EditView):
    success_message = _("Group '%(object)s' updated.")
    error_message = _("The group could not be saved due to errors.")
    delete_item_label = _("Delete group")
    context_object_name = "group"

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        self.object = self.get_object()

        form = self.get_form()
        permission_panels = self.get_permission_panel_forms()
        if form.is_valid() and all(panel.is_valid() for panel in permission_panels):
            response = self.form_valid(form)

            for panel in permission_panels:
                panel.save()

            return response
        else:
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # add a 'form_media' variable for the collected js/css media from the form and all formsets
        form_media = context["form"].media
        for panel in context["permission_panels"]:
            form_media += panel.media
        context["form_media"] = form_media

        return context


class DeleteView(generic.DeleteView):
    success_message = _("Group '%(object)s' deleted.")
    page_title = _("Delete group")
    confirmation_message = _("Are you sure you want to delete this group?")


class GroupViewSet(ModelViewSet):
    icon = "group"
    model = Group
    ordering = ["name"]
    add_to_reference_index = False
    _show_breadcrumbs = False

    index_view_class = IndexView
    add_view_class = CreateView
    edit_view_class = EditView
    delete_view_class = DeleteView

    template_prefix = "wagtailusers/groups/"

    @property
    def users_view(self):
        return Index.as_view()

    @property
    def users_results_view(self):
        return Index.as_view(results_only=True)

    def get_common_view_kwargs(self, **kwargs):
        return super().get_common_view_kwargs(
            **{
                "history_url_name": None,
                "usage_url_name": None,
                **kwargs,
            }
        )

    def get_form_class(self, for_update=False):
        return GroupForm

    def get_urlpatterns(self):
        return super().get_urlpatterns() + [
            re_path(r"(\d+)/users/$", self.users_view, name="users"),
            re_path(
                r"(\d+)/users/results/$", self.users_results_view, name="users_results"
            ),
        ]
