Nested Sets trees
=================

.. module:: treebeard.ns_tree

An implementation of Nested Sets trees for Django 1.4+, as described by
`Joe Celko`_ in `Trees and Hierarchies in SQL for Smarties`_.

Nested sets have very efficient reads at the cost of high maintenance on
write/delete operations.

.. warning::

   As with all tree implementations, please be aware of the
   :doc:`caveats`.


.. inheritance-diagram:: NS_Node
.. autoclass:: NS_Node
  :show-inheritance:

  .. warning::

     If you need to define your own
     :py:class:`~django.db.models.Manager` class,
     you'll need to subclass
     :py:class:`~NS_NodeManager`.

     Also, if in your manager you need to change the default
     queryset handler, you'll need to subclass
     :py:class:`~NS_NodeQuerySet`.


  .. attribute:: node_order_by

     Attribute: a list of model fields that will be used for node
     ordering. When enabled, all tree operations will assume this ordering.

     Example:

     .. code-block:: python

        node_order_by = ['field1', 'field2', 'field3']

  .. attribute:: depth

     ``PositiveIntegerField``, depth of a node in the tree. A root node
     has a depth of *1*.

  .. attribute:: lft

     ``PositiveIntegerField``

  .. attribute:: rgt

     ``PositiveIntegerField``

  .. attribute:: tree_id

     ``PositiveIntegerField``

  .. automethod:: get_tree

        See: :meth:`treebeard.Node.get_tree`

        .. note::

            This metod returns a queryset.


.. autoclass:: NS_NodeManager
  :show-inheritance:

.. autoclass:: NS_NodeQuerySet
  :show-inheritance:



.. _`Joe Celko`: http://en.wikipedia.org/wiki/Joe_Celko
.. _`Trees and Hierarchies in SQL for Smarties`:
  http://www.elsevier.com/wps/product/cws_home/702605
