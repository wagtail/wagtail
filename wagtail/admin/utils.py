# -*- coding: utf-8 -*-
import logging
from functools import wraps
import pytz

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.mail import get_connection
from django.core.mail.message import EmailMultiAlternatives
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.utils.translation import override, ugettext_lazy
from modelcluster.fields import ParentalKey
from taggit.models import Tag

from wagtail.core.models import GroupPagePermission, Page, PageRevision
from wagtail.users.models import UserProfile

logger = logging.getLogger('wagtail.admin')

# Wagtail languages with >=90% coverage
# This list is manually maintained
WAGTAILADMIN_PROVIDED_LANGUAGES = [
    ('ar', ugettext_lazy('Arabic')),
    ('ca', ugettext_lazy('Catalan')),
    ('de', ugettext_lazy('German')),
    ('el', ugettext_lazy('Greek')),
    ('en', ugettext_lazy('English')),
    ('es', ugettext_lazy('Spanish')),
    ('fi', ugettext_lazy('Finnish')),
    ('fr', ugettext_lazy('French')),
    ('gl', ugettext_lazy('Galician')),
    ('id-id', ugettext_lazy('Indonesian')),
    ('is-is', ugettext_lazy('Icelandic')),
    ('it', ugettext_lazy('Italian')),
    ('ko', ugettext_lazy('Korean')),
    ('lt', ugettext_lazy('Lithuanian')),
    ('mn', ugettext_lazy('Mongolian')),
    ('nb', ugettext_lazy('Norwegian Bokmål')),
    ('nl-nl', ugettext_lazy('Netherlands Dutch')),
    ('fa', ugettext_lazy('Persian')),
    ('pl', ugettext_lazy('Polish')),
    ('pt-br', ugettext_lazy('Brazilian Portuguese')),
    ('pt-pt', ugettext_lazy('Portuguese')),
    ('ro', ugettext_lazy('Romanian')),
    ('ru', ugettext_lazy('Russian')),
    ('sv', ugettext_lazy('Swedish')),
    ('sk-sk', ugettext_lazy('Slovak')),
    ('th', ugettext_lazy('Thai')),
    ('uk', ugettext_lazy('Ukrainian')),
    ('zh-hans', ugettext_lazy('Chinese (Simplified)')),
    ('zh-hant', ugettext_lazy('Chinese (Traditional)')),
]


def get_available_admin_languages():
    return getattr(settings, 'WAGTAILADMIN_PERMITTED_LANGUAGES', WAGTAILADMIN_PROVIDED_LANGUAGES)


def get_available_admin_time_zones():
    return getattr(settings, 'WAGTAIL_USER_TIME_ZONES', pytz.common_timezones)


def get_object_usage(obj):
    "Returns a queryset of pages that link to a particular object"

    pages = Page.objects.none()

    # get all the relation objects for obj
    relations = [f for f in type(obj)._meta.get_fields(include_hidden=True)
                 if (f.one_to_many or f.one_to_one) and f.auto_created]
    for relation in relations:
        related_model = relation.related_model

        # if the relation is between obj and a page, get the page
        if issubclass(related_model, Page):
            pages |= Page.objects.filter(
                id__in=related_model._base_manager.filter(**{
                    relation.field.name: obj.id
                }).values_list('id', flat=True)
            )
        else:
            # if the relation is between obj and an object that has a page as a
            # property, return the page
            for f in related_model._meta.fields:
                if isinstance(f, ParentalKey) and issubclass(f.remote_field.model, Page):
                    pages |= Page.objects.filter(
                        id__in=related_model._base_manager.filter(
                            **{
                                relation.field.name: obj.id
                            }).values_list(f.attname, flat=True)
                    )

    return pages


def popular_tags_for_model(model, count=10):
    """Return a queryset of the most frequently used tags used on this model class"""
    content_type = ContentType.objects.get_for_model(model)
    return Tag.objects.filter(
        taggit_taggeditem_items__content_type=content_type
    ).annotate(
        item_count=Count('taggit_taggeditem_items')
    ).order_by('-item_count')[:count]


def users_with_page_permission(page, permission_type, include_superusers=True):
    # Get user model
    User = get_user_model()

    # Find GroupPagePermission records of the given type that apply to this page or an ancestor
    ancestors_and_self = list(page.get_ancestors()) + [page]
    perm = GroupPagePermission.objects.filter(permission_type=permission_type, page__in=ancestors_and_self)
    q = Q(groups__page_permissions__in=perm)

    # Include superusers
    if include_superusers:
        q |= Q(is_superuser=True)

    return User.objects.filter(is_active=True).filter(q).distinct()


def permission_denied(request):
    """Return a standard 'permission denied' response"""
    if request.is_ajax():
        raise PermissionDenied

    from wagtail.admin import messages

    messages.error(request, _('Sorry, you do not have permission to access this area.'))
    return redirect('wagtailadmin_home')


def user_passes_test(test):
    """
    Given a test function that takes a user object and returns a boolean,
    return a view decorator that denies access to the user if the test returns false.
    """
    def decorator(view_func):
        # decorator takes the view function, and returns the view wrapped in
        # a permission check

        @wraps(view_func)
        def wrapped_view_func(request, *args, **kwargs):
            if test(request.user):
                # permission check succeeds; run the view function as normal
                return view_func(request, *args, **kwargs)
            else:
                # permission check failed
                return permission_denied(request)

        return wrapped_view_func

    return decorator


def permission_required(permission_name):
    """
    Replacement for django.contrib.auth.decorators.permission_required which returns a
    more meaningful 'permission denied' response than just redirecting to the login page.
    (The latter doesn't work anyway because Wagtail doesn't define LOGIN_URL...)
    """
    def test(user):
        return user.has_perm(permission_name)

    # user_passes_test constructs a decorator function specific to the above test function
    return user_passes_test(test)


def any_permission_required(*perms):
    """
    Decorator that accepts a list of permission names, and allows the user
    to pass if they have *any* of the permissions in the list
    """
    def test(user):
        for perm in perms:
            if user.has_perm(perm):
                return True

        return False

    return user_passes_test(test)


class PermissionPolicyChecker:
    """
    Provides a view decorator that enforces the given permission policy,
    returning the wagtailadmin 'permission denied' response if permission not granted
    """
    def __init__(self, policy):
        self.policy = policy

    def require(self, action):
        def test(user):
            return self.policy.user_has_permission(user, action)

        return user_passes_test(test)

    def require_any(self, *actions):
        def test(user):
            return self.policy.user_has_any_permission(user, actions)

        return user_passes_test(test)


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


def user_has_any_page_permission(user):
    """
    Check if a user has any permission to add, edit, or otherwise manage any
    page.
    """
    # Can't do nothin if you're not active.
    if not user.is_active:
        return False

    # Superusers can do anything.
    if user.is_superuser:
        return True

    # At least one of the users groups has a GroupPagePermission.
    # The user can probably do something.
    if GroupPagePermission.objects.filter(group__in=user.groups.all()).exists():
        return True

    # Specific permissions for a page type do not mean anything.

    # No luck! This user can not do anything with pages.
    return False
