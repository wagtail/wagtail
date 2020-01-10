import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import get_connection
from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.text import get_valid_filename
from django.utils.translation import override

from wagtail.admin.auth import users_with_page_permission
from wagtail.core.models import Page, PageRevision
from wagtail.users.models import UserProfile


logger = logging.getLogger('wagtail.admin')


class OpenedConnection:
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
                send_mail(email_subject, email_content, [recipient.email], connection=open_connection, **kwargs)
                sent_count += 1
            except Exception:
                logger.exception(
                    "Failed to send notification email '%s' to %s",
                    email_subject, recipient.email
                )

    return sent_count == len(email_recipients)


def send_group_approval_task_state_notification(task_state, notification, triggering_user):
    recipients = []
    page = task_state.workflow_state.page
    if notification in ('approved', 'rejected'):
        requested_by = task_state.workflow_state.requested_by
        if requested_by != triggering_user:
            recipients = [triggering_user]
    elif notification == 'submitted':
        recipients = task_state.task.specific.group.user_set
        include_superusers = getattr(settings, 'WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS', True)
        if include_superusers:
            recipients = recipients | get_user_model().objects.filter(is_superuser=True)
            recipients = recipients.exclude(pk=triggering_user.pk).distinct()
    context = {
        "page": page,
        "settings": settings,
        "task": task_state.task,
    }
    send_notification_emails(recipients, notification, context, template_base_prefix='group_approval_task')


def send_notification_emails(recipients, notification, context, template_base_prefix=''):

    # Get list of email addresses
    email_recipients = [
        recipient for recipient in recipients
        if recipient.email and getattr(
            UserProfile.get_for_user(recipient),
            notification + '_notifications'
        )
    ]

    # Return if there are no email addresses
    if not email_recipients:
        return True

    # Get template
    template_base = template_base_prefix + notification

    template_subject = 'wagtailadmin/notifications/' + template_base + '_subject.txt'
    template_text = 'wagtailadmin/notifications/' + template_base + '.txt'
    template_html = 'wagtailadmin/notifications/' + template_base + '.html'

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
                send_mail(email_subject, email_content, [recipient.email], connection=open_connection, **kwargs)
                sent_count += 1
            except Exception:
                logger.exception(
                    "Failed to send notification email '%s' to %s",
                    email_subject, recipient.email
                )

    return sent_count == len(email_recipients)
