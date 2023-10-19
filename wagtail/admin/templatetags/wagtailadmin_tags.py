import json
from datetime import datetime
from urllib.parse import urljoin
from warnings import warn

from django import template
from django.conf import settings
from django.contrib.admin.utils import quote
from django.contrib.humanize.templatetags.humanize import intcomma, naturaltime
from django.contrib.messages.constants import DEFAULT_TAGS as MESSAGE_TAGS
from django.http.request import HttpHeaders
from django.middleware.csrf import get_token
from django.shortcuts import resolve_url as resolve_url_func
from django.template import Context
from django.template.base import token_kwargs
from django.template.defaultfilters import stringfilter
from django.templatetags.static import static
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.html import avoid_wrapping, conditional_escape, json_script
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.timesince import timesince
from django.utils.translation import gettext_lazy as _

from wagtail import hooks
from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.localization import get_js_translation_strings
from wagtail.admin.menu import admin_menu
from wagtail.admin.search import admin_search_areas
from wagtail.admin.staticfiles import versioned_static as versioned_static_func
from wagtail.admin.ui import sidebar
from wagtail.admin.utils import (
    get_admin_base_url,
    get_latest_str,
    get_user_display_name,
    get_valid_next_url_from_request,
)
from wagtail.admin.views.bulk_action.registry import bulk_action_registry
from wagtail.admin.widgets import Button, ButtonWithDropdown, PageListingButton
from wagtail.coreutils import (
    accepts_kwarg,
    camelcase_to_underscore,
    escape_script,
    get_content_type_label,
    get_locales_display_names,
)
from wagtail.coreutils import cautious_slugify as _cautious_slugify
from wagtail.models import (
    CollectionViewRestriction,
    Locale,
    Page,
    PageViewRestriction,
    UserPagePermissionsProxy,
)
from wagtail.permission_policies.pages import PagePermissionPolicy
from wagtail.telepath import JSContext
from wagtail.users.utils import get_gravatar_url
from wagtail.utils.deprecation import RemovedInWagtail60Warning

register = template.Library()

register.filter("intcomma", intcomma)
register.filter("naturaltime", naturaltime)


@register.inclusion_tag("wagtailadmin/shared/breadcrumbs.html")
def breadcrumbs(items, is_expanded=False, classname=None):
    return {"items": items, "is_expanded": is_expanded, "classname": classname}


@register.inclusion_tag("wagtailadmin/shared/page_breadcrumbs.html", takes_context=True)
def page_breadcrumbs(
    context,
    page,
    url_name,
    url_root_name=None,
    include_self=True,
    is_expanded=False,
    page_perms=None,
    querystring_value=None,
    trailing_breadcrumb_title=None,
    classname=None,
):
    user = context["request"].user

    # find the closest common ancestor of the pages that this user has direct explore permission
    # (i.e. add/edit/publish/lock) over; this will be the root of the breadcrumb
    cca = PagePermissionPolicy().explorable_root_instance(user)
    if not cca:
        return {"items": Page.objects.none()}

    return {
        "items": page.get_ancestors(inclusive=include_self)
        .descendant_of(cca, inclusive=True)
        .specific(),
        "current_page": page,
        "is_expanded": is_expanded,
        "page_perms": page_perms,
        "querystring_value": querystring_value or "",
        "trailing_breadcrumb_title": trailing_breadcrumb_title,  # Only used in collapsible breadcrumb templates
        "url_name": url_name,
        "url_root_name": url_root_name,
        "classname": classname,
    }


@register.inclusion_tag("wagtailadmin/shared/search_other.html", takes_context=True)
def search_other(context, current=None):
    request = context["request"]

    return {
        "options_html": admin_search_areas.render_html(request, current),
        "request": request,
    }


@register.filter("ellipsistrim")
def ellipsistrim(value, max_length):
    if len(value) > max_length:
        truncd_val = value[:max_length]
        if not len(value) == (max_length + 1) and value[max_length + 1] != " ":
            truncd_val = truncd_val[: truncd_val.rfind(" ")]
        return truncd_val + "…"
    return value


@register.filter
def fieldtype(bound_field):
    try:
        return camelcase_to_underscore(bound_field.field.__class__.__name__)
    except AttributeError:
        try:
            return camelcase_to_underscore(bound_field.__class__.__name__)
        except AttributeError:
            return ""


@register.filter
def widgettype(bound_field):
    try:
        return camelcase_to_underscore(bound_field.field.widget.__class__.__name__)
    except AttributeError:
        try:
            return camelcase_to_underscore(bound_field.widget.__class__.__name__)
        except AttributeError:
            return ""


def _get_user_page_permissions(context):
    # RemovedInWagtail60Warning: Remove this function

    # Create a UserPagePermissionsProxy object to represent the user's global permissions, and
    # cache it in the context for the duration of the page request, if one does not exist already
    if "user_page_permissions" not in context:
        context["user_page_permissions"] = UserPagePermissionsProxy(
            context["request"].user
        )
    return context["user_page_permissions"]


@register.simple_tag(takes_context=True)
def page_permissions(context, page):
    """
    Usage: {% page_permissions page as page_perms %}
    Sets the variable 'page_perms' to a PagePermissionTester object that can be queried to find out
    what actions the current logged-in user can perform on the given page.
    """
    # RemovedInWagtail60Warning: Keep the UserPagePermissionsProxy object in the context
    # for backwards compatibility during the deprecation period, even though we don't use it
    _get_user_page_permissions(context)
    return page.permissions_for_user(context["request"].user)


@register.simple_tag
def is_page(obj):
    """
    Usage: {% is_page obj as is_page %}
    Sets the variable 'is_page' to True if the given object is a Page instance,
    False otherwise. Useful in shared templates that accept both Page and
    non-Page objects (e.g. snippets with the optional features enabled).
    """
    return isinstance(obj, Page)


@register.simple_tag(takes_context=True)
def admin_edit_url(context, obj, user=None):
    """
    Usage: {% admin_edit_url obj user %}
    Returns the URL of the edit view for the given object and user using the
    registered AdminURLFinder for the object. The AdminURLFinder instance is
    cached in the context for the duration of the page request.
    The user argument is optional and defaults to request.user if request is
    available in the context.
    """
    if not user and "request" in context:
        user = context["request"].user
    if "admin_url_finder" not in context:
        context["admin_url_finder"] = AdminURLFinder(user)
    return context["admin_url_finder"].get_edit_url(obj)


@register.simple_tag
def admin_url_name(obj, action):
    """
    Usage: {% admin_url_name obj action %}
    Returns the URL name of the given action for the given object, e.g.
    'wagtailadmin_pages:edit' for a Page object and 'edit' action.
    Works with pages and snippets only.
    """
    if isinstance(obj, Page):
        return f"wagtailadmin_pages:{action}"
    return obj.snippet_viewset.get_url_name(action)


@register.simple_tag
def latest_str(obj):
    """
    Usage: {% latest_str obj %}
    Returns the latest string representation of an object, making use of the
    latest revision where available to reflect draft changes.
    """
    return get_latest_str(obj)


@register.simple_tag
def classnames(*classes):
    """
    Usage <div class="{% classnames "w-base" classname active|yesno:"w-base--active," any_other_var %}"></div>
    Returns any args as a space-separated joined string for using in HTML class names.
    """
    return " ".join([classname.strip() for classname in classes if classname])


@register.simple_tag(takes_context=True)
def test_collection_is_public(context, collection):
    """
    Usage: {% test_collection_is_public collection as is_public %}
    Sets 'is_public' to True iff there are no collection view restrictions in place
    on this collection.
    Caches the list of collection view restrictions in the context, to avoid repeated
    DB queries on repeated calls.
    """
    if "all_collection_view_restrictions" not in context:
        context[
            "all_collection_view_restrictions"
        ] = CollectionViewRestriction.objects.select_related("collection").values_list(
            "collection__name", flat=True
        )

    is_private = collection.name in context["all_collection_view_restrictions"]

    return not is_private


@register.simple_tag(takes_context=True)
def test_page_is_public(context, page):
    """
    Usage: {% test_page_is_public page as is_public %}
    Sets 'is_public' to True iff there are no page view restrictions in place on
    this page.
    Caches the list of page view restrictions on the request, to avoid repeated
    DB queries on repeated calls.
    """
    if not hasattr(context["request"], "all_page_view_restriction_paths"):
        context[
            "request"
        ].all_page_view_restriction_paths = PageViewRestriction.objects.select_related(
            "page"
        ).values_list(
            "page__path", flat=True
        )

    is_private = any(
        page.path.startswith(restricted_path)
        for restricted_path in context["request"].all_page_view_restriction_paths
    )

    return not is_private


@register.simple_tag
def hook_output(hook_name):
    """
    Example: {% hook_output 'insert_global_admin_css' %}
    Whenever we have a hook whose functions take no parameters and return a string, this tag can be used
    to output the concatenation of all of those return values onto the page.
    Note that the output is not escaped - it is the hook function's responsibility to escape unsafe content.
    """
    snippets = [fn() for fn in hooks.get_hooks(hook_name)]

    if hook_name == "insert_editor_css" and snippets:
        warn(
            "The `insert_editor_css` hook is deprecated - use `insert_global_admin_css` instead.",
            category=RemovedInWagtail60Warning,
        )

    return mark_safe("".join(snippets))


@register.simple_tag
def base_url_setting(default=None):
    return get_admin_base_url() or default


@register.simple_tag
def allow_unicode_slugs():
    return getattr(settings, "WAGTAIL_ALLOW_UNICODE_SLUGS", True)


class EscapeScriptNode(template.Node):
    TAG_NAME = "escapescript"

    def __init__(self, nodelist):
        super().__init__()
        warn(
            "The `escapescript` template tag is deprecated - use `template` elements instead.",
            category=RemovedInWagtail60Warning,
        )
        self.nodelist = nodelist

    def render(self, context):
        out = self.nodelist.render(context)
        return escape_script(out)

    @classmethod
    def handle(cls, parser, token):
        nodelist = parser.parse(("end" + EscapeScriptNode.TAG_NAME,))
        parser.delete_first_token()
        return cls(nodelist)


register.tag(EscapeScriptNode.TAG_NAME, EscapeScriptNode.handle)


# Helpers for Widget.render_with_errors, our extension to the Django widget API that allows widgets to
# take on the responsibility of rendering their own error messages
@register.filter
def render_with_errors(bound_field):
    """
    Usage: {{ field|render_with_errors }} as opposed to {{ field }}.
    If the field (a BoundField instance) has errors on it, and the associated widget implements
    a render_with_errors method, call that; otherwise, call the regular widget rendering mechanism.
    """
    widget = bound_field.field.widget
    if bound_field.errors and hasattr(widget, "render_with_errors"):
        return widget.render_with_errors(
            bound_field.html_name,
            bound_field.value(),
            attrs={"id": bound_field.auto_id},
            errors=bound_field.errors,
        )
    else:
        attrs = {}
        # If the widget doesn't have an aria-describedby attribute,
        # and the field has help text, and the field has an id,
        # add an aria-describedby attribute pointing to the help text.
        # In this case, the corresponding help text element's id is set in the
        # wagtailadmin/shared/field.html template.

        # In Django 5.0 and up, this is done automatically, but we want to keep
        # this code because we use a different convention for the help text id
        # (we use -helptext suffix instead of Django's _helptext).
        if (
            not bound_field.field.widget.attrs.get("aria-describedby")
            and bound_field.field.help_text
            and bound_field.id_for_label
        ):
            attrs["aria-describedby"] = f"{bound_field.id_for_label}-helptext"
        return bound_field.as_widget(attrs=attrs)


@register.filter
def has_unrendered_errors(bound_field):
    """
    Return true if this field has errors that were not accounted for by render_with_errors, because
    the widget does not support the render_with_errors method
    """
    return bound_field.errors and not hasattr(
        bound_field.field.widget, "render_with_errors"
    )


@register.filter(is_safe=True)
@stringfilter
def cautious_slugify(value):
    return _cautious_slugify(value)


@register.simple_tag(takes_context=True)
def querystring(context, **kwargs):
    """
    Print out the current querystring. Any keyword arguments to this template
    tag will be added to the querystring before it is printed out.

        <a href="/page/{% querystring key='value' %}">

    Will result in something like:

        <a href="/page/?foo=bar&key=value">
    """
    request = context["request"]
    querydict = request.GET.copy()
    # Can't do querydict.update(kwargs), because QueryDict.update() appends to
    # the list of values, instead of replacing the values.
    for key, value in kwargs.items():
        if value is None:
            # Remove the key if the value is None
            querydict.pop(key, None)
        else:
            # Set the key otherwise
            querydict[key] = str(value)

    return "?" + querydict.urlencode()


@register.simple_tag(takes_context=True)
def pagination_querystring(context, page_number, page_key="p"):
    """
    Print out a querystring with an updated page number:

        {% if page.has_next_page %}
            <a href="{% pagination_link page.next_page_number %}">Next page</a>
        {% endif %}
    """
    return querystring(context, **{page_key: page_number})


@register.inclusion_tag(
    "wagtailadmin/pages/listing/_pagination.html", takes_context=True
)
def paginate(context, page, base_url="", page_key="p", classname=""):
    """
    Print pagination previous/next links, and the page count. Take the
    following arguments:

    page
        The current page of results. This should be a Django pagination `Page`
        instance

    base_url
        The base URL of the next/previous page, with no querystring.
        This is optional, and defaults to the current page by just printing the
        querystring for the next/previous page.

    page_key
        The name of the page variable in the query string. Defaults to 'p'.

    classname
        Extra classes to add to the next/previous links.
    """
    request = context["request"]
    return {
        "base_url": base_url,
        "classname": classname,
        "request": request,
        "page": page,
        "page_key": page_key,
        "paginator": page.paginator,
    }


@register.inclusion_tag("wagtailadmin/shared/buttons.html", takes_context=True)
def page_listing_buttons(context, page, user):
    next_url = context["request"].path
    button_hooks = hooks.get_hooks("register_page_listing_buttons")

    buttons = []
    for hook in button_hooks:
        if accepts_kwarg(hook, "user"):
            buttons.extend(hook(page=page, next_url=next_url, user=user))
        else:
            # old-style hook that accepts page_perms instead of user
            warn(
                "`register_page_listing_buttons` hook functions should accept a `user` argument instead of `page_perms` -"
                f" {hook.__module__}.{hook.__name__} needs to be updated",
                category=RemovedInWagtail60Warning,
            )

            page_perms = page.permissions_for_user(user)
            buttons.extend(hook(page, page_perms, next_url))

    buttons.sort()

    page_perms = page.permissions_for_user(user)
    for hook in hooks.get_hooks("construct_page_listing_buttons"):
        if accepts_kwarg(hook, "user"):
            hook(buttons, page=page, user=user, context=context)
        else:
            # old-style hook that accepts page_perms instead of user
            warn(
                "`construct_page_listing_buttons` hook functions should accept a `user` argument instead of `page_perms` -"
                f" {hook.__module__}.{hook.__name__} needs to be updated",
                category=RemovedInWagtail60Warning,
            )

            page_perms = page.permissions_for_user(user)
            hook(buttons, page, page_perms, context)

    return {"page": page, "buttons": buttons}


@register.inclusion_tag(
    "wagtailadmin/pages/listing/_page_header_buttons.html", takes_context=True
)
def page_header_buttons(context, page, user, view_name):
    next_url = context["request"].path
    page_perms = page.permissions_for_user(user)
    button_hooks = hooks.get_hooks("register_page_header_buttons")

    buttons = []
    for hook in button_hooks:
        if accepts_kwarg(hook, "user"):
            buttons.extend(
                hook(page=page, user=user, next_url=next_url, view_name=view_name)
            )
        else:
            # old-style hook that accepts page_perms instead of user
            warn(
                "`register_page_header_buttons` hook functions should accept a `user` argument instead of `page_perms` -"
                f" {hook.__module__}.{hook.__name__} needs to be updated",
                category=RemovedInWagtail60Warning,
            )

            page_perms = page.permissions_for_user(user)
            buttons.extend(hook(page, page_perms, next_url))

    buttons = [b for b in buttons if b.show]
    buttons.sort()
    return {
        "buttons": buttons,
    }


@register.inclusion_tag("wagtailadmin/shared/buttons.html", takes_context=True)
def bulk_action_choices(context, app_label, model_name):
    bulk_actions_list = list(
        bulk_action_registry.get_bulk_actions_for_model(app_label, model_name)
    )
    bulk_actions_list.sort(key=lambda x: x.action_priority)

    bulk_action_more_list = bulk_actions_list[4:]
    bulk_actions_list = bulk_actions_list[:4]

    next_url = get_valid_next_url_from_request(context["request"])
    if not next_url:
        next_url = context["request"].path

    bulk_action_buttons = [
        PageListingButton(
            action.display_name,
            reverse(
                "wagtail_bulk_action", args=[app_label, model_name, action.action_type]
            )
            + "?"
            + urlencode({"next": next_url}),
            attrs={"aria-label": action.aria_label, "data-bulk-action-button": ""},
            priority=action.action_priority,
            classname=" ".join(action.classes | {"bulk-action-btn"}),
        )
        for action in bulk_actions_list
    ]

    if bulk_action_more_list:
        more_button = ButtonWithDropdown(
            label=_("More"),
            attrs={"title": _("More bulk actions")},
            classname="button button-secondary button-small",
            buttons=[
                Button(
                    label=action.display_name,
                    url=reverse(
                        "wagtail_bulk_action",
                        args=[app_label, model_name, action.action_type],
                    )
                    + "?"
                    + urlencode({"next": next_url}),
                    attrs={
                        "aria-label": action.aria_label,
                        "data-bulk-action-button": "",
                    },
                    priority=action.action_priority,
                )
                for action in bulk_action_more_list
            ],
        )
        bulk_action_buttons.append(more_button)

    return {"buttons": bulk_action_buttons}


@register.inclusion_tag("wagtailadmin/shared/avatar.html")
def avatar(user=None, classname=None, size=None, tooltip=None):
    """
    Displays a user avatar using the avatar template
    Usage:
    {% load wagtailadmin_tags %}
    ...
    {% avatar user=request.user size='small' tooltip='JaneDoe' %}
    :param user: the user to get avatar information from (User)
    :param size: default None (None|'small'|'large'|'square')
    :param tooltip: Optional tooltip to display under the avatar (string)
    :return: Rendered template snippet
    """
    return {"user": user, "classname": classname, "size": size, "tooltip": tooltip}


@register.simple_tag
def message_level_tag(message):
    """
    Return the tag for this message's level as defined in
    django.contrib.messages.constants.DEFAULT_TAGS, ignoring the project-level
    MESSAGE_TAGS setting (which end-users might customise).
    """
    return MESSAGE_TAGS.get(message.level)


@register.simple_tag
def message_tags(message):
    level_tag = message_level_tag(message)
    if message.extra_tags and level_tag:
        return message.extra_tags + " " + level_tag
    elif message.extra_tags:
        return message.extra_tags
    elif level_tag:
        return level_tag
    else:
        return ""


@register.filter("abs")
def _abs(val):
    return abs(val)


@register.filter
def admin_urlquote(value):
    return quote(value)


@register.simple_tag
def avatar_url(user, size=50, gravatar_only=False):
    """
    A template tag that receives a user and size and return
    the appropriate avatar url for that user.
    Example usage: {% avatar_url request.user 50 %}
    """

    if (
        not gravatar_only
        and hasattr(user, "wagtail_userprofile")
        and user.wagtail_userprofile.avatar
    ):
        return user.wagtail_userprofile.avatar.url

    if hasattr(user, "email"):
        gravatar_url = get_gravatar_url(user.email, size=size)
        if gravatar_url is not None:
            return gravatar_url

    return versioned_static_func("wagtailadmin/images/default-user-avatar.png")


@register.simple_tag(takes_context=True)
def admin_theme_classname(context):
    """
    Retrieves the theme name for the current user.
    """
    user = context["request"].user
    theme_name = (
        user.wagtail_userprofile.theme
        if hasattr(user, "wagtail_userprofile")
        else "system"
    )
    return f"w-theme-{theme_name}"


@register.simple_tag
def js_translation_strings():
    return mark_safe(json.dumps(get_js_translation_strings()))


@register.simple_tag
def notification_static(path):
    """
    Variant of the {% static %}` tag for use in notification emails - tries to form
    a full URL using WAGTAILADMIN_BASE_URL if the static URL isn't already a full URL.
    """
    return urljoin(base_url_setting(), static(path))


@register.simple_tag
def versioned_static(path):
    """
    Wrapper for Django's static file finder to append a cache-busting query parameter
    that updates on each Wagtail version
    """
    return versioned_static_func(path)


@register.inclusion_tag("wagtailadmin/shared/icon.html", takes_context=False)
def icon(name=None, classname=None, title=None, wrapped=False, class_name=None):
    """
    Abstracts away the actual icon implementation.

    Usage:
        {% load wagtailadmin_tags %}
        ...
        {% icon name="cogs" classname="icon--red" title="Settings" %}

    :param name: the icon name/id, required (string)
    :param classname: defaults to 'icon' if not provided (string)
    :param title: accessible label intended for screen readers (string)
    :return: Rendered template snippet (string)
    """
    if not name:
        raise ValueError("You must supply an icon name")

    if class_name:
        warn(
            (
                "Icon template tag `class_name` has been renamed to `classname`, please adopt the new usage instead. "
                f'Replace `{{% icon ... class_name="{class_name}" %}}` with `{{% icon ... classname="{class_name}" %}}`'
            ),
            category=RemovedInWagtail60Warning,
        )

    deprecated_icons = [
        "angle-double-left",
        "angle-double-right",
        "arrow-down-big",
        "arrow-up-big",
        "arrows-up-down",
        "chain-broken",
        "dots-vertical",
        "ellipsis-v",
        "horizontalrule",
        "repeat",
        "reset",
        "undo",
        "wagtail-inverse",
    ]

    if name in deprecated_icons:
        warn(
            (f"Icon `{name}` is deprecated and will be removed in a future release."),
            category=RemovedInWagtail60Warning,
        )

    renamed_icons = {
        "chevron-down": "arrow-down",
        "download-alt": "download",
        "duplicate": "copy",
        "tick": "check",
        "uni52": "folder-inverse",
    }

    if name in renamed_icons:
        old_name = name
        name = renamed_icons[name]
        warn(
            (
                f"Icon `{old_name}` has been renamed to `{name}`, please adopt the new usage instead. "
                f'Replace `{{% icon name="{old_name}" ... %}}` with `{{% icon name="{name}" ... %}}`'
            ),
            category=RemovedInWagtail60Warning,
        )

    return {
        "name": name,
        # supporting class_name for backwards compatibility
        "classname": classname or class_name or "icon",
        "title": title,
        "wrapped": wrapped,
    }


@register.inclusion_tag("wagtailadmin/shared/status_tag.html")
def status(
    label=None,
    classname=None,
    url=None,
    title=None,
    hidden_label=None,
    attrs=None,
):
    """
    Generates a status-tag css with <span></span> or <a><a/> implementation.

    Usage:

        {% status label="live" url="/test/" title="title" hidden_label="current status:" classname="w-status--primary" %}

    :param label: the status test, (string)
    :param classname: defaults to 'status-tag' if not provided (string)
    :param url: the status url(to specify the use of anchor tag instead of default span), (string)
    :param title: accessible label intended for screen readers (string)
    :param hidden_label : the to specify the additional visually hidden span text, (string)
    :param attrs: any additional HTML attributes (as a string) to append to the root element
    :return: Rendered template snippet (string)

    """
    return {
        "label": label,
        "attrs": attrs,
        "classname": classname,
        "hidden_label": hidden_label,
        "title": title,
        "url": url,
    }


@register.filter()
def timesince_simple(d):
    """
    Returns a simplified timesince:
    19 hours, 48 minutes ago -> 19 hours ago
    1 week, 1 day ago -> 1 week ago
    0 minutes ago -> just now
    """
    # Note: Duplicate code in timesince_last_update()
    time_period = timesince(d).split(",")[0]
    if time_period == avoid_wrapping(_("0 minutes")):
        return _("just now")
    return _("%(time_period)s ago") % {"time_period": time_period}


@register.simple_tag
def timesince_last_update(
    last_update, show_time_prefix=False, user_display_name="", use_shorthand=True
):
    """
    Returns:
         - the time of update if last_update is today, if show_time_prefix=True, the output will be prefixed with "at "
         - time since last update otherwise. Defaults to the simplified timesince,
           but can return the full string if needed
    """
    # translation usage below is intentionally verbose to be easier to work with translations

    if last_update.date() == datetime.today().date():
        if timezone.is_aware(last_update):
            time_str = timezone.localtime(last_update).strftime("%H:%M")
        else:
            time_str = last_update.strftime("%H:%M")

        if show_time_prefix:
            if user_display_name:
                return _("at %(time)s by %(user_display_name)s") % {
                    "time": time_str,
                    "user_display_name": user_display_name,
                }
            else:
                return _("at %(time)s") % {"time": time_str}
        else:
            if user_display_name:
                return _("%(time)s by %(user_display_name)s") % {
                    "time": time_str,
                    "user_display_name": user_display_name,
                }
            else:
                return time_str
    else:
        if use_shorthand:
            # Note: Duplicate code in timesince_simple()
            time_period = timesince(last_update).split(",")[0]
            if time_period == avoid_wrapping(_("0 minutes")):
                if user_display_name:
                    return _("just now by %(user_display_name)s") % {
                        "user_display_name": user_display_name
                    }
                else:
                    return _("just now")
        else:
            time_period = timesince(last_update)

        if user_display_name:
            return _("%(time_period)s ago by %(user_display_name)s") % {
                "time_period": time_period,
                "user_display_name": user_display_name,
            }
        else:
            return _("%(time_period)s ago") % {"time_period": time_period}


@register.filter
def user_display_name(user):
    return get_user_display_name(user)


@register.filter
def format_content_type(content_type):
    return get_content_type_label(content_type)


@register.simple_tag
def i18n_enabled():
    return getattr(settings, "WAGTAIL_I18N_ENABLED", False)


@register.simple_tag
def locales():
    return json.dumps(
        [
            {
                "code": locale.language_code,
                "display_name": force_str(locale.get_display_name()),
            }
            for locale in Locale.objects.all()
        ]
    )


@register.simple_tag
def locale_label_from_id(locale_id):
    """
    Returns the Locale display name given its id.
    """
    return get_locales_display_names().get(locale_id)


@register.simple_tag(takes_context=True)
def sidebar_collapsed(context):
    request = context.get("request")
    collapsed = request.COOKIES.get("wagtail_sidebar_collapsed", "0")
    if collapsed == "0":
        return False
    return True


@register.simple_tag(takes_context=True)
def sidebar_props(context):
    request = context["request"]
    search_areas = admin_search_areas.search_items_for_request(request)
    if search_areas:
        search_area = search_areas[0]
    else:
        search_area = None

    account_menu = [
        sidebar.LinkMenuItem(
            "account", _("Account"), reverse("wagtailadmin_account"), icon_name="user"
        ),
        sidebar.ActionMenuItem(
            "logout", _("Log out"), reverse("wagtailadmin_logout"), icon_name="logout"
        ),
    ]

    modules = [
        sidebar.WagtailBrandingModule(),
        sidebar.SearchModule(search_area) if search_area else None,
        sidebar.MainMenuModule(
            admin_menu.render_component(request), account_menu, request.user
        ),
    ]
    modules = [module for module in modules if module is not None]

    return json_script(
        {
            "modules": JSContext().pack(modules),
        },
        element_id="wagtail-sidebar-props",
    )


@register.simple_tag
def get_comments_enabled():
    return getattr(settings, "WAGTAILADMIN_COMMENTS_ENABLED", True)


@register.simple_tag(takes_context=True)
def wagtail_config(context):
    request = context["request"]
    config = {
        "CSRF_TOKEN": get_token(request),
        "CSRF_HEADER_NAME": HttpHeaders.parse_header_name(
            getattr(settings, "CSRF_HEADER_NAME")
        ),
        "ADMIN_URLS": {
            "DISMISSIBLES": reverse("wagtailadmin_dismissibles"),
        },
    }

    default_settings = {
        "WAGTAIL_AUTO_UPDATE_PREVIEW": True,
        "WAGTAIL_AUTO_UPDATE_PREVIEW_INTERVAL": 500,
    }
    config.update(
        {
            option: getattr(settings, option, default)
            for option, default in default_settings.items()
        }
    )

    return config


@register.simple_tag
def resolve_url(url):
    # Used by wagtailadmin/shared/pagination_nav.html - given an input that may be a URL route
    # name, or a direct URL path, return it as a direct URL path. On failure (or being passed
    # an empty / None value), return empty string
    if not url:
        return ""

    try:
        return resolve_url_func(url)
    except NoReverseMatch:
        return ""


class ComponentNode(template.Node):
    def __init__(
        self,
        component,
        extra_context=None,
        isolated_context=False,
        fallback_render_method=None,
        target_var=None,
    ):
        self.component = component
        self.extra_context = extra_context or {}
        self.isolated_context = isolated_context
        self.fallback_render_method = fallback_render_method
        self.target_var = target_var

    def render(self, context: Context) -> str:
        # Render a component by calling its render_html method, passing request and context from the
        # calling template.
        # If fallback_render_method is true, objects without a render_html method will have render()
        # called instead (with no arguments) - this is to provide deprecation path for things that have
        # been newly upgraded to use the component pattern.

        component = self.component.resolve(context)

        if self.fallback_render_method:
            fallback_render_method = self.fallback_render_method.resolve(context)
        else:
            fallback_render_method = False

        values = {
            name: var.resolve(context) for name, var in self.extra_context.items()
        }

        if hasattr(component, "render_html"):
            if self.isolated_context:
                html = component.render_html(context.new(values))
            else:
                with context.push(**values):
                    html = component.render_html(context)
        elif fallback_render_method and hasattr(component, "render"):
            html = component.render()
        else:
            raise ValueError(f"Cannot render {component!r} as a component")

        if self.target_var:
            context[self.target_var] = html
            return ""
        else:
            if context.autoescape:
                html = conditional_escape(html)
            return html


@register.tag(name="component")
def component(parser, token):
    bits = token.split_contents()[1:]
    if not bits:
        raise template.TemplateSyntaxError(
            "'component' tag requires at least one argument, the component object"
        )

    component = parser.compile_filter(bits.pop(0))

    # the only valid keyword argument immediately following the component
    # is fallback_render_method
    flags = token_kwargs(bits, parser)
    fallback_render_method = flags.pop("fallback_render_method", None)
    if flags:
        raise template.TemplateSyntaxError(
            "'component' tag only accepts 'fallback_render_method' as a keyword argument"
        )

    extra_context = {}
    isolated_context = False
    target_var = None

    while bits:
        bit = bits.pop(0)
        if bit == "with":
            extra_context = token_kwargs(bits, parser)
        elif bit == "only":
            isolated_context = True
        elif bit == "as":
            try:
                target_var = bits.pop(0)
            except IndexError:
                raise template.TemplateSyntaxError(
                    "'component' tag with 'as' must be followed by a variable name"
                )
        else:
            raise template.TemplateSyntaxError(
                "'component' tag received an unknown argument: %r" % bit
            )

    return ComponentNode(
        component,
        extra_context=extra_context,
        isolated_context=isolated_context,
        fallback_render_method=fallback_render_method,
        target_var=target_var,
    )


class FragmentNode(template.Node):
    def __init__(self, nodelist, target_var):
        self.nodelist = nodelist
        self.target_var = target_var

    def render(self, context):
        fragment = self.nodelist.render(context) if self.nodelist else ""
        context[self.target_var] = fragment
        return ""


@register.tag(name="fragment")
def fragment(parser, token):
    """
    Store a template fragment as a variable.

    Usage:
        {% fragment as header_title %}
            {% blocktrans trimmed %}Welcome to the {{ site_name }} Wagtail CMS{% endblocktrans %}
        {% endfragment %}

    Copy-paste of slippers’ fragment template tag.
    See https://github.com/mixxorz/slippers/blob/254c720e6bb02eb46ae07d104863fce41d4d3164/slippers/templatetags/slippers.py#L173.
    """
    error_message = "The syntax for fragment is {% fragment as variable_name %}"

    try:
        tag_name, _, target_var = token.split_contents()
        nodelist = parser.parse(("endfragment",))
        parser.delete_first_token()
    except ValueError:
        if settings.DEBUG:
            raise template.TemplateSyntaxError(error_message)
        return ""

    return FragmentNode(nodelist, target_var)


class BlockInclusionNode(template.Node):
    """
    Create template-driven tags like Django’s inclusion_tag / InclusionNode, but for block-level tags.

    Usage:
        {% my_tag status="test" label="Alert" %}
            Proceed with caution.
        {% endmy_tag %}

    Within `my_tag`’s template, the template fragment will be accessible as the {{ children }} context variable.

    The output can also be stored as a variable in the parent context:

        {% my_tag status="test" label="Alert" as my_variable %}
            Proceed with caution.
        {% endmy_tag %}

    Inspired by slippers’ Component Node.
    See https://github.com/mixxorz/slippers/blob/254c720e6bb02eb46ae07d104863fce41d4d3164/slippers/templatetags/slippers.py#L47.
    """

    def __init__(self, nodelist, template, extra_context, target_var=None):
        self.nodelist = nodelist
        self.template = template
        self.extra_context = extra_context
        self.target_var = target_var

    def get_context_data(self, parent_context):
        return parent_context

    def render(self, context):
        children = self.nodelist.render(context) if self.nodelist else ""

        values = {
            # Resolve the tag’s parameters within the current context.
            key: value.resolve(context)
            for key, value in self.extra_context.items()
        }

        t = context.template.engine.get_template(self.template)
        # Add the `children` variable in the rendered template’s context.
        context_data = self.get_context_data({**values, "children": children})
        output = t.render(Context(context_data, autoescape=context.autoescape))

        if self.target_var:
            context[self.target_var] = output
            return ""

        return output

    @classmethod
    def handle(cls, parser, token):
        tag_name, *remaining_bits = token.split_contents()

        nodelist = parser.parse((f"end{tag_name}",))
        parser.delete_first_token()

        extra_context = token_kwargs(remaining_bits, parser)

        # Allow component fragment to be assigned to a variable
        target_var = None
        if len(remaining_bits) >= 2 and remaining_bits[-2] == "as":
            target_var = remaining_bits[-1]

        return cls(nodelist, cls.template, extra_context, target_var)


class DialogNode(BlockInclusionNode):
    template = "wagtailadmin/shared/dialog/dialog.html"

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)

        if "title" not in context:
            raise TypeError("You must supply a title")
        if "id" not in context:
            raise TypeError("You must supply an id")

        # Used for determining which icon the message will use
        message_icon_name = {
            "info": "info-circle",
            "warning": "warning",
            "critical": "warning",
            "success": "circle-check",
        }

        message_status = context.get("message_status")

        # If there is a message status then determine which icon to use.
        if message_status:
            context["message_icon_name"] = message_icon_name[message_status]

        return context


register.tag("dialog", DialogNode.handle)


class HelpBlockNode(BlockInclusionNode):
    template = "wagtailadmin/shared/help_block.html"


register.tag("help_block", HelpBlockNode.handle)


class DropdownNode(BlockInclusionNode):
    template = "wagtailadmin/shared/dropdown/dropdown.html"


register.tag("dropdown", DropdownNode.handle)


class PanelNode(BlockInclusionNode):
    template = "wagtailadmin/shared/panel.html"


register.tag("panel", PanelNode.handle)


class FieldNode(BlockInclusionNode):
    template = "wagtailadmin/shared/field.html"


register.tag("field", FieldNode.handle)


class FieldRowNode(BlockInclusionNode):
    template = "wagtailadmin/shared/forms/field_row.html"


register.tag("field_row", FieldRowNode.handle)


# Button used to open dialogs
@register.inclusion_tag("wagtailadmin/shared/dialog/dialog_toggle.html")
def dialog_toggle(dialog_id, classname="", text=None):
    if not dialog_id:
        raise ValueError("You must supply the dialog ID")

    return {
        "classname": classname,
        "text": text,
        # dialog_id must match the ID of the dialog you are toggling
        "dialog_id": dialog_id,
    }


@register.simple_tag()
def workflow_status_with_date(workflow_state):
    translation_context = {
        "finished_at": naturaltime(workflow_state.current_task_state.finished_at),
        "started_at": naturaltime(workflow_state.current_task_state.started_at),
        "task_name": workflow_state.current_task_state.task.name,
        "status_display": workflow_state.get_status_display,
    }

    if workflow_state.status == "needs_changes":
        return _("Changes requested %(finished_at)s") % translation_context

    if workflow_state.status == "in_progress":
        return _("Sent to %(task_name)s %(started_at)s") % translation_context

    return _("%(status_display)s %(task_name)s %(started_at)s") % translation_context


@register.inclusion_tag("wagtailadmin/shared/human_readable_date.html")
def human_readable_date(date, description=None, placement="top"):
    return {
        "date": date,
        "description": description,
        "placement": placement,
    }
