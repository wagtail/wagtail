from django import template

register = template.Library()


@register.inclusion_tag("wagtailadmin/shared/wagtail_icon.html", takes_context=False)
def wagtail_icon(name=None, classname='', title=None):
    """
    Usage: {% wagtail_icon name="cogs" classname="icon--red" title="Settings" %}

    First load the tags with {% load wagtailui_tags %}
    """
    return {
        'name': name,
        'classname': classname,
        'title': title,
    }
