import datetime

from django.contrib.admin.utils import quote
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.timezone import make_aware

from wagtail.log_actions import LogContext, log
from wagtail.models import ModelLogEntry
from wagtail.test.testapp.models import Advert, DraftStateModel, FullFeaturedSnippet
from wagtail.test.utils import WagtailTestUtils


class TestSnippetHistory(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def get(self, snippet, params=None):
        return self.client.get(self.get_url(snippet, "history"), params)

    def get_url(self, snippet, url_name, args=None):
        if args is None:
            args = [quote(snippet.pk)]
        return reverse(snippet.snippet_viewset.get_url_name(url_name), args=args)

    def setUp(self):
        self.user = self.login()
        self.non_revisable_snippet = Advert.objects.get(pk=1)
        ModelLogEntry.objects.create(
            content_type=ContentType.objects.get_for_model(Advert),
            label="Test Advert",
            action="wagtail.create",
            timestamp=make_aware(datetime.datetime(2021, 9, 30, 10, 1, 0)),
            object_id="1",
        )
        ModelLogEntry.objects.create(
            content_type=ContentType.objects.get_for_model(Advert),
            label="Test Advert Updated",
            action="wagtail.edit",
            timestamp=make_aware(datetime.datetime(2022, 5, 10, 12, 34, 0)),
            object_id="1",
        )
        self.revisable_snippet = FullFeaturedSnippet.objects.create(text="Foo")
        self.initial_revision = self.revisable_snippet.save_revision(user=self.user)
        ModelLogEntry.objects.create(
            content_type=ContentType.objects.get_for_model(FullFeaturedSnippet),
            label="Foo",
            action="wagtail.create",
            timestamp=make_aware(datetime.datetime(2022, 5, 10, 20, 22, 0)),
            object_id=self.revisable_snippet.pk,
            revision=self.initial_revision,
            content_changed=True,
        )
        self.revisable_snippet.text = "Bar"
        self.edit_revision = self.revisable_snippet.save_revision(
            user=self.user, log_action=True
        )

    def test_simple(self):
        response = self.get(self.non_revisable_snippet)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<td>Created</td>", html=True)
        self.assertContains(
            response,
            'data-w-tooltip-content-value="Sept. 30, 2021, 10:01 a.m."',
        )

    def test_filters(self):
        # Should work on both non-revisable and revisable snippets
        snippets = [self.non_revisable_snippet, self.revisable_snippet]
        for snippet in snippets:
            with self.subTest(snippet=snippet):
                response = self.get(snippet, {"action": "wagtail.edit"})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Edited", count=1)
                self.assertNotContains(response, "Created")
                soup = self.get_soup(response.content)
                filter = soup.select_one(".w-active-filters .w-pill")
                clear_button = filter.select_one(".w-pill__remove")
                self.assertEqual(
                    filter.get_text(separator=" ", strip=True),
                    "Action: Edit",
                )
                self.assertIsNotNone(clear_button)
                url, params = clear_button.attrs.get("data-w-swap-src-value").split("?")
                self.assertEqual(url, self.get_url(snippet, "history_results"))
                self.assertNotIn("action=wagtail.edit", params)

    def test_should_not_show_actions_on_non_revisable_snippet(self):
        response = self.get(self.non_revisable_snippet)
        edit_url = self.get_url(self.non_revisable_snippet, "edit")
        self.assertNotContains(
            response,
            f'<a href="{edit_url}">Edit</a>',
        )

    def test_should_show_actions_on_revisable_snippet(self):
        response = self.get(self.revisable_snippet)
        edit_url = self.get_url(self.revisable_snippet, "edit")
        revert_url = self.get_url(
            self.revisable_snippet,
            "revisions_revert",
            args=[self.revisable_snippet.pk, self.initial_revision.pk],
        )

        # Should not show the "live version" or "current draft" status tags
        self.assertNotContains(
            response, '<span class="w-status w-status--primary">Live version</span>'
        )
        self.assertNotContains(
            response, '<span class="w-status w-status--primary">Current draft</span>'
        )

        # The latest revision should have an "Edit" action instead of "Review"
        self.assertContains(
            response,
            f'<a href="{edit_url}">Edit</a>',
            count=1,
        )

        # Any other revision should have a "Review" action
        self.assertContains(
            response,
            f'<a href="{revert_url}">Review this version</a>',
            count=1,
        )

    def test_with_live_and_draft_status(self):
        snippet = DraftStateModel.objects.create(text="Draft-enabled Foo, Published")
        snippet.save_revision().publish()
        snippet.refresh_from_db()

        snippet.text = "Draft-enabled Bar, In Draft"
        snippet.save_revision(log_action=True)

        response = self.get(snippet)

        # Should show the "live version" status tag for the published revision
        self.assertContains(
            response,
            '<span class="w-status w-status--primary">Live version</span>',
            count=1,
            html=True,
        )

        # Should show the "current draft" status tag for the draft revision
        self.assertContains(
            response,
            '<span class="w-status w-status--primary">Current draft</span>',
            count=1,
            html=True,
        )

        soup = self.get_soup(response.content)
        sublabel = soup.select_one(".w-breadcrumbs__sublabel")
        # Should use the latest draft title in the breadcrumbs sublabel
        self.assertEqual(sublabel.get_text(strip=True), "Draft-enabled Bar, In Draft")

    def test_history_group_by_uuid_and_action(self):
        snippet = DraftStateModel.objects.create(text="Draft-enabled Foo, Published")
        # Simulate some edit log entries without UUID
        for _ in range(3):
            snippet.save_revision(user=self.user, log_action=True)

        with LogContext(user=self.user) as context_1:
            # Simulate new revisions but share the same log context UUID
            for _ in range(3):
                snippet.save_revision(user=self.user, log_action=True)
            # Simulate a different action with the same log context UUID
            log(instance=snippet, action="wagtail.publish", user=self.user)

        # Create a new revision with a new isolated context
        with LogContext(user=self.user) as context_2:
            revision = snippet.save_revision(user=self.user, log_action=True)

        loop_contexts = []
        for _ in range(3):
            # Create a new log context for each iteration to simulate multiple
            # request-response cycles
            with LogContext(user=self.user) as loop_context:
                loop_contexts.append(loop_context)
                # Overwriting a revision should create log entries using the last
                # UUID for the given revision instead of the current context's UUID.
                snippet.save_revision(
                    overwrite_revision=revision,
                    user=self.user,
                    log_action=True,
                )

                # Simulate a different action logged a couple times, which should
                # use the new log context UUID
                for _ in range(2):
                    log(
                        instance=snippet,
                        action="wagtail.reorder",
                        user=self.user,
                        revision=revision,
                    )

        edit_logs = ModelLogEntry.objects.for_instance(snippet).filter(
            action="wagtail.edit"
        )
        self.assertEqual(edit_logs.count(), 10)
        uuids = edit_logs.filter(uuid__isnull=False).values_list("uuid", flat=True)
        self.assertEqual(len(set(uuids)), 2)

        actions = (
            ModelLogEntry.objects.for_instance(snippet)
            .order_by("timestamp")
            .values_list("action", "uuid")
        )
        self.assertEqual(
            list(actions),
            # 3 edits without UUID
            3 * [("wagtail.edit", None)]
            # A new log context, in which we create 3 edits with new revisions
            # and a publish action. All share the same UUID from the context.
            # The edits will be grouped together when shown, and the publish
            # action should be shown separately.
            + 3 * [("wagtail.edit", context_1.uuid)]
            + [("wagtail.publish", context_1.uuid)]
            # A new log context, in which we create 1 edit with a new revision.
            + [("wagtail.edit", context_2.uuid)]
            # Each of the following 3 iterations create its own log context.
            + [
                item
                for sublist in [
                    [
                        # However, the edit action overwrites a previous revision,
                        # so it should use the last UUID for that
                        # user+revision+action combo instead of the current context.
                        ("wagtail.edit", context_2.uuid),
                        # While other actions should use the current context's UUID
                        # as normal.
                        ("wagtail.reorder", loop_contexts[i].uuid),
                        ("wagtail.reorder", loop_contexts[i].uuid),
                    ]
                    for i in range(3)
                ]
                for item in sublist
            ],
        )

        response = self.get(snippet)
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        actions = soup.select("main td:first-of-type")
        # Remove dropdowns to reduce noise when making assertions
        for dropdown in soup.select("main td [data-controller='w-dropdown']"):
            dropdown.extract()
        self.assertEqual(
            [action.get_text(strip=True, separator=" | ") for action in actions],
            [
                # Two reorder actions grouped as one, iteration 3
                "Reordered",
                # The edit with the same revision and user must share the same
                # UUID (even when using a different log context), and the last
                # edit happened here.
                "Edited | Current draft",
                # Two reorder actions grouped as one, iteration 2
                "Reordered",
                # Two reorder actions grouped as one, iteration 1
                "Reordered",
                # Published action in the same log context as below
                "Published | Live version",
                # 3 edits with new revisions but all created within the first
                # log context, so should be grouped as one
                "Edited",
                # 3 edits without UUID, each shown separately
                "Edited",
                "Edited",
                "Edited",
            ],
        )

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_get_with_i18n_enabled(self):
        response = self.get(self.non_revisable_snippet)
        self.assertEqual(response.status_code, 200)
        response = self.get(self.revisable_snippet)
        self.assertEqual(response.status_code, 200)

    def test_num_queries(self):
        snippet = self.revisable_snippet

        # Warm up the cache
        self.get(snippet)

        with self.assertNumQueries(14):
            self.get(snippet)

        for i in range(20):
            revision = snippet.save_revision(user=self.user, log_action=True)
            if i % 5 == 0:
                revision.publish(user=self.user, log_action=True)

        # Should have the same number of queries as before (no N+1 queries)
        with self.assertNumQueries(14):
            self.get(snippet)
