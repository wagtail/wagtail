import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import get_connection
from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import override

from wagtail.coreutils import camelcase_to_underscore
from wagtail.models import AbstractGroupApprovalTask, Page, TaskState, WorkflowState
from wagtail.users.models import UserProfile

logger = logging.getLogger("wagtail.admin")


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
        if hasattr(settings, "WAGTAILADMIN_NOTIFICATION_FROM_EMAIL"):
            from_email = settings.WAGTAILADMIN_NOTIFICATION_FROM_EMAIL
        elif hasattr(settings, "DEFAULT_FROM_EMAIL"):
            from_email = settings.DEFAULT_FROM_EMAIL
        else:
            # We are no longer using the term `webmaster` except in this case, where we continue to match Django's default: https://github.com/django/django/blob/stable/3.2.x/django/conf/global_settings.py#L223
            from_email = "webmaster@localhost"

    connection = kwargs.get("connection", False) or get_connection(
        username=kwargs.get("auth_user", None),
        password=kwargs.get("auth_password", None),
        fail_silently=kwargs.get("fail_silently", None),
    )
    multi_alt_kwargs = {
        "connection": connection,
        "headers": {
            "Auto-Submitted": "auto-generated",
        },
        "bcc": kwargs.get("bcc", None),
        "cc": kwargs.get("cc", None),
        "reply_to": kwargs.get("reply_to", None),
    }
    mail = EmailMultiAlternatives(
        subject, message, from_email, recipient_list, **multi_alt_kwargs
    )
    html_message = kwargs.get("html_message", None)
    if html_message:
        mail.attach_alternative(html_message, "text/html")

    return mail.send()


def send_notification(recipient_users, notification, extra_context):
    # Get list of email addresses
    email_recipients = [
        recipient
        for recipient in recipient_users
        if recipient.is_active
        and recipient.email
        and getattr(
            UserProfile.get_for_user(recipient), notification + "_notifications"
        )
    ]

    # Return if there are no email addresses
    if not email_recipients:
        return True

    # Get template
    template_subject = "wagtailadmin/notifications/" + notification + "_subject.txt"
    template_text = "wagtailadmin/notifications/" + notification + ".txt"
    template_html = "wagtailadmin/notifications/" + notification + ".html"

    # Common context to template
    context = {
        "settings": settings,
    }
    context.update(extra_context)

    connection = get_connection()

    with OpenedConnection(connection) as open_connection:
        # Send emails
        sent_count = 0
        for recipient in email_recipients:
            # update context with this recipient
            context["user"] = recipient

            # Translate text to the recipient language settings
            with override(recipient.wagtail_userprofile.get_preferred_language()):
                # Get email subject and content
                email_subject = render_to_string(template_subject, context).strip()
                email_content = render_to_string(template_text, context).strip()

            kwargs = {}
            if getattr(settings, "WAGTAILADMIN_NOTIFICATION_USE_HTML", False):
                kwargs["html_message"] = render_to_string(template_html, context)

            try:
                # Send email
                send_mail(
                    email_subject,
                    email_content,
                    [recipient.email],
                    connection=open_connection,
                    **kwargs,
                )
                sent_count += 1
            except Exception:
                logger.exception(
                    "Failed to send notification email '%s' to %s",
                    email_subject,
                    recipient.email,
                )

    return sent_count == len(email_recipients)


class Notifier:
    """Generic class for sending event notifications: callable, intended to be connected to a signal to send
    notifications using rendered templates."""

    notification = ""
    template_directory = "wagtailadmin/notifications/"

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
        return camelcase_to_underscore(type(instance).__name__) + "_"

    def get_context(self, instance, **kwargs):
        return {"settings": settings}

    def get_template_set(self, instance, **kwargs):
        """Return a dictionary of template paths for the templates: by default, a text message"""
        template_base = self.get_template_base_prefix(instance) + self.notification

        template_text = self.template_directory + template_base + ".txt"

        return {
            "text": template_text,
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


class EmailNotificationMixin:
    """Mixin for sending email notifications upon events"""

    def get_recipient_users(self, instance, **kwargs):
        """Gets the ideal set of recipient users, without accounting for notification preferences or missing email addresses"""

        return set()

    def get_valid_recipients(self, instance, **kwargs):
        """Filters notification recipients to those allowing the notification type on their UserProfile, and those
        with an email address"""
        return {
            recipient
            for recipient in self.get_recipient_users(instance, **kwargs)
            if recipient
            and recipient.is_active
            and recipient.email
            and getattr(
                UserProfile.get_for_user(recipient),
                self.notification + "_notifications",
            )
        }

    def get_template_set(self, instance, **kwargs):
        """Return a dictionary of template paths for the templates for the email subject and the text and html
        alternatives"""
        template_base = self.get_template_base_prefix(instance) + self.notification

        template_subject = self.template_directory + template_base + "_subject.txt"
        template_text = self.template_directory + template_base + ".txt"
        template_html = self.template_directory + template_base + ".html"

        return {
            "subject": template_subject,
            "text": template_text,
            "html": template_html,
        }

    def send_emails(self, template_set, context, recipients, **kwargs):
        connection = get_connection()
        sent_count = 0
        try:
            with OpenedConnection(connection) as open_connection:
                # Send emails
                for recipient in recipients:
                    # update context with this recipient
                    context["user"] = recipient

                    # Translate text to the recipient language settings
                    with override(
                        recipient.wagtail_userprofile.get_preferred_language()
                    ):
                        # Get email subject and content
                        email_subject = render_to_string(
                            template_set["subject"], context
                        ).strip()
                        email_content = render_to_string(
                            template_set["text"], context
                        ).strip()

                    kwargs = {}
                    if getattr(settings, "WAGTAILADMIN_NOTIFICATION_USE_HTML", False):
                        kwargs["html_message"] = render_to_string(
                            template_set["html"], context
                        )

                    try:
                        # Send email
                        send_mail(
                            email_subject,
                            email_content,
                            [recipient.email],
                            connection=open_connection,
                            **kwargs,
                        )
                        sent_count += 1
                    except Exception:
                        logger.exception(
                            "Failed to send notification email '%s' to %s",
                            email_subject,
                            recipient.email,
                        )
        except (TimeoutError, ConnectionError):
            logger.exception("Mail connection error, notification sending skipped")

        return sent_count == len(recipients)

    def send_notifications(self, template_set, context, recipients, **kwargs):
        return self.send_emails(template_set, context, recipients, **kwargs)


class BaseWorkflowStateEmailNotifier(EmailNotificationMixin, Notifier):
    """A base notifier to send email updates for WorkflowState events"""

    def __init__(self):
        super().__init__((WorkflowState,))

    def get_context(self, workflow_state: WorkflowState, **kwargs):
        context = super().get_context(workflow_state, **kwargs)
        context["workflow"] = workflow_state.workflow
        context["object"] = workflow_state.content_object
        context["model_name"] = context["object"]._meta.verbose_name
        if isinstance(context["object"], Page):
            context["page"] = context["object"].specific
        return context


class WorkflowStateApprovalEmailNotifier(BaseWorkflowStateEmailNotifier):
    """A notifier to send email updates for WorkflowState approval events"""

    notification = "approved"

    def get_recipient_users(self, workflow_state: WorkflowState, **kwargs):
        triggering_user = kwargs.get("user", None)
        recipients = set()
        requested_by = workflow_state.requested_by
        if requested_by is not None and requested_by != triggering_user:
            recipients = {requested_by}

        return recipients


class WorkflowStateRejectionEmailNotifier(BaseWorkflowStateEmailNotifier):
    """A notifier to send email updates for WorkflowState rejection events"""

    notification = "rejected"

    def get_recipient_users(self, workflow_state: WorkflowState, **kwargs):
        triggering_user = kwargs.get("user", None)
        recipients = set()
        requested_by = workflow_state.requested_by
        if requested_by is not None and requested_by != triggering_user:
            recipients = {requested_by}

        return recipients

    def get_context(self, workflow_state, **kwargs):
        context = super().get_context(workflow_state, **kwargs)
        task_state = workflow_state.current_task_state.specific
        context["task"] = task_state.task
        context["task_state"] = task_state
        context["comment"] = task_state.get_comment()
        return context


class WorkflowStateSubmissionEmailNotifier(BaseWorkflowStateEmailNotifier):
    """A notifier to send email updates for WorkflowState submission events"""

    notification = "submitted"

    def get_recipient_users(self, workflow_state: WorkflowState, **kwargs):
        triggering_user = kwargs.get("user", None)
        recipients = get_user_model().objects.none()
        include_superusers = getattr(
            settings, "WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS", True
        )
        if include_superusers:
            recipients = get_user_model().objects.filter(is_superuser=True)
        if triggering_user:
            recipients.exclude(pk=triggering_user.pk)

        return recipients

    def get_context(self, workflow_state, **kwargs):
        context = super().get_context(workflow_state, **kwargs)
        context["requested_by"] = workflow_state.requested_by
        return context


class BaseGroupApprovalTaskStateEmailNotifier(EmailNotificationMixin, Notifier):
    """A base notifier to send email updates for GroupApprovalTask events"""

    def __init__(self):
        super().__init__((TaskState,))

    def can_handle(self, instance, **kwargs):
        if super().can_handle(instance, **kwargs) and isinstance(
            instance.task.specific, AbstractGroupApprovalTask
        ):
            return True
        return False

    def get_context(self, task_state, **kwargs):
        context = super().get_context(task_state, **kwargs)
        context["task"] = task_state.task.specific
        context["object"] = task_state.workflow_state.content_object
        context["model_name"] = context["object"]._meta.verbose_name
        if isinstance(context["object"], Page):
            context["page"] = context["object"].specific
        return context

    def get_recipient_users(self, task_state: TaskState, **kwargs):
        triggering_user = kwargs.get("user", None)

        group_members = get_user_model().objects.filter(
            groups__in=task_state.task.specific.groups.all()
        )

        recipients = group_members

        include_superusers = getattr(
            settings, "WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS", True
        )
        if include_superusers:
            superusers = get_user_model().objects.filter(is_superuser=True)
            recipients = recipients | superusers

        if triggering_user:
            recipients = recipients.exclude(pk=triggering_user.pk)

        return recipients


class GroupApprovalTaskStateSubmissionEmailNotifier(
    BaseGroupApprovalTaskStateEmailNotifier
):
    """A notifier to send email updates for GroupApprovalTask submission events"""

    notification = "submitted"
