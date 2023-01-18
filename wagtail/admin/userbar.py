from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _


class BaseItem:
    template = "wagtailadmin/userbar/item_base.html"

    def render(self, request):
        return render_to_string(
            self.template, {"self": self, "request": request}, request=request
        )


class AdminItem(BaseItem):
    template = "wagtailadmin/userbar/item_admin.html"

    def render(self, request):

        # Don't render if user doesn't have permission to access the admin area
        if not request.user.has_perm("wagtailadmin.access_admin"):
            return ""

        return super().render(request)


class AccessibilityItem(BaseItem):
    template = "wagtailadmin/userbar/item_accessibility.html"

    def get_axe_configuration(self):
        return {
            # See https://github.com/dequelabs/axe-core/blob/develop/doc/context.md.
            "context": {
                "include": "body",
                "exclude": {"fromShadowDOM": ["wagtail-userbar"]},
            },
            # See https://github.com/dequelabs/axe-core/blob/develop/doc/API.md#options-parameter.
            "options": {
                "runOnly": {
                    "type": "rule",
                    "values": [
                        "empty-heading",
                        "heading-order",
                        "p-as-heading",
                    ],
                }
            },
            # Wagtail-specific translatable custom error messages.
            "messages": {
                "empty-heading": _(
                    "Empty heading found. Use meaningful text in headings."
                ),
                "heading-order": _(
                    "Incorrect heading hierarchy. Avoid skipping levels."
                ),
                "p-as-heading": _(
                    "Misusing paragraphs as headings. Use proper heading tags."
                ),
            },
        }

    def render(self, request):

        # Don't render if user doesn't have permission to access the admin area
        if not request.user.has_perm("wagtailadmin.access_admin"):
            return ""

        return render_to_string(
            self.template,
            {
                "self": self,
                "request": request,
                "axe_configuration": self.get_axe_configuration(),
            },
            request=request,
        )


class AddPageItem(BaseItem):
    template = "wagtailadmin/userbar/item_page_add.html"

    def __init__(self, page):
        self.page = page
        self.parent_page = page.get_parent()

    def render(self, request):
        # Don't render if the page doesn't have an id
        if not self.page.id:
            return ""

        # Don't render if user doesn't have permission to access the admin area
        if not request.user.has_perm("wagtailadmin.access_admin"):
            return ""

        # Don't render if user doesn't have ability to add children here
        permission_checker = self.page.permissions_for_user(request.user)
        if not permission_checker.can_add_subpage():
            return ""

        return super().render(request)


class ExplorePageItem(BaseItem):
    template = "wagtailadmin/userbar/item_page_explore.html"

    def __init__(self, page):
        self.page = page
        self.parent_page = page.get_parent()

    def render(self, request):
        # Don't render if the page doesn't have an id
        if not self.page.id:
            return ""

        # Don't render if user doesn't have permission to access the admin area
        if not request.user.has_perm("wagtailadmin.access_admin"):
            return ""

        # Don't render if user doesn't have ability to edit or publish sub-pages on the parent page
        permission_checker = self.parent_page.permissions_for_user(request.user)
        if (
            not permission_checker.can_edit()
            and not permission_checker.can_publish_subpage()
        ):
            return ""

        return super().render(request)


class EditPageItem(BaseItem):
    template = "wagtailadmin/userbar/item_page_edit.html"

    def __init__(self, page):
        self.page = page

    def render(self, request):
        # Don't render if the page doesn't have an id
        if not self.page.id:
            return ""

        # Don't render if request is a preview. This is to avoid confusion that
        # might arise when the user clicks edit on a preview.
        try:
            if request.is_preview:
                return ""
        except AttributeError:
            pass

        # Don't render if user doesn't have permission to access the admin area
        if not request.user.has_perm("wagtailadmin.access_admin"):
            return ""

        # Don't render if the user doesn't have permission to edit this page
        permission_checker = self.page.permissions_for_user(request.user)
        if not permission_checker.can_edit():
            return ""

        return super().render(request)


class ModeratePageItem(BaseItem):
    def __init__(self, revision):
        self.revision = revision

    def render(self, request):
        if not self.revision.id:
            return ""

        if not self.revision.submitted_for_moderation:
            return ""

        if not request.user.has_perm("wagtailadmin.access_admin"):
            return ""

        if not self.revision.content_object.permissions_for_user(
            request.user
        ).can_publish():
            return ""

        return super().render(request)


class ApproveModerationEditPageItem(ModeratePageItem):
    template = "wagtailadmin/userbar/item_page_approve.html"


class RejectModerationEditPageItem(ModeratePageItem):
    template = "wagtailadmin/userbar/item_page_reject.html"
