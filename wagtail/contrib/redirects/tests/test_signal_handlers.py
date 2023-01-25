from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from wagtail.contrib.redirects.models import Redirect
from wagtail.coreutils import get_dummy_request
from wagtail.models import Page, Site
from wagtail.test.routablepage.models import RoutablePageTest
from wagtail.test.testapp.models import EventIndex
from wagtail.test.utils import WagtailTestUtils

User = get_user_model()


@override_settings(WAGTAILREDIRECTS_AUTO_CREATE=True)
class TestAutocreateRedirects(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.select_related("root_page").get(is_default_site=True)
        cls.user = User.objects.first()

    def setUp(self):
        self.home_page = self.site.root_page
        self.event_index = EventIndex.objects.get()
        self.other_page = Page.objects.get(url_path="/home/about-us/")

    def trigger_page_slug_changed_signal(self, page):
        page.slug += "-extra"
        with self.captureOnCommitCallbacks(execute=True):
            page.save(log_action="wagtail.publish", user=self.user, clean=False)

    def test_golden_path(self):
        # the page we'll be triggering the change for here is...
        test_subject = self.event_index

        # identify 'draft' pages in this section
        drafts = test_subject.get_descendants().not_live()
        self.assertEqual(len(drafts), 4)

        # gather urls for 'live' pages in this branch
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

        self.trigger_page_slug_changed_signal(test_subject)

        # gather all of the redirects that were created
        redirects = Redirect.objects.all()
        redirect_page_ids = {r.redirect_page_id for r in redirects}

        # a redirect should have been created for the page itself
        self.assertIn(test_subject.id, redirect_page_ids)

        # as well as for each of its live descendants
        for descendant in test_subject.get_descendants().live().iterator():
            self.assertIn(descendant.id, redirect_page_ids)

        # but not for the draft pages
        for page in drafts:
            self.assertNotIn(page.id, redirect_page_ids)

        # for each redirect created:
        for r in redirects:
            # the old_path accurately matches a url from this branch
            self.assertIn(r.old_path, branch_urls)
            # the automatically_created flag should have been set to True
            self.assertTrue(r.automatically_created)

    def test_no_redirects_created_when_page_is_root_for_all_sites_it_belongs_to(self):
        self.trigger_page_slug_changed_signal(self.home_page)
        self.assertFalse(Redirect.objects.exists())

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

        self.trigger_page_slug_changed_signal(test_subject)

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

    def test_redirect_creation_for_custom_route_paths(self):
        # Add a page that has overridden get_route_paths()
        homepage = Page.objects.get(id=2)
        routable_page = homepage.add_child(
            instance=RoutablePageTest(
                title="Routable Page",
                live=True,
            )
        )

        # Move from below the homepage to below the event index
        routable_page.move(self.event_index, pos="last-child")

        # Redirects should have been created for each path returned by get_route_paths()
        self.assertEqual(
            list(
                Redirect.objects.all()
                .values_list("old_path", "redirect_page", "redirect_page_route_path")
                .order_by("redirect_page_route_path")
            ),
            [
                ("/routable-page", routable_page.id, ""),
                (
                    "/routable-page/not-a-valid-route",
                    routable_page.id,
                    "/not-a-valid-route",
                ),
                (
                    "/routable-page/render-method-test",
                    routable_page.id,
                    "/render-method-test/",
                ),
            ],
        )

    def test_no_redirects_created_when_pages_are_moved_to_a_different_site(self):

        # Add a new home page
        homepage_2 = Page(
            title="Second home",
            slug="second-home",
        )
        root_page = Page.objects.get(depth=1)
        root_page.add_child(instance=homepage_2)

        # Create a site with the above as the root_page
        Site.objects.create(
            root_page=homepage_2,
            hostname="newsite.com",
            port=80,
        )

        # Move the event index to the new site
        self.event_index.move(homepage_2, pos="last-child")

        # No redirects should have been created
        self.assertFalse(Redirect.objects.exists())

    @override_settings(WAGTAILREDIRECTS_AUTO_CREATE=False)
    def test_no_redirects_created_if_disabled(self):
        self.trigger_page_slug_changed_signal(self.event_index)
        self.assertFalse(Redirect.objects.exists())
