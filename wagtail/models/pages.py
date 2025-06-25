from __future__ import annotations

import functools
import logging
import posixpath
import uuid

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core import checks
from django.core.exceptions import (
    FieldDoesNotExist,
    ValidationError,
)
from django.db import models, transaction
from django.db.models import Q, Value
from django.db.models.expressions import Subquery
from django.db.models.functions import Concat, Substr
from django.dispatch import receiver
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseNotAllowed
from django.template.response import TemplateResponse
from django.urls import NoReverseMatch, reverse
from django.utils import translation as translation
from django.utils.encoding import force_bytes, force_str
from django.utils.functional import Promise, cached_property
from django.utils.log import log_response
from django.utils.text import capfirst, slugify
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import (
    ClusterableModel,
)
from treebeard.mp_tree import MP_Node

from wagtail.actions.copy_for_translation import CopyPageForTranslationAction
from wagtail.actions.copy_page import CopyPageAction
from wagtail.actions.create_alias import CreatePageAliasAction
from wagtail.actions.delete_page import DeletePageAction
from wagtail.actions.move_page import MovePageAction
from wagtail.actions.publish_page_revision import PublishPageRevisionAction
from wagtail.actions.unpublish_page import UnpublishPageAction
from wagtail.compat import HTTPMethod
from wagtail.coreutils import (
    WAGTAIL_APPEND_SLASH,
    camelcase_to_underscore,
    get_supported_content_language_variant,
    resolve_model_string,
    safe_md5,
)
from wagtail.fields import StreamField
from wagtail.log_actions import log
from wagtail.query import PageQuerySet
from wagtail.search import index
from wagtail.signals import (
    page_published,
    page_slug_changed,
    pre_validate_delete,
)
from wagtail.url_routing import RouteResult
from wagtail.utils.timestamps import ensure_utc

from .audit_log import BaseLogEntry, BaseLogEntryManager, LogEntryQuerySet
from .content_types import get_default_page_content_type
from .copying import _copy_m2m_relations
from .draft_state import DraftStateMixin
from .i18n import Locale, TranslatableMixin
from .locking import LockableMixin
from .panels import CommentPanelPlaceholder, PanelPlaceholder
from .preview import PreviewableMixin
from .revisions import Revision, RevisionMixin
from .sites import Site
from .specific import SpecificMixin
from .view_restrictions import BaseViewRestriction
from .workflows import WorkflowMixin

logger = logging.getLogger("wagtail")

PAGE_TEMPLATE_VAR = "page"
COMMENTS_RELATION_NAME = getattr(
    settings, "WAGTAIL_COMMENTS_RELATION_NAME", "wagtail_admin_comments"
)


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
    return PAGE_MODEL_CLASSES.copy()


def get_page_content_types(include_base_page_type=True):
    """
    Returns a queryset of all ContentType objects corresponding to Page model classes.
    """
    models = get_page_models()
    if not include_base_page_type:
        models.remove(Page)

    content_type_ids = [
        ct.pk for ct in ContentType.objects.get_for_models(*models).values()
    ]
    return ContentType.objects.filter(pk__in=content_type_ids).order_by("model")


@functools.cache
def get_streamfield_names(model_class):
    return tuple(
        field.name
        for field in model_class._meta.concrete_fields
        if isinstance(field, StreamField)
    )


class BasePageManager(models.Manager):
    def get_queryset(self):
        return self._queryset_class(self.model).order_by("path")

    def first_common_ancestor_of(self, pages, include_self=False, strict=False):
        """
        This is similar to ``PageQuerySet.first_common_ancestor`` but works
        for a list of pages instead of a queryset.
        """
        if not pages:
            if strict:
                raise self.model.DoesNotExist("Can not find ancestor of empty list")
            return self.model.get_first_root_node()

        if include_self:
            paths = list({page.path for page in pages})
        else:
            paths = list({page.path[: -self.model.steplen] for page in pages})

        # This method works on anything, not just file system paths.
        common_parent_path = posixpath.commonprefix(paths)
        extra_chars = len(common_parent_path) % self.model.steplen
        if extra_chars != 0:
            common_parent_path = common_parent_path[:-extra_chars]

        if common_parent_path == "":
            if strict:
                raise self.model.DoesNotExist("No common ancestor found!")

            return self.model.get_first_root_node()

        return self.get(path=common_parent_path)

    def annotate_parent_page(self, pages):
        """
        Annotates each page with its parent page. This is implemented as a
        manager-only method instead of a QuerySet method so it can be used with
        search results.

        If given a QuerySet, this method will evaluate it. Only use this method
        when you are ready to consume the queryset, e.g. after pagination has
        been applied. This is typically done in the view's ``get_context_data``
        using ``context["object_list"]``.

        This method does not return a new queryset, but modifies the existing one,
        to ensure any references to the queryset in the view's context are updated
        (e.g. when using ``context_object_name``).
        """
        parent_page_paths = {
            Page._get_parent_path_from_path(page.path) for page in pages
        }
        parent_pages_by_path = {
            page.path: page
            for page in Page.objects.filter(path__in=parent_page_paths).specific(
                defer=True
            )
        }
        for page in pages:
            parent_page = parent_pages_by_path.get(
                Page._get_parent_path_from_path(page.path)
            )
            page._parent_page = parent_page


PageManager = BasePageManager.from_queryset(PageQuerySet)


class PageBase(models.base.ModelBase):
    """Metaclass for Page"""

    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)

        if "template" not in dct:
            # Define a default template path derived from the app name and model name
            cls.template = "{}/{}.html".format(
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


class AbstractPage(
    WorkflowMixin,
    PreviewableMixin,
    DraftStateMixin,
    LockableMixin,
    RevisionMixin,
    TranslatableMixin,
    SpecificMixin,
    MP_Node,
):
    """
    Abstract superclass for Page. According to Django's inheritance rules, managers set on
    abstract models are inherited by subclasses, but managers set on concrete models that are extended
    via multi-table inheritance are not. We therefore need to attach PageManager to an abstract
    superclass to ensure that it is retained by subclasses of Page.
    """

    objects = PageManager()

    class Meta:
        abstract = True


# Make sure that this list is sorted by the codename (first item in the tuple)
# so that we can follow the same order when querying the Permission objects.
PAGE_PERMISSION_TYPES = [
    ("add_page", _("Add"), _("Add/edit pages you own")),
    ("bulk_delete_page", _("Bulk delete"), _("Delete pages with children")),
    ("change_page", _("Edit"), _("Edit any page")),
    ("lock_page", _("Lock"), _("Lock/unlock pages you've locked")),
    ("publish_page", _("Publish"), _("Publish any page")),
    ("unlock_page", _("Unlock"), _("Unlock any page")),
]

PAGE_PERMISSION_TYPE_CHOICES = [
    (identifier[:-5], long_label) for identifier, _, long_label in PAGE_PERMISSION_TYPES
]

PAGE_PERMISSION_CODENAMES = [identifier for identifier, *_ in PAGE_PERMISSION_TYPES]


class Page(AbstractPage, index.Indexed, ClusterableModel, metaclass=PageBase):
    title = models.CharField(
        verbose_name=_("title"),
        max_length=255,
        help_text=_("The page title as you'd like it to be seen by the public"),
    )
    title.required_on_save = True
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
    content_type.wagtail_reference_index_ignore = True
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
    owner.wagtail_reference_index_ignore = True

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

    latest_revision_created_at = models.DateTimeField(
        verbose_name=_("latest revision created at"), null=True, editable=False
    )

    _revisions = GenericRelation(
        "wagtailcore.Revision",
        content_type_field="content_type",
        object_id_field="object_id",
        related_query_name="page",
        for_concrete_model=False,
    )

    # Override WorkflowMixin's GenericRelation to specify related_query_name
    # so we can do WorkflowState.objects.filter(page=...) queries.
    # There is no need to override the workflow_states property, as the default
    # implementation in WorkflowMixin already ensures that the queryset uses the
    # base Page content type.
    _workflow_states = GenericRelation(
        "wagtailcore.WorkflowState",
        content_type_field="base_content_type",
        object_id_field="object_id",
        related_query_name="page",
        for_concrete_model=False,
    )

    # When using a specific queryset, accessing the _workflow_states GenericRelation
    # will yield no results. This is because the _workflow_states GenericRelation
    # uses the base_content_type as the content_type_field, which is not the same
    # as the content type of the specific queryset. To work around this, we define
    # a second GenericRelation that uses the specific content_type to be used
    # when working with specific querysets.
    _specific_workflow_states = GenericRelation(
        "wagtailcore.WorkflowState",
        content_type_field="content_type",
        object_id_field="object_id",
        related_query_name="page",
        for_concrete_model=False,
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
    alias_of.wagtail_reference_index_ignore = True

    search_fields = [
        index.SearchField("title", boost=2),
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

    # Set the default order for child pages to be shown in the Page index listing
    admin_default_ordering = "-latest_revision_created_at"

    # An array of additional field names that will not be included when a Page is copied.
    exclude_fields_in_copy = []
    default_exclude_fields_in_copy = [
        "id",
        "depth",
        "numchild",
        "url_path",
        "path",
        "postgres_index_entries",
        "index_entries",
        "latest_revision",
        COMMENTS_RELATION_NAME,
    ]

    # Real panel classes are defined in wagtail.admin.panels, which we can't import here
    # because it would create a circular import. Instead, define them with placeholders
    # to be replaced with the real classes by `wagtail.admin.panels.model_utils.expand_panel_list`.
    content_panels = [
        PanelPlaceholder("wagtail.admin.panels.TitleFieldPanel", ["title"], {}),
    ]
    promote_panels = [
        PanelPlaceholder(
            "wagtail.admin.panels.MultiFieldPanel",
            [
                [
                    "slug",
                    "seo_title",
                    "search_description",
                ],
                _("For search engines"),
            ],
            {},
        ),
        PanelPlaceholder(
            "wagtail.admin.panels.MultiFieldPanel",
            [
                [
                    "show_in_menus",
                ],
                _("For site menus"),
            ],
            {},
        ),
    ]
    settings_panels = [
        PanelPlaceholder("wagtail.admin.panels.PublishingPanel", [], {}),
        CommentPanelPlaceholder(),
    ]

    # Privacy options for page
    private_page_options = ["password", "groups", "login"]

    # Allows page types to specify a list of HTTP method names that page instances will
    # respond to. When the request type doesn't match, Wagtail should return a response
    # with a status code of 405.
    allowed_http_methods = [
        HTTPMethod.DELETE,
        HTTPMethod.GET,
        HTTPMethod.HEAD,
        HTTPMethod.OPTIONS,
        HTTPMethod.PATCH,
        HTTPMethod.POST,
        HTTPMethod.PUT,
    ]

    @staticmethod
    def route_for_request(request: HttpRequest, path: str) -> RouteResult | None:
        """
        Find the page route for the given HTTP request object, and URL path. The route
        result (`page`, `args`, and `kwargs`) will be cached via
        ``request._wagtail_route_for_request``.
        """
        if not hasattr(request, "_wagtail_route_for_request"):
            try:
                # we need a valid Site object for this request in order to proceed
                if site := Site.find_for_request(request):
                    path_components = [
                        component for component in path.split("/") if component
                    ]
                    request._wagtail_route_for_request = (
                        site.root_page.localized.specific.route(
                            request, path_components
                        )
                    )
                else:
                    request._wagtail_route_for_request = None
            except Http404:
                # .route() can raise Http404
                request._wagtail_route_for_request = None

        return request._wagtail_route_for_request

    @staticmethod
    def find_for_request(request: HttpRequest, path: str) -> Page | None:
        """
        Find the page for the given HTTP request object, and URL path. The full
        page route will be cached via ``request._wagtail_route_for_request``.
        """
        result = Page.route_for_request(request, path)
        if result is not None:
            return result[0]

    @classmethod
    def allowed_http_method_names(cls):
        return [
            method.value if hasattr(method, "value") else method
            for method in cls.allowed_http_methods
        ]

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

    @property
    def revisions(self):
        # Always use the specific page instance when querying for revisions as
        # they are always saved with the specific content_type.
        return self.specific_deferred._revisions

    def get_base_content_type(self):
        # We want to always use the default Page model's ContentType as the
        # base_content_type so that we can query for page revisions without
        # having to know the specific Page type.
        return get_default_page_content_type()

    def get_content_type(self):
        return self.content_type

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

    def get_admin_default_ordering(self):
        """
        Determine the default ordering for child pages in the admin index listing.
        Returns a string (e.g. 'latest_revision_created_at, title, ord' or 'live').
        """
        return self.admin_default_ordering

    def _set_core_field_defaults(self):
        """
        Set default values for core fields (slug, draft_title, locale) that need to be
        in place before validating or saving
        """
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

    def full_clean(self, *args, **kwargs):
        self._set_core_field_defaults()
        super().full_clean(*args, **kwargs)

    def _check_slug_is_unique(self):
        parent_page = self.get_parent()
        if not Page._slug_is_available(self.slug, parent_page, self):
            raise ValidationError(
                {
                    "slug": _(
                        "The slug '%(page_slug)s' is already in use within the parent page at '%(parent_url_path)s'"
                    )
                    % {"page_slug": self.slug, "parent_url_path": parent_page.url}
                }
            )

    def clean(self):
        super().clean()
        self._check_slug_is_unique()

    def minimal_clean(self):
        self._set_core_field_defaults()
        self.title = self._meta.get_field("title").clean(self.title, self)
        self._check_slug_is_unique()

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
        Writes the page to the database, performing additional housekeeping tasks to ensure data
        integrity:

        * ``locale``, ``draft_title`` and ``slug`` are set to default values if not provided, with ``slug``
          being generated from the title with a suffix to ensure uniqueness within the parent page
          where necessary
        * The ``url_path`` field is set based on the ``slug`` and the parent page
        * If the ``slug`` has changed, the ``url_path`` of this page and all descendants is updated and
          a :ref:`page_slug_changed` signal is sent

        New pages should be saved by passing the unsaved page instance to the
        :meth:`~treebeard.mp_tree.MP_Node.add_child`
        or :meth:`~treebeard.mp_tree.MP_Node.add_sibling` method of an existing page, which will correctly update
        the fields responsible for tracking the page's location in the tree.

        If ``clean=False`` is passed, the page is saved without validation. This is appropriate for updates that only
        change metadata such as `latest_revision` while keeping content and page location unchanged.

        If ``clean=True`` is passed (the default), and the page has ``live=True`` set, the page is validated using
        :meth:`~django.db.models.Model.full_clean` before saving.

        If ``clean=True`` is passed, and the page has ``live=False`` set, only the title and slug fields are validated.

        .. versionchanged:: 7.0
           ``clean=True`` now only performs full validation when the page is live. When the page is not live, only
           the title and slug fields are validated. Previously, full validation was always performed.
        """
        if clean:
            if self.live:
                self.full_clean()
            else:
                # Saving as draft; only perform the minimal validation to satisfy data integrity
                self.minimal_clean()

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
            Site.clear_site_root_paths_cache()

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
        errors = super().check(**kwargs)

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

    @property
    def page_type_display_name(self):
        """
        A human-readable version of this page's type.
        """
        if not self.specific_class or self.is_root():
            return ""
        else:
            return self.specific_class.get_verbose_name()

    def route(self, request, path_components):
        if path_components:
            # request is for a child of this page
            child_slug = path_components[0]
            remaining_components = path_components[1:]

            try:
                subpage = self.get_children().get(slug=child_slug)
                # Cache the parent page on the subpage to avoid another db query
                # Treebeard's get_parent will use the `_cached_parent_obj` attribute if it exists
                # And update = False
                setattr(subpage, "_cached_parent_obj", self)

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
        approved_go_live_at=None,
        changed=True,
        log_action=False,
        previous_revision=None,
        clean=True,
    ):
        # Raise error if this is not the specific version of the page
        if not isinstance(self, self.specific_class):
            raise RuntimeError(
                "page.save_revision() must be called on the specific version of the page. "
                "Call page.specific.save_revision() instead."
            )

        # Raise an error if this page is an alias.
        if self.alias_of_id:
            raise RuntimeError(
                "page.save_revision() was called on an alias page. "
                "Revisions are not required for alias pages as they are an exact copy of another page."
            )

        if clean:
            self.full_clean()

        new_comments = getattr(self, COMMENTS_RELATION_NAME).filter(pk__isnull=True)
        for comment in new_comments:
            # We need to ensure comments have an id in the revision, so positions can be identified correctly
            comment.save()

        revision = Revision.objects.create(
            content_object=self,
            base_content_type=self.get_base_content_type(),
            user=user,
            approved_go_live_at=approved_go_live_at,
            content=self.serializable_data(),
            object_str=str(self),
        )

        for comment in new_comments:
            comment.revision_created = revision

        self.latest_revision_created_at = revision.created_at
        self.draft_title = self.title
        self.latest_revision = revision

        update_fields = [
            COMMENTS_RELATION_NAME,
            "latest_revision_created_at",
            "draft_title",
            "latest_revision",
        ]

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
                            "created": ensure_utc(previous_revision.created_at),
                        }
                    },
                    revision=revision,
                    content_changed=changed,
                )

        return revision

    def get_latest_revision_as_object(self):
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
            return latest_revision.as_object()
        else:
            return self.specific

    def update_aliases(self, *, revision=None, _content=None, _updated_ids=None):
        """
        Publishes all aliases that follow this page with the latest content from this page.

        This is called by Wagtail whenever a page with aliases is published.

        :param revision: The revision of the original page that we are updating to (used for logging purposes)
        :type revision: Revision, Optional
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

    def publish(
        self,
        revision,
        user=None,
        changed=True,
        log_action=True,
        previous_revision=None,
        skip_permission_checks=False,
    ):
        return PublishPageRevisionAction(
            revision,
            user=user,
            changed=changed,
            log_action=log_action,
            previous_revision=previous_revision,
        ).execute(skip_permission_checks=skip_permission_checks)

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

    def get_preview_context(self, request, mode_name):
        return self.get_context(request)

    def get_template(self, request, *args, **kwargs):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return self.ajax_template or self.template
        else:
            return self.template

    def get_preview_template(self, request, mode_name):
        return self.get_template(request)

    def serve(self, request, *args, **kwargs):
        request.is_preview = False

        return TemplateResponse(
            request,
            self.get_template(request, *args, **kwargs),
            self.get_context(request, *args, **kwargs),
        )

    def check_request_method(self, request, *args, **kwargs):
        """
        Checks the ``method`` attribute of the request against those supported
        by the page (as defined by :attr:`allowed_http_methods`) and responds
        accordingly.

        If supported, ``None`` is returned, and the request is processed
        normally. If not, a warning is logged and an ``HttpResponseNotAllowed``
        is returned, and any further request handling is terminated.
        """
        allowed_methods = self.allowed_http_method_names()
        if request.method not in allowed_methods:
            response = HttpResponseNotAllowed(allowed_methods)
            log_response(
                "Method Not Allowed (%s): %s",
                request.method,
                request.path,
                request=request,
                response=response,
            )
            return response

    def handle_options_request(self, request, *args, **kwargs):
        """
        Returns an ``HttpResponse`` with an ``"Allow"`` header containing the list of
        supported HTTP methods for this page. This method is used instead of
        :meth:`serve` to handle requests when the ``OPTIONS`` HTTP verb is
        detected (and :class:`HTTPMethod.OPTIONS <python:http.HTTPMethod>` is
        present in :attr:`allowed_http_methods` for this type of page).
        """
        return HttpResponse(
            headers={"Allow": ", ".join(self.allowed_http_method_names())}
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
        Return ``None`` if the page is not routable, or return
        ``(site_id, None, None)`` if ``NoReverseMatch`` exception is raised.

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

        # Thanks to the ordering applied by Site.get_site_root_paths(),
        # the first item is ideal in the vast majority of setups.
        site_id, root_path, root_url, language_code = possible_sites[0]

        unique_site_ids = {values[0] for values in possible_sites}
        if len(unique_site_ids) > 1 and isinstance(request, HttpRequest):
            # The page somehow belongs to more than one site (rare, but possible).
            # If 'request' is indeed a HttpRequest, use it to identify the 'current'
            # site and prefer an option matching that (where present).
            site = Site.find_for_request(request)
            if site:
                for values in possible_sites:
                    if values[0] == site.pk:
                        site_id, root_path, root_url, language_code = values
                        break

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
        """
        Return the full URL (including protocol / domain) to this page, or ``None`` if it is not routable.
        """
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
        Return ``None`` if the page is not routable.

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
        Return ``None`` if the page is not routable.

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
        return super().get_indexed_objects().filter(content_type=content_type)

    def get_indexed_instance(self):
        # This is accessed on save by the wagtailsearch signal handler, and in edge
        # cases (e.g. loading test fixtures), may be called before the specific instance's
        # entry has been created. In those cases, we aren't ready to be indexed yet, so
        # return None.
        try:
            return self.specific
        except self.specific_class.DoesNotExist:
            return None

    def get_default_privacy_setting(self, request: HttpRequest):
        """Set the default privacy setting for a page."""
        return {"type": BaseViewRestriction.NONE}

    @classmethod
    def clean_subpage_models(cls):
        """
        Returns the list of subpage types, normalized as model classes.
        Throws ValueError if any entry in subpage_types cannot be recognized as a model name,
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
        Returns the list of parent page types, normalized as model classes.
        Throws ValueError if any entry in parent_page_types cannot be recognized as a model name,
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
        as a list of model classes.
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
        as a list of model classes.
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
        as a list of model classes.
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

    @classmethod
    def get_page_description(cls):
        """
        Returns a page description if it's set. For example "A multi-purpose web page".
        """
        description = getattr(cls, "page_description", None)

        # make sure that page_description is actually a string rather than a model field
        if isinstance(description, str):
            return description
        elif isinstance(description, Promise):
            # description is a lazy object (e.g. the result of gettext_lazy())
            return str(description)
        else:
            return ""

    @property
    def approved_schedule(self):
        """
        ``_approved_schedule`` may be populated by ``annotate_approved_schedule`` on ``PageQuerySet`` as a
        performance optimization.
        """
        if hasattr(self, "_approved_schedule"):
            return self._approved_schedule

        return self.scheduled_revision is not None

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

        :param log_action: flag for logging the action. Pass None to skip logging. Can be passed an action string. Defaults to ``'wagtail.copy'``.
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
        Return a PagePermissionsTester object defining what actions the user can perform on this page.
        """
        # Allow specific classes to override this method, but only cast to the
        # specific instance if it's not already specific and if the method has
        # been overridden. This helps improve performance when working with
        # base Page querysets.
        is_overridden = (
            self.specific_class
            and self.specific_class.permissions_for_user
            != type(self).permissions_for_user
        )
        if is_overridden and not isinstance(self, self.specific_class):
            return self.specific_deferred.permissions_for_user(user)
        return PagePermissionTester(user, self)

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

    def get_route_paths(self):
        """
        Returns a list of paths that this page can be viewed at.

        These values are combined with the dynamic portion of the page URL to
        automatically create redirects when the page's URL changes.

        .. note::

            If using ``RoutablePageMixin``, you may want to override this method
            to include the paths of popular routes.

        .. note::

            Redirect paths are 'normalized' to apply consistent ordering to GET parameters,
            so you don't need to include every variation. Fragment identifiers are discarded
            too, so should be avoided.
        """
        return ["/"]

    def get_cached_paths(self):
        """
        This returns a list of paths to invalidate in a frontend cache
        """
        return ["/"]

    def get_cache_key_components(self):
        """
        The components of a :class:`Page` which make up the :attr:`cache_key`. Any change to a
        page should be reflected in a change to at least one of these components.
        """

        return [
            self.id,
            self.url_path,
            self.last_published_at.isoformat() if self.last_published_at else None,
        ]

    @property
    def cache_key(self):
        """
        A generic cache key to identify a page in its current state.
        Should the page change, so will the key.

        Customizations to the cache key should be made in :attr:`get_cache_key_components`.
        """

        hasher = safe_md5()

        for component in self.get_cache_key_components():
            hasher.update(force_bytes(component))

        return hasher.hexdigest()

    def get_sitemap_urls(self, request=None):
        return [
            {
                "location": self.get_full_url(request),
                # fall back on latest_revision_created_at if last_published_at is null
                # (for backwards compatibility from before last_published_at was added)
                "lastmod": (self.last_published_at or self.latest_revision_created_at),
            }
        ]

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

    password_required_template = None

    def serve_password_required_response(self, request, form, action_url):
        """
        Serve a response indicating that the user has been denied access to view this page,
        and must supply a password.
        ``form`` = a Django form object containing the password input
            (and zero or more hidden fields that also need to be output on the template)
        ``action_url`` = URL that this form should be POSTed to
        """

        password_required_template = self.password_required_template or getattr(
            settings,
            "WAGTAIL_PASSWORD_REQUIRED_TEMPLATE",
            "wagtailcore/password_required.html",
        )

        context = self.get_context(request)
        context["form"] = form
        context["action_url"] = action_url
        return TemplateResponse(request, password_required_template, context)

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
        * ``latest_revision``
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
        obj.content_type_id = self.content_type_id

        # Override possibly-outdated tree parameter fields
        obj.path = self.path
        obj.depth = self.depth
        obj.numchild = self.numchild

        # Update url_path to reflect potential slug changes, but maintaining the page's
        # existing tree position
        obj.set_url_path(self.get_parent())

        # Ensure other values that are meaningful for the page as a whole (rather than
        # to a specific revision) are preserved
        obj.draft_title = self.draft_title
        obj.live = self.live
        obj.has_unpublished_changes = self.has_unpublished_changes
        obj.owner_id = self.owner_id
        obj.locked = self.locked
        obj.locked_by_id = self.locked_by_id
        obj.locked_at = self.locked_at
        obj.latest_revision_id = self.latest_revision_id
        obj.latest_revision_created_at = self.latest_revision_created_at

        if obj.first_published_at is None:
            obj.first_published_at = self.first_published_at

        obj.translation_key = self.translation_key
        obj.locale_id = self.locale_id
        obj.alias_of_id = self.alias_of_id
        revision_comment_positions = dict(
            getattr(obj, COMMENTS_RELATION_NAME).values_list("id", "position")
        )
        page_comments = (
            getattr(self, COMMENTS_RELATION_NAME)
            .filter(resolved_at__isnull=True)
            .defer("position")
        )
        for comment in page_comments:
            # attempt to retrieve the comment position from the revision's stored version
            # of the comment
            try:
                comment.position = revision_comment_positions[comment.id]
            except KeyError:
                pass
        setattr(obj, COMMENTS_RELATION_NAME, page_comments)

        return obj

    @property
    def has_workflow(self):
        """
        Returns ``True`` if the page or an ancestor has an active workflow assigned, otherwise ``False``.
        """
        if not getattr(settings, "WAGTAIL_WORKFLOW_ENABLED", True):
            return False
        return (
            self.get_ancestors(inclusive=True)
            .filter(workflowpage__isnull=False)
            .filter(workflowpage__workflow__active=True)
            .exists()
        )

    def get_workflow(self):
        """
        Returns the active workflow assigned to the page or its nearest ancestor.
        """
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

    class Meta:
        verbose_name = _("page")
        verbose_name_plural = _("pages")
        unique_together = [("translation_key", "locale")]
        # Make sure that we auto-create Permission objects that are defined in
        # PAGE_PERMISSION_TYPES, skipping the default_permissions from Django.
        permissions = [
            (codename, name)
            for codename, _, name in PAGE_PERMISSION_TYPES
            if codename not in {"add_page", "change_page", "delete_page", "view_page"}
        ]


# set module path of Page so that when Sphinx autodoc sees Page in type annotations
# it won't complain that there's no target for wagtail.models.pages.Page
Page.__module__ = "wagtail.models"


class GroupPagePermissionManager(models.Manager):
    def create(self, **kwargs):
        # Simplify creation of GroupPagePermission objects by allowing one
        # of permission or permission_type to be passed in.
        permission = kwargs.get("permission")
        permission_type = kwargs.pop("permission_type", None)
        if not permission and permission_type:
            kwargs["permission"] = Permission.objects.get(
                content_type=get_default_page_content_type(),
                codename=f"{permission_type}_page",
            )
        return super().create(**kwargs)


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
    permission = models.ForeignKey(
        Permission,
        verbose_name=_("permission"),
        on_delete=models.CASCADE,
    )

    objects = GroupPagePermissionManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("group", "page", "permission"),
                name="unique_permission",
            ),
        ]
        verbose_name = _("group page permission")
        verbose_name_plural = _("group page permissions")

    def __str__(self):
        return "Group %d ('%s') has permission '%s' on page %d ('%s')" % (
            self.group.id,
            self.group,
            self.permission.codename,
            self.page.id,
            self.page,
        )


class PagePermissionTester:
    def __init__(self, user, page):
        from wagtail.permissions import page_permission_policy

        self.user = user
        self.permission_policy = page_permission_policy
        self.page = page
        self.page_is_root = page.depth == 1  # Equivalent to page.is_root()

        if self.user.is_active and not self.user.is_superuser:
            self.permissions = {
                # Get the 'action' part of the permission codename, e.g.
                # 'add' instead of 'add_page'
                perm.permission.codename.rsplit("_", maxsplit=1)[0]
                for perm in self.permission_policy.get_cached_permissions_for_user(user)
                if self.page.path.startswith(perm.page.path)
            }

    def user_has_lock(self):
        return self.page.locked_by_id == self.user.pk

    def page_locked(self):
        lock = self.page.get_lock()
        return lock and lock.for_user(self.user)

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

        if "change" in self.permissions:
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

        if "change" in self.permissions:
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
        Reorder permission checking is similar to publishing a subpage, since it immediately
        affects published pages. However, it shouldn't care about the 'creatability' of
        page types, because the action only ever updates existing pages.
        """
        if not self.user.is_active:
            return False
        return self.user.is_superuser or ("publish" in self.permissions)

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
        # – but only check this if the page is not already under the target parent.
        # If it already is, then the user is just reordering the page, and we want
        # to allow it even if the page currently violates the subpage_type /
        # parent_page_type rules. This can happen if it was either created before
        # the rules were specified, or it was done programmatically (e.g. to
        # predefine a set of pages and disallow the creation of new subpages by
        # setting subpage_types = []).

        if (not self.page.is_child_of(destination)) and (
            not self.page.specific.can_move_to(destination)
        ):
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
        destination_perms = destination.permissions_for_user(self.user)

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
        destination_perms = destination.permissions_for_user(self.user)

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
        Custom delete handler to aid in logging.
        :param user: the user removing the view restriction
        """
        specific_instance = self.page.specific
        if specific_instance:
            removed_restriction_type = PageViewRestriction.objects.filter(
                id=self.id
            ).values_list("restriction_type", flat=True)[0]
            log(
                instance=specific_instance,
                action="wagtail.view_restriction.delete",
                user=user,
                data={
                    "restriction": {
                        "type": self.restriction_type,
                        "title": force_str(
                            dict(self.RESTRICTION_CHOICES).get(removed_restriction_type)
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
        Returns a queryset of pages that are affected by this ``WorkflowPage`` link.

        This includes all descendants of the page excluding any that have other ``WorkflowPage``(s).
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


class PageLogEntryQuerySet(LogEntryQuerySet):
    def get_content_type_ids(self):
        # for reporting purposes, pages of all types are combined under a single "Page"
        # object type
        if self.exists():
            return {ContentType.objects.get_for_model(Page).pk}
        else:
            return set()

    def filter_on_content_type(self, content_type):
        if content_type == ContentType.objects.get_for_model(Page):
            return self
        else:
            return self.none()


class PageLogEntryManager(BaseLogEntryManager):
    def get_queryset(self):
        return PageLogEntryQuerySet(self.model, using=self._db)

    def get_instance_title(self, instance):
        return instance.specific_deferred.get_admin_display_title()

    def log_action(self, instance, action, **kwargs):
        kwargs.update(page=instance)
        return super().log_action(instance, action, **kwargs)

    def viewable_by_user(self, user):
        from wagtail.permissions import page_permission_policy

        explorable_instances = page_permission_policy.explorable_instances(user)
        q = Q(page__in=explorable_instances.values_list("pk", flat=True))

        root_page_permissions = Page.get_first_root_node().permissions_for_user(user)
        if (
            user.is_superuser
            or root_page_permissions.can_add_subpage()
            or root_page_permissions.can_edit()
        ):
            # Include deleted entries
            q = q | Q(
                page_id__in=Subquery(
                    PageLogEntry.objects.filter(deleted=True).values("page_id")
                )
            )

        return PageLogEntry.objects.filter(q)

    def for_instance(self, instance):
        return self.filter(page=instance)


class PageLogEntry(BaseLogEntry):
    page = models.ForeignKey(
        "wagtailcore.Page",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        related_name="+",
    )

    objects = PageLogEntryManager()

    class Meta:
        ordering = ["-timestamp", "-id"]
        verbose_name = _("page log entry")
        verbose_name_plural = _("page log entries")

    def __str__(self):
        return "PageLogEntry %d: '%s' on '%s' with id %s" % (
            self.pk,
            self.action,
            self.object_verbose_name(),
            self.page_id,
        )

    @cached_property
    def object_id(self):
        return self.page_id

    @cached_property
    def message(self):
        # for page log entries, the 'edit' action should show as 'Draft saved'
        if self.action == "wagtail.edit":
            return _("Draft saved")
        else:
            return super().message


class Comment(ClusterableModel):
    """
    A comment on a field, or a field within a streamfield block
    """

    page = ParentalKey(
        Page, on_delete=models.CASCADE, related_name=COMMENTS_RELATION_NAME
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=COMMENTS_RELATION_NAME,
    )
    text = models.TextField()

    contentpath = models.TextField()
    # This stores the field or field within a streamfield block that the comment is applied on, in the form: 'field', or 'field.block_id.field'
    # This must be unchanging across all revisions, so we will not support (current-format) ListBlock or the contents of InlinePanels initially.

    position = models.TextField(blank=True)
    # This stores the position within a field, to be interpreted by the field's frontend widget. It may change between revisions

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    revision_created = models.ForeignKey(
        Revision,
        on_delete=models.CASCADE,
        related_name="created_comments",
        null=True,
        blank=True,
    )

    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="comments_resolved",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("comment")
        verbose_name_plural = _("comments")

    def __str__(self):
        return "Comment on Page '{}', left by {}: '{}'".format(
            self.page, self.user, self.text
        )

    def save(self, update_position=False, **kwargs):
        # Don't save the position unless specifically instructed to, as the position will normally be retrieved from the revision
        update_fields = kwargs.pop("update_fields", None)
        if not update_position and (
            not update_fields or "position" not in update_fields
        ):
            if self.id:
                # The instance is already saved; we can use `update_fields`
                update_fields = (
                    update_fields if update_fields else self._meta.get_fields()
                )
                update_fields = [
                    field.name
                    for field in update_fields
                    if field.name not in {"position", "id"}
                ]
            else:
                # This is a new instance, we have to preserve and then restore the position via a variable
                position = self.position
                result = super().save(**kwargs)
                self.position = position
                return result
        return super().save(update_fields=update_fields, **kwargs)

    def _log(self, action, page_revision=None, user=None):
        log(
            instance=self.page,
            action=action,
            user=user,
            revision=page_revision,
            data={
                "comment": {
                    "id": self.pk,
                    "contentpath": self.contentpath,
                    "text": self.text,
                }
            },
        )

    def log_create(self, **kwargs):
        self._log("wagtail.comments.create", **kwargs)

    def log_edit(self, **kwargs):
        self._log("wagtail.comments.edit", **kwargs)

    def log_resolve(self, **kwargs):
        self._log("wagtail.comments.resolve", **kwargs)

    def log_delete(self, **kwargs):
        self._log("wagtail.comments.delete", **kwargs)

    def has_valid_contentpath(self, page):
        """
        Return True if this comment's contentpath corresponds to a valid field or
        StreamField block on the given page object.
        """
        field_name, *remainder = self.contentpath.split(".")
        try:
            field = page._meta.get_field(field_name)
        except FieldDoesNotExist:
            return False

        if not remainder:
            # comment applies to the field as a whole
            return True

        if not isinstance(field, StreamField):
            # only StreamField supports content paths that are deeper than one level
            return False

        stream_value = getattr(page, field_name)
        block = field.get_block_by_content_path(stream_value, remainder)
        # content path is valid if this returns a BoundBlock rather than None
        return bool(block)


class CommentReply(models.Model):
    comment = ParentalKey(Comment, on_delete=models.CASCADE, related_name="replies")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comment_replies",
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("comment reply")
        verbose_name_plural = _("comment replies")

    def __str__(self):
        return f"CommentReply left by '{self.user}': '{self.text}'"

    def _log(self, action, page_revision=None, user=None):
        log(
            instance=self.comment.page,
            action=action,
            user=user,
            revision=page_revision,
            data={
                "comment": {
                    "id": self.comment.pk,
                    "contentpath": self.comment.contentpath,
                    "text": self.comment.text,
                },
                "reply": {
                    "id": self.pk,
                    "text": self.text,
                },
            },
        )

    def log_create(self, **kwargs):
        self._log("wagtail.comments.create_reply", **kwargs)

    def log_edit(self, **kwargs):
        self._log("wagtail.comments.edit_reply", **kwargs)

    def log_delete(self, **kwargs):
        self._log("wagtail.comments.delete_reply", **kwargs)


class PageSubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="page_subscriptions",
    )
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="subscribers")

    comment_notifications = models.BooleanField()

    wagtail_reference_index_ignore = True

    class Meta:
        unique_together = [
            ("page", "user"),
        ]
