from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.db.models.expressions import Subquery
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.models.audit_log import BaseLogEntry, BaseLogEntryManager, LogEntryQuerySet
from wagtail.models.pages import Page, UserPagePermissionsProxy


class PageLogEntryQuerySet(LogEntryQuerySet):
    def get_content_type_ids(self):
        # for reporting purposes, pages of all types are combined under a single "Page"
        # object type
        if self.exists():
            return {ContentType.objects.get_for_model(Page).pk}
        else:
            return set()

    def filter_on_content_type(self, content_type):
        if content_type == ContentType.objects.get_for_model(Page):
            return self
        else:
            return self.none()


class PageLogEntryManager(BaseLogEntryManager):
    def get_queryset(self):
        return PageLogEntryQuerySet(self.model, using=self._db)

    def get_instance_title(self, instance):
        return instance.specific_deferred.get_admin_display_title()

    def log_action(self, instance, action, **kwargs):
        kwargs.update(page=instance)
        return super().log_action(instance, action, **kwargs)

    def viewable_by_user(self, user):
        q = Q(
            page__in=UserPagePermissionsProxy(user)
            .explorable_pages()
            .values_list("pk", flat=True)
        )

        root_page_permissions = Page.get_first_root_node().permissions_for_user(user)
        if (
            user.is_superuser
            or root_page_permissions.can_add_subpage()
            or root_page_permissions.can_edit()
        ):
            # Include deleted entries
            q = q | Q(
                page_id__in=Subquery(
                    PageLogEntry.objects.filter(deleted=True).values("page_id")
                )
            )

        return PageLogEntry.objects.filter(q)


class PageLogEntry(BaseLogEntry):
    page = models.ForeignKey(
        "wagtailcore.Page",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        related_name="+",
    )
    # Pointer to a specific page revision
    revision = models.ForeignKey(
        "wagtailcore.PageRevision",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        related_name="+",
    )

    objects = PageLogEntryManager()

    class Meta:
        ordering = ["-timestamp", "-id"]
        verbose_name = _("page log entry")
        verbose_name_plural = _("page log entries")

    def __str__(self):
        return "PageLogEntry %d: '%s' on '%s' with id %s" % (
            self.pk,
            self.action,
            self.object_verbose_name(),
            self.page_id,
        )

    @cached_property
    def object_id(self):
        return self.page_id

    @cached_property
    def message(self):
        # for page log entries, the 'edit' action should show as 'Draft saved'
        if self.action == "wagtail.edit":
            return _("Draft saved")
        else:
            return super().message
