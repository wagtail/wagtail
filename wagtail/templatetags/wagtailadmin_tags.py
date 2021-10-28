from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

from .wagtailadmin import (
    EscapeScriptNode, _abs, admin_urlquote, allow_unicode_slugs, auto_update_preview, avatar_url,
    base_url_setting, cautious_slugify, component, ellipsistrim, explorer_breadcrumb, fieldtype,
    format_collection, format_content_type, get_comments_enabled, has_unrendered_errors,
    hook_output, i18n_enabled, icon, js_translation_strings, locales, main_nav, main_nav_css,
    main_nav_js, menu_props, menu_search, message_tags, minimum_collection_depth,
    notification_static, page_listing_buttons, page_permissions, page_table_header_label, paginate,
    pagination_querystring, querystring, render_with_errors, resolve_url, search_other,
    sidebar_collapsed, slim_sidebar_enabled, table_header_label, test_collection_is_public,
    test_page_is_public, timesince_last_update, timesince_simple, usage_count_enabled,
    user_display_name, versioned_static, widgettype)


register = template.Library()

register.filter('intcomma', intcomma)
register.simple_tag(takes_context=True)(menu_search)
register.inclusion_tag('wagtailadmin/shared/main_nav.html', takes_context=True)(main_nav)
register.inclusion_tag('wagtailadmin/shared/breadcrumb.html', takes_context=True)(explorer_breadcrumb)
register.inclusion_tag('wagtailadmin/shared/search_other.html', takes_context=True)(search_other)
register.simple_tag(main_nav_js)
register.simple_tag(main_nav_css)
register.filter("ellipsistrim")(ellipsistrim)
register.filter(fieldtype)
register.filter(widgettype)
register.simple_tag(takes_context=True)(page_permissions)
register.simple_tag(takes_context=True)(test_collection_is_public)
register.simple_tag(takes_context=True)(test_page_is_public)
register.simple_tag(hook_output)
register.simple_tag(usage_count_enabled)
register.simple_tag(base_url_setting)
register.simple_tag(allow_unicode_slugs)
register.simple_tag(auto_update_preview)
register.tag(EscapeScriptNode.TAG_NAME, EscapeScriptNode.handle)
register.filter(render_with_errors)
register.filter(has_unrendered_errors)
register.filter(is_safe=True)(cautious_slugify)
register.simple_tag(takes_context=True)(querystring)
register.simple_tag(takes_context=True)(page_table_header_label)
register.simple_tag(takes_context=True)(table_header_label)
register.simple_tag(takes_context=True)(pagination_querystring)
register.inclusion_tag("wagtailadmin/pages/listing/_pagination.html", takes_context=True)(paginate)
register.inclusion_tag("wagtailadmin/pages/listing/_buttons.html", takes_context=True)(page_listing_buttons)
register.simple_tag(message_tags)
register.filter('abs')(_abs)
register.filter(admin_urlquote)
register.simple_tag(avatar_url)
register.simple_tag(js_translation_strings)
register.simple_tag(notification_static)
register.simple_tag(versioned_static)
register.inclusion_tag("wagtailadmin/shared/icon.html", takes_context=False)(icon)
register.filter(timesince_simple)
register.simple_tag(timesince_last_update)
register.simple_tag(format_collection)
register.simple_tag(minimum_collection_depth)
register.filter(user_display_name)
register.filter(format_content_type)
register.simple_tag(i18n_enabled)
register.simple_tag(locales)
register.simple_tag(slim_sidebar_enabled)
register.simple_tag(takes_context=True)(sidebar_collapsed)
register.simple_tag(takes_context=True)(menu_props)
register.simple_tag(get_comments_enabled)
register.simple_tag(resolve_url)
register.simple_tag(takes_context=True)(component)
