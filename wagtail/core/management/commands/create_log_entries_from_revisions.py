from django.core.management.base import BaseCommand
from wagtail.core.models import PageLogEntry, PageRevision


def get_comparison(page, revision_a, revision_b):
    comparison = page.get_edit_handler().get_comparison()
    comparison = [comp(revision_a, revision_b) for comp in comparison]
    comparison = [comp for comp in comparison if comp.has_changed()]

    return comparison


class Command(BaseCommand):
    def handle(self, *args, **options):
        current_page_id = None
        for revision in PageRevision.objects.order_by('page_id', 'created_at').select_related('page').iterator():
            is_new_page = revision.page_id != current_page_id
            if is_new_page:
                # reset previous revision when encountering a new page.
                previous_revision = None

            has_content_changes = False
            current_page_id = revision.page_id

            if not PageLogEntry.objects.filter(revision=revision).exists():
                current_revision_as_page = revision.as_page_object()
                published = revision.id == revision.page.live_revision_id

                if previous_revision is not None:
                    # Must use .specific so the comparison picks up all fields, not just base Page ones.
                    comparison = get_comparison(revision.page.specific, previous_revision.as_page_object(), current_revision_as_page)
                    has_content_changes = len(comparison) > 0

                    if current_revision_as_page.live_revision_id == previous_revision.id:
                        # Log the previous revision publishing.
                        self.log_action('wagtail.publish', previous_revision, True)

                if is_new_page or has_content_changes or published:
                    if is_new_page:
                        action = 'wagtail.create'
                    elif published:
                        action = 'wagtail.publish'
                    else:
                        action = 'wagtail.edit'

                    if published and has_content_changes:
                        # When publishing, also log the 'draft save', but only if there have been content changes
                        self.log_action('wagtail.edit', revision, has_content_changes)

                    self.log_action(action, revision, has_content_changes)

            previous_revision = revision

    def log_action(self, action, revision, has_content_changes):
        PageLogEntry.objects.log_action(
            instance=revision.page.specific,
            action=action,
            data='',
            revision=None if action == 'wagtail.create' else revision,
            user=revision.user,
            timestamp=revision.created_at,
            content_changed=has_content_changes,
        )
