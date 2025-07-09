import django_filters
from django.contrib.auth import (
    get_user_model,
    update_session_auth_hash,
)
from django.contrib.auth.models import Group
from django.core.exceptions import FieldDoesNotExist, PermissionDenied
from django.forms import CheckboxSelectMultiple
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from wagtail import hooks
from wagtail.admin.filters import (
    DateRangePickerWidget,
    RelatedFilterMixin,
    WagtailFilterSet,
)
from wagtail.admin.search import SearchArea
from wagtail.admin.ui.menus import MenuItem
from wagtail.admin.ui.tables import (
    BooleanColumn,
    BulkActionsCheckboxColumn,
    Column,
    DateColumn,
    TitleColumn,
)
from wagtail.admin.utils import get_user_display_name
from wagtail.admin.views import generic
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.admin.widgets.boolean_radio_select import BooleanRadioSelect
from wagtail.admin.widgets.button import (
    BaseButton,
    Button,
    ButtonWithDropdown,
)
from wagtail.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME
from wagtail.search import index
from wagtail.users.forms import UserCreationForm, UserEditForm
from wagtail.users.utils import user_can_delete_user

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


class UserColumn(TitleColumn):
    cell_template_name = "wagtailusers/users/user_cell.html"


class GroupFilter(RelatedFilterMixin, django_filters.ModelMultipleChoiceFilter):
    pass


class UserFilterSet(WagtailFilterSet):
    is_superuser = django_filters.BooleanFilter(
        label=gettext_lazy("Administrator"),
        widget=BooleanRadioSelect,
    )
    last_login = django_filters.DateFromToRangeFilter(
        label=gettext_lazy("Last login"),
        widget=DateRangePickerWidget,
    )

    def __init__(
        self, data=None, queryset=None, *, request=None, prefix=None, is_searching=False
    ):
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

        self.filters["group"] = GroupFilter(
            field_name="groups",
            queryset=Group.objects.all(),
            label=gettext_lazy("Group"),
            use_subquery=is_searching,
            widget=CheckboxSelectMultiple,
        )

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
            BooleanColumn(
                "is_active",
                label=gettext_lazy("Active"),
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

    @cached_property
    def search_fields(self):
        # Use search_fields from the model if we're using Wagtail search
        if index.class_is_indexed(User) and self.search_backend_name:
            return None
        return self.model_fields & {"username", "first_name", "last_name", "email"}

    def get_filterset_kwargs(self):
        kwargs = super().get_filterset_kwargs()
        kwargs["is_searching"] = self.is_searching
        return kwargs

    def get_delete_url(self, instance):
        if user_can_delete_user(self.request.user, instance):
            return super().get_delete_url(instance)

    def get_list_buttons(self, instance):
        more_buttons = []
        list_buttons = []

        buttons = self.get_list_more_buttons(instance)
        for hook in hooks.get_hooks("register_user_listing_buttons"):
            buttons.extend(hook(user=instance, request_user=self.request.user))

        for button in buttons:
            if isinstance(button, BaseButton) and not button.allow_in_dropdown:
                # If the button is not allowed in a dropdown menu, add it to
                # the top-level list of buttons
                list_buttons.append(button)
            elif isinstance(button, MenuItem):
                # Allow simple MenuItem instances to be passed in directly
                if button.is_shown(self.request.user):
                    more_buttons.append(Button.from_menu_item(button))
            elif button.show:
                # Otherwise, add it to the default "More" dropdown
                more_buttons.append(button)

        list_buttons.append(
            ButtonWithDropdown(
                buttons=more_buttons,
                icon_name="dots-horizontal",
                attrs={
                    "aria-label": _("More options for '%(title)s'")
                    % {"title": str(instance)},
                },
            )
        )

        return list_buttons

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

    def get_form_class(self, for_update=False):
        if for_update:
            return UserEditForm
        return UserCreationForm

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
