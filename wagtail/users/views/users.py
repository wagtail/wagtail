from django.conf import settings
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from wagtail.admin.views.generic import CreateView, DeleteView, EditView, IndexView
from wagtail.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME
from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.users.forms import UserCreationForm, UserEditForm
from wagtail.users.utils import user_can_delete_user
from wagtail.utils.loading import get_custom_form

User = get_user_model()

# Typically we would check the permission 'auth.change_user' (and 'auth.add_user' /
# 'auth.delete_user') for user management actions, but this may vary according to
# the AUTH_USER_MODEL setting
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
        return get_custom_form(form_setting)
    else:
        return UserCreationForm


def get_user_edit_form():
    form_setting = "WAGTAIL_USER_EDIT_FORM"
    if hasattr(settings, form_setting):
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


class Index(IndexView):
    """
    Lists the users for management within the admin.
    """

    template_name = "wagtailusers/users/index.html"
    results_template_name = "wagtailusers/users/results.html"
    any_permission_required = ["add", "change", "delete"]
    permission_policy = ModelPermissionPolicy(User)
    model = User
    header_icon = "user"
    add_item_label = _("Add a user")
    context_object_name = "users"
    index_url_name = "wagtailusers_users:index"
    add_url_name = "wagtailusers_users:add"
    edit_url_name = "wagtailusers_users:edit"
    default_ordering = "name"
    paginate_by = 20
    is_searchable = True
    page_title = gettext_lazy("Users")

    model_fields = [f.name for f in User._meta.get_fields()]

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.group = get_object_or_404(Group, id=args[0]) if args else None
        self.group_filter = Q(groups=self.group) if self.group else Q()

    def get_index_results_url(self):
        if self.group:
            return reverse("wagtailusers_groups:users_results", args=[self.group.pk])
        else:
            return reverse("wagtailusers_users:index_results")

    def get_valid_orderings(self):
        return ["name", "username"]

    def get_queryset(self):
        model_fields = set(self.model_fields)
        if self.is_searching:
            conditions = get_users_filter_query(self.search_query, model_fields)
            users = User.objects.filter(self.group_filter & conditions)
        else:
            users = User.objects.filter(self.group_filter)

        if self.locale:
            users = users.filter(locale=self.locale)

        if "wagtail_userprofile" in model_fields:
            users = users.select_related("wagtail_userprofile")

        if "last_name" in model_fields and "first_name" in model_fields:
            users = users.order_by("last_name", "first_name")

        if self.get_ordering() == "username":
            users = users.order_by(User.USERNAME_FIELD)

        return users

    def get_context_data(self, *args, object_list=None, **kwargs):
        context_data = super().get_context_data(
            *args, object_list=object_list, **kwargs
        )
        context_data["ordering"] = self.get_ordering()
        context_data["group"] = self.group

        context_data.update(
            {
                "app_label": User._meta.app_label,
                "model_name": User._meta.model_name,
            }
        )
        return context_data


class Create(CreateView):
    """
    Provide the ability to create a user within the admin.
    """

    permission_policy = ModelPermissionPolicy(User)
    permission_required = "add"
    model = User
    form_class = get_user_creation_form()
    template_name = "wagtailusers/users/create.html"
    header_icon = "user"
    add_url_name = "wagtailusers_users:add"
    index_url_name = "wagtailusers_users:index"
    edit_url_name = "wagtailusers_users:edit"
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

    def get_add_url(self):
        return None


class Edit(EditView):
    """
    Provide the ability to edit a user within the admin.
    """

    model = User
    permission_policy = ModelPermissionPolicy(User)
    form_class = get_user_edit_form()
    header_icon = "user"
    template_name = "wagtailusers/users/edit.html"
    index_url_name = "wagtailusers_users:index"
    edit_url_name = "wagtailusers_users:edit"
    delete_url_name = "wagtailusers_users:delete"
    success_message = gettext_lazy("User '%(object)s' updated.")
    context_object_name = "user"
    error_message = gettext_lazy("The user could not be saved due to errors.")

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

    def get_edit_url(self):
        return reverse(self.edit_url_name, args=(self.object.pk,))

    def get_delete_url(self):
        return reverse(self.delete_url_name, args=(self.object.pk,))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.pop("action_url")
        context["can_delete"] = self.can_delete
        return context


class Delete(DeleteView):
    """
    Provide the ability to delete a user within the admin.
    """

    permission_policy = ModelPermissionPolicy(User)
    permission_required = "delete"
    model = User
    template_name = "wagtailusers/users/confirm_delete.html"
    delete_url_name = "wagtailusers_users:delete"
    edit_url_name = "wagtailusers_users:edit"
    index_url_name = "wagtailusers_users:index"
    page_title = gettext_lazy("Delete user")
    context_object_name = "user"
    success_message = gettext_lazy("User '%(object)s' deleted.")

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
