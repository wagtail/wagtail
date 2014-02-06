Adjacency List trees
====================

.. module:: treebeard.al_tree

This is a simple implementation of the traditional Adjacency List Model for
storing trees in relational databases.

In the adjacency list model, every node will have a
":attr:`~AL_Node.parent`" key, that will be NULL for root nodes.

Since ``django-treebeard`` must return trees ordered in a predictable way,
the ordering for models without the :attr:`~AL_Node.node_order_by`
attribute will have an extra attribute that will store the relative
position of a node between it's siblings: :attr:`~AL_Node.sib_order`.

The adjacency list model has the advantage of fast writes at the cost of
slow reads. If you read more than you write, use
:class:`~treebeard.mp_tree.MP_Node` instead.

.. warning::

   As with all tree implementations, please be aware of the
   :doc:`caveats`.


.. inheritance-diagram:: AL_Node
.. autoclass:: AL_Node
   :show-inheritance:

   .. warning::

     If you need to define your own
     :py:class:`~django.db.models.Manager` class,
     you'll need to subclass
     :py:class:`~AL_NodeManager`.


   .. attribute:: node_order_by

      Attribute: a list of model fields that will be used for node
      ordering. When enabled, all tree operations will assume this ordering.

      Example:

      .. code-block:: python

         node_order_by = ['field1', 'field2', 'field3']

   .. attribute:: parent

      ``ForeignKey`` to itself. This attribute **MUST** be defined in the
      subclass (sadly, this isn't inherited correctly from the ABC in
      `Django 1.0`). Just copy&paste these lines to your model:

      .. code-block:: python

               parent = models.ForeignKey('self',
                                          related_name='children_set',
                                          null=True,
                                          db_index=True)

   .. attribute:: sib_order

      ``PositiveIntegerField`` used to store the relative position of a node
      between it's siblings. This attribute is mandatory *ONLY* if you don't
      set a :attr:`node_order_by` field. You can define it copy&pasting this
      line in your model:

      .. code-block:: python

              sib_order = models.PositiveIntegerField()

   Examples:

   .. code-block:: python

           class AL_TestNode(AL_Node):
               parent = models.ForeignKey('self',
                                          related_name='children_set',
                                          null=True,
                                          db_index=True)
               sib_order = models.PositiveIntegerField()
               desc = models.CharField(max_length=255)

           class AL_TestNodeSorted(AL_Node):
               parent = models.ForeignKey('self',
                                          related_name='children_set',
                                          null=True,
                                          db_index=True)
               node_order_by = ['val1', 'val2', 'desc']
               val1 = models.IntegerField()
               val2 = models.IntegerField()
               desc = models.CharField(max_length=255)


   Read the API reference of :class:`treebeard.Node` for info on methods
   available in this class, or read the following section for methods with
   particular arguments or exceptions.
   
   .. automethod:: get_depth

        See: :meth:`treebeard.Node.get_depth`

.. autoclass:: AL_NodeManager
  :show-inheritance:
