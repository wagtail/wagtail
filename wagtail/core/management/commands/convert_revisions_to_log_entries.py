from django.core.management.base import BaseCommand
from wagtail.core.models import LogEntry, PageRevision


def get_comparison(page, revision_a, revision_b):
    comparison = page.get_edit_handler().get_comparison()
    comparison = [comp(revision_a, revision_b) for comp in comparison]
    comparison = [comp for comp in comparison if comp.has_changed()]

    return comparison


class Command(BaseCommand):
    def handle(self, *args, **options):
        current_page_id = None

        revisions_that_were_once_live = set()
        revisions_that_got_log_entries = set()
        previous_revision = None
        for revision in PageRevision.objects.order_by('page_id', 'created_at').select_related('page').iterator():
            is_new_page = revision.page_id != current_page_id
            has_content_changes = False
            current_page_id = revision.page_id

            current_revision_as_page = revision.as_page_object()

            if current_revision_as_page.live_revision:
                revisions_that_were_once_live.add(current_revision_as_page.live_revision_id)

            if not LogEntry.objects.filter(revision=revision).exists():
                published = revision.id == revision.page.live_revision_id

                if previous_revision is not None:
                    comparison = get_comparison(revision.page, current_revision_as_page, previous_revision.as_page_object())
                    has_content_changes = len(comparison) > 0

                if is_new_page or has_content_changes or published:
                    if is_new_page:
                        action = 'wagtail.create'
                    elif published:
                        action = 'wagtail.publish'
                    else:
                        action = 'wagtail.edit'

                    revisions_that_got_log_entries.add(revision.id)
                    LogEntry.objects.log_action(
                        instance=revision.page.specific,
                        action=action,
                        data='',
                        revision=revision,
                        user=revision.user,
                        timestamp=revision.created_at,
                        created=is_new_page,
                        content_changed=has_content_changes,
                        published=revision.id == revision.page.live_revision_id,
                    )

            previous_revision = revision

        LogEntry.objects.filter(
            revision_id__in=revisions_that_were_once_live.intersection(revisions_that_got_log_entries), published=False
        ).update(published=True)
