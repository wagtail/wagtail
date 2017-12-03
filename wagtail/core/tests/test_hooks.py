from copy import deepcopy

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.tests.testapp.models import SimplePage
from wagtail.tests.utils import WagtailTestUtils
from wagtail.core import hooks
from wagtail.core.models import Site


TEMPLATES_DEBUG_FALSE = deepcopy(settings.TEMPLATES)
TEMPLATES_DEBUG_FALSE[0]['OPTIONS']['debug'] = False


def test_hook():
    pass


class TestLoginView(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        super().setUp()
        site = Site.objects.get(is_default_site=True)
        self.root = site.root_page.specific
        self.login()

    @classmethod
    def setUpClass(cls):
        hooks.register('test_hook_name', test_hook)

    @classmethod
    def tearDownClass(cls):
        del hooks._hooks['test_hook_name']

    def test_before_hook(self):
        def before_hook():
            pass

        with self.register_hook('test_hook_name', before_hook, order=-1):
            hook_fns = hooks.get_hooks('test_hook_name')
            self.assertEqual(hook_fns, [before_hook, test_hook])

    def test_after_hook(self):
        def after_hook():
            pass

        with self.register_hook('test_hook_name', after_hook, order=1):
            hook_fns = hooks.get_hooks('test_hook_name')
            self.assertEqual(hook_fns, [test_hook, after_hook])


    @override_settings(DEBUG=False, TEMPLATES=TEMPLATES_DEBUG_FALSE)
    def test_exceptions_limited_to_hooks(self):
        """
        Test behaviour of hooks when one of them raises an exception.
        This test will be no longer necessary starting with Django 2.1.
        See https://github.com/wagtail/wagtail/issues/4080
        """

        def hook_raising_exception():
            raise Exception

        with self.register_hook('insert_editor_js', test_hook):
            with self.register_hook('insert_editor_js', hook_raising_exception):
                # hook_output.html is used for both insert_editor_css and insert_editor_js
                with self.assertTemplateUsed('wagtailadmin/shared/hook_output.html', count=2):
                    add_url = reverse('wagtailadmin_pages:add', args=[
                        SimplePage._meta.app_label, SimplePage._meta.model_name, self.root.pk
                    ])
                    response = self.client.get(add_url)

                    # the rest of the _editor_js.html include is still rendered
                    self.assertContains(response, 'page-editor.js')

                    # the insert_editor_css hook works too
                    self.assertContains(response, '<!-- hook_output insert_editor_css -->')

                    # The insert_editor_js hook raised an exception,
                    # so its hook_output.html template doesn't get rendered at all.
                    # In fact, none of the insert_editor_js hooks will be rendered.
                    self.assertNotContains(response, '<!-- hook_output insert_editor_js -->')
