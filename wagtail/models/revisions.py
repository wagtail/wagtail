from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Q
from django.db.models.expressions import OuterRef, Subquery
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.log_actions import log
from wagtail.utils.timestamps import ensure_utc

from .content_types import get_default_page_content_type


class RevisionQuerySet(models.QuerySet):
    def page_revisions_q(self):
        return Q(base_content_type=get_default_page_content_type())

    def page_revisions(self):
        return self.filter(self.page_revisions_q())

    def not_page_revisions(self):
        return self.exclude(self.page_revisions_q())

    def for_instance(self, instance):
        try:
            # Use RevisionMixin.get_base_content_type() if available
            return self.filter(
                base_content_type=instance.get_base_content_type(),
                object_id=str(instance.pk),
            )
        except AttributeError:
            # Fallback to ContentType for the model
            return self.filter(
                content_type=ContentType.objects.get_for_model(
                    instance, for_concrete_model=False
                ),
                object_id=str(instance.pk),
            )


class RevisionsManager(models.Manager.from_queryset(RevisionQuerySet)):
    def previous_revision_id_subquery(self, revision_fk_name="revision"):
        """
        Returns a Subquery that can be used to annotate a queryset with the ID
        of the previous revision, based on the revision_fk_name field. Useful
        to avoid N+1 queries when generating comparison links between revisions.

        The logic is similar to ``Revision.get_previous().pk``.
        """
        fk = revision_fk_name
        return Subquery(
            Revision.objects.filter(
                base_content_type_id=OuterRef(f"{fk}__base_content_type_id"),
                object_id=OuterRef(f"{fk}__object_id"),
            )
            .filter(
                Q(
                    created_at=OuterRef(f"{fk}__created_at"),
                    pk__lt=OuterRef(f"{fk}__pk"),
                )
                | Q(created_at__lt=OuterRef(f"{fk}__created_at"))
            )
            .order_by("-created_at", "-pk")
            .values_list("pk", flat=True)[:1]
        )


class PageRevisionsManager(RevisionsManager):
    def get_queryset(self):
        return RevisionQuerySet(self.model, using=self._db).page_revisions()


class Revision(models.Model):
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="+"
    )
    base_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="+"
    )
    object_id = models.CharField(
        max_length=255,
        verbose_name=_("object id"),
    )
    created_at = models.DateTimeField(db_index=True, verbose_name=_("created at"))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="wagtail_revisions",
    )
    object_str = models.TextField(default="")
    content = models.JSONField(
        verbose_name=_("content JSON"), encoder=DjangoJSONEncoder
    )
    approved_go_live_at = models.DateTimeField(
        verbose_name=_("approved go live at"), null=True, blank=True, db_index=True
    )

    objects = RevisionsManager()
    page_revisions = PageRevisionsManager()

    content_object = GenericForeignKey(
        "content_type", "object_id", for_concrete_model=False
    )

    wagtail_reference_index_ignore = True

    @cached_property
    def base_content_object(self):
        return self.base_content_type.get_object_for_this_type(pk=self.object_id)

    def save(self, user=None, *args, **kwargs):
        # Set default value for created_at to now
        # We cannot use auto_now_add as that will override
        # any value that is set before saving
        if self.created_at is None:
            self.created_at = timezone.now()

        # Set default value for base_content_type to the content_type.
        # Page revisions should set this to the default Page model's content type,
        # but the distinction may not be necessary for models that do not use inheritance.
        if self.base_content_type_id is None:
            self.base_content_type_id = self.content_type_id

        super().save(*args, **kwargs)

        if (
            self.approved_go_live_at is None
            and "update_fields" in kwargs
            and "approved_go_live_at" in kwargs["update_fields"]
        ):
            # Log scheduled revision publish cancellation
            object = self.as_object()
            # go_live_at = kwargs['update_fields'][]
            log(
                instance=object,
                action="wagtail.schedule.cancel",
                data={
                    "revision": {
                        "id": self.id,
                        "created": ensure_utc(self.created_at),
                        "go_live_at": ensure_utc(object.go_live_at)
                        if object.go_live_at
                        else None,
                        "has_live_version": object.live,
                    }
                },
                user=user,
                revision=self,
            )

    def as_object(self):
        return self.content_object.with_content_json(self.content)

    def is_latest_revision(self):
        if self.id is None:
            # special case: a revision without an ID is presumed to be newly-created and is thus
            # newer than any revision that might exist in the database
            return True

        latest_revision_id = (
            Revision.objects.filter(
                base_content_type_id=self.base_content_type_id,
                object_id=self.object_id,
            )
            .order_by("-created_at", "-id")
            .values_list("id", flat=True)
            .first()
        )
        return latest_revision_id == self.id

    def delete(self):
        # Update revision_created fields for comments that reference the current revision, if applicable.

        try:
            next_revision = self.get_next()
        except Revision.DoesNotExist:
            next_revision = None

        if next_revision:
            # move comments created on this revision to the next revision, as they may well still apply if they're unresolved
            self.created_comments.all().update(revision_created=next_revision)

        return super().delete()

    def publish(
        self,
        user=None,
        changed=True,
        log_action=True,
        previous_revision=None,
        skip_permission_checks=False,
    ):
        return self.content_object.publish(
            self,
            user=user,
            changed=changed,
            log_action=log_action,
            previous_revision=previous_revision,
            skip_permission_checks=skip_permission_checks,
        )

    def get_previous(self):
        return self.get_previous_by_created_at(
            base_content_type_id=self.base_content_type_id,
            object_id=self.object_id,
        )

    def get_next(self):
        return self.get_next_by_created_at(
            base_content_type_id=self.base_content_type_id,
            object_id=self.object_id,
        )

    def __str__(self):
        return '"' + str(self.content_object) + '" at ' + str(self.created_at)

    class Meta:
        verbose_name = _("revision")
        verbose_name_plural = _("revisions")
        indexes = [
            models.Index(
                fields=["content_type", "object_id"],
                name="content_object_idx",
            ),
            models.Index(
                fields=["base_content_type", "object_id"],
                name="base_content_object_idx",
            ),
        ]
