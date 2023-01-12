from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from wagtail.models import Revision

try:
    from wagtail.models import WorkflowState

    workflow_support = True
except ImportError:
    workflow_support = False


class Command(BaseCommand):
    help = "Delete page revisions which are not the latest revision for a page, published or scheduled to be published, or in moderation"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            help="Only delete revisions older than this number of days",
        )

    def handle(self, *args, **options):
        days = options.get("days")

        revisions_deleted = purge_revisions(days=days)

        if revisions_deleted:
            self.stdout.write(
                self.style.SUCCESS(
                    "Successfully deleted %s revisions" % revisions_deleted
                )
            )
        else:
            self.stdout.write("No revisions deleted")


def purge_revisions(days=None):
    # exclude revisions which have been submitted for moderation in the old system
    purgeable_revisions = Revision.page_revisions.exclude(
        submitted_for_moderation=True
    ).exclude(
        # and exclude revisions with an approved_go_live_at date
        approved_go_live_at__isnull=False
    )

    if workflow_support:
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
        # don't delete the latest revision for any page
        if not revision.is_latest_revision():
            revision.delete()
            deleted_revisions_count += 1

    return deleted_revisions_count
