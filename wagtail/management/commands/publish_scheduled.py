from django.apps import apps
from django.core.management.base import BaseCommand
from django.utils import dateparse, timezone

from wagtail.models import DraftStateMixin, Page, Revision


def revision_date_expired(r):
    expiry_str = r.content.get("expire_at")
    if not expiry_str:
        return False
    expire_at = dateparse.parse_datetime(expiry_str)
    if expire_at < timezone.now():
        return True
    else:
        return False


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--dryrun",
            action="store_true",
            dest="dryrun",
            default=False,
            help="Dry run -- don't change anything.",
        )

    def handle(self, *args, **options):
        dryrun = False
        if options["dryrun"]:
            self.stdout.write("Will do a dry run.")
            dryrun = True

        models = [Page]
        models += [
            model
            for model in apps.get_models()
            if issubclass(model, DraftStateMixin) and not issubclass(model, Page)
        ]

        # 1. get all expired objects with live = True
        expired_objects = []
        for model in models:
            expired_objects += [
                model.objects.filter(live=True, expire_at__lt=timezone.now()).order_by(
                    "expire_at"
                )
            ]

        if dryrun:
            self.stdout.write("\n---------------------------------")
            if any(expired_objects):
                self.stdout.write("Expired objects to be deactivated:")
                self.stdout.write("Expiry datetime\t\tModel\t\tSlug\t\tName")
                self.stdout.write("---------------\t\t-----\t\t----\t\t----")
                for queryset in expired_objects:
                    if queryset.model is Page:
                        for obj in queryset:
                            self.stdout.write(
                                "{}\t{}\t{}\t{}".format(
                                    obj.expire_at.strftime("%Y-%m-%d %H:%M"),
                                    obj.specific_class.__name__,
                                    obj.slug,
                                    obj.title,
                                )
                            )
                    else:
                        for obj in queryset:
                            self.stdout.write(
                                "{}\t{}\t{}\t\t{}".format(
                                    obj.expire_at.strftime("%Y-%m-%d %H:%M"),
                                    queryset.model.__name__,
                                    "",
                                    str(obj),
                                )
                            )
            else:
                self.stdout.write("No expired objects to be deactivated found.")
        else:
            # Unpublish the expired objects
            for queryset in expired_objects:
                # Cast to list to make sure the query is fully evaluated
                # before unpublishing anything
                for obj in list(queryset):
                    obj.unpublish(
                        set_expired=True, log_action="wagtail.unpublish.scheduled"
                    )

        # 2. get all object revisions for moderation that have been expired
        # RemovedInWagtail60Warning
        # Remove this when the deprecation period for the legacy
        # moderation system ends.
        expired_revs = [
            r
            for r in Revision.objects.filter(submitted_for_moderation=True)
            if revision_date_expired(r)
        ]
        if dryrun:
            self.stdout.write("\n---------------------------------")
            if expired_revs:
                self.stdout.write(
                    "Expired revisions to be dropped from moderation queue:"
                )
                self.stdout.write("Expiry datetime\t\tSlug\t\tName")
                self.stdout.write("---------------\t\t----\t\t----")
                for er in expired_revs:
                    rev_data = er.content
                    self.stdout.write(
                        "{}\t{}\t{}".format(
                            dateparse.parse_datetime(
                                rev_data.get("expire_at")
                            ).strftime("%Y-%m-%d %H:%M"),
                            rev_data.get("slug"),
                            rev_data.get("title"),
                        )
                    )
            else:
                self.stdout.write("No expired revision to be dropped from moderation.")
        else:
            for er in expired_revs:
                er.submitted_for_moderation = False
                er.save()

        # 3. get all revisions that need to be published
        revs_for_publishing = Revision.objects.filter(
            approved_go_live_at__lt=timezone.now()
        ).order_by("approved_go_live_at")
        if dryrun:
            self.stdout.write("\n---------------------------------")
            if revs_for_publishing:
                self.stdout.write("Revisions to be published:")
                self.stdout.write("Go live datetime\tModel\t\tSlug\t\tName")
                self.stdout.write("----------------\t-----\t\t----\t\t----")
                for rp in revs_for_publishing:
                    model = rp.content_type.model_class()
                    rev_data = rp.content
                    self.stdout.write(
                        "{}\t{}\t{}\t\t{}".format(
                            rp.approved_go_live_at.strftime("%Y-%m-%d %H:%M"),
                            model.__name__,
                            rev_data.get("slug", ""),
                            rev_data.get("title", rp.object_str),
                        )
                    )
            else:
                self.stdout.write("No objects to go live.")
        else:
            for rp in revs_for_publishing:
                # just run publish for the revision -- since the approved go
                # live datetime is before now it will make the object live
                rp.publish(log_action="wagtail.publish.scheduled")
