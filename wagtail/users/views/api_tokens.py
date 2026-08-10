import django_filters
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.forms import CharField, Form, ModelChoiceField
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, reverse
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from django.views import View

from wagtail.admin.filters import DateRangePickerWidget, WagtailFilterSet
from wagtail.admin.ui.components import MediaContainer
from wagtail.admin.ui.side_panels import StatusSidePanel
from wagtail.admin.ui.tables import Column, TitleColumn
from wagtail.admin.utils import get_user_display_name
from wagtail.admin.views.generic.base import WagtailAdminTemplateMixin
from wagtail.admin.views.generic.models import (
    CreateView,
    DeleteView,
    EditView,
    IndexView,
)
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.admin.widgets.boolean_radio_select import BooleanRadioSelect
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


class UserModelChoiceField(django_filters.fields.ModelChoiceField):
    def label_from_instance(self, obj):
        return get_user_display_name(obj)


class UserModelChoiceFilter(django_filters.ModelChoiceFilter):
    field_class = UserModelChoiceField


class APITokenFilterSet(WagtailFilterSet):
    user = UserModelChoiceFilter(
        label=_("User"),
        empty_label=_("All"),
        field_name="user",
        queryset=get_user_model().objects.none(),
    )
    created = django_filters.DateFromToRangeFilter(
        label=_("Created"),
        widget=DateRangePickerWidget,
    )
    last_used_at = django_filters.DateFromToRangeFilter(
        label=_("Last used"),
        widget=DateRangePickerWidget,
    )
    revoked = django_filters.BooleanFilter(
        label=_("Revoked"),
        method="filter_revoked",
        widget=BooleanRadioSelect,
    )

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(data, queryset, request=request, prefix=prefix)
        if request is not None:
            self.filters["user"].field.queryset = get_manageable_token_owners(
                request.user
            )

    def filter_revoked(self, queryset, name, value):
        if value is True:
            return queryset.filter(revoked_at__isnull=False)
        if value is False:
            return queryset.filter(revoked_at__isnull=True)
        return queryset

    class Meta:
        model = APIToken
        fields = []


class TokenManagementQuerysetMixin:
    """Scope object lookups to tokens the current user may manage."""

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(user__in=get_manageable_token_owners(self.request.user))
        )


class Index(TokenManagementQuerysetMixin, IndexView):
    filterset_class = APITokenFilterSet

    @cached_property
    def columns(self):
        # TitleColumn (+ ButtonsColumnMixin) links each row to edit and
        # exposes the actions menu (including revoke/delete). Plain Column
        # instances render text only, with no way into those views.
        return [
            self._get_title_column_class(TitleColumn)(
                "prefix",
                label=_("Token"),
                get_url=self.get_edit_url,
            ),
            Column("name", label=_("Name")),
            Column("user", label=_("User")),
            Column("created", label=_("Created")),
            Column("last_used_at", label=_("Last used")),
            Column("revoked_at", label=_("Revoked")),
        ]

    def get_queryset(self):
        return super().get_queryset().select_related("user")


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
        # re-submit and mint a duplicate token). Keyed by pk so multiple
        # pending secrets can coexist.
        stash = self.request.session.get(CREATED_SESSION_KEY, {})
        stash[str(self.object.pk)] = plaintext
        self.request.session[CREATED_SESSION_KEY] = stash
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("wagtailusers_api_tokens:created", args=[self.object.pk])


class Created(WagtailAdminTemplateMixin, View):
    """Displays a newly-created token's secret exactly once."""

    template_name = "wagtailusers/api_tokens/created.html"
    page_title = _("API token created")
    model = None
    index_url_name = None
    header_icon = ""

    def get_breadcrumbs_items(self):
        items = []
        if self.index_url_name and self.model:
            items.append(
                {
                    "url": reverse(self.index_url_name),
                    "label": capfirst(self.model._meta.verbose_name_plural),
                }
            )
        items.append({"url": "", "label": self.get_page_title()})
        return self.breadcrumbs_items + items

    def get(self, request, pk):
        # Peek before consuming: a stale link or prefetch must not wipe the
        # one-time secret.
        stash = request.session.get(CREATED_SESSION_KEY, {})
        plaintext = stash.get(str(pk))
        if plaintext is None:
            messages.warning(
                request,
                _("Token secrets are only displayed once, immediately after creation."),
            )
            return redirect("wagtailusers_api_tokens:index")
        self.object = get_object_or_404(APIToken, pk=pk)
        del stash[str(pk)]
        if stash:
            request.session[CREATED_SESSION_KEY] = stash
        else:
            del request.session[CREATED_SESSION_KEY]
        return self.render_to_response(
            self.get_context_data(object=self.object, token=plaintext)
        )


class APITokenStatusSidePanel(StatusSidePanel):
    """Replace the default Live/Draft workflow status with Active/Revoked."""

    def get_status_templates(self, context):
        templates = ["wagtailusers/api_tokens/status.html"]
        if self.usage_url is not None:
            templates.append(
                "wagtailadmin/shared/side_panels/includes/status/usage.html"
            )
        return templates


class Edit(TokenManagementQuerysetMixin, EditView):
    def get_side_panels(self):
        side_panels = []
        usage_url = self.get_usage_url()
        history_url = self.get_history_url()
        if usage_url or history_url:
            side_panels.append(
                APITokenStatusSidePanel(
                    self.object,
                    self.request,
                    usage_url=usage_url,
                    history_url=history_url,
                    last_updated_info=self.get_last_updated_info(),
                )
            )
        return MediaContainer(side_panels)


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
    menu_name = "api_tokens"
    menu_order = 602
    add_to_settings_menu = True
    add_to_reference_index = False
    copy_view_enabled = False
    inspect_view_enabled = False
    template_prefix = "wagtailusers/api_tokens/"
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
