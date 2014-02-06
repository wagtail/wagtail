Tutorial
========

Create a basic model for your tree. In this example we'll use a Materialized
Path tree:

.. code-block:: python

    from django.db import models
    from treebeard.mp_tree import MP_Node

    class Category(MP_Node):
        name = models.CharField(max_length=30)

        node_order_by = ['name']

        def __unicode__(self):
            return 'Category: %s' % self.name



Run syncdb:

.. code-block:: console

    $ python manage.py syncdb


Let's create some nodes:

.. code-block:: python

    >>> from treebeard_tutorial.models import Category
    >>> get = lambda node_id: Category.objects.get(pk=node_id)
    >>> root = Category.add_root(name='Computer Hardware')
    >>> node = get(root.pk).add_child(name='Memory')
    >>> get(node.pk).add_sibling(name='Hard Drives')
    <Category: Category: Hard Drives>
    >>> get(node.pk).add_sibling(name='SSD')
    <Category: Category: SSD>
    >>> get(node.pk).add_child(name='Desktop Memory')
    <Category: Category: Desktop Memory>
    >>> get(node.pk).add_child(name='Laptop Memory')
    <Category: Category: Laptop Memory>
    >>> get(node.pk).add_child(name='Server Memory')
    <Category: Category: Server Memory>

.. note::

    Why retrieving every node again after the first operation? Because
    ``django-treebeard`` uses raw queries for most write operations,
    and raw queries don't update the django objects of the db entries they
    modify. See: :doc:`caveats`.

We just created this tree:


.. digraph:: introduction_digraph

  "Computer Hardware";
  "Computer Hardware" -> "Hard Drives";
  "Computer Hardware" -> "Memory";
  "Memory" -> "Desktop Memory";
  "Memory" -> "Laptop Memory";
  "Memory" -> "Server Memory";
  "Computer Hardware" -> "SSD";


You can see the tree structure with code:

.. code-block:: python

    >>> Category.dump_bulk()
    [{'id': 1, 'data': {'name': u'Computer Hardware'},
      'children': [
         {'id': 3, 'data': {'name': u'Hard Drives'}},
         {'id': 2, 'data': {'name': u'Memory'},
          'children': [
             {'id': 5, 'data': {'name': u'Desktop Memory'}},
             {'id': 6, 'data': {'name': u'Laptop Memory'}},
             {'id': 7, 'data': {'name': u'Server Memory'}}]},
         {'id': 4, 'data': {'name': u'SSD'}}]}]
    >>> Category.get_annotated_list()
    [(<Category: Category: Computer Hardware>,
      {'close': [], 'level': 0, 'open': True}),
     (<Category: Category: Hard Drives>,
      {'close': [], 'level': 1, 'open': True}),
     (<Category: Category: Memory>,
      {'close': [], 'level': 1, 'open': False}),
     (<Category: Category: Desktop Memory>,
      {'close': [], 'level': 2, 'open': True}),
     (<Category: Category: Laptop Memory>,
      {'close': [], 'level': 2, 'open': False}),
     (<Category: Category: Server Memory>,
      {'close': [0], 'level': 2, 'open': False}),
     (<Category: Category: SSD>,
      {'close': [0, 1], 'level': 1, 'open': False})]



Read the :class:`treebeard.models.Node` API reference for detailed info.

.. _`treebeard mercurial repository`:
   http://code.tabo.pe/django-treebeard
.. _`latest treebeard version from PyPi`:
   http://pypi.python.org/pypi/django-treebeard/
