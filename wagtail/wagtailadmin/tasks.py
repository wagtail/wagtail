from celery.decorators import task

from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q

from wagtail.wagtailcore.models import PageRevision, GroupPagePermission


def users_with_page_permission(page, permission_type, include_superusers=True):
    # Get user model
    User = get_user_model()

    # Find GroupPagePermission records of the given type that apply to this page or an ancestor
    ancestors_and_self = list(page.get_ancestors()) + [page]
    perm = GroupPagePermission.objects.filter(permission_type=permission_type, page__in=ancestors_and_self)
    q = Q(groups__page_permissions=perm)

    # Include superusers
    if include_superusers:
        q |= Q(is_superuser=True)

    return User.objects.filter(q).distinct()


@task()
def send_notification(page_revision_id, notification, excluded_user_id):
    # Get revision
    revision = PageRevision.objects.get(id=page_revision_id)

    # Get list of recipients
    if notification == 'submitted':
        # Get list of publishers
        recipients = users_with_page_permission(revision.page, 'publish')
    elif notification == 'approved' or notification == 'rejected':
        # Get submitter
        recipients = [revision.user]
    else:
        return

    # Get list of email addresses
    email_addresses = [
        recipient.email for recipient in recipients
        if recipient.email and recipient.id != excluded_user_id
    ]

    # Return if there are no email addresses
    if not email_addresses:
        return

    # Get email subject and content
    template = 'wagtailadmin/notifications/' + notification + '.html'
    rendered_template = render_to_string(template, dict(revision=revision, settings=settings)).split('\n')
    email_subject = rendered_template[0]
    email_content = '\n'.join(rendered_template[1:])

    # Get from email
    if hasattr(settings, 'WAGTAILADMIN_NOTIFICATION_FROM_EMAIL'):
        from_email = settings.WAGTAILADMIN_NOTIFICATION_FROM_EMAIL
    elif hasattr(settings, 'DEFAULT_FROM_EMAIL'):
        from_email = settings.DEFAULT_FROM_EMAIL
    else:
        from_email = 'webmaster@localhost'

    # Send email
    send_mail(email_subject, email_content, from_email, email_addresses)
