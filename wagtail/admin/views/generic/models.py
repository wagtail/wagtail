from django import VERSION as DJANGO_VERSION
from django.contrib.admin.utils import quote, unquote
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.forms import Form
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.generic import TemplateView
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import BaseCreateView
from django.views.generic.edit import BaseDeleteView as DjangoBaseDeleteView
from django.views.generic.edit import BaseUpdateView, DeletionMixin, FormMixin
from django.views.generic.list import BaseListView

from wagtail.admin import messages
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.panels import get_edit_handler
from wagtail.admin.templatetags.wagtailadmin_tags import user_display_name
from wagtail.admin.ui.tables import Table, TitleColumn
from wagtail.log_actions import log
from wagtail.log_actions import registry as log_registry
from wagtail.models import DraftStateMixin, RevisionMixin
from wagtail.search.index import class_is_indexed

from .base import WagtailAdminTemplateMixin
from .mixins import BeforeAfterHookMixin, LocaleMixin, PanelMixin
from .permissions import PermissionCheckedMixin

if DJANGO_VERSION >= (4, 0):
    BaseDeleteView = DjangoBaseDeleteView
else:
    # As of Django 4.0 BaseDeleteView has switched to a new implementation based on FormMixin
    # where custom deletion logic now lives in form_valid:
    # https://docs.djangoproject.com/en/4.0/releases/4.0/#deleteview-changes
    # Here we define BaseDeleteView to match the Django 4.0 implementation to keep it consistent
    # across all versions.
    class BaseDeleteView(DeletionMixin, FormMixin, BaseDetailView):
        """
        Base view for deleting an object.
        Using this base class requires subclassing to provide a response mixin.
        """

        form_class = Form

        def post(self, request, *args, **kwargs):
            # Set self.object before the usual form processing flow.
            # Inlined because having DeletionMixin as the first base, for
            # get_success_url(), makes leveraging super() with ProcessFormView
            # overly complex.
            self.object = self.get_object()
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)

        def form_valid(self, form):
            success_url = self.get_success_url()
            self.object.delete()
            return HttpResponseRedirect(success_url)


class IndexView(
    LocaleMixin, PermissionCheckedMixin, WagtailAdminTemplateMixin, BaseListView
):
    model = None
    index_url_name = None
    add_url_name = None
    add_item_label = _("Add")
    edit_url_name = None
    template_name = "wagtailadmin/generic/index.html"
    context_object_name = None
    any_permission_required = ["add", "change", "delete"]
    page_kwarg = "p"
    default_ordering = None
    is_searchable = None
    search_kwarg = "q"
    table_class = Table

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if not hasattr(self, "columns"):
            self.columns = self.get_columns()
        self.setup_search()

    def setup_search(self):
        self.is_searchable = self.get_is_searchable()
        self.search_url = self.get_search_url()
        self.search_form = self.get_search_form()
        self.is_searching = False
        self.search_query = None

        if self.search_form and self.search_form.is_valid():
            self.search_query = self.search_form.cleaned_data[self.search_kwarg]
            self.is_searching = True

    def get_is_searchable(self):
        if self.model is None:
            return False
        if self.is_searchable is None:
            return class_is_indexed(self.model)
        return self.is_searchable

    def get_search_url(self):
        if not self.is_searchable:
            return None
        return self.index_url_name

    def get_search_form(self):
        if self.model is None:
            return None

        if self.is_searchable and self.search_kwarg in self.request.GET:
            return SearchForm(
                self.request.GET,
                placeholder=_("Search %(model_name)s")
                % {"model_name": self.model._meta.verbose_name_plural},
            )

        return SearchForm(
            placeholder=_("Search %(model_name)s")
            % {"model_name": self.model._meta.verbose_name_plural}
        )

    def get_columns(self):
        try:
            return self.columns
        except AttributeError:
            return [
                TitleColumn(
                    "name",
                    label=gettext_lazy("Name"),
                    accessor=str,
                    get_url=lambda obj: self.get_edit_url(obj),
                ),
            ]

    def get_index_url(self):
        if self.index_url_name:
            return reverse(self.index_url_name)

    def get_edit_url(self, instance):
        if self.edit_url_name:
            return reverse(self.edit_url_name, args=(instance.pk,))

    def get_add_url(self):
        if self.add_url_name:
            return reverse(self.add_url_name)

    def get_valid_orderings(self):
        orderings = []
        for col in self.columns:
            if col.sort_key:
                orderings.append(col.sort_key)
                orderings.append("-%s" % col.sort_key)
        return orderings

    def get_ordering(self):
        ordering = self.request.GET.get("ordering", self.default_ordering)
        if ordering not in self.get_valid_orderings():
            ordering = self.default_ordering
        return ordering

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        index_url = self.get_index_url()
        table = self.table_class(
            self.columns,
            context["object_list"],
            base_url=index_url,
            ordering=self.get_ordering(),
        )

        context["can_add"] = (
            self.permission_policy is None
            or self.permission_policy.user_has_permission(self.request.user, "add")
        )
        if context["can_add"]:
            context["add_url"] = self.get_add_url()
            context["add_item_label"] = self.add_item_label

        context["table"] = table
        context["media"] = table.media
        context["index_url"] = index_url
        context["is_paginated"] = bool(self.paginate_by)
        context["is_searchable"] = self.is_searchable
        context["search_url"] = self.get_search_url()
        context["search_form"] = self.search_form
        context["is_searching"] = self.is_searching
        context["query_string"] = self.search_query
        return context


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
    permission_required = "add"
    success_message = None
    error_message = None
    submit_button_label = gettext_lazy("Create")
    actions = ["create", "publish"]

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.action = self.get_action(request)

    def get_action(self, request):
        for action in self.actions:
            if request.POST.get(f"action-{action}"):
                return action
        return "create"

    def get_add_url(self):
        if not self.add_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.CreateView must provide an "
                "add_url_name attribute or a get_add_url method"
            )
        return reverse(self.add_url_name)

    def get_success_url(self):
        if not self.index_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.CreateView must provide an "
                "index_url_name attribute or a get_success_url method"
            )
        return reverse(self.index_url_name)

    def get_success_message(self, instance):
        if self.action == "publish":
            return _("'{0}' has been created and published.").format(str(instance))
        if self.success_message is None:
            return None
        return self.success_message.format(instance)

    def get_success_buttons(self):
        return [
            messages.button(
                reverse(self.edit_url_name, args=(self.object.id,)), _("Edit")
            )
        ]

    def get_error_message(self):
        if self.error_message is None:
            return None
        return self.error_message

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action_url"] = self.get_add_url()
        context["submit_button_label"] = self.submit_button_label
        return context

    def save_instance(self):
        """
        Called after the form is successfully validated - saves the object to the db
        and returns the new object. Override this to implement custom save logic.
        """
        if self.model and issubclass(self.model, DraftStateMixin):
            instance = self.form.save(commit=False)
            instance.live = False
            instance.save()
            self.form.save_m2m()
        else:
            instance = self.form.save()

        self.new_revision = None

        # Save revision if the model inherits from RevisionMixin
        if isinstance(instance, RevisionMixin):
            self.new_revision = instance.save_revision(user=self.request.user)

        log(
            instance=instance,
            action="wagtail.create",
            revision=self.new_revision,
            content_changed=True,
        )

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

    def publish_action(self):
        hook_response = self.run_hook("before_publish", self.request, self.object)
        if hook_response is not None:
            return hook_response

        self.new_revision.publish(user=self.request.user)

        hook_response = self.run_hook("after_publish", self.request, self.object)
        if hook_response is not None:
            return hook_response

        return None

    def form_valid(self, form):
        self.form = form
        with transaction.atomic():
            self.object = self.save_instance()

        if self.action == "publish" and isinstance(self.object, DraftStateMixin):
            response = self.publish_action()
            if response is not None:
                return response

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
    delete_url_name = None
    page_title = gettext_lazy("Editing")
    context_object_name = None
    template_name = "wagtailadmin/generic/edit.html"
    permission_required = "change"
    delete_item_label = gettext_lazy("Delete")
    success_message = None
    error_message = None
    submit_button_label = gettext_lazy("Save")
    actions = ["edit", "publish"]

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.action = self.get_action(request)
        self.revision_enabled = self.model and issubclass(self.model, RevisionMixin)
        self.draftstate_enabled = self.model and issubclass(self.model, DraftStateMixin)

    def get_action(self, request):
        for action in self.actions:
            if request.POST.get(f"action-{action}"):
                return action
        return "edit"

    def get_object(self, queryset=None):
        if "pk" not in self.kwargs:
            self.kwargs["pk"] = self.args[0]
        object = super().get_object(queryset)

        # Cannot use self.draftstate_enabled here as there are subclasses
        # that rely on get_object to determine the model
        if isinstance(object, DraftStateMixin):
            return object.get_latest_revision_as_object()
        return object

    def get_page_subtitle(self):
        return str(self.object)

    def get_edit_url(self):
        if not self.edit_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.EditView must provide an "
                "edit_url_name attribute or a get_edit_url method"
            )
        return reverse(self.edit_url_name, args=(self.object.id,))

    def get_delete_url(self):
        if self.delete_url_name:
            return reverse(self.delete_url_name, args=(self.object.id,))

    def get_success_url(self):
        if not self.index_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.EditView must provide an "
                "index_url_name attribute or a get_success_url method"
            )
        return reverse(self.index_url_name)

    def save_instance(self):
        """
        Called after the form is successfully validated - saves the object to the db.
        Override this to implement custom save logic.
        """
        commit = not self.draftstate_enabled
        instance = self.form.save(commit=commit)
        self.new_revision = None

        self.has_content_changes = self.form.has_changed()

        # Save revision if the model inherits from RevisionMixin
        if self.revision_enabled:
            self.new_revision = instance.save_revision(
                user=self.request.user,
                changed=self.has_content_changes,
            )

        log(
            instance=instance,
            action="wagtail.edit",
            revision=self.new_revision,
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

    def publish_action(self):
        hook_response = self.run_hook("before_publish", self.request, self.object)
        if hook_response is not None:
            return hook_response

        self.new_revision.publish(user=self.request.user)

        hook_response = self.run_hook("after_publish", self.request, self.object)
        if hook_response is not None:
            return hook_response

        return None

    def get_success_message(self):
        if self.action == "publish":
            return _("'{0}' has been published.").format(str(self.object))
        if self.success_message is None:
            return None
        return self.success_message.format(self.object)

    def get_success_buttons(self):
        return [
            messages.button(
                reverse(self.edit_url_name, args=(self.object.id,)), _("Edit")
            )
        ]

    def get_error_message(self):
        if self.error_message is None:
            return None
        return self.error_message

    def get_live_last_updated_info(self):
        # DraftStateMixin is applied but object is not live
        if self.draftstate_enabled and not self.object.live:
            return None

        revision = None
        # DraftStateMixin is applied and object is live
        if self.draftstate_enabled and self.object.live_revision:
            revision = self.object.live_revision
        # RevisionMixin is applied, so object is assumed to be live
        elif self.revision_enabled and self.object.latest_revision:
            revision = self.object.latest_revision

        # No mixin is applied or no revision exists, fall back to latest log entry
        if not revision:
            return log_registry.get_logs_for_instance(self.object).first()

        return {
            "timestamp": revision.created_at,
            "user_display_name": user_display_name(revision.user),
        }

    def get_draft_last_updated_info(self):
        if not (self.draftstate_enabled and self.object.has_unpublished_changes):
            return None

        revision = self.object.latest_revision
        return {
            "timestamp": revision.created_at,
            "user_display_name": user_display_name(revision.user),
        }

    def form_valid(self, form):
        self.form = form
        with transaction.atomic():
            self.object = self.save_instance()

        if self.action == "publish" and self.draftstate_enabled:
            response = self.publish_action()
            if response is not None:
                return response

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action_url"] = self.get_edit_url()
        context["submit_button_label"] = self.submit_button_label
        context["can_delete"] = (
            self.permission_policy is None
            or self.permission_policy.user_has_permission(self.request.user, "delete")
        )
        if context["can_delete"]:
            context["delete_url"] = self.get_delete_url()
            context["delete_item_label"] = self.delete_item_label

        context["revision_enabled"] = self.revision_enabled
        context["draftstate_enabled"] = self.draftstate_enabled

        context["live_last_updated_info"] = self.get_live_last_updated_info()
        context["draft_last_updated_info"] = self.get_draft_last_updated_info()
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
    delete_url_name = None
    template_name = "wagtailadmin/generic/confirm_delete.html"
    context_object_name = None
    permission_required = "delete"
    success_message = None

    def get_object(self, queryset=None):
        if "pk" not in self.kwargs:
            self.kwargs["pk"] = self.args[0]
        return super().get_object(queryset)

    def get_success_url(self):
        if not self.index_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.DeleteView must provide an "
                "index_url_name attribute or a get_success_url method"
            )
        return reverse(self.index_url_name)

    def get_page_subtitle(self):
        return str(self.object)

    def get_delete_url(self):
        if not self.index_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.DeleteView must provide a "
                "delete_url_name attribute or a get_delete_url method"
            )
        return reverse(self.delete_url_name, args=(self.object.id,))

    def get_success_message(self):
        if self.success_message is None:
            return None
        return self.success_message.format(self.object)

    def delete_action(self):
        with transaction.atomic():
            log(instance=self.object, action="wagtail.delete")
            self.object.delete()

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.delete_action()
        messages.success(self.request, self.get_success_message())
        hook_response = self.run_after_hook()
        if hook_response is not None:
            return hook_response
        return HttpResponseRedirect(success_url)


class RevisionsCompareView(WagtailAdminTemplateMixin, TemplateView):
    edit_url_name = None
    history_url_name = None
    edit_label = gettext_lazy("Edit")
    history_label = gettext_lazy("History")
    template_name = "wagtailadmin/generic/revisions/compare.html"
    model = None

    def setup(self, request, pk, revision_id_a, revision_id_b, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.pk = pk
        self.revision_id_a = revision_id_a
        self.revision_id_b = revision_id_b
        self.object = self.get_object()

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, pk=unquote(self.pk))

    def get_edit_handler(self):
        return get_edit_handler(self.model)

    def get_page_subtitle(self):
        return str(self.object)

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
                "history_label": self.history_label,
                "edit_label": self.edit_label,
                "history_url": self.get_history_url(),
                "edit_url": self.get_edit_url(),
                "revision_a": revision_a,
                "revision_a_heading": revision_a_heading,
                "revision_b": revision_b,
                "revision_b_heading": revision_b_heading,
                "comparison": comparison,
            }
        )

        return context
