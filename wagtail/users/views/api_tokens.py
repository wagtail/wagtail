import django_filters
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.utils import quote
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.forms import (
    CharField,
    CheckboxSelectMultiple,
    Form,
    ModelChoiceField,
    TextInput,
)
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.admin.filters import (
    DateRangePickerWidget,
    MultipleUserFilter,
    WagtailFilterSet,
)
from wagtail.admin.forms.choosers import BaseFilterForm
from wagtail.admin.templatetags.wagtailadmin_tags import timesince_simple
from wagtail.admin.ui.components import MediaContainer
from wagtail.admin.ui.side_panels import StatusSidePanel
from wagtail.admin.ui.tables import Column, TitleColumn
from wagtail.admin.utils import get_user_display_name
from wagtail.admin.views import generic
from wagtail.admin.views.generic import chooser as chooser_views
from wagtail.admin.viewsets.chooser import ChooserViewSet
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.admin.widgets.boolean_radio_select import BooleanRadioSelect
from wagtail.admin.widgets.chooser import BaseChooser
from wagtail.log_actions import log
from wagtail.models import APIToken
from wagtail.users.utils import get_manageable_token_owners, user_can_manage_token


class APITokenUserChooserWidget(BaseChooser):
    """
    Chooser for the token owner. Unlike a <select>, it does not render every
    manageable user up front, so the create form stays usable with a large
    user table.
    """

    choose_one_text = _("Choose a user")
    choose_another_text = _("Choose another user")
    icon = "user"
    show_edit_link = False
    show_clear_link = False
    model = settings.AUTH_USER_MODEL
    chooser_modal_url_name = "wagtailusers_api_token_user_chooser:choose"

    #: Limits which users can be rendered as the current value. Set by
    #: APITokenForm so that a submitted pk outside the user's scope is not
    #: echoed back (as a display name) when the form is redisplayed.
    queryset = None

    def get_instance(self, value):
        if value is None:
            return None
        if isinstance(value, self.model_class):
            return value
        queryset = self.model_class.objects if self.queryset is None else self.queryset
        try:
            return queryset.get(pk=value)
        except (self.model_class.DoesNotExist, ValueError, ValidationError):
            return None

    def get_display_title(self, instance):
        return get_user_display_name(instance)

    def get_value_data_from_instance(self, instance):
        return {
            "id": instance.pk,
            self.display_title_key: self.get_display_title(instance),
        }


class APITokenForm(Form):
    name = CharField(max_length=255, label=_("Name"))
    user = ModelChoiceField(
        queryset=None, label=_("User"), widget=APITokenUserChooserWidget
    )

    def __init__(self, *args, manageable_users, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = manageable_users
        self.fields["user"].widget.queryset = manageable_users


class UserSearchFilterForm(BaseFilterForm):
    q = CharField(
        label=_("Search term"),
        widget=TextInput(attrs={"placeholder": _("Search")}),
        required=False,
    )

    def filter(self, objects):
        search_query = self.cleaned_data.get("q")
        if not search_query:
            return objects

        model_fields = {f.name for f in objects.model._meta.get_fields()}
        search_fields = model_fields & {"username", "first_name", "last_name", "email"}
        # Every term has to match at least one of the fields
        for term in search_query.split():
            objects = objects.filter(
                Q(
                    *[Q(**{f"{field}__icontains": term}) for field in search_fields],
                    _connector=Q.OR,
                )
            )
        self.is_searching = True
        self.search_query = search_query
        return objects


class ManageableUsersChooserMixin:
    """
    Scope every chooser view to the users that the current user may create
    tokens for, so that the chooser cannot be used to enumerate other users.
    """

    filter_form_class = UserSearchFilterForm

    @cached_property
    def ordering(self):
        return get_user_model().USERNAME_FIELD

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm("wagtailcore.add_apitoken"):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def can_create(self):
        # Users are not created from within this chooser
        return False

    def get_manageable_users(self):
        return get_manageable_token_owners(self.request.user)

    def get_object_list(self):
        return self.get_manageable_users()

    def get_object(self, pk):
        users = self.get_manageable_users()
        try:
            return users.get(pk=pk)
        except (ValueError, ValidationError) as e:
            # a malformed pk is indistinguishable from a missing one
            raise users.model.DoesNotExist from e

    def get_objects(self, pks):
        users = self.get_manageable_users()
        try:
            return users.filter(pk__in=pks)
        except (ValueError, ValidationError):
            return users.none()

    def get_display_title(self, instance):
        return get_user_display_name(instance)

    def get_edit_item_url(self, instance):
        return None

    @property
    def title_column(self):
        if self.is_multiple_choice:
            return TitleColumn(
                "title",
                label=_("User"),
                accessor=get_user_display_name,
                label_prefix="chooser-modal-select",
            )
        return TitleColumn(
            "title",
            label=_("User"),
            accessor=get_user_display_name,
            get_url=lambda obj: self.append_preserved_url_parameters(
                reverse(self.chosen_url_name, args=(quote(obj.pk),))
            ),
            link_attrs={"data-chooser-modal-choice": True},
        )


class UserChooseView(ManageableUsersChooserMixin, chooser_views.ChooseView):
    pass


class UserChooseResultsView(
    ManageableUsersChooserMixin, chooser_views.ChooseResultsView
):
    pass


class UserChosenView(ManageableUsersChooserMixin, chooser_views.ChosenView):
    pass


class UserChosenMultipleView(
    ManageableUsersChooserMixin, chooser_views.ChosenMultipleView
):
    pass


class UserCreateView(ManageableUsersChooserMixin, chooser_views.CreateView):
    pass


class APITokenUserChooserViewSet(ChooserViewSet):
    """
    The chooser behind APITokenUserChooserWidget. It is deliberately not
    registered as the default widget for foreign keys to the user model.
    """

    model = settings.AUTH_USER_MODEL
    icon = "user"
    choose_one_text = _("Choose a user")
    choose_another_text = _("Choose another user")
    register_widget = False

    choose_view_class = UserChooseView
    choose_results_view_class = UserChooseResultsView
    chosen_view_class = UserChosenView
    chosen_multiple_view_class = UserChosenMultipleView
    create_view_class = UserCreateView


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
