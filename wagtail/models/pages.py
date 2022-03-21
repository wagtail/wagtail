"""
wagtail.models is split into submodules for maintainability. All definitions intended as
public should be imported here (with 'noqa' comments as required) and outside code should continue
to import them from wagtail.models (e.g. `from wagtail.models import Site`, not
`from wagtail.models.sites import Site`.)

Submodules should take care to keep the direction of dependencies consistent; where possible they
should implement low-level generic functionality which is then imported by higher-level models such
as Page.
"""

import functools
import logging
import uuid
from io import StringIO
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core import checks
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.handlers.base import BaseHandler
from django.core.handlers.wsgi import WSGIRequest
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models, transaction
from django.db.models import DEFERRED, Q, Value
from django.db.models.functions import Concat, Substr
from django.dispatch import receiver
from django.http import Http404
from django.template.response import TemplateResponse
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils import translation as translation
from django.utils.cache import patch_cache_control
from django.utils.encoding import force_str
from django.utils.functional import cached_property
from django.utils.text import capfirst, slugify
from django.utils.translation import gettext_lazy as _
from modelcluster.models import ClusterableModel
from treebeard.mp_tree import MP_Node

from wagtail.actions.copy_for_translation import CopyPageForTranslationAction
from wagtail.actions.copy_page import CopyPageAction
from wagtail.actions.create_alias import CreatePageAliasAction
from wagtail.actions.delete_page import DeletePageAction
from wagtail.actions.move_page import MovePageAction
from wagtail.actions.publish_page_revision import PublishPageRevisionAction
from wagtail.actions.unpublish_page import UnpublishPageAction
from wagtail.coreutils import (
    WAGTAIL_APPEND_SLASH,
    camelcase_to_underscore,
    get_supported_content_language_variant,
    resolve_model_string,
)
from wagtail.fields import StreamField
from wagtail.log_actions import log
from wagtail.query import PageQuerySet
from wagtail.search import index
from wagtail.signals import page_published, page_slug_changed, pre_validate_delete
from wagtail.treebeard import TreebeardPathFixMixin
from wagtail.url_routing import RouteResult

from .commenting import COMMENTS_RELATION_NAME, Comment
from .copying import _copy_m2m_relations
from .i18n import Locale, TranslatableMixin
from .sites import Site
from .view_restrictions import BaseViewRestriction

logger = logging.getLogger("wagtail")

PAGE_TEMPLATE_VAR = "page"


@receiver(pre_validate_delete, sender=Locale)
def reassign_root_page_locale_on_delete(sender, instance, **kwargs):
    # if we're deleting the locale used on the root page node, reassign that to a new locale first
    root_page_with_this_locale = Page.objects.filter(depth=1, locale=instance)
    if root_page_with_this_locale.exists():
        # Select the default locale, if one exists and isn't the one being deleted
        try:
            new_locale = Locale.get_default()
            default_locale_is_ok = new_locale != instance
        except (Locale.DoesNotExist, LookupError):
            default_locale_is_ok = False

        if not default_locale_is_ok:
            # fall back on any remaining locale
            new_locale = Locale.all_objects.exclude(pk=instance.pk).first()

        root_page_with_this_locale.update(locale=new_locale)


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


@functools.lru_cache(maxsize=None)
def get_streamfield_names(model_class):
    return tuple(
        field.name
        for field in model_class._meta.concrete_fields
        if isinstance(field, StreamField)
    )


class BasePageManager(models.Manager):
    def get_queryset(self):
        return self._queryset_class(self.model).order_by("path")


PageManager = BasePageManager.from_queryset(PageQuerySet)


class PageBase(models.base.ModelBase):
    """Metaclass for Page"""

    def __init__(cls, name, bases, dct):
        super(PageBase, cls).__init__(name, bases, dct)

        if "template" not in dct:
            # Define a default template path derived from the app name and model name
            cls.template = "%s/%s.html" % (
                cls._meta.app_label,
                camelcase_to_underscore(name),
            )

        if "ajax_template" not in dct:
            cls.ajax_template = None

        cls._clean_subpage_models = (
            None  # to be filled in on first call to cls.clean_subpage_models
        )
        cls._clean_parent_page_models = (
            None  # to be filled in on first call to cls.clean_parent_page_models
        )

        # All pages should be creatable unless explicitly set otherwise.
        # This attribute is not inheritable.
        if "is_creatable" not in dct:
            cls.is_creatable = not cls._meta.abstract

        if not cls._meta.abstract:
            # register this type in the list of page content types
            PAGE_MODEL_CLASSES.append(cls)


class AbstractPage(TranslatableMixin, TreebeardPathFixMixin, MP_Node):
    """
    Abstract superclass for Page. According to Django's inheritance rules, managers set on
    abstract models are inherited by subclasses, but managers set on concrete models that are extended
    via multi-table inheritance are not. We therefore need to attach PageManager to an abstract
    superclass to ensure that it is retained by subclasses of Page.
    """

    objects = PageManager()

    class Meta:
        abstract = True


class Page(AbstractPage, index.Indexed, ClusterableModel, metaclass=PageBase):
    title = models.CharField(
        verbose_name=_("title"),
        max_length=255,
        help_text=_("The page title as you'd like it to be seen by the public"),
    )
    # to reflect title of a current draft in the admin UI
    draft_title = models.CharField(max_length=255, editable=False)
    slug = models.SlugField(
        verbose_name=_("slug"),
        allow_unicode=True,
        max_length=255,
        help_text=_(
            "The name of the page as it will appear in URLs e.g http://domain.com/blog/[my-slug]/"
        ),
    )
    content_type = models.ForeignKey(
        ContentType,
        verbose_name=_("content type"),
        related_name="pages",
        on_delete=models.SET(get_default_page_content_type),
    )
    live = models.BooleanField(verbose_name=_("live"), default=True, editable=False)
    has_unpublished_changes = models.BooleanField(
        verbose_name=_("has unpublished changes"), default=False, editable=False
    )
    url_path = models.TextField(verbose_name=_("URL path"), blank=True, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("owner"),
        null=True,
        blank=True,
        editable=True,
        on_delete=models.SET_NULL,
        related_name="owned_pages",
    )

    seo_title = models.CharField(
        verbose_name=_("title tag"),
        max_length=255,
        blank=True,
        help_text=_(
            "The name of the page displayed on search engine results as the clickable headline."
        ),
    )

    show_in_menus_default = False
    show_in_menus = models.BooleanField(
        verbose_name=_("show in menus"),
        default=False,
        help_text=_(
            "Whether a link to this page will appear in automatically generated menus"
        ),
    )
    search_description = models.TextField(
        verbose_name=_("meta description"),
        blank=True,
        help_text=_(
            "The descriptive text displayed underneath a headline in search engine results."
        ),
    )

    go_live_at = models.DateTimeField(
        verbose_name=_("go live date/time"), blank=True, null=True
    )
    expire_at = models.DateTimeField(
        verbose_name=_("expiry date/time"), blank=True, null=True
    )
    expired = models.BooleanField(
        verbose_name=_("expired"), default=False, editable=False
    )

    locked = models.BooleanField(
        verbose_name=_("locked"), default=False, editable=False
    )
    locked_at = models.DateTimeField(
        verbose_name=_("locked at"), null=True, editable=False
    )
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("locked by"),
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name="locked_pages",
    )

    first_published_at = models.DateTimeField(
        verbose_name=_("first published at"), blank=True, null=True, db_index=True
    )
    last_published_at = models.DateTimeField(
        verbose_name=_("last published at"), null=True, editable=False
    )
    latest_revision_created_at = models.DateTimeField(
        verbose_name=_("latest revision created at"), null=True, editable=False
    )
    live_revision = models.ForeignKey(
        "PageRevision",
        related_name="+",
        verbose_name=_("live revision"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
    )

    # If non-null, this page is an alias of the linked page
    # This means the page is kept in sync with the live version
    # of the linked pages and is not editable by users.
    alias_of = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name="aliases",
    )

    search_fields = [
        index.SearchField("title", partial_match=True, boost=2),
        index.AutocompleteField("title"),
        index.FilterField("title"),
        index.FilterField("id"),
        index.FilterField("live"),
        index.FilterField("owner"),
        index.FilterField("content_type"),
        index.FilterField("path"),
        index.FilterField("depth"),
        index.FilterField("locked"),
        index.FilterField("show_in_menus"),
        index.FilterField("first_published_at"),
        index.FilterField("last_published_at"),
        index.FilterField("latest_revision_created_at"),
        index.FilterField("locale"),
        index.FilterField("translation_key"),
    ]

    # Do not allow plain Page instances to be created through the Wagtail admin
    is_creatable = False

    # Define the maximum number of instances this page type can have. Default to unlimited.
    max_count = None

    # Define the maximum number of instances this page can have under a specific parent. Default to unlimited.
    max_count_per_parent = None

    # An array of additional field names that will not be included when a Page is copied.
    exclude_fields_in_copy = []
    default_exclude_fields_in_copy = [
        "id",
        "path",
        "depth",
        "numchild",
        "url_path",
        "path",
        "postgres_index_entries",
        "index_entries",
        COMMENTS_RELATION_NAME,
    ]

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
            if "show_in_menus" not in kwargs:
                # if the value is not set on submit refer to the model setting
                self.show_in_menus = self.show_in_menus_default

    def __str__(self):
        return self.title

    @classmethod
    def get_streamfield_names(cls):
        return get_streamfield_names(cls)

    def set_url_path(self, parent):
        """
        Populate the url_path field based on this page's slug and the specified parent page.
        (We pass a parent in here, rather than retrieving it via get_parent, so that we can give
        new unsaved pages a meaningful URL when previewing them; at that point the page has not
        been assigned a position in the tree, as far as treebeard is concerned.
        """
        if parent:
            self.url_path = parent.url_path + self.slug + "/"
        else:
            # a page without a parent is the tree root, which always has a url_path of '/'
            self.url_path = "/"

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

    def get_default_locale(self):
        """
        Finds the default locale to use for this page.

        This will be called just before the initial save.
        """
        parent = self.get_parent()
        if parent is not None:
            return (
                parent.specific_class.objects.defer()
                .select_related("locale")
                .get(id=parent.id)
                .locale
            )

        return super().get_default_locale()

    def full_clean(self, *args, **kwargs):
        # Apply fixups that need to happen before per-field validation occurs

        if not self.slug:
            # Try to auto-populate slug from title
            allow_unicode = getattr(settings, "WAGTAIL_ALLOW_UNICODE_SLUGS", True)
            base_slug = slugify(self.title, allow_unicode=allow_unicode)

            # only proceed if we get a non-empty base slug back from slugify
            if base_slug:
                self.slug = self._get_autogenerated_slug(base_slug)

        if not self.draft_title:
            self.draft_title = self.title

        # Set the locale
        if self.locale_id is None:
            self.locale = self.get_default_locale()

        super().full_clean(*args, **kwargs)

    def clean(self):
        super().clean()
        if not Page._slug_is_available(self.slug, self.get_parent(), self):
            raise ValidationError({"slug": _("This slug is already in use")})

    def is_site_root(self):
        """
        Returns True if this page is the root of any site.

        This includes translations of site root pages as well.
        """
        # `_is_site_root` may be populated by `annotate_site_root_state` on `PageQuerySet` as a
        # performance optimisation
        if hasattr(self, "_is_site_root"):
            return self._is_site_root

        return Site.objects.filter(
            root_page__translation_key=self.translation_key
        ).exists()

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

        slug_changed = False
        is_new = self.id is None

        if is_new:
            # we are creating a record. If we're doing things properly, this should happen
            # through a treebeard method like add_child, in which case the 'path' field
            # has been set and so we can safely call get_parent
            self.set_url_path(self.get_parent())
        else:
            # Check that we are committing the slug to the database
            # Basically: If update_fields has been specified, and slug is not included, skip this step
            if not (
                "update_fields" in kwargs and "slug" not in kwargs["update_fields"]
            ):
                # see if the slug has changed from the record in the db, in which case we need to
                # update url_path of self and all descendants. Even though we might not need it,
                # the specific page is fetched here for sending to the 'page_slug_changed' signal.
                old_record = Page.objects.get(id=self.id).specific
                if old_record.slug != self.slug:
                    self.set_url_path(self.get_parent())
                    slug_changed = True
                    old_url_path = old_record.url_path
                    new_url_path = self.url_path

        result = super().save(**kwargs)

        if slug_changed:
            self._update_descendant_url_paths(old_url_path, new_url_path)
            # Emit page_slug_changed signal on successful db commit
            transaction.on_commit(
                lambda: page_slug_changed.send(
                    sender=self.specific_class or self.__class__,
                    instance=self.specific,
                    instance_before=old_record,
                )
            )

        # Check if this is a root page of any sites and clear the 'wagtail_site_root_paths' key if so
        # Note: New translations of existing site roots are considered site roots as well, so we must
        # always check if this page is a site root, even if it's new.
        if self.is_site_root():
            cache.delete("wagtail_site_root_paths")

        # Log
        if is_new:
            cls = type(self)
            logger.info(
                'Page created: "%s" id=%d content_type=%s.%s path=%s',
                self.title,
                self.id,
                cls._meta.app_label,
                cls.__name__,
                self.url_path,
            )

        if log_action is not None:
            # The default for log_action is False. i.e. don't log unless specifically instructed
            # Page creation is a special case that we want logged by default, but allow skipping it
            # explicitly by passing log_action=None
            if is_new:
                log(
                    instance=self,
                    action="wagtail.create",
                    user=user or self.owner,
                    content_changed=True,
                )
            elif log_action:
                log(instance=self, action=log_action, user=user)

        return result

    def delete(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        return DeletePageAction(self, user=user).execute(*args, **kwargs)

    @classmethod
    def check(cls, **kwargs):
        errors = super(Page, cls).check(**kwargs)

        # Check that foreign keys from pages are not configured to cascade
        # This is the default Django behaviour which must be explicitly overridden
        # to prevent pages disappearing unexpectedly and the tree being corrupted

        # get names of foreign keys pointing to parent classes (such as page_ptr)
        field_exceptions = [
            field.name
            for model in [cls] + list(cls._meta.get_parent_list())
            for field in model._meta.parents.values()
            if field
        ]

        for field in cls._meta.fields:
            if (
                isinstance(field, models.ForeignKey)
                and field.name not in field_exceptions
            ):
                if field.remote_field.on_delete == models.CASCADE:
                    errors.append(
                        checks.Warning(
                            "Field hasn't specified on_delete action",
                            hint="Set on_delete=models.SET_NULL and make sure the field is nullable or set on_delete=models.PROTECT. Wagtail does not allow simple database CASCADE because it will corrupt its tree storage.",
                            obj=field,
                            id="wagtailcore.W001",
                        )
                    )

        if not isinstance(cls.objects, PageManager):
            errors.append(
                checks.Error(
                    "Manager does not inherit from PageManager",
                    hint="Ensure that custom Page managers inherit from wagtail.models.PageManager",
                    obj=cls,
                    id="wagtailcore.E002",
                )
            )

        try:
            cls.clean_subpage_models()
        except (ValueError, LookupError) as e:
            errors.append(
                checks.Error(
                    "Invalid subpage_types setting for %s" % cls,
                    hint=str(e),
                    id="wagtailcore.E002",
                )
            )

        try:
            cls.clean_parent_page_models()
        except (ValueError, LookupError) as e:
            errors.append(
                checks.Error(
                    "Invalid parent_page_types setting for %s" % cls,
                    hint=str(e),
                    id="wagtailcore.E002",
                )
            )

        return errors

    def _update_descendant_url_paths(self, old_url_path, new_url_path):
        (
            Page.objects.filter(path__startswith=self.path)
            .exclude(pk=self.pk)
            .update(
                url_path=Concat(
                    Value(new_url_path), Substr("url_path", len(old_url_path) + 1)
                )
            )
        )

    def get_specific(self, deferred=False, copy_attrs=None, copy_attrs_exclude=None):
        """
        Return this page in its most specific subclassed form.

        By default, a database query is made to fetch all field values for the
        specific object. If you only require access to custom methods or other
        non-field attributes on the specific object, you can use
        ``deferred=True`` to avoid this query. However, any attempts to access
        specific field values from the returned object will trigger additional
        database queries.

        By default, references to all non-field attribute values are copied
        from current object to the returned one. This includes:

        * Values set by a queryset, for example: annotations, or values set as
          a result of using ``select_related()`` or ``prefetch_related()``.
        * Any ``cached_property`` values that have been evaluated.
        * Attributes set elsewhere in Python code.

        For fine-grained control over which non-field values are copied to the
        returned object, you can use ``copy_attrs`` to specify a complete list
        of attribute names to include. Alternatively, you can use
        ``copy_attrs_exclude`` to specify a list of attribute names to exclude.

        If called on a page object that is already an instance of the most
        specific class (e.g. an ``EventPage``), the object will be returned
        as is, and no database queries or other operations will be triggered.

        If the page was originally created using a page type that has since
        been removed from the codebase, a generic ``Page`` object will be
        returned (without any custom field values or other functionality
        present on the original class). Usually, deleting these pages is the
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

        if deferred:
            # Generate a tuple of values in the order expected by __init__(),
            # with missing values substituted with DEFERRED ()
            values = tuple(
                getattr(self, f.attname, self.pk if f.primary_key else DEFERRED)
                for f in model_class._meta.concrete_fields
            )
            # Create object from known attribute values
            specific_obj = model_class(*values)
            specific_obj._state.adding = self._state.adding
        else:
            # Fetch object from database
            specific_obj = model_class._default_manager.get(id=self.id)

        # Copy non-field attribute values
        if copy_attrs is not None:
            for attr in (attr for attr in copy_attrs if attr in self.__dict__):
                setattr(specific_obj, attr, getattr(self, attr))
        else:
            exclude = copy_attrs_exclude or ()
            for k, v in ((k, v) for k, v in self.__dict__.items() if k not in exclude):
                # only set values that haven't already been set
                specific_obj.__dict__.setdefault(k, v)

        return specific_obj

    @cached_property
    def specific(self):
        """
        Returns this page in its most specific subclassed form with all field
        values fetched from the database. The result is cached in memory.
        """
        return self.get_specific()

    @cached_property
    def specific_deferred(self):
        """
        Returns this page in its most specific subclassed form without any
        additional field values being fetched from the database. The result
        is cached in memory.
        """
        return self.get_specific(deferred=True)

    @cached_property
    def specific_class(self):
        """
        Return the class that this page would be if instantiated in its
        most specific form.

        If the model class can no longer be found in the codebase, and the
        relevant ``ContentType`` has been removed by a database migration,
        the return value will be ``None``.

        If the model class can no longer be found in the codebase, but the
        relevant ``ContentType`` is still present in the database (usually a
        result of switching between git branches without running or reverting
        database migrations beforehand), the return value will be ``None``.
        """
        return self.cached_content_type.model_class()

    @property
    def cached_content_type(self):
        """
        Return this page's ``content_type`` value from the ``ContentType``
        model's cached manager, which will avoid a database query if the
        object is already in memory.
        """
        return ContentType.objects.get_for_id(self.content_type_id)

    @property
    def localized_draft(self):
        """
        Finds the translation in the current active language.

        If there is no translation in the active language, self is returned.

        Note: This will return translations that are in draft. If you want to exclude
        these, use the ``.localized`` attribute.
        """
        try:
            locale = Locale.get_active()
        except (LookupError, Locale.DoesNotExist):
            return self

        if locale.id == self.locale_id:
            return self

        return self.get_translation_or_none(locale) or self

    @property
    def localized(self):
        """
        Finds the translation in the current active language.

        If there is no translation in the active language, self is returned.

        Note: This will not return the translation if it is in draft.
        If you want to include drafts, use the ``.localized_draft`` attribute instead.
        """
        localized = self.localized_draft
        if not localized.live:
            return self

        return localized

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

    def save_revision(
        self,
        user=None,
        submitted_for_moderation=False,
        approved_go_live_at=None,
        changed=True,
        log_action=False,
        previous_revision=None,
        clean=True,
    ):
        """
        Creates and saves a page revision.
        :param user: the user performing the action
        :param submitted_for_moderation: indicates whether the page was submitted for moderation
        :param approved_go_live_at: the date and time the revision is approved to go live
        :param changed: indicates whether there were any content changes
        :param log_action: flag for logging the action. Pass False to skip logging. Can be passed an action string.
            Defaults to 'wagtail.edit' when no 'previous_revision' param is passed, otherwise 'wagtail.revert'
        :param previous_revision: indicates a revision reversal. Should be set to the previous revision instance
        :param clean: Set this to False to skip cleaning page content before saving this revision
        :return: the newly created revision
        """
        # Raise an error if this page is an alias.
        if self.alias_of_id:
            raise RuntimeError(
                "save_revision() was called on an alias page. "
                "Revisions are not required for alias pages as they are an exact copy of another page."
            )

        if clean:
            self.full_clean()

        new_comments = getattr(self, COMMENTS_RELATION_NAME).filter(pk__isnull=True)
        for comment in new_comments:
            # We need to ensure comments have an id in the revision, so positions can be identified correctly
            comment.save()

        # Create revision
        revision = self.revisions.create(
            content=self.serializable_data(),
            user=user,
            submitted_for_moderation=submitted_for_moderation,
            approved_go_live_at=approved_go_live_at,
        )

        for comment in new_comments:
            comment.revision_created = revision

        update_fields = [COMMENTS_RELATION_NAME]

        self.latest_revision_created_at = revision.created_at
        update_fields.append("latest_revision_created_at")

        self.draft_title = self.title
        update_fields.append("draft_title")

        if changed:
            self.has_unpublished_changes = True
            update_fields.append("has_unpublished_changes")

        if update_fields:
            # clean=False because the fields we're updating don't need validation
            self.save(update_fields=update_fields, clean=False)

        # Log
        logger.info(
            'Page edited: "%s" id=%d revision_id=%d', self.title, self.id, revision.id
        )
        if log_action:
            if not previous_revision:
                log(
                    instance=self,
                    action=log_action
                    if isinstance(log_action, str)
                    else "wagtail.edit",
                    user=user,
                    revision=revision,
                    content_changed=changed,
                )
            else:
                log(
                    instance=self,
                    action=log_action
                    if isinstance(log_action, str)
                    else "wagtail.revert",
                    user=user,
                    data={
                        "revision": {
                            "id": previous_revision.id,
                            "created": previous_revision.created_at.strftime(
                                "%d %b %Y %H:%M"
                            ),
                        }
                    },
                    revision=revision,
                    content_changed=changed,
                )

        if submitted_for_moderation:
            logger.info(
                'Page submitted for moderation: "%s" id=%d revision_id=%d',
                self.title,
                self.id,
                revision.id,
            )

        return revision

    def get_latest_revision(self):
        return self.revisions.order_by("-created_at", "-id").first()

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

    def update_aliases(
        self, *, revision=None, user=None, _content=None, _updated_ids=None
    ):
        """
        Publishes all aliases that follow this page with the latest content from this page.

        This is called by Wagtail whenever a page with aliases is published.

        :param revision: The revision of the original page that we are updating to (used for logging purposes)
        :type revision: PageRevision, optional
        :param user: The user who is publishing (used for logging purposes)
        :type user: User, optional
        """
        specific_self = self.specific

        # Only compute this if necessary since it's quite a heavy operation
        if _content is None:
            _content = self.serializable_data()

        # A list of IDs that have already been updated. This is just in case someone has
        # created an alias loop (which is impossible to do with the UI Wagtail provides)
        _updated_ids = _updated_ids or []

        for alias in self.specific_class.objects.filter(alias_of=self).exclude(
            id__in=_updated_ids
        ):
            # FIXME: Switch to the same fields that are excluded from copy
            # We can't do this right now because we can't exclude fields from with_content_json
            exclude_fields = [
                "id",
                "path",
                "depth",
                "numchild",
                "url_path",
                "path",
                "index_entries",
                "postgres_index_entries",
            ]

            # Copy field content
            alias_updated = alias.with_content_json(_content)

            # Publish the alias if it's currently in draft
            alias_updated.live = True
            alias_updated.has_unpublished_changes = False

            # Copy child relations
            child_object_map = specific_self.copy_all_child_relations(
                target=alias_updated, exclude=exclude_fields
            )

            # Process child objects
            # This has two jobs:
            #  - If the alias is in a different locale, this updates the
            #    locale of any translatable child objects to match
            #  - If the alias is not a translation of the original, this
            #    changes the translation_key field of all child objects
            #    so they do not clash
            if child_object_map:
                alias_is_translation = alias.translation_key == self.translation_key

                def process_child_object(child_object):
                    if isinstance(child_object, TranslatableMixin):
                        # Child object's locale must always match the page
                        child_object.locale = alias_updated.locale

                        # If the alias isn't a translation of the original page,
                        # change the child object's translation_keys so they are
                        # not either
                        if not alias_is_translation:
                            child_object.translation_key = uuid.uuid4()

                for (rel, previous_id), child_objects in child_object_map.items():
                    if previous_id is None:
                        for child_object in child_objects:
                            process_child_object(child_object)
                    else:
                        process_child_object(child_objects)

            # Copy M2M relations
            _copy_m2m_relations(
                specific_self, alias_updated, exclude_fields=exclude_fields
            )

            # Don't change the aliases slug
            # Aliases can have their own slugs so they can be siblings of the original
            alias_updated.slug = alias.slug
            alias_updated.set_url_path(alias_updated.get_parent())

            # Aliases don't have revisions, so update fields that would normally be updated by save_revision
            alias_updated.draft_title = alias_updated.title
            alias_updated.latest_revision_created_at = self.latest_revision_created_at

            alias_updated.save(clean=False)

            page_published.send(
                sender=alias_updated.specific_class,
                instance=alias_updated,
                revision=revision,
                alias=True,
            )

            # Log the publish of the alias
            log(
                instance=alias_updated,
                action="wagtail.publish",
                user=user,
            )

            # Update any aliases of that alias

            # Design note:
            # It could be argued that this will be faster if we just changed these alias-of-alias
            # pages to all point to the original page and avoid having to update them recursively.
            #
            # But, it's useful to have a record of how aliases have been chained.
            # For example, In Wagtail Localize, we use aliases to create mirrored trees, but those
            # trees themselves could have aliases within them. If an alias within a tree is
            # converted to a regular page, we want the alias in the mirrored tree to follow that
            # new page and stop receiving updates from the original page.
            #
            # Doing it this way requires an extra lookup query per alias but this is small in
            # comparison to the work required to update the alias.

            alias.update_aliases(
                revision=revision,
                _content=_content,
                _updated_ids=_updated_ids,
            )

    update_aliases.alters_data = True

    def unpublish(self, set_expired=False, commit=True, user=None, log_action=True):
        return UnpublishPageAction(
            self,
            set_expired=set_expired,
            commit=commit,
            user=user,
            log_action=log_action,
        ).execute()

    context_object_name = None

    def get_context(self, request, *args, **kwargs):
        context = {
            PAGE_TEMPLATE_VAR: self,
            "self": self,
            "request": request,
        }

        if self.context_object_name:
            context[self.context_object_name] = self

        return context

    def get_template(self, request, *args, **kwargs):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return self.ajax_template or self.template
        else:
            return self.template

    def serve(self, request, *args, **kwargs):
        request.is_preview = getattr(request, "is_preview", False)

        return TemplateResponse(
            request,
            self.get_template(request, *args, **kwargs),
            self.get_context(request, *args, **kwargs),
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

    def _get_relevant_site_root_paths(self, cache_object=None):
        """
        .. versionadded::2.16

        Returns a tuple of root paths for all sites this page belongs to.
        """
        return tuple(
            srp
            for srp in self._get_site_root_paths(cache_object)
            if self.url_path.startswith(srp.root_path)
        )

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

        possible_sites = self._get_relevant_site_root_paths(request)

        if not possible_sites:
            return None

        site_id, root_path, root_url, language_code = possible_sites[0]

        site = Site.find_for_request(request)
        if site:
            for site_id, root_path, root_url, language_code in possible_sites:
                if site_id == site.pk:
                    break
            else:
                site_id, root_path, root_url, language_code = possible_sites[0]

        use_wagtail_i18n = getattr(settings, "WAGTAIL_I18N_ENABLED", False)

        if use_wagtail_i18n:
            # If the active language code is a variant of the page's language, then
            # use that instead
            # This is used when LANGUAGES contain more languages than WAGTAIL_CONTENT_LANGUAGES
            try:
                if (
                    get_supported_content_language_variant(translation.get_language())
                    == language_code
                ):
                    language_code = translation.get_language()
            except LookupError:
                # active language code is not a recognised content language, so leave
                # page's language code unchanged
                pass

        # The page may not be routable because wagtail_serve is not registered
        # This may be the case if Wagtail is used headless
        try:
            if use_wagtail_i18n:
                with translation.override(language_code):
                    page_path = reverse(
                        "wagtail_serve", args=(self.url_path[len(root_path) :],)
                    )
            else:
                page_path = reverse(
                    "wagtail_serve", args=(self.url_path[len(root_path) :],)
                )
        except NoReverseMatch:
            return (site_id, None, None)

        # Remove the trailing slash from the URL reverse generates if
        # WAGTAIL_APPEND_SLASH is False and we're not trying to serve
        # the root path
        if not WAGTAIL_APPEND_SLASH and page_path != "/":
            page_path = page_path.rstrip("/")

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

        # Get number of unique sites in root paths
        # Note: there may be more root paths to sites if there are multiple languages
        num_sites = len(
            {root_path[0] for root_path in self._get_site_root_paths(request)}
        )

        if (current_site is not None and site_id == current_site.id) or num_sites == 1:
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
            subpage_types = getattr(cls, "subpage_types", None)
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
            parent_page_types = getattr(cls, "parent_page_types", None)
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
            parent_model
            for parent_model in cls.clean_parent_page_models()
            if cls in parent_model.clean_subpage_models()
        ]

    @classmethod
    def allowed_subpage_models(cls):
        """
        Returns the list of page types that this page type can have as subpages,
        as a list of model classes
        """
        return [
            subpage_model
            for subpage_model in cls.clean_subpage_models()
            if cls in subpage_model.clean_parent_page_models()
        ]

    @classmethod
    def creatable_subpage_models(cls):
        """
        Returns the list of page types that may be created under this page type,
        as a list of model classes
        """
        return [
            page_model
            for page_model in cls.allowed_subpage_models()
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
            can_create = (
                can_create
                and parent.get_children().type(cls).count() < cls.max_count_per_parent
            )

        return can_create

    def can_move_to(self, parent):
        """
        Checks if this page instance can be moved to be a subpage of a parent
        page instance.
        """
        # Prevent pages from being moved to different language sections
        # The only page that can have multi-lingual children is the root page
        parent_is_root = parent.depth == 1
        if not parent_is_root and parent.locale_id != self.locale_id:
            return False

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
        # `_approved_schedule` may be populated by `annotate_approved_schedule` on `PageQuerySet` as a
        # performance optimisation
        if hasattr(self, "_approved_schedule"):
            return self._approved_schedule

        return self.revisions.exclude(approved_go_live_at__isnull=True).exists()

    def has_unpublished_subtree(self):
        """
        An awkwardly-defined flag used in determining whether unprivileged editors have
        permission to delete this article. Returns true if and only if this page is non-live,
        and it has no live children.
        """
        return (not self.live) and (
            not self.get_descendants().filter(live=True).exists()
        )

    def move(self, target, pos=None, user=None):
        """
        Extension to the treebeard 'move' method to ensure that url_path is updated,
        and to emit a 'pre_page_move' and 'post_page_move' signals.
        """
        return MovePageAction(self, target, pos=pos, user=user).execute()

    def copy(
        self,
        recursive=False,
        to=None,
        update_attrs=None,
        copy_revisions=True,
        keep_live=True,
        user=None,
        process_child_object=None,
        exclude_fields=None,
        log_action="wagtail.copy",
        reset_translation_key=True,
    ):
        """
        Copies a given page
        :param log_action flag for logging the action. Pass None to skip logging.
            Can be passed an action string. Defaults to 'wagtail.copy'
        """
        return CopyPageAction(
            self,
            to=to,
            update_attrs=update_attrs,
            exclude_fields=exclude_fields,
            recursive=recursive,
            copy_revisions=copy_revisions,
            keep_live=keep_live,
            user=user,
            process_child_object=process_child_object,
            log_action=log_action,
            reset_translation_key=reset_translation_key,
        ).execute(skip_permission_checks=True)

    copy.alters_data = True

    def create_alias(
        self,
        *,
        recursive=False,
        parent=None,
        update_slug=None,
        update_locale=None,
        user=None,
        log_action="wagtail.create_alias",
        reset_translation_key=True,
        _mpnode_attrs=None,
    ):
        return CreatePageAliasAction(
            self,
            recursive=recursive,
            parent=parent,
            update_slug=update_slug,
            update_locale=update_locale,
            user=user,
            log_action=log_action,
            reset_translation_key=reset_translation_key,
            _mpnode_attrs=_mpnode_attrs,
        ).execute()

    create_alias.alters_data = True

    def copy_for_translation(
        self, locale, copy_parents=False, alias=False, exclude_fields=None
    ):
        """Creates a copy of this page in the specified locale."""

        return CopyPageForTranslationAction(
            self,
            locale,
            copy_parents=copy_parents,
            alias=alias,
            exclude_fields=exclude_fields,
        ).execute()

    copy_for_translation.alters_data = True

    def permissions_for_user(self, user):
        """
        Return a PagePermissionsTester object defining what actions the user can perform on this page
        """
        user_perms = UserPagePermissionsProxy(user)
        return user_perms.for_page(self)

    def make_preview_request(
        self, original_request=None, preview_mode=None, extra_request_attrs=None
    ):
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
                if hasattr(response, "render") and callable(response.render):
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
            port = url_info.port or (443 if url_info.scheme == "https" else 80)
            scheme = url_info.scheme
        else:
            # Cannot determine a URL to this page - cobble one together based on
            # whatever we find in ALLOWED_HOSTS
            try:
                hostname = settings.ALLOWED_HOSTS[0]
                if hostname == "*":
                    # '*' is a valid value to find in ALLOWED_HOSTS[0], but it's not a valid domain name.
                    # So we pretend it isn't there.
                    raise IndexError
            except IndexError:
                hostname = "localhost"
            path = "/"
            port = 80
            scheme = "http"

        http_host = hostname
        if port != (443 if scheme == "https" else 80):
            http_host = "%s:%s" % (http_host, port)
        dummy_values = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": path,
            "SERVER_NAME": hostname,
            "SERVER_PORT": port,
            "SERVER_PROTOCOL": "HTTP/1.1",
            "HTTP_HOST": http_host,
            "wsgi.version": (1, 0),
            "wsgi.input": StringIO(),
            "wsgi.errors": StringIO(),
            "wsgi.url_scheme": scheme,
            "wsgi.multithread": True,
            "wsgi.multiprocess": True,
            "wsgi.run_once": False,
        }

        # Add important values from the original request object, if it was provided.
        HEADERS_FROM_ORIGINAL_REQUEST = [
            "REMOTE_ADDR",
            "HTTP_X_FORWARDED_FOR",
            "HTTP_COOKIE",
            "HTTP_USER_AGENT",
            "HTTP_AUTHORIZATION",
            "wsgi.version",
            "wsgi.multithread",
            "wsgi.multiprocess",
            "wsgi.run_once",
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

    DEFAULT_PREVIEW_MODES = [("", _("Default"))]

    @property
    def preview_modes(self):
        """
        A list of (internal_name, display_name) tuples for the modes in which
        this page can be displayed for preview/moderation purposes. Ordinarily a page
        will only have one display mode, but subclasses of Page can override this -
        for example, a page containing a form might have a default view of the form,
        and a post-submission 'thank you' page
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
        request.preview_mode = mode_name

        response = self.serve(request)
        patch_cache_control(response, private=True)
        return response

    def get_route_paths(self):
        """
        .. versionadded:: 2.16

        Returns a list of paths that this page can be viewed at.

        These values are combined with the dynamic portion of the page URL to
        automatically create redirects when the page's URL changes.

        .. note::

            If using ``RoutablePageMixin``, you may want to override this method
            to include the paths of popualar routes.

        .. note::

            Redirect paths are 'normalized' to apply consistant ordering to GET parameters,
            so you don't need to include every variation. Fragment identifiers are discarded
            too, so should be avoided.
        """
        return ["/"]

    def get_cached_paths(self):
        """
        This returns a list of paths to invalidate in a frontend cache
        """
        return ["/"]

    def get_sitemap_urls(self, request=None):
        return [
            {
                "location": self.get_full_url(request),
                # fall back on latest_revision_created_at if last_published_at is null
                # (for backwards compatibility from before last_published_at was added)
                "lastmod": (self.last_published_at or self.latest_revision_created_at),
            }
        ]

    def get_static_site_paths(self):
        """
        This is a generator of URL paths to feed into a static site generator
        Override this if you would like to create static versions of subpages
        """
        # Yield path for this page
        yield "/"

        # Yield paths for child pages
        for child in self.get_children().live():
            for path in child.specific.get_static_site_paths():
                yield "/" + child.slug + path

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
        return self.get_siblings(inclusive).filter(path__gte=self.path).order_by("path")

    def get_prev_siblings(self, inclusive=False):
        return (
            self.get_siblings(inclusive).filter(path__lte=self.path).order_by("-path")
        )

    def get_view_restrictions(self):
        """
        Return a query set of all page view restrictions that apply to this page.

        This checks the current page and all ancestor pages for page view restrictions.

        If any of those pages are aliases, it will resolve them to their source pages
        before querying PageViewRestrictions so alias pages use the same view restrictions
        as their source page and they cannot have their own.
        """
        page_ids_to_check = set()

        def add_page_to_check_list(page):
            # If the page is an alias, add the source page to the check list instead
            if page.alias_of:
                add_page_to_check_list(page.alias_of)
            else:
                page_ids_to_check.add(page.id)

        # Check current page for view restrictions
        add_page_to_check_list(self)

        # Check each ancestor for view restrictions as well
        for page in self.get_ancestors().only("alias_of"):
            add_page_to_check_list(page)

        return PageViewRestriction.objects.filter(page_id__in=page_ids_to_check)

    password_required_template = getattr(
        settings, "PASSWORD_REQUIRED_TEMPLATE", "wagtailcore/password_required.html"
    )

    def serve_password_required_response(self, request, form, action_url):
        """
        Serve a response indicating that the user has been denied access to view this page,
        and must supply a password.
        form = a Django form object containing the password input
            (and zero or more hidden fields that also need to be output on the template)
        action_url = URL that this form should be POSTed to
        """
        context = self.get_context(request)
        context["form"] = form
        context["action_url"] = action_url
        return TemplateResponse(request, self.password_required_template, context)

    def with_content_json(self, content):
        """
        Returns a new version of the page with field values updated to reflect changes
        in the provided ``content`` (which usually comes from a previously-saved
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
        * ``alias_of``
        * ``wagtail_admin_comments`` (COMMENTS_RELATION_NAME)
        """

        # Old revisions (pre Wagtail 2.15) may have saved comment data under the name 'comments'
        # rather than the current relation name as set by COMMENTS_RELATION_NAME;
        # if a 'comments' field exists and looks like our comments model, alter the data to use
        # COMMENTS_RELATION_NAME before restoring
        if (
            COMMENTS_RELATION_NAME not in content
            and "comments" in content
            and isinstance(content["comments"], list)
            and len(content["comments"])
            and isinstance(content["comments"][0], dict)
            and "contentpath" in content["comments"][0]
        ):
            content[COMMENTS_RELATION_NAME] = content["comments"]
            del content["comments"]

        obj = self.specific_class.from_serializable_data(content)

        # These should definitely never change between revisions
        obj.id = self.id
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
        obj.translation_key = self.translation_key
        obj.locale = self.locale
        obj.alias_of_id = self.alias_of_id
        revision_comments = getattr(obj, COMMENTS_RELATION_NAME)
        page_comments = getattr(self, COMMENTS_RELATION_NAME).filter(
            resolved_at__isnull=True
        )
        for comment in page_comments:
            # attempt to retrieve the comment position from the revision's stored version
            # of the comment
            try:
                revision_comment = revision_comments.get(id=comment.id)
                comment.position = revision_comment.position
            except Comment.DoesNotExist:
                pass
        setattr(obj, COMMENTS_RELATION_NAME, page_comments)

        return obj

    @property
    def has_workflow(self):
        """Returns True if the page or an ancestor has an active workflow assigned, otherwise False"""
        if not getattr(settings, "WAGTAIL_WORKFLOW_ENABLED", True):
            return False
        return (
            self.get_ancestors(inclusive=True)
            .filter(workflowpage__isnull=False)
            .filter(workflowpage__workflow__active=True)
            .exists()
        )

    def get_workflow(self):
        """Returns the active workflow assigned to the page or its nearest ancestor"""
        if not getattr(settings, "WAGTAIL_WORKFLOW_ENABLED", True):
            return None

        if hasattr(self, "workflowpage") and self.workflowpage.workflow.active:
            return self.workflowpage.workflow
        else:
            try:
                workflow = (
                    self.get_ancestors()
                    .filter(workflowpage__isnull=False)
                    .filter(workflowpage__workflow__active=True)
                    .order_by("-depth")
                    .first()
                    .workflowpage.workflow
                )
            except AttributeError:
                workflow = None
            return workflow

    @property
    def workflow_in_progress(self):
        """Returns True if a workflow is in progress on the current page, otherwise False"""
        from .workflows import WorkflowState

        if not getattr(settings, "WAGTAIL_WORKFLOW_ENABLED", True):
            return False

        # `_current_workflow_states` may be populated by `prefetch_workflow_states` on `PageQuerySet` as a
        # performance optimisation
        if hasattr(self, "_current_workflow_states"):
            for state in self._current_workflow_states:
                if state.status == WorkflowState.STATUS_IN_PROGRESS:
                    return True
            return False

        return WorkflowState.objects.filter(
            page=self, status=WorkflowState.STATUS_IN_PROGRESS
        ).exists()

    @property
    def current_workflow_state(self):
        """Returns the in progress or needs changes workflow state on this page, if it exists"""
        from .workflows import WorkflowState

        if not getattr(settings, "WAGTAIL_WORKFLOW_ENABLED", True):
            return None

        # `_current_workflow_states` may be populated by `prefetch_workflow_states` on `pagequeryset` as a
        # performance optimisation
        if hasattr(self, "_current_workflow_states"):
            try:
                return self._current_workflow_states[0]
            except IndexError:
                return

        try:
            return (
                WorkflowState.objects.active()
                .select_related("current_task_state__task")
                .get(page=self)
            )
        except WorkflowState.DoesNotExist:
            return

    @property
    def current_workflow_task_state(self):
        """Returns (specific class of) the current task state of the workflow on this page, if it exists"""
        from .workflows import WorkflowState

        current_workflow_state = self.current_workflow_state
        if (
            current_workflow_state
            and current_workflow_state.status == WorkflowState.STATUS_IN_PROGRESS
            and current_workflow_state.current_task_state
        ):
            return current_workflow_state.current_task_state.specific

    @property
    def current_workflow_task(self):
        """Returns (specific class of) the current task in progress on this page, if it exists"""
        current_workflow_task_state = self.current_workflow_task_state
        if current_workflow_task_state:
            return current_workflow_task_state.task.specific

    class Meta:
        verbose_name = _("page")
        verbose_name_plural = _("pages")
        unique_together = [("translation_key", "locale")]


class Orderable(models.Model):
    sort_order = models.IntegerField(null=True, blank=True, editable=False)
    sort_order_field = "sort_order"

    class Meta:
        abstract = True
        ordering = ["sort_order"]


class SubmittedRevisionsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(submitted_for_moderation=True)


class PageRevision(models.Model):
    page = models.ForeignKey(
        "Page",
        verbose_name=_("page"),
        related_name="revisions",
        on_delete=models.CASCADE,
    )
    submitted_for_moderation = models.BooleanField(
        verbose_name=_("submitted for moderation"), default=False, db_index=True
    )
    created_at = models.DateTimeField(db_index=True, verbose_name=_("created at"))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    content = models.JSONField(
        verbose_name=_("content JSON"), encoder=DjangoJSONEncoder
    )
    approved_go_live_at = models.DateTimeField(
        verbose_name=_("approved go live at"), null=True, blank=True, db_index=True
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
            self.page.revisions.exclude(id=self.id).update(
                submitted_for_moderation=False
            )

        if (
            self.approved_go_live_at is None
            and "update_fields" in kwargs
            and "approved_go_live_at" in kwargs["update_fields"]
        ):
            # Log scheduled revision publish cancellation
            page = self.as_page_object()
            # go_live_at = kwargs['update_fields'][]
            log(
                instance=page,
                action="wagtail.schedule.cancel",
                data={
                    "revision": {
                        "id": self.id,
                        "created": self.created_at.strftime("%d %b %Y %H:%M"),
                        "go_live_at": page.go_live_at.strftime("%d %b %Y %H:%M")
                        if page.go_live_at
                        else None,
                    }
                },
                user=user,
                revision=self,
            )

    def as_page_object(self):
        return self.page.specific.with_content_json(self.content)

    def approve_moderation(self, user=None):
        if self.submitted_for_moderation:
            logger.info(
                'Page moderation approved: "%s" id=%d revision_id=%d',
                self.page.title,
                self.page.id,
                self.id,
            )
            log(
                instance=self.as_page_object(),
                action="wagtail.moderation.approve",
                user=user,
                revision=self,
            )
            self.publish()

    def reject_moderation(self, user=None):
        if self.submitted_for_moderation:
            logger.info(
                'Page moderation rejected: "%s" id=%d revision_id=%d',
                self.page.title,
                self.page.id,
                self.id,
            )
            log(
                instance=self.as_page_object(),
                action="wagtail.moderation.reject",
                user=user,
                revision=self,
            )
            self.submitted_for_moderation = False
            self.save(update_fields=["submitted_for_moderation"])

    def is_latest_revision(self):
        if self.id is None:
            # special case: a revision without an ID is presumed to be newly-created and is thus
            # newer than any revision that might exist in the database
            return True
        latest_revision = (
            PageRevision.objects.filter(page_id=self.page_id)
            .order_by("-created_at", "-id")
            .first()
        )
        return latest_revision == self

    def delete(self):
        # Update revision_created fields for comments that reference the current revision, if applicable.

        try:
            next_revision = self.get_next()
        except PageRevision.DoesNotExist:
            next_revision = None

        if next_revision:
            # move comments created on this revision to the next revision, as they may well still apply if they're unresolved
            self.created_comments.all().update(revision_created=next_revision)

        return super().delete()

    def publish(self, user=None, changed=True, log_action=True, previous_revision=None):
        return PublishPageRevisionAction(
            self,
            user=user,
            changed=changed,
            log_action=log_action,
            previous_revision=previous_revision,
        ).execute()

    def get_previous(self):
        return self.get_previous_by_created_at(page=self.page)

    def get_next(self):
        return self.get_next_by_created_at(page=self.page)

    def __str__(self):
        return '"' + str(self.page) + '" at ' + str(self.created_at)

    class Meta:
        verbose_name = _("page revision")
        verbose_name_plural = _("page revisions")


PAGE_PERMISSION_TYPES = [
    ("add", _("Add"), _("Add/edit pages you own")),
    ("edit", _("Edit"), _("Edit any page")),
    ("publish", _("Publish"), _("Publish any page")),
    ("bulk_delete", _("Bulk delete"), _("Delete pages with children")),
    ("lock", _("Lock"), _("Lock/unlock pages you've locked")),
    ("unlock", _("Unlock"), _("Unlock any page")),
]

PAGE_PERMISSION_TYPE_CHOICES = [
    (identifier, long_label)
    for identifier, short_label, long_label in PAGE_PERMISSION_TYPES
]


class GroupPagePermission(models.Model):
    group = models.ForeignKey(
        Group,
        verbose_name=_("group"),
        related_name="page_permissions",
        on_delete=models.CASCADE,
    )
    page = models.ForeignKey(
        "Page",
        verbose_name=_("page"),
        related_name="group_permissions",
        on_delete=models.CASCADE,
    )
    permission_type = models.CharField(
        verbose_name=_("permission type"),
        max_length=20,
        choices=PAGE_PERMISSION_TYPE_CHOICES,
    )

    class Meta:
        unique_together = ("group", "page", "permission_type")
        verbose_name = _("group page permission")
        verbose_name_plural = _("group page permissions")

    def __str__(self):
        return "Group %d ('%s') has permission '%s' on page %d ('%s')" % (
            self.group.id,
            self.group,
            self.permission_type,
            self.page.id,
            self.page,
        )


class UserPagePermissionsProxy:
    """Helper object that encapsulates all the page permission rules that this user has
    across the page hierarchy."""

    def __init__(self, user):
        self.user = user

        if user.is_active and not user.is_superuser:
            self.permissions = GroupPagePermission.objects.filter(
                group__user=self.user
            ).select_related("page")

    def revisions_for_moderation(self):
        """Return a queryset of page revisions awaiting moderation that this user has publish permission on"""

        # Deal with the trivial cases first...
        if not self.user.is_active:
            return PageRevision.objects.none()
        if self.user.is_superuser:
            return PageRevision.submitted_revisions.all()

        # get the list of pages for which they have direct publish permission
        # (i.e. they can publish any page within this subtree)
        publishable_pages_paths = (
            self.permissions.filter(permission_type="publish")
            .values_list("page__path", flat=True)
            .distinct()
        )
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
            explorable_pages |= Page.objects.descendant_of(perm.page, inclusive=True)

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

        for perm in self.permissions.filter(permission_type="add"):
            # user has edit permission on any subpage of perm.page
            # (including perm.page itself) that is owned by them
            editable_pages |= Page.objects.descendant_of(
                perm.page, inclusive=True
            ).filter(owner=self.user)

        for perm in self.permissions.filter(permission_type="edit"):
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

        for perm in self.permissions.filter(permission_type="publish"):
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
            return self.permissions.filter(permission_type="unlock").exists()


class PagePermissionTester:
    def __init__(self, user_perms, page):
        self.user = user_perms.user
        self.user_perms = user_perms
        self.page = page
        self.page_is_root = page.depth == 1  # Equivalent to page.is_root()

        if self.user.is_active and not self.user.is_superuser:
            self.permissions = {
                perm.permission_type
                for perm in user_perms.permissions
                if self.page.path.startswith(perm.page.path)
            }

    def user_has_lock(self):
        return self.page.locked_by_id == self.user.pk

    def page_locked(self):
        current_workflow_task = self.page.current_workflow_task
        if current_workflow_task:
            if current_workflow_task.page_locked_for_user(self.page, self.user):
                return True

        if not self.page.locked:
            # Page is not locked
            return False

        if getattr(settings, "WAGTAILADMIN_GLOBAL_PAGE_EDIT_LOCK", False):
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
        return self.user.is_superuser or ("add" in self.permissions)

    def can_edit(self):
        if not self.user.is_active:
            return False

        if (
            self.page_is_root
        ):  # root node is not a page and can never be edited, even by superusers
            return False

        if self.user.is_superuser:
            return True

        if "edit" in self.permissions:
            return True

        if "add" in self.permissions and self.page.owner_id == self.user.pk:
            return True

        current_workflow_task = self.page.current_workflow_task
        if current_workflow_task:
            if current_workflow_task.user_can_access_editor(self.page, self.user):
                return True

        return False

    def can_delete(self, ignore_bulk=False):
        if not self.user.is_active:
            return False

        if (
            self.page_is_root
        ):  # root node is not a page and can never be deleted, even by superusers
            return False

        if self.user.is_superuser:
            # superusers require no further checks
            return True

        # if the user does not have bulk_delete permission, they may only delete leaf pages
        if (
            "bulk_delete" not in self.permissions
            and not self.page.is_leaf()
            and not ignore_bulk
        ):
            return False

        if "edit" in self.permissions:
            # if the user does not have publish permission, we also need to confirm that there
            # are no published pages here
            if "publish" not in self.permissions:
                pages_to_delete = self.page.get_descendants(inclusive=True)
                if pages_to_delete.live().exists():
                    return False

            return True

        elif "add" in self.permissions:
            pages_to_delete = self.page.get_descendants(inclusive=True)
            if "publish" in self.permissions:
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

        return self.user.is_superuser or ("publish" in self.permissions)

    def can_publish(self):
        if not self.user.is_active:
            return False
        if self.page_is_root:
            return False

        return self.user.is_superuser or ("publish" in self.permissions)

    def can_submit_for_moderation(self):
        return (
            not self.page_locked()
            and self.page.has_workflow
            and not self.page.workflow_in_progress
        )

    def can_set_view_restrictions(self):
        return self.can_publish()

    def can_unschedule(self):
        return self.can_publish()

    def can_lock(self):
        if self.user.is_superuser:
            return True
        current_workflow_task = self.page.current_workflow_task
        if current_workflow_task:
            return current_workflow_task.user_can_lock(self.page, self.user)

        if "lock" in self.permissions:
            return True

        return False

    def can_unlock(self):
        if self.user.is_superuser:
            return True

        if self.user_has_lock():
            return True

        current_workflow_task = self.page.current_workflow_task
        if current_workflow_task:
            return current_workflow_task.user_can_unlock(self.page, self.user)

        if "unlock" in self.permissions:
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

        return self.user.is_superuser or ("publish" in self.permissions)

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
        if "add" not in destination_perms.permissions:
            return False

        if self.page.live or self.page.get_descendants().filter(live=True).exists():
            # moving this page will entail publishing within the destination section
            return "publish" in destination_perms.permissions
        else:
            # no publishing required, so the already-tested 'add' permission is sufficient
            return True

    def can_copy_to(self, destination, recursive=False):
        # reject the logically impossible cases first
        # recursive can't copy to the same tree otherwise it will be on infinite loop
        if recursive and (
            self.page == destination or destination.is_descendant_of(self.page)
        ):
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
        if "add" not in destination_perms.permissions:
            return False

        return True

    def can_view_revisions(self):
        return not self.page_is_root


class PageViewRestriction(BaseViewRestriction):
    page = models.ForeignKey(
        "Page",
        verbose_name=_("page"),
        related_name="view_restrictions",
        on_delete=models.CASCADE,
    )

    passed_view_restrictions_session_key = "passed_page_view_restrictions"

    class Meta:
        verbose_name = _("page view restriction")
        verbose_name_plural = _("page view restrictions")

    def save(self, user=None, **kwargs):
        """
        Custom save handler to include logging.
        :param user: the user add/updating the view restriction
        :param specific_instance: the specific model instance the restriction applies to
        """
        specific_instance = self.page.specific
        is_new = self.id is None
        super().save(**kwargs)

        if specific_instance:
            log(
                instance=specific_instance,
                action="wagtail.view_restriction.create"
                if is_new
                else "wagtail.view_restriction.edit",
                user=user,
                data={
                    "restriction": {
                        "type": self.restriction_type,
                        "title": force_str(
                            dict(self.RESTRICTION_CHOICES).get(self.restriction_type)
                        ),
                    }
                },
            )

    def delete(self, user=None, **kwargs):
        """
        Custom delete handler to aid in logging
        :param user: the user removing the view restriction
        :param specific_instance: the specific model instance the restriction applies to
        """
        specific_instance = self.page.specific
        if specific_instance:
            log(
                instance=specific_instance,
                action="wagtail.view_restriction.delete",
                user=user,
                data={
                    "restriction": {
                        "type": self.restriction_type,
                        "title": force_str(
                            dict(self.RESTRICTION_CHOICES).get(self.restriction_type)
                        ),
                    }
                },
            )
        return super().delete(**kwargs)


class WorkflowPage(models.Model):
    page = models.OneToOneField(
        "Page",
        verbose_name=_("page"),
        on_delete=models.CASCADE,
        primary_key=True,
        unique=True,
    )
    workflow = models.ForeignKey(
        "Workflow",
        related_name="workflow_pages",
        verbose_name=_("workflow"),
        on_delete=models.CASCADE,
    )

    def get_pages(self):
        """
        Returns a queryset of pages that are affected by this WorkflowPage link.

        This includes all descendants of the page excluding any that have other WorkflowPages.
        """
        descendant_pages = Page.objects.descendant_of(self.page, inclusive=True)
        descendant_workflow_pages = WorkflowPage.objects.filter(
            page_id__in=descendant_pages.values_list("id", flat=True)
        ).exclude(pk=self.pk)

        for path, depth in descendant_workflow_pages.values_list(
            "page__path", "page__depth"
        ):
            descendant_pages = descendant_pages.exclude(
                path__startswith=path, depth__gte=depth
            )

        return descendant_pages

    class Meta:
        verbose_name = _("workflow page")
        verbose_name_plural = _("workflow pages")
