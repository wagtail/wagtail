Materialized Path trees
=======================

.. module:: treebeard.mp_tree

This is an efficient implementation of Materialized Path
trees for Django 1.4+, as described by `Vadim Tropashko`_ in `SQL Design
Patterns`_. Materialized Path is probably the fastest way of working with
trees in SQL without the need of extra work in the database, like Oracle's
``CONNECT BY`` or sprocs and triggers for nested intervals.

In a materialized path approach, every node in the tree will have a
:attr:`~MP_Node.path` attribute, where the full path from the root
to the node will be stored. This has the advantage of needing very simple
and fast queries, at the risk of inconsistency because of the
denormalization of ``parent``/``child`` foreign keys. This can be prevented
with transactions.

``django-treebeard`` uses a particular approach: every step in the path has
a fixed width and has no separators. This makes queries predictable and
faster at the cost of using more characters to store a step. To address
this problem, every step number is encoded.

Also, two extra fields are stored in every node:
:attr:`~MP_Node.depth` and :attr:`~MP_Node.numchild`.
This makes the read operations faster, at the cost of a little more
maintenance on tree updates/inserts/deletes. Don't worry, even with these
extra steps, materialized path is more efficient than other approaches.

.. warning::

   As with all tree implementations, please be aware of the
   :doc:`caveats`.

.. note::

   The materialized path approach makes heavy use of ``LIKE`` in your
   database, with clauses like ``WHERE path LIKE '002003%'``. If you think
   that ``LIKE`` is too slow, you're right, but in this case the
   :attr:`~MP_Node.path` field is indexed in the database, and all
   ``LIKE`` clauses that don't **start** with a ``%`` character will use
   the index. This is what makes the materialized path approach so fast.

.. inheritance-diagram:: MP_Node
.. autoclass:: MP_Node
  :show-inheritance:

  .. warning::

     Do not change the values of :attr:`path`, :attr:`depth` or
     :attr:`numchild` directly: use one of the included methods instead.
     Consider these values *read-only*.

  .. warning::

     Do not change the values of the :attr:`steplen`, :attr:`alphabet` or
     :attr:`node_order_by` after saving your first object. Doing so will
     corrupt the tree.

  .. warning::

     If you need to define your own
     :py:class:`~django.db.models.Manager` class,
     you'll need to subclass
     :py:class:`~MP_NodeManager`.

     Also, if in your manager you need to change the default
     queryset handler, you'll need to subclass
     :py:class:`~MP_NodeQuerySet`.


  Example:

  .. code-block:: python

     class SortedNode(MP_Node):
        node_order_by = ['numval', 'strval']

        numval = models.IntegerField()
        strval = models.CharField(max_length=255)

  Read the API reference of :class:`treebeard.Node` for info on methods
  available in this class, or read the following section for methods with
  particular arguments or exceptions.

  .. attribute:: steplen

     Attribute that defines the length of each step in the :attr:`path` of
     a node.  The default value of *4* allows a maximum of
     *1679615* children per node. Increase this value if you plan to store
     large trees (a ``steplen`` of *5* allows more than *60M* children per
     node). Note that increasing this value, while increasing the number of
     children per node, will decrease the max :attr:`depth` of the tree (by
     default: *63*). To increase the max :attr:`depth`, increase the
     max_length attribute of the :attr:`path` field in your model.

  .. attribute:: alphabet

     Attribute: the alphabet that will be used in base conversions
     when encoding the path steps into strings. The default value,
     ``0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ`` is the most optimal possible
     value that is portable between the supported databases (which means:
     their default collation will order the :attr:`path` field correctly).

     .. note::

        In case you know what you are doing, there is a test that is
        disabled by default that can tell you the optimal default alphabet
        in your enviroment. To run the test you must enable the
        :envvar:`TREEBEARD_TEST_ALPHABET` enviroment variable:

        .. code-block:: console

          $ TREEBEARD_TEST_ALPHABET=1 python manage.py test treebeard.TestTreeAlphabet

        On my Mountain Lion system, these are the optimal values for the
        three supported databases in their *default* configuration:

         ================ ================
         Database         Optimal Alphabet
         ================ ================
         MySQL 5.6.10     0-9A-Z
         PostgreSQL 9.2.4 0-9A-Z
         Sqlite3          0-9A-Z
         ================ ================

  .. attribute:: node_order_by

     Attribute: a list of model fields that will be used for node
     ordering. When enabled, all tree operations will assume this ordering.

     Example:

     .. code-block:: python

       node_order_by = ['field1', 'field2', 'field3']

  .. attribute:: path

     ``CharField``, stores the full materialized path for each node. The
     default value of it's max_length, *255*, is the max efficient and
     portable value for a ``varchar``. Increase it to allow deeper trees (max
     depth by default: *63*)

     .. note::

       `django-treebeard` uses Django's abstract model inheritance, so:

       1. To change the max_length value of the path in your model, you
          can't just define it since you'd get a django exception, you have
          to modify the already defined attribute:

          .. code-block:: python

            class MyNodeModel(MP_Node):
                pass

            MyNodeModel._meta.get_field('path').max_length = 1024

       2. You can't rely on Django's `auto_now` properties in date fields
          for sorting, you'll have to manually set the value before creating
          a node:

          .. code-block:: python

            class TestNodeSortedAutoNow(MP_Node):
                desc = models.CharField(max_length=255)
                created = models.DateTimeField(auto_now_add=True)
                node_order_by = ['created']

            TestNodeSortedAutoNow.add_root(desc='foo',
                                           created=datetime.datetime.now())

     .. note::

       For performance, and if your database allows it, you can safely
       define the path column as ASCII (not utf-8/unicode/iso8859-1/etc) to
       keep the index smaller (and faster). Also note that some databases
       (mysql) have a small index size limit. InnoDB for instance has a
       limit of 765 bytes per index, so that would be the limit if your path
       is ASCII encoded. If your path column in InnoDB is using unicode,
       the index limit will be 255 characters since in MySQL's indexes,
       unicode means 3 bytes per character.

     .. note::

        ``django-treebeard`` uses `numconv`_ for path encoding.


  .. attribute:: depth

     ``PositiveIntegerField``, depth of a node in the tree. A root node
     has a depth of *1*.

  .. attribute:: numchild

     ``PositiveIntegerField``, the number of children of the node.

  .. automethod:: add_root

     See: :meth:`treebeard.Node.add_root`

  .. automethod:: add_child

     See: :meth:`treebeard.Node.add_child`

  .. automethod:: add_sibling

     See: :meth:`treebeard.Node.add_sibling`

  .. automethod:: move

     See: :meth:`treebeard.Node.move`

  .. automethod:: get_tree

     See: :meth:`treebeard.Node.get_tree`

     .. note::

        This metod returns a queryset.

  .. automethod:: find_problems

     .. note::

        A node won't appear in more than one list, even when it exhibits
        more than one problem. This method stops checking a node when it
        finds a problem and continues to the next node.

     .. note::

        Problems 1, 2 and 3 can't be solved automatically.

     Example:

     .. code-block:: python

        MyNodeModel.find_problems()

  .. automethod:: fix_tree

     Example:

     .. code-block:: python

        MyNodeModel.fix_tree()



.. autoclass:: MP_NodeManager
  :show-inheritance:

.. autoclass:: MP_NodeQuerySet
  :show-inheritance:



.. _`Vadim Tropashko`: http://vadimtropashko.wordpress.com/
.. _`Sql Design Patterns`:
   http://www.rampant-books.com/book_2006_1_sql_coding_styles.htm
.. _numconv: https://tabo.pe/projects/numconv/
