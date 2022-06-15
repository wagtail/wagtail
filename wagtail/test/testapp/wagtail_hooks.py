from django.http import HttpResponse
from django.utils.safestring import mark_safe

import wagtail.admin.rich_text.editors.draftail.features as draftail_features
from wagtail import hooks
from wagtail.admin.action_menu import ActionMenuItem
from wagtail.admin.menu import MenuItem
from wagtail.admin.rich_text.converters.html_to_contentstate import BlockElementHandler
from wagtail.admin.search import SearchArea
from wagtail.admin.site_summary import SummaryItem
from wagtail.admin.ui.components import Component
from wagtail.admin.views.account import BaseSettingsPanel
from wagtail.admin.widgets import Button

from .forms import FavouriteColourForm


# Register one hook using decorators...
@hooks.register("insert_editor_css")
def editor_css():
    return """<link rel="stylesheet" href="/path/to/my/custom.css">"""


# And the other using old-style function calls
def editor_js():
    return """<script src="/path/to/my/custom.js"></script>"""


hooks.register("insert_editor_js", editor_js)


def block_googlebot(page, request, serve_args, serve_kwargs):
    if request.META.get("HTTP_USER_AGENT") == "GoogleBot":
        return HttpResponse("<h1>bad googlebot no cookie</h1>")


hooks.register("before_serve_page", block_googlebot)


class KittensMenuItem(MenuItem):
    def is_shown(self, request):
        return not request.GET.get("hide-kittens", False)


@hooks.register("register_admin_menu_item")
def register_kittens_menu_item():
    return KittensMenuItem(
        "Kittens!",
        "http://www.tomroyal.com/teaandkittens/",
        classnames="kitten--test",
        icon_name="kitten",
        attrs={"data-is-custom": "true"},
        order=10000,
    )


# Admin Other Searches hook
class MyCustomSearchArea(SearchArea):
    def is_shown(self, request):
        return not request.GET.get("hide-option", False)

    def is_active(self, request, current=None):
        return request.GET.get("active-option", False)


@hooks.register("register_admin_search_area")
def register_custom_search_area():
    return MyCustomSearchArea(
        "My Search",
        "/customsearch/",
        classnames="search--custom-class",
        icon_name="custom",
        attrs={"is-custom": "true"},
        order=10000,
    )


@hooks.register("construct_explorer_page_queryset")
def polite_pages_only(parent_page, pages, request):
    # if the URL parameter polite_pages_only is set,
    # only return pages with a slug that starts with 'hello'
    if request.GET.get("polite_pages_only"):
        pages = pages.filter(slug__startswith="hello")

    return pages


@hooks.register("construct_explorer_page_queryset")
def hide_hidden_pages(parent_page, pages, request):
    # Pages with 'hidden' in their title are hidden. Magic!
    return pages.exclude(title__icontains="hidden")


# register 'quotation' as a rich text feature supported by a Draftail feature
@hooks.register("register_rich_text_features")
def register_quotation_feature(features):
    features.register_editor_plugin(
        "draftail",
        "quotation",
        draftail_features.EntityFeature(
            {},
            js=["testapp/js/draftail-quotation.js"],
            css={"all": ["testapp/css/draftail-quotation.css"]},
        ),
    )


# register 'intro' as a rich text feature which converts an `intro-paragraph` contentstate block
# to a <p class="intro"> tag in db HTML and vice versa
@hooks.register("register_rich_text_features")
def register_intro_rule(features):
    features.register_converter_rule(
        "contentstate",
        "intro",
        {
            "from_database_format": {
                'p[class="intro"]': BlockElementHandler("intro-paragraph"),
            },
            "to_database_format": {
                "block_map": {
                    "intro-paragraph": {"element": "p", "props": {"class": "intro"}}
                },
            },
        },
    )


class PanicMenuItem(ActionMenuItem):
    label = "Panic!"
    name = "action-panic"

    class Media:
        js = ["testapp/js/siren.js"]


@hooks.register("register_page_action_menu_item")
def register_panic_menu_item():
    return PanicMenuItem()


@hooks.register("register_page_action_menu_item")
def register_none_menu_item():
    return None


class RelaxMenuItem(ActionMenuItem):
    label = "Relax."
    name = "action-relax"


@hooks.register("construct_page_action_menu")
def register_relax_menu_item(menu_items, request, context):
    # Run a validation check on all core menu items to ensure name attribute is present
    names = [(item.__class__.__name__, item.name or "") for item in menu_items]
    name_exists_on_all_items = [len(name[1]) > 1 for name in names]
    if not all(name_exists_on_all_items):
        raise AttributeError(
            "all core sub-classes of ActionMenuItems must have a name attribute", names
        )

    menu_items.append(RelaxMenuItem())


@hooks.register("construct_page_listing_buttons")
def register_page_listing_button_item(
    buttons, page, page_perms, is_parent=False, context=None
):
    item = Button(
        label="Dummy Button",
        url="/dummy-button",
        priority=10,
    )
    buttons.append(item)


@hooks.register("construct_snippet_listing_buttons")
def register_snippet_listing_button_item(buttons, snippet, user, context=None):
    item = Button(
        label="Dummy Button",
        url="/dummy-button",
        priority=10,
    )
    buttons.append(item)


@hooks.register("register_account_settings_panel")
class FavouriteColourPanel(BaseSettingsPanel):
    name = "favourite_colour"
    title = "Favourite colour"
    order = 500
    form_class = FavouriteColourForm
    form_object = "user"


class ClippyPanel(Component):
    order = 50

    def render_html(self, parent_context):
        return mark_safe(
            "<p>It looks like you're making a website. Would you like some help?</p>"
        )

    class Media:
        js = ["testapp/js/clippy.js"]


@hooks.register("construct_homepage_panels")
def add_clippy_panel(request, panels):
    panels.append(ClippyPanel())


class BrokenLinksSummaryItem(SummaryItem):
    order = 100

    def render_html(self, parent_context):
        return mark_safe("<p>0 broken links</p>")

    class Media:
        css = {"all": ["testapp/css/broken-links.css"]}


@hooks.register("construct_homepage_summary_items")
def add_broken_links_summary_item(request, items):
    items.append(BrokenLinksSummaryItem(request))
