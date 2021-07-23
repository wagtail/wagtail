"""
Base model definitions for audit logging. These may be subclassed to accommodate specific models
such as Page, but the definitions here should remain generic and not depend on the base
wagtail.core.models module or specific models such as Page.
"""

import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _


class LogEntryQuerySet(models.QuerySet):
    def get_users(self):
        """
        Returns a QuerySet of Users who have created at least one log entry in this QuerySet.

        The returned queryset is ordered by the username.
        """
        User = get_user_model()
        return User.objects.filter(
            pk__in=set(self.values_list('user__pk', flat=True))
        ).order_by(User.USERNAME_FIELD)


class BaseLogEntryManager(models.Manager):
    def get_queryset(self):
        return LogEntryQuerySet(self.model, using=self._db)

    def get_instance_title(self, instance):
        return str(instance)

    def log_action(self, instance, action, **kwargs):
        """
        :param instance: The model instance we are logging an action for
        :param action: The action. Should be namespaced to app (e.g. wagtail.create, wagtail.workflow.start)
        :param kwargs: Addition fields to for the model deriving from BaseLogEntry
            - user: The user performing the action
            - title: the instance title
            - data: any additional metadata
            - content_changed, deleted - Boolean flags
        :return: The new log entry
        """
        data = kwargs.pop('data', '')
        title = kwargs.pop('title', None)
        if not title:
            title = self.get_instance_title(instance)

        timestamp = kwargs.pop('timestamp', timezone.now())
        return self.model.objects.create(
            content_type=ContentType.objects.get_for_model(instance, for_concrete_model=False),
            label=title,
            action=action,
            timestamp=timestamp,
            data_json=json.dumps(data),
            **kwargs,
        )

    def get_for_model(self, model):
        # Return empty queryset if the given object is not valid.
        if not issubclass(model, models.Model):
            return self.none()

        ct = ContentType.objects.get_for_model(model)

        return self.filter(content_type=ct)

    def get_for_user(self, user_id):
        return self.filter(user=user_id)


class BaseLogEntry(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        models.SET_NULL,
        verbose_name=_('content type'),
        blank=True, null=True,
        related_name='+',
    )
    label = models.TextField()

    action = models.CharField(max_length=255, blank=True, db_index=True)
    data_json = models.TextField(blank=True)
    timestamp = models.DateTimeField(verbose_name=_('timestamp (UTC)'))

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,  # Null if actioned by system
        blank=True,
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        related_name='+',
    )

    # Flags for additional context to the 'action' made by the user (or system).
    content_changed = models.BooleanField(default=False, db_index=True)
    deleted = models.BooleanField(default=False)

    objects = BaseLogEntryManager()

    action_registry = None

    class Meta:
        abstract = True
        verbose_name = _('log entry')
        verbose_name_plural = _('log entries')
        ordering = ['-timestamp']

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def clean(self):
        self.action_registry.scan_for_actions()

        if self.action not in self.action_registry.actions:
            raise ValidationError({'action': _("The log action '{}' has not been registered.").format(self.action)})

    def __str__(self):
        return "LogEntry %d: '%s' on '%s'" % (
            self.pk, self.action, self.object_verbose_name()
        )

    @cached_property
    def user_display_name(self):
        """
        Returns the display name of the associated user;
        get_full_name if available and non-empty, otherwise get_username.
        Defaults to 'system' when none is provided
        """
        if self.user_id:
            try:
                user = self.user
            except self._meta.get_field('user').related_model.DoesNotExist:
                # User has been deleted
                return _('user %(id)d (deleted)') % {'id': self.user_id}

            try:
                full_name = user.get_full_name().strip()
            except AttributeError:
                full_name = ''
            return full_name or user.get_username()

        else:
            return _('system')

    @cached_property
    def data(self):
        """
        Provides deserialized data
        """
        if self.data_json:
            return json.loads(self.data_json)
        else:
            return {}

    @cached_property
    def object_verbose_name(self):
        model_class = self.content_type.model_class()
        if model_class is None:
            return self.content_type_id

        return model_class._meta.verbose_name.title

    def object_id(self):
        raise NotImplementedError

    def format_message(self):
        return self.action_registry.format_message(self)

    def format_comment(self):
        return self.action_registry.format_comment(self)

    @property
    def comment(self):
        return self.format_comment()
