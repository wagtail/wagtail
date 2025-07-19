from time import time

from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.http.request import QueryDict
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.translation import gettext
from django.views.generic import TemplateView, View

from wagtail.admin.forms.models import WagtailAdminModelForm
from wagtail.admin.panels import get_edit_handler
from wagtail.blocks.base import Block
from wagtail.models import PreviewableMixin, RevisionMixin
from wagtail.utils.decorators import xframe_options_sameorigin_override


class PreviewOnEdit(View):
    model = None
    form_class = None
    http_method_names = ("post", "get", "delete")
    preview_expiration_timeout = 60 * 60 * 24  # seconds
    session_key_prefix = "wagtail-preview-"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.object = self.get_object()

    def dispatch(self, request, *args, **kwargs):
        if not isinstance(self.object, PreviewableMixin):
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def remove_old_preview_data(self):
        expiration = time() - self.preview_expiration_timeout
        expired_keys = [
            k
            for k, v in self.request.session.items()
            if k.startswith(self.session_key_prefix) and v[1] < expiration
        ]
        # Removes the session key gracefully
        for k in expired_keys:
            self.request.session.pop(k)

    @property
    def session_key(self):
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        unique_key = f"{app_label}-{model_name}-{self.object.pk}"
        return f"{self.session_key_prefix}{unique_key}"

    def get_object(self):
        obj = get_object_or_404(self.model, pk=unquote(str(self.kwargs["pk"])))
        if isinstance(obj, RevisionMixin):
            obj = obj.get_latest_revision_as_object()
        return obj

    def get_form_class(self):
        if self.form_class:
            return self.form_class
        return get_edit_handler(self.model).get_form_class()

    def get_form(self, query_dict):
        form_class = self.get_form_class()

        if not query_dict:
            # Query dict is empty, return null form
            return form_class(instance=self.object, for_user=self.request.user)

        return form_class(query_dict, instance=self.object, for_user=self.request.user)

    def _get_data_from_session(self):
        post_data, _ = self.request.session.get(self.session_key, (None, None))
        if not isinstance(post_data, str):
            post_data = ""
        return QueryDict(post_data)

    def validate_form(self, form):
        if isinstance(form, WagtailAdminModelForm):
            form.defer_required_fields()
        return form.is_valid()

    def post(self, request, *args, **kwargs):
        self.remove_old_preview_data()
        form = self.get_form(request.POST)
        is_valid = self.validate_form(form)

        if is_valid:
            # TODO: Handle request.FILES.
            request.session[self.session_key] = request.POST.urlencode(), time()
            is_available = True
        else:
            # Check previous data in session to determine preview availability
            form = self.get_form(self._get_data_from_session())
            is_available = self.validate_form(form)

        return JsonResponse({"is_valid": is_valid, "is_available": is_available})

    def error_response(self):
        return TemplateResponse(
            self.request,
            "wagtailadmin/generic/preview_error.html",
            {"object": self.object},
        )

    def get_extra_request_attrs(self):
        return {
            "in_preview_panel": self.request.GET.get("in_preview_panel") == "true",
            "is_editing": True,
        }

    @method_decorator(xframe_options_sameorigin_override)
    def get(self, request, *args, **kwargs):
        form = self.get_form(self._get_data_from_session())

        if not self.validate_form(form):
            return self.error_response()

        form.save(commit=False)

        try:
            preview_mode = request.GET.get("mode", self.object.default_preview_mode)
        except IndexError:
            raise PermissionDenied

        extra_attrs = self.get_extra_request_attrs()

        return self.object.make_preview_request(request, preview_mode, extra_attrs)

    def delete(self, request, *args, **kwargs):
        request.session.pop(self.session_key, None)
        return JsonResponse({"success": True})


class PreviewOnCreate(PreviewOnEdit):
    @property
    def session_key(self):
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        return f"{self.session_key_prefix}{app_label}-{model_name}"

    def get_object(self):
        return self.model()


class PreviewRevision(View):
    model = None
    http_method_names = ("get",)

    def setup(self, request, pk, revision_id, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.pk = pk
        self.revision_id = revision_id
        self.object = self.get_object()
        self.revision_object = self.get_revision_object()

    def get_object(self):
        if not issubclass(self.model, RevisionMixin):
            raise Http404
        return get_object_or_404(self.model, pk=unquote(str(self.pk)))

    def get_revision_object(self):
        revision = get_object_or_404(self.object.revisions, id=self.revision_id)
        return revision.as_object()

    def get(self, request, *args, **kwargs):
        try:
            preview_mode = request.GET.get(
                "mode", self.revision_object.default_preview_mode
            )
        except IndexError:
            raise PermissionDenied

        return self.revision_object.make_preview_request(request, preview_mode)


@method_decorator(xframe_options_sameorigin_override, name="get")
class StreamFieldBlockPreview(TemplateView):
    http_method_names = ("get",)

    @cached_property
    def block_id(self):
        return self.request.GET.get("id")

    @cached_property
    def block_def(self) -> Block:
        if not (block := Block.definition_registry.get(self.block_id)):
            raise Http404
        return block

    @cached_property
    def block_value(self):
        return self.block_def.get_preview_value()

    @cached_property
    def page_title(self):
        return gettext("Preview for %(block_label)s (%(block_type)s)") % {
            "block_label": self.block_def.label,
            "block_type": self.block_def.__class__.__name__,
        }

    @cached_property
    def base_context(self):
        # Do NOT use the name `block` in the context, as it will conflict with
        # the current block inside a template {% block %} tag.
        # If any changes are made here that needs to be publicly documented,
        # make sure to update the docs for `Block.get_preview_context`.
        return {
            "request": self.request,
            "block_def": self.block_def,
            "block_class": self.block_def.__class__,
            "bound_block": self.block_def.bind(self.block_value),
            "page_title": self.page_title,
        }

    def get_template_names(self):
        return self.block_def.get_preview_template(self.block_value, self.base_context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.base_context)
        return self.block_def.get_preview_context(self.block_value, context)
