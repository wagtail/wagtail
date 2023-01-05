from django.core.management.base import BaseCommand

from wagtail.models import PageLogEntry, Revision


def get_comparison(page, revision_a, revision_b):
    comparison = (
        page.get_edit_handler()
        .get_bound_panel(instance=page, form=None, request=None)
        .get_comparison()
    )
    comparison = [comp(revision_a, revision_b) for comp in comparison]
    comparison = [comp for comp in comparison if comp.has_changed()]

    return comparison


class Command(BaseCommand):
    def handle(self, *args, **options):
        current_page_id = None
        missing_models_content_type_ids = set()
        for revision in Revision.page_revisions.order_by(
            "object_id", "created_at"
        ).iterator():
            # This revision is for a page type that is no longer in the database. Bail out early.
            if (
                revision.content_object.content_type_id
                in missing_models_content_type_ids
            ):
                continue
            if not revision.content_object.specific_class:
                missing_models_content_type_ids.add(
                    revision.content_object.content_type_id
                )
                continue

            is_new_page = revision.object_id != current_page_id
            if is_new_page:
                # reset previous revision when encountering a new page.
                previous_revision = None

            has_content_changes = False
            current_page_id = revision.object_id

            if not PageLogEntry.objects.filter(revision=revision).exists():
                try:
                    current_revision_as_page = revision.as_object()
                except Exception:
                    # restoring old revisions may fail if e.g. they have an on_delete=PROTECT foreign key
                    # to a no-longer-existing model instance. We cannot compare changes between two
                    # non-restorable revisions, although we can at least infer that there was a content
                    # change at the point that it went from restorable to non-restorable or vice versa.
                    current_revision_as_page = None

                published = revision.id == revision.content_object.live_revision_id

                if previous_revision is not None:
                    try:
                        previous_revision_as_page = previous_revision.as_object()
                    except Exception:
                        previous_revision_as_page = None

                    if (
                        previous_revision_as_page is None
                        and current_revision_as_page is None
                    ):
                        # both revisions failed to restore - unable to determine presence of content changes
                        has_content_changes = False
                    elif (
                        previous_revision_as_page is None
                        or current_revision_as_page is None
                    ):
                        # one or the other revision failed to restore, which indicates a content change
                        has_content_changes = True
                    else:
                        # Must use .specific so the comparison picks up all fields, not just base Page ones.
                        comparison = get_comparison(
                            revision.content_object.specific,
                            previous_revision_as_page,
                            current_revision_as_page,
                        )
                        has_content_changes = len(comparison) > 0

                    if (
                        current_revision_as_page is not None
                        and current_revision_as_page.live_revision_id
                        == previous_revision.id
                    ):
                        # Log the previous revision publishing.
                        self.log_page_action("wagtail.publish", previous_revision, True)

                if is_new_page or has_content_changes or published:
                    actions = []

                    if is_new_page:
                        actions.append("wagtail.create")

                    if is_new_page or has_content_changes:
                        actions.append("wagtail.edit")

                    if published:
                        actions.append("wagtail.publish")

                    for action in actions:
                        self.log_page_action(action, revision, has_content_changes)

            previous_revision = revision

    def log_page_action(self, action, revision, has_content_changes):
        PageLogEntry.objects.log_action(
            instance=revision.content_object.specific,
            action=action,
            data={},
            revision=None if action == "wagtail.create" else revision,
            user=revision.user,
            timestamp=revision.created_at,
            content_changed=has_content_changes,
        )
