from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def wagtailuserbar(context, cssfile=""):
    try:
        items = ''.join(["<li>%s</li>" % item for item in context['request'].userbar])
        context.hasuserbar = True
        return """<link rel="stylesheet" href="%s" /><ul id="wagtail-userbar">%s</ul>""" % (cssfile, items)
    except AttributeError:
        return ''
