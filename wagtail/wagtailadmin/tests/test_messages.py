from __future__ import absolute_import, unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings


class TestPageExplorer(TestCase):
    @override_settings(MESSAGE_TAGS={
        messages.DEBUG: 'my-custom-tag',
        messages.INFO: 'my-custom-tag',
        messages.SUCCESS: 'my-custom-tag',
        messages.WARNING: 'my-custom-tag',
        messages.ERROR: 'my-custom-tag',
    })
    def test_message_tag_classes(self):
        url = reverse('testapp_message_test')

        response = self.client.post(url, {'level': 'success', 'message': 'A message'},
                                    follow=True)
        # Make sure the message appears
        self.assertContains(response, 'A message')
        # Make sure the Wagtail-require CSS tag appears
        self.assertContains(response, 'success')
        # Make sure the classes set in the settings do *not* appear
        self.assertNotContains(response, 'my-custom-tag')

        response = self.client.post(url, {'level': 'error', 'message': 'Danger danger!'},
                                    follow=True)
        self.assertContains(response, 'Danger danger!')
        self.assertContains(response, 'error')
        self.assertNotContains(response, 'my-custom-tag')
