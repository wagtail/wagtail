from django import template
from django.shortcuts import reverse
from django.template.defaulttags import token_kwargs
from django.utils.encoding import force_str
from django.utils.safestring import mark_safe

from wagtail import VERSION, __version__
from wagtail.core.models import Page, Site
from wagtail.core.rich_text import RichText, expand_db_html
from wagtail.utils.version import get_main_version

register = template.Library()


@register.simple_tag(takes_context=True)
def pageurl(context, page, fallback=None):
    """
    Outputs a page's URL as relative (/foo/bar/) if it's within the same site as the
    current page, or absolute (http://example.com/foo/bar/) if not.
    If kwargs contains a fallback view name and page is None, the fallback view url will be returned.
    """
    if page is None and fallback:
        return reverse(fallback)

    if not hasattr(page, 'relative_url'):
        raise ValueError("pageurl tag expected a Page object, got %r" % page)

    try:
        site = Site.find_for_request(context['request'])
        current_site = site
    except (KeyError, AttributeError):
        # site not available in the current context; fall back on page.url
        return page.url

    if current_site is None:
        # request.site is set to None; fall back on page.url
        return page.url

    # Pass page.relative_url the request object, which may contain a cached copy of
    # Site.get_site_root_paths()
    # This avoids page.relative_url having to make a database/cache fetch for this list
    # each time it's called.
    return page.relative_url(current_site, request=context.get('request'))


@register.simple_tag(takes_context=True)
def slugurl(context, slug):
    """
    Returns the URL for the page that has the given slug.

    First tries to find a page on the current site. If that fails or a request
    is not available in the context, then returns the URL for the first page
    that matches the slug on any site.
    """

    page = None
    try:
        site = Site.find_for_request(context['request'])
        current_site = site
    except (KeyError, AttributeError):
        # No site object found - allow the fallback below to take place.
        pass
    else:
        if current_site is not None:
            page = Page.objects.in_site(current_site).filter(slug=slug).first()

    # If no page is found, fall back to searching the whole tree.
    if page is None:
        page = Page.objects.filter(slug=slug).first()

    if page:
        # call pageurl() instead of page.relative_url() here so we get the ``accepts_kwarg`` logic
        return pageurl(context, page)


@register.simple_tag
def wagtail_version():
    return __version__


@register.simple_tag
def wagtail_documentation_path():
    major, minor, patch, release, num = VERSION
    if release == 'final':
        return 'https://docs.wagtail.io/en/v%s' % __version__
    else:
        return 'https://docs.wagtail.io/en/latest'


@register.simple_tag
def wagtail_release_notes_path():
    return "%s.html" % get_main_version(VERSION)


@register.filter
def richtext(value):
    if isinstance(value, RichText):
        # passing a RichText value through the |richtext filter should have no effect
        return value
    elif value is None:
        html = ''
    else:
        if isinstance(value, str):
            html = expand_db_html(value)
        else:
            raise TypeError("'richtext' template filter received an invalid value; expected string, got {}.".format(type(value)))

    return mark_safe('<div class="rich-text">' + html + '</div>')


class IncludeBlockNode(template.Node):
    def __init__(self, block_var, extra_context, use_parent_context):
        self.block_var = block_var
        self.extra_context = extra_context
        self.use_parent_context = use_parent_context

    def render(self, context):
        try:
            value = self.block_var.resolve(context)
        except template.VariableDoesNotExist:
            return ''

        if hasattr(value, 'render_as_block'):
            if self.use_parent_context:
                new_context = context.flatten()
            else:
                new_context = {}

            if self.extra_context:
                for var_name, var_value in self.extra_context.items():
                    new_context[var_name] = var_value.resolve(context)

            return value.render_as_block(context=new_context)
        else:
            return force_str(value)


@register.tag
def include_block(parser, token):
    """
    Render the passed item of StreamField content, passing the current template context
    if there's an identifiable way of doing so (i.e. if it has a `render_as_block` method).
    """
    tokens = token.split_contents()

    try:
        tag_name = tokens.pop(0)
        block_var_token = tokens.pop(0)
    except IndexError:
        raise template.TemplateSyntaxError("%r tag requires at least one argument" % tag_name)

    block_var = parser.compile_filter(block_var_token)

    if tokens and tokens[0] == 'with':
        tokens.pop(0)
        extra_context = token_kwargs(tokens, parser)
    else:
        extra_context = None

    use_parent_context = True
    if tokens and tokens[0] == 'only':
        tokens.pop(0)
        use_parent_context = False

    if tokens:
        raise template.TemplateSyntaxError("Unexpected argument to %r tag: %r" % (tag_name, tokens[0]))

    return IncludeBlockNode(block_var, extra_context, use_parent_context)


@register.simple_tag(takes_context=True)
def wagtail_site(context):
    """
        Returns the Site object for the given request
    """
    return Site.find_for_request(request=context.request)
