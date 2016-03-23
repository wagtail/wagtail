from __future__ import print_function

import json

from django.core.management.base import BaseCommand
from django.utils import dateparse, timezone

from wagtail.wagtailcore.models import Page, PageRevision


def revision_date_expired(r):
    expiry_str = json.loads(r.content_json).get('expire_at')
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
            '--dryrun', action='store_true', dest='dryrun', default=False,
            help="Dry run -- dont't change anything.")

    def handle(self, *args, **options):
        dryrun = False
        if options['dryrun']:
            print("Will do a dry run.")
            dryrun = True

        # 1. get all expired pages with live = True
        expired_pages = Page.objects.filter(
            live=True,
            expire_at__lt=timezone.now()
        )
        if dryrun:
            if expired_pages:
                print("Expired pages to be deactivated:")
                print("Expiry datetime\t\tSlug\t\tName")
                print("---------------\t\t----\t\t----")
                for ep in expired_pages:
                    print("{0}\t{1}\t{2}".format(
                        ep.expire_at.strftime("%Y-%m-%d %H:%M"),
                        ep.slug,
                        ep.title
                    ))
            else:
                print("No expired pages to be deactivated found.")
        else:
            # Unpublish the expired pages
            # Cast to list to make sure the query is fully evaluated
            # before unpublishing anything
            for page in list(expired_pages):
                page.unpublish(set_expired=True)

        # 2. get all page revisions for moderation that have been expired
        expired_revs = [
            r for r in PageRevision.objects.filter(
                submitted_for_moderation=True
            ) if revision_date_expired(r)
        ]
        if dryrun:
            print("---------------------------------")
            if expired_revs:
                print("Expired revisions to be dropped from moderation queue:")
                print("Expiry datetime\t\tSlug\t\tName")
                print("---------------\t\t----\t\t----")
                for er in expired_revs:
                    rev_data = json.loads(er.content_json)
                    print("{0}\t{1}\t{2}".format(
                        dateparse.parse_datetime(
                            rev_data.get('expire_at')
                        ).strftime("%Y-%m-%d %H:%M"),
                        rev_data.get('slug'),
                        rev_data.get('title')
                    ))
            else:
                print("No expired revision to be dropped from moderation.")
        else:
            for er in expired_revs:
                er.submitted_for_moderation = False
                er.save()

        # 3. get all revisions that need to be published
        revs_for_publishing = PageRevision.objects.filter(
            approved_go_live_at__lt=timezone.now()
        )
        if dryrun:
            print("---------------------------------")
            if revs_for_publishing:
                print("Revisions to be published:")
                print("Go live datetime\t\tSlug\t\tName")
                print("---------------\t\t\t----\t\t----")
                for rp in revs_for_publishing:
                    rev_data = json.loads(rp.content_json)
                    print("{0}\t\t{1}\t{2}".format(
                        rp.approved_go_live_at.strftime("%Y-%m-%d %H:%M"),
                        rev_data.get('slug'),
                        rev_data.get('title')
                    ))
            else:
                print("No pages to go live.")
        else:
            for rp in revs_for_publishing:
                # just run publish for the revision -- since the approved go
                # live datetime is before now it will make the page live
                rp.publish()
