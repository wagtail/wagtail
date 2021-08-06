from django.test import TestCase
from django.urls import reverse
from django.utils.text import slugify

from .wagtail_tests import WagtailTestUtils


class WagtailPageTests(WagtailTestUtils, TestCase):
    """
    A set of asserts to help write tests for your own Wagtail site.
    """
    def setUp(self):
        super().setUp()
        self.login()

    def _testCanCreateAt(self, parent_model, child_model):
        return child_model in parent_model.allowed_subpage_models()

    def assertCanCreateAt(self, parent_model, child_model, msg=None):
        """
        Assert a particular child Page type can be created under a parent
        Page type. ``parent_model`` and ``child_model`` should be the Page
        classes being tested.
        """
        if not self._testCanCreateAt(parent_model, child_model):
            msg = self._formatMessage(msg, "Can not create a %s.%s under a %s.%s" % (
                child_model._meta.app_label, child_model._meta.model_name,
                parent_model._meta.app_label, parent_model._meta.model_name))
            raise self.failureException(msg)

    def assertCanNotCreateAt(self, parent_model, child_model, msg=None):
        """
        Assert a particular child Page type can not be created under a parent
        Page type. ``parent_model`` and ``child_model`` should be the Page
        classes being tested.
        """
        if self._testCanCreateAt(parent_model, child_model):
            msg = self._formatMessage(msg, "Can create a %s.%s under a %s.%s" % (
                child_model._meta.app_label, child_model._meta.model_name,
                parent_model._meta.app_label, parent_model._meta.model_name))
            raise self.failureException(msg)

    def assertCanCreate(self, parent, child_model, data, msg=None):
        """
        Assert that a child of the given Page type can be created under the
        parent, using the supplied POST data.

        ``parent`` should be a Page instance, and ``child_model`` should be a
        Page subclass. ``data`` should be a dict that will be POSTed at the
        Wagtail admin Page creation method.
        """
        self.assertCanCreateAt(parent.specific_class, child_model)

        if 'slug' not in data and 'title' in data:
            data['slug'] = slugify(data['title'])
        data['action-publish'] = 'action-publish'

        add_url = reverse('wagtailadmin_pages:add', args=[
            child_model._meta.app_label, child_model._meta.model_name, parent.pk])
        response = self.client.post(add_url, data, follow=True)

        if response.status_code != 200:
            msg = self._formatMessage(msg, 'Creating a %s.%s returned a %d' % (
                child_model._meta.app_label, child_model._meta.model_name, response.status_code))
            raise self.failureException(msg)

        if response.redirect_chain == []:
            if 'form' not in response.context:
                msg = self._formatMessage(msg, 'Creating a page failed unusually')
                raise self.failureException(msg)
            form = response.context['form']
            if not form.errors:
                msg = self._formatMessage(msg, 'Creating a page failed for an unknown reason')
                raise self.failureException(msg)

            errors = '\n'.join('  %s:\n    %s' % (field, '\n    '.join(errors))
                               for field, errors in sorted(form.errors.items()))
            msg = self._formatMessage(msg, 'Validation errors found when creating a %s.%s:\n%s' % (
                child_model._meta.app_label, child_model._meta.model_name, errors))
            raise self.failureException(msg)

        explore_url = reverse('wagtailadmin_explore', args=[parent.pk])
        if response.redirect_chain != [(explore_url, 302)]:
            msg = self._formatMessage(msg, 'Creating a page %s.%s didn\'t redirect the user to the explorer, but to %s' % (
                child_model._meta.app_label, child_model._meta.model_name,
                response.redirect_chain))
            raise self.failureException(msg)

    def assertAllowedSubpageTypes(self, parent_model, child_models, msg=None):
        """
        Test that the only page types that can be created under
        ``parent_model`` are ``child_models``.

        The list of allowed child models may differ from those set in
        ``Page.subpage_types``, if the child models have set
        ``Page.parent_page_types``.
        """
        self.assertEqual(
            set(parent_model.allowed_subpage_models()),
            set(child_models),
            msg=msg)

    def assertAllowedParentPageTypes(self, child_model, parent_models, msg=None):
        """
        Test that the only page types that ``child_model`` can be created under
        are ``parent_models``.

        The list of allowed parent models may differ from those set in
        ``Page.parent_page_types``, if the parent models have set
        ``Page.subpage_types``.
        """
        self.assertEqual(
            set(child_model.allowed_parent_page_models()),
            set(parent_models),
            msg=msg)
