# -*- coding: utf-8 -*-
import logging
import sys

from django.conf import settings
from django.core.mail import get_connection
from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import override

from wagtail.admin.auth import users_with_page_permission
from wagtail.admin.navigation import get_explorable_root_page
from wagtail.core.models import PageRevision
from wagtail.users.models import UserProfile
from wagtail.utils.deprecation import MovedDefinitionHandler, RemovedInWagtail29Warning

logger = logging.getLogger('wagtail.admin')


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
            send_mail(email_subject, email_content, [recipient.email], **kwargs)
            sent_count += 1
        except Exception:
            logger.exception(
                "Failed to send notification email '%s' to %s",
                email_subject, recipient.email
            )

    return sent_count == len(email_recipients)


def get_site_for_user(user):
    root_page = get_explorable_root_page(user)
    if root_page:
        root_site = root_page.get_site()
    else:
        root_site = None
    real_site_name = None
    if root_site:
        real_site_name = root_site.site_name if root_site.site_name else root_site.hostname
    return {
        'root_page': root_page,
        'root_site': root_site,
        'site_name': real_site_name if real_site_name else settings.WAGTAIL_SITE_NAME,
    }


MOVED_DEFINITIONS = {
    'WAGTAILADMIN_PROVIDED_LANGUAGES': 'wagtail.admin.locale',
    'get_js_translation_strings': 'wagtail.admin.locale',
    'get_available_admin_languages': 'wagtail.admin.locale',
    'get_available_admin_time_zones': 'wagtail.admin.locale',

    'get_object_usage': 'wagtail.admin.models',
    'popular_tags_for_model': 'wagtail.admin.models',

    'users_with_page_permission': 'wagtail.admin.auth',
    'permission_denied': 'wagtail.admin.auth',
    'user_passes_test': 'wagtail.admin.auth',
    'permission_required': 'wagtail.admin.auth',
    'any_permission_required': 'wagtail.admin.auth',
    'PermissionPolicyChecker': 'wagtail.admin.auth',
    'user_has_any_page_permission': 'wagtail.admin.auth',
}

sys.modules[__name__] = MovedDefinitionHandler(sys.modules[__name__], MOVED_DEFINITIONS, RemovedInWagtail29Warning)
