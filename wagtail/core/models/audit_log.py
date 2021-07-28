"""
Base model definitions for audit logging. These may be subclassed to accommodate specific models
such as Page, but the definitions here should remain generic and not depend on the base
wagtail.core.models module or specific models such as Page.
"""

import json

from collections import defaultdict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.core.log_actions import registry as log_action_registry


class LogEntryQuerySet(models.QuerySet):
    def get_user_ids(self):
        """
        Returns a set of user IDs of users who have created at least one log entry in this QuerySet
        """
        return set(self.order_by().values_list('user_id', flat=True).distinct())

    def get_users(self):
        """
        Returns a QuerySet of Users who have created at least one log entry in this QuerySet.

        The returned queryset is ordered by the username.
        """
        User = get_user_model()
        return User.objects.filter(pk__in=self.get_user_ids()).order_by(User.USERNAME_FIELD)

    def get_content_type_ids(self):
        """
        Returns a set of IDs of content types with logged actions in this QuerySet
        """
        return set(self.order_by().values_list('content_type_id', flat=True).distinct())

    def filter_on_content_type(self, content_type):
        # custom method for filtering by content type, to allow overriding on log entry models
        # that have a concept of object types that doesn't correspond directly to ContentType
        # instances (e.g. PageLogEntry, which treats all page types as a single Page type)
        return self.filter(content_type_id=content_type.id)

    def with_instances(self):
        # return an iterable of (log_entry, instance) tuples for all log entries in this queryset.
        # instance is None if the instance does not exist.
        # Note: This is an expensive operation and should only be done on small querysets
        # (e.g. after pagination).

        # evaluate the queryset in full now, as we'll be iterating over it multiple times
        log_entries = list(self)
        ids_by_content_type = defaultdict(list)
        for log_entry in log_entries:
            ids_by_content_type[log_entry.content_type_id].append(log_entry.object_id)

        instances_by_id = {}  # lookup of (content_type_id, stringified_object_id) to instance
        for content_type_id, object_ids in ids_by_content_type.items():
            model = ContentType.objects.get_for_id(content_type_id).model_class()
            model_instances = model.objects.in_bulk(object_ids)
            for object_id, instance in model_instances.items():
                instances_by_id[(content_type_id, str(object_id))] = instance

        for log_entry in log_entries:
            lookup_key = (log_entry.content_type_id, str(log_entry.object_id))
            yield (log_entry, instances_by_id.get(lookup_key))


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
            - uuid: uuid shared between log entries from the same user action
            - title: the instance title
            - data: any additional metadata
            - content_changed, deleted - Boolean flags
        :return: The new log entry
        """
        if instance.pk is None:
            raise ValueError("Attempted to log an action for object %r with empty primary key" % (instance, ))

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

    def viewable_by_user(self, user):
        return self.all()

    def get_for_model(self, model):
        # Return empty queryset if the given object is not valid.
        if not issubclass(model, models.Model):
            return self.none()

        ct = ContentType.objects.get_for_model(model)

        return self.filter(content_type=ct)

    def get_for_user(self, user_id):
        return self.filter(user=user_id)

    def for_instance(self, instance):
        """
        Return a queryset of log entries from this log model that relate to the given object instance
        """
        raise NotImplementedError  # must be implemented by subclass


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
    timestamp = models.DateTimeField(verbose_name=_('timestamp (UTC)'), db_index=True)
    uuid = models.UUIDField(
        blank=True, null=True, editable=False,
        help_text="Log entries that happened as part of the same user action are assigned the same UUID"
    )

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

    class Meta:
        abstract = True
        verbose_name = _('log entry')
        verbose_name_plural = _('log entries')
        ordering = ['-timestamp']

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def clean(self):
        if not log_action_registry.action_exists(self.action):
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
            user = self.user
            if user is None:
                # User has been deleted. Using a string placeholder as the user id could be non-numeric
                return _('user %(id)s (deleted)') % {'id': self.user_id}

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

    @cached_property
    def formatter(self):
        return log_action_registry.get_formatter(self)

    @cached_property
    def message(self):
        if self.formatter:
            return self.formatter.format_message(self)
        else:
            return _('Unknown %(action)s') % {'action': self.action}

    @cached_property
    def comment(self):
        if self.formatter:
            return self.formatter.format_comment(self)
        else:
            return ''


class ModelLogEntryManager(BaseLogEntryManager):
    def log_action(self, instance, action, **kwargs):
        kwargs.update(object_id=str(instance.pk))
        return super().log_action(instance, action, **kwargs)

    def for_instance(self, instance):
        return self.filter(
            content_type=ContentType.objects.get_for_model(instance, for_concrete_model=False),
            object_id=str(instance.pk)
        )


class ModelLogEntry(BaseLogEntry):
    """
    Simple logger for generic Django models
    """
    object_id = models.CharField(max_length=255, blank=False, db_index=True)

    objects = ModelLogEntryManager()

    class Meta:
        ordering = ['-timestamp', '-id']
        verbose_name = _('model log entry')
        verbose_name_plural = _('model log entries')

    def __str__(self):
        return "ModelLogEntry %d: '%s' on '%s' with id %s" % (
            self.pk, self.action, self.object_verbose_name(), self.object_id
        )
