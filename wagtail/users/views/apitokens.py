from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.forms import CharField, Form, ModelChoiceField
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from django.views import View

from wagtail.admin.ui.tables import Column
from wagtail.admin.views.generic.base import WagtailAdminTemplateMixin
from wagtail.admin.views.generic.models import (
    CreateView,
    DeleteView,
    EditView,
    IndexView,
)
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.log_actions import log
from wagtail.models import APIToken
from wagtail.users.utils import get_manageable_token_owners, user_can_manage_token

CREATED_SESSION_KEY = "wagtail_apitoken_created"


class APITokenForm(Form):
    name = CharField(max_length=255, label=_("Name"))
    user = ModelChoiceField(queryset=None, label=_("User"))

    def __init__(self, *args, manageable_users, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = manageable_users


class TokenManagementQuerysetMixin:
    """Scope object lookups to tokens the current user may manage."""

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(user__in=get_manageable_token_owners(self.request.user))
        )


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
        # Stash the secret in the session for a single display on the
        # redirected-to page (POST/redirect/GET, so a refresh cannot
        # re-submit and mint a duplicate token).
        self.request.session[CREATED_SESSION_KEY] = {
            "pk": self.object.pk,
            "token": plaintext,
        }
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("wagtailusers_apitokens:created", args=[self.object.pk])


class Created(WagtailAdminTemplateMixin, View):
    """Displays a newly-created token's secret exactly once."""

    template_name = "wagtailusers/apitokens/created.html"

    def get(self, request, pk):
        stash = request.session.pop(CREATED_SESSION_KEY, None)
        if not stash or stash["pk"] != pk:
            messages.warning(
                request,
                _("Token secrets are only displayed once, immediately after creation."),
            )
            return redirect("wagtailusers_apitokens:index")
        self.object = get_object_or_404(APIToken, pk=pk)
        return self.render_to_response({"object": self.object, "token": stash["token"]})


class Edit(TokenManagementQuerysetMixin, EditView):
    pass


class Revoke(TokenManagementQuerysetMixin, DeleteView):
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
    edit_view_class = Edit
    delete_view_class = Revoke

    @property
    def created_view(self):
        return self.construct_view(Created)

    def get_urlpatterns(self):
        return super().get_urlpatterns() + [
            path("created/<int:pk>/", self.created_view, name="created"),
        ]

    def get_form_class(self, for_update=False):
        if for_update:
            return super().get_form_class(for_update=True)
        return APITokenForm
