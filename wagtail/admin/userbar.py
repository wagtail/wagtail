from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _


class BaseItem:
    template = "wagtailadmin/userbar/item_base.html"

    def get_context_data(self, request):
        return {"self": self, "request": request}

    def render(self, request):
        return render_to_string(
            self.template, self.get_context_data(request), request=request
        )


class AdminItem(BaseItem):
    template = "wagtailadmin/userbar/item_admin.html"

    def render(self, request):
        # Don't render if user doesn't have permission to access the admin area
        if not request.user.has_perm("wagtailadmin.access_admin"):
            return ""

        return super().render(request)


class AccessibilityItem(BaseItem):
    """A userbar item that runs the accessibility checker."""

    #: The template to use for rendering the item.
    template = "wagtailadmin/userbar/item_accessibility.html"

    #: A list of CSS selector(s) to test specific parts of the page.
    #: For more details, see `Axe documentation <https://github.com/dequelabs/axe-core/blob/master/doc/context.md#the-include-property>`__.
    axe_include = ["body"]

    #: A list of CSS selector(s) to exclude specific parts of the page from testing.
    #: For more details, see `Axe documentation <https://github.com/dequelabs/axe-core/blob/master/doc/context.md#exclude-elements-from-test>`__.
    axe_exclude = []

    # Make sure that the userbar is not tested.
    _axe_default_exclude = [{"fromShadowDOM": ["wagtail-userbar"]}]

    #: A list of `axe-core tags <https://github.com/dequelabs/axe-core/blob/master/doc/API.md#axe-core-tags>`_
    #: or a list of `axe-core rule IDs <https://github.com/dequelabs/axe-core/blob/master/doc/rule-descriptions.md>`_
    #: (not a mix of both).
    #: Setting this to a falsy value (e.g. ``None``) will omit the ``runOnly`` option and make Axe run with all non-experimental rules enabled.
    axe_run_only = [
        "button-name",
        "empty-heading",
        "empty-table-header",
        "frame-title",
        "heading-order",
        "input-button-name",
        "link-name",
        "p-as-heading",
    ]

    #: A dictionary that maps axe-core rule IDs to a dictionary of rule options,
    #: commonly in the format of ``{"enabled": True/False}``. This can be used in
    #: conjunction with :attr:`axe_run_only` to enable or disable specific rules.
    #: For more details, see `Axe documentation <https://github.com/dequelabs/axe-core/blob/master/doc/API.md#options-parameter-examples>`__.
    axe_rules = {}

    #: A list to add custom Axe rules or override their properties,
    #: alongside with ``axe_custom_checks``. Includes Wagtail’s custom rules.
    #: For more details, see `Axe documentation <https://github.com/dequelabs/axe-core/blob/master/doc/API.md#api-name-axeconfigure>`_.
    axe_custom_rules = [
        {
            "id": "alt-text-quality",
            "impact": "serious",
            "selector": "img[alt]",
            "tags": ["best-practice"],
            "any": ["check-image-alt-text"],
            # If omitted, defaults to True and overrides configs in `axe_run_only`.
            "enabled": True,
        },
    ]

    #: A list to add custom Axe checks or override their properties.
    #: Should be used in conjunction with ``axe_custom_rules``.
    #: For more details, see `Axe documentation <https://github.com/dequelabs/axe-core/blob/master/doc/API.md#api-name-axeconfigure>`_.
    axe_custom_checks = [
        {
            "id": "check-image-alt-text",
            "options": {"pattern": "\\.(avif|gif|jpg|jpeg|png|svg|webp)$|_"},
        },
    ]

    #: A dictionary that maps axe-core rule IDs to custom translatable strings
    #: to use as the error messages. If an enabled rule does not exist in this
    #: dictionary, Axe's error message for the rule will be used as fallback.
    axe_messages = {
        "button-name": {
            "error_name": _("Button text is empty"),
            "help_text": _("Use meaningful text for screen reader users"),
        },
        "empty-heading": {
            "error_name": _("Empty heading found"),
            "help_text": _("Use meaningful text for screen reader users"),
        },
        "empty-table-header": {
            "error_name": _("Table header text is empty"),
            "help_text": _("Use meaningful text for screen reader users"),
        },
        "frame-title": {
            "error_name": _("Empty frame title found"),
            "help_text": _("Use a meaningful title for screen reader users"),
        },
        "heading-order": {
            "error_name": _("Incorrect heading hierarchy"),
            "help_text": _("Avoid skipping levels"),
        },
        "input-button-name": {
            "error_name": _("Input button text is empty"),
            "help_text": _("Use meaningful text for screen reader users"),
        },
        "link-name": {
            "error_name": _("Link text is empty"),
            "help_text": _("Use meaningful text for screen reader users"),
        },
        "p-as-heading": {
            "error_name": _("Misusing paragraphs as headings"),
            "help_text": _("Use proper heading tags"),
        },
        "alt-text-quality": {
            "error_name": _("Image alt text has inappropriate pattern"),
            "help_text": _("Use meaningful text"),
        },
    }

    def get_axe_include(self, request):
        """Returns a list of CSS selector(s) to test specific parts of the page."""
        return self.axe_include

    def get_axe_exclude(self, request):
        """Returns a list of CSS selector(s) to exclude specific parts of the page from testing."""
        return self.axe_exclude + self._axe_default_exclude

    def get_axe_run_only(self, request):
        """Returns a list of axe-core tags or a list of axe-core rule IDs (not a mix of both)."""
        return self.axe_run_only

    def get_axe_rules(self, request):
        """Returns a dictionary that maps axe-core rule IDs to a dictionary of rule options."""
        return self.axe_rules

    def get_axe_custom_rules(self, request):
        """List of rule objects per axe.run API."""
        return self.axe_custom_rules

    def get_axe_custom_checks(self, request):
        """List of check objects per axe.run API, without evaluate function."""
        return self.axe_custom_checks

    def get_axe_messages(self, request):
        """Returns a dictionary that maps axe-core rule IDs to custom translatable strings."""
        return self.axe_messages

    def get_axe_context(self, request):
        """
        Returns the `context object <https://github.com/dequelabs/axe-core/blob/develop/doc/context.md>`_
        to be passed as the
        `context parameter <https://github.com/dequelabs/axe-core/blob/develop/doc/API.md#context-parameter>`_
        for ``axe.run``.
        """
        return {
            "include": self.get_axe_include(request),
            "exclude": self.get_axe_exclude(request),
        }

    def get_axe_options(self, request):
        """
        Returns the options object to be passed as the
        `options parameter <https://github.com/dequelabs/axe-core/blob/develop/doc/API.md#options-parameter>`_
        for ``axe.run``.
        """
        options = {
            "runOnly": self.get_axe_run_only(request),
            "rules": self.get_axe_rules(request),
        }
        # If the runOnly option is omitted, Axe will run all rules except those
        # with the "experimental" flag or that are disabled in the rules option.
        # The runOnly has to be omitted (instead of set to an empty list or null)
        # for this to work, so we remove it if it's falsy.
        if not options["runOnly"]:
            options.pop("runOnly")
        return options

    def get_axe_spec(self, request):
        """Returns spec for Axe, including custom rules and custom checks"""
        return {
            "rules": self.get_axe_custom_rules(request),
            "checks": self.get_axe_custom_checks(request),
        }

    def get_axe_configuration(self, request):
        return {
            "context": self.get_axe_context(request),
            "options": self.get_axe_options(request),
            "messages": self.get_axe_messages(request),
            "spec": self.get_axe_spec(request),
        }

    def get_context_data(self, request):
        return {
            **super().get_context_data(request),
            "axe_configuration": self.get_axe_configuration(request),
        }

    def render(self, request):
        # Don't render if user doesn't have permission to access the admin area
        if not request.user.has_perm("wagtailadmin.access_admin"):
            return ""

        return super().render(request)


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
            if request.is_preview and request.is_editing:
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
