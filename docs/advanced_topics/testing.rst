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

            def test_can_create_content_page(self):
                # Get the HomePage
                root_page = HomePage.objects.get(pk=2)

                # Assert that a ContentPage can be made here, with this POST data
                self.assertCanCreate(root_page, ContentPage, {
                    'title': 'About us',
                    'body': 'Lorem ipsum dolor sit amet')

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
