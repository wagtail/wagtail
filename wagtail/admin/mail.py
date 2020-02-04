import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import get_connection
from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import override

from wagtail.admin.auth import users_with_page_permission
from wagtail.core.models import GroupApprovalTask, Page, PageRevision, TaskState, WorkflowState
from wagtail.core.utils import camelcase_to_underscore
from wagtail.users.models import UserProfile


logger = logging.getLogger('wagtail.admin')


class OpenedConnection:
    """Context manager for mail connections to ensure they are closed when manually opened"""
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        self.connection.open()
        return self.connection

    def __exit__(self, type, value, traceback):
        self.connection.close()
        return self.connection


def send_mail(subject, message, recipient_list, from_email=None, **kwargs):
    """
    Wrapper around Django's EmailMultiAlternatives as done in send_mail().
    Custom from_email handling and special Auto-Submitted header.
    """
    if not from_email:
        if hasattr(settings, 'WAGTAILADMIN_NOTIFICATION_FROM_EMAIL'):
            from_email = settings.WAGTAILADMIN_NOTIFICATION_FROM_EMAIL
        elif hasattr(settings, 'DEFAULT_FROM_EMAIL'):
            from_email = settings.DEFAULT_FROM_EMAIL
        else:
            from_email = 'webmaster@localhost'

    connection = kwargs.get('connection', False) or get_connection(
        username=kwargs.get('auth_user', None),
        password=kwargs.get('auth_password', None),
        fail_silently=kwargs.get('fail_silently', None),
    )
    multi_alt_kwargs = {
        'connection': connection,
        'headers': {
            'Auto-Submitted': 'auto-generated',
        }
    }
    mail = EmailMultiAlternatives(subject, message, from_email, recipient_list, **multi_alt_kwargs)
    html_message = kwargs.get('html_message', None)
    if html_message:
        mail.attach_alternative(html_message, 'text/html')

    return mail.send()


def send_notification(page_revision_id, notification, excluded_user_id):
    # Get revision
    revision = PageRevision.objects.get(id=page_revision_id)

    # Get list of recipients
    if notification == 'submitted':
        # Get list of publishers
        include_superusers = getattr(settings, 'WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS', True)
        recipients = users_with_page_permission(revision.page, 'publish', include_superusers)
    elif notification in ['rejected', 'approved']:
        # Get submitter
        recipients = [revision.user]
    else:
        return False

    # Get list of email addresses
    email_recipients = [
        recipient for recipient in recipients
        if recipient.email and recipient.pk != excluded_user_id and getattr(
            UserProfile.get_for_user(recipient),
            notification + '_notifications'
        )
    ]

    # Return if there are no email addresses
    if not email_recipients:
        return True

    # Get template
    template_subject = 'wagtailadmin/notifications/' + notification + '_subject.txt'
    template_text = 'wagtailadmin/notifications/' + notification + '.txt'
    template_html = 'wagtailadmin/notifications/' + notification + '.html'

    # Common context to template
    context = {
        "revision": revision,
        "settings": settings,
    }

    connection = get_connection()

    with OpenedConnection(connection) as open_connection:

        # Send emails
        sent_count = 0
        for recipient in email_recipients:
            try:
                # update context with this recipient
                context["user"] = recipient

                # Translate text to the recipient language settings
                with override(recipient.wagtail_userprofile.get_preferred_language()):
                    # Get email subject and content
                    email_subject = render_to_string(template_subject, context).strip()
                    email_content = render_to_string(template_text, context).strip()

                kwargs = {}
                if getattr(settings, 'WAGTAILADMIN_NOTIFICATION_USE_HTML', False):
                    kwargs['html_message'] = render_to_string(template_html, context)

                # Send email
                print(recipient.email)
                send_mail(email_subject, email_content, [recipient.email], connection=open_connection, **kwargs)
                sent_count += 1
            except Exception:
                logger.exception(
                    "Failed to send notification email '%s' to %s",
                    email_subject, recipient.email
                )

    return sent_count == len(email_recipients)


class Notifier:
    """Generic class for sending event notifications: callable, intended to be connected to a signal to send
    notifications using rendered templates. """

    notification = ''

    def __init__(self, valid_classes):
        # the classes of the calling instance that the notifier can handle
        self.valid_classes = valid_classes

    def can_handle(self, instance, **kwargs):
        """Returns True if the Notifier can handle sending the notification from the instance, otherwise False"""
        return isinstance(instance, self.valid_classes)

    def get_valid_recipients(self, instance, **kwargs):
        """Returns a set of the final list of recipients for the notification message"""
        return set()

    def get_template_base_prefix(self, instance, **kwargs):
        return camelcase_to_underscore(type(instance).__name__)+'_'

    def get_context(self, instance, **kwargs):
        return {'settings': settings}

    def get_template_set(self, instance, **kwargs):
        """Return a dictionary of template paths for the templates: by default, a text message"""
        template_base = self.get_template_base_prefix(instance) + self.notification

        template_text = 'wagtailadmin/notifications/' + template_base + '.txt'

        return {
            'text': template_text,
        }

    def send_notifications(self, template_set, context, recipients, **kwargs):
        raise NotImplementedError

    def __call__(self, instance=None, **kwargs):
        """Send notifications from an instance (intended to be the signal sender), returning True if all sent correctly
        and False otherwise"""

        if not self.can_handle(instance, **kwargs):
            return False

        recipients = self.get_valid_recipients(instance, **kwargs)

        if not recipients:
            return True

        template_set = self.get_template_set(instance, **kwargs)

        context = self.get_context(instance, **kwargs)

        return self.send_notifications(template_set, context, recipients, **kwargs)


class EmailNotifier(Notifier):
    """Class for sending email notifications upon events"""

    def get_recipient_users(self, instance, **kwargs):
        """Gets the ideal set of recipient users, without accounting for notification preferences or missing email addresses"""

        return set()

    def get_valid_recipients(self, instance, **kwargs):
        """Filters notification recipients to those allowing the notification type on their UserProfile, and those
        with an email address"""

        return {recipient for recipient in self.get_recipient_users(instance, **kwargs) if recipient.email and getattr(
            UserProfile.get_for_user(recipient),
            self.notification + '_notifications'
        )}


    def get_template_set(self, instance, **kwargs):
        """Return a dictionary of template paths for the templates for the email subject and the text and html
        alternatives"""
        template_base = self.get_template_base_prefix(instance) + self.notification

        template_subject = 'wagtailadmin/notifications/' + template_base + '_subject.txt'
        template_text = 'wagtailadmin/notifications/' + template_base + '.txt'
        template_html = 'wagtailadmin/notifications/' + template_base + '.html'

        return {
            'subject': template_subject,
            'text': template_text,
            'html': template_html,
        }

    def send_emails(self, template_set, context, recipients, **kwargs):

        connection = get_connection()

        with OpenedConnection(connection) as open_connection:

            # Send emails
            sent_count = 0
            for recipient in recipients:
                try:

                    # update context with this recipient
                    context["user"] = recipient

                    # Translate text to the recipient language settings
                    with override(recipient.wagtail_userprofile.get_preferred_language()):
                        # Get email subject and content
                        email_subject = render_to_string(template_set['subject'], context).strip()
                        email_content = render_to_string(template_set['text'], context).strip()

                    kwargs = {}
                    if getattr(settings, 'WAGTAILADMIN_NOTIFICATION_USE_HTML', False):
                        kwargs['html_message'] = render_to_string(template_set['html'], context)

                    # Send email
                    send_mail(email_subject, email_content, [recipient.email], connection=open_connection, **kwargs)
                    sent_count += 1
                except Exception:
                    logger.exception(
                        "Failed to send notification email '%s' to %s",
                        email_subject, recipient.email
                    )

        return sent_count == len(recipients)

    def send_notifications(self, template_set, context, recipients, **kwargs):
        return self.send_emails(template_set, context, recipients, **kwargs)


class BaseWorkflowStateEmailNotifier(EmailNotifier):
    """A base EmailNotifier to send updates for WorkflowState events"""

    def __init__(self):
        super().__init__((WorkflowState,))

    def get_context(self, workflow_state, **kwargs):
        context = super().get_context(workflow_state, **kwargs)
        context['page'] = workflow_state.page
        context['workflow'] = workflow_state.workflow
        return context


class WorkflowStateApprovalEmailNotifier(BaseWorkflowStateEmailNotifier):
    """An EmailNotifier to send updates for WorkflowState approval events"""

    notification = 'approved'

    def get_recipient_users(self, workflow_state, **kwargs):
        triggering_user = kwargs.get('user', None)
        recipients = {}
        requested_by = workflow_state.requested_by
        if requested_by != triggering_user:
            recipients = {requested_by}

        return recipients


class WorkflowStateRejectionEmailNotifier(BaseWorkflowStateEmailNotifier):
    """An EmailNotifier to send updates for WorkflowState rejection events"""

    notification = 'rejected'

    def get_recipient_users(self, workflow_state, **kwargs):
        triggering_user = kwargs.get('user', None)
        recipients = {}
        requested_by = workflow_state.requested_by
        if requested_by != triggering_user:
            recipients = {requested_by}

        return recipients


class WorkflowStateSubmissionEmailNotifier(BaseWorkflowStateEmailNotifier):
    """An EmailNotifier to send updates for WorkflowState submission events"""

    notification = 'submitted'

    def get_recipient_users(self, workflow_state, **kwargs):
        triggering_user = kwargs.get('user', None)
        recipients = {}
        include_superusers = getattr(settings, 'WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS', True)
        if include_superusers:
            recipients = get_user_model().objects.filter(is_superuser=True)
            if triggering_user:
                recipients.exclude(pk=triggering_user.pk)

        return recipients


class BaseGroupApprovalTaskStateEmailNotifier(EmailNotifier):
    """A base EmailNotifier to send updates for GroupApprovalTask events"""

    def __init__(self):
        super().__init__((TaskState,))

    def can_handle(self, instance, **kwargs):
        if super().can_handle(instance, **kwargs) and isinstance(instance.task.specific, GroupApprovalTask):
            # Don't send notifications if a Task has been cancelled and then resumed - ie page was updated to a new revision
            return not TaskState.objects.filter(workflow_state=instance.workflow_state, task=instance.task, status=TaskState.STATUS_CANCELLED).exists()
        return False

    def get_context(self, task_state, **kwargs):
        context = super().get_context(task_state, **kwargs)
        context['page'] = task_state.workflow_state.page
        context['task'] = task_state.task.specific
        return context

    def get_recipient_users(self, task_state, **kwargs):
        triggering_user = kwargs.get('user', None)
        group_members = task_state.task.specific.group.user_set.all()

        recipients = group_members

        include_superusers = getattr(settings, 'WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS', True)
        if include_superusers:
            superusers = get_user_model().objects.filter(is_superuser=True)
            recipients = recipients | superusers

        if triggering_user:
            recipients = recipients.exclude(pk=triggering_user.pk)

        return recipients


class GroupApprovalTaskStateSubmissionEmailNotifier(BaseGroupApprovalTaskStateEmailNotifier):
    """An EmailNotifier to send updates for GroupApprovalTask submission events"""

    notification = 'submitted'


class GroupApprovalTaskStateApprovalEmailNotifier(BaseGroupApprovalTaskStateEmailNotifier):
    """An EmailNotifier to send updates for GroupApprovalTask approval events"""

    notification = 'approved'

    def get_recipient_users(self, task_state, **kwargs):
        recipients = super().get_recipient_users(task_state, **kwargs)
        requested_by = task_state.workflow_state.requested_by
        # add the EmailNotifier's requester
        triggering_user = kwargs.get('user', None)
        if  (not triggering_user or triggering_user.pk != requested_by.pk):
            recipients = set(recipients)
            recipients.add(requested_by)

        return recipients


class GroupApprovalTaskStateRejectionEmailNotifier(BaseGroupApprovalTaskStateEmailNotifier):
    """An EmailNotifier to send updates for GroupApprovalTask rejection events"""

    notification = 'rejected'

    def get_recipient_users(self, task_state, **kwargs):
        recipients = super().get_recipient_users(task_state, **kwargs)
        requested_by = task_state.workflow_state.requested_by
        # add the EmailNotifier's requester
        triggering_user = kwargs.get('user', None)
        if  (not triggering_user or triggering_user.pk != requested_by.pk):
            recipients = set(recipients)
            recipients.add(requested_by)

        return recipients
