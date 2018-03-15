from django import template

register = template.Library()


@register.inclusion_tag("wagtailadmin/shared/icon.html",
                        takes_context=False)
def wagtail_icon(classnames, title='', show_label=True, decorative=True):
    """
    Usage: {% wagtail_icon classnames title show_label decorative %}

    The css classes necessary to show the icon are provided as a first argument.
    The 'title' argument is optional, but recommended. When 'show_label' is True, the title is shown next to the icon.
    When an icon is marked decorative, it is hidden for screenreaders (a11y). If 'decorative' is False, the title is
    visible for screenreaders, regardless whether 'show_label' is True or not.

    """
    return {'classnames': classnames, 'title': title, 'show_label': show_label, 'decorative': decorative}
