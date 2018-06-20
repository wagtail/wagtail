.. _reference:

=========================
Testing your Wagtail site
=========================

Wagtail comes with some utilities that simplify writing tests for your site.

.. automodule:: wagtail.tests.utils


WagtailPageTests
================

.. class:: WagtailPageTests

    ``WagtailPageTests`` extends ``django.test.TestCase``, adding a few new ``assert`` methods. You should extend this class to make use of its methods:

    .. code-block:: python

        from wagtail.tests.utils import WagtailPageTests
        from myapp.models import MyPage

        class MyPageTests(WagtailPageTests):
            def test_can_create_a_page(self):
                ...

    .. automethod:: assertCanCreateAt

        .. code-block:: python

            def test_can_create_under_home_page(self):
                # You can create a ContentPage under a HomePage
                self.assertCanCreateAt(HomePage, ContentPage)

    .. automethod:: assertCanNotCreateAt

        .. code-block:: python

            def test_cant_create_under_event_page(self):
                # You can not create a ContentPage under an EventPage
                self.assertCanNotCreateAt(EventPage, ContentPage)

    .. automethod:: assertCanCreate

        .. code-block:: python

            from wagtail.tests.utils.form_data import nested_form_data, streamfield

            def test_can_create_content_page(self):
                # Get the HomePage
                root_page = HomePage.objects.get(pk=2)

                # Assert that a ContentPage can be made here, with this POST data
                self.assertCanCreate(root_page, ContentPage, nested_form_data({
                    'title': 'About us',
                    'body': streamfield([
                        ('text', 'Lorem ipsum dolor sit amet'),
                    ])
                }))

        See :ref:`form_data_test_helpers` for a set of functions useful for constructing POST data.

    .. automethod:: assertAllowedParentPageTypes

        .. code-block:: python

            def test_content_page_parent_pages(self):
                # A ContentPage can only be created under a HomePage
                # or another ContentPage
                self.assertAllowedParentPageTypes(
                    ContentPage, {HomePage, ContentPage})

                # An EventPage can only be created under an EventIndex
                self.assertAllowedParentPageTypes(
                    EventPage, {EventIndex})

    .. automethod:: assertAllowedSubpageTypes

        .. code-block:: python

            def test_content_page_subpages(self):
                # A ContentPage can only have other ContentPage children
                self.assertAllowedSubpageTypes(
                    ContentPage, {ContentPage})

                # A HomePage can have ContentPage and EventIndex children
                self.assertAllowedParentPageTypes(
                    HomePage, {ContentPage, EventIndex})


.. _form_data_test_helpers:

Form data helpers
=================

.. automodule:: wagtail.tests.utils.form_data

   .. autofunction:: nested_form_data

   .. autofunction:: rich_text

   .. autofunction:: streamfield

   .. autofunction:: inline_formset



Fixtures
========

Using ``dumpdata``
------------------

Creating fixtures_ for tests is best done by creating content in a development environment,
and using Django's dumpdata_ command.

Note that by default ``dumpdata`` will represent ``content_type`` by the primary key; this may cause consistency issues when adding / removing models, as content types are populated separately from fixtures. To prevent this, use the ``--natural-foreign`` switch, which represents content types by ``["app", "model"]`` instead.


Manual modification
-------------------

You could modify the dumped fixtures manually, or even write them all by hand.
Here are a few things to be wary of.


Custom Page models
~~~~~~~~~~~~~~~~~~

When creating customised Page models in fixtures, you will need to add both a
``wagtailcore.page`` entry, and one for your custom Page model.

Let's say you have a ``website`` module which defines a ``Homepage(Page)`` class.
You could create such a homepage in a fixture with:

.. code-block:: json

    [
      {
        "model": "wagtailcore.page",
        "pk": 3,
        "fields": {
          "title": "My Customer's Homepage",
          "content_type": ["website", "homepage"],
          "depth": 2
        }
      },
      {
        "model": "website.homepage",
        "pk": 3,
        "fields": {}
      }
    ]


Treebeard fields
~~~~~~~~~~~~~~~~

Filling in the ``path`` / ``numchild`` / ``depth`` fields is necessary in order for tree operations like ``get_parent()`` to work correctly.
``url_path`` is another field that can cause errors in some uncommon cases if it isn't filled in.

The `Treebeard docs`_ might help in understanding how this works.

.. _fixtures: https://docs.djangoproject.com/en/2.0/howto/initial-data/
.. _dumpdata: https://docs.djangoproject.com/en/2.0/ref/django-admin/#django-admin-dumpdata
.. _Treebeard docs: http://django-treebeard.readthedocs.io/en/latest/mp_tree.html
