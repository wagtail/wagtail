from django.db.models.query import QuerySet
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType


class PageQuerySet(QuerySet):
    """
    Defines some extra query set methods that are useful for pages.
    """
    def live_q(self):
        return Q(live=True)

    def live(self):
        return self.filter(self.live_q())

    def not_live(self):
        return self.exclude(self.live_q())

    def descendant_of_q(self, other):
        return Q(path__startswith=other.path) & Q(depth__gt=other.depth)

    def descendant_of(self, other):
        return self.filter(self.descendant_of_q(other))

    def not_descendant_of(self, other):
        return self.exclude(self.descendant_of_q(other))

    def child_of_q(self, other):
        return self.descendant_of_q(other) & Q(depth=other.depth + 1)

    def child_of(self, other):
        return self.filter(self.child_of_q(other))

    def not_child_of(self, other):
        return self.exclude(self.child_of_q(other))

    def ascendant_of_q(self, other):
        paths = [
            other.path[0:pos]
            for pos in range(0, len(other.path), other.steplen)[1:]
        ]
        return Q(path__in=paths)

    def ascendant_of(self, other):
        return self.filter(self.ascendant_of_q(other))

    def not_ascendant_of(self, other):
        return self.exclude(self.ascendant_of_q(other))

    def parent_of_q(self, other):
        return Q(path=self.model._get_parent_path_from_path(other.path))

    def parent_of(self, other):
        return self.filter(self.parent_of_q(other))

    def not_parent_of(self, other):
        return self.exclude(self.parent_of_q(other))

    def sibling_of_q(self, other):
        return Q(path__startswith=self.model._get_parent_path_from_path(other.path)) & Q(depth=other.depth)

    def sibling_of(self, other):
        return self.filter(self.sibling_of_q(other))

    def not_sibling_of(self, other):
        return self.exclude(self.sibling_of_q(other))

    def type_q(self, model):
        content_type = ContentType.objects.get_for_model(model)
        return Q(content_type=content_type)

    def type(self, model):
        return self.filter(self.type_q(model))

    def not_type(self, model):
        return self.exclude(self.type_q(model))
