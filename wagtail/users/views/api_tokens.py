import django_filters
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.forms import CharField, CheckboxSelectMultiple, Form, ModelChoiceField
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.admin.filters import (
    DateRangePickerWidget,
    MultipleUserFilter,
    WagtailFilterSet,
)
from wagtail.admin.templatetags.wagtailadmin_tags import timesince_simple
from wagtail.admin.ui.components import MediaContainer
from wagtail.admin.ui.side_panels import StatusSidePanel
from wagtail.admin.ui.tables import Column, TitleColumn
from wagtail.admin.views import generic
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.admin.widgets.boolean_radio_select import BooleanRadioSelect
from wagtail.log_actions import log
from wagtail.models import APIToken
from wagtail.users.utils import get_manageable_token_owners, user_can_manage_token


class APITokenForm(Form):
    name = CharField(max_length=255, label=_("Name"))
    user = ModelChoiceField(queryset=None, label=_("User"))

    def __init__(self, *args, manageable_users, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = manageable_users


class APITokenFilterSet(WagtailFilterSet):
    user = MultipleUserFilter(
        label=_("User"),
        field_name="user",
        queryset=lambda request: get_manageable_token_owners(request.user),
        widget=CheckboxSelectMultiple,
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


class IndexView(TokenManagementQuerysetMixin, generic.IndexView):
    filterset_class = APITokenFilterSet

    @cached_property
    def columns(self):
        # TitleColumn (+ ButtonsColumnMixin) links each row to edit and
        # exposes the actions menu (including revoke). Plain Column
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

    def get_list_more_buttons(self, instance):
        buttons = super().get_list_more_buttons(instance)
        delete_url = self.get_delete_url(instance)
        for button in buttons:
            if delete_url and button.url == delete_url:
                button.label = _("Revoke")
                break
        return buttons


class CreateView(generic.CreateView):
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
        return TemplateResponse(
            self.request,
            "wagtailusers/api_tokens/created.html",
            self.get_created_context(plaintext),
        )

    def get_created_context(self, plaintext):
        context = super().get_context_data(token=plaintext)
        context["page_title"] = _("API token created")
        context["header_title"] = _("API token created")
        return context


class APITokenStatusSidePanel(StatusSidePanel):
    """Replace the default Live/Draft workflow status with Active/Revoked."""

    def get_status_templates(self, context):
        templates = [
            "wagtailusers/api_tokens/status.html",
            "wagtailadmin/shared/side_panels/includes/status/usage.html",
        ]
        return templates

    def get_usage_context(self):
        # Reference-index "Used N times" is meaningless for tokens; show
        # last_used_at instead. Empty usage_url renders plain text, not a link.
        if self.object.last_used_at:
            usage_url_text = timesince_simple(self.object.last_used_at)
        else:
            usage_url_text = _("Never")
        return {
            "usage_url": "",
            "usage_url_text": usage_url_text,
        }


class EditView(TokenManagementQuerysetMixin, generic.EditView):
    delete_item_label = _("Revoke")

    def get_side_panels(self):
        side_panels = []
        usage_url = self.get_usage_url()
        history_url = self.get_history_url()
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


class RevokeView(TokenManagementQuerysetMixin, generic.DeleteView):
    """Soft-delete: revoking keeps the row for the audit trail."""

    page_title = _("Revoke")
    template_name = "wagtailusers/api_tokens/confirm_revoke.html"

    @property
    def confirmation_message(self):
        return _("Are you sure you want to revoke this API token?")

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
    index_view_class = IndexView
    add_view_class = CreateView
    edit_view_class = EditView
    delete_view_class = RevokeView

    def get_form_class(self, for_update=False):
        if for_update:
            return super().get_form_class(for_update=True)
        return APITokenForm
