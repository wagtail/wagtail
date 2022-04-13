from urllib.parse import urlencode

from django.apps import apps
from django.conf import settings
from django.contrib.admin.utils import quote, unquote
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy, ngettext
from django.views.generic import TemplateView

from wagtail import hooks
from wagtail.admin import messages
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.panels import ObjectList, extract_panel_definitions_from_model_class
from wagtail.admin.ui.tables import Column, DateColumn, UserColumn
from wagtail.admin.views.generic import CreateView, IndexView
from wagtail.log_actions import log
from wagtail.log_actions import registry as log_registry
from wagtail.models import Locale, TranslatableMixin
from wagtail.search.backends import get_search_backend
from wagtail.search.index import class_is_indexed
from wagtail.snippets.action_menu import SnippetActionMenu
from wagtail.snippets.models import get_snippet_models
from wagtail.snippets.permissions import get_permission_name, user_can_edit_snippet_type


# == Helper functions ==
def get_snippet_model_from_url_params(app_name, model_name):
    """
    Retrieve a model from an app_label / model_name combo.
    Raise Http404 if the model is not a valid snippet type.
    """
    try:
        model = apps.get_model(app_name, model_name)
    except LookupError:
        raise Http404
    if model not in get_snippet_models():
        # don't allow people to hack the URL to edit content types that aren't registered as snippets
        raise Http404

    return model


SNIPPET_EDIT_HANDLERS = {}


def get_snippet_edit_handler(model):
    if model not in SNIPPET_EDIT_HANDLERS:
        if hasattr(model, "edit_handler"):
            # use the edit handler specified on the page class
            edit_handler = model.edit_handler
        else:
            panels = extract_panel_definitions_from_model_class(model)
            edit_handler = ObjectList(panels)

        SNIPPET_EDIT_HANDLERS[model] = edit_handler.bind_to_model(model)

    return SNIPPET_EDIT_HANDLERS[model]


# == Views ==


def index(request):
    snippet_model_opts = [
        model._meta
        for model in get_snippet_models()
        if user_can_edit_snippet_type(request.user, model)
    ]
    if snippet_model_opts:
        return TemplateResponse(
            request,
            "wagtailsnippets/snippets/index.html",
            {
                "snippet_model_opts": sorted(
                    snippet_model_opts, key=lambda x: x.verbose_name.lower()
                )
            },
        )
    else:
        raise PermissionDenied


class ListView(TemplateView):

    # If true, returns just the 'results' include, for use in AJAX responses from search
    results_only = False

    def get(self, request, app_label, model_name):
        self.app_label = app_label
        self.model_name = model_name
        self.model = get_snippet_model_from_url_params(app_label, model_name)

        permissions = [
            get_permission_name(action, self.model)
            for action in ["add", "change", "delete"]
        ]
        if not any([request.user.has_perm(perm) for perm in permissions]):
            raise PermissionDenied

        return super().get(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        items = self.model.objects.all()
        enable_locale_filter = getattr(
            settings, "WAGTAIL_I18N_ENABLED", False
        ) and issubclass(self.model, TranslatableMixin)

        if enable_locale_filter:
            if "locale" in self.request.GET:
                try:
                    locale = Locale.objects.get(
                        language_code=self.request.GET["locale"]
                    )
                except Locale.DoesNotExist:
                    # Redirect to snippet without locale
                    return redirect(
                        "wagtailsnippets:list", self.app_label, self.model_name
                    )
            else:
                # Default to active locale (this will take into account the user's chosen admin language)
                locale = Locale.get_active()

            items = items.filter(locale=locale)

        else:
            locale = None

        # Preserve the snippet's model-level ordering if specified, but fall back on PK if not
        # (to ensure pagination is consistent)
        if not items.ordered:
            items = items.order_by("pk")

        # Search
        is_searchable = class_is_indexed(self.model)
        is_searching = False
        search_query = None
        if is_searchable and "q" in self.request.GET:
            search_form = SearchForm(
                self.request.GET,
                placeholder=_("Search %(snippet_type_name)s")
                % {"snippet_type_name": self.model._meta.verbose_name_plural},
            )

            if search_form.is_valid():
                search_query = search_form.cleaned_data["q"]

                search_backend = get_search_backend()
                items = search_backend.search(search_query, items)
                is_searching = True

        else:
            search_form = SearchForm(
                placeholder=_("Search %(snippet_type_name)s")
                % {"snippet_type_name": self.model._meta.verbose_name_plural}
            )

        paginator = Paginator(items, per_page=20)
        paginated_items = paginator.get_page(self.request.GET.get("p"))

        context.update(
            {
                "model_opts": self.model._meta,
                "items": paginated_items,
                "can_add_snippet": self.request.user.has_perm(
                    get_permission_name("add", self.model)
                ),
                "can_delete_snippets": self.request.user.has_perm(
                    get_permission_name("delete", self.model)
                ),
                "is_searchable": is_searchable,
                "search_form": search_form,
                "is_searching": is_searching,
                "query_string": search_query,
                "locale": None,
                "translations": [],
            }
        )

        if enable_locale_filter:
            context.update(
                {
                    "locale": locale,
                    "translations": [
                        {
                            "locale": locale,
                            "url": reverse(
                                "wagtailsnippets:list",
                                args=[self.app_label, self.model_name],
                            )
                            + "?locale="
                            + locale.language_code,
                        }
                        for locale in Locale.objects.all().exclude(id=locale.id)
                    ],
                }
            )

        return context

    def get_template_names(self):
        if self.results_only:
            return ["wagtailsnippets/snippets/results.html"]
        else:
            return ["wagtailsnippets/snippets/type_index.html"]


class Create(CreateView):
    template_name = "wagtailsnippets/snippets/create.html"
    error_message = _("The snippet could not be created due to errors.")

    def _run_before_hooks(self):
        for fn in hooks.get_hooks("before_create_snippet"):
            result = fn(self.request, self.model)
            if hasattr(result, "status_code"):
                return result
        return None

    def _run_after_hooks(self):
        for fn in hooks.get_hooks("after_create_snippet"):
            result = fn(self.request, self.object)
            if hasattr(result, "status_code"):
                return result
        return None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.app_label = kwargs.get("app_label")
        self.model_name = kwargs.get("model_name")
        self.model = self._get_model()
        self.locale = self._get_locale()
        self.edit_handler = self._get_edit_handler()

    def _get_model(self):
        return get_snippet_model_from_url_params(self.app_label, self.model_name)

    def _get_locale(self):
        if getattr(settings, "WAGTAIL_I18N_ENABLED", False) and issubclass(
            self.model, TranslatableMixin
        ):
            selected_locale = self.request.GET.get("locale")
            if selected_locale:
                return get_object_or_404(Locale, language_code=selected_locale)
            return Locale.get_default()

        return None

    def _get_edit_handler(self):
        return get_snippet_edit_handler(self.model)

    def dispatch(self, request, *args, **kwargs):
        permission = get_permission_name("add", self.model)

        if not request.user.has_perm(permission):
            raise PermissionDenied

        hooks_result = self._run_before_hooks()
        if hooks_result is not None:
            return hooks_result

        return super().dispatch(request, *args, **kwargs)

    def get_add_url(self):
        url = reverse("wagtailsnippets:add", args=[self.app_label, self.model_name])
        if self.locale:
            url += "?locale=" + self.locale.language_code
        return url

    def get_success_url(self):
        urlquery = ""
        if self.locale and self.object.locale is not Locale.get_default():
            urlquery = "?locale=" + self.object.locale.language_code

        return (
            reverse("wagtailsnippets:list", args=[self.app_label, self.model_name])
            + urlquery
        )

    def get_success_message(self, instance):
        return _("%(snippet_type)s '%(instance)s' created.") % {
            "snippet_type": capfirst(self.model._meta.verbose_name),
            "instance": instance,
        }

    def get_success_buttons(self):
        return [
            messages.button(
                reverse(
                    "wagtailsnippets:edit",
                    args=(
                        self.app_label,
                        self.model_name,
                        quote(self.object.pk),
                    ),
                ),
                _("Edit"),
            )
        ]

    def _get_bound_panel(self, form):
        return self.edit_handler.get_bound_panel(
            request=self.request, instance=form.instance, form=form
        )

    def _get_action_menu(self):
        return SnippetActionMenu(self.request, view="create", model=self.model)

    def _get_initial_form_instance(self):
        instance = self.model()

        # Set locale of the new instance
        if self.locale:
            instance.locale = self.locale

        return instance

    def get_form_class(self):
        return self.edit_handler.get_form_class()

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            "instance": self._get_initial_form_instance(),
            "for_user": self.request.user,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        form = context.get("form")
        edit_handler = self._get_bound_panel(form)
        action_menu = self._get_action_menu()
        instance = form.instance

        context.update(
            {
                "model_opts": self.model._meta,
                "edit_handler": edit_handler,
                "action_menu": action_menu,
                "locale": None,
                "translations": [],
                "media": edit_handler.media + form.media + action_menu.media,
            }
        )

        if self.locale:
            context.update(
                {
                    "locale": instance.locale,
                    "translations": [
                        {
                            "locale": locale,
                            "url": reverse(
                                "wagtailsnippets:add",
                                args=[self.app_label, self.model_name],
                            )
                            + "?locale="
                            + locale.language_code,
                        }
                        for locale in Locale.objects.all().exclude(
                            id=instance.locale.id
                        )
                    ],
                }
            )

        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        hooks_result = self._run_after_hooks()
        if hooks_result is not None:
            return hooks_result

        return response


def edit(request, app_label, model_name, pk):
    model = get_snippet_model_from_url_params(app_label, model_name)

    permission = get_permission_name("change", model)
    if not request.user.has_perm(permission):
        raise PermissionDenied

    instance = get_object_or_404(model, pk=unquote(pk))

    for fn in hooks.get_hooks("before_edit_snippet"):
        result = fn(request, instance)
        if hasattr(result, "status_code"):
            return result

    edit_handler = get_snippet_edit_handler(model)
    form_class = edit_handler.get_form_class()

    if request.method == "POST":
        form = form_class(
            request.POST, request.FILES, instance=instance, for_user=request.user
        )

        if form.is_valid():
            with transaction.atomic():
                form.save()
                log(instance=instance, action="wagtail.edit")

            messages.success(
                request,
                _("%(snippet_type)s '%(instance)s' updated.")
                % {
                    "snippet_type": capfirst(model._meta.verbose_name),
                    "instance": instance,
                },
                buttons=[
                    messages.button(
                        reverse(
                            "wagtailsnippets:edit",
                            args=(app_label, model_name, quote(instance.pk)),
                        ),
                        _("Edit"),
                    )
                ],
            )

            for fn in hooks.get_hooks("after_edit_snippet"):
                result = fn(request, instance)
                if hasattr(result, "status_code"):
                    return result

            return redirect("wagtailsnippets:list", app_label, model_name)
        else:
            messages.validation_error(
                request, _("The snippet could not be saved due to errors."), form
            )
    else:
        form = form_class(instance=instance, for_user=request.user)

    edit_handler = edit_handler.get_bound_panel(
        instance=instance, request=request, form=form
    )
    latest_log_entry = log_registry.get_logs_for_instance(instance).first()
    action_menu = SnippetActionMenu(request, view="edit", instance=instance)

    context = {
        "model_opts": model._meta,
        "instance": instance,
        "edit_handler": edit_handler,
        "form": form,
        "action_menu": action_menu,
        "locale": None,
        "translations": [],
        "latest_log_entry": latest_log_entry,
        "media": edit_handler.media + form.media + action_menu.media,
    }

    if getattr(settings, "WAGTAIL_I18N_ENABLED", False) and issubclass(
        model, TranslatableMixin
    ):
        context.update(
            {
                "locale": instance.locale,
                "translations": [
                    {
                        "locale": translation.locale,
                        "url": reverse(
                            "wagtailsnippets:edit",
                            args=[app_label, model_name, quote(translation.pk)],
                        ),
                    }
                    for translation in instance.get_translations().select_related(
                        "locale"
                    )
                ],
            }
        )

    return TemplateResponse(request, "wagtailsnippets/snippets/edit.html", context)


def delete(request, app_label, model_name, pk=None):
    model = get_snippet_model_from_url_params(app_label, model_name)

    permission = get_permission_name("delete", model)
    if not request.user.has_perm(permission):
        raise PermissionDenied

    if pk:
        instances = [get_object_or_404(model, pk=unquote(pk))]
    else:
        ids = request.GET.getlist("id")
        instances = model.objects.filter(pk__in=ids)

    for fn in hooks.get_hooks("before_delete_snippet"):
        result = fn(request, instances)
        if hasattr(result, "status_code"):
            return result

    count = len(instances)

    if request.method == "POST":
        with transaction.atomic():
            for instance in instances:
                log(instance=instance, action="wagtail.delete")
                instance.delete()

        if count == 1:
            message_content = _("%(snippet_type)s '%(instance)s' deleted.") % {
                "snippet_type": capfirst(model._meta.verbose_name),
                "instance": instance,
            }
        else:
            # This message is only used in plural form, but we'll define it with ngettext so that
            # languages with multiple plural forms can be handled correctly (or, at least, as
            # correctly as possible within the limitations of verbose_name_plural...)
            message_content = ngettext(
                "%(count)d %(snippet_type)s deleted.",
                "%(count)d %(snippet_type)s deleted.",
                count,
            ) % {
                "snippet_type": capfirst(model._meta.verbose_name_plural),
                "count": count,
            }

        messages.success(request, message_content)

        for fn in hooks.get_hooks("after_delete_snippet"):
            result = fn(request, instances)
            if hasattr(result, "status_code"):
                return result

        return redirect("wagtailsnippets:list", app_label, model_name)

    return TemplateResponse(
        request,
        "wagtailsnippets/snippets/confirm_delete.html",
        {
            "model_opts": model._meta,
            "count": count,
            "instances": instances,
            "submit_url": (
                reverse("wagtailsnippets:delete-multiple", args=(app_label, model_name))
                + "?"
                + urlencode([("id", instance.pk) for instance in instances])
            ),
        },
    )


class Usage(IndexView):
    template_name = "wagtailsnippets/snippets/usage.html"
    paginate_by = 20
    page_kwarg = "p"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.app_label = kwargs.get("app_label")
        self.model_name = kwargs.get("model_name")
        self.pk = kwargs.get("pk")
        self.model = self._get_model()
        self.instance = self._get_instance()

    def _get_model(self):
        return get_snippet_model_from_url_params(self.app_label, self.model_name)

    def _get_instance(self):
        return get_object_or_404(self.model, pk=unquote(self.pk))

    def get_queryset(self):
        return self.instance.get_usage()

    def paginate_queryset(self, queryset, page_size):
        paginator = self.get_paginator(
            queryset,
            page_size,
            orphans=self.get_paginate_orphans(),
            allow_empty_first_page=self.get_allow_empty(),
        )

        page_number = self.request.GET.get(self.page_kwarg)
        page = paginator.get_page(page_number)
        return (paginator, page, page.object_list, page.has_other_pages())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"instance": self.instance, "used_by": context.get("page_obj")})
        return context


def redirect_to_edit(request, app_label, model_name, pk):
    return redirect("wagtailsnippets:edit", app_label, model_name, pk, permanent=True)


def redirect_to_delete(request, app_label, model_name, pk):
    return redirect("wagtailsnippets:delete", app_label, model_name, pk, permanent=True)


def redirect_to_usage(request, app_label, model_name, pk):
    return redirect("wagtailsnippets:usage", app_label, model_name, pk, permanent=True)


class HistoryView(IndexView):
    template_name = "wagtailadmin/generic/index.html"
    page_title = gettext_lazy("Snippet history")
    header_icon = "history"
    paginate_by = 50
    columns = [
        Column("message", label=gettext_lazy("Action")),
        UserColumn("user", blank_display_name="system"),
        DateColumn("timestamp", label=gettext_lazy("Date")),
    ]

    def dispatch(self, request, app_label, model_name, pk):
        self.app_label = app_label
        self.model_name = model_name
        self.model = get_snippet_model_from_url_params(app_label, model_name)
        self.object = get_object_or_404(self.model, pk=unquote(pk))

        return super().dispatch(request)

    def get_page_subtitle(self):
        return str(self.object)

    def get_index_url(self):
        return reverse(
            "wagtailsnippets:history",
            args=(self.app_label, self.model_name, quote(self.object.pk)),
        )

    def get_queryset(self):
        return log_registry.get_logs_for_instance(self.object).prefetch_related(
            "user__wagtail_userprofile"
        )
