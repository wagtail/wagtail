from __future__ import absolute_import, print_function, unicode_literals

from functools import total_ordering

from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import Page


class LinkChooserRegistry(object):

    @cached_property
    def items(self):
        registered_hooks = hooks.get_hooks('register_link_chooser')
        return sorted(hook() for hook in registered_hooks)

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)


registry = LinkChooserRegistry()


@total_ordering
@python_2_unicode_compatible
class LinkChooser(object):
    id = None
    title = None
    url_name = None
    priority = None

    def __eq__(self, other):
        if not isinstance(other, LinkChooser):
            return NotImplemented
        return self.priority == other.priority

    def __lt__(self, other):
        if not isinstance(other, LinkChooser):
            return NotImplemented
        return self.priority < other.priority

    def __str__(self):
        return 'LinkChooser({})'.format(self.id)

    def __repr__(self):
        return '<{}.{}>'.format(self.__class__.__module__, self.__class__.__name__)

    @classmethod
    def get_db_attributes(cls, tag):
        """
        Given an element from a RichText editor, return a dict of all the
        attributes required to store the element in the database
        representation.

        The opposite of ``expand_db_attributes``.
        """
        raise NotImplementedError()

    @classmethod
    def expand_db_attributes(cls, attrs, for_editor):
        """
        Given a dict of attributes from a link in some RichText stored in the
        database, return a dict of HTML attributes to build an ``<a>`` tag.

        If ``for_editor`` is true, the RichText is being edited, otherwise it
        is being displayed to the user.
        """
        raise NotImplementedError()


class InternalLinkChooser(LinkChooser):
    """
    PageLinkHandler will be invoked whenever we encounter an <a> element in
    HTML content with an attribute of data-linktype="page". The resulting
    element in the database representation will be: <a linktype="page"
    id="42">hello world</a>
    """

    id = 'page'
    title = _('Internal link')
    url_name = 'wagtailadmin_choose_page'
    priority = 100

    @classmethod
    def get_db_attributes(cls, tag):
        """
        Given an <a> tag that we've identified as a page link embed (because it has a
        data-linktype="page" attribute), return a dict of the attributes we should
        have on the resulting <a linktype="page"> element.
        """
        return {'id': tag['data-id']}

    @classmethod
    def expand_db_attributes(cls, attrs, for_editor):
        try:
            page = Page.objects.get(id=attrs['id'])
        except Page.DoesNotExist:
            return {}

        attrs = {'href': page.url}
        if for_editor:
            attrs['data-id'] = page.id
        return attrs


class SimpleLinkChooser(LinkChooser):
    """
    A link type that only has an href.
    """
    @classmethod
    def get_db_attributes(cls, tag):
        return {'href': tag['href']}

    @classmethod
    def expand_db_attributes(cls, attrs, for_editor):
        return {'href': attrs['href']}


class ExternalLinkChooser(SimpleLinkChooser):
    id = 'external'
    title = _('External link')
    url_name = 'wagtailadmin_choose_page_external_link'
    priority = 200


class EmailLinkChooser(SimpleLinkChooser):
    id = 'email'
    title = _('Email link')
    url_name = 'wagtailadmin_choose_page_email_link'
    priority = 300
