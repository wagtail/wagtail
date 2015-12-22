from __future__ import unicode_literals


import logging
import json
import warnings

from collections import defaultdict
from modelcluster.models import ClusterableModel, get_all_child_relations
from django.db import models, connection, transaction
from django.db.models import Q
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch.dispatcher import receiver
from django.http import Http404
from django.core.cache import cache
from django.core.handlers.wsgi import WSGIRequest
from django.core.handlers.base import BaseHandler
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group
from django.conf import settings
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.six import StringIO
from django.utils.six.moves.urllib.parse import urlparse
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils.functional import cached_property
from django.utils.encoding import python_2_unicode_compatible
from django.core import checks

# Must be imported from Django so we get the new implementation of with_metaclass
from django.utils import six

from treebeard.mp_tree import MP_Node

from wagtail.wagtailcore.utils import camelcase_to_underscore, resolve_model_string
from wagtail.wagtailcore.query import PageQuerySet
from wagtail.wagtailcore.url_routing import RouteResult
from wagtail.wagtailcore.signals import page_published, page_unpublished

from wagtail.wagtailsearch import index

from wagtail.utils.deprecation import RemovedInWagtail15Warning


logger = logging.getLogger('wagtail.core')

PAGE_TEMPLATE_VAR = 'page'


class SiteManager(models.Manager):
    def get_by_natural_key(self, hostname, port):
        return self.get(hostname=hostname, port=port)


@python_2_unicode_compatible
class Site(models.Model):
    hostname = models.CharField(verbose_name=_('hostname'), max_length=255, db_index=True)
    port = models.IntegerField(
        verbose_name=_('port'),
        default=80,
        help_text=_(
            "Set this to something other than 80 if you need a specific port number to appear in URLs"
            " (e.g. development on port 8000). Does not affect request handling (so port forwarding still works)."
        )
    )
    site_name = models.CharField(
        verbose_name=_('site name'),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Human-readable name for the site.")
    )
    root_page = models.ForeignKey('Page', verbose_name=_('root page'), related_name='sites_rooted_here')
    is_default_site = models.BooleanField(
        verbose_name=_('is default site'),
        default=False,
        help_text=_(
            "If true, this site will handle requests for all other hostnames that do not have a site entry of their own"
        )
    )

    objects = SiteManager()

    class Meta:
        unique_together = ('hostname', 'port')
        verbose_name = _('site')
        verbose_name_plural = _('sites')

    def natural_key(self):
        return (self.hostname, self.port)

    def __str__(self):
        return (
            self.hostname +
            ("" if self.port == 80 else (":%d" % self.port)) +
            (" [default]" if self.is_default_site else "")
        )

    @staticmethod
    def find_for_request(request):
        """
        Find the site object responsible for responding to this HTTP
        request object. Try:

        * unique hostname first
        * then hostname and port
        * if there is no matching hostname at all, or no matching
          hostname:port combination, fall back to the unique default site,
          or raise an exception

        NB this means that high-numbered ports on an extant hostname may
        still be routed to a different hostname which is set as the default
        """
        try:
            hostname = request.META['HTTP_HOST'].split(':')[0]  # KeyError here goes to the final except clause
            try:
                # find a Site matching this specific hostname
                return Site.objects.get(hostname=hostname)  # Site.DoesNotExist here goes to the final except clause
            except Site.MultipleObjectsReturned:
                # as there were more than one, try matching by port too
                port = request.META['SERVER_PORT']  # KeyError here goes to the final except clause
                return Site.objects.get(hostname=hostname, port=int(port))
                # Site.DoesNotExist here goes to the final except clause
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

    def clean_fields(self, exclude=None):
        super(Site, self).clean_fields(exclude)
        # Only one site can have the is_default_site flag set
        try:
            default = Site.objects.get(is_default_site=True)
        except Site.DoesNotExist:
            pass
        except Site.MultipleObjectsReturned:
            raise
        else:
            if self.is_default_site and self.pk != default.pk:
                raise ValidationError(
                    {'is_default_site': [
                        _(
                            "%(hostname)s is already configured as the default site."
                            " You must unset that before you can save this site as default."
                        )
                        % {'hostname': default.hostname}
                    ]}
                )

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


# Clear the wagtail_site_root_paths from the cache whenever Site records are updated
@receiver(post_save, sender=Site)
def clear_site_root_paths_on_save(sender, instance, **kwargs):
    cache.delete('wagtail_site_root_paths')


@receiver(post_delete, sender=Site)
def clear_site_root_paths_on_delete(sender, instance, **kwargs):
    cache.delete('wagtail_site_root_paths')


PAGE_MODEL_CLASSES = []


def get_content_type_list(models):
    """
    Helper function to return a list of content types, given a list of models
    """
    return ContentType.objects.get_for_models(*models).values()


def get_page_models():
    """
    Returns a list of all non-abstract Page model classes defined in this project.
    """
    return PAGE_MODEL_CLASSES


def get_default_page_content_type():
    """
    Returns the content type to use as a default for pages whose content type
    has been deleted.
    """
    return ContentType.objects.get_for_model(Page)


def get_page_types():
    """
    DEPRECATED.
    Returns a list of ContentType objects for all non-abstract Page model classes
    defined in this project.
    """
    warnings.warn(
        "get_page_types is deprecated - please use get_page_models instead",
        RemovedInWagtail15Warning, stacklevel=2)

    return get_content_type_list(PAGE_MODEL_CLASSES)


class BasePageManager(models.Manager):
    def get_queryset(self):
        return PageQuerySet(self.model).order_by('path')

PageManager = BasePageManager.from_queryset(PageQuerySet)


class PageBase(models.base.ModelBase):
    """Metaclass for Page"""
    def __init__(cls, name, bases, dct):
        super(PageBase, cls).__init__(name, bases, dct)

        if cls._deferred:
            # this is an internal class built for Django's deferred-attribute mechanism;
            # don't proceed with all this page type registration stuff
            return

        # Override the default `objects` attribute with a `PageManager`.
        # Managers are not inherited by MTI child models, so `Page` subclasses
        # will get a plain `Manager` instead of a `PageManager`.
        # If the developer has set their own custom `Manager` subclass, do not
        # clobber it.
        if not cls._meta.abstract and type(cls.objects) is models.Manager:
            PageManager().contribute_to_class(cls, 'objects')

        if 'template' not in dct:
            # Define a default template path derived from the app name and model name
            cls.template = "%s/%s.html" % (cls._meta.app_label, camelcase_to_underscore(name))

        if 'ajax_template' not in dct:
            cls.ajax_template = None

        cls._clean_subpage_models = None  # to be filled in on first call to cls.clean_subpage_models
        cls._clean_parent_page_models = None  # to be filled in on first call to cls.clean_parent_page_models

        # All pages should be creatable unless explicitly set otherwise.
        # This attribute is not inheritable.
        if 'is_creatable' not in dct:
            cls.is_creatable = not cls._meta.abstract

        if not cls._meta.abstract:
            # register this type in the list of page content types
            PAGE_MODEL_CLASSES.append(cls)


@python_2_unicode_compatible
class Page(six.with_metaclass(PageBase, MP_Node, ClusterableModel, index.Indexed)):
    title = models.CharField(
        verbose_name=_('title'),
        max_length=255,
        help_text=_("The page title as you'd like it to be seen by the public")
    )
    slug = models.SlugField(
        verbose_name=_('slug'),
        max_length=255,
        help_text=_("The name of the page as it will appear in URLs e.g http://domain.com/blog/[my-slug]/")
    )
    # TODO: enforce uniqueness on slug field per parent (will have to be done at the Django
    # level rather than db, since there is no explicit parent relation in the db)
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        verbose_name=_('content type'),
        related_name='pages',
        on_delete=models.SET(get_default_page_content_type)
    )
    live = models.BooleanField(verbose_name=_('live'), default=True, editable=False)
    has_unpublished_changes = models.BooleanField(
        verbose_name=_('has unpublished changes'),
        default=False,
        editable=False
    )
    url_path = models.TextField(verbose_name=_('URL path'), blank=True, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('owner'),
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name='owned_pages'
    )

    seo_title = models.CharField(
        verbose_name=_("page title"),
        max_length=255,
        blank=True,
        help_text=_("Optional. 'Search Engine Friendly' title. This will appear at the top of the browser window.")
    )
    show_in_menus = models.BooleanField(
        verbose_name=_('show in menus'),
        default=False,
        help_text=_("Whether a link to this page will appear in automatically generated menus")
    )
    search_description = models.TextField(verbose_name=_('search description'), blank=True)

    go_live_at = models.DateTimeField(
        verbose_name=_("go live date/time"),
        help_text=_("Please add a date-time in the form YYYY-MM-DD hh:mm."),
        blank=True,
        null=True
    )
    expire_at = models.DateTimeField(
        verbose_name=_("expiry date/time"),
        help_text=_("Please add a date-time in the form YYYY-MM-DD hh:mm."),
        blank=True,
        null=True
    )
    expired = models.BooleanField(verbose_name=_('expired'), default=False, editable=False)

    locked = models.BooleanField(verbose_name=_('locked'), default=False, editable=False)

    first_published_at = models.DateTimeField(
        verbose_name=_('first published at'),
        null=True,
        editable=False,
        db_index=True
    )
    latest_revision_created_at = models.DateTimeField(
        verbose_name=_('latest revision created at'),
        null=True,
        editable=False
    )

    search_fields = (
        index.SearchField('title', partial_match=True, boost=2),
        index.FilterField('id'),
        index.FilterField('live'),
        index.FilterField('owner'),
        index.FilterField('content_type'),
        index.FilterField('path'),
        index.FilterField('depth'),
        index.FilterField('locked'),
        index.FilterField('show_in_menus'),
        index.FilterField('first_published_at'),
        index.FilterField('latest_revision_created_at'),
    )

    # Do not allow plain Page instances to be created through the Wagtail admin
    is_creatable = False

    objects = PageManager()

    def __init__(self, *args, **kwargs):
        super(Page, self).__init__(*args, **kwargs)
        if not self.id and not self.content_type_id:
            # this model is being newly created rather than retrieved from the db;
            # set content type to correctly represent the model class that this was
            # created as
            self.content_type = ContentType.objects.get_for_model(self)

    def __str__(self):
        return self.title

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

    @transaction.atomic
    # ensure that changes are only committed when we have updated all descendant URL paths, to preserve consistency
    def save(self, *args, **kwargs):
        update_descendant_url_paths = False
        is_new = self.id is None

        if is_new:
            # we are creating a record. If we're doing things properly, this should happen
            # through a treebeard method like add_child, in which case the 'path' field
            # has been set and so we can safely call get_parent
            self.set_url_path(self.get_parent())
        else:
            # Check that we are committing the slug to the database
            # Basically: If update_fields has been specified, and slug is not included, skip this step
            if not ('update_fields' in kwargs and 'slug' not in kwargs['update_fields']):
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

        # Log
        if is_new:
            cls = type(self)
            logger.info(
                "Page created: \"%s\" id=%d content_type=%s.%s path=%s",
                self.title,
                self.id,
                cls._meta.app_label,
                cls.__name__,
                self.url_path
            )

        return result

    def delete(self, *args, **kwargs):
        # Ensure that deletion always happens on an instance of Page, not a specific subclass. This
        # works around a bug in treebeard <= 3.0 where calling SpecificPage.delete() fails to delete
        # child pages that are not instances of SpecificPage
        if type(self) is Page:
            # this is a Page instance, so carry on as we were
            return super(Page, self).delete(*args, **kwargs)
        else:
            # retrieve an actual Page instance and delete that instead of self
            return Page.objects.get(id=self.id).delete(*args, **kwargs)

    @classmethod
    def check(cls, **kwargs):
        errors = super(Page, cls).check(**kwargs)

        # Check that foreign keys from pages are not configured to cascade
        # This is the default Django behaviour which must be explicitly overridden
        # to prevent pages disappearing unexpectedly and the tree being corrupted

        # get names of foreign keys pointing to parent classes (such as page_ptr)
        field_exceptions = [field.name
                            for model in [cls] + list(cls._meta.get_parent_list())
                            for field in model._meta.parents.values() if field]

        for field in cls._meta.fields:
            if isinstance(field, models.ForeignKey) and field.name not in field_exceptions:
                if field.rel.on_delete == models.CASCADE:
                    errors.append(
                        checks.Warning(
                            "Field hasn't specified on_delete action",
                            hint="Set on_delete=models.SET_NULL and make sure the field is nullable.",
                            obj=field,
                            id='wagtailcore.W001',
                        )
                    )

        if not isinstance(cls.objects, PageManager):
            errors.append(
                checks.Error(
                    "Manager does not inherit from PageManager",
                    hint="Ensure that custom Page managers inherit from {}.{}".format(
                        PageManager.__module__, PageManager.__name__),
                    obj=cls,
                    id='wagtailcore.E002',
                )
            )

        try:
            cls.clean_subpage_models()
        except (ValueError, LookupError) as e:
            errors.append(
                checks.Error(
                    "Invalid subpage_types setting for %s" % cls,
                    hint=str(e),
                    id='wagtailcore.E002'
                )
            )

        try:
            cls.clean_parent_page_models()
        except (ValueError, LookupError) as e:
            errors.append(
                checks.Error(
                    "Invalid parent_page_types setting for %s" % cls,
                    hint=str(e),
                    id='wagtailcore.E002'
                )
            )

        return errors

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
        cursor.execute(update_statement, [new_url_path, len(old_url_path) + 1, self.path + '%', self.id])

    #: Return this page in its most specific subclassed form.
    @cached_property
    def specific(self):
        """
        Return this page in its most specific subclassed form.
        """
        # the ContentType.objects manager keeps a cache, so this should potentially
        # avoid a database lookup over doing self.content_type. I think.
        content_type = ContentType.objects.get_for_id(self.content_type_id)
        model_class = content_type.model_class()
        if model_class is None:
            # Cannot locate a model class for this content type. This might happen
            # if the codebase and database are out of sync (e.g. the model exists
            # on a different git branch and we haven't rolled back migrations before
            # switching branches); if so, the best we can do is return the page
            # unchanged.
            return self
        elif isinstance(self, model_class):
            # self is already the an instance of the most specific class
            return self
        else:
            return content_type.get_object_for_this_type(id=self.id)

    #: Return the class that this page would be if instantiated in its
    #: most specific form
    @cached_property
    def specific_class(self):
        """
        Return the class that this page would be if instantiated in its
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
                return RouteResult(self)
            else:
                raise Http404

    def save_revision(self, user=None, submitted_for_moderation=False, approved_go_live_at=None, changed=True):
        # Create revision
        revision = self.revisions.create(
            content_json=self.to_json(),
            user=user,
            submitted_for_moderation=submitted_for_moderation,
            approved_go_live_at=approved_go_live_at,
        )

        update_fields = []

        self.latest_revision_created_at = revision.created_at
        update_fields.append('latest_revision_created_at')

        if changed:
            self.has_unpublished_changes = True
            update_fields.append('has_unpublished_changes')

        if update_fields:
            self.save(update_fields=update_fields)

        # Log
        logger.info("Page edited: \"%s\" id=%d revision_id=%d", self.title, self.id, revision.id)

        if submitted_for_moderation:
            logger.info("Page submitted for moderation: \"%s\" id=%d revision_id=%d", self.title, self.id, revision.id)

        return revision

    def get_latest_revision(self):
        return self.revisions.order_by('-created_at', '-id').first()

    def get_latest_revision_as_page(self):
        if not self.has_unpublished_changes:
            # Use the live database copy in preference to the revision record, as:
            # 1) this will pick up any changes that have been made directly to the model,
            #    such as automated data imports;
            # 2) it ensures that inline child objects pick up real database IDs even if
            #    those are absent from the revision data. (If this wasn't the case, the child
            #    objects would be recreated with new IDs on next publish - see #1853)
            return self.specific

        latest_revision = self.get_latest_revision()

        if latest_revision:
            return latest_revision.as_page_object()
        else:
            return self.specific

    def unpublish(self, set_expired=False, commit=True):
        if self.live:
            self.live = False
            self.has_unpublished_changes = True

            if set_expired:
                self.expired = True

            if commit:
                self.save()

            page_unpublished.send(sender=self.specific_class, instance=self.specific)

            logger.info("Page unpublished: \"%s\" id=%d", self.title, self.id)

            self.revisions.update(approved_go_live_at=None)

    def get_context(self, request, *args, **kwargs):
        return {
            PAGE_TEMPLATE_VAR: self,
            'self': self,
            'request': request,
        }

    def get_template(self, request, *args, **kwargs):
        if request.is_ajax():
            return self.ajax_template or self.template
        else:
            return self.template

    def serve(self, request, *args, **kwargs):
        request.is_preview = getattr(request, 'is_preview', False)

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

    @property
    def full_url(self):
        """Return the full URL (including protocol / domain) to this page, or None if it is not routable"""
        for (id, root_path, root_url) in Site.get_site_root_paths():
            if self.url_path.startswith(root_path):
                return root_url + reverse('wagtail_serve', args=(self.url_path[len(root_path):],))

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
        for (id, root_path, root_url) in root_paths:
            if self.url_path.startswith(root_path):
                return ('' if len(root_paths) == 1 else root_url) + reverse(
                    'wagtail_serve', args=(self.url_path[len(root_path):],)
                )

    def relative_url(self, current_site):
        """
        Return the 'most appropriate' URL for this page taking into account the site we're currently on;
        a local URL if the site matches, or a fully qualified one otherwise.
        Return None if the page is not routable.
        """
        for (id, root_path, root_url) in Site.get_site_root_paths():
            if self.url_path.startswith(root_path):
                return ('' if current_site.id == id else root_url) + reverse(
                    'wagtail_serve', args=(self.url_path[len(root_path):],)
                )

    @classmethod
    def get_indexed_objects(cls):
        content_type = ContentType.objects.get_for_model(cls)
        return super(Page, cls).get_indexed_objects().filter(content_type=content_type)

    def get_indexed_instance(self):
        # This is accessed on save by the wagtailsearch signal handler, and in edge
        # cases (e.g. loading test fixtures), may be called before the specific instance's
        # entry has been created. In those cases, we aren't ready to be indexed yet, so
        # return None.
        try:
            return self.specific
        except self.specific_class.DoesNotExist:
            return None

    @classmethod
    def clean_subpage_models(cls):
        """
        Returns the list of subpage types, normalised as model classes.
        Throws ValueError if any entry in subpage_types cannot be recognised as a model name,
        or LookupError if a model does not exist (or is not a Page subclass).
        """
        if cls._clean_subpage_models is None:
            subpage_types = getattr(cls, 'subpage_types', None)
            if subpage_types is None:
                # if subpage_types is not specified on the Page class, allow all page types as subpages
                cls._clean_subpage_models = get_page_models()
            else:
                cls._clean_subpage_models = [
                    resolve_model_string(model_string, cls._meta.app_label)
                    for model_string in subpage_types
                ]

                for model in cls._clean_subpage_models:
                    if not issubclass(model, Page):
                        raise LookupError("%s is not a Page subclass" % model)

        return cls._clean_subpage_models

    @classmethod
    def clean_subpage_types(cls):
        """
        DEPRECATED.
        Returns the list of subpage types, normalised as ContentType objects
        """
        warnings.warn(
            "clean_subpage_types is deprecated - please use clean_subpage_models instead",
            RemovedInWagtail15Warning, stacklevel=2)

        return get_content_type_list(cls.clean_subpage_models())

    @classmethod
    def clean_parent_page_models(cls):
        """
        Returns the list of parent page types, normalised as model classes.
        Throws ValueError if any entry in parent_page_types cannot be recognised as a model name,
        or LookupError if a model does not exist (or is not a Page subclass).
        """

        if cls._clean_parent_page_models is None:
            parent_page_types = getattr(cls, 'parent_page_types', None)
            if parent_page_types is None:
                # if parent_page_types is not specified on the Page class, allow all page types as subpages
                cls._clean_parent_page_models = get_page_models()
            else:
                cls._clean_parent_page_models = [
                    resolve_model_string(model_string, cls._meta.app_label)
                    for model_string in parent_page_types
                ]

                for model in cls._clean_parent_page_models:
                    if not issubclass(model, Page):
                        raise LookupError("%s is not a Page subclass" % model)

        return cls._clean_parent_page_models

    @classmethod
    def clean_parent_page_types(cls):
        """
        DEPRECATED.
        Returns the list of parent page types, normalised as ContentType objects
        """
        warnings.warn(
            "clean_parent_page_types is deprecated - please use clean_parent_page_models instead",
            RemovedInWagtail15Warning, stacklevel=2)

        return get_content_type_list(cls.clean_parent_page_models())

    @classmethod
    def allowed_parent_page_models(cls):
        """
        Returns the list of page types that this page type can be a subpage of,
        as a list of model classes
        """
        return [
            parent_model for parent_model in cls.clean_parent_page_models()
            if cls in parent_model.clean_subpage_models()
        ]

    @classmethod
    def allowed_parent_page_types(cls):
        """
        DEPRECATED.
        Returns the list of page types that this page type can be a subpage of,
        as a list of ContentType objects
        """
        warnings.warn(
            "allowed_parent_page_types is deprecated - please use allowed_parent_page_models instead",
            RemovedInWagtail15Warning, stacklevel=2)

        return get_content_type_list(cls.allowed_parent_page_models())

    @classmethod
    def allowed_subpage_models(cls):
        """
        Returns the list of page types that this page type can have as subpages,
        as a list of model classes
        """
        return [
            subpage_model for subpage_model in cls.clean_subpage_models()
            if cls in subpage_model.clean_parent_page_models()
        ]

    @classmethod
    def allowed_subpage_types(cls):
        """
        DEPRECATED.
        Returns the list of page types that this page type can have as subpages,
        as a list of ContentType objects
        """
        warnings.warn(
            "allowed_subpage_types is deprecated - please use allowed_subpage_models instead",
            RemovedInWagtail15Warning, stacklevel=2)

        return get_content_type_list(cls.allowed_subpage_models())

    @classmethod
    def creatable_subpage_models(cls):
        """
        Returns the list of page types that may be created under this page type,
        as a list of model classes
        """
        return [
            page_model for page_model in cls.allowed_subpage_models()
            if page_model.is_creatable
        ]

    @classmethod
    def can_exist_under(cls, parent):
        """
        Checks if this page type can exist as a subpage under a parent page
        instance.

        See also: :func:`Page.can_create_at` and :func:`Page.can_move_to`
        """
        return cls in parent.specific_class.allowed_subpage_models()

    @classmethod
    def can_create_at(cls, parent):
        """
        Checks if this page type can be created as a subpage under a parent
        page instance.
        """
        return cls.is_creatable and cls.can_exist_under(parent)

    def can_move_to(self, parent):
        """
        Checks if this page instance can be moved to be a subpage of a parent
        page instance.
        """
        return self.can_exist_under(parent)

    @classmethod
    def get_verbose_name(cls):
        """
            Returns the human-readable "verbose name" of this page model e.g "Blog page".
        """
        # This is similar to doing cls._meta.verbose_name.title()
        # except this doesn't convert any characters to lowercase
        return ' '.join([word[0].upper() + word[1:] for word in cls._meta.verbose_name.split()])

    @property
    def status_string(self):
        if not self.live:
            if self.expired:
                return _("expired")
            elif self.approved_schedule:
                return _("scheduled")
            else:
                return _("draft")
        else:
            if self.has_unpublished_changes:
                return _("live + draft")
            else:
                return _("live")

    @property
    def approved_schedule(self):
        return self.revisions.exclude(approved_go_live_at__isnull=True).exists()

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

        # Log
        logger.info("Page moved: \"%s\" id=%d path=%s", self.title, self.id, new_url_path)

    def copy(self, recursive=False, to=None, update_attrs=None, copy_revisions=True, keep_live=True, user=None):
        # Fill dict with self.specific values
        exclude_fields = ['id', 'path', 'depth', 'numchild', 'url_path', 'path']
        specific_self = self.specific
        specific_dict = {}

        for field in specific_self._meta.get_fields():
            # Ignore explicitly excluded fields
            if field.name in exclude_fields:
                continue

            # Ignore reverse relations
            if field.auto_created:
                continue

            # Ignore m2m relations - they will be copied as child objects
            # if modelcluster supports them at all (as it does for tags)
            if field.many_to_many:
                continue

            # Ignore parent links (page_ptr)
            if isinstance(field, models.OneToOneField) and field.parent_link:
                continue

            specific_dict[field.name] = getattr(specific_self, field.name)

        # New instance from prepared dict values, in case the instance class implements multiple levels inheritance
        page_copy = self.specific_class(**specific_dict)

        if not keep_live:
            page_copy.live = False
            page_copy.has_unpublished_changes = True

        if user:
            page_copy.owner = user

        if update_attrs:
            for field, value in update_attrs.items():
                setattr(page_copy, field, value)

        if to:
            page_copy = to.add_child(instance=page_copy)
        else:
            page_copy = self.add_sibling(instance=page_copy)

        # A dict that maps child objects to their new ids
        # Used to remap child object ids in revisions
        child_object_id_map = defaultdict(dict)

        # Copy child objects
        specific_self = self.specific
        for child_relation in get_all_child_relations(specific_self):
            accessor_name = child_relation.get_accessor_name()
            parental_key_name = child_relation.field.attname
            child_objects = getattr(specific_self, accessor_name, None)

            if child_objects:
                for child_object in child_objects.all():
                    old_pk = child_object.pk
                    child_object.pk = None
                    setattr(child_object, parental_key_name, page_copy.id)
                    child_object.save()

                    # Add mapping to new primary key (so we can apply this change to revisions)
                    child_object_id_map[accessor_name][old_pk] = child_object.pk

        # Copy revisions
        if copy_revisions:
            for revision in self.revisions.all():
                revision.pk = None
                revision.submitted_for_moderation = False
                revision.approved_go_live_at = None
                revision.page = page_copy

                # Update ID fields in content
                revision_content = json.loads(revision.content_json)
                revision_content['pk'] = page_copy.pk

                for child_relation in get_all_child_relations(specific_self):
                    accessor_name = child_relation.get_accessor_name()
                    try:
                        child_objects = revision_content[accessor_name]
                    except KeyError:
                        # KeyErrors are possible if the revision was created
                        # before this child relation was added to the database
                        continue

                    for child_object in child_objects:
                        child_object[child_relation.field.name] = page_copy.pk

                        # Remap primary key to copied versions
                        # If the primary key is not recognised (eg, the child object has been deleted from the database)
                        # set the primary key to None
                        child_object['pk'] = child_object_id_map[accessor_name].get(child_object['pk'], None)

                revision.content_json = json.dumps(revision_content)

                # Save
                revision.save()

        # Create a new revision
        # This code serves a few purposes:
        # * It makes sure update_attrs gets applied to the latest revision
        # * It bumps the last_revision_created_at value so the new page gets ordered as if it was just created
        # * It sets the user of the new revision so it's possible to see who copied the page by looking at its history
        latest_revision = page_copy.get_latest_revision_as_page()

        if update_attrs:
            for field, value in update_attrs.items():
                setattr(latest_revision, field, value)

        latest_revision.save_revision(user=user, changed=False)

        # Log
        logger.info("Page copied: \"%s\" id=%d from=%d", page_copy.title, page_copy.id, self.id)

        # Copy child pages
        if recursive:
            for child_page in self.get_children():
                child_page.specific.copy(
                    recursive=True,
                    to=page_copy,
                    copy_revisions=copy_revisions,
                    keep_live=keep_live,
                    user=user
                )

        return page_copy

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
            'HTTP_HOST': hostname,
            'wsgi.input': StringIO(),
        })

        # Apply middleware to the request - see http://www.mellowmorning.com/2011/04/18/mock-django-request-for-testing/
        handler = BaseHandler()
        handler.load_middleware()
        # call each middleware in turn and throw away any responses that they might return
        for middleware_method in handler._request_middleware:
            middleware_method(request)

        return request

    DEFAULT_PREVIEW_MODES = [('', _('Default'))]

    @property
    def preview_modes(self):
        """
        A list of (internal_name, display_name) tuples for the modes in which
        this page can be displayed for preview/moderation purposes. Ordinarily a page
        will only have one display mode, but subclasses of Page can override this -
        for example, a page containing a form might have a default view of the form,
        and a post-submission 'thankyou' page
        """
        return Page.DEFAULT_PREVIEW_MODES

    @property
    def default_preview_mode(self):
        return self.preview_modes[0][0]

    def serve_preview(self, request, mode_name):
        """
        Return an HTTP response for use in page previews. Normally this would be equivalent
        to self.serve(request), since we obviously want the preview to be indicative of how
        it looks on the live site. However, there are a couple of cases where this is not
        appropriate, and custom behaviour is required:

        1) The page has custom routing logic that derives some additional required
        args/kwargs to be passed to serve(). The routing mechanism is bypassed when
        previewing, so there's no way to know what args we should pass. In such a case,
        the page model needs to implement its own version of serve_preview.

        2) The page has several different renderings that we would like to be able to see
        when previewing - for example, a form page might have one rendering that displays
        the form, and another rendering to display a landing page when the form is posted.
        This can be done by setting a custom preview_modes list on the page model -
        Wagtail will allow the user to specify one of those modes when previewing, and
        pass the chosen mode_name to serve_preview so that the page model can decide how
        to render it appropriately. (Page models that do not specify their own preview_modes
        list will always receive an empty string as mode_name.)

        Any templates rendered during this process should use the 'request' object passed
        here - this ensures that request.user and other properties are set appropriately for
        the wagtail user bar to be displayed. This request will always be a GET.
        """
        request.is_preview = True

        return self.serve(request)

    def get_cached_paths(self):
        """
        This returns a list of paths to invalidate in a frontend cache
        """
        return ['/']

    def get_sitemap_urls(self):
        return [
            {
                'location': self.full_url,
                'lastmod': self.latest_revision_created_at
            }
        ]

    def get_static_site_paths(self):
        """
        This is a generator of URL paths to feed into a static site generator
        Override this if you would like to create static versions of subpages
        """
        # Yield path for this page
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

    def get_next_siblings(self, inclusive=False):
        return self.get_siblings(inclusive).filter(path__gte=self.path).order_by('path')

    def get_prev_siblings(self, inclusive=False):
        return self.get_siblings(inclusive).filter(path__lte=self.path).order_by('-path')

    def get_view_restrictions(self):
        """Return a query set of all page view restrictions that apply to this page"""
        return PageViewRestriction.objects.filter(page__in=self.get_ancestors(inclusive=True))

    password_required_template = getattr(settings, 'PASSWORD_REQUIRED_TEMPLATE', 'wagtailcore/password_required.html')

    def serve_password_required_response(self, request, form, action_url):
        """
        Serve a response indicating that the user has been denied access to view this page,
        and must supply a password.
        form = a Django form object containing the password input
            (and zero or more hidden fields that also need to be output on the template)
        action_url = URL that this form should be POSTed to
        """
        context = self.get_context(request)
        context['form'] = form
        context['action_url'] = action_url
        return TemplateResponse(request, self.password_required_template, context)

    class Meta:
        verbose_name = _('page')
        verbose_name_plural = _('pages')


def get_navigation_menu_items():
    # Get all pages that appear in the navigation menu: ones which have children,
    # or are at the top-level (this rule required so that an empty site out-of-the-box has a working menu)
    pages = Page.objects.filter(Q(depth=2) | Q(numchild__gt=0)).order_by('path')

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


@receiver(pre_delete, sender=Page)
def unpublish_page_before_delete(sender, instance, **kwargs):
    # Make sure pages are unpublished before deleting
    if instance.live:
        # Don't bother to save, this page is just about to be deleted!
        instance.unpublish(commit=False)


@receiver(post_delete, sender=Page)
def log_page_deletion(sender, instance, **kwargs):
    logger.info("Page deleted: \"%s\" id=%d", instance.title, instance.id)


class Orderable(models.Model):
    sort_order = models.IntegerField(null=True, blank=True, editable=False)
    sort_order_field = 'sort_order'

    class Meta:
        abstract = True
        ordering = ['sort_order']


class SubmittedRevisionsManager(models.Manager):
    def get_queryset(self):
        return super(SubmittedRevisionsManager, self).get_queryset().filter(submitted_for_moderation=True)


@python_2_unicode_compatible
class PageRevision(models.Model):
    page = models.ForeignKey('Page', verbose_name=_('page'), related_name='revisions')
    submitted_for_moderation = models.BooleanField(
        verbose_name=_('submitted for moderation'),
        default=False,
        db_index=True
    )
    created_at = models.DateTimeField(verbose_name=_('created at'))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('user'), null=True, blank=True,
        on_delete=models.SET_NULL
    )
    content_json = models.TextField(verbose_name=_('content JSON'))
    approved_go_live_at = models.DateTimeField(verbose_name=_('approved go live at'), null=True, blank=True)

    objects = models.Manager()
    submitted_revisions = SubmittedRevisionsManager()

    def save(self, *args, **kwargs):
        # Set default value for created_at to now
        # We cannot use auto_now_add as that will override
        # any value that is set before saving
        if self.created_at is None:
            self.created_at = timezone.now()

        super(PageRevision, self).save(*args, **kwargs)
        if self.submitted_for_moderation:
            # ensure that all other revisions of this page have the 'submitted for moderation' flag unset
            self.page.revisions.exclude(id=self.id).update(submitted_for_moderation=False)

    def as_page_object(self):
        obj = self.page.specific_class.from_json(self.content_json)

        # Override the possibly-outdated tree parameter fields from this revision object
        # with up-to-date values
        obj.pk = self.page.pk
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
        obj.locked = self.page.locked
        obj.latest_revision_created_at = self.page.latest_revision_created_at
        obj.first_published_at = self.page.first_published_at

        return obj

    def approve_moderation(self):
        if self.submitted_for_moderation:
            logger.info("Page moderation approved: \"%s\" id=%d revision_id=%d", self.page.title, self.page.id, self.id)
            self.publish()

    def reject_moderation(self):
        if self.submitted_for_moderation:
            logger.info("Page moderation rejected: \"%s\" id=%d revision_id=%d", self.page.title, self.page.id, self.id)
            self.submitted_for_moderation = False
            self.save(update_fields=['submitted_for_moderation'])

    def is_latest_revision(self):
        if self.id is None:
            # special case: a revision without an ID is presumed to be newly-created and is thus
            # newer than any revision that might exist in the database
            return True
        latest_revision = PageRevision.objects.filter(page_id=self.page_id).order_by('-created_at', '-id').first()
        return (latest_revision == self)

    def publish(self):
        page = self.as_page_object()
        if page.go_live_at and page.go_live_at > timezone.now():
            # if we have a go_live in the future don't make the page live
            page.live = False
            page.has_unpublished_changes = True
            # Instead set the approved_go_live_at of this revision
            self.approved_go_live_at = page.go_live_at
            self.save()
            # And clear the the approved_go_live_at of any other revisions
            page.revisions.exclude(id=self.id).update(approved_go_live_at=None)
        else:
            page.live = True
            # at this point, the page has unpublished changes iff there are newer revisions than this one
            page.has_unpublished_changes = not self.is_latest_revision()
            # If page goes live clear the approved_go_live_at of all revisions
            page.revisions.update(approved_go_live_at=None)
        page.expired = False  # When a page is published it can't be expired

        # Set first_published_at if the page is being published now
        if page.live and page.first_published_at is None:
            page.first_published_at = timezone.now()

        page.save()
        self.submitted_for_moderation = False
        page.revisions.update(submitted_for_moderation=False)

        if page.live:
            page_published.send(sender=page.specific_class, instance=page.specific, revision=self)

            logger.info("Page published: \"%s\" id=%d revision_id=%d", page.title, page.id, self.id)
        elif page.go_live_at:
            logger.info(
                "Page scheduled for publish: \"%s\" id=%d revision_id=%d go_live_at=%s",
                page.title,
                page.id,
                self.id,
                page.go_live_at.isoformat()
            )

    def __str__(self):
        return '"' + six.text_type(self.page) + '" at ' + six.text_type(self.created_at)

    class Meta:
        verbose_name = _('page revision')
        verbose_name_plural = _('page revisions')


PAGE_PERMISSION_TYPE_CHOICES = [
    ('add', _('Add/edit pages you own')),
    ('edit', _('Edit any page')),
    ('publish', _('Publish any page')),
    ('lock', _('Lock/unlock any page')),
]


class GroupPagePermission(models.Model):
    group = models.ForeignKey(Group, verbose_name=_('group'), related_name='page_permissions')
    page = models.ForeignKey('Page', verbose_name=_('page'), related_name='group_permissions')
    permission_type = models.CharField(
        verbose_name=_('permission type'),
        max_length=20,
        choices=PAGE_PERMISSION_TYPE_CHOICES
    )

    class Meta:
        unique_together = ('group', 'page', 'permission_type')
        verbose_name = _('group page permission')
        verbose_name_plural = _('group page permissions')


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

        # get the list of pages for which they have direct publish permission
        # (i.e. they can publish any page within this subtree)
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

        editable_pages = Page.objects.none()

        for perm in self.permissions.filter(permission_type='add'):
            # user has edit permission on any subpage of perm.page
            # (including perm.page itself) that is owned by them
            editable_pages |= Page.objects.descendant_of(perm.page, inclusive=True).filter(owner=self.user)

        for perm in self.permissions.filter(permission_type='edit'):
            # user has edit permission on any subpage of perm.page
            # (including perm.page itself) regardless of owner
            editable_pages |= Page.objects.descendant_of(perm.page, inclusive=True)

        return editable_pages

    def can_edit_pages(self):
        """Return True if the user has permission to edit any pages"""
        return self.editable_pages().exists()

    def publishable_pages(self):
        """Return a queryset of the pages that this user has permission to publish"""
        # Deal with the trivial cases first...
        if not self.user.is_active:
            return Page.objects.none()
        if self.user.is_superuser:
            return Page.objects.all()

        publishable_pages = Page.objects.none()

        for perm in self.permissions.filter(permission_type='publish'):
            # user has publish permission on any subpage of perm.page
            # (including perm.page itself)
            publishable_pages |= Page.objects.descendant_of(perm.page, inclusive=True)

        return publishable_pages

    def can_publish_pages(self):
        """Return True if the user has permission to publish any pages"""
        return self.publishable_pages().exists()


class PagePermissionTester(object):
    def __init__(self, user_perms, page):
        self.user = user_perms.user
        self.user_perms = user_perms
        self.page = page
        self.page_is_root = page.depth == 1  # Equivalent to page.is_root()

        if self.user.is_active and not self.user.is_superuser:
            self.permissions = set(
                perm.permission_type for perm in user_perms.permissions
                if self.page.path.startswith(perm.page.path)
            )

    def can_add_subpage(self):
        if not self.user.is_active:
            return False
        if not self.page.specific_class.creatable_subpage_models():
            return False
        return self.user.is_superuser or ('add' in self.permissions)

    def can_edit(self):
        if not self.user.is_active:
            return False
        if self.page_is_root:  # root node is not a page and can never be edited, even by superusers
            return False
        return (
            self.user.is_superuser or
            ('edit' in self.permissions) or
            ('add' in self.permissions and self.page.owner_id == self.user.id)
        )

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
        if self.page.locked:
            return False

        return self.user.is_superuser or ('publish' in self.permissions)

    def can_publish(self):
        if not self.user.is_active:
            return False
        if self.page_is_root:
            return False

        return self.user.is_superuser or ('publish' in self.permissions)

    def can_set_view_restrictions(self):
        return self.can_publish()

    def can_lock(self):
        return self.user.is_superuser or ('lock' in self.permissions)

    def can_publish_subpage(self):
        """
        Niggly special case for creating and publishing a page in one go.
        Differs from can_publish in that we want to be able to publish subpages of root, but not
        to be able to publish root itself. (Also, can_publish_subpage returns false if the page
        does not allow subpages at all.)
        """
        if not self.user.is_active:
            return False
        if not self.page.specific_class.creatable_subpage_models():
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

        # reject moves that are forbidden by subpage_types / parent_page_types rules
        # (these rules apply to superusers too)
        if not self.page.specific.can_move_to(destination):
            return False

        # shortcut the trivial 'everything' / 'nothing' permissions
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


class PageViewRestriction(models.Model):
    page = models.ForeignKey('Page', verbose_name=_('page'), related_name='view_restrictions')
    password = models.CharField(verbose_name=_('password'), max_length=255)

    class Meta:
        verbose_name = _('page view restriction')
        verbose_name_plural = _('page view restrictions')
