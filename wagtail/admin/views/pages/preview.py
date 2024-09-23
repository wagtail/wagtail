from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404

from wagtail.admin.views.generic.preview import PreviewOnEdit as GenericPreviewOnEdit
from wagtail.models import Page


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


class PreviewOnEdit(GenericPreviewOnEdit):
    @property
    def session_key(self):
        return "{}{}".format(self.session_key_prefix, self.kwargs["page_id"])

    def get_object(self):
        return get_object_or_404(
            Page, id=self.kwargs["page_id"]
        ).get_latest_revision_as_object()

    def get_form(self, query_dict):
        form_class = self.object.get_edit_handler().get_form_class()
        parent_page = self.object.get_parent().specific

        if not query_dict:
            # Query dict is empty, return null form
            return form_class(
                instance=self.object,
                parent_page=parent_page,
                for_user=self.request.user,
            )

        return form_class(
            query_dict,
            instance=self.object,
            parent_page=parent_page,
            for_user=self.request.user,
        )


class PreviewOnCreate(PreviewOnEdit):
    @property
    def session_key(self):
        return "{}{}-{}-{}".format(
            self.session_key_prefix,
            self.kwargs["content_type_app_name"],
            self.kwargs["content_type_model_name"],
            self.kwargs["parent_page_id"],
        )

    def get_object(self):
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

    def get_form(self, query_dict):
        form = super().get_form(query_dict)
        if form.is_valid():
            # Ensures our unsaved page has a suitable url.
            form.instance.set_url_path(form.parent_page)

            form.instance.full_clean()
        return form
