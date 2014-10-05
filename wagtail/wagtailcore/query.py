from django.db.models import Q, get_models
from django.contrib.contenttypes.models import ContentType
from treebeard.mp_tree import MP_NodeQuerySet

from wagtail.wagtailsearch.backends import get_search_backend


class PageQuerySet(MP_NodeQuerySet):
    def live_q(self):
        return Q(live=True)

    def live(self):
        """
        This filters the queryset to only contain published pages.
        """
        return self.filter(self.live_q())

    def not_live(self):
        """
        This filters the queryset to only contain unpublished pages.
        """
        return self.exclude(self.live_q())

    def in_menu_q(self):
        return Q(show_in_menus=True)

    def in_menu(self):
        """
        This filters the queryset to only contain pages that are in the menus.
        """
        return self.filter(self.in_menu_q())

    def not_in_menu(self):
        return self.exclude(self.in_menu_q())

    def page_q(self, other):
        return Q(id=other.id)

    def page(self, other):
        """
        This filters the queryset so it only contains the specified page.
        """
        return self.filter(self.page_q(other))

    def not_page(self, other):
        """
        This filters the queryset so it doesn't contain the specified page.
        """
        return self.exclude(self.page_q(other))

    def descendant_of_q(self, other, inclusive=False):
        q = Q(path__startswith=other.path) & Q(depth__gte=other.depth)

        if not inclusive:
            q &= ~self.page_q(other)

        return q

    def descendant_of(self, other, inclusive=False):
        """
        This filters the queryset to only contain pages that descend from the specified page.

        If inclusive is set to True, it will also contain the page itself (instead of just its descendants).
        """
        return self.filter(self.descendant_of_q(other, inclusive))

    def not_descendant_of(self, other, inclusive=False):
        """
        This filters the queryset to not contain any pages that descend from the specified page.

        If inclusive is set to True, it will also exclude the specified page.
        """
        return self.exclude(self.descendant_of_q(other, inclusive))

    def child_of_q(self, other):
        return self.descendant_of_q(other) & Q(depth=other.depth + 1)

    def child_of(self, other):
        """
        This filters the queryset to only contain pages that are direct children of the specified page.
        """
        return self.filter(self.child_of_q(other))

    def not_child_of(self, other):
        """
        This filters the queryset to not contain any pages that are direct children of the specified page.
        """
        return self.exclude(self.child_of_q(other))

    def ancestor_of_q(self, other, inclusive=False):
        paths = [
            other.path[0:pos]
            for pos in range(0, len(other.path) + 1, other.steplen)[1:]
        ]
        q = Q(path__in=paths)

        if not inclusive:
            q &= ~self.page_q(other)

        return q

    def ancestor_of(self, other, inclusive=False):
        """
        This filters the queryset to only contain pages that are ancestors of the specified page.

        If inclusive is set to True, it will also include the specified page.
        """
        return self.filter(self.ancestor_of_q(other, inclusive))

    def not_ancestor_of(self, other, inclusive=False):
        """
        This filters the queryset to not contain any pages that are ancestors of the specified page.

        If inclusive is set to True, it will also exclude the specified page.
        """
        return self.exclude(self.ancestor_of_q(other, inclusive))

    def parent_of_q(self, other):
        return Q(path=self.model._get_parent_path_from_path(other.path))

    def parent_of(self, other):
        return self.filter(self.parent_of_q(other))

    def not_parent_of(self, other):
        return self.exclude(self.parent_of_q(other))

    def sibling_of_q(self, other, inclusive=True):
        q = Q(path__startswith=self.model._get_parent_path_from_path(other.path)) & Q(depth=other.depth)

        if not inclusive:
            q &= ~self.page_q(other)

        return q

    def sibling_of(self, other, inclusive=True):
        """
        This filters the queryset to only contain pages that are siblings of the specified page.

        By default, inclusive is set to True so it will include the specified page in the results.

        If inclusive is set to False, the page will be excluded from the results.
        """
        return self.filter(self.sibling_of_q(other, inclusive))

    def not_sibling_of(self, other, inclusive=True):
        """
        This filters the queryset to not contain any pages that are siblings of the specified page.

        By default, inclusive is set to True so it will exclude the specified page from the results.

        If inclusive is set to False, the page will be included the results.
        """
        return self.exclude(self.sibling_of_q(other, inclusive))

    def type_q(self, klass):
        content_types = ContentType.objects.get_for_models(*[
            model for model in get_models()
            if issubclass(model, klass)
        ]).values()

        return Q(content_type__in=content_types)

    def type(self, model):
        """
        This filters the queryset to only contain pages that are an instance of the specified model (including subclasses).
        """
        return self.filter(self.type_q(model))

    def not_type(self, model):
        """
        This filters the queryset to not contain any pages which are an instance of the specified model.
        """
        return self.exclude(self.type_q(model))

    def public_q(self):
        from wagtail.wagtailcore.models import PageViewRestriction

        q = Q()
        for restriction in PageViewRestriction.objects.all():
            q &= ~self.descendant_of_q(restriction.page, inclusive=True)
        return q

    def public(self):
        """
        This filters the queryset to only contain pages that are not in a private section
        """
        return self.filter(self.public_q())

    def not_public(self):
        """
        This filters the queryset to only contain pages that are in a private section
        """
        return self.exclude(self.public_q())

    def search(self, query_string, fields=None, backend='default'):
        """
        This runs a search query on all the pages in the queryset
        """
        search_backend = get_search_backend(backend)
        return search_backend.search(query_string, self, fields=None)

    def unpublish(self):
        """
        This unpublishes all pages in the queryset
        """
        self.update(live=False, has_unpublished_changes=True)
