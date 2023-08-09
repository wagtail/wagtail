from django.test import TestCase
from django.urls import reverse


class TestPageExplorer(TestCase):
    def test_message_tag_classes(self):
        url = reverse("testapp_message_test")

        response = self.client.post(
            url, {"level": "success", "message": "A message"}, follow=True
        )
        # Make sure the message appears
        self.assertContains(response, "A message")
        # Make sure the Wagtail-require CSS tag appears
        self.assertContains(response, "success")

        # https://github.com/wagtail/wagtail/issues/2551 -
        # `my-custom-tag` is set in MESSAGE_TAGS in the project settings, which
        # end-users should be able to do without it leaking into the admin styles.
        self.assertNotContains(response, "my-custom-tag")

        response = self.client.post(
            url, {"level": "error", "message": "Danger danger!"}, follow=True
        )
        self.assertContains(response, "Danger danger!")
        self.assertContains(response, "error")
        self.assertNotContains(response, "my-custom-tag")
