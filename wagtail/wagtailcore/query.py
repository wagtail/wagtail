from django.db.models import Q
from django.contrib.contenttypes.models import ContentType


# hack to import our patched copy of treebeard at wagtail/vendor/django-treebeard -
# based on http://stackoverflow.com/questions/17211078/how-to-temporarily-modify-sys-path-in-python
import sys
import os
treebeard_path = os.path.join(os.path.dirname(__file__), '..', 'vendor', 'django-treebeard')
sys.path.insert(0, treebeard_path)
from treebeard.mp_tree import MP_NodeQuerySet
sys.path.pop(0)


class PageQuerySet(MP_NodeQuerySet):
    """
    Defines some extra query set methods that are useful for pages.
    """
    def live_q(self):
        return Q(live=True)

    def live(self):
        return self.filter(self.live_q())

    def not_live(self):
        return self.exclude(self.live_q())

    def page_q(self, other):
        return Q(id=other.id)

    def page(self, other):
        return self.filter(self.page_q(other))

    def not_page(self, other):
        return self.exclude(self.page_q(other))

    def descendant_of_q(self, other, inclusive=False):
        q = Q(path__startswith=other.path) & Q(depth__gte=other.depth)

        if not inclusive:
            q &= ~self.page_q(other)

        return q

    def descendant_of(self, other, inclusive=False):
        return self.filter(self.descendant_of_q(other, inclusive))

    def not_descendant_of(self, other, inclusive=False):
        return self.exclude(self.descendant_of_q(other, inclusive))

    def child_of_q(self, other):
        return self.descendant_of_q(other) & Q(depth=other.depth + 1)

    def child_of(self, other):
        return self.filter(self.child_of_q(other))

    def not_child_of(self, other):
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
        return self.filter(self.ancestor_of_q(other, inclusive))

    def not_ancestor_of(self, other, inclusive=False):
        return self.exclude(self.ancestor_of_q(other, inclusive))

    def parent_of_q(self, other):
        return Q(path=self.model._get_parent_path_from_path(other.path))

    def parent_of(self, other):
        return self.filter(self.parent_of_q(other))

    def not_parent_of(self, other):
        return self.exclude(self.parent_of_q(other))

    def sibling_of_q(self, other, inclusive=False):
        q = Q(path__startswith=self.model._get_parent_path_from_path(other.path)) & Q(depth=other.depth)

        if not inclusive:
            q &= ~self.page_q(other)

        return q

    def sibling_of(self, other, inclusive=False):
        return self.filter(self.sibling_of_q(other, inclusive))

    def not_sibling_of(self, other, inclusive=False):
        return self.exclude(self.sibling_of_q(other, inclusive))

    def type_q(self, model):
        content_type = ContentType.objects.get_for_model(model)
        return Q(content_type=content_type)

    def type(self, model):
        return self.filter(self.type_q(model))

    def not_type(self, model):
        return self.exclude(self.type_q(model))
