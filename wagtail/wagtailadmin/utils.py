from django.template.loader import render_to_string
from django.core.mail import send_mail as django_send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import redirect
from django.utils.translation import ugettext as _

from modelcluster.fields import ParentalKey

from wagtail.wagtailcore.models import Page, PageRevision, GroupPagePermission
from wagtail.wagtailusers.models import UserProfile
from wagtail.utils.compat import get_related_model


def get_object_usage(obj):
    "Returns a queryset of pages that link to a particular object"

    pages = Page.objects.none()

    # get all the relation objects for obj
    relations = type(obj)._meta.get_all_related_objects(
        include_hidden=True,
        include_proxy_eq=True
    )
    for relation in relations:
        related_model = get_related_model(relation)

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
    q = Q(groups__page_permissions=perm)

    # Include superusers
    if include_superusers:
        q |= Q(is_superuser=True)

    return User.objects.filter(is_active=True).filter(q).distinct()


def any_permission_required(*perms):
    """
    Decorator that accepts a list of permission names, and allows the user
    to pass if they have *any* of the permissions in the list
    """
    from wagtail.wagtailadmin import messages

    # Construct and return a decorator function specific to the permission list
    # that has been passed in
    def decorator(view_func):
        # decorator takes the view function, and returns the view wrapped in
        # a permission check

        def wrapped_view_func(request, *args, **kwargs):
            for perm in perms:
                if request.user.has_perm(perm):
                    # permission check succeeds; run the view function as normal
                    return view_func(request, *args, **kwargs)

            # if we get here, none of the permission checks have passed
            messages.error(request, _('Sorry, you do not have permission to access this area.'))
            return redirect('wagtailadmin_home')

        return wrapped_view_func

    return decorator


def send_mail(email_subject, email_content, email_addresses, from_email=None):
    if not from_email:
        if hasattr(settings, 'WAGTAILADMIN_NOTIFICATION_FROM_EMAIL'):
            from_email = settings.WAGTAILADMIN_NOTIFICATION_FROM_EMAIL
        elif hasattr(settings, 'DEFAULT_FROM_EMAIL'):
            from_email = settings.DEFAULT_FROM_EMAIL
        else:
            from_email = 'webmaster@localhost'

    django_send_mail(email_subject, email_content, from_email, email_addresses)


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
        return

    # Get list of email addresses
    email_addresses = [
        recipient.email for recipient in recipients
        if recipient.email and recipient.id != excluded_user_id and getattr(UserProfile.get_for_user(recipient), notification + '_notifications')
    ]

    # Return if there are no email addresses
    if not email_addresses:
        return

    # Get email subject and content
    template = 'wagtailadmin/notifications/' + notification + '.html'
    rendered_template = render_to_string(template, dict(revision=revision, settings=settings)).split('\n')
    email_subject = rendered_template[0]
    email_content = '\n'.join(rendered_template[1:])

    # Send email
    send_mail(email_subject, email_content, email_addresses)
