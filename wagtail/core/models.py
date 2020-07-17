import json
import logging
from collections import defaultdict
from io import StringIO
from urllib.parse import urlparse

from django import forms
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core import checks
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.handlers.base import BaseHandler
from django.core.handlers.wsgi import WSGIRequest
from django.db import models, transaction
from django.db.models import Case, Q, Value, When
from django.db.models.expressions import OuterRef, Subquery
from django.db.models.functions import Concat, Lower, Substr
from django.http import Http404
from django.http.request import split_domain_port
from django.template.response import TemplateResponse
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.cache import patch_cache_control
from django.utils.encoding import force_str
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from django.utils.text import capfirst, slugify
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel, get_all_child_relations
from treebeard.mp_tree import MP_Node

from wagtail.core.forms import TaskStateCommentForm
from wagtail.core.query import PageQuerySet, TreeQuerySet
from wagtail.core.signals import (
    page_published, page_unpublished, post_page_move, pre_page_move,
    task_approved, task_cancelled, task_rejected, task_submitted,
    workflow_approved, workflow_cancelled, workflow_rejected, workflow_submitted)
from wagtail.core.sites import get_site_for_hostname
from wagtail.core.url_routing import RouteResult
from wagtail.core.utils import WAGTAIL_APPEND_SLASH, camelcase_to_underscore, resolve_model_string
from wagtail.search import index

logger = logging.getLogger('wagtail.core')

PAGE_TEMPLATE_VAR = 'page'


class MultiTableCopyMixin:
    default_exclude_fields_in_copy = ['id']

    def _get_field_dictionaries(self, exclude_fields=None):
        """Get dictionaries representing the model: one with all non m2m fields, and one containing the m2m fields"""
        specific_self = self.specific
        exclude_fields = exclude_fields or []
        specific_dict = {}
        specific_m2m_dict = {}

        for field in specific_self._meta.get_fields():
            # Ignore explicitly excluded fields
            if field.name in exclude_fields:
                continue

            # Ignore reverse relations
            if field.auto_created:
                continue

            # Copy parental m2m relations
            # Otherwise add them to the m2m dict to be set after saving
            if field.many_to_many:
                if isinstance(field, ParentalManyToManyField):
                    parental_field = getattr(specific_self, field.name)
                    if hasattr(parental_field, 'all'):
                        values = parental_field.all()
                        if values:
                            specific_dict[field.name] = values
                else:
                    try:
                        # Do not copy m2m links with a through model that has a ParentalKey to the model being copied - these will be copied as child objects
                        through_model_parental_links = [field for field in field.through._meta.get_fields() if isinstance(field, ParentalKey) and (field.related_model == specific_self.__class__ or field.related_model in specific_self._meta.parents)]
                        if through_model_parental_links:
                            continue
                    except AttributeError:
                        pass
                    specific_m2m_dict[field.name] = getattr(specific_self, field.name).all()
                continue

            # Ignore parent links (page_ptr)
            if isinstance(field, models.OneToOneField) and field.remote_field.parent_link:
                continue

            specific_dict[field.name] = getattr(specific_self, field.name)

        return specific_dict, specific_m2m_dict

    def _get_copy_instance(self, specific_dict, specific_m2m_dict, update_attrs=None):
        """Create a copy instance (without saving) from dictionaries of the model's fields, and update any attributes in update_attrs"""

        if not update_attrs:
            update_attrs = {}

        specific_class = self.specific.__class__

        copy_instance = specific_class(**specific_dict)

        if update_attrs:
            for field, value in update_attrs.items():
                if field in specific_m2m_dict:
                    continue
                setattr(copy_instance, field, value)

        return copy_instance

    def _save_copy_instance(self, instance, **kwargs):
        raise NotImplementedError

    def _set_m2m_relations(self, instance, specific_m2m_dict, update_attrs=None):
        """Set non-ParentalManyToMany m2m relations"""
        if not update_attrs:
            update_attrs = {}
        for field_name, value in specific_m2m_dict.items():
            value = update_attrs.get(field_name, value)
            getattr(instance, field_name).set(value)

        return instance

    def _copy_child_objects_to_instance(self, instance, exclude_fields=None, process_child_object=None):
        """Copy objects linked to the model by a ParentalKey, and set this to the new revision"""

        # A dict that maps child objects to their new ids
        # Used to remap child object ids in revisions
        child_object_id_map = defaultdict(dict)
        exclude_fields = exclude_fields or []
        specific_self = self.specific
        for child_relation in get_all_child_relations(specific_self):
            accessor_name = child_relation.get_accessor_name()

            if accessor_name in exclude_fields:
                continue

            parental_key_name = child_relation.field.attname
            child_objects = getattr(specific_self, accessor_name, None)

            if child_objects:
                for child_object in child_objects.all():
                    old_pk = child_object.pk
                    child_object.pk = None
                    setattr(child_object, parental_key_name, instance.id)

                    if process_child_object is not None:
                        process_child_object(specific_self, instance, child_relation, child_object)

                    child_object.save()

                    # Add mapping to new primary key (so we can apply this change to revisions)
                    child_object_id_map[accessor_name][old_pk] = child_object.pk

        return child_object_id_map

    def _copy(self, exclude_fields=None, update_attrs=None, process_child_object=None, **kwargs):
        exclude_fields = self.default_exclude_fields_in_copy + self.specific.exclude_fields_in_copy + (exclude_fields or [])

        specific_dict, specific_m2m_dict = self._get_field_dictionaries(exclude_fields=exclude_fields)

        copy_instance = self._get_copy_instance(specific_dict, specific_m2m_dict, update_attrs=update_attrs)

        copy_instance = self._save_copy_instance(copy_instance, **kwargs)

        copy_instance = self._set_m2m_relations(copy_instance, specific_m2m_dict, update_attrs)

        child_object_id_map = self._copy_child_objects_to_instance(copy_instance, exclude_fields=exclude_fields, process_child_object=process_child_object)

        return copy_instance, child_object_id_map


class SiteManager(models.Manager):
    def get_queryset(self):
        return super(SiteManager, self).get_queryset().order_by(Lower("hostname"))

    def get_by_natural_key(self, hostname, port):
        return self.get(hostname=hostname, port=port)


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
        blank=True,
        help_text=_("Human-readable name for the site.")
    )
    root_page = models.ForeignKey('Page', verbose_name=_('root page'), related_name='sites_rooted_here',
                                  on_delete=models.CASCADE)
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
        default_suffix = " [{}]".format(_("default"))
        if self.site_name:
            return (
                self.site_name
                + (default_suffix if self.is_default_site else "")
            )
        else:
            return (
                self.hostname
                + ("" if self.port == 80 else (":%d" % self.port))
                + (default_suffix if self.is_default_site else "")
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

        The site will be cached via request._wagtail_site
        """

        if request is None:
            return None

        if not hasattr(request, '_wagtail_site'):
            site = Site._find_for_request(request)
            setattr(request, '_wagtail_site', site)
        return request._wagtail_site

    @staticmethod
    def _find_for_request(request):
        hostname = split_domain_port(request.get_host())[0]
        port = request.get_port()
        site = None
        try:
            site = get_site_for_hostname(hostname, port)
        except Site.DoesNotExist:
            pass
            # copy old SiteMiddleware behavior
        return site

    @property
    def root_url(self):
        if self.port == 80:
            return 'http://%s' % self.hostname
        elif self.port == 443:
            return 'https://%s' % self.hostname
        else:
            return 'http://%s:%d' % (self.hostname, self.port)

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude)
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
        Return a list of (id, root_path, root_url) tuples, most specific path
        first - used to translate url_paths into actual URLs with hostnames
        """
        result = cache.get('wagtail_site_root_paths')

        if result is None:
            result = [
                (site.id, site.root_page.url_path, site.root_url)
                for site in Site.objects.select_related('root_page').order_by(
                    '-root_page__url_path', '-is_default_site', 'hostname')
            ]
            cache.set('wagtail_site_root_paths', result, 3600)

        return result


PAGE_MODEL_CLASSES = []


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


class BasePageManager(models.Manager):
    def get_queryset(self):
        return self._queryset_class(self.model).order_by('path')


PageManager = BasePageManager.from_queryset(PageQuerySet)


class PageBase(models.base.ModelBase):
    """Metaclass for Page"""

    def __init__(cls, name, bases, dct):
        super(PageBase, cls).__init__(name, bases, dct)

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


class AbstractPage(MP_Node):
    """
    Abstract superclass for Page. According to Django's inheritance rules, managers set on
    abstract models are inherited by subclasses, but managers set on concrete models that are extended
    via multi-table inheritance are not. We therefore need to attach PageManager to an abstract
    superclass to ensure that it is retained by subclasses of Page.
    """
    objects = PageManager()

    class Meta:
        abstract = True


class Page(MultiTableCopyMixin, AbstractPage, index.Indexed, ClusterableModel, metaclass=PageBase):
    title = models.CharField(
        verbose_name=_('title'),
        max_length=255,
        help_text=_("The page title as you'd like it to be seen by the public")
    )
    # to reflect title of a current draft in the admin UI
    draft_title = models.CharField(
        max_length=255,
        editable=False
    )
    slug = models.SlugField(
        verbose_name=_('slug'),
        allow_unicode=True,
        max_length=255,
        help_text=_("The name of the page as it will appear in URLs e.g http://domain.com/blog/[my-slug]/")
    )
    content_type = models.ForeignKey(
        ContentType,
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
        editable=True,
        on_delete=models.SET_NULL,
        related_name='owned_pages'
    )

    seo_title = models.CharField(
        verbose_name=_("page title"),
        max_length=255,
        blank=True,
        help_text=_("Optional. 'Search Engine Friendly' title. This will appear at the top of the browser window.")
    )

    show_in_menus_default = False
    show_in_menus = models.BooleanField(
        verbose_name=_('show in menus'),
        default=False,
        help_text=_("Whether a link to this page will appear in automatically generated menus")
    )
    search_description = models.TextField(verbose_name=_('search description'), blank=True)

    go_live_at = models.DateTimeField(
        verbose_name=_("go live date/time"),
        blank=True,
        null=True
    )
    expire_at = models.DateTimeField(
        verbose_name=_("expiry date/time"),
        blank=True,
        null=True
    )
    expired = models.BooleanField(verbose_name=_('expired'), default=False, editable=False)

    locked = models.BooleanField(verbose_name=_('locked'), default=False, editable=False)
    locked_at = models.DateTimeField(verbose_name=_('locked at'), null=True, editable=False)
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('locked by'),
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name='locked_pages'
    )

    first_published_at = models.DateTimeField(
        verbose_name=_('first published at'),
        blank=True,
        null=True,
        db_index=True
    )
    last_published_at = models.DateTimeField(
        verbose_name=_('last published at'),
        null=True,
        editable=False
    )
    latest_revision_created_at = models.DateTimeField(
        verbose_name=_('latest revision created at'),
        null=True,
        editable=False
    )
    live_revision = models.ForeignKey(
        'PageRevision',
        related_name='+',
        verbose_name=_('live revision'),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False
    )

    search_fields = [
        index.SearchField('title', partial_match=True, boost=2),
        index.AutocompleteField('title'),
        index.FilterField('title'),
        index.FilterField('id'),
        index.FilterField('live'),
        index.FilterField('owner'),
        index.FilterField('content_type'),
        index.FilterField('path'),
        index.FilterField('depth'),
        index.FilterField('locked'),
        index.FilterField('show_in_menus'),
        index.FilterField('first_published_at'),
        index.FilterField('last_published_at'),
        index.FilterField('latest_revision_created_at'),
    ]

    # Do not allow plain Page instances to be created through the Wagtail admin
    is_creatable = False

    # Define the maximum number of instances this page type can have. Default to unlimited.
    max_count = None

    # Define the maximum number of instances this page can have under a specific parent. Default to unlimited.
    max_count_per_parent = None

    # An array of additional field names that will not be included when a Page is copied.
    exclude_fields_in_copy = []
    default_exclude_fields_in_copy = ['id', 'path', 'depth', 'numchild', 'url_path', 'path', 'index_entries']

    # Define these attributes early to avoid masking errors. (Issue #3078)
    # The canonical definition is in wagtailadmin.edit_handlers.
    content_panels = []
    promote_panels = []
    settings_panels = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.id:
            # this model is being newly created
            # rather than retrieved from the db;
            if not self.content_type_id:
                # set content type to correctly represent the model class
                # that this was created as
                self.content_type = ContentType.objects.get_for_model(self)
            if 'show_in_menus' not in kwargs:
                # if the value is not set on submit refer to the model setting
                self.show_in_menus = self.show_in_menus_default

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

    @staticmethod
    def _slug_is_available(slug, parent_page, page=None):
        """
        Determine whether the given slug is available for use on a child page of
        parent_page. If 'page' is passed, the slug is intended for use on that page
        (and so it will be excluded from the duplicate check).
        """
        if parent_page is None:
            # the root page's slug can be whatever it likes...
            return True

        siblings = parent_page.get_children()
        if page:
            siblings = siblings.not_page(page)

        return not siblings.filter(slug=slug).exists()

    def _get_autogenerated_slug(self, base_slug):
        candidate_slug = base_slug
        suffix = 1
        parent_page = self.get_parent()

        while not Page._slug_is_available(candidate_slug, parent_page, self):
            # try with incrementing suffix until we find a slug which is available
            suffix += 1
            candidate_slug = "%s-%d" % (base_slug, suffix)

        return candidate_slug

    def full_clean(self, *args, **kwargs):
        # Apply fixups that need to happen before per-field validation occurs

        if not self.slug:
            # Try to auto-populate slug from title
            allow_unicode = getattr(settings, 'WAGTAIL_ALLOW_UNICODE_SLUGS', True)
            base_slug = slugify(self.title, allow_unicode=allow_unicode)

            # only proceed if we get a non-empty base slug back from slugify
            if base_slug:
                self.slug = self._get_autogenerated_slug(base_slug)

        if not self.draft_title:
            self.draft_title = self.title

        super().full_clean(*args, **kwargs)

    def clean(self):
        super().clean()
        if not Page._slug_is_available(self.slug, self.get_parent(), self):
            raise ValidationError({'slug': _("This slug is already in use")})

    @transaction.atomic
    # ensure that changes are only committed when we have updated all descendant URL paths, to preserve consistency
    def save(self, clean=True, user=None, log_action=False, **kwargs):
        """
        Overrides default method behaviour to make additional updates unique to pages,
        such as updating the ``url_path`` value of descendant page to reflect changes
        to this page's slug.

        New pages should generally be saved via the ``add_child()`` or ``add_sibling()``
        method of an existing page, which will correctly set the ``path`` and ``depth``
        fields on the new page before saving it.

        By default, pages are validated using ``full_clean()`` before attempting to
        save changes to the database, which helps to preserve validity when restoring
        pages from historic revisions (which might not necessarily reflect the current
        model state). This validation step can be bypassed by calling the method with
        ``clean=False``.
        """
        if clean:
            self.full_clean()

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

        result = super().save(**kwargs)

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

        if log_action is not None:
            # The default for log_action is False. i.e. don't log unless specifically instructed
            # Page creation is a special case that we want logged by default, but allow skipping it
            # explicitly by passing log_action=None
            if is_new:
                PageLogEntry.objects.log_action(
                    instance=self,
                    action='wagtail.create',
                    user=user or self.owner,
                    content_changed=True,
                )
            elif log_action:
                PageLogEntry.objects.log_action(
                    instance=self,
                    action=log_action,
                    user=user
                )

        return result

    def delete(self, *args, **kwargs):
        # Ensure that deletion always happens on an instance of Page, not a specific subclass. This
        # works around a bug in treebeard <= 3.0 where calling SpecificPage.delete() fails to delete
        # child pages that are not instances of SpecificPage
        if type(self) is Page:
            user = kwargs.pop('user', None)

            def log_deletion(page, user):
                PageLogEntry.objects.log_action(
                    instance=page,
                    action='wagtail.delete',
                    user=user,
                    deleted=True,
                )
            if self.get_children().exists():
                for child in self.get_children():
                    log_deletion(child.specific, user)
            log_deletion(self.specific, user)

            # this is a Page instance, so carry on as we were
            return super().delete(*args, **kwargs)
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
                if field.remote_field.on_delete == models.CASCADE:
                    errors.append(
                        checks.Warning(
                            "Field hasn't specified on_delete action",
                            hint="Set on_delete=models.SET_NULL and make sure the field is nullable or set on_delete=models.PROTECT. Wagtail does not allow simple database CASCADE because it will corrupt its tree storage.",
                            obj=field,
                            id='wagtailcore.W001',
                        )
                    )

        if not isinstance(cls.objects, PageManager):
            errors.append(
                checks.Error(
                    "Manager does not inherit from PageManager",
                    hint="Ensure that custom Page managers inherit from wagtail.core.models.PageManager",
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
        (
            Page.objects
            .filter(path__startswith=self.path)
            .exclude(pk=self.pk)
            .update(
                url_path=Concat(
                    Value(new_url_path),
                    Substr('url_path', len(old_url_path) + 1)
                )
            )
        )

    @cached_property
    def specific(self):
        """
        Return this page in its most specific subclassed form.

        If called on a page object that is already an instance of the most
        specific class (e.g. an ``EventPage``), the object will be returned
        as is, and no database queries or other operations will be triggered.

        If the page was originally created using a page type that has since
        been removed from the codebase, a generic ``Page`` object will be
        returned (without any custom field values or other functionality
        present on the orginal class). Usually, deleting these pages is the
        best course of action, but there is currently no safe way for Wagtail
        to do that at migration time.
        """
        model_class = self.specific_class

        if model_class is None:
            # The codebase and database are out of sync (e.g. the model exists
            # on a different git branch and migrations were not applied or
            # reverted before switching branches). So, the best we can do is
            # return the page in it's current form.
            return self
        if isinstance(self, model_class):
            # self is already the an instance of the most specific class
            return self
        return self.cached_content_type.get_object_for_this_type(id=self.id)

    @cached_property
    def specific_class(self):
        """
        Return the class that this page would be if instantiated in its
        most specific form.

        If the model class can no longer be found in the codebase, and the
        relevant ``ContentType`` has been removed by a database migration,
        the return value will be ``Page``.

        If the model class can no longer be found in the codebase, but the
        relevant ``ContentType`` is still present in the database (usually a
        result of switching between git branches without running or reverting
        database migrations beforehand), the return value will be ``None``.
        """
        return self.cached_content_type.model_class()

    @property
    def cached_content_type(self):
        """
        versionadded:: 2.10

        Return this page's ``content_type`` value from the ``ContentType``
        model's cached manager, which will avoid a database query if the
        object is already in memory.
        """
        return ContentType.objects.get_for_id(self.content_type_id)

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

    def get_admin_display_title(self):
        """
        Return the title for this page as it should appear in the admin backend;
        override this if you wish to display extra contextual information about the page,
        such as language. By default, returns ``draft_title``.
        """
        # Fall back on title if draft_title is blank (which may happen if the page was created
        # in a fixture or migration that didn't explicitly handle draft_title)
        return self.draft_title or self.title

    def save_revision(self, user=None, submitted_for_moderation=False, approved_go_live_at=None, changed=True,
                      log_action=False, previous_revision=None):
        """
        Creates and saves a page revision.
        :param user: the user performing the action
        :param submitted_for_moderation: indicates whether the page was submitted for moderation
        :param approved_go_live_at: the date and time the revision is approved to go live
        :param changed: indicates whether there were any content changes
        :param log_action: flag for logging the action. Pass False to skip logging. Can be passed an action string.
            Defaults to 'wagtail.edit' when no 'previous_revision' param is passed, otherwise 'wagtail.revert'
        :param previous_revision: indicates a revision reversal. Should be set to the previous revision instance
        :return: the newly created revision
        """
        self.full_clean()

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

        self.draft_title = self.title
        update_fields.append('draft_title')

        if changed:
            self.has_unpublished_changes = True
            update_fields.append('has_unpublished_changes')

        if update_fields:
            self.save(update_fields=update_fields)

        # Log
        logger.info("Page edited: \"%s\" id=%d revision_id=%d", self.title, self.id, revision.id)
        if log_action:
            if not previous_revision:
                PageLogEntry.objects.log_action(
                    instance=self,
                    action=log_action if isinstance(log_action, str) else 'wagtail.edit',
                    user=user,
                    revision=revision,
                    content_changed=changed,
                )
            else:
                PageLogEntry.objects.log_action(
                    instance=self,
                    action=log_action if isinstance(log_action, str) else 'wagtail.revert',
                    user=user,
                    data={
                        'revision': {
                            'id': previous_revision.id,
                            'created': previous_revision.created_at.strftime("%d %b %Y %H:%M")
                        }
                    },
                    revision=revision,
                    content_changed=changed,
                )

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

    def unpublish(self, set_expired=False, commit=True, user=None, log_action=True):
        """
        Unpublish the page by setting ``live`` to ``False``. Does nothing if ``live`` is already ``False``
        :param log_action: flag for logging the action. Pass False to skip logging. Can be passed an action string.
            Defaults to 'wagtail.unpublish'
        """
        if self.live:
            self.live = False
            self.has_unpublished_changes = True
            self.live_revision = None

            if set_expired:
                self.expired = True

            if commit:
                # using clean=False to bypass validation
                self.save(clean=False)

            page_unpublished.send(sender=self.specific_class, instance=self.specific)

            if log_action:
                PageLogEntry.objects.log_action(
                    instance=self,
                    action=log_action if isinstance(log_action, str) else 'wagtail.unpublish',
                    user=user,
                )

            logger.info("Page unpublished: \"%s\" id=%d", self.title, self.id)

            self.revisions.update(approved_go_live_at=None)

    context_object_name = None

    def get_context(self, request, *args, **kwargs):
        context = {
            PAGE_TEMPLATE_VAR: self,
            'self': self,
            'request': request,
        }

        if self.context_object_name:
            context[self.context_object_name] = self

        return context

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

    def _get_site_root_paths(self, request=None):
        """
        Return ``Site.get_site_root_paths()``, using the cached copy on the
        request object if available.
        """
        # if we have a request, use that to cache site_root_paths; otherwise, use self
        cache_object = request if request else self
        try:
            return cache_object._wagtail_cached_site_root_paths
        except AttributeError:
            cache_object._wagtail_cached_site_root_paths = Site.get_site_root_paths()
            return cache_object._wagtail_cached_site_root_paths

    def get_url_parts(self, request=None):
        """
        Determine the URL for this page and return it as a tuple of
        ``(site_id, site_root_url, page_url_relative_to_site_root)``.
        Return None if the page is not routable.

        This is used internally by the ``full_url``, ``url``, ``relative_url``
        and ``get_site`` properties and methods; pages with custom URL routing
        should override this method in order to have those operations return
        the custom URLs.

        Accepts an optional keyword argument ``request``, which may be used
        to avoid repeated database / cache lookups. Typically, a page model
        that overrides ``get_url_parts`` should not need to deal with
        ``request`` directly, and should just pass it to the original method
        when calling ``super``.
        """

        possible_sites = [
            (pk, path, url)
            for pk, path, url in self._get_site_root_paths(request)
            if self.url_path.startswith(path)
        ]

        if not possible_sites:
            return None

        site_id, root_path, root_url = possible_sites[0]

        site = Site.find_for_request(request)
        if site:
            for site_id, root_path, root_url in possible_sites:
                if site_id == site.pk:
                    break
            else:
                site_id, root_path, root_url = possible_sites[0]

        # The page may not be routable because wagtail_serve is not registered
        # This may be the case if Wagtail is used headless
        try:
            page_path = reverse(
                'wagtail_serve', args=(self.url_path[len(root_path):],))
        except NoReverseMatch:
            return (site_id, None, None)

        # Remove the trailing slash from the URL reverse generates if
        # WAGTAIL_APPEND_SLASH is False and we're not trying to serve
        # the root path
        if not WAGTAIL_APPEND_SLASH and page_path != '/':
            page_path = page_path.rstrip('/')

        return (site_id, root_url, page_path)

    def get_full_url(self, request=None):
        """Return the full URL (including protocol / domain) to this page, or None if it is not routable"""
        url_parts = self.get_url_parts(request=request)

        if url_parts is None or url_parts[1] is None and url_parts[2] is None:
            # page is not routable
            return

        site_id, root_url, page_path = url_parts

        return root_url + page_path

    full_url = property(get_full_url)

    def get_url(self, request=None, current_site=None):
        """
        Return the 'most appropriate' URL for referring to this page from the pages we serve,
        within the Wagtail backend and actual website templates;
        this is the local URL (starting with '/') if we're only running a single site
        (i.e. we know that whatever the current page is being served from, this link will be on the
        same domain), and the full URL (with domain) if not.
        Return None if the page is not routable.

        Accepts an optional but recommended ``request`` keyword argument that, if provided, will
        be used to cache site-level URL information (thereby avoiding repeated database / cache
        lookups) and, via the ``Site.find_for_request()`` function, determine whether a relative
        or full URL is most appropriate.
        """
        # ``current_site`` is purposefully undocumented, as one can simply pass the request and get
        # a relative URL based on ``Site.find_for_request()``. Nonetheless, support it here to avoid
        # copy/pasting the code to the ``relative_url`` method below.
        if current_site is None and request is not None:
            site = Site.find_for_request(request)
            current_site = site
        url_parts = self.get_url_parts(request=request)

        if url_parts is None or url_parts[1] is None and url_parts[2] is None:
            # page is not routable
            return

        site_id, root_url, page_path = url_parts

        if (current_site is not None and site_id == current_site.id) or len(self._get_site_root_paths(request)) == 1:
            # the site matches OR we're only running a single site, so a local URL is sufficient
            return page_path
        else:
            return root_url + page_path

    url = property(get_url)

    def relative_url(self, current_site, request=None):
        """
        Return the 'most appropriate' URL for this page taking into account the site we're currently on;
        a local URL if the site matches, or a fully qualified one otherwise.
        Return None if the page is not routable.

        Accepts an optional but recommended ``request`` keyword argument that, if provided, will
        be used to cache site-level URL information (thereby avoiding repeated database / cache
        lookups).
        """
        return self.get_url(request=request, current_site=current_site)

    def get_site(self):
        """
        Return the Site object that this page belongs to.
        """

        url_parts = self.get_url_parts()

        if url_parts is None:
            # page is not routable
            return

        site_id, root_url, page_path = url_parts

        return Site.objects.get(id=site_id)

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
        can_create = cls.is_creatable and cls.can_exist_under(parent)

        if cls.max_count is not None:
            can_create = can_create and cls.objects.count() < cls.max_count

        if cls.max_count_per_parent is not None:
            can_create = can_create and parent.get_children().type(cls).count() < cls.max_count_per_parent

        return can_create

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
        return capfirst(cls._meta.verbose_name)

    @property
    def status_string(self):
        if not self.live:
            if self.expired:
                return _("expired")
            elif self.approved_schedule:
                return _("scheduled")
            elif self.workflow_in_progress:
                return _("in moderation")
            else:
                return _("draft")
        else:
            if self.approved_schedule:
                return _("live + scheduled")
            elif self.workflow_in_progress:
                return _("live + in moderation")
            elif self.has_unpublished_changes:
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

    def move(self, target, pos=None, user=None):
        """
        Extension to the treebeard 'move' method to ensure that url_path is updated,
        and to emit a 'pre_page_move' and 'post_page_move' signals.
        """
        # Determine old and new parents
        parent_before = self.get_parent()
        if pos in ('first-child', 'last-child', 'sorted-child'):
            parent_after = target
        else:
            parent_after = target.get_parent()

        # Determine old and new url_paths
        # Fetching new object to avoid affecting `self`
        old_self = Page.objects.get(id=self.id)
        old_url_path = old_self.url_path
        new_url_path = old_self.set_url_path(parent=parent_after)

        # Emit pre_page_move signal
        pre_page_move.send(
            sender=self.specific_class or self.__class__,
            instance=self,
            parent_page_before=parent_before,
            parent_page_after=parent_after,
            url_path_before=old_url_path,
            url_path_after=new_url_path,
        )

        # Only commit when all descendants are properly updated
        with transaction.atomic():
            # Allow treebeard to update `path` values
            super().move(target, pos=pos)

            # Treebeard's move method doesn't actually update the in-memory instance,
            # so we need to work with a freshly loaded one now
            new_self = Page.objects.get(id=self.id)
            new_self.url_path = new_url_path
            new_self.save()

            # Update descendant paths if url_path has changed
            if old_url_path != new_url_path:
                new_self._update_descendant_url_paths(old_url_path, new_url_path)

        # Emit post_page_move signal
        post_page_move.send(
            sender=self.specific_class or self.__class__,
            instance=new_self,
            parent_page_before=parent_before,
            parent_page_after=parent_after,
            url_path_before=old_url_path,
            url_path_after=new_url_path,
        )

        # Log
        PageLogEntry.objects.log_action(
            instance=self,
            action='wagtail.move',
            user=user,
            data={
                'source': {
                    'id': parent_before.id,
                    'title': parent_before.get_admin_display_title()
                },
                'destination': {
                    'id': parent_after.id,
                    'title': parent_after.get_admin_display_title()
                }
            }
        )
        logger.info("Page moved: \"%s\" id=%d path=%s", self.title, self.id, new_url_path)

    def copy(self, recursive=False, to=None, update_attrs=None, copy_revisions=True, keep_live=True, user=None,
             process_child_object=None, exclude_fields=None, log_action='wagtail.copy'):
        """
        Copies a given page
        :param log_action flag for logging the action. Pass None to skip logging.
            Can be passed an action string. Defaults to 'wagtail.copy'
        """

        specific_self = self.specific
        if keep_live:
            base_update_attrs = {}
        else:
            base_update_attrs = {
                'live': False,
                'has_unpublished_changes': True,
                'live_revision': None,
                'first_published_at': None,
                'last_published_at': None
            }

        if user:
            base_update_attrs['owner'] = user

        if update_attrs:
            base_update_attrs.update(update_attrs)

        page_copy, child_object_id_map = self._copy(exclude_fields=exclude_fields, update_attrs=base_update_attrs, to=to, recursive=recursive, process_child_object=process_child_object)

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

        latest_revision_as_page_revision = latest_revision.save_revision(user=user, changed=False)
        if keep_live:
            page_copy.live_revision = latest_revision_as_page_revision
            page_copy.last_published_at = latest_revision_as_page_revision.created_at
            page_copy.first_published_at = latest_revision_as_page_revision.created_at
            page_copy.save()

        # Log
        if log_action:
            parent = specific_self.get_parent()
            PageLogEntry.objects.log_action(
                instance=page_copy,
                action=log_action,
                user=user,
                data={
                    'page': {
                        'id': page_copy.id,
                        'title': page_copy.get_admin_display_title()
                    },
                    'source': {'id': parent.id, 'title': parent.get_admin_display_title()} if parent else None,
                    'destination': {'id': to.id, 'title': to.get_admin_display_title()} if to else None,
                    'keep_live': page_copy.live and keep_live
                },
            )
            if page_copy.live and keep_live:
                # Log the publish if the use chose to keep the copied page live
                PageLogEntry.objects.log_action(
                    instance=page_copy,
                    action='wagtail.publish',
                    user=user,
                    revision=latest_revision_as_page_revision,
                )
        logger.info("Page copied: \"%s\" id=%d from=%d", page_copy.title, page_copy.id, self.id)

        # Copy child pages
        if recursive:
            for child_page in self.get_children():
                child_page.specific.copy(
                    recursive=True,
                    to=page_copy,
                    copy_revisions=copy_revisions,
                    keep_live=keep_live,
                    user=user,
                    process_child_object=process_child_object,
                )

        return page_copy

    def _save_copy_instance(self, instance, to=None, recursive=False, **kwargs):
        if to:
            if recursive and (to == self or to.is_descendant_of(self)):
                raise Exception("You cannot copy a tree branch recursively into itself")
            instance = to.add_child(instance=instance)
        else:
            instance = self.add_sibling(instance=instance)
        return instance

    copy.alters_data = True

    def permissions_for_user(self, user):
        """
        Return a PagePermissionsTester object defining what actions the user can perform on this page
        """
        user_perms = UserPagePermissionsProxy(user)
        return user_perms.for_page(self)

    def make_preview_request(self, original_request=None, preview_mode=None, extra_request_attrs=None):
        """
        Simulate a request to this page, by constructing a fake HttpRequest object that is (as far
        as possible) representative of a real request to this page's front-end URL, and invoking
        serve_preview with that request (and the given preview_mode).

        Used for previewing / moderation and any other place where we
        want to display a view of this page in the admin interface without going through the regular
        page routing logic.

        If you pass in a real request object as original_request, additional information (e.g. client IP, cookies)
        will be included in the dummy request.
        """
        dummy_meta = self._get_dummy_headers(original_request)
        request = WSGIRequest(dummy_meta)

        # Add a flag to let middleware know that this is a dummy request.
        request.is_dummy = True

        if extra_request_attrs:
            for k, v in extra_request_attrs.items():
                setattr(request, k, v)

        page = self

        # Build a custom django.core.handlers.BaseHandler subclass that invokes serve_preview as
        # the eventual view function called at the end of the middleware chain, rather than going
        # through the URL resolver
        class Handler(BaseHandler):
            def _get_response(self, request):
                response = page.serve_preview(request, preview_mode)
                if hasattr(response, 'render') and callable(response.render):
                    response = response.render()
                return response

        # Invoke this custom handler.
        handler = Handler()
        handler.load_middleware()
        return handler.get_response(request)

    def _get_dummy_headers(self, original_request=None):
        """
        Return a dict of META information to be included in a faked HttpRequest object to pass to
        serve_preview.
        """
        url = self._get_dummy_header_url(original_request)
        if url:
            url_info = urlparse(url)
            hostname = url_info.hostname
            path = url_info.path
            port = url_info.port or (443 if url_info.scheme == 'https' else 80)
            scheme = url_info.scheme
        else:
            # Cannot determine a URL to this page - cobble one together based on
            # whatever we find in ALLOWED_HOSTS
            try:
                hostname = settings.ALLOWED_HOSTS[0]
                if hostname == '*':
                    # '*' is a valid value to find in ALLOWED_HOSTS[0], but it's not a valid domain name.
                    # So we pretend it isn't there.
                    raise IndexError
            except IndexError:
                hostname = 'localhost'
            path = '/'
            port = 80
            scheme = 'http'

        http_host = hostname
        if port != (443 if scheme == 'https' else 80):
            http_host = '%s:%s' % (http_host, port)
        dummy_values = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': path,
            'SERVER_NAME': hostname,
            'SERVER_PORT': port,
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'HTTP_HOST': http_host,
            'wsgi.version': (1, 0),
            'wsgi.input': StringIO(),
            'wsgi.errors': StringIO(),
            'wsgi.url_scheme': scheme,
            'wsgi.multithread': True,
            'wsgi.multiprocess': True,
            'wsgi.run_once': False,
        }

        # Add important values from the original request object, if it was provided.
        HEADERS_FROM_ORIGINAL_REQUEST = [
            'REMOTE_ADDR', 'HTTP_X_FORWARDED_FOR', 'HTTP_COOKIE', 'HTTP_USER_AGENT', 'HTTP_AUTHORIZATION',
            'wsgi.version', 'wsgi.multithread', 'wsgi.multiprocess', 'wsgi.run_once',
        ]
        if settings.SECURE_PROXY_SSL_HEADER:
            HEADERS_FROM_ORIGINAL_REQUEST.append(settings.SECURE_PROXY_SSL_HEADER[0])
        if original_request:
            for header in HEADERS_FROM_ORIGINAL_REQUEST:
                if header in original_request.META:
                    dummy_values[header] = original_request.META[header]

        return dummy_values

    def _get_dummy_header_url(self, original_request=None):
        """
        Return the URL that _get_dummy_headers() should use to set META headers
        for the faked HttpRequest.
        """
        return self.full_url

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
        """
        The preview mode to use in workflows that do not give the user the option of selecting a
        mode explicitly, e.g. moderator approval. Will raise IndexError if preview_modes is empty
        """
        return self.preview_modes[0][0]

    def is_previewable(self):
        """Returns True if at least one preview mode is specified"""
        # It's possible that this will be called from a listing page using a plain Page queryset -
        # if so, checking self.preview_modes would incorrectly give us the default set from
        # Page.preview_modes. However, accessing self.specific.preview_modes would result in an N+1
        # query problem. To avoid this (at least in the general case), we'll call .specific only if
        # a check of the property at the class level indicates that preview_modes has been
        # overridden from whatever type we're currently in.
        page = self
        if page.specific_class.preview_modes != type(page).preview_modes:
            page = page.specific

        return bool(page.preview_modes)

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

        response = self.serve(request)
        patch_cache_control(response, private=True)
        return response

    def get_cached_paths(self):
        """
        This returns a list of paths to invalidate in a frontend cache
        """
        return ['/']

    def get_sitemap_urls(self, request=None):
        return [
            {
                'location': self.get_full_url(request),
                # fall back on latest_revision_created_at if last_published_at is null
                # (for backwards compatibility from before last_published_at was added)
                'lastmod': (self.last_published_at or self.latest_revision_created_at),
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
        """
        Returns a queryset of the current page's ancestors, starting at the root page
        and descending to the parent, or to the current page itself if ``inclusive`` is true.
        """
        return Page.objects.ancestor_of(self, inclusive)

    def get_descendants(self, inclusive=False):
        """
        Returns a queryset of all pages underneath the current page, any number of levels deep.
        If ``inclusive`` is true, the current page itself is included in the queryset.
        """
        return Page.objects.descendant_of(self, inclusive)

    def get_siblings(self, inclusive=True):
        """
        Returns a queryset of all other pages with the same parent as the current page.
        If ``inclusive`` is true, the current page itself is included in the queryset.
        """
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

    def with_content_json(self, content_json):
        """
        Returns a new version of the page with field values updated to reflect changes
        in the provided ``content_json`` (which usually comes from a previously-saved
        page revision).

        Certain field values are preserved in order to prevent errors if the returned
        page is saved, such as ``id``, ``content_type`` and some tree-related values.
        The following field values are also preserved, as they are considered to be
        meaningful to the page as a whole, rather than to a specific revision:

        * ``draft_title``
        * ``live``
        * ``has_unpublished_changes``
        * ``owner``
        * ``locked``
        * ``locked_by``
        * ``locked_at``
        * ``latest_revision_created_at``
        * ``first_published_at``
        """

        obj = self.specific_class.from_json(content_json)

        # These should definitely never change between revisions
        obj.pk = self.pk
        obj.content_type = self.content_type

        # Override possibly-outdated tree parameter fields
        obj.path = self.path
        obj.depth = self.depth
        obj.numchild = self.numchild

        # Update url_path to reflect potential slug changes, but maintining the page's
        # existing tree position
        obj.set_url_path(self.get_parent())

        # Ensure other values that are meaningful for the page as a whole (rather than
        # to a specific revision) are preserved
        obj.draft_title = self.draft_title
        obj.live = self.live
        obj.has_unpublished_changes = self.has_unpublished_changes
        obj.owner = self.owner
        obj.locked = self.locked
        obj.locked_by = self.locked_by
        obj.locked_at = self.locked_at
        obj.latest_revision_created_at = self.latest_revision_created_at
        obj.first_published_at = self.first_published_at

        return obj

    @property
    def has_workflow(self):
        """Returns True if the page or an ancestor has an active workflow assigned, otherwise False"""
        return self.get_ancestors(inclusive=True).filter(workflowpage__isnull=False).filter(workflowpage__workflow__active=True).exists()

    def get_workflow(self):
        """Returns the active workflow assigned to the page or its nearest ancestor"""
        if hasattr(self, 'workflowpage') and self.workflowpage.workflow.active:
            return self.workflowpage.workflow
        else:
            try:
                workflow = self.get_ancestors().filter(workflowpage__isnull=False).filter(workflowpage__workflow__active=True).order_by(
                    '-depth').first().workflowpage.workflow
            except AttributeError:
                workflow = None
            return workflow

    @property
    def workflow_in_progress(self):
        """Returns True if a workflow is in progress on the current page, otherwise False"""
        return WorkflowState.objects.filter(page=self, status=WorkflowState.STATUS_IN_PROGRESS).exists()

    @property
    def current_workflow_state(self):
        """Returns the in progress or needs changes workflow state on this page, if it exists"""
        try:
            return WorkflowState.objects.active().get(page=self)
        except WorkflowState.DoesNotExist:
            return

    @property
    def current_workflow_task_state(self):
        """Returns (specific class of) the current task state of the workflow on this page, if it exists"""
        if self.current_workflow_state and self.current_workflow_state.status == WorkflowState.STATUS_IN_PROGRESS and self.current_workflow_state.current_task_state:
            return self.current_workflow_state.current_task_state.specific

    @property
    def current_workflow_task(self):
        """Returns (specific class of) the current task in progress on this page, if it exists"""
        if self.current_workflow_task_state:
            return self.current_workflow_task_state.task.specific

    class Meta:
        verbose_name = _('page')
        verbose_name_plural = _('pages')


class Orderable(models.Model):
    sort_order = models.IntegerField(null=True, blank=True, editable=False)
    sort_order_field = 'sort_order'

    class Meta:
        abstract = True
        ordering = ['sort_order']


class SubmittedRevisionsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(submitted_for_moderation=True)


class PageRevision(models.Model):
    page = models.ForeignKey('Page', verbose_name=_('page'), related_name='revisions', on_delete=models.CASCADE)
    submitted_for_moderation = models.BooleanField(
        verbose_name=_('submitted for moderation'),
        default=False,
        db_index=True
    )
    created_at = models.DateTimeField(db_index=True, verbose_name=_('created at'))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('user'), null=True, blank=True,
        on_delete=models.SET_NULL
    )
    content_json = models.TextField(verbose_name=_('content JSON'))
    approved_go_live_at = models.DateTimeField(
        verbose_name=_('approved go live at'),
        null=True,
        blank=True,
        db_index=True
    )

    objects = models.Manager()
    submitted_revisions = SubmittedRevisionsManager()

    def save(self, user=None, *args, **kwargs):
        # Set default value for created_at to now
        # We cannot use auto_now_add as that will override
        # any value that is set before saving
        if self.created_at is None:
            self.created_at = timezone.now()

        super().save(*args, **kwargs)
        if self.submitted_for_moderation:
            # ensure that all other revisions of this page have the 'submitted for moderation' flag unset
            self.page.revisions.exclude(id=self.id).update(submitted_for_moderation=False)

        if (
            self.approved_go_live_at is None
            and 'update_fields' in kwargs and 'approved_go_live_at' in kwargs['update_fields']
        ):
            # Log scheduled revision publish cancellation
            page = self.as_page_object()
            # go_live_at = kwargs['update_fields'][]
            PageLogEntry.objects.log_action(
                instance=page,
                action='wagtail.schedule.cancel',
                data={
                    'revision': {
                        'id': self.id,
                        'created': self.created_at.strftime("%d %b %Y %H:%M"),
                        'go_live_at': page.go_live_at.strftime("%d %b %Y %H:%M") if page.go_live_at else None,
                    }
                },
                user=user,
                revision=self,
            )

    def as_page_object(self):
        return self.page.specific.with_content_json(self.content_json)

    def approve_moderation(self, user=None):
        if self.submitted_for_moderation:
            logger.info("Page moderation approved: \"%s\" id=%d revision_id=%d", self.page.title, self.page.id, self.id)
            PageLogEntry.objects.log_action(
                instance=self.as_page_object(),
                action='wagtail.moderation.approve',
                user=user,
                revision=self,
            )
            self.publish()

    def reject_moderation(self, user=None):
        if self.submitted_for_moderation:
            logger.info("Page moderation rejected: \"%s\" id=%d revision_id=%d", self.page.title, self.page.id, self.id)
            PageLogEntry.objects.log_action(
                instance=self.as_page_object(),
                action='wagtail.moderation.reject',
                user=user,
                revision=self,
            )
            self.submitted_for_moderation = False
            self.save(update_fields=['submitted_for_moderation'])

    def is_latest_revision(self):
        if self.id is None:
            # special case: a revision without an ID is presumed to be newly-created and is thus
            # newer than any revision that might exist in the database
            return True
        latest_revision = PageRevision.objects.filter(page_id=self.page_id).order_by('-created_at', '-id').first()
        return (latest_revision == self)

    def publish(self, user=None, changed=True, log_action=True, previous_revision=None):
        """
        Publishes or schedules revision for publishing.

        :param user: the publishing user
        :param changed: indicated whether content has changed
        :param log_action:
            flag for the logging action. Pass False to skip logging. Cannot pass an action string as the method
            performs several actions: "publish", "revert" (and publish the reverted revision),
            "schedule publishing with a live revision", "schedule revision reversal publishing, with a live revision",
            "schedule publishing", "schedule revision reversal publishing"
        :param previous_revision: indicates a revision reversal. Should be set to the previous revision instance
        """
        page = self.as_page_object()

        def log_scheduling_action(revision, user=None, changed=changed):
            PageLogEntry.objects.log_action(
                instance=page,
                action='wagtail.publish.schedule',
                user=user,
                data={
                    'revision': {
                        'id': revision.id,
                        'created': revision.created_at.strftime("%d %b %Y %H:%M"),
                        'go_live_at': page.go_live_at.strftime("%d %b %Y %H:%M"),
                        'has_live_version': page.live,
                    }
                },
                revision=revision,
                content_changed=changed,
            )

        if page.go_live_at and page.go_live_at > timezone.now():
            page.has_unpublished_changes = True
            # Instead set the approved_go_live_at of this revision
            self.approved_go_live_at = page.go_live_at
            self.save()
            # And clear the the approved_go_live_at of any other revisions
            page.revisions.exclude(id=self.id).update(approved_go_live_at=None)
            # if we are updating a currently live page skip the rest
            if page.live_revision:
                # Log scheduled publishing
                if log_action:
                    log_scheduling_action(self, user, changed)

                return
            # if we have a go_live in the future don't make the page live
            page.live = False
        else:
            page.live = True
            # at this point, the page has unpublished changes iff there are newer revisions than this one
            page.has_unpublished_changes = not self.is_latest_revision()
            # If page goes live clear the approved_go_live_at of all revisions
            page.revisions.update(approved_go_live_at=None)
        page.expired = False  # When a page is published it can't be expired

        # Set first_published_at, last_published_at and live_revision
        # if the page is being published now
        if page.live:
            now = timezone.now()
            page.last_published_at = now
            page.live_revision = self

            if page.first_published_at is None:
                page.first_published_at = now

            if previous_revision:
                previous_revision_page = previous_revision.as_page_object()
                old_page_title = previous_revision_page.title if page.title != previous_revision_page.title else None
            else:
                try:
                    previous = self.get_previous()
                except PageRevision.DoesNotExist:
                    previous = None
                old_page_title = previous.page.title if previous and page.title != previous.page.title else None
        else:
            # Unset live_revision if the page is going live in the future
            page.live_revision = None

        page.save()
        self.submitted_for_moderation = False
        page.revisions.update(submitted_for_moderation=False)

        workflow_state = page.current_workflow_state
        if workflow_state and getattr(settings, 'WAGTAIL_WORKFLOW_CANCEL_ON_PUBLISH', True):
            workflow_state.cancel(user=user)

        if page.live:
            page_published.send(sender=page.specific_class, instance=page.specific, revision=self)

            if log_action:
                data = None
                if previous_revision:
                    data = {
                        'revision': {
                            'id': previous_revision.id,
                            'created': previous_revision.created_at.strftime("%d %b %Y %H:%M")
                        }
                    }

                if old_page_title:
                    data = data or {}
                    data['title'] = {
                        'old': old_page_title,
                        'new': page.title,
                    }

                    PageLogEntry.objects.log_action(
                        instance=page,
                        action='wagtail.rename',
                        user=user,
                        data=data,
                        revision=self,
                    )

                PageLogEntry.objects.log_action(
                    instance=page,
                    action=log_action if isinstance(log_action, str) else 'wagtail.publish',
                    user=user,
                    data=data,
                    revision=self,
                    content_changed=changed,
                )

            logger.info("Page published: \"%s\" id=%d revision_id=%d", page.title, page.id, self.id)
        elif page.go_live_at:
            logger.info(
                "Page scheduled for publish: \"%s\" id=%d revision_id=%d go_live_at=%s",
                page.title,
                page.id,
                self.id,
                page.go_live_at.isoformat()
            )

            if log_action:
                log_scheduling_action(self, user, changed)

    def get_previous(self):
        return self.get_previous_by_created_at(page=self.page)

    def get_next(self):
        return self.get_next_by_created_at(page=self.page)

    def __str__(self):
        return '"' + str(self.page) + '" at ' + str(self.created_at)

    class Meta:
        verbose_name = _('page revision')
        verbose_name_plural = _('page revisions')


PAGE_PERMISSION_TYPES = [
    ('add', _("Add"), _("Add/edit pages you own")),
    ('edit', _("Edit"), _("Edit any page")),
    ('publish', _("Publish"), _("Publish any page")),
    ('bulk_delete', _("Bulk delete"), _("Delete pages with children")),
    ('lock', _("Lock"), _("Lock/unlock pages you've locked")),
    ('unlock', _("Unlock"), _("Unlock any page")),
]

PAGE_PERMISSION_TYPE_CHOICES = [
    (identifier, long_label)
    for identifier, short_label, long_label in PAGE_PERMISSION_TYPES
]


class GroupPagePermission(models.Model):
    group = models.ForeignKey(Group, verbose_name=_('group'), related_name='page_permissions', on_delete=models.CASCADE)
    page = models.ForeignKey('Page', verbose_name=_('page'), related_name='group_permissions', on_delete=models.CASCADE)
    permission_type = models.CharField(
        verbose_name=_('permission type'),
        max_length=20,
        choices=PAGE_PERMISSION_TYPE_CHOICES
    )

    class Meta:
        unique_together = ('group', 'page', 'permission_type')
        verbose_name = _('group page permission')
        verbose_name_plural = _('group page permissions')

    def __str__(self):
        return "Group %d ('%s') has permission '%s' on page %d ('%s')" % (
            self.group.id, self.group,
            self.permission_type,
            self.page.id, self.page
        )


class UserPagePermissionsProxy:
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
        publishable_pages_paths = self.permissions.filter(
            permission_type='publish'
        ).values_list('page__path', flat=True).distinct()
        if not publishable_pages_paths:
            return PageRevision.objects.none()

        # compile a filter expression to apply to the PageRevision.submitted_revisions manager:
        # return only those pages whose paths start with one of the publishable_pages paths
        only_my_sections = Q(page__path__startswith=publishable_pages_paths[0])
        for page_path in publishable_pages_paths[1:]:
            only_my_sections = only_my_sections | Q(page__path__startswith=page_path)

        # return the filtered queryset
        return PageRevision.submitted_revisions.filter(only_my_sections)

    def for_page(self, page):
        """Return a PagePermissionTester object that can be used to query whether this user has
        permission to perform specific tasks on the given page"""
        return PagePermissionTester(self, page)

    def explorable_pages(self):
        """Return a queryset of pages that the user has access to view in the
        explorer (e.g. add/edit/publish permission). Includes all pages with
        specific group permissions and also the ancestors of those pages (in
        order to enable navigation in the explorer)"""
        # Deal with the trivial cases first...
        if not self.user.is_active:
            return Page.objects.none()
        if self.user.is_superuser:
            return Page.objects.all()

        explorable_pages = Page.objects.none()

        # Creates a union queryset of all objects the user has access to add,
        # edit and publish
        for perm in self.permissions.filter(
            Q(permission_type="add")
            | Q(permission_type="edit")
            | Q(permission_type="publish")
            | Q(permission_type="lock")
        ):
            explorable_pages |= Page.objects.descendant_of(
                perm.page, inclusive=True
            )

        # For all pages with specific permissions, add their ancestors as
        # explorable. This will allow deeply nested pages to be accessed in the
        # explorer. For example, in the hierarchy A>B>C>D where the user has
        # 'edit' access on D, they will be able to navigate to D without having
        # explicit access to A, B or C.
        page_permissions = Page.objects.filter(group_permissions__in=self.permissions)
        for page in page_permissions:
            explorable_pages |= page.get_ancestors()

        # Remove unnecessary top-level ancestors that the user has no access to
        fca_page = page_permissions.first_common_ancestor()
        explorable_pages = explorable_pages.filter(path__startswith=fca_page.path)

        return explorable_pages

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

    def can_remove_locks(self):
        """Returns True if the user has permission to unlock pages they have not locked"""
        if self.user.is_superuser:
            return True
        if not self.user.is_active:
            return False
        else:
            return self.permissions.filter(permission_type='unlock').exists()


class PagePermissionTester:
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

    def user_has_lock(self):
        return self.page.locked_by_id == self.user.pk

    def page_locked(self):
        if self.page.current_workflow_task:
            if self.page.current_workflow_task.page_locked_for_user(self.page, self.user):
                return True

        if not self.page.locked:
            # Page is not locked
            return False

        if getattr(settings, 'WAGTAILADMIN_GLOBAL_PAGE_EDIT_LOCK', False):
            # All locks are global
            return True
        else:
            # Locked only if the current user was not the one who locked the page
            return not self.user_has_lock()

    def can_add_subpage(self):
        if not self.user.is_active:
            return False
        specific_class = self.page.specific_class
        if specific_class is None or not specific_class.creatable_subpage_models():
            return False
        return self.user.is_superuser or ('add' in self.permissions)

    def can_edit(self):
        if not self.user.is_active:
            return False

        if self.page_is_root:  # root node is not a page and can never be edited, even by superusers
            return False

        if self.user.is_superuser:
            return True

        if 'edit' in self.permissions:
            return True

        if 'add' in self.permissions and self.page.owner_id == self.user.pk:
            return True

        if self.page.current_workflow_task:
            if self.page.current_workflow_task.user_can_access_editor(self.page, self.user):
                return True

        return False

    def can_delete(self, ignore_bulk=False):
        if not self.user.is_active:
            return False

        if self.page_is_root:  # root node is not a page and can never be deleted, even by superusers
            return False

        if self.user.is_superuser:
            # superusers require no further checks
            return True

        # if the user does not have bulk_delete permission, they may only delete leaf pages
        if 'bulk_delete' not in self.permissions and not self.page.is_leaf() and not ignore_bulk:
            return False

        if 'edit' in self.permissions:
            # if the user does not have publish permission, we also need to confirm that there
            # are no published pages here
            if 'publish' not in self.permissions:
                pages_to_delete = self.page.get_descendants(inclusive=True)
                if pages_to_delete.live().exists():
                    return False

            return True

        elif 'add' in self.permissions:
            pages_to_delete = self.page.get_descendants(inclusive=True)
            if 'publish' in self.permissions:
                # we don't care about live state, but all pages must be owned by this user
                # (i.e. eliminating pages owned by this user must give us the empty set)
                return not pages_to_delete.exclude(owner=self.user).exists()
            else:
                # all pages must be owned by this user and non-live
                # (i.e. eliminating non-live pages owned by this user must give us the empty set)
                return not pages_to_delete.exclude(live=False, owner=self.user).exists()

        else:
            return False

    def can_unpublish(self):
        if not self.user.is_active:
            return False
        if (not self.page.live) or self.page_is_root:
            return False
        if self.page_locked():
            return False

        return self.user.is_superuser or ('publish' in self.permissions)

    def can_publish(self):
        if not self.user.is_active:
            return False
        if self.page_is_root:
            return False

        return self.user.is_superuser or ('publish' in self.permissions)

    def can_submit_for_moderation(self):
        return not self.page_locked() and self.page.has_workflow and not self.page.workflow_in_progress

    def can_set_view_restrictions(self):
        return self.can_publish()

    def can_unschedule(self):
        return self.can_publish()

    def can_lock(self):
        if self.user.is_superuser:
            return True

        if self.page.current_workflow_task:
            return self.page.current_workflow_task.user_can_lock(self.page, self.user)

        if 'lock' in self.permissions:
            return True

        return False

    def can_unlock(self):
        if self.user.is_superuser:
            return True

        if self.user_has_lock():
            return True

        if self.page.current_workflow_task:
            return self.page.current_workflow_task.user_can_unlock(self.page, self.user)

        if 'unlock' in self.permissions:
            return True

        return False

    def can_publish_subpage(self):
        """
        Niggly special case for creating and publishing a page in one go.
        Differs from can_publish in that we want to be able to publish subpages of root, but not
        to be able to publish root itself. (Also, can_publish_subpage returns false if the page
        does not allow subpages at all.)
        """
        if not self.user.is_active:
            return False
        specific_class = self.page.specific_class
        if specific_class is None or not specific_class.creatable_subpage_models():
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
        return self.can_delete(ignore_bulk=True)

    def can_copy(self):
        return not self.page_is_root

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

    def can_copy_to(self, destination, recursive=False):
        # reject the logically impossible cases first
        # recursive can't copy to the same tree otherwise it will be on infinite loop
        if recursive and (self.page == destination or destination.is_descendant_of(self.page)):
            return False

        # reject inactive users early
        if not self.user.is_active:
            return False

        # reject early if pages of this type cannot be created at the destination
        if not self.page.specific_class.can_create_at(destination):
            return False

        # skip permission checking for super users
        if self.user.is_superuser:
            return True

        # Inspect permissions on the destination
        destination_perms = self.user_perms.for_page(destination)

        if not destination.specific_class.creatable_subpage_models():
            return False

        # we always need at least add permission in the target
        if 'add' not in destination_perms.permissions:
            return False

        return True

    def can_view_revisions(self):
        return not self.page_is_root


class BaseViewRestriction(models.Model):
    NONE = 'none'
    PASSWORD = 'password'
    GROUPS = 'groups'
    LOGIN = 'login'

    RESTRICTION_CHOICES = (
        (NONE, _("Public")),
        (LOGIN, _("Private, accessible to logged-in users")),
        (PASSWORD, _("Private, accessible with the following password")),
        (GROUPS, _("Private, accessible to users in specific groups")),
    )

    restriction_type = models.CharField(
        max_length=20, choices=RESTRICTION_CHOICES)
    password = models.CharField(verbose_name=_('password'), max_length=255, blank=True)
    groups = models.ManyToManyField(Group, verbose_name=_('groups'), blank=True)

    def accept_request(self, request):
        if self.restriction_type == BaseViewRestriction.PASSWORD:
            passed_restrictions = request.session.get(self.passed_view_restrictions_session_key, [])
            if self.id not in passed_restrictions:
                return False

        elif self.restriction_type == BaseViewRestriction.LOGIN:
            if not request.user.is_authenticated:
                return False

        elif self.restriction_type == BaseViewRestriction.GROUPS:
            if not request.user.is_superuser:
                current_user_groups = request.user.groups.all()

                if not any(group in current_user_groups for group in self.groups.all()):
                    return False

        return True

    def mark_as_passed(self, request):
        """
        Update the session data in the request to mark the user as having passed this
        view restriction
        """
        has_existing_session = (settings.SESSION_COOKIE_NAME in request.COOKIES)
        passed_restrictions = request.session.setdefault(self.passed_view_restrictions_session_key, [])
        if self.id not in passed_restrictions:
            passed_restrictions.append(self.id)
            request.session[self.passed_view_restrictions_session_key] = passed_restrictions
        if not has_existing_session:
            # if this is a session we've created, set it to expire at the end
            # of the browser session
            request.session.set_expiry(0)

    class Meta:
        abstract = True
        verbose_name = _('view restriction')
        verbose_name_plural = _('view restrictions')

    def save(self, user=None, specific_instance=None, **kwargs):
        """
        Custom save handler to include logging.
        :param user: the user add/updating the view restriction
        :param specific_instance: the specific model instance the restriction applies to
        """
        is_new = self.id is None
        super().save(**kwargs)

        if specific_instance:
            PageLogEntry.objects.log_action(
                instance=specific_instance,
                action='wagtail.view_restriction.create' if is_new else 'wagtail.view_restriction.edit',
                user=user,
                data={
                    'restriction': {
                        'type': self.restriction_type,
                        'title': force_str(dict(self.RESTRICTION_CHOICES).get(self.restriction_type))
                    }
                }
            )

    def delete(self, user=None, specific_instance=None, **kwargs):
        """
        Custom delete handler to aid in logging
        :param user: the user removing the view restriction
        :param specific_instance: the specific model instance the restriction applies to
        """
        if specific_instance:
            PageLogEntry.objects.log_action(
                instance=specific_instance,
                action='wagtail.view_restriction.delete',
                user=user,
                data={
                    'restriction': {
                        'type': self.restriction_type,
                        'title': force_str(dict(self.RESTRICTION_CHOICES).get(self.restriction_type))
                    }
                }
            )
        return super().delete(**kwargs)


class PageViewRestriction(BaseViewRestriction):
    page = models.ForeignKey(
        'Page', verbose_name=_('page'), related_name='view_restrictions', on_delete=models.CASCADE
    )

    passed_view_restrictions_session_key = 'passed_page_view_restrictions'

    class Meta:
        verbose_name = _('page view restriction')
        verbose_name_plural = _('page view restrictions')

    def save(self, user=None, **kwargs):
        return super().save(user, specific_instance=self.page.specific, **kwargs)

    def delete(self, user=None, **kwargs):
        return super().delete(user, specific_instance=self.page.specific, **kwargs)


class BaseCollectionManager(models.Manager):
    def get_queryset(self):
        return TreeQuerySet(self.model).order_by('path')


CollectionManager = BaseCollectionManager.from_queryset(TreeQuerySet)


class CollectionViewRestriction(BaseViewRestriction):
    collection = models.ForeignKey(
        'Collection',
        verbose_name=_('collection'),
        related_name='view_restrictions',
        on_delete=models.CASCADE
    )

    passed_view_restrictions_session_key = 'passed_collection_view_restrictions'

    class Meta:
        verbose_name = _('collection view restriction')
        verbose_name_plural = _('collection view restrictions')


class Collection(MP_Node):
    """
    A location in which resources such as images and documents can be grouped
    """
    name = models.CharField(max_length=255, verbose_name=_('name'))

    objects = CollectionManager()

    def __str__(self):
        return self.name

    def get_ancestors(self, inclusive=False):
        return Collection.objects.ancestor_of(self, inclusive)

    def get_descendants(self, inclusive=False):
        return Collection.objects.descendant_of(self, inclusive)

    def get_siblings(self, inclusive=True):
        return Collection.objects.sibling_of(self, inclusive)

    def get_next_siblings(self, inclusive=False):
        return self.get_siblings(inclusive).filter(path__gte=self.path).order_by('path')

    def get_prev_siblings(self, inclusive=False):
        return self.get_siblings(inclusive).filter(path__lte=self.path).order_by('-path')

    def get_view_restrictions(self):
        """Return a query set of all collection view restrictions that apply to this collection"""
        return CollectionViewRestriction.objects.filter(collection__in=self.get_ancestors(inclusive=True))

    @staticmethod
    def order_for_display(queryset):
        return queryset.annotate(
            display_order=Case(
                When(depth=1, then=Value('')),
                default='name')
        ).order_by('display_order')

    class Meta:
        verbose_name = _('collection')
        verbose_name_plural = _('collections')


def get_root_collection_id():
    return Collection.get_first_root_node().id


class CollectionMember(models.Model):
    """
    Base class for models that are categorised into collections
    """
    collection = models.ForeignKey(
        Collection,
        default=get_root_collection_id,
        verbose_name=_('collection'),
        related_name='+',
        on_delete=models.CASCADE
    )

    search_fields = [
        index.FilterField('collection'),
    ]

    class Meta:
        abstract = True


class GroupCollectionPermission(models.Model):
    """
    A rule indicating that a group has permission for some action (e.g. "create document")
    within a specified collection.
    """
    group = models.ForeignKey(
        Group,
        verbose_name=_('group'),
        related_name='collection_permissions',
        on_delete=models.CASCADE
    )
    collection = models.ForeignKey(
        Collection,
        verbose_name=_('collection'),
        related_name='group_permissions',
        on_delete=models.CASCADE
    )
    permission = models.ForeignKey(
        Permission,
        verbose_name=_('permission'),
        on_delete=models.CASCADE
    )

    def __str__(self):
        return "Group %d ('%s') has permission '%s' on collection %d ('%s')" % (
            self.group.id, self.group,
            self.permission,
            self.collection.id, self.collection
        )

    class Meta:
        unique_together = ('group', 'collection', 'permission')
        verbose_name = _('group collection permission')
        verbose_name_plural = _('group collection permissions')


class WorkflowPage(models.Model):
    page = models.OneToOneField(
        'Page',
        verbose_name=_('page'),
        on_delete=models.CASCADE,
        primary_key=True,
        unique=True
    )
    workflow = models.ForeignKey(
        'Workflow',
        related_name='workflow_pages',
        verbose_name=_('workflow'),
        on_delete=models.CASCADE,
    )

    def get_pages(self):
        """
        Returns a queryset of pages that are affected by this WorkflowPage link.

        This includes all descendants of the page excluding any that have other WorkflowPages.
        """
        descendant_pages = Page.objects.descendant_of(self.page, inclusive=True)
        descendant_workflow_pages = WorkflowPage.objects.filter(page_id__in=descendant_pages.values_list('id', flat=True)).exclude(pk=self.pk)

        for path, depth in descendant_workflow_pages.values_list('page__path', 'page__depth'):
            descendant_pages = descendant_pages.exclude(path__startswith=path, depth__gte=depth)

        return descendant_pages

    class Meta:
        verbose_name = _('workflow page')
        verbose_name_plural = _('workflow pages')


class WorkflowTask(Orderable):
    workflow = ParentalKey('Workflow', on_delete=models.CASCADE, verbose_name=_('workflow_tasks'),
                           related_name='workflow_tasks')
    task = models.ForeignKey('Task', on_delete=models.CASCADE, verbose_name=_('task'), related_name='workflow_tasks',
                             limit_choices_to={'active': True})

    class Meta(Orderable.Meta):
        unique_together = [('workflow', 'task')]
        verbose_name = _('workflow task order')
        verbose_name_plural = _('workflow task orders')


class TaskManager(models.Manager):
    def active(self):
        return self.filter(active=True)


class Task(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('name'))
    content_type = models.ForeignKey(
        ContentType,
        verbose_name=_('content type'),
        related_name='wagtail_tasks',
        on_delete=models.CASCADE
    )
    active = models.BooleanField(verbose_name=_('active'), default=True, help_text=_(
        "Active tasks can be added to workflows. Deactivating a task does not remove it from existing workflows."))
    objects = TaskManager()

    admin_form_fields = ['name']
    admin_form_readonly_on_edit_fields = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.id:
            # this model is being newly created
            # rather than retrieved from the db;
            if not self.content_type_id:
                # set content type to correctly represent the model class
                # that this was created as
                self.content_type = ContentType.objects.get_for_model(self)

    def __str__(self):
        return self.name

    @property
    def workflows(self):
        """Returns all ``Workflow`` instances that use this task"""
        return Workflow.objects.filter(workflow_tasks__task=self)

    @property
    def active_workflows(self):
        """Return a ``QuerySet``` of active workflows that this task is part of"""
        return Workflow.objects.active().filter(workflow_tasks__task=self)

    @classmethod
    def get_verbose_name(cls):
        """
        Returns the human-readable "verbose name" of this task model e.g "Group approval task".
        """
        # This is similar to doing cls._meta.verbose_name.title()
        # except this doesn't convert any characters to lowercase
        return capfirst(cls._meta.verbose_name)

    @cached_property
    def specific(self):
        """
        Return this Task in its most specific subclassed form.
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

    task_state_class = None

    @classmethod
    def get_task_state_class(self):
        return self.task_state_class or TaskState

    def start(self, workflow_state, user=None):
        """Start this task on the provided workflow state by creating an instance of TaskState"""
        task_state = self.get_task_state_class()(workflow_state=workflow_state)
        task_state.status = TaskState.STATUS_IN_PROGRESS
        task_state.page_revision = workflow_state.page.get_latest_revision()
        task_state.task = self
        task_state.save()
        task_submitted.send(sender=task_state.specific.__class__, instance=task_state.specific, user=user)
        return task_state

    @transaction.atomic
    def on_action(self, task_state, user, action_name, **kwargs):
        """Performs an action on a task state determined by the ``action_name`` string passed"""
        if action_name == 'approve':
            task_state.approve(user=user, **kwargs)
        elif action_name == 'reject':
            task_state.reject(user=user, **kwargs)

    def user_can_access_editor(self, page, user):
        """Returns True if a user who would not normally be able to access the editor for the page should be able to if the page is currently on this task.
        Note that returning False does not remove permissions from users who would otherwise have them."""
        return False

    def page_locked_for_user(self, page, user):
        """Returns True if the page should be locked to a given user's edits. This can be used to prevent editing by non-reviewers."""
        return False

    def user_can_lock(self, page, user):
        """Returns True if a user who would not normally be able to lock the page should be able to if the page is currently on this task.
        Note that returning False does not remove permissions from users who would otherwise have them."""
        return False

    def user_can_unlock(self, page, user):
        """Returns True if a user who would not normally be able to unlock the page should be able to if the page is currently on this task.
        Note that returning False does not remove permissions from users who would otherwise have them."""
        return False

    def get_actions(self, page, user):
        """
        Get the list of action strings (name, verbose_name, whether the action requires additional data - see
        ``get_form_for_action``) for actions the current user can perform for this task on the given page.
        These strings should be the same as those able to be passed to ``on_action``
        """
        return []

    def get_form_for_action(self, action):
        return TaskStateCommentForm

    def get_template_for_action(self, action):
        return ''

    def get_task_states_user_can_moderate(self, user, **kwargs):
        """Returns a ``QuerySet`` of the task states the current user can moderate"""
        return TaskState.objects.none()

    @classmethod
    def get_description(cls):
        """Returns the task description."""
        return ''

    @transaction.atomic
    def deactivate(self, user=None):
        """Set ``active`` to False and cancel all in progress task states linked to this task"""
        self.active = False
        self.save()
        in_progress_states = TaskState.objects.filter(task=self, status=TaskState.STATUS_IN_PROGRESS)
        for state in in_progress_states:
            state.cancel(user=user)

    class Meta:
        verbose_name = _('task')
        verbose_name_plural = _('tasks')


class WorkflowManager(models.Manager):
    def active(self):
        return self.filter(active=True)


class Workflow(ClusterableModel):
    name = models.CharField(max_length=255, verbose_name=_('name'))
    active = models.BooleanField(verbose_name=_('active'), default=True, help_text=_(
        "Active workflows can be added to pages. Deactivating a workflow does not remove it from existing pages."))
    objects = WorkflowManager()

    def __str__(self):
        return self.name

    @property
    def tasks(self):
        """Returns all ``Task`` instances linked to this workflow"""
        return Task.objects.filter(workflow_tasks__workflow=self).order_by('workflow_tasks__sort_order')

    @transaction.atomic
    def start(self, page, user):
        """Initiates a workflow by creating an instance of ``WorkflowState``"""
        state = WorkflowState(page=page, workflow=self, status=WorkflowState.STATUS_IN_PROGRESS, requested_by=user)
        state.save()
        state.update(user=user)
        workflow_submitted.send(sender=state.__class__, instance=state, user=user)

        next_task_data = None
        if state.current_task_state:
            next_task_data = {
                'id': state.current_task_state.task.id,
                'title': state.current_task_state.task.name,
            }
        PageLogEntry.objects.log_action(
            instance=page,
            action='wagtail.workflow.start',
            data={
                'workflow': {
                    'id': self.id,
                    'title': self.name,
                    'status': state.status,
                    'next': next_task_data,
                    'task_state_id': state.current_task_state.id if state.current_task_state else None,
                }
            },
            revision=page.get_latest_revision(),
            user=user,
        )

        return state

    @transaction.atomic
    def deactivate(self, user=None):
        """Sets the workflow as inactive, and cancels all in progress instances of ``WorkflowState`` linked to this workflow"""
        self.active = False
        in_progress_states = WorkflowState.objects.filter(workflow=self, status=WorkflowState.STATUS_IN_PROGRESS)
        for state in in_progress_states:
            state.cancel(user=user)
        WorkflowPage.objects.filter(workflow=self).delete()
        self.save()

    def all_pages(self):
        """
        Returns a queryset of all the pages that this Workflow applies to.
        """
        pages = Page.objects.none()

        for workflow_page in self.workflow_pages.all():
            pages |= workflow_page.get_pages()

        return pages

    class Meta:
        verbose_name = _('workflow')
        verbose_name_plural = _('workflows')


class GroupApprovalTask(Task):
    groups = models.ManyToManyField(Group, verbose_name=_('groups'), help_text=_('Pages at this step in a workflow will be moderated or approved by these groups of users'))

    admin_form_fields = Task.admin_form_fields + ['groups']
    admin_form_widgets = {
        'groups': forms.CheckboxSelectMultiple,
    }

    def start(self, workflow_state, user=None):
        if workflow_state.page.locked_by:
            # If the person who locked the page isn't in one of the groups, unlock the page
            if not workflow_state.page.locked_by.groups.filter(id__in=self.groups.all()).exists():
                workflow_state.page.locked = False
                workflow_state.page.locked_by = None
                workflow_state.page.locked_at = None
                workflow_state.page.save(update_fields=['locked', 'locked_by', 'locked_at'])

        return super().start(workflow_state, user=user)

    def user_can_access_editor(self, page, user):
        return self.groups.filter(id__in=user.groups.all()).exists() or user.is_superuser

    def page_locked_for_user(self, page, user):
        return not (self.groups.filter(id__in=user.groups.all()).exists() or user.is_superuser)

    def user_can_lock(self, page, user):
        return self.groups.filter(id__in=user.groups.all()).exists()

    def user_can_unlock(self, page, user):
        return False

    def get_actions(self, page, user):
        if self.groups.filter(id__in=user.groups.all()).exists() or user.is_superuser:
            return [
                ('reject', _("Request changes"), True),
                ('approve', _("Approve"), False),
                ('approve', _("Approve with comment"), True),
            ]

        return []

    def get_task_states_user_can_moderate(self, user, **kwargs):
        if self.groups.filter(id__in=user.groups.all()).exists() or user.is_superuser:
            return TaskState.objects.filter(status=TaskState.STATUS_IN_PROGRESS, task=self.task_ptr)
        else:
            return TaskState.objects.none()

    @classmethod
    def get_description(cls):
        return _("Members of the chosen Wagtail Groups can approve this task")

    class Meta:
        verbose_name = _('Group approval task')
        verbose_name_plural = _('Group approval tasks')


class WorkflowStateManager(models.Manager):
    def active(self):
        """
        Filters to only STATUS_IN_PROGRESS and STATUS_NEEDS_CHANGES WorkflowStates
        """
        return self.filter(Q(status=WorkflowState.STATUS_IN_PROGRESS) | Q(status=WorkflowState.STATUS_NEEDS_CHANGES))


class WorkflowState(models.Model):
    """Tracks the status of a started Workflow on a Page."""
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_APPROVED = 'approved'
    STATUS_NEEDS_CHANGES = 'needs_changes'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = (
        (STATUS_IN_PROGRESS, _("In progress")),
        (STATUS_APPROVED, _("Approved")),
        (STATUS_NEEDS_CHANGES, _("Needs changes")),
        (STATUS_CANCELLED, _("Cancelled")),
    )

    page = models.ForeignKey('Page', on_delete=models.CASCADE, verbose_name=_("page"), related_name='workflow_states')
    workflow = models.ForeignKey('Workflow', on_delete=models.CASCADE, verbose_name=_('workflow'), related_name='workflow_states')
    status = models.fields.CharField(choices=STATUS_CHOICES, verbose_name=_("status"), max_length=50, default=STATUS_IN_PROGRESS)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                     verbose_name=_('requested by'),
                                     null=True,
                                     blank=True,
                                     editable=True,
                                     on_delete=models.SET_NULL,
                                     related_name='requested_workflows')
    current_task_state = models.OneToOneField('TaskState', on_delete=models.SET_NULL, null=True, blank=True,
                                              verbose_name=_("current task state"))

    # allows a custom function to be called on finishing the Workflow successfully.
    on_finish = import_string(getattr(settings, 'WAGTAIL_FINISH_WORKFLOW_ACTION', 'wagtail.core.workflows.publish_workflow_state'))

    objects = WorkflowStateManager()

    def clean(self):
        super().clean()

        if self.status in (self.STATUS_IN_PROGRESS, self.STATUS_NEEDS_CHANGES):
            # The unique constraint is conditional, and so not supported on the MySQL backend - so an additional check is done here
            if WorkflowState.objects.active().filter(page=self.page).exclude(pk=self.pk).exists():
                raise ValidationError(_('There may only be one in progress or needs changes workflow state per page.'))

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return _("Workflow '{0}' on Page '{1}': {2}").format(self.workflow, self.page, self.status)

    def resume(self, user=None):
        """Put a STATUS_NEEDS_CHANGES workflow state back into STATUS_IN_PROGRESS, and restart the current task"""
        if self.status != self.STATUS_NEEDS_CHANGES:
            raise PermissionDenied
        revision = self.current_task_state.page_revision
        current_task_state = self.current_task_state
        self.current_task_state = None
        self.status = self.STATUS_IN_PROGRESS
        self.save()

        PageLogEntry.objects.log_action(
            instance=self.page.specific,
            action='wagtail.workflow.resume',
            data={
                'workflow': {
                    'id': self.workflow_id,
                    'title': self.workflow.name,
                    'status': self.status,
                    'task_state_id': current_task_state.id,
                    'task': {
                        'id': current_task_state.task.id,
                        'title': current_task_state.task.name,
                    },
                }
            },
            revision=revision,
            user=user,
        )
        return self.update(user=user, next_task=current_task_state.task)

    def user_can_cancel(self, user):
        if self.page.locked and self.page.locked_by != user:
            return False
        return user == self.requested_by or user == self.page.owner or (self.current_task_state and self.current_task_state.status == self.current_task_state.STATUS_IN_PROGRESS and 'approve' in [action[0] for action in self.current_task_state.task.get_actions(self.page, user)])

    def update(self, user=None, next_task=None):
        """Checks the status of the current task, and progresses (or ends) the workflow if appropriate. If the workflow progresses,
        next_task will be used to start a specific task next if provided."""
        if self.status != self.STATUS_IN_PROGRESS:
            # Updating a completed or cancelled workflow should have no effect
            return
        try:
            current_status = self.current_task_state.status
        except AttributeError:
            current_status = None
        if current_status == TaskState.STATUS_REJECTED:
            self.status = self.STATUS_NEEDS_CHANGES
            self.save()
            workflow_rejected.send(sender=self.__class__, instance=self, user=user)
        else:
            if not next_task:
                next_task = self.get_next_task()
            if next_task:
                if (not self.current_task_state) or self.current_task_state.status != self.current_task_state.STATUS_IN_PROGRESS:
                    # if not on a task, or the next task to move to is not the current task (ie current task's status is
                    # not STATUS_IN_PROGRESS), move to the next task
                    self.current_task_state = next_task.specific.start(self, user=user)
                    self.save()
                    # if task has auto-approved, update the workflow again
                    if self.current_task_state.status != self.current_task_state.STATUS_IN_PROGRESS:
                        self.update(user=user)
                # otherwise, continue on the current task
            else:
                # if there is no uncompleted task, finish the workflow.
                self.finish(user=user)

    @property
    def successful_task_states(self):
        successful_task_states = self.task_states.filter(
            Q(status=TaskState.STATUS_APPROVED) | Q(status=TaskState.STATUS_SKIPPED)
        )
        if getattr(settings, "WAGTAIL_WORKFLOW_REQUIRE_REAPPROVAL_ON_EDIT", False):
            successful_task_states = successful_task_states.filter(page_revision=self.page.get_latest_revision())

        return successful_task_states

    def get_next_task(self):
        """Returns the next active task, which has not been either approved or skipped"""

        return (
            Task.objects.filter(workflow_tasks__workflow=self.workflow, active=True)
            .exclude(
                task_states__in=self.successful_task_states
            ).order_by('workflow_tasks__sort_order').first()
        )

    def cancel(self, user=None):
        """Cancels the workflow state"""
        if self.status not in (self.STATUS_IN_PROGRESS, self.STATUS_NEEDS_CHANGES):
            raise PermissionDenied
        self.status = self.STATUS_CANCELLED
        self.save()

        PageLogEntry.objects.log_action(
            instance=self.page.specific,
            action='wagtail.workflow.cancel',
            data={
                'workflow': {
                    'id': self.workflow_id,
                    'title': self.workflow.name,
                    'status': self.status,
                    'task_state_id': self.current_task_state.id,
                    'task': {
                        'id': self.current_task_state.task.id,
                        'title': self.current_task_state.task.name,
                    },
                }
            },
            revision=self.current_task_state.page_revision,
            user=user,
        )

        for state in self.task_states.filter(status=TaskState.STATUS_IN_PROGRESS):
            # Cancel all in progress task states
            state.specific.cancel(user=user)
        workflow_cancelled.send(sender=self.__class__, instance=self, user=user)

    @transaction.atomic
    def finish(self, user=None):
        """Finishes a successful in progress workflow, marking it as approved and performing the ``on_finish`` action"""
        if self.status != self.STATUS_IN_PROGRESS:
            raise PermissionDenied
        self.status = self.STATUS_APPROVED
        self.save()
        self.on_finish(user=user)
        workflow_approved.send(sender=self.__class__, instance=self, user=user)

    def copy_approved_task_states_to_revision(self, revision):
        """This creates copies of previously approved task states with page_revision set to a different revision."""
        approved_states = TaskState.objects.filter(workflow_state=self, status=TaskState.STATUS_APPROVED)
        for state in approved_states:
            state.copy(update_attrs={'page_revision': revision})

    def revisions(self):
        """Returns all page revisions associated with task states linked to the current workflow state"""
        return PageRevision.objects.filter(
            page_id=self.page_id,
            id__in=self.task_states.values_list('page_revision_id', flat=True)
        ).defer('content_json')

    def _get_applicable_task_states(self):
        """Returns the set of task states whose status applies to the current revision"""

        task_states = TaskState.objects.filter(workflow_state_id=self.id)
        # If WAGTAIL_WORKFLOW_REQUIRE_REAPPROVAL_ON_EDIT=True, this is only task states created on the current revision
        if getattr(settings, "WAGTAIL_WORKFLOW_REQUIRE_REAPPROVAL_ON_EDIT", False):
            latest_revision_id = self.revisions().order_by('-created_at', '-id').values_list('id', flat=True).first()
            task_states = task_states.filter(page_revision_id=latest_revision_id)
        return task_states

    def all_tasks_with_status(self):
        """
        Returns a list of Task objects that are linked with this workflow state's
        workflow. The status of that task in this workflow state is annotated in the
        `.status` field. And a displayable version of that status is annotated in the
        `.status_display` field.

        This is different to querying TaskState as it also returns tasks that haven't
        been started yet (so won't have a TaskState).
        """
        # Get the set of task states whose status applies to the current revision
        task_states = self._get_applicable_task_states()

        tasks = list(
            self.workflow.tasks.annotate(
                status=Subquery(
                    task_states.filter(
                        task_id=OuterRef('id'),
                    ).order_by(
                        '-started_at', '-id'
                    ).values('status')[:1]
                ),
            )
        )

        # Manually annotate status_display
        status_choices = dict(TaskState.STATUS_CHOICES)
        for task in tasks:
            task.status_display = status_choices.get(task.status, _("Not started"))

        return tasks

    def all_tasks_with_state(self):
        """
        Returns a list of Task objects that are linked with this WorkflowState's
        workflow, and have the latest task state.

        In a "Submit for moderation -> reject at step 1 -> resubmit -> accept" workflow, this ensures
        the task list reflects the accept, rather than the reject.
        """
        task_states = self._get_applicable_task_states()

        tasks = list(
            self.workflow.tasks.annotate(
                task_state_id=Subquery(
                    task_states.filter(
                        task_id=OuterRef('id'),
                    ).order_by(
                        '-started_at', '-id'
                    ).values('id')[:1]
                ),
            )
        )

        task_states = {task_state.id: task_state for task_state in task_states}
        # Manually annotate task_state
        for task in tasks:
            task.task_state = task_states.get(task.task_state_id)

        return tasks

    @property
    def is_active(self):
        return self.status not in [self.STATUS_APPROVED, self.STATUS_CANCELLED]

    @property
    def is_at_final_task(self):
        """Returns the next active task, which has not been either approved or skipped"""

        last_task = Task.objects.filter(workflow_tasks__workflow=self.workflow, active=True)\
            .exclude(task_states__in=self.successful_task_states)\
            .order_by('workflow_tasks__sort_order').last()

        return self.get_next_task() == last_task

    class Meta:
        verbose_name = _('Workflow state')
        verbose_name_plural = _('Workflow states')
        # prevent multiple STATUS_IN_PROGRESS/STATUS_NEEDS_CHANGES workflows for the same page. This is not supported by MySQL, so is checked additionally on save.
        constraints = [
            models.UniqueConstraint(fields=['page'], condition=(Q(status='in_progress') | Q(status='needs_changes')), name='unique_in_progress_workflow')
        ]


class TaskStateManager(models.Manager):
    def reviewable_by(self, user):
        tasks = Task.objects.filter(active=True)
        states = TaskState.objects.none()
        for task in tasks:
            states = states | task.specific.get_task_states_user_can_moderate(user=user)
        return states


class TaskState(MultiTableCopyMixin, models.Model):
    """Tracks the status of a given Task for a particular page revision."""
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_SKIPPED = 'skipped'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = (
        (STATUS_IN_PROGRESS, _("In progress")),
        (STATUS_APPROVED, _("Approved")),
        (STATUS_REJECTED, _("Rejected")),
        (STATUS_SKIPPED, _("Skipped")),
        (STATUS_CANCELLED, _("Cancelled")),
    )

    workflow_state = models.ForeignKey('WorkflowState', on_delete=models.CASCADE, verbose_name=_('workflow state'), related_name='task_states')
    page_revision = models.ForeignKey('PageRevision', on_delete=models.CASCADE, verbose_name=_('page revision'), related_name='task_states')
    task = models.ForeignKey('Task', on_delete=models.CASCADE, verbose_name=_('task'), related_name='task_states')
    status = models.fields.CharField(choices=STATUS_CHOICES, verbose_name=_("status"), max_length=50, default=STATUS_IN_PROGRESS)
    started_at = models.DateTimeField(verbose_name=_('started at'), auto_now_add=True)
    finished_at = models.DateTimeField(verbose_name=_('finished at'), blank=True, null=True)
    finished_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('finished by'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='finished_task_states'
    )
    comment = models.TextField(blank=True)
    content_type = models.ForeignKey(
        ContentType,
        verbose_name=_('content type'),
        related_name='wagtail_task_states',
        on_delete=models.CASCADE
    )
    exclude_fields_in_copy = []

    objects = TaskStateManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.id:
            # this model is being newly created
            # rather than retrieved from the db;
            if not self.content_type_id:
                # set content type to correctly represent the model class
                # that this was created as
                self.content_type = ContentType.objects.get_for_model(self)

    def __str__(self):
        return _("Task '{0}' on Page Revision '{1}': {2}").format(self.task, self.page_revision, self.status)

    @cached_property
    def specific(self):
        """
        Return this TaskState in its most specific subclassed form.
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

    @transaction.atomic
    def approve(self, user=None, update=True, comment=''):
        """Approve the task state and update the workflow state"""
        if self.status != self.STATUS_IN_PROGRESS:
            raise PermissionDenied
        self.status = self.STATUS_APPROVED
        self.finished_at = timezone.now()
        self.finished_by = user
        self.comment = comment
        self.save()

        self.log_state_change_action(user, 'approve')
        if update:
            self.workflow_state.update(user=user)
        task_approved.send(sender=self.specific.__class__, instance=self.specific, user=user)
        return self

    @transaction.atomic
    def reject(self, user=None, update=True, comment=''):
        """Reject the task state and update the workflow state"""
        if self.status != self.STATUS_IN_PROGRESS:
            raise PermissionDenied
        self.status = self.STATUS_REJECTED
        self.finished_at = timezone.now()
        self.finished_by = user
        self.comment = comment
        self.save()

        self.log_state_change_action(user, 'reject')
        if update:
            self.workflow_state.update(user=user)
        task_rejected.send(sender=self.specific.__class__, instance=self.specific, user=user)

        return self

    @cached_property
    def task_type_started_at(self):
        """Finds the first chronological started_at for successive TaskStates - ie started_at if the task had not been restarted"""
        task_states = TaskState.objects.filter(workflow_state=self.workflow_state).order_by('-started_at').select_related('task')
        started_at = None
        for task_state in task_states:
            if task_state.task == self.task:
                started_at = task_state.started_at
            elif started_at:
                break
        return started_at

    @transaction.atomic
    def cancel(self, user=None, resume=False, comment=''):
        """Cancel the task state and update the workflow state. If ``resume`` is set to True, then upon update the workflow state
        is passed the current task as ``next_task``, causing it to start a new task state on the current task if possible"""
        self.status = self.STATUS_CANCELLED
        self.finished_at = timezone.now()
        self.comment = comment
        self.finished_by = user
        self.save()
        if resume:
            self.workflow_state.update(user=user, next_task=self.task.specific)
        else:
            self.workflow_state.update(user=user)
        task_cancelled.send(sender=self.specific.__class__, instance=self.specific, user=user)
        return self

    def copy(self, update_attrs=None, exclude_fields=None):
        """Copy this task state, excluding the attributes in the ``exclude_fields`` list and updating any attributes to values
        specified in the ``update_attrs`` dictionary of ``attribute``: ``new value`` pairs"""
        copy_instance, _ = self._copy(exclude_fields, update_attrs)
        return copy_instance

    def _save_copy_instance(self, instance, **kwargs):
        instance.save()
        return instance

    def get_comment(self):
        """
        Returns a string that is displayed in workflow history.

        This could be a comment by the reviewer, or generated.
        Use mark_safe to return HTML.
        """
        return self.comment

    def log_state_change_action(self, user, action):
        """Log the approval/rejection action"""
        page = self.page_revision.as_page_object()
        next_task = self.workflow_state.get_next_task()
        next_task_data = None
        if next_task:
            next_task_data = {
                'id': next_task.id,
                'title': next_task.name
            }
        PageLogEntry.objects.log_action(
            instance=page,
            action='wagtail.workflow.{}'.format(action),
            user=user,
            data={
                'workflow': {
                    'id': self.workflow_state.workflow.id,
                    'title': self.workflow_state.workflow.name,
                    'status': self.status,
                    'task_state_id': self.id,
                    'task': {
                        'id': self.task.id,
                        'title': self.task.name,
                    },
                    'next': next_task_data,
                },
                'comment': self.get_comment()
            },
            revision=self.page_revision
        )

    class Meta:
        verbose_name = _('Task state')
        verbose_name_plural = _('Task states')


class BaseLogEntryManager(models.Manager):
    def log_action(self, instance, action, **kwargs):
        """
        :param instance: The model instance we are logging an action for
        :param action: The action. Should be namespaced to app (e.g. wagtail.create, wagtail.workflow.start)
        :param kwargs: Addition fields to for the model deriving from BaseLogEntry
            - user: The user performing the action
            - title: the instance title
            - data: any additional metadata
            - content_changed, deleted - Boolean flags
        :return: The new log entry
        """
        data = kwargs.pop('data', '')
        title = kwargs.pop('title', None)
        if not title:
            if hasattr(instance, 'get_admin_display_title'):
                title = instance.get_admin_display_title()
            else:
                title = str(instance)

        timestamp = kwargs.pop('timestamp', timezone.now())
        return self.model.objects.create(
            content_type=ContentType.objects.get_for_model(instance, for_concrete_model=False),
            label=title,
            action=action,
            timestamp=timestamp,
            data_json=json.dumps(data),
            **kwargs,
        )

    def get_for_model(self, model):
        # Return empty queryset if the given object is not valid.
        if not issubclass(model, models.Model):
            return self.none()

        ct = ContentType.objects.get_for_model(model)

        return self.filter(content_type=ct)

    def get_for_user(self, user_id):
        return self.filter(user=user_id)


class PageLogEntryManager(BaseLogEntryManager):

    def log_action(self, instance, action, **kwargs):
        kwargs.update(page=instance)
        return super().log_action(instance, action, **kwargs)


class BaseLogEntry(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        models.SET_NULL,
        verbose_name=_('content type'),
        blank=True, null=True,
        related_name='+',
    )
    label = models.TextField()

    action = models.CharField(max_length=255, blank=True, db_index=True)
    data_json = models.TextField(blank=True)
    timestamp = models.DateTimeField(verbose_name=_('timestamp (UTC)'))

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,  # Null if actioned by system
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        related_name='+',
    )

    # Flags for additional context to the 'action' made by the user (or system).
    content_changed = models.BooleanField(default=False, db_index=True)
    deleted = models.BooleanField(default=False)

    objects = BaseLogEntryManager()

    class Meta:
        abstract = True
        verbose_name = _('log entry')
        verbose_name_plural = _('log entries')
        ordering = ['-timestamp']

    def __str__(self):
        return "LogEntry %d: '%s' on '%s'" % (
            self.pk, self.action, self.object_verbose_name()
        )

    @cached_property
    def username(self):
        """
        Returns the associated username. Defaults to 'system' when none is provided
        """
        if self.user_id:
            try:
                return self.user.get_username()
            except self._meta.get_field('user').related_model.DoesNotExist:
                # User has been deleted
                return _('user {id} (deleted)').format(id=self.user_id)
        else:
            return _('system')

    @cached_property
    def data(self):
        """
        Provides deserialized data
        """
        if self.data_json:
            return json.loads(self.data_json)
        else:
            return {}

    @cached_property
    def object_verbose_name(self):
        model_class = self.content_type.model_class()
        if model_class is None:
            return self.content_type_id

        return model_class._meta.verbose_name.title

    def object_id(self):
        raise NotImplementedError

    @cached_property
    def comment(self):
        if self.data:
            return self.data.get('comment', '')
        return ''


class PageLogEntry(BaseLogEntry):
    page = models.ForeignKey(
        'wagtailcore.Page',
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        related_name='+'
    )
    # Pointer to a specific page revision
    revision = models.ForeignKey(
        'wagtailcore.PageRevision',
        null=True,
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        related_name='+',
    )

    objects = PageLogEntryManager()

    class Meta:
        ordering = ['-timestamp', '-id']
        verbose_name = _('page log entry')
        verbose_name_plural = _('page log entries')

    def __str__(self):
        return "PageLogEntry %d: '%s' on '%s' with id %s" % (
            self.pk, self.action, self.object_verbose_name(), self.page_id
        )

    @cached_property
    def object_id(self):
        return self.page_id
