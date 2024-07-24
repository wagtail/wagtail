"""Adjacency List"""

from django.core import serializers
from django.db import models
from django.utils.translation import gettext_noop as _
from treebeard.exceptions import InvalidMoveToDescendant, NodeAlreadySaved
from treebeard.models import Node


def get_result_class(cls):
    """
    For the given model class, determine what class we should use for the
    nodes returned by its tree methods (such as get_children).

    Usually this will be trivially the same as the initial model class,
    but there are special cases when model inheritance is in use:

    * If the model extends another via multi-table inheritance, we need to
      use whichever ancestor originally implemented the tree behaviour (i.e.
      the one which defines the 'parent' field). We can't use the
      subclass, because it's not guaranteed that the other nodes reachable
      from the current one will be instances of the same subclass.

    * If the model is a proxy model, the returned nodes should also use
      the proxy class.
    """
    base_class = cls._meta.get_field('parent').model
    if cls._meta.proxy_for_model == base_class:
        return cls
    else:
        return base_class


class AL_NodeManager(models.Manager):
    """Custom manager for nodes in an Adjacency List tree."""
    def get_queryset(self):
        """Sets the custom queryset as the default."""
        if self.model.node_order_by:
            order_by = ['parent'] + list(self.model.node_order_by)
        else:
            order_by = ['parent', 'sib_order']
        return super().get_queryset().order_by(*order_by)


class AL_Node(Node):
    """Abstract model to create your own Adjacency List Trees."""

    objects = AL_NodeManager()
    node_order_by = None

    @classmethod
    def add_root(cls, **kwargs):
        """Adds a root node to the tree."""

        if len(kwargs) == 1 and 'instance' in kwargs:
            # adding the passed (unsaved) instance to the tree
            newobj = kwargs['instance']
            if not newobj._state.adding:
                raise NodeAlreadySaved("Attempted to add a tree node that is "\
                    "already in the database")
        else:
            newobj = cls(**kwargs)

        newobj._cached_depth = 1
        if not cls.node_order_by:
            try:
                max = get_result_class(cls).objects.filter(
                    parent__isnull=True).order_by(
                    'sib_order').reverse()[0].sib_order
            except IndexError:
                max = 0
            newobj.sib_order = max + 1
        newobj.save()
        return newobj

    @classmethod
    def get_root_nodes(cls):
        """:returns: A queryset containing the root nodes in the tree."""
        return get_result_class(cls).objects.filter(parent__isnull=True)

    def get_depth(self, update=False):
        """
        :returns: the depth (level) of the node
            Caches the result in the object itself to help in loops.

        :param update: Updates the cached value.
        """

        if self.parent_id is None:
            return 1

        try:
            if update:
                del self._cached_depth
            else:
                return self._cached_depth
        except AttributeError:
            pass

        depth = 0
        node = self
        while node:
            node = node.parent
            depth += 1
        self._cached_depth = depth
        return depth

    def get_children(self):
        """:returns: A queryset of all the node's children"""
        return get_result_class(self.__class__).objects.filter(parent=self)

    def get_parent(self, update=False):
        """:returns: the parent node of the current node object."""
        if self._meta.proxy_for_model:
            # the current node is a proxy model; the returned parent
            # should be the same proxy model, so we need to explicitly
            # fetch it as an instance of that model rather than simply
            # following the 'parent' relation
            if self.parent_id is None:
                return None
            else:
                return self.__class__.objects.get(pk=self.parent_id)
        else:
            return self.parent

    def get_ancestors(self):
        """
        :returns: A *list* containing the current node object's ancestors,
            starting by the root node and descending to the parent.
        """
        ancestors = []
        if self._meta.proxy_for_model:
            # the current node is a proxy model; our result set
            # should use the same proxy model, so we need to
            # explicitly fetch instances of that model
            # when following the 'parent' relation
            cls = self.__class__
            node = self
            while node.parent_id:
                node = cls.objects.get(pk=node.parent_id)
                ancestors.insert(0, node)
        else:
            node = self.parent
            while node:
                ancestors.insert(0, node)
                node = node.parent
        return ancestors

    def get_root(self):
        """:returns: the root node for the current node object."""
        ancestors = self.get_ancestors()
        if ancestors:
            return ancestors[0]
        return self

    def is_descendant_of(self, node):
        """
        :returns: ``True`` if the node if a descendant of another node given
            as an argument, else, returns ``False``
        """
        return self.pk in [obj.pk for obj in node.get_descendants()]

    @classmethod
    def dump_bulk(cls, parent=None, keep_ids=True):
        """Dumps a tree branch to a python data structure."""

        serializable_cls = cls._get_serializable_model()
        if (
                parent and serializable_cls != cls and
                parent.__class__ != serializable_cls
        ):
            parent = serializable_cls.objects.get(pk=parent.pk)

        # a list of nodes: not really a queryset, but it works
        objs = serializable_cls.get_tree(parent)

        ret, lnk = [], {}
        pk_field = cls._meta.pk.attname
        for node, pyobj in zip(objs, serializers.serialize('python', objs)):
            depth = node.get_depth()
            # django's serializer stores the attributes in 'fields'
            fields = pyobj['fields']
            del fields['parent']

            # non-sorted trees have this
            if 'sib_order' in fields:
                del fields['sib_order']

            if pk_field in fields:
                del fields[pk_field]

            newobj = {'data': fields}
            if keep_ids:
                newobj[pk_field] = pyobj['pk']

            if (not parent and depth == 1) or\
               (parent and depth == parent.get_depth()):
                ret.append(newobj)
            else:
                parentobj = lnk[node.parent_id]
                if 'children' not in parentobj:
                    parentobj['children'] = []
                parentobj['children'].append(newobj)
            lnk[node.pk] = newobj
        return ret

    def add_child(self, **kwargs):
        """Adds a child to the node."""
        cls = get_result_class(self.__class__)

        if len(kwargs) == 1 and 'instance' in kwargs:
            # adding the passed (unsaved) instance to the tree
            newobj = kwargs['instance']
            if not newobj._state.adding:
                raise NodeAlreadySaved("Attempted to add a tree node that is "\
                    "already in the database")
        else:
            newobj = cls(**kwargs)

        try:
            newobj._cached_depth = self._cached_depth + 1
        except AttributeError:
            pass
        if not cls.node_order_by:
            try:
                max = cls.objects.filter(parent=self).reverse(
                )[0].sib_order
            except IndexError:
                max = 0
            newobj.sib_order = max + 1
        newobj.parent = self
        newobj.save()
        return newobj

    @classmethod
    def _get_tree_recursively(cls, results, parent, depth):
        if parent:
            nodes = parent.get_children()
        else:
            nodes = cls.get_root_nodes()
        for node in nodes:
            node._cached_depth = depth
            results.append(node)
            cls._get_tree_recursively(results, node, depth + 1)

    @classmethod
    def get_tree(cls, parent=None):
        """
        :returns: A list of nodes ordered as DFS, including the parent. If
                  no parent is given, the entire tree is returned.
        """
        if parent:
            depth = parent.get_depth() + 1
            results = [parent]
        else:
            depth = 1
            results = []
        cls._get_tree_recursively(results, parent, depth)
        return results

    def get_descendants(self):
        """
        :returns: A *list* of all the node's descendants, doesn't
            include the node itself
        """
        return self.__class__.get_tree(parent=self)[1:]

    def get_descendant_count(self):
        """:returns: the number of descendants of a nodee"""
        return len(self.get_descendants())

    def get_siblings(self):
        """
        :returns: A queryset of all the node's siblings, including the node
            itself.
        """
        if self.parent:
            return get_result_class(self.__class__).objects.filter(
                parent=self.parent)
        return self.__class__.get_root_nodes()

    def add_sibling(self, pos=None, **kwargs):
        """Adds a new node as a sibling to the current node object."""
        pos = self._prepare_pos_var_for_add_sibling(pos)

        if len(kwargs) == 1 and 'instance' in kwargs:
            # adding the passed (unsaved) instance to the tree
            newobj = kwargs['instance']
            if not newobj._state.adding:
                raise NodeAlreadySaved("Attempted to add a tree node that is "\
                    "already in the database")
        else:
            # creating a new object
            newobj = get_result_class(self.__class__)(**kwargs)

        if not self.node_order_by:
            newobj.sib_order = self.__class__._get_new_sibling_order(pos,
                                                                     self)
        newobj.parent_id = self.parent_id
        newobj.save()
        return newobj

    @classmethod
    def _is_target_pos_the_last_sibling(cls, pos, target):
        return pos == 'last-sibling' or (
            pos == 'right' and target == target.get_last_sibling())

    @classmethod
    def _make_hole_in_db(cls, min, target_node):
        qset = get_result_class(cls).objects.filter(sib_order__gte=min)
        if target_node.is_root():
            qset = qset.filter(parent__isnull=True)
        else:
            qset = qset.filter(parent=target_node.parent)
        qset.update(sib_order=models.F('sib_order') + 1)

    @classmethod
    def _make_hole_and_get_sibling_order(cls, pos, target_node):
        siblings = target_node.get_siblings()
        siblings = {
            'left': siblings.filter(sib_order__gte=target_node.sib_order),
            'right': siblings.filter(sib_order__gt=target_node.sib_order),
            'first-sibling': siblings
        }[pos]
        sib_order = {
            'left': target_node.sib_order,
            'right': target_node.sib_order + 1,
            'first-sibling': 1
        }[pos]
        try:
            min = siblings.order_by('sib_order')[0].sib_order
        except IndexError:
            min = 0
        if min:
            cls._make_hole_in_db(min, target_node)
        return sib_order

    @classmethod
    def _get_new_sibling_order(cls, pos, target_node):
        if cls._is_target_pos_the_last_sibling(pos, target_node):
            sib_order = target_node.get_last_sibling().sib_order + 1
        else:
            sib_order = cls._make_hole_and_get_sibling_order(pos, target_node)
        return sib_order

    def move(self, target, pos=None):
        """
        Moves the current node and all it's descendants to a new position
        relative to another node.
        """

        pos = self._prepare_pos_var_for_move(pos)

        sib_order = None
        parent = None

        if pos in ('first-child', 'last-child', 'sorted-child'):
            # moving to a child
            if not target.is_leaf():
                target = target.get_last_child()
                pos = {'first-child': 'first-sibling',
                       'last-child': 'last-sibling',
                       'sorted-child': 'sorted-sibling'}[pos]
            else:
                parent = target
                if pos == 'sorted-child':
                    pos = 'sorted-sibling'
                else:
                    pos = 'first-sibling'
                    sib_order = 1

        if target.is_descendant_of(self):
            raise InvalidMoveToDescendant(
                _("Can't move node to a descendant."))

        if self == target and (
            (pos == 'left') or
            (pos in ('right', 'last-sibling') and
             target == target.get_last_sibling()) or
            (pos == 'first-sibling' and
             target == target.get_first_sibling())):
            # special cases, not actually moving the node so no need to UPDATE
            return

        if pos == 'sorted-sibling':
            if parent:
                self.parent = parent
            else:
                self.parent = target.parent
        else:
            if sib_order:
                self.sib_order = sib_order
            else:
                self.sib_order = self.__class__._get_new_sibling_order(pos,
                                                                       target)
            if parent:
                self.parent = parent
            else:
                self.parent = target.parent

        self.save()

    class Meta:
        """Abstract model."""
        abstract = True
