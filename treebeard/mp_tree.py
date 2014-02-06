"""Materialized Path Trees"""

import sys
import operator

if sys.version_info >= (3, 0):
    from functools import reduce

from django.core import serializers
from django.db import models, transaction, connection
from django.db.models import F, Q
from django.utils.translation import ugettext_noop as _

from treebeard.numconv import NumConv
from treebeard.models import Node
from treebeard.exceptions import InvalidMoveToDescendant, PathOverflow


def get_base_model_class(cls):
    """
    Return the class in this model's inheritance chain which implements tree behaviour
    (i.e. the one which defines the 'path' field). Necessary because a method like
    get_children invoked on a multiple-table-inheritance subclass needs to perform
    the query on the base class, in order to return child nodes that are not
    the same subclass as that parent.
    """
    return cls._meta.get_field('path').model


class MP_NodeQuerySet(models.query.QuerySet):
    """
    Custom queryset for the tree node manager.

    Needed only for the custom delete method.
    """

    def delete(self):
        """
        Custom delete method, will remove all descendant nodes to ensure a
        consistent tree (no orphans)

        :returns: ``None``
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
        if toremove:
            qset = self.model.objects.filter(reduce(operator.or_, toremove))
            super(MP_NodeQuerySet, qset).delete()
        transaction.commit_unless_managed()


class MP_NodeManager(models.Manager):
    """Custom manager for nodes in a Materialized Path tree."""

    def get_query_set(self):
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
                  connection.ops.quote_name(get_base_model_class(self.node_cls)._meta.db_table),
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
            connection.ops.quote_name(get_base_model_class(self.node_cls)._meta.db_table), )

        # <3 "standard" sql
        if vendor == 'sqlite':
            # I know that the third argument in SUBSTR (LENGTH(path)) is
            # awful, but sqlite fails without it:
            # OperationalError: wrong number of arguments to function substr()
            # even when the documentation says that 2 arguments are valid:
            # http://www.sqlite.org/lang_corefunc.html
            sqlpath = "%s||SUBSTR(path, %s, LENGTH(path))"
        elif vendor == 'mysql':
            # hooray for mysql ignoring standards in their default
            # configuration!
            # to make || work as it should, enable ansi mode
            # http://dev.mysql.com/doc/refman/5.0/en/ansi-mode.html
            sqlpath = "CONCAT(%s, SUBSTR(path, %s))"
        else:
            sqlpath = "%s||SUBSTR(path, %s)"

        sql2 = ["path=%s" % (sqlpath, )]
        vals = [newpath, len(oldpath) + 1]
        if len(oldpath) != len(newpath) and vendor != 'mysql':
            # when using mysql, this won't update the depth and it has to be
            # done in another query
            # doesn't even work with sql_mode='ANSI,TRADITIONAL'
            # TODO: FIND OUT WHY?!?? right now I'm just blaming mysql
            sql2.append("depth=LENGTH(%s)/%%s" % (sqlpath, ))
            vals.extend([newpath, len(oldpath) + 1, self.node_cls.steplen])
        sql3 = "WHERE path LIKE %s"
        vals.extend([oldpath + '%'])
        sql = '%s %s %s' % (sql1, ', '.join(sql2), sql3)
        return sql, vals


class MP_AddRootHandler(MP_AddHandler):
    def __init__(self, cls, instance, **kwargs):
        super(MP_AddRootHandler, self).__init__()
        self.cls = cls
        self.instance = instance
        self.kwargs = kwargs

    def process(self):

        # do we have a root node already?
        last_root = self.cls.get_last_root_node()

        if last_root and last_root.node_order_by:
            # there are root nodes and node_order_by has been set
            # delegate sorted insertion to add_sibling
            return last_root.add_sibling('sorted-sibling', self.instance, **self.kwargs)

        if last_root:
            # adding the new root node as the last one
            newpath = last_root._inc_path()
        else:
            # adding the first root node
            newpath = self.cls._get_path(None, 1, 1)

        if self.instance:
            if self.instance.pk:
                raise ValueError("Attempted to add a tree node that is already in the database")
            newobj = self.instance
        else:
            # creating the new object
            newobj = self.cls(**self.kwargs)

        newobj.depth = 1
        newobj.path = newpath
        # saving the instance before returning it
        newobj.save()
        transaction.commit_unless_managed()
        return newobj


class MP_AddChildHandler(MP_AddHandler):
    def __init__(self, node, instance, **kwargs):
        super(MP_AddChildHandler, self).__init__()
        self.node = node
        self.node_cls = node.__class__
        self.instance = instance
        self.kwargs = kwargs

    def process(self):
        if self.node_cls.node_order_by and not self.node.is_leaf():
            # there are child nodes and node_order_by has been set
            # delegate sorted insertion to add_sibling
            self.node.numchild += 1
            return self.node.get_last_child().add_sibling(
                'sorted-sibling', self.instance, **self.kwargs)

        if self.instance:
            if self.instance.pk:
                raise ValueError("Attempted to add a tree node that is already in the database")
            newobj = self.instance
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
        # saving the instance before returning it
        newobj.save()
        newobj._cached_parent_obj = self.node

        get_base_model_class(self.node_cls).objects.filter(
            path=self.node.path).update(numchild=F('numchild')+1)

        # we increase the numchild value of the object in memory
        self.node.numchild += 1
        transaction.commit_unless_managed()
        return newobj


class MP_AddSiblingHandler(MP_ComplexAddMoveHandler):
    def __init__(self, node, pos, instance, **kwargs):
        super(MP_AddSiblingHandler, self).__init__()
        self.node = node
        self.node_cls = node.__class__
        self.pos = pos
        self.instance = instance
        self.kwargs = kwargs

    def process(self):
        self.pos = self.node._prepare_pos_var_for_add_sibling(self.pos)

        if self.instance:
            if self.instance.pk:
                raise ValueError("Attempted to add a tree node that is already in the database")
            newobj = self.instance
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

        transaction.commit_unless_managed()
        return newobj


class MP_MoveHandler(MP_ComplexAddMoveHandler):
    def __init__(self, node, target, pos=None):
        super(MP_MoveHandler, self).__init__()
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
        transaction.commit_unless_managed()

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
                siblings = get_base_model_class(self.node_cls).objects.none()
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
        sql = "UPDATE %s SET depth=LENGTH(path)/%%s WHERE path LIKE %%s" % (
            connection.ops.quote_name(get_base_model_class(self.node_cls)._meta.db_table), )
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
    def add_root(cls, instance=None, **kwargs):
        """
        Adds a root node to the tree.

        :raise PathOverflow: when no more root objects can be added
        """
        return MP_AddRootHandler(cls, instance, **kwargs).process()

    @classmethod
    def dump_bulk(cls, parent=None, keep_ids=True):
        """Dumps a tree branch to a python data structure."""

        cls = get_base_model_class(cls)

        # Because of fix_tree, this method assumes that the depth
        # and numchild properties in the nodes can be incorrect,
        # so no helper methods are used
        qset = cls._get_serializable_model().objects.all()
        if parent:
            qset = qset.filter(path__startswith=parent.path)
        ret, lnk = [], {}
        for pyobj in serializers.serialize('python', qset):
            # django's serializer stores the attributes in 'fields'
            fields = pyobj['fields']
            path = fields['path']
            depth = int(len(path) / cls.steplen)
            # this will be useless in load_bulk
            del fields['depth']
            del fields['path']
            del fields['numchild']
            if 'id' in fields:
                # this happens immediately after a load_bulk
                del fields['id']

            newobj = {'data': fields}
            if keep_ids:
                newobj['id'] = pyobj['pk']

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
        cls = get_base_model_class(cls)

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
                where=['LENGTH(path)/%d=%d' % (cls.steplen, node.depth + 1)]
            ).count()
            if real_numchild != node.numchild:
                wrong_numchild.append(node.pk)
                continue

        return evil_chars, bad_steplen, orphans, wrong_depth, wrong_numchild

    @classmethod
    def fix_tree(cls, destructive=False):
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

        :param destructive:

            A boolean value. If True, a more agressive fix_tree method will be
            attemped. If False (the default), it will use a safe (and fast!)
            fix approach, but it will only solve the ``depth`` and
            ``numchild`` nodes, it won't fix the tree holes or broken path
            ordering.

            .. warning::

               Currently what the ``destructive`` method does is:

               1. Backup the tree with :meth:`dump_data`
               2. Remove all nodes in the tree.
               3. Restore the tree with :meth:`load_data`

               So, even when the primary keys of your nodes will be preserved,
               this method isn't foreign-key friendly. That needs complex
               in-place tree reordering, not available at the moment (hint:
               patches are welcome).
        """
        cls = get_base_model_class(cls)

        if destructive:
            dump = cls.dump_bulk(None, True)
            cls.objects.all().delete()
            cls.load_bulk(dump, None, True)
        else:
            cursor = cls._get_database_cursor('write')

            # fix the depth field
            # we need the WHERE to speed up postgres
            sql = "UPDATE %s "\
                  "SET depth=LENGTH(path)/%%s "\
                  "WHERE depth!=LENGTH(path)/%%s" % (
                      connection.ops.quote_name(cls._meta.db_table), )
            vals = [cls.steplen, cls.steplen]
            cursor.execute(sql, vals)

            # fix the numchild field
            vals = ['_' * cls.steplen]
            # the cake and sql portability are a lie
            if cls.get_database_vendor('read') == 'mysql':
                sql = "SELECT tbn1.path, tbn1.numchild, ("\
                      "SELECT COUNT(1) "\
                      "FROM %(table)s AS tbn2 "\
                      "WHERE tbn2.path LIKE "\
                      "CONCAT(tbn1.path, %%s)) AS real_numchild "\
                      "FROM %(table)s AS tbn1 "\
                      "HAVING tbn1.numchild != real_numchild" % {
                          'table': connection.ops.quote_name(
                              cls._meta.db_table)}
            else:
                subquery = "(SELECT COUNT(1) FROM %(table)s AS tbn2"\
                           " WHERE tbn2.path LIKE tbn1.path||%%s)"
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

            transaction.commit_unless_managed()

    @classmethod
    def get_tree(cls, parent=None):
        """
        :returns:

            A *queryset* of nodes ordered as DFS, including the parent.
            If no parent is given, the entire tree is returned.
        """
        cls = get_base_model_class(cls)  # method doesn't make sense when constrained to a subclass

        if parent is None:
            # return the entire tree
            return cls.objects.all()
        if parent.is_leaf():
            return cls.objects.filter(pk=parent.pk)
        return cls.objects.filter(path__startswith=parent.path,
                                  depth__gte=parent.depth)

    @classmethod
    def get_root_nodes(cls):
        """:returns: A queryset containing the root nodes in the tree."""
        return get_base_model_class(cls).objects.filter(depth=1)

    @classmethod
    def get_descendants_group_count(cls, parent=None):
        """
        Helper for a very common case: get a group of siblings and the number
        of *descendants* in every sibling.
        """

        #~
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
        #~

        cls = get_base_model_class(cls)

        if parent:
            depth = parent.depth + 1
            params = cls._get_children_path_interval(parent.path)
            extrand = 'AND path BETWEEN %s AND %s'
        else:
            depth = 1
            params = []
            extrand = ''

        sql = 'SELECT * FROM %(table)s AS t1 INNER JOIN '\
              ' (SELECT '\
              '   SUBSTR(path, 1, %(subpathlen)s) AS subpath, '\
              '   COUNT(1)-1 AS count '\
              '   FROM %(table)s '\
              '   WHERE depth >= %(depth)s %(extrand)s'\
              '   GROUP BY subpath) AS t2 '\
              ' ON t1.path=t2.subpath '\
              ' ORDER BY t1.path' % {
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
        transaction.commit_unless_managed()
        return ret

    def get_depth(self):
        """:returns: the depth (level) of the node"""
        return self.depth

    def get_siblings(self):
        """
        :returns: A queryset of all the node's siblings, including the node
            itself.
        """
        qset = get_base_model_class(self.__class__).objects.filter(depth=self.depth)
        if self.depth > 1:
            # making sure the non-root nodes share a parent
            parentpath = self._get_basepath(self.path, self.depth - 1)
            qset = qset.filter(
                path__range=self._get_children_path_interval(parentpath))
        return qset

    def get_children(self):
        """:returns: A queryset of all the node's children"""
        if self.is_leaf():
            return get_base_model_class(self.__class__).objects.none()
        return get_base_model_class(self.__class__).objects.filter(
            depth=self.depth + 1,
            path__range=self._get_children_path_interval(self.path)
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

    def add_child(self, instance=None, **kwargs):
        """
        Adds a child to the node.

        :raise PathOverflow: when no more child nodes can be added
        """
        return MP_AddChildHandler(self, instance, **kwargs).process()

    def add_sibling(self, pos=None, instance=None, **kwargs):
        """
        Adds a new node as a sibling to the current node object.

        :raise PathOverflow: when the library can't make room for the
           node's new position
        """
        return MP_AddSiblingHandler(self, pos, instance, **kwargs).process()

    def get_root(self):
        """:returns: the root node for the current node object."""
        return get_base_model_class(self.__class__).objects.get(path=self.path[0:self.steplen])

    def is_leaf(self):
        """:returns: True if the node is a leaf node (else, returns False)"""
        return self.numchild == 0

    def get_ancestors(self):
        """
        :returns: A queryset containing the current node object's ancestors,
            starting by the root node and descending to the parent.
        """
        paths = [
            self.path[0:pos]
            for pos in range(0, len(self.path), self.steplen)[1:]
        ]
        return get_base_model_class(self.__class__).objects.filter(path__in=paths).order_by('depth')

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
        self._cached_parent_obj = get_base_model_class(self.__class__).objects.get(path=parentpath)
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
        return '%s%s%s' % (parentpath,
                           '0' * (cls.steplen - len(key)),
                           key)

    def _inc_path(self):
        """:returns: The path of the next sibling of a given node path."""
        newpos = self._str2int(self.path[-self.steplen:]) + 1
        key = self._int2str(newpos)
        if len(key) > self.steplen:
            raise PathOverflow(_("Path Overflow from: '%s'" % (self.path, )))
        return '%s%s%s' % (self.path[:-self.steplen],
                           '0' * (self.steplen - len(key)),
                           key)

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
