"""Materialized Path Trees"""

import operator
from functools import reduce

from django.core import serializers
from django.db import models, transaction, connection
from django.db.models import F, Q, Value
from django.db.models.functions import Concat, Substr
from django.utils.translation import gettext_noop as _

from treebeard.numconv import NumConv
from treebeard.models import Node
from treebeard.exceptions import InvalidMoveToDescendant, PathOverflow,\
    NodeAlreadySaved


# The following functions generate vendor-specific SQL functions
def sql_concat(*args, **kwargs):
    vendor = kwargs.pop('vendor', None)
    if vendor == 'mysql':
        return 'CONCAT({})'.format(', '.join(args))
    if vendor == 'microsoft':
        return ' + '.join(args)
    return '||'.join(args)


def sql_length(field, vendor=None):
    if vendor == 'microsoft':
        return 'LEN({})'.format(field)
    return 'LENGTH({})'.format(field)


def sql_substr(field, pos, length=None, **kwargs):
    vendor = kwargs.pop('vendor', None)
    function = 'SUBSTR({field}, {pos})'
    if length:
        function = 'SUBSTR({field}, {pos}, {length})'
    if vendor == 'microsoft':
        if not length:
            length = 'LEN({})'.format(field)
        function = 'SUBSTRING({field}, {pos}, {length})'
    return function.format(field=field, pos=pos, length=length)


def get_result_class(cls):
    """
    For the given model class, determine what class we should use for the
    nodes returned by its tree methods (such as get_children).

    Usually this will be trivially the same as the initial model class,
    but there are special cases when model inheritance is in use:

    * If the model extends another via multi-table inheritance, we need to
      use whichever ancestor originally implemented the tree behaviour (i.e.
      the one which defines the 'path' field). We can't use the
      subclass, because it's not guaranteed that the other nodes reachable
      from the current one will be instances of the same subclass.

    * If the model is a proxy model, the returned nodes should also use
      the proxy class.
    """
    base_class = cls._meta.get_field('path').model
    if cls._meta.proxy_for_model == base_class:
        return cls
    else:
        return base_class


class MP_NodeQuerySet(models.query.QuerySet):
    """
    Custom queryset for the tree node manager.

    Needed only for the custom delete method.
    """

    def delete(self, *args, **kwargs):
        """
        Custom delete method, will remove all descendant nodes to ensure a
        consistent tree (no orphans)

        :returns: tuple of the number of objects deleted and a dictionary 
                  with the number of deletions per object type
        """
        # we'll have to manually run through all the nodes that are going
        # to be deleted and remove nodes from the list if an ancestor is
        # already getting removed, since that would be redundant
        removed = {}
        for node in self.order_by('depth', 'path'):
            found = False
            for depth in range(1, int(len(node.path) / node.steplen)):
                path = node._get_basepath(node.path, depth)
                if path in removed:
                    # we are already removing a parent of this node
                    # skip
                    found = True
                    break
            if not found:
                removed[node.path] = node

        # ok, got the minimal list of nodes to remove...
        # we must also remove their children
        # and update every parent node's numchild attribute
        # LOTS OF FUN HERE!
        parents = {}
        toremove = []
        for path, node in removed.items():
            parentpath = node._get_basepath(node.path, node.depth - 1)
            if parentpath:
                if parentpath not in parents:
                    parents[parentpath] = node.get_parent(True)
                parent = parents[parentpath]
                if parent and parent.numchild > 0:
                    parent.numchild -= 1
                    parent.save()
            if node.is_leaf():
                toremove.append(Q(path=node.path))
            else:
                toremove.append(Q(path__startswith=node.path))

        # Django will handle this as a SELECT and then a DELETE of
        # ids, and will deal with removing related objects
        model = get_result_class(self.model)
        if toremove:
            qset = model.objects.filter(reduce(operator.or_, toremove))
        else:
            qset = model.objects.none()
        return super(MP_NodeQuerySet, qset).delete(*args, **kwargs)

    delete.alters_data = True
    delete.queryset_only = True

class MP_NodeManager(models.Manager):
    """Custom manager for nodes in a Materialized Path tree."""

    def get_queryset(self):
        """Sets the custom queryset as the default."""
        return MP_NodeQuerySet(self.model).order_by('path')


class MP_AddHandler(object):
    def __init__(self):
        self.stmts = []


class MP_ComplexAddMoveHandler(MP_AddHandler):

    def run_sql_stmts(self):
        cursor = self.node_cls._get_database_cursor('write')
        for sql, vals in self.stmts:
            cursor.execute(sql, vals)

    def get_sql_update_numchild(self, path, incdec='inc'):
        """:returns: The sql needed the numchild value of a node"""
        sql = "UPDATE %s SET numchild=numchild%s1"\
              " WHERE path=%%s" % (
                  connection.ops.quote_name(
                      get_result_class(self.node_cls)._meta.db_table),
                  {'inc': '+', 'dec': '-'}[incdec])
        vals = [path]
        return sql, vals

    def reorder_nodes_before_add_or_move(self, pos, newpos, newdepth, target,
                                         siblings, oldpath=None,
                                         movebranch=False):
        """
        Handles the reordering of nodes and branches when adding/moving
        nodes.

        :returns: A tuple containing the old path and the new path.
        """
        if (
                (pos == 'last-sibling') or
                (pos == 'right' and target == target.get_last_sibling())
        ):
            # easy, the last node
            last = target.get_last_sibling()
            newpath = last._inc_path()
            if movebranch:
                self.stmts.append(
                    self.get_sql_newpath_in_branches(oldpath, newpath))
        else:
            # do the UPDATE dance

            if newpos is None:
                siblings = target.get_siblings()
                siblings = {'left': siblings.filter(path__gte=target.path),
                            'right': siblings.filter(path__gt=target.path),
                            'first-sibling': siblings}[pos]
                basenum = target._get_lastpos_in_path()
                newpos = {'first-sibling': 1,
                          'left': basenum,
                          'right': basenum + 1}[pos]

            newpath = self.node_cls._get_path(target.path, newdepth, newpos)

            # If the move is amongst siblings and is to the left and there
            # are siblings to the right of its new position then to be on
            # the safe side we temporarily dump it on the end of the list
            tempnewpath = None
            if movebranch and len(oldpath) == len(newpath):
                parentoldpath = self.node_cls._get_basepath(
                    oldpath,
                    int(len(oldpath) / self.node_cls.steplen) - 1
                )
                parentnewpath = self.node_cls._get_basepath(
                    newpath, newdepth - 1)
                if (
                    parentoldpath == parentnewpath and
                    siblings and
                    newpath < oldpath
                ):
                    last = target.get_last_sibling()
                    basenum = last._get_lastpos_in_path()
                    tempnewpath = self.node_cls._get_path(
                        newpath, newdepth, basenum + 2)
                    self.stmts.append(
                        self.get_sql_newpath_in_branches(
                            oldpath, tempnewpath))

            # Optimisation to only move siblings which need moving
            # (i.e. if we've got holes, allow them to compress)
            movesiblings = []
            priorpath = newpath
            for node in siblings:
                # If the path of the node is already greater than the path
                # of the previous node it doesn't need shifting
                if node.path > priorpath:
                    break
                # It does need shifting, so add to the list
                movesiblings.append(node)
                # Calculate the path that it would be moved to, as that's
                # the next "priorpath"
                priorpath = node._inc_path()
            movesiblings.reverse()

            for node in movesiblings:
                # moving the siblings (and their branches) at the right of the
                # related position one step to the right
                sql, vals = self.get_sql_newpath_in_branches(
                    node.path, node._inc_path())
                self.stmts.append((sql, vals))

                if movebranch:
                    if oldpath.startswith(node.path):
                        # if moving to a parent, update oldpath since we just
                        # increased the path of the entire branch
                        oldpath = vals[0] + oldpath[len(vals[0]):]
                    if target.path.startswith(node.path):
                        # and if we moved the target, update the object
                        # django made for us, since the update won't do it
                        # maybe useful in loops
                        target.path = vals[0] + target.path[len(vals[0]):]
            if movebranch:
                # node to move
                if tempnewpath:
                    self.stmts.append(
                        self.get_sql_newpath_in_branches(
                            tempnewpath, newpath))
                else:
                    self.stmts.append(
                        self.get_sql_newpath_in_branches(
                            oldpath, newpath))
        return oldpath, newpath

    def get_sql_newpath_in_branches(self, oldpath, newpath):
        """
        :returns: The sql needed to move a branch to another position.

        .. note::

           The generated sql will only update the depth values if needed.

        """

        vendor = self.node_cls.get_database_vendor('write')
        sql1 = "UPDATE %s SET" % (
            connection.ops.quote_name(
                get_result_class(self.node_cls)._meta.db_table), )

        if vendor == 'mysql':
            # hooray for mysql ignoring standards in their default
            # configuration!
            # to make || work as it should, enable ansi mode
            # http://dev.mysql.com/doc/refman/5.0/en/ansi-mode.html
            sqlpath = "CONCAT(%s, SUBSTR(path, %s))"
        else:
            sqlpath = sql_concat("%s", sql_substr("path", "%s", vendor=vendor), vendor=vendor)

        sql2 = ["path=%s" % (sqlpath, )]
        vals = [newpath, len(oldpath) + 1]
        if len(oldpath) != len(newpath) and vendor != 'mysql':
            # when using mysql, this won't update the depth and it has to be
            # done in another query
            # doesn't even work with sql_mode='ANSI,TRADITIONAL'
            # TODO: FIND OUT WHY?!?? right now I'm just blaming mysql
            sql2.append(("depth=" + sql_length("%s", vendor=vendor) + "/%%s") % (sqlpath, ))
            vals.extend([newpath, len(oldpath) + 1, self.node_cls.steplen])
        sql3 = "WHERE path LIKE %s"
        vals.extend([oldpath + '%'])
        sql = '%s %s %s' % (sql1, ', '.join(sql2), sql3)
        return sql, vals


class MP_AddRootHandler(MP_AddHandler):
    def __init__(self, cls, **kwargs):
        super().__init__()
        self.cls = cls
        self.kwargs = kwargs

    def process(self):

        # do we have a root node already?
        last_root = self.cls.get_last_root_node()

        if last_root and last_root.node_order_by:
            # there are root nodes and node_order_by has been set
            # delegate sorted insertion to add_sibling
            return last_root.add_sibling('sorted-sibling', **self.kwargs)

        if last_root:
            # adding the new root node as the last one
            newpath = last_root._inc_path()
        else:
            # adding the first root node
            newpath = self.cls._get_path(None, 1, 1)

        if len(self.kwargs) == 1 and 'instance' in self.kwargs:
            # adding the passed (unsaved) instance to the tree
            newobj = self.kwargs['instance']
            if not newobj._state.adding:
                raise NodeAlreadySaved("Attempted to add a tree node that is "\
                    "already in the database")
        else:
            # creating the new object
            newobj = self.cls(**self.kwargs)

        newobj.depth = 1
        newobj.path = newpath
        # saving the instance before returning it
        newobj.save()
        return newobj


class MP_AddChildHandler(MP_AddHandler):
    def __init__(self, node, **kwargs):
        super().__init__()
        self.node = node
        self.node_cls = node.__class__
        self.kwargs = kwargs

    def process(self):
        if self.node_cls.node_order_by and not self.node.is_leaf():
            # there are child nodes and node_order_by has been set
            # delegate sorted insertion to add_sibling
            self.node.numchild += 1
            return self.node.get_last_child().add_sibling(
                'sorted-sibling', **self.kwargs)

        if len(self.kwargs) == 1 and 'instance' in self.kwargs:
            # adding the passed (unsaved) instance to the tree
            newobj = self.kwargs['instance']
            if not newobj._state.adding:
                raise NodeAlreadySaved("Attempted to add a tree node that is "\
                    "already in the database")
        else:
            # creating a new object
            newobj = self.node_cls(**self.kwargs)

        newobj.depth = self.node.depth + 1
        if self.node.is_leaf():
            # the node had no children, adding the first child
            newobj.path = self.node_cls._get_path(
                self.node.path, newobj.depth, 1)
            max_length = self.node_cls._meta.get_field('path').max_length
            if len(newobj.path) > max_length:
                raise PathOverflow(
                    _('The new node is too deep in the tree, try'
                      ' increasing the path.max_length property'
                      ' and UPDATE your database'))
        else:
            # adding the new child as the last one
            newobj.path = self.node.get_last_child()._inc_path()

        get_result_class(self.node_cls).objects.filter(
            path=self.node.path).update(numchild=F('numchild')+1)

        # we increase the numchild value of the object in memory
        self.node.numchild += 1

        # saving the instance before returning it
        newobj._cached_parent_obj = self.node
        newobj.save()

        return newobj


class MP_AddSiblingHandler(MP_ComplexAddMoveHandler):
    def __init__(self, node, pos, **kwargs):
        super().__init__()
        self.node = node
        self.node_cls = node.__class__
        self.pos = pos
        self.kwargs = kwargs

    def process(self):
        self.pos = self.node._prepare_pos_var_for_add_sibling(self.pos)

        if len(self.kwargs) == 1 and 'instance' in self.kwargs:
            # adding the passed (unsaved) instance to the tree
            newobj = self.kwargs['instance']
            if not newobj._state.adding:
                raise NodeAlreadySaved("Attempted to add a tree node that is "\
                    "already in the database")
        else:
            # creating a new object
            newobj = self.node_cls(**self.kwargs)

        newobj.depth = self.node.depth

        if self.pos == 'sorted-sibling':
            siblings = self.node.get_sorted_pos_queryset(
                self.node.get_siblings(), newobj)
            try:
                newpos = siblings.all()[0]._get_lastpos_in_path()
            except IndexError:
                newpos = None
            if newpos is None:
                self.pos = 'last-sibling'
        else:
            newpos, siblings = None, []

        _, newpath = self.reorder_nodes_before_add_or_move(
            self.pos, newpos, self.node.depth, self.node, siblings, None,
            False)

        parentpath = self.node._get_basepath(newpath, self.node.depth - 1)
        if parentpath:
            self.stmts.append(
                self.get_sql_update_numchild(parentpath, 'inc'))

        self.run_sql_stmts()

        # saving the instance before returning it
        newobj.path = newpath
        newobj.save()

        return newobj


class MP_MoveHandler(MP_ComplexAddMoveHandler):
    def __init__(self, node, target, pos=None):
        super().__init__()
        self.node = node
        self.node_cls = node.__class__
        self.target = target
        self.pos = pos

    def process(self):

        self.pos = self.node._prepare_pos_var_for_move(self.pos)

        oldpath = self.node.path

        # initialize variables and if moving to a child, updates "move to
        # child" to become a "move to sibling" if possible (if it can't
        # be done, it means that we are  adding the first child)
        newdepth, siblings, newpos = self.update_move_to_child_vars()

        if self.target.is_descendant_of(self.node):
            raise InvalidMoveToDescendant(
                _("Can't move node to a descendant."))

        if (
            oldpath == self.target.path and
            (
                (self.pos == 'left') or
                (
                    self.pos in ('right', 'last-sibling') and
                    self.target.path == self.target.get_last_sibling().path
                ) or
                (
                    self.pos == 'first-sibling' and
                    self.target.path == self.target.get_first_sibling().path
                )
            )
        ):
            # special cases, not actually moving the node so no need to UPDATE
            return

        if self.pos == 'sorted-sibling':
            siblings = self.node.get_sorted_pos_queryset(
                self.target.get_siblings(), self.node)
            try:
                newpos = siblings.all()[0]._get_lastpos_in_path()
            except IndexError:
                newpos = None
            if newpos is None:
                self.pos = 'last-sibling'

        # generate the sql that will do the actual moving of nodes
        oldpath, newpath = self.reorder_nodes_before_add_or_move(
            self.pos, newpos, newdepth, self.target, siblings, oldpath, True)
        # updates needed for mysql and children count in parents
        self.sanity_updates_after_move(oldpath, newpath)

        self.run_sql_stmts()

    def sanity_updates_after_move(self, oldpath, newpath):
        """
        Updates the list of sql statements needed after moving nodes.

        1. :attr:`depth` updates *ONLY* needed by mysql databases (*sigh*)
        2. update the number of children of parent nodes
        """
        if (
                self.node_cls.get_database_vendor('write') == 'mysql' and
                len(oldpath) != len(newpath)
        ):
            # no words can describe how dumb mysql is
            # we must update the depth of the branch in a different query
            self.stmts.append(
                self.get_mysql_update_depth_in_branch(newpath))

        oldparentpath = self.node_cls._get_parent_path_from_path(oldpath)
        newparentpath = self.node_cls._get_parent_path_from_path(newpath)
        if (
                (not oldparentpath and newparentpath) or
                (oldparentpath and not newparentpath) or
                (oldparentpath != newparentpath)
        ):
            # node changed parent, updating count
            if oldparentpath:
                self.stmts.append(
                    self.get_sql_update_numchild(oldparentpath, 'dec'))
            if newparentpath:
                self.stmts.append(
                    self.get_sql_update_numchild(newparentpath, 'inc'))

    def update_move_to_child_vars(self):
        """Update preliminar vars in :meth:`move` when moving to a child"""
        newdepth = self.target.depth
        newpos = None
        siblings = []
        if self.pos in ('first-child', 'last-child', 'sorted-child'):
            # moving to a child
            parent = self.target
            newdepth += 1
            if self.target.is_leaf():
                # moving as a target's first child
                newpos = 1
                self.pos = 'first-sibling'
                siblings = get_result_class(self.node_cls).objects.none()
            else:
                self.target = self.target.get_last_child()
                self.pos = {
                    'first-child': 'first-sibling',
                    'last-child': 'last-sibling',
                    'sorted-child': 'sorted-sibling'}[self.pos]

            # this is not for save(), since if needed, will be handled with a
            # custom UPDATE, this is only here to update django's object,
            # should be useful in loops
            parent.numchild += 1

        return newdepth, siblings, newpos

    def get_mysql_update_depth_in_branch(self, path):
        """
        :returns: The sql needed to update the depth of all the nodes in a
                  branch.
        """
        vendor = self.node_cls.get_database_vendor('write')
        sql = ("UPDATE %s SET depth=" + sql_length("path", vendor=vendor) + "/%%s WHERE path LIKE %%s") % (
            connection.ops.quote_name(
                get_result_class(self.node_cls)._meta.db_table), )
        vals = [self.node_cls.steplen, path + '%']
        return sql, vals


class MP_Node(Node):
    """Abstract model to create your own Materialized Path Trees."""

    steplen = 4
    alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    node_order_by = []
    path = models.CharField(max_length=255, unique=True)
    depth = models.PositiveIntegerField()
    numchild = models.PositiveIntegerField(default=0)
    gap = 1

    objects = MP_NodeManager()

    numconv_obj_ = None

    @classmethod
    def _int2str(cls, num):
        return cls.numconv_obj().int2str(num)

    @classmethod
    def _str2int(cls, num):
        return cls.numconv_obj().str2int(num)

    @classmethod
    def numconv_obj(cls):
        if cls.numconv_obj_ is None:
            cls.numconv_obj_ = NumConv(len(cls.alphabet), cls.alphabet)
        return cls.numconv_obj_

    @classmethod
    def add_root(cls, **kwargs):
        """
        Adds a root node to the tree.

        This method saves the node in database. The object is populated as if via:

        ```
        obj = cls(**kwargs)
        ```

        :raise PathOverflow: when no more root objects can be added
        """
        return MP_AddRootHandler(cls, **kwargs).process()

    @classmethod
    def dump_bulk(cls, parent=None, keep_ids=True):
        """Dumps a tree branch to a python data structure."""

        cls = get_result_class(cls)

        # Because of fix_tree, this method assumes that the depth
        # and numchild properties in the nodes can be incorrect,
        # so no helper methods are used
        qset = cls._get_serializable_model().objects.all()
        if parent:
            qset = qset.filter(path__startswith=parent.path)
        ret, lnk = [], {}
        pk_field = cls._meta.pk.attname
        for pyobj in serializers.serialize('python', qset):
            # django's serializer stores the attributes in 'fields'
            fields = pyobj['fields']
            path = fields['path']
            depth = int(len(path) / cls.steplen)
            # this will be useless in load_bulk
            del fields['depth']
            del fields['path']
            del fields['numchild']
            if pk_field in fields:
                # this happens immediately after a load_bulk
                del fields[pk_field]

            newobj = {'data': fields}
            if keep_ids:
                newobj[pk_field] = pyobj['pk']

            if (not parent and depth == 1) or\
               (parent and len(path) == len(parent.path)):
                ret.append(newobj)
            else:
                parentpath = cls._get_basepath(path, depth - 1)
                parentobj = lnk[parentpath]
                if 'children' not in parentobj:
                    parentobj['children'] = []
                parentobj['children'].append(newobj)
            lnk[path] = newobj
        return ret

    @classmethod
    def find_problems(cls):
        """
        Checks for problems in the tree structure, problems can occur when:

           1. your code breaks and you get incomplete transactions (always
              use transactions!)
           2. changing the ``steplen`` value in a model (you must
              :meth:`dump_bulk` first, change ``steplen`` and then
              :meth:`load_bulk`

        :returns: A tuple of five lists:

                  1. a list of ids of nodes with characters not found in the
                     ``alphabet``
                  2. a list of ids of nodes when a wrong ``path`` length
                     according to ``steplen``
                  3. a list of ids of orphaned nodes
                  4. a list of ids of nodes with the wrong depth value for
                     their path
                  5. a list of ids nodes that report a wrong number of children
        """
        cls = get_result_class(cls)
        vendor = cls.get_database_vendor('write')

        evil_chars, bad_steplen, orphans = [], [], []
        wrong_depth, wrong_numchild = [], []
        for node in cls.objects.all():
            found_error = False
            for char in node.path:
                if char not in cls.alphabet:
                    evil_chars.append(node.pk)
                    found_error = True
                    break
            if found_error:
                continue
            if len(node.path) % cls.steplen:
                bad_steplen.append(node.pk)
                continue
            try:
                node.get_parent(True)
            except cls.DoesNotExist:
                orphans.append(node.pk)
                continue

            if node.depth != int(len(node.path) / cls.steplen):
                wrong_depth.append(node.pk)
                continue

            real_numchild = cls.objects.filter(
                path__range=cls._get_children_path_interval(node.path)
            ).extra(
                where=[(sql_length("path", vendor=vendor) + '/%d=%d') % (cls.steplen, node.depth + 1)]
            ).count()
            if real_numchild != node.numchild:
                wrong_numchild.append(node.pk)
                continue

        return evil_chars, bad_steplen, orphans, wrong_depth, wrong_numchild

    @classmethod
    def fix_tree(cls, destructive=False, fix_paths=False):
        """
        Solves some problems that can appear when transactions are not used and
        a piece of code breaks, leaving the tree in an inconsistent state.

        The problems this method solves are:

           1. Nodes with an incorrect ``depth`` or ``numchild`` values due to
              incorrect code and lack of database transactions.
           2. "Holes" in the tree. This is normal if you move/delete nodes a
              lot. Holes in a tree don't affect performance,
           3. Incorrect ordering of nodes when ``node_order_by`` is enabled.
              Ordering is enforced on *node insertion*, so if an attribute in
              ``node_order_by`` is modified after the node is inserted, the
              tree ordering will be inconsistent.

        :param fix_paths:

            A boolean value. If True, a slower, more complex fix_tree method
            will be attempted. If False (the default), it will use a safe (and
            fast!) fix approach, but it will only solve the ``depth`` and
            ``numchild`` nodes, it won't fix the tree holes or broken path
            ordering.

        :param destructive:

            Deprecated; alias for ``fix_paths``.
        """
        cls = get_result_class(cls)
        vendor = cls.get_database_vendor('write')

        cursor = cls._get_database_cursor('write')

        # fix the depth field
        # we need the WHERE to speed up postgres
        sql = (
            "UPDATE %s "
            "SET depth=" + sql_length("path", vendor=vendor) + "/%%s "
            "WHERE depth!=" + sql_length("path", vendor=vendor) + "/%%s"
        ) % (connection.ops.quote_name(cls._meta.db_table), )
        vals = [cls.steplen, cls.steplen]
        cursor.execute(sql, vals)

        # fix the numchild field
        vals = ['_' * cls.steplen]
        # the cake and sql portability are a lie
        if cls.get_database_vendor('read') == 'mysql':
            sql = (
                "SELECT tbn1.path, tbn1.numchild, ("
                "SELECT COUNT(1) "
                "FROM %(table)s AS tbn2 "
                "WHERE tbn2.path LIKE " +
                sql_concat("tbn1.path", "%%s", vendor=vendor) + ") AS real_numchild "
                "FROM %(table)s AS tbn1 "
                "HAVING tbn1.numchild != real_numchild"
            ) % {'table': connection.ops.quote_name(cls._meta.db_table)}
        else:
            subquery = "(SELECT COUNT(1) FROM %(table)s AS tbn2"\
                        " WHERE tbn2.path LIKE " + sql_concat("tbn1.path", "%%s", vendor=vendor) + ")"
            sql = ("SELECT tbn1.path, tbn1.numchild, " + subquery +
                    " FROM %(table)s AS tbn1 WHERE tbn1.numchild != " +
                    subquery)
            sql = sql % {
                'table': connection.ops.quote_name(cls._meta.db_table)}
            # we include the subquery twice
            vals *= 2
        cursor.execute(sql, vals)
        sql = "UPDATE %(table)s "\
                "SET numchild=%%s "\
                "WHERE path=%%s" % {
                    'table': connection.ops.quote_name(cls._meta.db_table)}
        for node_data in cursor.fetchall():
            vals = [node_data[2], node_data[0]]
            cursor.execute(sql, vals)

        if fix_paths or destructive:
            with transaction.atomic():
                # To fix holes and mis-orderings in paths, we consider each non-leaf node in turn
                # and ensure that its children's path values are consecutive (and in the order
                # given by node_order_by, if applicable). children_to_fix is a queue of child sets
                # that we know about but have not yet fixed, expressed as a tuple of
                # (parent_path, depth). Since we're updating paths as we go, we must take care to
                # only add items to this list after the corresponding parent node has been fixed
                # (and is thus not going to change).

                # Initially children_to_fix is the set of root nodes, i.e. ones with a path
                # starting with '' and depth 1.
                children_to_fix = [('', 1)]

                while children_to_fix:
                    parent_path, depth = children_to_fix.pop(0)

                    children = cls.objects.filter(
                        path__startswith=parent_path, depth=depth
                    ).values('pk', 'path', 'depth', 'numchild')

                    desired_sequence = children.order_by(*(cls.node_order_by or ['path']))

                    # mapping of current path position (converted to numeric) to item
                    actual_sequence = {}

                    # highest numeric path position currently in use
                    max_position = None

                    # loop over items to populate actual_sequence and max_position
                    for item in desired_sequence:
                        actual_position = cls._str2int(item['path'][-cls.steplen:])
                        actual_sequence[actual_position] = item
                        if max_position is None or actual_position > max_position:
                            max_position = actual_position

                    # loop over items to perform path adjustments
                    for (i, item) in enumerate(desired_sequence):
                        desired_position = i + 1  # positions are 1-indexed
                        actual_position = cls._str2int(item['path'][-cls.steplen:])
                        if actual_position == desired_position:
                            pass
                        else:
                            # if a node is already in the desired position, move that node
                            # to max_position + 1 to get it out of the way
                            occupant = actual_sequence.get(desired_position)
                            if occupant:
                                old_path = occupant['path']
                                max_position += 1
                                new_path = cls._get_path(parent_path, depth, max_position)
                                if len(new_path) > len(old_path):
                                    previous_max_path = cls._get_path(parent_path, depth, max_position - 1)
                                    raise PathOverflow(_("Path Overflow from: '%s'" % (previous_max_path, )))

                                cls._rewrite_node_path(old_path, new_path)
                                # update actual_sequence to reflect the new position
                                actual_sequence[max_position] = occupant
                                del(actual_sequence[desired_position])
                                occupant['path'] = new_path

                            # move item into the (now vacated) desired position
                            old_path = item['path']
                            new_path = cls._get_path(parent_path, depth, desired_position)
                            cls._rewrite_node_path(old_path, new_path)
                            # update actual_sequence to reflect the new position
                            actual_sequence[desired_position] = item
                            del(actual_sequence[actual_position])
                            item['path'] = new_path

                        if item['numchild']:
                            # this item has children to process, and we have now moved the parent
                            # node into its final position, so it's safe to add to children_to_fix
                            children_to_fix.append((item['path'], depth + 1))

    @classmethod
    def _rewrite_node_path(cls, old_path, new_path):
        cls.objects.filter(path__startswith=old_path).update(
            path=Concat(
                Value(new_path),
                Substr('path', len(old_path) + 1)
            )
        )

    @classmethod
    def get_tree(cls, parent=None):
        """
        :returns:

            A *queryset* of nodes ordered as DFS, including the parent.
            If no parent is given, the entire tree is returned.
        """
        cls = get_result_class(cls)

        if parent is None:
            # return the entire tree
            return cls.objects.all()
        if parent.is_leaf():
            return cls.objects.filter(pk=parent.pk)
        return cls.objects.filter(
            path__startswith=parent.path,
            depth__gte=parent.depth
        ).order_by(
            'path'
        )

    @classmethod
    def get_root_nodes(cls):
        """:returns: A queryset containing the root nodes in the tree."""
        return get_result_class(cls).objects.filter(depth=1).order_by('path')

    @classmethod
    def get_descendants_group_count(cls, parent=None):
        """
        Helper for a very common case: get a group of siblings and the number
        of *descendants* in every sibling.
        """

        # ~
        # disclaimer: this is the FOURTH implementation I wrote for this
        # function. I really tried to make it return a queryset, but doing so
        # with a *single* query isn't trivial with Django's ORM.

        # ok, I DID manage to make Django's ORM return a queryset here,
        # defining two querysets, passing one subquery in the tables parameters
        # of .extra() of the second queryset, using the undocumented order_by
        # feature, and using a HORRIBLE hack to avoid django quoting the
        # subquery as a table, BUT (and there is always a but) the hack didn't
        # survive turning the QuerySet into a ValuesQuerySet, so I just used
        # good old SQL.
        # NOTE: in case there is interest, the hack to avoid django quoting the
        # subquery as a table, was adding the subquery to the alias cache of
        # the queryset's query object:
        #
        #     qset.query.quote_cache[subquery] = subquery
        #
        # If there is a better way to do this in an UNMODIFIED django 1.0, let
        # me know.
        # ~

        cls = get_result_class(cls)
        vendor = cls.get_database_vendor('write')

        if parent:
            depth = parent.depth + 1
            params = cls._get_children_path_interval(parent.path)
            extrand = 'AND path BETWEEN %s AND %s'
        else:
            depth = 1
            params = []
            extrand = ''

        subpath = sql_substr("path", "1", "%(subpathlen)s", vendor=vendor)

        sql = (
            'SELECT * FROM %(table)s AS t1 INNER JOIN '
            ' (SELECT '
            '   ' + subpath + ' AS subpath, '
            '   COUNT(1)-1 AS count '
            '   FROM %(table)s '
            '   WHERE depth >= %(depth)s %(extrand)s'
            '   GROUP BY ' + subpath + ') AS t2 '
            ' ON t1.path=t2.subpath '
            ' ORDER BY t1.path'
        ) % {
            'table': connection.ops.quote_name(cls._meta.db_table),
            'subpathlen': depth * cls.steplen,
            'depth': depth,
                'extrand': extrand}
        cursor = cls._get_database_cursor('write')
        cursor.execute(sql, params)

        ret = []
        field_names = [field[0] for field in cursor.description]
        for node_data in cursor.fetchall():
            node = cls(**dict(zip(field_names, node_data[:-2])))
            node.descendants_count = node_data[-1]
            ret.append(node)
        return ret

    def get_depth(self):
        """:returns: the depth (level) of the node"""
        return self.depth

    def get_siblings(self):
        """
        :returns: A queryset of all the node's siblings, including the node
            itself.
        """
        qset = get_result_class(self.__class__).objects.filter(
            depth=self.depth
        ).order_by(
            'path'
        )
        if self.depth > 1:
            # making sure the non-root nodes share a parent
            parentpath = self._get_basepath(self.path, self.depth - 1)
            qset = qset.filter(
                path__range=self._get_children_path_interval(parentpath))
        return qset

    def get_children(self):
        """:returns: A queryset of all the node's children"""
        if self.is_leaf():
            return get_result_class(self.__class__).objects.none()
        return get_result_class(self.__class__).objects.filter(
            depth=self.depth + 1,
            path__range=self._get_children_path_interval(self.path)
        ).order_by(
            'path'
        )

    def get_next_sibling(self):
        """
        :returns: The next node's sibling, or None if it was the rightmost
            sibling.
        """
        try:
            return self.get_siblings().filter(path__gt=self.path)[0]
        except IndexError:
            return None

    def get_descendants(self):
        """
        :returns: A queryset of all the node's descendants as DFS, doesn't
            include the node itself
        """
        if self.is_leaf():
            return get_result_class(self.__class__).objects.none()
        return self.__class__.get_tree(self).exclude(pk=self.pk)

    def get_prev_sibling(self):
        """
        :returns: The previous node's sibling, or None if it was the leftmost
            sibling.
        """
        try:
            return self.get_siblings().filter(path__lt=self.path).reverse()[0]
        except IndexError:
            return None

    def get_children_count(self):
        """
        :returns: The number the node's children, calculated in the most
        efficient possible way.
        """
        return self.numchild

    def is_sibling_of(self, node):
        """
        :returns: ``True`` if the node is a sibling of another node given as an
            argument, else, returns ``False``
        """
        aux = self.depth == node.depth
        # Check non-root nodes share a parent only if they have the same depth
        if aux and self.depth > 1:
            # making sure the non-root nodes share a parent
            parentpath = self._get_basepath(self.path, self.depth - 1)
            return aux and node.path.startswith(parentpath)
        return aux

    def is_child_of(self, node):
        """
        :returns: ``True`` is the node if a child of another node given as an
            argument, else, returns ``False``
        """
        return (self.path.startswith(node.path) and
                self.depth == node.depth + 1)

    def is_descendant_of(self, node):
        """
        :returns: ``True`` if the node is a descendant of another node given
            as an argument, else, returns ``False``
        """
        return self.path.startswith(node.path) and self.depth > node.depth

    def add_child(self, **kwargs):
        """
        Adds a child to the node.

        This method saves the node in database. The object is populated as if via:

        ```
        obj = self.__class__(**kwargs)
        ```

        :raise PathOverflow: when no more child nodes can be added
        """
        return MP_AddChildHandler(self, **kwargs).process()

    def add_sibling(self, pos=None, **kwargs):
        """
        Adds a new node as a sibling to the current node object.

        This method saves the node in database. The object is populated as if via:

        ```
        obj = self.__class__(**kwargs)
        ```

        :raise PathOverflow: when the library can't make room for the
           node's new position
        """
        return MP_AddSiblingHandler(self, pos, **kwargs).process()

    def get_root(self):
        """:returns: the root node for the current node object."""
        return get_result_class(self.__class__).objects.get(
            path=self.path[0:self.steplen])

    def is_root(self):
        """:returns: True if the node is a root node (else, returns False)"""
        return self.depth == 1

    def is_leaf(self):
        """:returns: True if the node is a leaf node (else, returns False)"""
        return self.numchild == 0

    def get_ancestors(self):
        """
        :returns: A queryset containing the current node object's ancestors,
            starting by the root node and descending to the parent.
        """
        if self.is_root():
            return get_result_class(self.__class__).objects.none()

        paths = [
            self.path[0:pos]
            for pos in range(0, len(self.path), self.steplen)[1:]
        ]
        return get_result_class(self.__class__).objects.filter(
            path__in=paths).order_by('depth')

    def get_parent(self, update=False):
        """
        :returns: the parent node of the current node object.
            Caches the result in the object itself to help in loops.
        """
        depth = int(len(self.path) / self.steplen)
        if depth <= 1:
            return
        try:
            if update:
                del self._cached_parent_obj
            else:
                return self._cached_parent_obj
        except AttributeError:
            pass
        parentpath = self._get_basepath(self.path, depth - 1)
        self._cached_parent_obj = get_result_class(
            self.__class__).objects.get(path=parentpath)
        return self._cached_parent_obj

    def move(self, target, pos=None):
        """
        Moves the current node and all it's descendants to a new position
        relative to another node.

        :raise PathOverflow: when the library can't make room for the
           node's new position
        """
        return MP_MoveHandler(self, target, pos).process()

    @classmethod
    def _get_basepath(cls, path, depth):
        """:returns: The base path of another path up to a given depth"""
        if path:
            return path[0:depth * cls.steplen]
        return ''

    @classmethod
    def _get_path(cls, path, depth, newstep):
        """
        Builds a path given some values

        :param path: the base path
        :param depth: the depth of the  node
        :param newstep: the value (integer) of the new step
        """
        parentpath = cls._get_basepath(path, depth - 1)
        key = cls._int2str(newstep)
        return '{0}{1}{2}'.format(
            parentpath,
            cls.alphabet[0] * (cls.steplen - len(key)),
            key
        )

    def _inc_path(self):
        """:returns: The path of the next sibling of a given node path."""
        newpos = self._str2int(self.path[-self.steplen:]) + 1
        key = self._int2str(newpos)
        if len(key) > self.steplen:
            raise PathOverflow(_("Path Overflow from: '%s'" % (self.path, )))
        return '{0}{1}{2}'.format(
            self.path[:-self.steplen],
            self.alphabet[0] * (self.steplen - len(key)),
            key
        )

    def _get_lastpos_in_path(self):
        """:returns: The integer value of the last step in a path."""
        return self._str2int(self.path[-self.steplen:])

    @classmethod
    def _get_parent_path_from_path(cls, path):
        """:returns: The parent path for a given path"""
        if path:
            return path[0:len(path) - cls.steplen]
        return ''

    @classmethod
    def _get_children_path_interval(cls, path):
        """:returns: An interval of all possible children paths for a node."""
        return (path + cls.alphabet[0] * cls.steplen,
                path + cls.alphabet[-1] * cls.steplen)

    class Meta:
        """Abstract model."""
        abstract = True
