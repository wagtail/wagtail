from warnings import warn

import django_filters
from django.conf import settings
from django.contrib.auth import (
    get_user_model,
    update_session_auth_hash,
)
from django.contrib.auth.models import Group
from django.core.exceptions import FieldDoesNotExist, PermissionDenied
from django.db.models import Q
from django.forms import CheckboxSelectMultiple
from django.template import RequestContext
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from wagtail import hooks
from wagtail.admin.filters import DateRangePickerWidget, WagtailFilterSet
from wagtail.admin.search import SearchArea
from wagtail.admin.ui.tables import (
    BulkActionsCheckboxColumn,
    Column,
    DateColumn,
    StatusTagColumn,
    TitleColumn,
)
from wagtail.admin.utils import get_user_display_name
from wagtail.admin.views import generic
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.admin.widgets.boolean_radio_select import BooleanRadioSelect
from wagtail.admin.widgets.button import (
    BaseDropdownMenuButton,
    ButtonWithDropdown,
)
from wagtail.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME
from wagtail.coreutils import accepts_kwarg
from wagtail.users.forms import UserCreationForm, UserEditForm
from wagtail.users.utils import user_can_delete_user
from wagtail.utils.deprecation import RemovedInWagtail70Warning
from wagtail.utils.loading import get_custom_form

User = get_user_model()

# Typically we would check the permission 'auth.change_user' (and 'auth.add_user' /
# 'auth.delete_user') for user management actions, but this may vary according to
# the AUTH_USER_MODEL setting. These are no longer used in the codebase in favour
# of ModelPermissionPolicy, but are kept here for backwards compatibility.
add_user_perm = f"{AUTH_USER_APP_LABEL}.add_{AUTH_USER_MODEL_NAME.lower()}"
change_user_perm = "{}.change_{}".format(
    AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower()
)
delete_user_perm = "{}.delete_{}".format(
    AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower()
)


def get_user_creation_form():
    form_setting = "WAGTAIL_USER_CREATION_FORM"
    if hasattr(settings, form_setting):
        warn(
            "The `WAGTAIL_USER_CREATION_FORM` setting is deprecated. Use a custom "
            "`UserViewSet` subclass and override `get_form_class()` instead.",
            RemovedInWagtail70Warning,
        )
        return get_custom_form(form_setting)
    else:
        return UserCreationForm


def get_user_edit_form():
    form_setting = "WAGTAIL_USER_EDIT_FORM"
    if hasattr(settings, form_setting):
        warn(
            "The `WAGTAIL_USER_EDIT_FORM` setting is deprecated. Use a custom "
            "`UserViewSet` subclass and override `get_form_class()` instead.",
            RemovedInWagtail70Warning,
        )
        return get_custom_form(form_setting)
    else:
        return UserEditForm


def get_users_filter_query(q, model_fields):
    conditions = Q()

    for term in q.split():
        if "username" in model_fields:
            conditions |= Q(username__icontains=term)

        if "first_name" in model_fields:
            conditions |= Q(first_name__icontains=term)

        if "last_name" in model_fields:
            conditions |= Q(last_name__icontains=term)

        if "email" in model_fields:
            conditions |= Q(email__icontains=term)

    return conditions


class UserColumn(TitleColumn):
    cell_template_name = "wagtailusers/users/user_cell.html"


class UserFilterSet(WagtailFilterSet):
    is_superuser = django_filters.BooleanFilter(
        label=gettext_lazy("Administrator"),
        widget=BooleanRadioSelect,
    )
    last_login = django_filters.DateFromToRangeFilter(
        label=gettext_lazy("Last login"),
        widget=DateRangePickerWidget,
    )
    group = django_filters.ModelMultipleChoiceFilter(
        field_name="groups",
        queryset=Group.objects.all(),
        label=gettext_lazy("Group"),
        widget=CheckboxSelectMultiple,
    )

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(data, queryset, request=request, prefix=prefix)
        try:
            self._meta.model._meta.get_field("is_active")
        except FieldDoesNotExist:
            pass
        else:
            self.filters["is_active"] = django_filters.BooleanFilter(
                field_name="is_active",
                label=gettext_lazy("Active"),
                widget=BooleanRadioSelect,
            )
            self.filters.move_to_end("is_active", last=False)

    class Meta:
        model = User
        fields = []


class IndexView(generic.IndexView):
    """
    Lists the users for management within the admin.
    """

    template_name = "wagtailusers/users/index.html"
    results_template_name = "wagtailusers/users/index_results.html"
    add_item_label = gettext_lazy("Add a user")
    context_object_name = "users"
    # We don't set search_fields and the model may not be indexed, but we override
    # search_queryset, so we set is_searchable to True to enable search
    is_searchable = True
    page_title = gettext_lazy("Users")
    show_other_searches = True

    @cached_property
    def columns(self):
        _UserColumn = self._get_title_column_class(UserColumn)
        return [
            BulkActionsCheckboxColumn("bulk_actions", obj_type="user"),
            _UserColumn(
                "name",
                accessor=lambda u: get_user_display_name(u),
                label=gettext_lazy("Name"),
                sort_key="name"
                if self.model_fields.issuperset({"first_name", "last_name"})
                else None,
                get_url=self.get_edit_url,
                classname="name",
            ),
            Column(
                self.model.USERNAME_FIELD,
                accessor="get_username",
                label=gettext_lazy("Username"),
                sort_key=self.model.USERNAME_FIELD,
                classname="username",
                width="20%",
            ),
            Column(
                "is_superuser",
                accessor=lambda u: gettext_lazy("Admin") if u.is_superuser else None,
                label=gettext_lazy("Access level"),
                sort_key="is_superuser",
                classname="level",
                width="10%",
            ),
            StatusTagColumn(
                "is_active",
                accessor=lambda u: gettext_lazy("Active")
                if u.is_active
                else gettext_lazy("Inactive"),
                primary=lambda u: u.is_active,
                label=gettext_lazy("Status"),
                sort_key="is_active" if "is_active" in self.model_fields else None,
                classname="status",
                width="10%",
            ),
            DateColumn(
                "last_login",
                label=gettext_lazy("Last login"),
                sort_key="last_login",
                classname="last-login",
                width="15%",
            ),
        ]

    @cached_property
    def model_fields(self):
        return {f.name for f in User._meta.get_fields()}

    def get_delete_url(self, instance):
        if user_can_delete_user(self.request.user, instance):
            return super().get_delete_url(instance)

    def get_list_buttons(self, instance):
        more_buttons = self.get_list_more_buttons(instance)
        list_buttons = []

        for hook in hooks.get_hooks("register_user_listing_buttons"):
            if accepts_kwarg(hook, "request_user"):
                hook_buttons = hook(user=instance, request_user=self.request.user)
            else:
                # old-style hook that accepts a context argument instead of request_user
                hook_buttons = hook(RequestContext(self.request), instance)
                warn(
                    "`register_user_listing_buttons` hook functions should accept a `request_user` argument instead of `context` -"
                    f" {hook.__module__}.{hook.__name__} needs to be updated",
                    category=RemovedInWagtail70Warning,
                )

            for button in hook_buttons:
                if isinstance(button, BaseDropdownMenuButton):
                    # If the button is a dropdown menu, add it to the top-level
                    # because we do not support nested dropdowns
                    list_buttons.append(button)
                else:
                    # Otherwise, add it to the default "More" dropdown
                    more_buttons.append(button)

        list_buttons.append(
            ButtonWithDropdown(
                buttons=sorted(more_buttons),
                icon_name="dots-horizontal",
                attrs={
                    "aria-label": _("More options for '%(title)s'")
                    % {"title": str(instance)},
                },
            )
        )

        return sorted(list_buttons)

    def get_base_queryset(self):
        users = User._default_manager.all()

        if "wagtail_userprofile" in self.model_fields:
            users = users.select_related("wagtail_userprofile")

        return users

    def order_queryset(self, queryset):
        if self.ordering == "name":
            return queryset.order_by("last_name", "first_name")
        if self.ordering == "-name":
            return queryset.order_by("-last_name", "-first_name")
        return super().order_queryset(queryset)

    def search_queryset(self, queryset):
        if self.is_searching:
            conditions = get_users_filter_query(self.search_query, self.model_fields)
            return queryset.filter(conditions)
        return queryset


class CreateView(generic.CreateView):
    """
    Provide the ability to create a user within the admin.
    """

    success_message = gettext_lazy("User '%(object)s' created.")
    page_title = gettext_lazy("Add user")

    def run_before_hook(self):
        return self.run_hook(
            "before_create_user",
            self.request,
        )

    def run_after_hook(self):
        return self.run_hook(
            "after_create_user",
            self.request,
            self.object,
        )


class EditView(generic.EditView):
    """
    Provide the ability to edit a user within the admin.
    """

    success_message = gettext_lazy("User '%(object)s' updated.")
    error_message = gettext_lazy("The user could not be saved due to errors.")
    context_object_name = "user"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.object = self.get_object()
        self.can_delete = user_can_delete_user(request.user, self.object)
        self.editing_self = request.user == self.object

    def save_instance(self):
        instance = super().save_instance()
        if self.object == self.request.user and "password1" in self.form.changed_data:
            # User is changing their own password; need to update their session hash
            update_session_auth_hash(self.request, self.object)
        return instance

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {
                "editing_self": self.editing_self,
            }
        )
        return kwargs

    def run_before_hook(self):
        return self.run_hook(
            "before_edit_user",
            self.request,
            self.object,
        )

    def run_after_hook(self):
        return self.run_hook(
            "after_edit_user",
            self.request,
            self.object,
        )

    def get_page_subtitle(self):
        return get_user_display_name(self.object)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_delete"] = self.can_delete
        return context


class DeleteView(generic.DeleteView):
    """
    Provide the ability to delete a user within the admin.
    """

    page_title = gettext_lazy("Delete user")
    success_message = gettext_lazy("User '%(object)s' deleted.")
    context_object_name = "user"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not user_can_delete_user(self.request.user, self.object):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def run_before_hook(self):
        return self.run_hook(
            "before_delete_user",
            self.request,
            self.object,
        )

    def run_after_hook(self):
        return self.run_hook(
            "after_delete_user",
            self.request,
            self.object,
        )


class HistoryView(generic.HistoryView):
    def get_page_subtitle(self):
        return get_user_display_name(self.object)


class UserViewSet(ModelViewSet):
    icon = "user"
    model = User
    ordering = "name"
    add_to_reference_index = False
    filterset_class = UserFilterSet
    menu_name = "users"
    menu_label = gettext_lazy("Users")
    menu_order = 600
    add_to_settings_menu = True

    index_view_class = IndexView
    add_view_class = CreateView
    edit_view_class = EditView
    delete_view_class = DeleteView
    history_view_class = HistoryView

    template_prefix = "wagtailusers/users/"

    def get_common_view_kwargs(self, **kwargs):
        return super().get_common_view_kwargs(
            **{
                "usage_url_name": None,
                **kwargs,
            }
        )

    def get_form_class(self, for_update=False):
        if for_update:
            return get_user_edit_form()
        return get_user_creation_form()

    @cached_property
    def search_area_class(self):
        class UsersSearchArea(SearchArea):
            def is_shown(search_area, request):
                return self.permission_policy.user_has_any_permission(
                    request.user, {"add", "change", "delete"}
                )

        return UsersSearchArea

    def get_search_area(self):
        return self.search_area_class(
            gettext_lazy("Users"),
            reverse(self.get_url_name("index")),
            name="users",
            icon_name="user",
            order=600,
        )

    def register_search_area(self):
        hooks.register("register_admin_search_area", self.get_search_area)

    def on_register(self):
        super().on_register()
        self.register_search_area()
