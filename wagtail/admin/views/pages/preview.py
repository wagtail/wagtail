from time import time

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.http.request import QueryDict
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.generic import View

from wagtail.models import Page
from wagtail.utils.decorators import xframe_options_sameorigin_override


def view_draft(request, page_id):
    page = get_object_or_404(Page, id=page_id).get_latest_revision_as_object()
    perms = page.permissions_for_user(request.user)
    if not (perms.can_publish() or perms.can_edit()):
        raise PermissionDenied

    try:
        preview_mode = page.default_preview_mode
    except IndexError:
        raise PermissionDenied

    return page.make_preview_request(request, preview_mode)


class PreviewOnEdit(View):
    http_method_names = ("post", "get")
    preview_expiration_timeout = 60 * 60 * 24  # seconds
    session_key_prefix = "wagtail-preview-"

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
        return "{}{}".format(self.session_key_prefix, self.kwargs["page_id"])

    def get_page(self):
        return get_object_or_404(
            Page, id=self.kwargs["page_id"]
        ).get_latest_revision_as_object()

    def get_form(self, page, query_dict):
        form_class = page.get_edit_handler().get_form_class()
        parent_page = page.get_parent().specific

        if not query_dict:
            # Query dict is empty, return null form
            return form_class(instance=page, parent_page=parent_page)

        return form_class(query_dict, instance=page, parent_page=parent_page)

    def _get_data_from_session(self):
        post_data, _ = self.request.session.get(self.session_key, (None, None))
        if not isinstance(post_data, str):
            post_data = ""
        return QueryDict(post_data)

    def post(self, request, *args, **kwargs):
        self.remove_old_preview_data()
        page = self.get_page()
        form = self.get_form(page, request.POST)
        is_valid = form.is_valid()

        if is_valid:
            # TODO: Handle request.FILES.
            request.session[self.session_key] = request.POST.urlencode(), time()
            is_available = True
        else:
            # Check previous data in session to determine preview availability
            form = self.get_form(page, self._get_data_from_session())
            is_available = form.is_valid()

        return JsonResponse({"is_valid": is_valid, "is_available": is_available})

    def error_response(self, page):
        return TemplateResponse(
            self.request, "wagtailadmin/pages/preview_error.html", {"page": page}
        )

    @method_decorator(xframe_options_sameorigin_override)
    def get(self, request, *args, **kwargs):
        page = self.get_page()
        form = self.get_form(page, self._get_data_from_session())

        if not form.is_valid():
            return self.error_response(page)

        form.save(commit=False)

        try:
            preview_mode = request.GET.get("mode", page.default_preview_mode)
        except IndexError:
            raise PermissionDenied

        extra_attrs = {
            "in_preview_panel": request.GET.get("in_preview_panel") == "true"
        }

        return page.make_preview_request(request, preview_mode, extra_attrs)


class PreviewOnCreate(PreviewOnEdit):
    @property
    def session_key(self):
        return "{}{}-{}-{}".format(
            self.session_key_prefix,
            self.kwargs["content_type_app_name"],
            self.kwargs["content_type_model_name"],
            self.kwargs["parent_page_id"],
        )

    def get_page(self):
        content_type_app_name = self.kwargs["content_type_app_name"]
        content_type_model_name = self.kwargs["content_type_model_name"]
        parent_page_id = self.kwargs["parent_page_id"]
        try:
            content_type = ContentType.objects.get_by_natural_key(
                content_type_app_name, content_type_model_name
            )
        except ContentType.DoesNotExist:
            raise Http404

        page = content_type.model_class()()
        parent_page = get_object_or_404(Page, id=parent_page_id).specific
        # We need to populate treebeard's path / depth fields in order to
        # pass validation. We can't make these 100% consistent with the rest
        # of the tree without making actual database changes (such as
        # incrementing the parent's numchild field), but by calling treebeard's
        # internal _get_path method, we can set a 'realistic' value that will
        # hopefully enable tree traversal operations
        # to at least partially work.
        page.depth = parent_page.depth + 1
        # Puts the page at the next available path
        # for a child of `parent_page`.
        if parent_page.is_leaf():
            # set the path as the first child of parent_page
            page.path = page._get_path(parent_page.path, page.depth, 1)
        else:
            # add the new page after the last child of parent_page
            page.path = parent_page.get_last_child()._inc_path()

        return page

    def get_form(self, page, query_dict):
        form = super().get_form(page, query_dict)
        if form.is_valid():
            # Ensures our unsaved page has a suitable url.
            form.instance.set_url_path(form.parent_page)

            form.instance.full_clean()
        return form
