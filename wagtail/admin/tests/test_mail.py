from django.contrib.auth.models import Group
from django.core import mail
from django.test import TestCase, override_settings

from wagtail.admin.mail import EmailNotificationMixin, Notifier
from wagtail.core.models import Page
from wagtail.tests.testapp.models import SimplePage
from wagtail.tests.utils import WagtailTestUtils


class TestNotifier(EmailNotificationMixin, Notifier):
    notification = "approved"

    def __init__(self, *args, **kwargs):
        self.recipients = kwargs.pop("recipients")

    def can_handle(self, instance, **kwargs):
        return True

    def get_recipient_users(self, instance, **kwargs):
        return self.recipients

    def get_context(self, instance, **kwargs):
        return {
            "page": instance
        }

    def get_template_base_prefix(self, instance, **kwargs):
        return "task_state_"


class TestEmailNotificationMixin(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create 5 editors
        self.editor_users = []
        editors = Group.objects.get(name='Editors')
        for i in range(5):
            editor = self.create_user(
                username='editor{}'.format(i),
                email='editor{}@email.com'.format(i),
                password='password',
            )
            self.editor_users.append(editor)
            editors.user_set.add(editor)

        root_page = Page.objects.get(id=2)
        self.page = SimplePage(
            title="Hello world!",
            slug='hello-world',
            content="hello",
            live=False,
            has_unpublished_changes=True,
        )

        root_page.add_child(instance=self.page)

    def test_non_bulk_emails(self):
        notifier = TestNotifier(recipients=self.editor_users)
        notifier(instance=self.page)

        self.assertEqual(len(mail.outbox), 5)

    @override_settings(WAGTAILADMIN_NOTIFICATION_BULK_SEND_THRESHOLD=2)
    def test_bulk_emails(self):
        notifier = TestNotifier(recipients=self.editor_users)
        notifier(instance=self.page)

        self.assertEqual(len(mail.outbox), 1)
