import posixpath
import warnings
from collections import defaultdict
from typing import Any, Dict, Iterable, Tuple

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import CharField, Prefetch, Q
from django.db.models.expressions import Exists, OuterRef
from django.db.models.functions import Cast, Length, Substr
from django.db.models.query import BaseIterable, ModelIterable
from treebeard.mp_tree import MP_NodeQuerySet

from wagtail.models.sites import Site
from wagtail.search.queryset import SearchableQuerySetMixin


class TreeQuerySet(MP_NodeQuerySet):
    """
    Extends Treebeard's MP_NodeQuerySet with additional useful tree-related operations.
    """

    def delete(self):
        """Redefine the delete method unbound, so we can set the queryset_only parameter."""
        super().delete()

    delete.queryset_only = True

    def descendant_of_q(self, other, inclusive=False):
        q = Q(path__startswith=other.path) & Q(depth__gte=other.depth)

        if not inclusive:
            q &= ~Q(pk=other.pk)

        return q

    def descendant_of(self, other, inclusive=False):
        """
        This filters the QuerySet to only contain pages that descend from the specified page.

        If inclusive is set to True, it will also contain the page itself (instead of just its descendants).
        """
        return self.filter(self.descendant_of_q(other, inclusive))

    def not_descendant_of(self, other, inclusive=False):
        """
        This filters the QuerySet to not contain any pages that descend from the specified page.

        If inclusive is set to True, it will also exclude the specified page.
        """
        return self.exclude(self.descendant_of_q(other, inclusive))

    def child_of_q(self, other):
        return self.descendant_of_q(other) & Q(depth=other.depth + 1)

    def child_of(self, other):
        """
        This filters the QuerySet to only contain pages that are direct children of the specified page.
        """
        return self.filter(self.child_of_q(other))

    def not_child_of(self, other):
        """
        This filters the QuerySet to not contain any pages that are direct children of the specified page.
        """
        return self.exclude(self.child_of_q(other))

    def ancestor_of_q(self, other, inclusive=False):
        paths = [
            other.path[0:pos]
            for pos in range(0, len(other.path) + 1, other.steplen)[1:]
        ]
        q = Q(path__in=paths)

        if not inclusive:
            q &= ~Q(pk=other.pk)

        return q

    def ancestor_of(self, other, inclusive=False):
        """
        This filters the QuerySet to only contain pages that are ancestors of the specified page.

        If inclusive is set to True, it will also include the specified page.
        """
        return self.filter(self.ancestor_of_q(other, inclusive))

    def not_ancestor_of(self, other, inclusive=False):
        """
        This filters the QuerySet to not contain any pages that are ancestors of the specified page.

        If inclusive is set to True, it will also exclude the specified page.
        """
        return self.exclude(self.ancestor_of_q(other, inclusive))

    def parent_of_q(self, other):
        return Q(path=self.model._get_parent_path_from_path(other.path))

    def parent_of(self, other):
        """
        This filters the QuerySet to only contain the parent of the specified page.
        """
        return self.filter(self.parent_of_q(other))

    def not_parent_of(self, other):
        """
        This filters the QuerySet to exclude the parent of the specified page.
        """
        return self.exclude(self.parent_of_q(other))

    def sibling_of_q(self, other, inclusive=True):
        q = Q(path__startswith=self.model._get_parent_path_from_path(other.path)) & Q(
            depth=other.depth
        )

        if not inclusive:
            q &= ~Q(pk=other.pk)

        return q

    def sibling_of(self, other, inclusive=True):
        """
        This filters the QuerySet to only contain pages that are siblings of the specified page.

        By default, inclusive is set to True so it will include the specified page in the results.

        If inclusive is set to False, the page will be excluded from the results.
        """
        return self.filter(self.sibling_of_q(other, inclusive))

    def not_sibling_of(self, other, inclusive=True):
        """
        This filters the QuerySet to not contain any pages that are siblings of the specified page.

        By default, inclusive is set to True so it will exclude the specified page from the results.

        If inclusive is set to False, the page will be included in the results.
        """
        return self.exclude(self.sibling_of_q(other, inclusive))


class SpecificQuerySetMixin:
    def __init__(self, *args, **kwargs):
        """Set custom instance attributes"""
        super().__init__(*args, **kwargs)
        # set by PageQuerySet.defer_streamfields()
        self._defer_streamfields = False

    def _clone(self):
        """Ensure clones inherit custom attribute values."""
        clone = super()._clone()
        clone._defer_streamfields = self._defer_streamfields
        return clone

    def specific(self, defer=False):
        """
        This efficiently gets all the specific items for the queryset, using
        the minimum number of queries.

        When the "defer" keyword argument is set to True, only generic
        field values will be loaded and all specific fields will be deferred.
        """
        clone = self._clone()
        if defer:
            clone._iterable_class = DeferredSpecificIterable
        else:
            clone._iterable_class = SpecificIterable
        return clone

    @property
    def is_specific(self):
        """
        Returns True if this queryset is already specific, False otherwise.
        """
        return issubclass(
            self._iterable_class,
            (SpecificIterable, DeferredSpecificIterable),
        )


class PageQuerySet(SearchableQuerySetMixin, SpecificQuerySetMixin, TreeQuerySet):
    def live_q(self):
        return Q(live=True)

    def live(self):
        """
        This filters the QuerySet to only contain published pages.
        """
        return self.filter(self.live_q())

    def not_live(self):
        """
        This filters the QuerySet to only contain unpublished pages.
        """
        return self.exclude(self.live_q())

    def in_menu_q(self):
        return Q(show_in_menus=True)

    def in_menu(self):
        """
        This filters the QuerySet to only contain pages that are in the menus.
        """
        return self.filter(self.in_menu_q())

    def not_in_menu(self):
        """
        This filters the QuerySet to only contain pages that are not in the menus.
        """
        return self.exclude(self.in_menu_q())

    def page_q(self, other):
        return Q(id=other.id)

    def page(self, other):
        """
        This filters the QuerySet so it only contains the specified page.
        """
        return self.filter(self.page_q(other))

    def not_page(self, other):
        """
        This filters the QuerySet so it doesn't contain the specified page.
        """
        return self.exclude(self.page_q(other))

    def type_q(self, *types):
        all_subclasses = {
            model for model in apps.get_models() if issubclass(model, types)
        }
        content_types = ContentType.objects.get_for_models(*all_subclasses)
        return Q(content_type__in=list(content_types.values()))

    def type(self, *types):
        """
        This filters the QuerySet to only contain pages that are an instance
        of the specified model(s) (including subclasses).
        """
        return self.filter(self.type_q(*types))

    def not_type(self, *types):
        """
        This filters the QuerySet to exclude any pages which are an instance of the specified model(s).
        """
        return self.exclude(self.type_q(*types))

    def exact_type_q(self, *types):
        content_types = ContentType.objects.get_for_models(*types)
        return Q(content_type__in=list(content_types.values()))

    def exact_type(self, *types):
        """
        This filters the QuerySet to only contain pages that are an instance of the specified model(s)
        (matching the model exactly, not subclasses).
        """
        return self.filter(self.exact_type_q(*types))

    def not_exact_type(self, *types):
        """
        This filters the QuerySet to exclude any pages which are an instance of the specified model(s)
        (matching the model exactly, not subclasses).
        """
        return self.exclude(self.exact_type_q(*types))

    def private_q(self):
        from wagtail.models import PageViewRestriction

        q = Q()
        for restriction in PageViewRestriction.objects.select_related("page").all():
            q |= self.descendant_of_q(restriction.page, inclusive=True)

        # do not match any page if no private section exists.
        return q if q else Q(pk__in=[])

    def public(self):
        """
        Filters the QuerySet to only contain pages that are not in a private
        section and their descendants.
        """
        return self.exclude(self.private_q())

    def not_public(self):
        """
        Filters the QuerySet to only contain pages that are in a private
        section and their descendants.
        """
        return self.filter(self.private_q())

    def private(self):
        """
        Filters the QuerySet to only contain pages that are in a private
        section and their descendants.
        """
        return self.filter(self.private_q())

    def first_common_ancestor(self, include_self=False, strict=False):
        """
        Find the first ancestor that all pages in this queryset have in common.
        For example, consider a page hierarchy like::

            - Home/
                - Foo Event Index/
                    - Foo Event Page 1/
                    - Foo Event Page 2/
                - Bar Event Index/
                    - Bar Event Page 1/
                    - Bar Event Page 2/

        The common ancestors for some queries would be:

        .. code-block:: python

            >>> Page.objects\\
            ...     .type(EventPage)\\
            ...     .first_common_ancestor()
            <Page: Home>
            >>> Page.objects\\
            ...     .type(EventPage)\\
            ...     .filter(title__contains='Foo')\\
            ...     .first_common_ancestor()
            <Page: Foo Event Index>

        This method tries to be efficient, but if you have millions of pages
        scattered across your page tree, it will be slow.

        If `include_self` is True, the ancestor can be one of the pages in the
        queryset:

        .. code-block:: python

            >>> Page.objects\\
            ...     .filter(title__contains='Foo')\\
            ...     .first_common_ancestor()
            <Page: Foo Event Index>
            >>> Page.objects\\
            ...     .filter(title__exact='Bar Event Index')\\
            ...     .first_common_ancestor()
            <Page: Bar Event Index>

        A few invalid cases exist: when the queryset is empty, when the root
        Page is in the queryset and ``include_self`` is False, and when there
        are multiple page trees with no common root (a case Wagtail does not
        support). If ``strict`` is False (the default), then the first root
        node is returned in these cases. If ``strict`` is True, then a
        ``ObjectDoesNotExist`` is raised.
        """
        # An empty queryset has no ancestors. This is a problem
        if not self.exists():
            if strict:
                raise self.model.DoesNotExist("Can not find ancestor of empty queryset")
            return self.model.get_first_root_node()

        if include_self:
            # Get all the paths of the matched pages.
            paths = self.order_by().values_list("path", flat=True)
        else:
            # Find all the distinct parent paths of all matched pages.
            # The empty `.order_by()` ensures that `Page.path` is not also
            # selected to order the results, which makes `.distinct()` works.
            paths = (
                self.order_by()
                .annotate(
                    parent_path=Substr(
                        "path",
                        1,
                        Length("path") - self.model.steplen,
                        output_field=CharField(max_length=255),
                    )
                )
                .values_list("parent_path", flat=True)
                .distinct()
            )

        # This method works on anything, not just file system paths.
        common_parent_path = posixpath.commonprefix(paths)

        # That may have returned a path like (0001, 0002, 000), which is
        # missing some chars off the end. Fix this by trimming the path to a
        # multiple of `Page.steplen`
        extra_chars = len(common_parent_path) % self.model.steplen
        if extra_chars != 0:
            common_parent_path = common_parent_path[:-extra_chars]

        if common_parent_path == "":
            # This should only happen when there are multiple trees,
            # a situation that Wagtail does not support;
            # or when the root node itself is part of the queryset.
            if strict:
                raise self.model.DoesNotExist("No common ancestor found!")

            # Assuming the situation is the latter, just return the root node.
            # The root node is not its own ancestor, so this is technically
            # incorrect. If you want very correct operation, use `strict=True`
            # and receive an error.
            return self.model.get_first_root_node()

        # Assuming the database is in a consistent state, this page should
        # *always* exist. If your database is not in a consistent state, you've
        # got bigger problems.
        return self.model.objects.get(path=common_parent_path)

    def unpublish(self):
        """
        This unpublishes all live pages in the QuerySet.
        """
        for page in self.live():
            page.unpublish()

    def defer_streamfields(self):
        """
        Apply to a queryset to prevent fetching/decoding of StreamField values on
        evaluation. Useful when working with potentially large numbers of results,
        where StreamField values are unlikely to be needed. For example, when
        generating a sitemap or a long list of page links.
        """
        clone = self._clone()
        clone._defer_streamfields = True  # used by specific_iterator()
        streamfield_names = self.model.get_streamfield_names()
        if not streamfield_names:
            return clone
        return clone.defer(*streamfield_names)

    def in_site(self, site):
        """
        This filters the QuerySet to only contain pages within the specified site.
        """
        return self.descendant_of(site.root_page, inclusive=True)

    def translation_of_q(self, page, inclusive):
        q = Q(translation_key=page.translation_key)

        if not inclusive:
            q &= ~Q(pk=page.pk)

        return q

    def translation_of(self, page, inclusive=False):
        """
        This filters the QuerySet to only contain pages that are translations of the specified page.

        If inclusive is True, the page itself is returned.
        """
        return self.filter(self.translation_of_q(page, inclusive))

    def not_translation_of(self, page, inclusive=False):
        """
        This filters the QuerySet to only contain pages that are not translations of the specified page.

        Note, this will include the page itself as the page is technically not a translation of itself.
        If inclusive is True, we consider the page to be a translation of itself so this excludes the page
        from the results.
        """
        return self.exclude(self.translation_of_q(page, inclusive))

    def prefetch_workflow_states(self):
        """
        Performance optimisation for listing pages.
        Prefetches the active workflow states on each page in this queryset.
        Used by `workflow_in_progress` and `current_workflow_progress` properties on
        `wagtailcore.models.Page`.
        """
        from .models import WorkflowState

        workflow_states = WorkflowState.objects.active().select_related(
            "current_task_state__task"
        )

        relation = "_workflow_states"
        if self.is_specific:
            relation = "_specific_workflow_states"

        return self.prefetch_related(
            Prefetch(
                relation,
                queryset=workflow_states,
                to_attr="_current_workflow_states",
            )
        )

    def annotate_approved_schedule(self):
        """
        Performance optimisation for listing pages.
        Annotates each page with the existence of an approved go live time.
        Used by `approved_schedule` property on `wagtailcore.models.Page`.
        """
        from .models import Revision

        return self.annotate(
            _approved_schedule=Exists(
                Revision.page_revisions.exclude(
                    approved_go_live_at__isnull=True
                ).filter(object_id=Cast(OuterRef("pk"), output_field=CharField()))
            )
        )

    def annotate_site_root_state(self):
        """
        Performance optimisation for listing pages.
        Annotates each object with whether it is a root page of any site.
        Used by `is_site_root` method on `wagtailcore.models.Page`.
        """
        return self.annotate(
            _is_site_root=Exists(
                Site.objects.filter(
                    root_page__translation_key=OuterRef("translation_key")
                )
            )
        )


class SpecificIterable(BaseIterable):
    def __iter__(self):
        """
        Identify and return all specific items in a queryset, and return them
        in the same order, with any annotations intact.
        """
        qs = self.queryset
        annotation_aliases = qs.query.annotations.keys()
        values_qs = qs.values("pk", "content_type", *annotation_aliases)

        # Gather items in batches to reduce peak memory usage
        for values in self._get_chunks(values_qs):

            annotations_by_pk = defaultdict(list)
            if annotation_aliases:
                # Extract annotation results keyed by pk so we can reapply to fetched items.
                for data in values:
                    annotations_by_pk[data["pk"]] = {
                        k: v for k, v in data.items() if k in annotation_aliases
                    }

            pks_and_types = [[v["pk"], v["content_type"]] for v in values]
            pks_by_type = defaultdict(list)
            for pk, content_type in pks_and_types:
                pks_by_type[content_type].append(pk)

            # Content types are cached by ID, so this will not run any queries.
            content_types = {
                pk: ContentType.objects.get_for_id(pk) for _, pk in pks_and_types
            }

            # Get the specific instances of all items, one model class at a time.
            items_by_type = {}
            missing_pks = []

            for content_type, pks in pks_by_type.items():
                # look up model class for this content type, falling back on the original
                # model (i.e. Page) if the more specific one is missing
                model = content_types[content_type].model_class() or qs.model
                items = model.objects.filter(pk__in=pks)

                if qs._defer_streamfields and hasattr(items, "defer_streamfields"):
                    items = items.defer_streamfields()

                items_for_type = {item.pk: item for item in items}
                items_by_type[content_type] = items_for_type
                missing_pks.extend(pk for pk in pks if pk not in items_for_type)

            # Fetch generic items to supplement missing items
            if missing_pks:
                generic_items = (
                    qs.model.objects.filter(pk__in=missing_pks)
                    .select_related("content_type")
                    .in_bulk()
                )
                warnings.warn(
                    "Specific versions of the following items could not be found. "
                    "This is most likely because a database migration has removed "
                    "the relevant table or record since the item was created:\n{}".format(
                        [
                            {"id": p.id, "title": p.title, "type": p.content_type}
                            for p in generic_items.values()
                        ]
                    ),
                    category=RuntimeWarning,
                )
            else:
                generic_items = {}

            # Yield all items in the order they occurred in the original query.
            for pk, content_type in pks_and_types:
                try:
                    item = items_by_type[content_type][pk]
                except KeyError:
                    item = generic_items[pk]
                if annotation_aliases:
                    # Reapply annotations before returning
                    for annotation, value in annotations_by_pk.get(item.pk, {}).items():
                        setattr(item, annotation, value)
                yield item

    def _get_chunks(self, queryset) -> Iterable[Tuple[Dict[str, Any]]]:
        if not self.chunked_fetch:
            # The entire result will be stored in memory, so there is no
            # benefit to splitting the result
            yield tuple(queryset)
        else:
            # Iterate through the queryset, returning the rows in manageable
            # chunks for self.__iter__() to fetch full instances for
            current_chunk = []
            for r in queryset.iterator(self.chunk_size):
                current_chunk.append(r)
                if len(current_chunk) == self.chunk_size:
                    yield tuple(current_chunk)
                    current_chunk.clear()
            # Return any left-overs
            if current_chunk:
                yield tuple(current_chunk)


class DeferredSpecificIterable(ModelIterable):
    def __iter__(self):
        for obj in super().__iter__():
            if obj.specific_class:
                yield obj.specific_deferred
            else:
                warnings.warn(
                    "A specific version of the following object could not be returned "
                    "because the specific model is not present on the active "
                    f"branch: <{obj.__class__.__name__} id='{obj.id}' title='{obj.title}' "
                    f"type='{obj.content_type}'>",
                    category=RuntimeWarning,
                )
                yield obj
