from django.contrib.auth import get_user_model
from django.test import TestCase

from wagtail.contrib.redirects.models import Redirect
from wagtail.contrib.redirects.signal_handlers import autocreate_redirects
from wagtail.core.models import PageLogEntry, Site
from wagtail.core.utils import get_dummy_request
from wagtail.tests.testapp.models import EventIndex
from wagtail.tests.utils import WagtailTestUtils


User = get_user_model()


class TestAutocreateRedirects(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.select_related("root_page").get(is_default_site=True)
        cls.user = User.objects.first()

    def setUp(self):
        self.root_page = self.site.root_page
        self.event_index = EventIndex.objects.get()

    def test_redirects_created(self):
        # the page we'll be triggering the change for here is...
        test_subject = self.event_index

        # gather urls for this branch
        request = get_dummy_request()
        branch_urls = []
        for page in (
            test_subject.get_descendants(inclusive=True)
            .live()
            .specific(defer=True)
            .iterator()
        ):
            main_url = page.get_url(request).rstrip("/")
            branch_urls.extend(
                main_url + path.rstrip("/") for path in page.get_cached_paths()
            )

        # make a change that affects the url_path
        url_path_before = test_subject.url_path
        test_subject.slug = "something-different"
        test_subject.save(user=self.user, log_action="wagtail.publish")
        log_entry = PageLogEntry.objects.last()

        # invoke the signal handler
        autocreate_redirects(
            sender=EventIndex,
            instance=test_subject,
            url_path_before=url_path_before,
            url_path_after=test_subject.url_path,
            log_entry=log_entry
        )

        # gather all of the redirects that were created
        redirects = Redirect.objects.all()
        redirect_page_ids = set(r.redirect_page_id for r in redirects)

        # a redirect should have been created for the page itself
        self.assertIn(test_subject.id, redirect_page_ids)

        # as well as for each of its live descendants
        for descendant in test_subject.get_descendants().live().iterator():
            self.assertIn(descendant.id, redirect_page_ids)

        # for each redirect created:
        for r in redirects:
            # the old_path accurately matches a url from this branch
            self.assertIn(r.old_path, branch_urls)
            # the automatically_created flag should have been set to True
            self.assertTrue(r.automatically_created)
            # the trigger GenericForeignKey returns the relevant log action
            self.assertEqual(r.trigger, log_entry)

    def test_redirects_not_created_for_draft_pages(self):
        # the page we'll be triggering the change for here is...
        test_subject = self.event_index

        # but before we do, let's identify some 'draft-only' descendants
        not_live = test_subject.get_descendants().not_live()
        self.assertEqual(len(not_live), 4)

        # now, repeat the change from `test_redirects_created` to affect the `url_path``
        url_path_before = test_subject.url_path
        test_subject.slug = "something-different"
        test_subject.save(user=self.user, log_action="wagtail.publish")

        # invoke the signal handler
        autocreate_redirects(
            sender=EventIndex,
            instance=test_subject,
            url_path_before=url_path_before,
            url_path_after=test_subject.url_path,
            log_entry=PageLogEntry.objects.last()
        )

        # gather all of the redirects that were created
        redirects_by_page_id = {
            obj.redirect_page_id: obj for obj in Redirect.objects.all()
        }

        # a redirect should have been created for the page itself
        self.assertIn(test_subject.id, redirects_by_page_id)

        # and each of the 'live' descendants
        for descendant in test_subject.get_descendants().live().iterator():
            self.assertIn(descendant.id, redirects_by_page_id)

        # but, not for the draft pages
        for page in not_live:
            self.assertNotIn(page.id, redirects_by_page_id)

    def test_handling_of_existing_redirects(self):
        # the page we'll be triggering the change for here is...
        test_subject = self.event_index

        descendants = test_subject.get_descendants().live()

        # but before we do, let's add some redirects that we'll expect to conflict
        # with ones created by the signal handler
        redirect1 = Redirect.objects.create(
            old_path=Redirect.normalise_path(descendants.first().specific.url),
            site=self.site,
            redirect_link="/some-place",
            automatically_created=False,
        )
        redirect2 = Redirect.objects.create(
            old_path=Redirect.normalise_path(descendants.last().specific.url),
            site=self.site,
            redirect_link="/some-other-place",
            automatically_created=True,
        )

        # now, repeat the change from `test_redirects_created` to affect the `url_path``
        url_path_before = test_subject.url_path
        test_subject.slug = "something-different"
        test_subject.save(user=self.user, log_action="wagtail.publish")

        # invoke the signal handler
        autocreate_redirects(
            sender=EventIndex,
            instance=test_subject,
            url_path_before=url_path_before,
            url_path_after=test_subject.url_path,
            log_entry=PageLogEntry.objects.last()
        )

        # pre-existing manually-created redirects should be preserved
        from_db = Redirect.objects.get(id=redirect1.id)
        self.assertEqual(
            (
                redirect1.old_path,
                redirect1.site_id,
                redirect1.is_permanent,
                redirect1.redirect_link,
                redirect1.redirect_page,
            ),
            (
                from_db.old_path,
                from_db.site_id,
                from_db.is_permanent,
                from_db.redirect_link,
                from_db.redirect_page,
            ),
        )

        # pre-existing automatically-created redirects should be replaced completely
        self.assertFalse(Redirect.objects.filter(pk=redirect2.pk).exists())
        self.assertTrue(
            Redirect.objects.filter(
                old_path=redirect2.old_path,
                site_id=redirect2.site_id,
            ).exists()
        )

    def test_no_redirects_created_for_site_root(self):
        # the page we'll be triggering the change for here is...
        test_subject = self.root_page

        # make a change that affects the url_path
        url_path_before = test_subject.url_path
        test_subject.slug = "something-different"
        test_subject.save(user=self.user, log_action="wagtail.publish")

        # invoke the signal handler
        autocreate_redirects(
            sender=type(test_subject),
            instance=test_subject,
            url_path_before=url_path_before,
            url_path_after=test_subject.url_path,
            log_entry=PageLogEntry.objects.last()
        )

        # test that no redirects were created
        self.assertFalse(Redirect.objects.all().exists())
