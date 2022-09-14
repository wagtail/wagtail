from django.conf import settings
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from wagtail import hooks
from wagtail.admin import messages
from wagtail.admin.auth import permission_required
from wagtail.admin.views.generic import CreateView, DeleteView, IndexView
from wagtail.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME
from wagtail.log_actions import log
from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.users.forms import UserCreationForm, UserEditForm
from wagtail.users.utils import user_can_delete_user
from wagtail.utils.loading import get_custom_form

User = get_user_model()

# Typically we would check the permission 'auth.change_user' (and 'auth.add_user' /
# 'auth.delete_user') for user management actions, but this may vary according to
# the AUTH_USER_MODEL setting
add_user_perm = "{0}.add_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower())
change_user_perm = "{0}.change_{1}".format(
    AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower()
)
delete_user_perm = "{0}.delete_{1}".format(
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

    any_permission_required = ["add", "change", "delete"]
    permission_policy = ModelPermissionPolicy(User)
    model = User
    context_object_name = "users"
    index_url_name = "wagtailusers_users:index"
    add_url_name = "wagtailusers_users:add"
    edit_url_name = "wagtailusers_users:edit"
    default_ordering = "name"
    paginate_by = 20
    template_name = None
    is_searchable = True
    page_title = gettext_lazy("Users")

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        setattr(self, "template_name", self.get_template())
        self.group = get_object_or_404(Group, id=args[0]) if args else None
        self.group_filter = Q(groups=self.group) if self.group else Q()
        self.model_fields = [f.name for f in User._meta.get_fields()]

    def get_valid_orderings(self):
        return ["name", "username"]

    def get_queryset(self):
        if self.is_searching:
            conditions = get_users_filter_query(self.search_query, self.model_fields)
            users = User.objects.filter(self.group_filter & conditions)
        else:
            users = User.objects.filter(self.group_filter)

        if self.locale:
            users = users.filter(locale=self.locale)

        if "last_name" in self.model_fields and "first_name" in self.model_fields:
            users = users.order_by("last_name", "first_name")

        if self.get_ordering() == "username":
            users = users.order_by(User.USERNAME_FIELD)

        return users

    def get_template(self):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return "wagtailusers/users/results.html"
        else:
            return "wagtailusers/users/index.html"

    def get_context_data(self, *args, object_list=None, **kwargs):
        context_data = super().get_context_data(
            *args, object_list=object_list, **kwargs
        )
        context_data["ordering"] = self.get_ordering()
        context_data["group"] = self.group
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return context_data

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
    form_class = get_user_creation_form()
    template_name = "wagtailusers/users/create.html"
    add_url_name = "wagtailusers_users:add"
    index_url_name = "wagtailusers_users:index"
    edit_url_name = "wagtailusers_users:edit"
    success_message = "User '{0}' created."
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

    def get_success_buttons(self):
        return [
            messages.button(
                reverse(self.edit_url_name, args=(self.object.pk,)), _("Edit")
            )
        ]


@permission_required(change_user_perm)
def edit(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    can_delete = user_can_delete_user(request.user, user)
    editing_self = request.user == user

    for fn in hooks.get_hooks("before_edit_user"):
        result = fn(request, user)
        if hasattr(result, "status_code"):
            return result
    if request.method == "POST":
        form = get_user_edit_form()(
            request.POST, request.FILES, instance=user, editing_self=editing_self
        )
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                log(user, "wagtail.edit")

            if user == request.user and "password1" in form.changed_data:
                # User is changing their own password; need to update their session hash
                update_session_auth_hash(request, user)

            messages.success(
                request,
                _("User '{0}' updated.").format(user),
                buttons=[
                    messages.button(
                        reverse("wagtailusers_users:edit", args=(user.pk,)), _("Edit")
                    )
                ],
            )
            for fn in hooks.get_hooks("after_edit_user"):
                result = fn(request, user)
                if hasattr(result, "status_code"):
                    return result
            return redirect("wagtailusers_users:index")
        else:
            messages.error(request, _("The user could not be saved due to errors."))
    else:
        form = get_user_edit_form()(instance=user, editing_self=editing_self)

    return TemplateResponse(
        request,
        "wagtailusers/users/edit.html",
        {
            "user": user,
            "form": form,
            "can_delete": can_delete,
        },
    )


class Delete(DeleteView):
    """
    Provide the ability to delete a user within the admin.
    """

    permission_policy = ModelPermissionPolicy(User)
    permission_required = "delete"
    model = User
    template_name = "wagtailusers/users/confirm_delete.html"
    delete_url_name = "wagtailusers_users:delete"
    index_url_name = "wagtailusers_users:index"
    page_title = gettext_lazy("Delete user")
    context_object_name = "user"
    success_message = _("User '{0}' deleted.")

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
