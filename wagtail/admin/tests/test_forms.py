from django.forms.fields import CharField
from django.test import SimpleTestCase, TestCase

from wagtail.admin.forms.auth import LoginForm, PasswordResetForm
from wagtail.admin.forms.models import WagtailAdminModelForm
from wagtail.models import Page
from wagtail.test.snippets.models import MultiSectionRichTextSnippet
from wagtail.test.testapp.models import Advert, EventPage
from wagtail.test.utils.form_data import inline_formset, nested_form_data, rich_text


class CustomLoginForm(LoginForm):
    captcha = CharField(label="Captcha", help_text="should be in extra_fields()")

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("captcha") == "solved":
            self.add_error(None, "Captcha is invalid")
        return cleaned_data


class CustomPasswordResetForm(PasswordResetForm):
    captcha = CharField(label="Captcha", help_text="should be in extra_fields()")


class TestLoginForm(TestCase):
    def test_extra_fields(self):
        form = CustomLoginForm()
        self.assertEqual(list(form.extra_fields), [("captcha", form["captcha"])])


class TestPasswordResetForm(SimpleTestCase):
    def test_extra_fields(self):
        form = CustomPasswordResetForm()
        self.assertEqual(list(form.extra_fields), [("captcha", form["captcha"])])


class TestDeferRequiredFields(TestCase):
    def test_defer_required_fields(self):
        class AdvertForm(WagtailAdminModelForm):
            class Meta:
                model = Advert
                fields = ["url", "text"]
                defer_required_on_fields = ["text"]

        form = AdvertForm(
            {
                "url": "https://www.example.com",
                "text": "",
            }
        )
        self.assertFalse(form.is_valid())

        form = AdvertForm(
            {
                "url": "https://www.example.com",
                "text": "",
            }
        )
        form.defer_required_fields()
        self.assertTrue(form.is_valid())

        form = AdvertForm(
            {
                "url": "https://www.example.com",
                "text": "",
            }
        )
        form.defer_required_fields()
        form.restore_required_fields()
        self.assertFalse(form.is_valid())


class SnippetForm(WagtailAdminModelForm):
    class Meta:
        model = MultiSectionRichTextSnippet
        fields = []
        formsets = {
            "sections": {
                "fields": ["body"],
            }
        }


class TestGetFieldUpdatesForResave(TestCase):
    def test_get_field_updates_for_resave_on_create(self):
        form = SnippetForm(
            nested_form_data(
                {
                    "sections": inline_formset(
                        [
                            {"id": "", "body": rich_text("<p>Section 1 body</p>")},
                            {"id": "", "body": rich_text("<p>Section 2 body</p>")},
                        ]
                    )
                }
            )
        )
        self.assertTrue(form.is_valid())
        snippet = form.save()
        section_1 = snippet.sections.get(body__contains="Section 1 body")
        section_2 = snippet.sections.get(body__contains="Section 2 body")
        self.assertCountEqual(
            form.get_field_updates_for_resave(),
            [
                ("sections-INITIAL_FORMS", "2"),
                ("sections-0-id", str(section_1.id)),
                ("sections-1-id", str(section_2.id)),
            ],
        )

    def test_get_field_updates_for_resave_on_update(self):
        snippet = MultiSectionRichTextSnippet()
        section_1 = snippet.sections.create(body="<p>Initial body 1</p>")
        snippet.save()

        form = SnippetForm(
            nested_form_data(
                {
                    "sections": inline_formset(
                        [
                            {
                                "id": str(section_1.id),
                                "body": rich_text("<p>Section 1 body</p>"),
                            },
                            {"id": "", "body": rich_text("<p>Section 2 body</p>")},
                        ],
                        initial=1,
                    )
                }
            ),
            instance=snippet,
        )
        self.assertTrue(form.is_valid())
        form.save()
        section_2 = snippet.sections.get(body__contains="Section 2 body")
        self.assertCountEqual(
            form.get_field_updates_for_resave(),
            [
                ("sections-INITIAL_FORMS", "2"),
                ("sections-1-id", str(section_2.id)),
            ],
        )

    def test_get_field_updates_for_resave_on_update_when_deleting_child(self):
        snippet = MultiSectionRichTextSnippet()
        section_1 = snippet.sections.create(body="<p>Initial body 1</p>")
        section_2 = snippet.sections.create(body="<p>Initial body 2</p>")
        snippet.save()

        form = SnippetForm(
            nested_form_data(
                {
                    "sections": inline_formset(
                        [
                            {
                                "id": str(section_1.id),
                                "body": rich_text("<p>Section 1 body</p>"),
                                "DELETE": "on",
                            },
                            {
                                "id": str(section_2.id),
                                "body": rich_text("<p>Section 2 body</p>"),
                            },
                            {
                                # created and immediately deleted - should not appear in updates
                                "id": "",
                                "body": rich_text("<p>Section 3 body</p>"),
                                "DELETE": "on",
                            },
                        ],
                        initial=2,
                    )
                }
            ),
            instance=snippet,
        )
        self.assertTrue(form.is_valid())
        form.save()
        self.assertCountEqual(
            form.get_field_updates_for_resave(),
            [
                ("sections-INITIAL_FORMS", "3"),
                ("sections-0-id", ""),
            ],
        )

    def test_get_field_updates_for_resave_with_nested_inline_panel(self):
        event_page = EventPage(
            title="Test event",
            date_from="2024-01-01",
            audience="public",
            location="Test location",
            cost="Free",
        )
        speaker = event_page.speakers.create(first_name="First", last_name="Last")
        award_1 = speaker.awards.create(name="Award 1")
        root_page = Page.objects.filter(depth=2).first()
        root_page.add_child(instance=event_page)

        form = event_page.get_edit_handler().get_form_class()(
            nested_form_data(
                {
                    "title": "Test event",
                    "date_from": "2024-01-01",
                    "audience": "public",
                    "location": "Test location",
                    "cost": "Free",
                    "slug": "test-event",
                    "speakers": inline_formset(
                        [
                            {
                                "id": str(speaker.id),
                                "first_name": "First",
                                "last_name": "Last",
                                "awards": inline_formset(
                                    [
                                        {"id": str(award_1.id), "name": "Award 1"},
                                        {"id": "", "name": "Award 2"},
                                    ],
                                    initial=1,
                                ),
                            },
                            {
                                "id": "",
                                "first_name": "New",
                                "last_name": "Speaker",
                                "awards": inline_formset(
                                    [
                                        {"id": "", "name": "New Award"},
                                    ]
                                ),
                            },
                        ],
                        initial=1,
                    ),
                    "carousel_items": inline_formset([]),
                    "related_links": inline_formset([]),
                    "head_counts": inline_formset([]),
                },
            ),
            instance=event_page,
        )
        self.assertTrue(form.is_valid())
        form.save()
        award_2 = speaker.awards.get(name="Award 2")
        speaker_2 = event_page.speakers.get(first_name="New", last_name="Speaker")
        award_3 = speaker_2.awards.get(name="New Award")
        self.assertCountEqual(
            form.get_field_updates_for_resave(),
            [
                ("speakers-INITIAL_FORMS", "2"),
                ("speakers-0-awards-INITIAL_FORMS", "2"),
                ("speakers-0-awards-1-id", str(award_2.id)),
                ("speakers-1-id", str(speaker_2.id)),
                ("speakers-1-awards-INITIAL_FORMS", "1"),
                ("speakers-1-awards-0-id", str(award_3.id)),
            ],
        )
