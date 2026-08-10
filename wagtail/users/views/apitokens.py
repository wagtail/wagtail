from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.forms import CharField, Form, ModelChoiceField
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _

from wagtail.admin.ui.tables import Column
from wagtail.admin.views.generic.models import CreateView, DeleteView, IndexView
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.log_actions import log
from wagtail.models import APIToken
from wagtail.users.utils import get_manageable_token_owners, user_can_manage_token


class APITokenForm(Form):
    name = CharField(max_length=255, label=_("Name"))
    user = ModelChoiceField(queryset=None, label=_("User"))

    def __init__(self, *args, manageable_users, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = manageable_users


class Index(IndexView):
    columns = [
        Column("prefix", label=_("Token")),
        Column("name", label=_("Name")),
        Column("user", label=_("User")),
        Column("created", label=_("Created")),
        Column("last_used_at", label=_("Last used")),
        Column("revoked_at", label=_("Revoked")),
    ]

    def get_queryset(self):
        qs = super().get_queryset().select_related("user")
        return qs.filter(user__in=get_manageable_token_owners(self.request.user))


class Create(CreateView):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # APITokenForm is a plain Form, not a ModelForm.
        kwargs.pop("instance", None)
        kwargs["manageable_users"] = get_manageable_token_owners(self.request.user)
        return kwargs

    def form_valid(self, form):
        owner = form.cleaned_data["user"]
        if not user_can_manage_token(
            self.request.user, owner, "wagtailcore.add_apitoken"
        ):
            raise PermissionDenied
        self.object, plaintext = APIToken.create_token(
            user=owner, name=form.cleaned_data["name"]
        )
        log(self.object, "wagtail.apitoken.create", user=self.request.user)
        # Show the secret exactly once; it is never retrievable afterwards.
        return TemplateResponse(
            self.request,
            "wagtailusers/apitokens/created.html",
            {"object": self.object, "token": plaintext},
        )


class Revoke(DeleteView):
    """Soft-delete: revoking keeps the row for the audit trail."""

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not user_can_manage_token(
            request.user, self.object.user, "wagtailcore.delete_apitoken"
        ):
            raise PermissionDenied
        self.object.revoke()
        log(self.object, "wagtail.apitoken.revoke", user=request.user)
        messages.success(
            request, _("API token '%(name)s' revoked.") % {"name": self.object.name}
        )
        return redirect(self.get_success_url())


class APITokenViewSet(ModelViewSet):
    model = APIToken
    icon = "key"
    menu_label = _("API tokens")
    menu_name = "apitokens"
    menu_order = 602
    add_to_settings_menu = True
    add_to_reference_index = False
    copy_view_enabled = False
    inspect_view_enabled = False
    template_prefix = "wagtailusers/apitokens/"
    form_fields = ["name"]  # edit view: rename only
    index_view_class = Index
    add_view_class = Create
    delete_view_class = Revoke

    def get_form_class(self, for_update=False):
        if for_update:
            return super().get_form_class(for_update=True)
        return APITokenForm
