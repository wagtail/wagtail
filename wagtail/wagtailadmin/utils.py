from __future__ import absolute_import, unicode_literals

import logging
from functools import wraps

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail as django_send_mail
from django.db.models import Q
from django.http.response import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from modelcluster.fields import ParentalKey

from wagtail.wagtailcore.models import GroupPagePermission, Page, PageRevision
from wagtail.wagtailusers.models import UserProfile

logger = logging.getLogger('wagtail.admin')


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
                if isinstance(f, ParentalKey) and issubclass(f.rel.to, Page):
                    pages |= Page.objects.filter(
                        id__in=related_model._base_manager.filter(
                            **{
                                relation.field.name: obj.id
                            }).values_list(f.attname, flat=True)
                    )

    return pages


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
    from wagtail.wagtailadmin import messages

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


class PermissionPolicyChecker(object):
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
    if not from_email:
        if hasattr(settings, 'WAGTAILADMIN_NOTIFICATION_FROM_EMAIL'):
            from_email = settings.WAGTAILADMIN_NOTIFICATION_FROM_EMAIL
        elif hasattr(settings, 'DEFAULT_FROM_EMAIL'):
            from_email = settings.DEFAULT_FROM_EMAIL
        else:
            from_email = 'webmaster@localhost'

    return django_send_mail(subject, message, from_email, recipient_list, **kwargs)


def send_notification(page_revision_id, notification, excluded_user_id):
    # Get revision
    revision = PageRevision.objects.get(id=page_revision_id)

    # Get list of recipients
    if notification == 'submitted':
        # Get list of publishers
        recipients = users_with_page_permission(revision.page, 'publish')
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


def get_page_if_explorable(page_id, request, allow_ancestors=True):
    """
    Returns the Page with the given page_id, if the current user has permission to explore that Page.
    """
    return _get_page_if_permitted(page_id, request, allow_ancestors, choosable=False)


def get_page_if_choosable(page_id, request, allow_ancestors=True):
    """
    Returns the Page with the given page_id, if the current user has permission to choose that Page.
    """
    return _get_page_if_permitted(page_id, request, allow_ancestors, choosable=True)


def _get_page_if_permitted(page_id, request, allow_ancestors, choosable):
    """
    Internal function called by get_page_if_explorable() and get_page_if_choosable(), which does all their work.
    If the Page is not explorable/choosable, an exception will be thrown:
        PermissionDenied if the Page is on the current site
        Http404 if not

    Required ancestors are normally considered explorable/choosable, since Explorer and the Page Chooser need to let
    users traverse through them to get to the Pages they are permitted to act upon or choose.
    If allow_ancestors=False, though, required ancestors will not be considered explorable/choosable.
    This lets Explorer/PageChooser *display* a required ancestor to a user who isn't permitted to act upon or choose it.

    If choosable=True, the Page's permissibility will be evaluated based on whether it's got the "choose" permission,
    rather than whether it's explorable.
    """
    page = get_object_or_404(Page, id=page_id)
    # Superusers can explore and choose every page.
    if request.user.is_superuser:
        return page

    # Other users can only explore/choose their permitted pages.
    page_perms_proxy = page.permissions_for_user(request.user, request)
    if (choosable and page_perms_proxy.can_choose(allow_ancestors)) or page_perms_proxy.can_explore(allow_ancestors):
        return page
    else:
        raise PermissionDenied
