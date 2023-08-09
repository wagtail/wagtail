from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from wagtail.models import Revision, WorkflowState


class Command(BaseCommand):
    help = "Delete revisions which are not the latest revision, published or scheduled to be published, or in moderation"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            help="Only delete revisions older than this number of days",
        )
        parser.add_argument(
            "--pages",
            action="store_true",
            help="Only delete revisions of page models",
        )
        parser.add_argument(
            "--non-pages",
            action="store_true",
            help="Only delete revisions of non-page models",
        )

    def handle(self, *args, **options):
        days = options.get("days")
        pages = options.get("pages")
        non_pages = options.get("non_pages")

        revisions_deleted = purge_revisions(days=days, pages=pages, non_pages=non_pages)

        if revisions_deleted:
            self.stdout.write(
                self.style.SUCCESS(
                    "Successfully deleted %s revisions" % revisions_deleted
                )
            )
        else:
            self.stdout.write("No revisions deleted")


def purge_revisions(days=None, pages=True, non_pages=True):
    if pages == non_pages:
        # If both are True or both are False, purge revisions of pages and non-pages
        objects = Revision.objects.all()
    elif pages:
        objects = Revision.objects.page_revisions()
    elif non_pages:
        objects = Revision.objects.not_page_revisions()

    # exclude revisions which have been submitted for moderation in the old system
    purgeable_revisions = objects.exclude(submitted_for_moderation=True).exclude(
        # and exclude revisions with an approved_go_live_at date
        approved_go_live_at__isnull=False
    )

    if getattr(settings, "WAGTAIL_WORKFLOW_ENABLED", True):
        purgeable_revisions = purgeable_revisions.exclude(
            # and exclude revisions linked to an in progress or needs changes workflow state
            Q(task_states__workflow_state__status=WorkflowState.STATUS_IN_PROGRESS)
            | Q(task_states__workflow_state__status=WorkflowState.STATUS_NEEDS_CHANGES)
        )

    if days:
        purgeable_until = timezone.now() - timezone.timedelta(days=days)
        # only include revisions which were created before the cut off date
        purgeable_revisions = purgeable_revisions.filter(created_at__lt=purgeable_until)

    deleted_revisions_count = 0

    for revision in purgeable_revisions.iterator():
        # don't delete the latest revision
        if not revision.is_latest_revision():
            revision.delete()
            deleted_revisions_count += 1

    return deleted_revisions_count
