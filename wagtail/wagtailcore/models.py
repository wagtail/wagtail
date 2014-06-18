from StringIO import StringIO
from urlparse import urlparse
import warnings

from modelcluster.models import ClusterableModel

from django.db import models, connection, transaction
from django.db.models import get_model, Q
from django.http import Http404
from django.core.cache import cache
from django.core.handlers.wsgi import WSGIRequest
from django.core.handlers.base import BaseHandler
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group
from django.conf import settings
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from treebeard.mp_tree import MP_Node

from wagtail.wagtailcore.utils import camelcase_to_underscore
from wagtail.wagtailcore.query import PageQuerySet

from wagtail.wagtailsearch import Indexed, get_search_backend


class SiteManager(models.Manager):
    def get_by_natural_key(self, hostname):
        return self.get(hostname=hostname)


class Site(models.Model):
    hostname = models.CharField(max_length=255, unique=True, db_index=True)
    port = models.IntegerField(default=80, help_text=_("Set this to something other than 80 if you need a specific port number to appear in URLs (e.g. development on port 8000). Does not affect request handling (so port forwarding still works)."))
    root_page = models.ForeignKey('Page', related_name='sites_rooted_here')
    is_default_site = models.BooleanField(default=False, help_text=_("If true, this site will handle requests for all other hostnames that do not have a site entry of their own"))

    def natural_key(self):
        return (self.hostname,)

    def __unicode__(self):
        return self.hostname + ("" if self.port == 80 else (":%d" % self.port)) + (" [default]" if self.is_default_site else "")

    @staticmethod
    def find_for_request(request):
        """Find the site object responsible for responding to this HTTP request object"""
        try:
            hostname = request.META['HTTP_HOST'].split(':')[0]
            # find a Site matching this specific hostname
            return Site.objects.get(hostname=hostname)
        except (Site.DoesNotExist, KeyError):
            # If no matching site exists, or request does not specify an HTTP_HOST (which
            # will often be the case for the Django test client), look for a catch-all Site.
            # If that fails, let the Site.DoesNotExist propagate back to the caller
            return Site.objects.get(is_default_site=True)

    @property
    def root_url(self):
        if self.port == 80:
            return 'http://%s' % self.hostname
        elif self.port == 443:
            return 'https://%s' % self.hostname
        else:
            return 'http://%s:%d' % (self.hostname, self.port)

    # clear the wagtail_site_root_paths cache whenever Site records are updated
    def save(self, *args, **kwargs):
        result = super(Site, self).save(*args, **kwargs)
        cache.delete('wagtail_site_root_paths')
        return result

    @staticmethod
    def get_site_root_paths():
        """
        Return a list of (root_path, root_url) tuples, most specific path first -
        used to translate url_paths into actual URLs with hostnames
        """
        result = cache.get('wagtail_site_root_paths')

        if result is None:
            result = [
                (site.id, site.root_page.url_path, site.root_url)
                for site in Site.objects.select_related('root_page').order_by('-root_page__url_path')
            ]
            cache.set('wagtail_site_root_paths', result, 3600)

        return result


PAGE_MODEL_CLASSES = []
_PAGE_CONTENT_TYPES = []


def get_page_types():
    global _PAGE_CONTENT_TYPES
    if len(_PAGE_CONTENT_TYPES) != len(PAGE_MODEL_CLASSES):
        _PAGE_CONTENT_TYPES = [
            ContentType.objects.get_for_model(cls) for cls in PAGE_MODEL_CLASSES
        ]
    return _PAGE_CONTENT_TYPES


def get_leaf_page_content_type_ids():
    warnings.warn("""
        get_leaf_page_content_type_ids is deprecated, as it treats pages without an explicit subpage_types
        setting as 'leaf' pages. Code that calls get_leaf_page_content_type_ids must be rewritten to avoid
        this incorrect assumption.
    """, DeprecationWarning)
    return [
        content_type.id
        for content_type in get_page_types()
        if not getattr(content_type.model_class(), 'subpage_types', None)
    ]

def get_navigable_page_content_type_ids():
    warnings.warn("""
        get_navigable_page_content_type_ids is deprecated, as it treats pages without an explicit subpage_types
        setting as 'leaf' pages. Code that calls get_navigable_page_content_type_ids must be rewritten to avoid
        this incorrect assumption.
    """, DeprecationWarning)
    return [
        content_type.id
        for content_type in get_page_types()
        if getattr(content_type.model_class(), 'subpage_types', None)
    ]


class PageManager(models.Manager):
    def get_query_set(self):
        return PageQuerySet(self.model).order_by('path')

    def live(self):
        return self.get_query_set().live()

    def not_live(self):
        return self.get_query_set().not_live()

    def page(self, other):
        return self.get_query_set().page(other)

    def not_page(self, other):
        return self.get_query_set().not_page(other)

    def descendant_of(self, other, inclusive=False):
        return self.get_query_set().descendant_of(other, inclusive)

    def not_descendant_of(self, other, inclusive=False):
        return self.get_query_set().not_descendant_of(other, inclusive)

    def child_of(self, other):
        return self.get_query_set().child_of(other)

    def not_child_of(self, other):
        return self.get_query_set().not_child_of(other)

    def ancestor_of(self, other, inclusive=False):
        return self.get_query_set().ancestor_of(other, inclusive)

    def not_ancestor_of(self, other, inclusive=False):
        return self.get_query_set().not_ancestor_of(other, inclusive)

    def parent_of(self, other):
        return self.get_query_set().parent_of(other)

    def not_parent_of(self, other):
        return self.get_query_set().not_parent_of(other)

    def sibling_of(self, other, inclusive=False):
        return self.get_query_set().sibling_of(other, inclusive)

    def not_sibling_of(self, other, inclusive=False):
        return self.get_query_set().not_sibling_of(other, inclusive)

    def type(self, model):
        return self.get_query_set().type(model)

    def not_type(self, model):
        return self.get_query_set().not_type(model)


class PageBase(models.base.ModelBase):
    """Metaclass for Page"""
    def __init__(cls, name, bases, dct):
        super(PageBase, cls).__init__(name, bases, dct)

        if cls._deferred:
            # this is an internal class built for Django's deferred-attribute mechanism;
            # don't proceed with all this page type registration stuff
            return

        # Add page manager
        PageManager().contribute_to_class(cls, 'objects')

        if 'template' not in dct:
            # Define a default template path derived from the app name and model name
            cls.template = "%s/%s.html" % (cls._meta.app_label, camelcase_to_underscore(name))

        if 'ajax_template' not in dct:
            cls.ajax_template = None

        cls._clean_subpage_types = None  # to be filled in on first call to cls.clean_subpage_types

        if not dct.get('is_abstract'):
            # subclasses are only abstract if the subclass itself defines itself so
            cls.is_abstract = False

        if not cls.is_abstract:
            # register this type in the list of page content types
            PAGE_MODEL_CLASSES.append(cls)


class Page(MP_Node, ClusterableModel, Indexed):
    __metaclass__ = PageBase

    title = models.CharField(max_length=255, help_text=_("The page title as you'd like it to be seen by the public"))
    slug = models.SlugField(help_text=_("The name of the page as it will appear in URLs e.g http://domain.com/blog/[my-slug]/"))
    # TODO: enforce uniqueness on slug field per parent (will have to be done at the Django
    # level rather than db, since there is no explicit parent relation in the db)
    content_type = models.ForeignKey('contenttypes.ContentType', related_name='pages')
    live = models.BooleanField(default=True, editable=False)
    has_unpublished_changes = models.BooleanField(default=False, editable=False)
    url_path = models.CharField(max_length=255, blank=True, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, editable=False, related_name='owned_pages')

    seo_title = models.CharField(verbose_name=_("Page title"), max_length=255, blank=True, help_text=_("Optional. 'Search Engine Friendly' title. This will appear at the top of the browser window."))
    show_in_menus = models.BooleanField(default=False, help_text=_("Whether a link to this page will appear in automatically generated menus"))
    search_description = models.TextField(blank=True)

    indexed_fields = {
        'title': {
            'type': 'string',
            'analyzer': 'edgengram_analyzer',
            'boost': 100,
        },
        'live': {
            'type': 'boolean',
            'index': 'not_analyzed',
        },
        'path': {
            'type': 'string',
            'index': 'not_analyzed',
        },
    }

    def __init__(self, *args, **kwargs):
        super(Page, self).__init__(*args, **kwargs)
        if not self.id and not self.content_type_id:
            # this model is being newly created rather than retrieved from the db;
            # set content type to correctly represent the model class that this was
            # created as
            self.content_type = ContentType.objects.get_for_model(self)

    def __unicode__(self):
        return self.title

    is_abstract = True  # don't offer Page in the list of page types a superuser can create

    def set_url_path(self, parent):
        """
        Populate the url_path field based on this page's slug and the specified parent page.
        (We pass a parent in here, rather than retrieving it via get_parent, so that we can give
        new unsaved pages a meaningful URL when previewing them; at that point the page has not
        been assigned a position in the tree, as far as treebeard is concerned.
        """
        if parent:
            self.url_path = parent.url_path + self.slug + '/'
        else:
            # a page without a parent is the tree root, which always has a url_path of '/'
            self.url_path = '/'

        return self.url_path

    @transaction.atomic  # ensure that changes are only committed when we have updated all descendant URL paths, to preserve consistency
    def save(self, *args, **kwargs):
        update_descendant_url_paths = False

        if self.id is None:
            # we are creating a record. If we're doing things properly, this should happen
            # through a treebeard method like add_child, in which case the 'path' field
            # has been set and so we can safely call get_parent
            self.set_url_path(self.get_parent())
        else:
            # see if the slug has changed from the record in the db, in which case we need to
            # update url_path of self and all descendants
            old_record = Page.objects.get(id=self.id)
            if old_record.slug != self.slug:
                self.set_url_path(self.get_parent())
                update_descendant_url_paths = True
                old_url_path = old_record.url_path
                new_url_path = self.url_path

        result = super(Page, self).save(*args, **kwargs)

        if update_descendant_url_paths:
            self._update_descendant_url_paths(old_url_path, new_url_path)

        # Check if this is a root page of any sites and clear the 'wagtail_site_root_paths' key if so
        if Site.objects.filter(root_page=self).exists():
            cache.delete('wagtail_site_root_paths')

        return result

    def _update_descendant_url_paths(self, old_url_path, new_url_path):
        cursor = connection.cursor()
        if connection.vendor == 'sqlite':
            update_statement = """
                UPDATE wagtailcore_page
                SET url_path = %s || substr(url_path, %s)
                WHERE path LIKE %s AND id <> %s
            """
        elif connection.vendor == 'mysql':
            update_statement = """
                UPDATE wagtailcore_page
                SET url_path= CONCAT(%s, substring(url_path, %s))
                WHERE path LIKE %s AND id <> %s
            """
        else:
            update_statement = """
                UPDATE wagtailcore_page
                SET url_path = %s || substring(url_path from %s)
                WHERE path LIKE %s AND id <> %s
            """
        cursor.execute(update_statement, 
            [new_url_path, len(old_url_path) + 1, self.path + '%', self.id])

    @property
    def specific(self):
        """
            Return this page in its most specific subclassed form.
        """
        # the ContentType.objects manager keeps a cache, so this should potentially
        # avoid a database lookup over doing self.content_type. I think.
        content_type = ContentType.objects.get_for_id(self.content_type_id)
        if isinstance(self, content_type.model_class()):
            # self is already the an instance of the most specific class
            return self
        else:
            return content_type.get_object_for_this_type(id=self.id)

    @property
    def specific_class(self):
        """
            return the class that this page would be if instantiated in its
            most specific form
        """
        content_type = ContentType.objects.get_for_id(self.content_type_id)
        return content_type.model_class()

    def route(self, request, path_components):
        if path_components:
            # request is for a child of this page
            child_slug = path_components[0]
            remaining_components = path_components[1:]

            try:
                subpage = self.get_children().get(slug=child_slug)
            except Page.DoesNotExist:
                raise Http404

            return subpage.specific.route(request, remaining_components)

        else:
            # request is for this very page
            if self.live:
                return self.serve(request)
            else:
                raise Http404

    def save_revision(self, user=None, submitted_for_moderation=False):
        self.revisions.create(content_json=self.to_json(), user=user, submitted_for_moderation=submitted_for_moderation)

    def get_latest_revision(self):
        try:
            revision = self.revisions.order_by('-created_at')[0]
        except IndexError:
            return False

        return revision

    def get_latest_revision_as_page(self):
        try:
            revision = self.revisions.order_by('-created_at')[0]
        except IndexError:
            return self.specific

        return revision.as_page_object()

    def get_context(self, request, *args, **kwargs):
        return {
            'self': self,
            'request': request,
        }

    def get_template(self, request, *args, **kwargs):
        if request.is_ajax():
            return self.ajax_template or self.template
        else:
            return self.template

    def serve(self, request, *args, **kwargs):
        return TemplateResponse(
            request, 
            self.get_template(request, *args, **kwargs), 
            self.get_context(request, *args, **kwargs)
        )

    def is_navigable(self):
        """
        Return true if it's meaningful to browse subpages of this page -
        i.e. it currently has subpages,
        or it's at the top level (this rule necessary for empty out-of-the-box sites to have working navigation)
        """
        return (not self.is_leaf()) or self.depth == 2

    def get_other_siblings(self):
        # get sibling pages excluding self
        return self.get_siblings().exclude(id=self.id)

    @property
    def full_url(self):
        """Return the full URL (including protocol / domain) to this page, or None if it is not routable"""
        for (id, root_path, root_url) in Site.get_site_root_paths():
            if self.url_path.startswith(root_path):
                return root_url + self.url_path[len(root_path) - 1:]

    @property
    def url(self):
        """
        Return the 'most appropriate' URL for referring to this page from the pages we serve,
        within the Wagtail backend and actual website templates;
        this is the local URL (starting with '/') if we're only running a single site
        (i.e. we know that whatever the current page is being served from, this link will be on the
        same domain), and the full URL (with domain) if not.
        Return None if the page is not routable.
        """
        root_paths = Site.get_site_root_paths()
        for (id, root_path, root_url) in Site.get_site_root_paths():
            if self.url_path.startswith(root_path):
                return ('' if len(root_paths) == 1 else root_url) + self.url_path[len(root_path) - 1:]

    def relative_url(self, current_site):
        """
        Return the 'most appropriate' URL for this page taking into account the site we're currently on;
        a local URL if the site matches, or a fully qualified one otherwise.
        Return None if the page is not routable.
        """
        for (id, root_path, root_url) in Site.get_site_root_paths():
            if self.url_path.startswith(root_path):
                return ('' if current_site.id == id else root_url) + self.url_path[len(root_path) - 1:]

    @classmethod
    def search(cls, query_string, show_unpublished=False, search_title_only=False, extra_filters={}, prefetch_related=[], path=None):
        # Filters
        filters = extra_filters.copy()
        if not show_unpublished:
            filters['live'] = True

        # Path
        if path:
            filters['path__startswith'] = path

        # Fields
        fields = None
        if search_title_only:
            fields = ['title']

        # Search
        s = get_search_backend()
        return s.search(query_string, model=cls, fields=fields, filters=filters, prefetch_related=prefetch_related)

    @classmethod
    def clean_subpage_types(cls):
        """
            Returns the list of subpage types, with strings converted to class objects
            where required
        """
        if cls._clean_subpage_types is None:
            subpage_types = getattr(cls, 'subpage_types', None)
            if subpage_types is None:
                # if subpage_types is not specified on the Page class, allow all page types as subpages
                res = get_page_types()
            else:
                res = []
                for page_type in cls.subpage_types:
                    if isinstance(page_type, basestring):
                        try:
                            app_label, model_name = page_type.split(".")
                        except ValueError:
                            # If we can't split, assume a model in current app
                            app_label = cls._meta.app_label
                            model_name = page_type

                        model = get_model(app_label, model_name)
                        if model:
                            res.append(ContentType.objects.get_for_model(model))
                        else:
                            raise NameError(_("name '{0}' (used in subpage_types list) is not defined.").format(page_type))

                    else:
                        # assume it's already a model class
                        res.append(ContentType.objects.get_for_model(page_type))

            cls._clean_subpage_types = res

        return cls._clean_subpage_types

    @classmethod
    def allowed_parent_page_types(cls):
        """
            Returns the list of page types that this page type can be a subpage of
        """
        return [ct for ct in get_page_types() if cls in ct.model_class().clean_subpage_types()]

    @classmethod
    def allowed_parent_pages(cls):
        """
            Returns the list of pages that this page type can be a subpage of
        """
        return Page.objects.filter(content_type__in=cls.allowed_parent_page_types())

    @classmethod
    def get_verbose_name(cls):
        # This is similar to doing cls._meta.verbose_name.title()
        # except this doesn't convert any characters to lowercase
        return ' '.join([word[0].upper() + word[1:] for word in cls._meta.verbose_name.split()])

    @property
    def status_string(self):
        if not self.live:
            return "draft"
        else:
            if self.has_unpublished_changes:
                return "live + draft"
            else:
                return "live"

    def has_unpublished_subtree(self):
        """
        An awkwardly-defined flag used in determining whether unprivileged editors have
        permission to delete this article. Returns true if and only if this page is non-live,
        and it has no live children.
        """
        return (not self.live) and (not self.get_descendants().filter(live=True).exists())

    @transaction.atomic  # only commit when all descendants are properly updated
    def move(self, target, pos=None):
        """
        Extension to the treebeard 'move' method to ensure that url_path is updated too.
        """
        old_url_path = Page.objects.get(id=self.id).url_path
        super(Page, self).move(target, pos=pos)
        # treebeard's move method doesn't actually update the in-memory instance, so we need to work
        # with a freshly loaded one now
        new_self = Page.objects.get(id=self.id)
        new_url_path = new_self.set_url_path(new_self.get_parent())
        new_self.save()
        new_self._update_descendant_url_paths(old_url_path, new_url_path)

    def permissions_for_user(self, user):
        """
        Return a PagePermissionsTester object defining what actions the user can perform on this page
        """
        user_perms = UserPagePermissionsProxy(user)
        return user_perms.for_page(self)

    def dummy_request(self):
        """
        Construct a HttpRequest object that is, as far as possible, representative of ones that would
        receive this page as a response. Used for previewing / moderation and any other place where we
        want to display a view of this page in the admin interface without going through the regular
        page routing logic.
        """
        url = self.full_url
        if url:
            url_info = urlparse(url)
            hostname = url_info.hostname
            path = url_info.path
            port = url_info.port or 80
        else:
            # Cannot determine a URL to this page - cobble one together based on
            # whatever we find in ALLOWED_HOSTS
            try:
                hostname = settings.ALLOWED_HOSTS[0]
            except IndexError:
                hostname = 'localhost'
            path = '/'
            port = 80

        request = WSGIRequest({
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': path,
            'SERVER_NAME': hostname,
            'SERVER_PORT': port,
            'wsgi.input': StringIO(),
        })

        # Apply middleware to the request - see http://www.mellowmorning.com/2011/04/18/mock-django-request-for-testing/
        handler = BaseHandler()
        handler.load_middleware()
        for middleware_method in handler._request_middleware:
            if middleware_method(request):
                raise Exception("Couldn't create request mock object - "
                                "request middleware returned a response")
        return request

    def get_page_modes(self):
        """
        Return a list of (internal_name, display_name) tuples for the modes in which
        this page can be displayed for preview/moderation purposes. Ordinarily a page
        will only have one display mode, but subclasses of Page can override this -
        for example, a page containing a form might have a default view of the form,
        and a post-submission 'thankyou' page
        """
        return [('', 'Default')]

    def show_as_mode(self, mode_name):
        """
        Given an internal name from the get_page_modes() list, return an HTTP response
        indicative of the page being viewed in that mode. By default this passes a
        dummy request into the serve() mechanism, ensuring that it matches the behaviour
        on the front-end; subclasses that define additional page modes will need to
        implement alternative logic to serve up the appropriate view here.
        """
        return self.serve(self.dummy_request())

    def get_static_site_paths(self):
        """
        This is a generator of URL paths to feed into a static site generator
        Override this if you would like to create static versions of subpages
        """
        # Yield paths for this page
        yield '/'

        # Yield paths for child pages
        for child in self.get_children().live():
            for path in child.specific.get_static_site_paths():
                yield '/' + child.slug + path

    def get_ancestors(self, inclusive=False):
        return Page.objects.ancestor_of(self, inclusive)

    def get_descendants(self, inclusive=False):
        return Page.objects.descendant_of(self, inclusive)

    def get_siblings(self, inclusive=True):
        return Page.objects.sibling_of(self, inclusive)


def get_navigation_menu_items():
    # Get all pages that appear in the navigation menu: ones which have children,
    # or are at the top-level (this rule required so that an empty site out-of-the-box has a working menu)
    pages = Page.objects.filter(Q(depth=2)|Q(numchild__gt=0)).order_by('path')

    # Turn this into a tree structure:
    #     tree_node = (page, children)
    #     where 'children' is a list of tree_nodes.
    # Algorithm:
    # Maintain a list that tells us, for each depth level, the last page we saw at that depth level.
    # Since our page list is ordered by path, we know that whenever we see a page
    # at depth d, its parent must be the last page we saw at depth (d-1), and so we can
    # find it in that list.

    depth_list = [(None, [])]  # a dummy node for depth=0, since one doesn't exist in the DB

    for page in pages:
        # create a node for this page
        node = (page, [])
        # retrieve the parent from depth_list
        parent_page, parent_childlist = depth_list[page.depth - 1]
        # insert this new node in the parent's child list
        parent_childlist.append(node)

        # add the new node to depth_list
        try:
            depth_list[page.depth] = node
        except IndexError:
            # an exception here means that this node is one level deeper than any we've seen so far
            depth_list.append(node)

    # in Wagtail, the convention is to have one root node in the db (depth=1); the menu proper
    # begins with the children of that node (depth=2).
    try:
        root, root_children = depth_list[1]
        return root_children
    except IndexError:
        # what, we don't even have a root node? Fine, just return an empty list...
        return []


class Orderable(models.Model):
    sort_order = models.IntegerField(null=True, blank=True, editable=False)
    sort_order_field = 'sort_order'

    class Meta:
        abstract = True
        ordering = ['sort_order']


class SubmittedRevisionsManager(models.Manager):
    def get_query_set(self):
        return super(SubmittedRevisionsManager, self).get_query_set().filter(submitted_for_moderation=True)


class PageRevision(models.Model):
    page = models.ForeignKey('Page', related_name='revisions')
    submitted_for_moderation = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    content_json = models.TextField()

    objects = models.Manager()
    submitted_revisions = SubmittedRevisionsManager()

    def save(self, *args, **kwargs):
        super(PageRevision, self).save(*args, **kwargs)
        if self.submitted_for_moderation:
            # ensure that all other revisions of this page have the 'submitted for moderation' flag unset
            self.page.revisions.exclude(id=self.id).update(submitted_for_moderation=False)

    def as_page_object(self):
        obj = self.page.specific_class.from_json(self.content_json)

        # Override the possibly-outdated tree parameter fields from this revision object
        # with up-to-date values
        obj.path = self.page.path
        obj.depth = self.page.depth
        obj.numchild = self.page.numchild

        # Populate url_path based on the revision's current slug and the parent page as determined
        # by path
        obj.set_url_path(self.page.get_parent())

        # also copy over other properties which are meaningful for the page as a whole, not a
        # specific revision of it
        obj.live = self.page.live
        obj.has_unpublished_changes = self.page.has_unpublished_changes
        obj.owner = self.page.owner

        return obj

    def publish(self):
        page = self.as_page_object()
        page.live = True
        page.save()
        self.submitted_for_moderation = False
        page.revisions.update(submitted_for_moderation=False)

PAGE_PERMISSION_TYPE_CHOICES = [
    ('add', 'Add'),
    ('edit', 'Edit'),
    ('publish', 'Publish'),
]


class GroupPagePermission(models.Model):
    group = models.ForeignKey(Group, related_name='page_permissions')
    page = models.ForeignKey('Page', related_name='group_permissions')
    permission_type = models.CharField(max_length=20, choices=PAGE_PERMISSION_TYPE_CHOICES)


class UserPagePermissionsProxy(object):
    """Helper object that encapsulates all the page permission rules that this user has
    across the page hierarchy."""
    def __init__(self, user):
        self.user = user

        if user.is_active and not user.is_superuser:
            self.permissions = GroupPagePermission.objects.filter(group__user=self.user).select_related('page')

    def revisions_for_moderation(self):
        """Return a queryset of page revisions awaiting moderation that this user has publish permission on"""

        # Deal with the trivial cases first...
        if not self.user.is_active:
            return PageRevision.objects.none()
        if self.user.is_superuser:
            return PageRevision.submitted_revisions.all()

        # get the list of pages for which they have direct publish permission (i.e. they can publish any page within this subtree)
        publishable_pages = [perm.page for perm in self.permissions if perm.permission_type == 'publish']
        if not publishable_pages:
            return PageRevision.objects.none()

        # compile a filter expression to apply to the PageRevision.submitted_revisions manager:
        # return only those pages whose paths start with one of the publishable_pages paths
        only_my_sections = Q(page__path__startswith=publishable_pages[0].path)
        for page in publishable_pages[1:]:
            only_my_sections = only_my_sections | Q(page__path__startswith=page.path)

        # return the filtered queryset
        return PageRevision.submitted_revisions.filter(only_my_sections)

    def for_page(self, page):
        """Return a PagePermissionTester object that can be used to query whether this user has
        permission to perform specific tasks on the given page"""
        return PagePermissionTester(self, page)

    def editable_pages(self):
        """Return a queryset of the pages that this user has permission to edit"""
        # Deal with the trivial cases first...
        if not self.user.is_active:
            return Page.objects.none()
        if self.user.is_superuser:
            return Page.objects.all()

        # Translate each of the user's permission rules into a Q-expression
        q_expressions = []
        for perm in self.permissions:
            if perm.permission_type == 'add':
                # user has edit permission on any subpage of perm.page
                # (including perm.page itself) that is owned by them
                q_expressions.append(
                    Q(path__startswith=perm.page.path, owner=self.user)
                )
            elif perm.permission_type == 'edit':
                # user has edit permission on any subpage of perm.page
                # (including perm.page itself) regardless of owner
                q_expressions.append(
                    Q(path__startswith=perm.page.path)
                )

        if q_expressions:
            all_rules = q_expressions[0]
            for expr in q_expressions[1:]:
                all_rules = all_rules | expr
            return Page.objects.filter(all_rules)
        else:
            return Page.objects.none()

class PagePermissionTester(object):
    def __init__(self, user_perms, page):
        self.user = user_perms.user
        self.user_perms = user_perms
        self.page = page
        self.page_is_root = page.depth == 1 # Equivalent to page.is_root()

        if self.user.is_active and not self.user.is_superuser:
            self.permissions = set(
                perm.permission_type for perm in user_perms.permissions
                if self.page.path.startswith(perm.page.path)
            )

    def can_add_subpage(self):
        if not self.user.is_active:
            return False
        return self.user.is_superuser or ('add' in self.permissions)

    def can_edit(self):
        if not self.user.is_active:
            return False
        if self.page_is_root:  # root node is not a page and can never be edited, even by superusers
            return False
        return self.user.is_superuser or ('edit' in self.permissions) or ('add' in self.permissions and self.page.owner_id == self.user.id)

    def can_delete(self):
        if not self.user.is_active:
            return False
        if self.page_is_root:  # root node is not a page and can never be deleted, even by superusers
            return False

        if self.user.is_superuser or ('publish' in self.permissions):
            # Users with publish permission can unpublish any pages that need to be unpublished to achieve deletion
            return True

        elif 'edit' in self.permissions:
            # user can only delete if there are no live pages in this subtree
            return (not self.page.live) and (not self.page.get_descendants().filter(live=True).exists())

        elif 'add' in self.permissions:
            # user can only delete if all pages in this subtree are unpublished and owned by this user
            return (
                (not self.page.live)
                and (self.page.owner_id == self.user.id)
                and (not self.page.get_descendants().exclude(live=False, owner=self.user).exists())
            )

        else:
            return False

    def can_unpublish(self):
        if not self.user.is_active:
            return False
        if (not self.page.live) or self.page_is_root:
            return False

        return self.user.is_superuser or ('publish' in self.permissions)

    def can_publish(self):
        if not self.user.is_active:
            return False
        if self.page_is_root:
            return False

        return self.user.is_superuser or ('publish' in self.permissions)

    def can_publish_subpage(self):
        """
        Niggly special case for creating and publishing a page in one go.
        Differs from can_publish in that we want to be able to publish subpages of root, but not
        to be able to publish root itself
        """
        if not self.user.is_active:
            return False

        return self.user.is_superuser or ('publish' in self.permissions)

    def can_reorder_children(self):
        """
        Keep reorder permissions the same as publishing, since it immediately affects published pages
        (and the use-cases for a non-admin needing to do it are fairly obscure...)
        """
        return self.can_publish_subpage()

    def can_move(self):
        """
        Moving a page should be logically equivalent to deleting and re-adding it (and all its children).
        As such, the permission test for 'can this be moved at all?' should be the same as for deletion.
        (Further constraints will then apply on where it can be moved *to*.)
        """
        return self.can_delete()

    def can_move_to(self, destination):
        # reject the logically impossible cases first
        if self.page == destination or destination.is_descendant_of(self.page):
            return False

        # and shortcut the trivial 'everything' / 'nothing' permissions
        if not self.user.is_active:
            return False
        if self.user.is_superuser:
            return True

        # check that the page can be moved at all
        if not self.can_move():
            return False

        # Inspect permissions on the destination
        destination_perms = self.user_perms.for_page(destination)

        # we always need at least add permission in the target
        if 'add' not in destination_perms.permissions:
            return False

        if self.page.live or self.page.get_descendants().filter(live=True).exists():
            # moving this page will entail publishing within the destination section
            return ('publish' in destination_perms.permissions)
        else:
            # no publishing required, so the already-tested 'add' permission is sufficient
            return True
