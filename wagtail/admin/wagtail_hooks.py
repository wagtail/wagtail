from django.conf import settings
from django.contrib.auth.models import Permission
from django.urls import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from draftjs_exporter.dom import DOM

import wagtail.admin.rich_text.editors.draftail.features as draftail_features
from wagtail import __version__, hooks
from wagtail.admin.admin_url_finder import (
    ModelAdminURLFinder,
    register_admin_url_finder,
)
from wagtail.admin.auth import user_has_any_page_permission
from wagtail.admin.forms.collections import GroupCollectionManagementPermissionFormSet
from wagtail.admin.menu import (
    DismissibleMenuItem,
    DismissibleSubmenuMenuItem,
    MenuItem,
    SubmenuMenuItem,
    help_menu,
    reports_menu,
    settings_menu,
)
from wagtail.admin.rich_text.converters.contentstate import link_entity
from wagtail.admin.rich_text.converters.editor_html import (
    LinkTypeRule,
    PageLinkHandler,
    WhitelistRule,
)
from wagtail.admin.rich_text.converters.html_to_contentstate import (
    BlockElementHandler,
    ExternalLinkElementHandler,
    HorizontalRuleHandler,
    InlineStyleElementHandler,
    ListElementHandler,
    ListItemElementHandler,
    PageLinkElementHandler,
)
from wagtail.admin.search import SearchArea
from wagtail.admin.site_summary import PagesSummaryItem
from wagtail.admin.ui.menus.pages import PageMenuItem
from wagtail.admin.ui.sidebar import (
    PageExplorerMenuItem as PageExplorerMenuItemComponent,
)
from wagtail.admin.ui.sidebar import SubMenuItem as SubMenuItemComponent
from wagtail.admin.views.pages.bulk_actions import (
    DeleteBulkAction,
    MoveBulkAction,
    PublishBulkAction,
    UnpublishBulkAction,
)
from wagtail.admin.viewsets import viewsets
from wagtail.admin.widgets import ButtonWithDropdownFromHook
from wagtail.models import Collection, Page, Task, Workflow
from wagtail.permissions import (
    collection_permission_policy,
    page_permission_policy,
    task_permission_policy,
    workflow_permission_policy,
)
from wagtail.templatetags.wagtailcore_tags import (
    wagtail_feature_release_editor_guide_link,
    wagtail_feature_release_whats_new_link,
)
from wagtail.utils.version import get_main_version
from wagtail.whitelist import allow_without_attributes, attribute_rule, check_url


class ExplorerMenuItem(MenuItem):
    def is_shown(self, request):
        return user_has_any_page_permission(request.user)

    def get_context(self, request):
        context = super().get_context(request)
        start_page = page_permission_policy.explorable_root_instance(request.user)

        if start_page:
            context["start_page_id"] = start_page.id

        return context

    def render_component(self, request):
        start_page = page_permission_policy.explorable_root_instance(request.user)

        if start_page:
            return PageExplorerMenuItemComponent(
                self.name,
                self.label,
                self.url,
                start_page.id,
                icon_name=self.icon_name,
                classname=self.classname,
            )
        else:
            return super().render_component(request)


@hooks.register("register_admin_menu_item")
def register_explorer_menu_item():
    return ExplorerMenuItem(
        _("Pages"),
        reverse("wagtailadmin_explore_root"),
        name="explorer",
        icon_name="folder-open-inverse",
        order=100,
    )


class SettingsMenuItem(SubmenuMenuItem):
    def render_component(self, request):
        return SubMenuItemComponent(
            self.name,
            self.label,
            self.menu.render_component(request),
            icon_name=self.icon_name,
            classname=self.classname,
            footer_text="Wagtail v" + __version__,
        )


@hooks.register("register_admin_menu_item")
def register_settings_menu():
    return SettingsMenuItem(
        _("Settings"),
        settings_menu,
        name="settings",
        icon_name="cogs",
        order=10000,
    )


@hooks.register("register_permissions")
def register_permissions():
    return Permission.objects.filter(
        content_type__app_label="wagtailadmin", codename="access_admin"
    )


class PageSearchArea(SearchArea):
    def __init__(self):
        super().__init__(
            _("Pages"),
            reverse("wagtailadmin_pages:search"),
            name="pages",
            icon_name="folder-open-inverse",
            order=100,
        )

    def is_shown(self, request):
        return user_has_any_page_permission(request.user)


@hooks.register("register_admin_search_area")
def register_pages_search_area():
    return PageSearchArea()


@hooks.register("register_group_permission_panel")
def register_collection_permissions_panel():
    return GroupCollectionManagementPermissionFormSet


class CollectionsMenuItem(MenuItem):
    def is_shown(self, request):
        return collection_permission_policy.user_has_any_permission(
            request.user, ["add", "change", "delete"]
        )


@hooks.register("register_settings_menu_item")
def register_collections_menu_item():
    return CollectionsMenuItem(
        _("Collections"),
        reverse("wagtailadmin_collections:index"),
        name="collections",
        icon_name="folder-open-1",
        order=700,
    )


class WorkflowsMenuItem(MenuItem):
    def is_shown(self, request):
        if not getattr(settings, "WAGTAIL_WORKFLOW_ENABLED", True):
            return False

        return workflow_permission_policy.user_has_any_permission(
            request.user, ["add", "change", "delete"]
        )


class WorkflowTasksMenuItem(MenuItem):
    def is_shown(self, request):
        if not getattr(settings, "WAGTAIL_WORKFLOW_ENABLED", True):
            return False

        return task_permission_policy.user_has_any_permission(
            request.user, ["add", "change", "delete"]
        )


@hooks.register("register_settings_menu_item")
def register_workflows_menu_item():
    return WorkflowsMenuItem(
        _("Workflows"),
        reverse("wagtailadmin_workflows:index"),
        name="workflows",
        icon_name="tasks",
        order=100,
    )


@hooks.register("register_settings_menu_item")
def register_workflow_tasks_menu_item():
    return WorkflowTasksMenuItem(
        _("Workflow tasks"),
        reverse("wagtailadmin_workflows:task_index"),
        name="workflow-tasks",
        icon_name="thumbtack",
        order=150,
    )


@hooks.register("register_page_listing_buttons")
def page_listing_buttons(page, user, next_url=None):
    yield ButtonWithDropdownFromHook(
        "",
        hook_name="register_page_listing_more_buttons",
        page=page,
        user=user,
        next_url=next_url,
        icon_name="dots-horizontal",
        attrs={
            "aria-label": _("More options for '%(title)s'")
            % {"title": page.get_admin_display_title()},
        },
        priority=50,
    )


class PageListingEditButton(PageMenuItem):
    label = _("Edit")
    icon_name = "edit"
    url_name = "wagtailadmin_pages:edit"

    def is_shown(self, user):
        return self.page.permissions_for_user(user).can_edit()


class PageListingViewDraftButton(PageMenuItem):
    label = _("View draft")
    icon_name = "draft"
    url_name = "wagtailadmin_pages:view_draft"
    link_rel = "noreferrer"

    def is_shown(self, user):
        return self.page.has_unpublished_changes and self.page.is_previewable()


class PageListingViewLiveButton(PageMenuItem):
    label = _("View live")
    icon_name = "doc-empty"
    link_rel = "noreferrer"

    def is_shown(self, user):
        return self.page.live and self.page.url


class PageListingAddChildPageButton(PageMenuItem):
    label = _("Add child page")
    icon_name = "circle-plus"
    url_name = "wagtailadmin_pages:add_subpage"

    def is_shown(self, user):
        return self.page.permissions_for_user(user).can_add_subpage()


class PageListingMoveButton(PageMenuItem):
    label = _("Move")
    icon_name = "arrow-right-full"
    url_name = "wagtailadmin_pages:move"

    def is_shown(self, user):
        return self.page.permissions_for_user(user).can_move()


class PageListingCopyButton(PageMenuItem):
    label = _("Copy")
    icon_name = "copy"
    url_name = "wagtailadmin_pages:copy"

    def is_shown(self, user):
        return self.page.permissions_for_user(user).can_copy()


class PageListingDeleteButton(PageMenuItem):
    label = _("Delete")
    icon_name = "bin"

    @cached_property
    def url(self):
        if self.page:
            url = reverse("wagtailadmin_pages:delete", args=[self.page.id])
            if self.next_url:
                if self.next_url == reverse(
                    "wagtailadmin_explore", args=[self.page.id]
                ):
                    # cannot redirect to the explore view after deleting the page
                    pass
                elif self.next_url == reverse(
                    "wagtailadmin_pages:edit", args=[self.page.id]
                ):
                    # cannot redirect to the edit view after deleting the page
                    pass
                else:
                    # OK to add the 'next' parameter
                    url += "?" + urlencode({"next": self.next_url})
            return url

    def is_shown(self, user):
        return self.page.permissions_for_user(user).can_delete()


class PageListingUnpublishButton(PageMenuItem):
    label = _("Unpublish")
    icon_name = "download"
    url_name = "wagtailadmin_pages:unpublish"

    def is_shown(self, user):
        return self.page.permissions_for_user(user).can_unpublish()


class PageListingHistoryButton(PageMenuItem):
    label = _("History")
    icon_name = "history"
    url_name = "wagtailadmin_pages:history"

    def is_shown(self, user):
        return self.page.permissions_for_user(user).can_view_revisions()


class PageListingSortMenuOrderButton(PageMenuItem):
    label = _("Sort menu order")
    icon_name = "list-ul"

    def is_shown(self, user):
        return self.page.permissions_for_user(user).can_reorder_children()

    @cached_property
    def url(self):
        return reverse("wagtailadmin_explore", args=[self.page.id]) + "?ordering=ord"


@hooks.register("register_page_listing_more_buttons")
def page_listing_more_buttons(page, user, next_url=None):
    yield PageListingEditButton(page=page, next_url=next_url, priority=2)
    yield PageListingViewDraftButton(page=page, priority=4)
    yield PageListingViewLiveButton(page=page, url=page.url, priority=6)
    yield PageListingAddChildPageButton(page=page, next_url=next_url, priority=8)
    yield PageListingMoveButton(page=page, priority=10)
    yield PageListingCopyButton(page=page, next_url=next_url, priority=20)
    yield PageListingDeleteButton(page=page, next_url=next_url, priority=30)
    yield PageListingUnpublishButton(page=page, next_url=next_url, priority=40)
    yield PageListingHistoryButton(page=page, priority=50)
    yield PageListingSortMenuOrderButton(page=page, priority=60)


@hooks.register("register_page_header_buttons")
def page_header_buttons(page, user, view_name, next_url=None):
    yield PageListingEditButton(page=page, priority=10)

    # "add child" is a separate primary action on the index page
    if view_name != "index":
        yield PageListingAddChildPageButton(page=page, priority=15)

    yield PageListingMoveButton(page=page, priority=20)
    yield PageListingCopyButton(page=page, next_url=next_url, priority=30)
    yield PageListingDeleteButton(page=page, next_url=next_url, priority=50)
    yield PageListingUnpublishButton(page=page, next_url=next_url, priority=60)
    yield PageListingHistoryButton(page=page, priority=65)
    yield PageListingSortMenuOrderButton(page=page, priority=70)


@hooks.register("register_admin_urls")
def register_viewsets_urls():
    viewsets.populate()
    return viewsets.get_urlpatterns()


@hooks.register("register_rich_text_features")
def register_core_features(features):
    features.register_converter_rule(
        "editorhtml",
        "link",
        [
            WhitelistRule("a", attribute_rule({"href": check_url})),
            LinkTypeRule("page", PageLinkHandler),
        ],
    )

    features.register_converter_rule(
        "editorhtml",
        "bold",
        [
            WhitelistRule("b", allow_without_attributes),
            WhitelistRule("strong", allow_without_attributes),
        ],
    )

    features.register_converter_rule(
        "editorhtml",
        "italic",
        [
            WhitelistRule("i", allow_without_attributes),
            WhitelistRule("em", allow_without_attributes),
        ],
    )

    headings_elements = ["h1", "h2", "h3", "h4", "h5", "h6"]
    for order, element in enumerate(headings_elements):
        features.register_converter_rule(
            "editorhtml", element, [WhitelistRule(element, allow_without_attributes)]
        )

    features.register_converter_rule(
        "editorhtml",
        "ol",
        [
            WhitelistRule("ol", allow_without_attributes),
            WhitelistRule("li", allow_without_attributes),
        ],
    )

    features.register_converter_rule(
        "editorhtml",
        "ul",
        [
            WhitelistRule("ul", allow_without_attributes),
            WhitelistRule("li", allow_without_attributes),
        ],
    )

    # Draftail
    features.register_editor_plugin(
        "draftail", "hr", draftail_features.BooleanFeature("enableHorizontalRule")
    )
    features.register_converter_rule(
        "contentstate",
        "hr",
        {
            "from_database_format": {
                "hr": HorizontalRuleHandler(),
            },
            "to_database_format": {
                "entity_decorators": {
                    "HORIZONTAL_RULE": lambda props: DOM.create_element("hr")
                }
            },
        },
    )

    features.register_editor_plugin(
        "draftail",
        "h1",
        draftail_features.BlockFeature(
            {
                "icon": "h1",
                "type": "header-one",
                "description": _("Heading 1"),
            }
        ),
    )
    features.register_converter_rule(
        "contentstate",
        "h1",
        {
            "from_database_format": {
                "h1": BlockElementHandler("header-one"),
            },
            "to_database_format": {"block_map": {"header-one": "h1"}},
        },
    )
    features.register_editor_plugin(
        "draftail",
        "h2",
        draftail_features.BlockFeature(
            {
                "icon": "h2",
                "type": "header-two",
                "description": _("Heading 2"),
            }
        ),
    )
    features.register_converter_rule(
        "contentstate",
        "h2",
        {
            "from_database_format": {
                "h2": BlockElementHandler("header-two"),
            },
            "to_database_format": {"block_map": {"header-two": "h2"}},
        },
    )
    features.register_editor_plugin(
        "draftail",
        "h3",
        draftail_features.BlockFeature(
            {
                "icon": "h3",
                "type": "header-three",
                "description": _("Heading 3"),
            }
        ),
    )
    features.register_converter_rule(
        "contentstate",
        "h3",
        {
            "from_database_format": {
                "h3": BlockElementHandler("header-three"),
            },
            "to_database_format": {"block_map": {"header-three": "h3"}},
        },
    )
    features.register_editor_plugin(
        "draftail",
        "h4",
        draftail_features.BlockFeature(
            {
                "icon": "h4",
                "type": "header-four",
                "description": _("Heading 4"),
            }
        ),
    )
    features.register_converter_rule(
        "contentstate",
        "h4",
        {
            "from_database_format": {
                "h4": BlockElementHandler("header-four"),
            },
            "to_database_format": {"block_map": {"header-four": "h4"}},
        },
    )
    features.register_editor_plugin(
        "draftail",
        "h5",
        draftail_features.BlockFeature(
            {
                "icon": "h5",
                "type": "header-five",
                "description": _("Heading 5"),
            }
        ),
    )
    features.register_converter_rule(
        "contentstate",
        "h5",
        {
            "from_database_format": {
                "h5": BlockElementHandler("header-five"),
            },
            "to_database_format": {"block_map": {"header-five": "h5"}},
        },
    )
    features.register_editor_plugin(
        "draftail",
        "h6",
        draftail_features.BlockFeature(
            {
                "icon": "h6",
                "type": "header-six",
                "description": _("Heading 6"),
            }
        ),
    )
    features.register_converter_rule(
        "contentstate",
        "h6",
        {
            "from_database_format": {
                "h6": BlockElementHandler("header-six"),
            },
            "to_database_format": {"block_map": {"header-six": "h6"}},
        },
    )
    features.register_editor_plugin(
        "draftail",
        "ul",
        draftail_features.BlockFeature(
            {
                "type": "unordered-list-item",
                "icon": "list-ul",
                "description": _("Bulleted list"),
            }
        ),
    )
    features.register_converter_rule(
        "contentstate",
        "ul",
        {
            "from_database_format": {
                "ul": ListElementHandler("unordered-list-item"),
                "li": ListItemElementHandler(),
            },
            "to_database_format": {
                "block_map": {"unordered-list-item": {"element": "li", "wrapper": "ul"}}
            },
        },
    )
    features.register_editor_plugin(
        "draftail",
        "ol",
        draftail_features.BlockFeature(
            {
                "type": "ordered-list-item",
                "icon": "list-ol",
                "description": _("Numbered list"),
            }
        ),
    )
    features.register_converter_rule(
        "contentstate",
        "ol",
        {
            "from_database_format": {
                "ol": ListElementHandler("ordered-list-item"),
                "li": ListItemElementHandler(),
            },
            "to_database_format": {
                "block_map": {"ordered-list-item": {"element": "li", "wrapper": "ol"}}
            },
        },
    )
    features.register_editor_plugin(
        "draftail",
        "blockquote",
        draftail_features.BlockFeature(
            {
                "type": "blockquote",
                "icon": "openquote",
                "description": _("Blockquote"),
            }
        ),
    )
    features.register_converter_rule(
        "contentstate",
        "blockquote",
        {
            "from_database_format": {
                "blockquote": BlockElementHandler("blockquote"),
            },
            "to_database_format": {"block_map": {"blockquote": "blockquote"}},
        },
    )

    features.register_editor_plugin(
        "draftail",
        "bold",
        draftail_features.InlineStyleFeature(
            {
                "type": "BOLD",
                "icon": "bold",
                "description": _("Bold"),
            }
        ),
    )
    features.register_converter_rule(
        "contentstate",
        "bold",
        {
            "from_database_format": {
                "b": InlineStyleElementHandler("BOLD"),
                "strong": InlineStyleElementHandler("BOLD"),
            },
            "to_database_format": {"style_map": {"BOLD": "b"}},
        },
    )
    features.register_editor_plugin(
        "draftail",
        "italic",
        draftail_features.InlineStyleFeature(
            {
                "type": "ITALIC",
                "icon": "italic",
                "description": _("Italic"),
            }
        ),
    )
    features.register_converter_rule(
        "contentstate",
        "italic",
        {
            "from_database_format": {
                "i": InlineStyleElementHandler("ITALIC"),
                "em": InlineStyleElementHandler("ITALIC"),
            },
            "to_database_format": {"style_map": {"ITALIC": "i"}},
        },
    )

    features.register_editor_plugin(
        "draftail",
        "link",
        draftail_features.EntityFeature(
            {
                "type": "LINK",
                "icon": "link",
                "description": _("Link"),
                # We want to enforce constraints on which links can be pasted into rich text.
                # Keep only the attributes Wagtail needs.
                "attributes": ["url", "id", "parentId"],
                "allowlist": {
                    # Keep pasted links with http/https protocol, and not-pasted links (href = undefined).
                    "href": "^(http:|https:|undefined$)",
                },
                "chooserUrls": {
                    "pageChooser": reverse_lazy("wagtailadmin_choose_page"),
                    "externalLinkChooser": reverse_lazy(
                        "wagtailadmin_choose_page_external_link"
                    ),
                    "emailLinkChooser": reverse_lazy(
                        "wagtailadmin_choose_page_email_link"
                    ),
                    "phoneLinkChooser": reverse_lazy(
                        "wagtailadmin_choose_page_phone_link"
                    ),
                    "anchorLinkChooser": reverse_lazy(
                        "wagtailadmin_choose_page_anchor_link"
                    ),
                },
            },
            js=[
                "wagtailadmin/js/page-chooser-modal.js",
            ],
        ),
    )
    features.register_converter_rule(
        "contentstate",
        "link",
        {
            "from_database_format": {
                "a[href]": ExternalLinkElementHandler("LINK"),
                'a[linktype="page"]': PageLinkElementHandler("LINK"),
            },
            "to_database_format": {"entity_decorators": {"LINK": link_entity}},
        },
    )
    features.register_editor_plugin(
        "draftail",
        "superscript",
        draftail_features.InlineStyleFeature(
            {
                "type": "SUPERSCRIPT",
                "icon": "superscript",
                "description": _("Superscript"),
            }
        ),
    )
    features.register_converter_rule(
        "contentstate",
        "superscript",
        {
            "from_database_format": {
                "sup": InlineStyleElementHandler("SUPERSCRIPT"),
            },
            "to_database_format": {"style_map": {"SUPERSCRIPT": "sup"}},
        },
    )
    features.register_editor_plugin(
        "draftail",
        "subscript",
        draftail_features.InlineStyleFeature(
            {
                "type": "SUBSCRIPT",
                "icon": "subscript",
                "description": _("Subscript"),
            }
        ),
    )
    features.register_converter_rule(
        "contentstate",
        "subscript",
        {
            "from_database_format": {
                "sub": InlineStyleElementHandler("SUBSCRIPT"),
            },
            "to_database_format": {"style_map": {"SUBSCRIPT": "sub"}},
        },
    )
    features.register_editor_plugin(
        "draftail",
        "strikethrough",
        draftail_features.InlineStyleFeature(
            {
                "type": "STRIKETHROUGH",
                "icon": "strikethrough",
                "description": _("Strikethrough"),
            }
        ),
    )
    features.register_converter_rule(
        "contentstate",
        "strikethrough",
        {
            "from_database_format": {
                "s": InlineStyleElementHandler("STRIKETHROUGH"),
            },
            "to_database_format": {"style_map": {"STRIKETHROUGH": "s"}},
        },
    )
    features.register_editor_plugin(
        "draftail",
        "code",
        draftail_features.InlineStyleFeature(
            {
                "type": "CODE",
                "icon": "code",
                "description": _("Code"),
            }
        ),
    )
    features.register_converter_rule(
        "contentstate",
        "code",
        {
            "from_database_format": {
                "code": InlineStyleElementHandler("CODE"),
            },
            "to_database_format": {"style_map": {"CODE": "code"}},
        },
    )


class LockedPagesMenuItem(MenuItem):
    def is_shown(self, request):
        return page_permission_policy.user_has_permission(request.user, "unlock")


class WorkflowReportMenuItem(MenuItem):
    def is_shown(self, request):
        return getattr(
            settings, "WAGTAIL_WORKFLOW_ENABLED", True
        ) and page_permission_policy.user_has_any_permission(
            request.user, ["add", "change", "publish"]
        )


class SiteHistoryReportMenuItem(MenuItem):
    def is_shown(self, request):
        return page_permission_policy.explorable_root_instance(request.user) is not None


class AgingPagesReportMenuItem(MenuItem):
    def is_shown(self, request):
        return getattr(
            settings, "WAGTAIL_AGING_PAGES_ENABLED", True
        ) and page_permission_policy.user_has_any_permission(
            request.user, ["add", "change", "publish"]
        )


class PageTypesReportMenuItem(MenuItem):
    def is_shown(self, request):
        return page_permission_policy.user_has_any_permission(
            request.user, ["add", "change", "publish"]
        )


@hooks.register("register_reports_menu_item")
def register_locked_pages_menu_item():
    return LockedPagesMenuItem(
        _("Locked pages"),
        reverse("wagtailadmin_reports:locked_pages"),
        name="locked-pages",
        icon_name="lock",
        order=700,
    )


@hooks.register("register_reports_menu_item")
def register_workflow_report_menu_item():
    return WorkflowReportMenuItem(
        _("Workflows"),
        reverse("wagtailadmin_reports:workflow"),
        name="workflows",
        icon_name="tasks",
        order=800,
    )


@hooks.register("register_reports_menu_item")
def register_workflow_tasks_report_menu_item():
    return WorkflowReportMenuItem(
        _("Workflow tasks"),
        reverse("wagtailadmin_reports:workflow_tasks"),
        name="workflow-tasks",
        icon_name="thumbtack",
        order=900,
    )


@hooks.register("register_reports_menu_item")
def register_site_history_report_menu_item():
    return SiteHistoryReportMenuItem(
        _("Site history"),
        reverse("wagtailadmin_reports:site_history"),
        name="site-history",
        icon_name="history",
        order=1000,
    )


@hooks.register("register_reports_menu_item")
def register_aging_pages_report_menu_item():
    return AgingPagesReportMenuItem(
        _("Aging pages"),
        reverse("wagtailadmin_reports:aging_pages"),
        name="aging-pages",
        icon_name="time",
        order=1100,
    )


@hooks.register("register_reports_menu_item")
def register_page_types_report_menu_item():
    return PageTypesReportMenuItem(
        _("Page types usage"),
        reverse("wagtailadmin_reports:page_types_usage"),
        name="page-types-usage",
        icon_name="doc-empty-inverse",
        order=1200,
    )


@hooks.register("register_admin_menu_item")
def register_reports_menu():
    return SubmenuMenuItem(
        _("Reports"),
        reports_menu,
        name="reports",
        icon_name="site",
        order=9000,
    )


@hooks.register("register_help_menu_item")
def register_whats_new_in_wagtail_version_menu_item():
    version = get_main_version(include_patch=False)
    return DismissibleMenuItem(
        _("What's new in Wagtail %(version)s") % {"version": version},
        wagtail_feature_release_whats_new_link(),
        icon_name="help",
        order=1000,
        attrs={"target": "_blank", "rel": "noreferrer"},
        name=f"whats-new-in-wagtail-{version}",
    )


@hooks.register("register_help_menu_item")
def register_editors_guide_menu_item():
    return DismissibleMenuItem(
        _("Editor Guide"),
        wagtail_feature_release_editor_guide_link(),
        icon_name="help",
        order=1100,
        attrs={"target": "_blank", "rel": "noreferrer"},
        name="editor-guide",
    )


@hooks.register("register_help_menu_item")
def register_keyboard_shortcuts_menu_item():
    """
    Triggers the keyboard shortcuts dialog to open when clicked
    while preventing the default link click action.
    """

    return MenuItem(
        _("Shortcuts"),
        icon_name="keyboard",
        order=1200,
        attrs={
            "role": "button",  # Ensure screen readers announce this as a button
            "data-a11y-dialog-show": "keyboard-shortcuts-dialog",
            "data-action": "w-action#noop:prevent:stop",
            "data-controller": "w-action",
        },
        name="keyboard-shortcuts-trigger",
        url="#",
    )


@hooks.register("register_admin_menu_item")
def register_help_menu():
    return DismissibleSubmenuMenuItem(
        _("Help"),
        help_menu,
        name="help",
        icon_name="help",
        order=11000,
    )


@hooks.register("register_icons")
def register_icons(icons):
    for icon in [
        "arrow-down.svg",
        "arrow-right-full.svg",
        "arrow-left.svg",
        "arrow-right.svg",
        "arrow-up.svg",
        "bars.svg",
        "bin.svg",
        "bold.svg",
        "breadcrumb-expand.svg",
        "calendar.svg",
        "calendar-alt.svg",
        "calendar-check.svg",
        "check.svg",
        "circle-check.svg",
        "circle-plus.svg",
        "circle-xmark.svg",
        "clipboard-list.svg",
        "code.svg",
        "cog.svg",
        "cogs.svg",
        "copy.svg",
        "collapse-down.svg",
        "collapse-up.svg",
        "comment.svg",
        "comment-add.svg",
        "comment-add-reversed.svg",
        "cross.svg",
        "crosshairs.svg",
        "cut.svg",
        "date.svg",
        "decimal.svg",
        "desktop.svg",
        "doc-empty-inverse.svg",
        "doc-empty.svg",
        "doc-full-inverse.svg",
        "doc-full.svg",
        "dots-horizontal.svg",
        "download.svg",
        "draft.svg",
        "edit.svg",
        "expand-right.svg",
        "error.svg",
        "folder-inverse.svg",
        "folder-open-1.svg",
        "folder-open-inverse.svg",
        "folder.svg",
        "form.svg",
        "glasses.svg",
        "globe.svg",
        "grid.svg",
        "grip.svg",
        "group.svg",
        "h1.svg",
        "h2.svg",
        "h3.svg",
        "h4.svg",
        "h5.svg",
        "h6.svg",
        "help.svg",
        "history.svg",
        "home.svg",
        "image.svg",
        "info-circle.svg",
        "italic.svg",
        "key.svg",
        "keyboard.svg",
        "link.svg",
        "link-external.svg",
        "list-ol.svg",
        "list-ul.svg",
        "lock-open.svg",
        "lock.svg",
        "login.svg",
        "logout.svg",
        "mail.svg",
        "media.svg",
        "minus.svg",
        "mobile-alt.svg",
        "no-view.svg",
        "openquote.svg",
        "order-down.svg",
        "order-up.svg",
        "order.svg",
        "password.svg",
        "pick.svg",
        "pilcrow.svg",
        "placeholder.svg",
        "plus-inverse.svg",
        "plus.svg",
        "radio-empty.svg",
        "radio-full.svg",
        "redirect.svg",
        "regex.svg",
        "resubmit.svg",
        "rotate.svg",
        "search.svg",
        "site.svg",
        "sliders.svg",
        "snippet.svg",
        "spinner.svg",
        "strikethrough.svg",
        "success.svg",
        "subscript.svg",
        "superscript.svg",
        "table.svg",
        "tablet-alt.svg",
        "tag.svg",
        "tasks.svg",
        "thumbtack.svg",
        "thumbtack-crossed.svg",
        "tick-inverse.svg",
        "time.svg",
        "title.svg",
        "upload.svg",
        "user.svg",
        "view.svg",
        "wagtail.svg",
        "warning.svg",
    ]:
        icons.append(f"wagtailadmin/icons/{icon}")
    return icons


@hooks.register("construct_homepage_summary_items")
def add_pages_summary_item(request, items):
    items.insert(0, PagesSummaryItem(request))


class PageAdminURLFinder:
    def __init__(self, user):
        self.user = user

    def get_edit_url(self, instance):
        if self.user and not instance.permissions_for_user(self.user).can_edit():
            return None
        else:
            return reverse("wagtailadmin_pages:edit", args=(instance.pk,))


register_admin_url_finder(Page, PageAdminURLFinder)


class CollectionAdminURLFinder(ModelAdminURLFinder):
    permission_policy = collection_permission_policy
    edit_url_name = "wagtailadmin_collections:edit"


register_admin_url_finder(Collection, CollectionAdminURLFinder)


class WorkflowAdminURLFinder(ModelAdminURLFinder):
    permission_policy = workflow_permission_policy
    edit_url_name = "wagtailadmin_workflows:edit"


register_admin_url_finder(Workflow, WorkflowAdminURLFinder)


class WorkflowTaskAdminURLFinder(ModelAdminURLFinder):
    permission_policy = task_permission_policy
    edit_url_name = "wagtailadmin_workflows:edit_task"


register_admin_url_finder(Task, WorkflowTaskAdminURLFinder)


for action_class in [
    DeleteBulkAction,
    MoveBulkAction,
    PublishBulkAction,
    UnpublishBulkAction,
]:
    hooks.register("register_bulk_action", action_class)
