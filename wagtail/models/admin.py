import os
import uuid

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Count, Model
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from taggit.models import Tag


def upload_avatar_to(instance, filename):
    filename, ext = os.path.splitext(filename)
    return os.path.join(
        'avatar_images',
        'avatar_{uuid}_{filename}{ext}'.format(
            uuid=uuid.uuid4(), filename=filename, ext=ext)
    )


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wagtail_userprofile'
    )

    submitted_notifications = models.BooleanField(
        verbose_name=_('submitted notifications'),
        default=True,
        help_text=_("Receive notification when a page is submitted for moderation")
    )

    approved_notifications = models.BooleanField(
        verbose_name=_('approved notifications'),
        default=True,
        help_text=_("Receive notification when your page edit is approved")
    )

    rejected_notifications = models.BooleanField(
        verbose_name=_('rejected notifications'),
        default=True,
        help_text=_("Receive notification when your page edit is rejected")
    )

    updated_comments_notifications = models.BooleanField(
        verbose_name=_('updated comments notifications'),
        default=True,
        help_text=_("Receive notification when comments have been created, resolved, or deleted on a page that you have subscribed to receive comment notifications on")
    )

    preferred_language = models.CharField(
        verbose_name=_('preferred language'),
        max_length=10,
        help_text=_("Select language for the admin"),
        default=''
    )

    current_time_zone = models.CharField(
        verbose_name=_('current time zone'),
        max_length=40,
        help_text=_("Select your current time zone"),
        default=''
    )

    avatar = models.ImageField(
        verbose_name=_('profile picture'),
        upload_to=upload_avatar_to,
        blank=True,
    )

    @classmethod
    def get_for_user(cls, user):
        return cls.objects.get_or_create(user=user)[0]

    def get_preferred_language(self):
        return self.preferred_language or get_language()

    def get_current_time_zone(self):
        return self.current_time_zone or settings.TIME_ZONE

    def __str__(self):
        return self.user.get_username()

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')


# A dummy model that exists purely to attach the access_admin permission type to, so that it
# doesn't get identified as a stale content type and removed by the remove_stale_contenttypes
# management command.
class Admin(Model):
    class Meta:
        default_permissions = []  # don't create the default add / change / delete / view perms
        permissions = [
            ('access_admin', "Can access Wagtail admin"),
        ]


def get_object_usage(obj):
    """Returns a queryset of pages that link to a particular object"""
    from wagtail.models import Page

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
