from django.contrib.admin.utils import label_for_field, quote, unquote
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import (
    FieldDoesNotExist,
    ImproperlyConfigured,
    PermissionDenied,
)
from django.db import models, transaction
from django.db.models.constants import LOOKUP_SEP
from django.db.models.functions import Cast
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import (
    BaseCreateView,
    BaseDeleteView,
    BaseUpdateView,
)

from wagtail.actions.unpublish import UnpublishAction
from wagtail.admin import messages
from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.forms.models import WagtailAdminModelForm
from wagtail.admin.panels import get_edit_handler
from wagtail.admin.ui.components import Component, MediaContainer
from wagtail.admin.ui.fields import display_class_registry
from wagtail.admin.ui.menus import MenuItem
from wagtail.admin.ui.side_panels import StatusSidePanel
from wagtail.admin.ui.tables import (
    ButtonsColumnMixin,
    Column,
    LocaleColumn,
    TitleColumn,
    UpdatedAtColumn,
)
from wagtail.admin.utils import get_latest_str, get_valid_next_url_from_request
from wagtail.admin.views.mixins import SpreadsheetExportMixin
from wagtail.admin.widgets.button import (
    BaseButton,
    Button,
    ButtonWithDropdown,
    HeaderButton,
)
from wagtail.log_actions import log
from wagtail.log_actions import registry as log_registry
from wagtail.models import DraftStateMixin, Locale, ReferenceIndex
from wagtail.models.audit_log import ModelLogEntry
from wagtail.search.index import class_is_indexed

from .base import BaseListingView, WagtailAdminTemplateMixin
from .mixins import BeforeAfterHookMixin, HookResponseMixin, LocaleMixin, PanelMixin
from .permissions import PermissionCheckedMixin


class IndexView(
    SpreadsheetExportMixin,
    LocaleMixin,
    PermissionCheckedMixin,
    BaseListingView,
):
    model = None
    template_name = "wagtailadmin/generic/index.html"
    results_template_name = "wagtailadmin/generic/index_results.html"
    add_url_name = None
    edit_url_name = None
    copy_url_name = None
    inspect_url_name = None
    delete_url_name = None
    any_permission_required = ["add", "change", "delete", "view"]
    list_filter = None
    show_other_searches = False

    @cached_property
    def is_searchable(self):
        # Do not automatically enable search if the model is not indexed and
        # search_fields is not defined.
        if not (self.model and class_is_indexed(self.model)) and not self.search_fields:
            return False

        # Require the results-only view to be set up before enabling search
        return bool(self.index_results_url or self.search_url)

    @cached_property
    def filterset_class(self):
        # Allow filterset_class to be dynamically constructed from list_filter.

        # If the model is translatable, ensure a ``WagtailFilterSet`` subclass
        # is returned anyway (even if list_filter is undefined), so the locale
        # filter is always included.
        if not self.model or (not self.list_filter and not self.locale):
            return None

        class Meta:
            model = self.model
            fields = self.list_filter or []

        return type(
            f"{self.model.__name__}FilterSet",
            (WagtailFilterSet,),
            {"Meta": Meta},
        )

    def _annotate_queryset_updated_at(self, queryset):
        # Annotate the objects' updated_at, use _ prefix to avoid name collision
        # with an existing database field.
        # By default, use the latest log entry's timestamp, but subclasses may
        # override this to e.g. use the latest revision's timestamp instead.

        log_model = log_registry.get_log_model_for_model(queryset.model)

        # If the log model is not a subclass of ModelLogEntry, we don't know how
        # to query the logs for the object, so skip the annotation.
        if not log_model or not issubclass(log_model, ModelLogEntry):
            return queryset

        latest_log = (
            log_model.objects.filter(
                content_type=ContentType.objects.get_for_model(
                    queryset.model, for_concrete_model=False
                ),
                object_id=Cast(models.OuterRef("pk"), models.CharField()),
            )
            .order_by("-timestamp", "-pk")
            .values("timestamp")[:1]
        )
        return queryset.annotate(_updated_at=models.Subquery(latest_log))

    def order_queryset(self, queryset):
        has_updated_at_column = any(
            getattr(column, "accessor", None) == "_updated_at"
            for column in self.columns
        )
        if has_updated_at_column:
            queryset = self._annotate_queryset_updated_at(queryset)

        # Explicitly handle null values for the updated at column to ensure consistency
        # across database backends and match the behaviour in page explorer
        if self.ordering == "_updated_at":
            return queryset.order_by(models.F("_updated_at").asc(nulls_first=True))
        elif self.ordering == "-_updated_at":
            return queryset.order_by(models.F("_updated_at").desc(nulls_last=True))
        else:
            queryset = super().order_queryset(queryset)

            # Preserve the model-level ordering if specified, but fall back on
            # updated_at and PK if not (to ensure pagination is consistent)
            if not queryset.ordered:
                if has_updated_at_column:
                    queryset = queryset.order_by(
                        models.F("_updated_at").desc(nulls_last=True), "-pk"
                    )
                else:
                    queryset = queryset.order_by("-pk")

            return queryset

    def _get_title_column_class(self, column_class):
        if not issubclass(column_class, ButtonsColumnMixin):

            def get_buttons(column, instance, *args, **kwargs):
                return self.get_list_buttons(instance)

            column_class = type(
                column_class.__name__,
                (ButtonsColumnMixin, column_class),
                {"get_buttons": get_buttons},
            )
        return column_class

    def _get_title_column(self, field_name, column_class=TitleColumn, **kwargs):
        column_class = self._get_title_column_class(column_class)

        def get_url(instance):
            if edit_url := self.get_edit_url(instance):
                return edit_url
            return self.get_inspect_url(instance)

        if not self.model:
            return column_class(
                "name",
                label=gettext_lazy("Name"),
                accessor=str,
                get_url=get_url,
            )
        return self._get_custom_column(
            field_name, column_class, get_url=get_url, **kwargs
        )

    def _get_custom_column(self, field_name, column_class=Column, **kwargs):
        lookups = (
            [field_name]
            if hasattr(self.model, field_name)
            else field_name.split(LOOKUP_SEP)
        )
        *relations, field = lookups
        model_class = self.model

        # Iterate over the relation list to try to get the last model
        # where the field exists
        foreign_field_name = ""
        for model in relations:
            foreign_field = model_class._meta.get_field(model)
            foreign_field_name = foreign_field.verbose_name
            model_class = foreign_field.related_model

        label, attr = label_for_field(field, model_class, return_attr=True)

        # For some languages, it may be more appropriate to put the field label
        # before the related model name
        if foreign_field_name:
            label = _("%(related_model_name)s %(field_label)s") % {
                "related_model_name": foreign_field_name,
                "field_label": label,
            }

        sort_key = getattr(attr, "admin_order_field", None)

        # attr is None if the field is an actual database field,
        # so it's possible to sort by it
        if attr is None:
            sort_key = field_name

        accessor = field_name
        # Build the dotted relation if needed, for use in multigetattr
        if relations:
            accessor = ".".join(lookups)
        return column_class(
            accessor,
            label=capfirst(label),
            sort_key=sort_key,
            **kwargs,
        )

    @cached_property
    def list_display(self):
        list_display = ["__str__", UpdatedAtColumn()]
        if self.i18n_enabled:
            list_display.insert(1, LocaleColumn())
        return list_display

    @cached_property
    def columns(self):
        # If not explicitly overridden, derive from list_display
        columns = []
        for i, field in enumerate(self.list_display):
            if isinstance(field, Column):
                column = field
            elif i == 0:
                column = self._get_title_column(field)
            else:
                column = self._get_custom_column(field)
            columns.append(column)

        return columns

    def get_edit_url(self, instance):
        if self.edit_url_name and self.user_has_permission("change"):
            return reverse(self.edit_url_name, args=(quote(instance.pk),))

    def get_copy_url(self, instance):
        if self.copy_url_name and self.user_has_permission("add"):
            return reverse(self.copy_url_name, args=(quote(instance.pk),))

    def get_inspect_url(self, instance):
        if self.inspect_url_name and self.user_has_any_permission(
            {"add", "change", "delete", "view"}
        ):
            return reverse(self.inspect_url_name, args=(quote(instance.pk),))

    def get_delete_url(self, instance):
        if self.delete_url_name and self.user_has_permission("delete"):
            return reverse(self.delete_url_name, args=(quote(instance.pk),))

    def get_add_url(self):
        if self.add_url_name and self.user_has_permission("add"):
            return self._set_locale_query_param(reverse(self.add_url_name))

    @cached_property
    def add_url(self):
        return self.get_add_url()

    def get_page_title(self):
        if not self.page_title and self.model:
            return capfirst(self.model._meta.verbose_name_plural)
        return self.page_title

    @cached_property
    def header_buttons(self):
        buttons = []
        if self.add_url:
            buttons.append(
                HeaderButton(
                    self.add_item_label,
                    url=self.add_url,
                    icon_name="plus",
                )
            )
        return buttons

    def get_list_more_buttons(self, instance):
        buttons = []
        if edit_url := self.get_edit_url(instance):
            buttons.append(
                MenuItem(
                    _("Edit"),
                    url=edit_url,
                    icon_name="edit",
                    priority=10,
                )
            )
        if copy_url := self.get_copy_url(instance):
            buttons.append(
                MenuItem(
                    _("Copy"),
                    url=copy_url,
                    icon_name="copy",
                    priority=20,
                )
            )
        if inspect_url := self.get_inspect_url(instance):
            buttons.append(
                MenuItem(
                    _("Inspect"),
                    url=inspect_url,
                    icon_name="info-circle",
                    priority=20,
                )
            )
        if delete_url := self.get_delete_url(instance):
            buttons.append(
                MenuItem(
                    _("Delete"),
                    url=delete_url,
                    icon_name="bin",
                    priority=30,
                )
            )
        return buttons

    def get_list_buttons(self, instance):
        buttons = []
        more_buttons = []

        for button in self.get_list_more_buttons(instance):
            if isinstance(button, BaseButton) and not button.allow_in_dropdown:
                buttons.append(button)
            elif isinstance(button, MenuItem):
                if button.is_shown(self.request.user):
                    more_buttons.append(Button.from_menu_item(button))
            elif button.show:
                more_buttons.append(button)

        if more_buttons:
            buttons.append(
                ButtonWithDropdown(
                    buttons=more_buttons,
                    icon_name="dots-horizontal",
                    attrs={
                        "aria-label": _("More options for '%(title)s'")
                        % {"title": str(instance)},
                    },
                )
            )
        return buttons

    @cached_property
    def add_item_label(self):
        if self.model:
            return capfirst(
                _("Add %(model_name)s") % {"model_name": self.model._meta.verbose_name}
            )
        return _("Add")

    @cached_property
    def verbose_name_plural(self):
        if self.model:
            return self.model._meta.verbose_name_plural
        return None

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        context["can_add"] = self.user_has_permission("add")
        if context["can_add"]:
            context["add_url"] = context["header_action_url"] = self.add_url
            context["header_action_label"] = self.add_item_label

        context["model_opts"] = self.model and self.model._meta
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.is_export:
            return self.as_spreadsheet(
                context["object_list"], self.request.GET.get("export")
            )
        return super().render_to_response(context, **response_kwargs)


class CreateView(
    LocaleMixin,
    PanelMixin,
    PermissionCheckedMixin,
    BeforeAfterHookMixin,
    WagtailAdminTemplateMixin,
    BaseCreateView,
):
    model = None
    form_class = None
    index_url_name = None
    add_url_name = None
    edit_url_name = None
    template_name = "wagtailadmin/generic/create.html"
    page_title = gettext_lazy("New")
    permission_required = "add"
    success_message = gettext_lazy("%(model_name)s '%(object)s' created.")
    error_message = gettext_lazy(
        "The %(model_name)s could not be created due to errors."
    )
    submit_button_label = gettext_lazy("Create")
    submit_button_active_label = gettext_lazy("Creating…")
    actions = ["create"]

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.action = self.get_action(request)

    def get_action(self, request):
        for action in self.get_available_actions():
            if request.POST.get(f"action-{action}"):
                return action
        return "create"

    def get_available_actions(self):
        return self.actions

    def get_page_subtitle(self):
        if not self.page_subtitle and self.model:
            return capfirst(self.model._meta.verbose_name)
        return self.page_subtitle

    def get_breadcrumbs_items(self):
        if not self.model:
            return self.breadcrumbs_items
        items = []
        if self.index_url_name:
            items.append(
                {
                    "url": reverse(self.index_url_name),
                    "label": capfirst(self.model._meta.verbose_name_plural),
                }
            )
        items.append(
            {
                "url": "",
                "label": _("New: %(model_name)s")
                % {"model_name": self.get_page_subtitle()},
            }
        )
        return self.breadcrumbs_items + items

    def get_add_url(self):
        if not self.add_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.CreateView must provide an "
                "add_url_name attribute or a get_add_url method"
            )
        return self._set_locale_query_param(reverse(self.add_url_name))

    @cached_property
    def add_url(self):
        return self.get_add_url()

    def get_edit_url(self):
        if not self.edit_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.CreateView must provide an "
                "edit_url_name attribute or a get_edit_url method"
            )
        return reverse(self.edit_url_name, args=(quote(self.object.pk),))

    def get_success_url(self):
        if not self.index_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.CreateView must provide an "
                "index_url_name attribute or a get_success_url method"
            )
        return self._set_locale_query_param(reverse(self.index_url_name))

    def get_success_message(self, instance):
        if self.success_message is None:
            return None
        return capfirst(
            self.success_message
            % {
                "object": instance,
                "model_name": self.model and self.model._meta.verbose_name,
            }
        )

    def get_success_buttons(self):
        return [messages.button(self.get_edit_url(), _("Edit"))]

    def get_error_message(self):
        if self.error_message is None:
            return None
        return capfirst(
            self.error_message
            % {"model_name": self.model and self.model._meta.verbose_name}
        )

    @cached_property
    def has_unsaved_changes(self):
        return self.form.is_bound

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.form = context.get("form")
        side_panels = self.get_side_panels()
        context["action_url"] = self.add_url
        context["submit_button_label"] = self.submit_button_label
        context["submit_button_active_label"] = self.submit_button_active_label
        context["side_panels"] = side_panels
        context["media"] += side_panels.media
        context["has_unsaved_changes"] = self.has_unsaved_changes
        return context

    def get_side_panels(self):
        side_panels = []
        if self.locale:
            side_panels.append(
                StatusSidePanel(
                    self.form.instance,
                    self.request,
                    locale=self.locale,
                    translations=self.translations,
                )
            )
        return MediaContainer(side_panels)

    def get_translations(self):
        return [
            {
                "locale": locale,
                "url": self._set_locale_query_param(self.add_url, locale),
            }
            for locale in Locale.objects.all().exclude(id=self.locale.id)
        ]

    def get_initial_form_instance(self):
        if self.locale:
            instance = self.model()
            instance.locale = self.locale
            return instance

    def get_form_kwargs(self):
        if instance := self.get_initial_form_instance():
            # super().get_form_kwargs() will use self.object as the instance kwarg
            self.object = instance
        kwargs = super().get_form_kwargs()

        form_class = self.get_form_class()
        # Add for_user support for PermissionedForm
        if issubclass(form_class, WagtailAdminModelForm):
            kwargs["for_user"] = self.request.user
        return kwargs

    def save_instance(self):
        """
        Called after the form is successfully validated - saves the object to the db
        and returns the new object. Override this to implement custom save logic.
        """
        instance = self.form.save()
        log(instance=instance, action="wagtail.create", content_changed=True)
        return instance

    def save_action(self):
        success_message = self.get_success_message(self.object)
        success_buttons = self.get_success_buttons()
        if success_message is not None:
            messages.success(
                self.request,
                success_message,
                buttons=success_buttons,
            )
        return redirect(self.get_success_url())

    def form_valid(self, form):
        self.form = form
        with transaction.atomic():
            self.object = self.save_instance()

        response = self.save_action()

        hook_response = self.run_after_hook()
        if hook_response is not None:
            return hook_response

        return response

    def form_invalid(self, form):
        self.form = form
        error_message = self.get_error_message()
        if error_message is not None:
            messages.validation_error(self.request, error_message, form)
        return super().form_invalid(form)


class CopyViewMixin:
    def get_object(self, queryset=None):
        return get_object_or_404(
            self.model, pk=unquote(str(self.kwargs[self.pk_url_kwarg]))
        )

    def get_initial_form_instance(self):
        return self.get_object()


class CopyView(CopyViewMixin, CreateView):
    pass


class EditView(
    LocaleMixin,
    PanelMixin,
    PermissionCheckedMixin,
    BeforeAfterHookMixin,
    WagtailAdminTemplateMixin,
    BaseUpdateView,
):
    model = None
    form_class = None
    index_url_name = None
    edit_url_name = None
    copy_url_name = None
    delete_url_name = None
    history_url_name = None
    inspect_url_name = None
    usage_url_name = None
    page_title = gettext_lazy("Editing")
    context_object_name = None
    template_name = "wagtailadmin/generic/edit.html"
    permission_required = "change"
    delete_item_label = gettext_lazy("Delete")
    success_message = gettext_lazy("%(model_name)s '%(object)s' updated.")
    error_message = gettext_lazy("The %(model_name)s could not be saved due to errors.")
    submit_button_label = gettext_lazy("Save")
    submit_button_active_label = gettext_lazy("Saving…")
    actions = ["edit"]

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.action = self.get_action(request)

    @cached_property
    def object_pk(self):
        # Must be a cached_property to prevent this from being re-run on the unquoted
        # pk written back by get_object, which would result in it being unquoted again.
        try:
            quoted_pk = self.kwargs[self.pk_url_kwarg]
        except KeyError:
            quoted_pk = self.args[0]
        return unquote(str(quoted_pk))

    def get_action(self, request):
        for action in self.get_available_actions():
            if request.POST.get(f"action-{action}"):
                return action
        return "edit"

    def get_available_actions(self):
        return self.actions

    def get_object(self, queryset=None):
        # SingleObjectMixin.get_object looks for the unquoted pk in self.kwargs,
        # so we need to write it back there.
        self.kwargs[self.pk_url_kwarg] = self.object_pk
        return super().get_object(queryset)

    def get_page_subtitle(self):
        return get_latest_str(self.object)

    def get_breadcrumbs_items(self):
        if not self.model:
            return self.breadcrumbs_items
        items = []
        if self.index_url_name:
            items.append(
                {
                    "url": reverse(self.index_url_name),
                    "label": capfirst(self.model._meta.verbose_name_plural),
                }
            )
        items.append({"url": "", "label": self.get_page_subtitle()})
        return self.breadcrumbs_items + items

    def get_side_panels(self):
        side_panels = []
        usage_url = self.get_usage_url()
        history_url = self.get_history_url()
        if usage_url or history_url:
            side_panels.append(
                StatusSidePanel(
                    self.object,
                    self.request,
                    locale=self.locale,
                    translations=self.translations,
                    usage_url=usage_url,
                    history_url=history_url,
                    last_updated_info=self.get_last_updated_info(),
                )
            )
        return MediaContainer(side_panels)

    def get_last_updated_info(self):
        return (
            log_registry.get_logs_for_instance(self.object)
            .select_related("user")
            .first()
        )

    @cached_property
    def can_delete(self):
        return self.user_has_permission_for_instance("delete", self.object)

    @cached_property
    def header_more_buttons(self):
        buttons = []
        if copy_url := self.get_copy_url():
            buttons.append(
                Button(
                    _("Copy"),
                    url=copy_url,
                    icon_name="copy",
                    priority=10,
                )
            )
        if self.can_delete and (delete_url := self.get_delete_url()):
            buttons.append(
                Button(
                    self.delete_item_label,
                    url=delete_url,
                    icon_name="bin",
                    priority=20,
                )
            )
        if inspect_url := self.get_inspect_url():
            buttons.append(
                Button(
                    _("Inspect"),
                    url=inspect_url,
                    icon_name="info-circle",
                    priority=30,
                )
            )
        return buttons

    def get_edit_url(self):
        if not self.edit_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.EditView must provide an "
                "edit_url_name attribute or a get_edit_url method"
            )
        return reverse(self.edit_url_name, args=(quote(self.object.pk),))

    def get_copy_url(self):
        if self.copy_url_name and self.user_has_permission("add"):
            return reverse(self.copy_url_name, args=(quote(self.object.pk),))

    def get_delete_url(self):
        if self.delete_url_name:
            return reverse(self.delete_url_name, args=(quote(self.object.pk),))

    def get_history_url(self):
        if self.history_url_name:
            return reverse(self.history_url_name, args=(quote(self.object.pk),))

    def get_inspect_url(self):
        if self.inspect_url_name:
            return reverse(self.inspect_url_name, args=(quote(self.object.pk),))

    def get_usage_url(self):
        if self.usage_url_name:
            return reverse(self.usage_url_name, args=[quote(self.object.pk)])

    def get_success_url(self):
        if not self.index_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.EditView must provide an "
                "index_url_name attribute or a get_success_url method"
            )
        return reverse(self.index_url_name)

    def get_translations(self):
        if not self.edit_url_name:
            return []
        return [
            {
                "locale": translation.locale,
                "url": reverse(self.edit_url_name, args=[quote(translation.pk)]),
            }
            for translation in self.object.get_translations().select_related("locale")
        ]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        form_class = self.get_form_class()
        if issubclass(form_class, WagtailAdminModelForm):
            kwargs["for_user"] = self.request.user
        return kwargs

    def save_instance(self):
        """
        Called after the form is successfully validated - saves the object to the db.
        Override this to implement custom save logic.
        """
        instance = self.form.save()

        self.has_content_changes = self.form.has_changed()

        log(
            instance=instance,
            action="wagtail.edit",
            content_changed=self.has_content_changes,
        )

        return instance

    def save_action(self):
        success_message = self.get_success_message()
        success_buttons = self.get_success_buttons()
        if success_message is not None:
            messages.success(
                self.request,
                success_message,
                buttons=success_buttons,
            )
        return redirect(self.get_success_url())

    def get_success_message(self):
        if self.success_message is None:
            return None
        return capfirst(
            self.success_message
            % {
                "object": self.object,
                "model_name": self.model and self.model._meta.verbose_name,
            }
        )

    def get_success_buttons(self):
        return [messages.button(self.get_edit_url(), _("Edit"))]

    def get_error_message(self):
        if self.error_message is None:
            return None
        return capfirst(
            self.error_message
            % {"model_name": self.model and self.model._meta.verbose_name}
        )

    def form_valid(self, form):
        self.form = form
        with transaction.atomic():
            self.object = self.save_instance()

        response = self.save_action()

        hook_response = self.run_after_hook()
        if hook_response is not None:
            return hook_response

        return response

    def form_invalid(self, form):
        self.form = form
        error_message = self.get_error_message()
        if error_message is not None:
            messages.validation_error(self.request, error_message, form)
        return super().form_invalid(form)

    @cached_property
    def has_unsaved_changes(self):
        return self.form.is_bound

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.form = context.get("form")
        side_panels = self.get_side_panels()
        context["action_url"] = self.get_edit_url()
        context["history_url"] = self.get_history_url()
        context["side_panels"] = side_panels
        context["media"] += side_panels.media
        context["submit_button_label"] = self.submit_button_label
        context["submit_button_active_label"] = self.submit_button_active_label
        context["has_unsaved_changes"] = self.has_unsaved_changes
        context["can_delete"] = self.can_delete
        if context["can_delete"]:
            context["delete_url"] = self.get_delete_url()
            context["delete_item_label"] = self.delete_item_label
        return context


class DeleteView(
    LocaleMixin,
    PanelMixin,
    PermissionCheckedMixin,
    BeforeAfterHookMixin,
    WagtailAdminTemplateMixin,
    BaseDeleteView,
):
    model = None
    index_url_name = None
    edit_url_name = None
    delete_url_name = None
    usage_url_name = None
    template_name = "wagtailadmin/generic/confirm_delete.html"
    context_object_name = None
    permission_required = "delete"
    page_title = gettext_lazy("Delete")
    success_message = gettext_lazy("%(model_name)s '%(object)s' deleted.")

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.object = self.get_object()
        # Get this here instead of the template so that we do not iterate through
        # the usage and potentially trigger a database query for each item
        self.usage_url = self.get_usage_url()
        self.usage = self.get_usage()

    def get_object(self, queryset=None):
        # If the object has already been loaded, return it to avoid another query
        if getattr(self, "object", None):
            return self.object

        # SingleObjectMixin.get_object looks for the unquoted pk in self.kwargs,
        # so we need to write it back there.
        try:
            quoted_pk = self.kwargs[self.pk_url_kwarg]
        except KeyError:
            quoted_pk = self.args[0]
        self.kwargs[self.pk_url_kwarg] = unquote(str(quoted_pk))

        return super().get_object(queryset)

    def get_usage(self):
        if not self.usage_url:
            return None
        return ReferenceIndex.get_grouped_references_to(self.object)

    def get_success_url(self):
        next_url = get_valid_next_url_from_request(self.request)
        if next_url:
            return next_url
        if not self.index_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.DeleteView must provide an "
                "index_url_name attribute or a get_success_url method"
            )
        return reverse(self.index_url_name)

    def get_page_subtitle(self):
        return str(self.object)

    def get_breadcrumbs_items(self):
        return []

    def get_delete_url(self):
        if not self.delete_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.DeleteView must provide a "
                "delete_url_name attribute or a get_delete_url method"
            )
        return reverse(self.delete_url_name, args=(quote(self.object.pk),))

    def get_usage_url(self):
        # Usage URL is optional, allow it to be unset
        if self.usage_url_name:
            return (
                reverse(self.usage_url_name, args=(quote(self.object.pk),))
                + "?describe_on_delete=1"
            )

    @property
    def confirmation_message(self):
        return _("Are you sure you want to delete this %(model_name)s?") % {
            "model_name": self.object._meta.verbose_name
        }

    def get_success_message(self):
        if self.success_message is None:
            return None
        return capfirst(
            self.success_message
            % {
                "model_name": capfirst(self.object._meta.verbose_name),
                "object": self.object,
            }
        )

    def delete_action(self):
        with transaction.atomic():
            log(instance=self.object, action="wagtail.delete")
            self.object.delete()

    def form_valid(self, form):
        if self.usage and self.usage.is_protected:
            raise PermissionDenied
        success_url = self.get_success_url()
        self.delete_action()
        messages.success(self.request, self.get_success_message())
        hook_response = self.run_after_hook()
        if hook_response is not None:
            return hook_response
        return HttpResponseRedirect(success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_opts"] = self.object._meta
        context["next"] = self.get_success_url()
        if self.usage_url:
            context["usage_url"] = self.usage_url
            context["usage_count"] = self.usage.count()
            context["is_protected"] = self.usage.is_protected
        return context


class InspectView(PermissionCheckedMixin, WagtailAdminTemplateMixin, TemplateView):
    any_permission_required = ["add", "change", "delete", "view"]
    template_name = "wagtailadmin/generic/inspect.html"
    page_title = gettext_lazy("Inspect")
    model = None
    index_url_name = None
    edit_url_name = None
    delete_url_name = None
    fields = []
    fields_exclude = []
    pk_url_kwarg = "pk"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.pk = self.kwargs[self.pk_url_kwarg]
        self.fields = self.get_fields()
        self.object = self.get_object()

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, pk=unquote(str(self.pk)))

    def get_page_subtitle(self):
        return get_latest_str(self.object)

    def get_breadcrumbs_items(self):
        items = []
        if self.index_url_name:
            items.append(
                {
                    "url": reverse(self.index_url_name),
                    "label": capfirst(self.model._meta.verbose_name_plural),
                }
            )
        edit_url = self.get_edit_url()
        object_str = self.get_page_subtitle()
        if edit_url:
            items.append({"url": edit_url, "label": object_str})
        items.append(
            {
                "url": "",
                "label": self.get_page_title(),
                "sublabel": object_str,
            }
        )
        return self.breadcrumbs_items + items

    @cached_property
    def header_more_buttons(self):
        buttons = []
        if edit_url := self.get_edit_url():
            buttons.append(
                Button(_("Edit"), url=edit_url, icon_name="edit", priority=10)
            )
        if delete_url := self.get_delete_url():
            buttons.append(
                Button(_("Delete"), url=delete_url, icon_name="bin", priority=20)
            )
        return buttons

    def get_fields(self):
        fields = self.fields or [
            f.name
            for f in self.model._meta.get_fields()
            if f.concrete
            and (not f.is_relation or (not f.auto_created and f.related_model))
        ]

        fields = [f for f in fields if f not in self.fields_exclude]
        return fields

    def get_field_label(self, field_name, field):
        return capfirst(label_for_field(field_name, model=self.model))

    def get_field_display_value(self, field_name, field):
        # First we check for a `get_fieldname_display_value` method on the InspectView
        # then for a 'get_fieldname_display' property/method on
        # the model, and return the value of that, if present.
        value_func = getattr(self, f"get_{field_name}_display_value", None)
        if value_func is not None and callable(value_func):
            return value_func()

        value_func = getattr(self.object, "get_%s_display" % field_name, None)
        if value_func is not None:
            if callable(value_func):
                return value_func()
            return value_func

        # Now let's get the attribute value from the instance itself and see if
        # we can render something useful. Raises AttributeError appropriately.
        value = getattr(self.object, field_name)

        if isinstance(value, models.Manager):
            value = value.all()

        if isinstance(value, models.QuerySet):
            return ", ".join(str(obj) for obj in value) or "-"

        display_class = display_class_registry.get(field)

        if display_class:
            return display_class(value)

        return value

    def get_context_for_field(self, field_name):
        try:
            field = self.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            field = None
        context = {
            "label": self.get_field_label(field_name, field),
            "value": self.get_field_display_value(field_name, field),
            "component": None,
        }
        if isinstance(context["value"], Component):
            context["component"] = context["value"]
        return context

    def get_fields_context(self):
        return [self.get_context_for_field(field_name) for field_name in self.fields]

    def get_edit_url(self):
        if self.edit_url_name and self.user_has_permission("change"):
            return reverse(self.edit_url_name, args=(quote(self.object.pk),))

    def get_delete_url(self):
        if self.delete_url_name and self.user_has_permission("delete"):
            return reverse(self.delete_url_name, args=(quote(self.object.pk),))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.object
        context["fields"] = self.get_fields_context()
        return context


class RevisionsCompareView(WagtailAdminTemplateMixin, TemplateView):
    edit_handler = None
    index_url_name = None
    edit_url_name = None
    history_url_name = None
    edit_label = gettext_lazy("Edit")
    history_label = gettext_lazy("History")
    page_title = gettext_lazy("Compare")
    template_name = "wagtailadmin/generic/revisions/compare.html"
    model = None

    def get_breadcrumbs_items(self):
        items = []
        if (index_url := self.get_index_url()) and self.model:
            items.append(
                {
                    "url": index_url,
                    "label": capfirst(self.model._meta.verbose_name_plural),
                }
            )
        if edit_url := self.get_edit_url():
            items.append({"url": edit_url, "label": self.get_page_subtitle()})
        if history_url := self.get_history_url():
            items.append({"url": history_url, "label": self.history_label})
        items.append(
            {
                "url": "",
                "label": self.get_page_title(),
                "sublabel": self.get_page_subtitle(),
            }
        )
        return self.breadcrumbs_items + items

    @cached_property
    def header_buttons(self):
        buttons = []
        if edit_url := self.get_edit_url():
            buttons.append(
                HeaderButton(self.edit_label, url=edit_url, icon_name="edit")
            )
        return buttons

    def setup(self, request, pk, revision_id_a, revision_id_b, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.pk = pk
        self.revision_id_a = revision_id_a
        self.revision_id_b = revision_id_b
        self.object = self.get_object()

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, pk=unquote(str(self.pk)))

    def get_edit_handler(self):
        if self.edit_handler:
            return self.edit_handler
        return get_edit_handler(self.model)

    def get_page_subtitle(self):
        return str(self.object)

    def get_index_url(self):
        if self.index_url_name:
            return reverse(self.index_url_name)

    def get_history_url(self):
        if self.history_url_name:
            return reverse(self.history_url_name, args=(quote(self.object.pk),))

    def get_edit_url(self):
        if self.edit_url_name:
            return reverse(self.edit_url_name, args=(quote(self.object.pk),))

    def _get_revision_and_heading(self, revision_id):
        if revision_id == "live":
            revision = self.object
            revision_heading = _("Live")
            return revision, revision_heading

        if revision_id == "earliest":
            revision = self.object.revisions.order_by("created_at", "id").first()
            revision_heading = _("Earliest")
        elif revision_id == "latest":
            revision = self.object.revisions.order_by("created_at", "id").last()
            revision_heading = _("Latest")
        else:
            revision = get_object_or_404(self.object.revisions, id=revision_id)
            if revision:
                revision_heading = str(revision.created_at)

        if not revision:
            raise Http404

        revision = revision.as_object()

        return revision, revision_heading

    def _get_comparison(self, revision_a, revision_b):
        comparison = (
            self.get_edit_handler()
            .get_bound_panel(instance=self.object, request=self.request, form=None)
            .get_comparison()
        )

        result = []
        for comp in comparison:
            diff = comp(revision_a, revision_b)
            if diff.has_changed():
                result += [diff]

        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        revision_a, revision_a_heading = self._get_revision_and_heading(
            self.revision_id_a
        )
        revision_b, revision_b_heading = self._get_revision_and_heading(
            self.revision_id_b
        )
        comparison = self._get_comparison(revision_a, revision_b)

        context.update(
            {
                "object": self.object,
                "revision_a": revision_a,
                "revision_a_heading": revision_a_heading,
                "revision_b": revision_b,
                "revision_b_heading": revision_b_heading,
                "comparison": comparison,
            }
        )

        return context


class UnpublishView(HookResponseMixin, WagtailAdminTemplateMixin, TemplateView):
    model = None
    index_url_name = None
    edit_url_name = None
    unpublish_url_name = None
    usage_url_name = None
    page_title = gettext_lazy("Unpublish")
    success_message = gettext_lazy("'%(object)s' unpublished.")
    template_name = "wagtailadmin/generic/confirm_unpublish.html"

    def setup(self, request, pk, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.pk = pk
        self.object = self.get_object()

    def dispatch(self, request, *args, **kwargs):
        self.objects_to_unpublish = self.get_objects_to_unpublish()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not self.model or not issubclass(self.model, DraftStateMixin):
            raise Http404
        return get_object_or_404(self.model, pk=unquote(str(self.pk)))

    def get_usage(self):
        return ReferenceIndex.get_grouped_references_to(self.object)

    def get_breadcrumbs_items(self):
        return []

    def get_objects_to_unpublish(self):
        # Hook to allow child classes to have more objects to unpublish (e.g. page descendants)
        return [self.object]

    def get_page_subtitle(self):
        return get_latest_str(self.object)

    def get_success_message(self):
        if self.success_message is None:
            return None
        return self.success_message % {"object": str(self.object)}

    def get_success_buttons(self):
        if self.edit_url_name:
            return [
                messages.button(
                    reverse(self.edit_url_name, args=(quote(self.object.pk),)),
                    _("Edit"),
                )
            ]

    def get_next_url(self):
        if not self.index_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.UnpublishView "
                "must provide an index_url_name attribute or a get_next_url method"
            )
        return reverse(self.index_url_name)

    def get_unpublish_url(self):
        if not self.unpublish_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.UnpublishView "
                "must provide an unpublish_url_name attribute or a get_unpublish_url method"
            )
        return reverse(self.unpublish_url_name, args=(quote(self.object.pk),))

    def get_usage_url(self):
        # Usage URL is optional, allow it to be unset
        if self.usage_url_name:
            return reverse(self.usage_url_name, args=(quote(self.object.pk),))

    def unpublish(self):
        hook_response = self.run_hook("before_unpublish", self.request, self.object)
        if hook_response is not None:
            return hook_response

        for object in self.objects_to_unpublish:
            action = UnpublishAction(object, user=self.request.user)
            action.execute(skip_permission_checks=True)

        hook_response = self.run_hook("after_unpublish", self.request, self.object)
        if hook_response is not None:
            return hook_response

    def post(self, request, *args, **kwargs):
        hook_response = self.unpublish()
        if hook_response:
            return hook_response

        success_message = self.get_success_message()
        success_buttons = self.get_success_buttons()
        if success_message is not None:
            messages.success(request, success_message, buttons=success_buttons)

        return redirect(self.get_next_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_opts"] = self.object._meta
        context["object"] = self.object
        context["unpublish_url"] = self.get_unpublish_url()
        context["next_url"] = self.get_next_url()
        context["usage_url"] = self.get_usage_url()
        if context["usage_url"]:
            usage = self.get_usage()
            context["usage_count"] = usage.count()
        return context


class RevisionsUnscheduleView(WagtailAdminTemplateMixin, TemplateView):
    model = None
    edit_url_name = None
    history_url_name = None
    revisions_unschedule_url_name = None
    success_message = gettext_lazy(
        'Version %(revision_id)s of "%(object)s" unscheduled.'
    )
    template_name = "wagtailadmin/shared/revisions/confirm_unschedule.html"
    page_title = gettext_lazy("Unschedule")

    def setup(self, request, pk, revision_id, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.pk = pk
        self.revision_id = revision_id
        self.object = self.get_object()
        self.revision = self.get_revision()

    def get_object(self, queryset=None):
        if not self.model or not issubclass(self.model, DraftStateMixin):
            raise Http404
        return get_object_or_404(self.model, pk=unquote(str(self.pk)))

    def get_breadcrumbs_items(self):
        return []

    def get_revision(self):
        return get_object_or_404(self.object.revisions, id=self.revision_id)

    def get_revisions_unschedule_url(self):
        return reverse(
            self.revisions_unschedule_url_name,
            args=(quote(self.object.pk), self.revision.id),
        )

    def get_object_display_title(self):
        return get_latest_str(self.object)

    def get_success_message(self):
        if self.success_message is None:
            return None
        return self.success_message % {
            "revision_id": self.revision.id,
            "object": self.get_object_display_title(),
        }

    def get_success_buttons(self):
        return [
            messages.button(
                reverse(self.edit_url_name, args=(quote(self.object.pk),)), _("Edit")
            )
        ]

    def get_next_url(self):
        next_url = get_valid_next_url_from_request(self.request)
        if next_url:
            return next_url

        if not self.history_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.RevisionsUnscheduleView "
                " must provide a history_url_name attribute or a get_next_url method"
            )
        return reverse(self.history_url_name, args=(quote(self.object.pk),))

    def get_page_subtitle(self):
        return capfirst(
            _('revision %(revision_id)s of "%(object)s"')
            % {
                "revision_id": self.revision.id,
                "object": self.get_object_display_title(),
            }
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "object": self.object,
                "revision": self.revision,
                "revisions_unschedule_url": self.get_revisions_unschedule_url(),
                "next_url": self.get_next_url(),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        self.revision.approved_go_live_at = None
        self.revision.save(user=request.user, update_fields=["approved_go_live_at"])

        success_message = self.get_success_message()
        success_buttons = self.get_success_buttons()
        if success_message:
            messages.success(
                request,
                success_message,
                buttons=success_buttons,
            )

        return redirect(self.get_next_url())
