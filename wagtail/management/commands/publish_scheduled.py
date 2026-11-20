import sched
import time
from argparse import ArgumentTypeError
from datetime import timedelta
from operator import attrgetter

import swapper
from django.apps import apps
from django.core.management.base import BaseCommand
from django.utils import timezone

from wagtail.models import DraftStateMixin, Revision

Page = swapper.load_model("wagtailcore", "Page")


def valid_include_future(val: str) -> int:
    num = int(val)
    if num <= 0:
        raise ArgumentTypeError("Must be greater than zero")
    return num


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--dryrun",
            action="store_true",
            dest="dryrun",
            default=False,
            help="Dry run -- don't change anything.",
        )
        parser.add_argument(
            "--include-future",
            type=valid_include_future,
            default=0,
            help=(
                "Number of seconds in the future to include for publishing. "
                "Pages in the future will be held until their publishing time."
            ),
        )

    def _get_expired_objects(self, max_expire_at):
        models = [Page]
        models += [
            model
            for model in apps.get_models()
            if issubclass(model, DraftStateMixin) and not issubclass(model, Page)
        ]
        for model in models:
            yield from model.objects.filter(
                live=True, expire_at__lte=max_expire_at
            ).order_by("expire_at")

    def _get_revisions_to_publish(self, max_approved_go_live_at):
        yield from (
            Revision.objects.filter(approved_go_live_at__lte=max_approved_go_live_at)
            .order_by("approved_go_live_at")
            .select_related("content_type")
        )

    def _unpublish_instance(self, obj):
        self.stdout.write(f"Unpublishing {obj} ({type(obj).__name__} {obj.pk})")
        obj.unpublish(set_expired=True, log_action="wagtail.unpublish.scheduled")

    def _publish_revision(self, revision):
        self.stdout.write(
            f"Publishing {revision.object_str} ({revision.content_type.model_class.__name__} {revision.object_id})"
        )
        # just run publish for the revision -- since the approved go
        # live datetime is before now it will make the object live
        revision.publish(log_action="wagtail.publish.scheduled")

    def handle(self, *args, **options):
        max_operation_date = timezone.now() + timedelta(
            seconds=options["include_future"]
        )

        # Explicitly use `time.time` so enterabs can be called with absolute timestamps.
        scheduler = sched.scheduler(timefunc=time.time)

        expired_objects = list(self._get_expired_objects(max_operation_date))

        self.stdout.write("\n---------------------------------")
        self.stdout.write("Expired objects to be deactivated:")
        if expired_objects:
            for obj in sorted(expired_objects, key=attrgetter("expire_at")):
                self.stdout.write(
                    f"{obj.expire_at.isoformat()}\t{obj} ({type(obj).__name__} {obj.pk})"
                )
        else:
            self.stdout.write("No expired objects to be deactivated found.")

        revisions_for_publish = list(self._get_revisions_to_publish(max_operation_date))

        self.stdout.write("\n---------------------------------")
        self.stdout.write("Revisions to be published:")
        if revisions_for_publish:
            for rp in sorted(
                revisions_for_publish, key=attrgetter("approved_go_live_at")
            ):
                self.stdout.write(
                    f"{rp.approved_go_live_at.isoformat()}\t{rp.object_str} ({rp.content_type.model_class.__name__} {rp.object_id})"
                )
        else:
            self.stdout.write("No objects to go live.")

        if options["dryrun"]:
            self.stdout.write("Dry run - no work to do.")
        else:
            for obj in expired_objects:
                scheduler.enterabs(
                    obj.expire_at.timestamp(),
                    1,
                    self._unpublish_instance,
                    argument=(obj,),
                )
            for rp in revisions_for_publish:
                scheduler.enterabs(
                    rp.approved_go_live_at.timestamp(),
                    1,
                    self._publish_revision,
                    argument=(rp,),
                )

            self.stdout.write(f"{len(scheduler.queue)} object(s) are scheduled.")

            # Run the scheduler
            scheduler.run()

            self.stdout.write(
                f"{len(revisions_for_publish)} revisions published, {len(expired_objects)} objects expired."
            )
