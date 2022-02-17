# -*- coding: utf-8 -*-
import datetime
from io import BytesIO

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from openpyxl import load_workbook

from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.admin.panels import get_form_for_model
from wagtail.contrib.forms.models import FormSubmission
from wagtail.contrib.forms.panels import FormSubmissionsPanel
from wagtail.contrib.forms.tests.utils import (
    make_form_page,
    make_form_page_with_custom_submission,
)
from wagtail.models import Locale, Page
from wagtail.test.testapp.models import (
    CustomFormPageSubmission,
    ExtendedFormField,
    FormField,
    FormFieldForCustomListViewPage,
    FormFieldWithCustomSubmission,
    FormPage,
    FormPageWithCustomFormBuilder,
    FormPageWithCustomSubmission,
    FormPageWithCustomSubmissionListView,
)
from wagtail.test.utils import WagtailTestUtils


class TestFormResponsesPanel(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/")
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user

        self.form_page = make_form_page()

        self.FormPageForm = get_form_for_model(
            FormPage,
            form_class=WagtailAdminPageForm,
            fields=["title", "slug", "to_address", "from_address", "subject"],
        )

        panel = FormSubmissionsPanel().bind_to_model(FormPage)
        self.panel = panel.get_bound_panel(
            instance=self.form_page, form=self.FormPageForm(), request=self.request
        )

    def test_render_with_submissions(self):
        """Show the panel with the count of submission and a link to the list_submissions view."""
        self.client.post(
            "/contact-us/",
            {
                "your_email": "bob@example.com",
                "your_message": "hello world",
                "your_choices": {"foo": "", "bar": "", "baz": ""},
            },
        )

        self.assertTrue(self.panel.is_shown())
        result = self.panel.render_html()

        url = reverse("wagtailforms:list_submissions", args=(self.form_page.id,))
        link = '<a href="{}">1</a>'.format(url)

        self.assertIn(link, result)

    def test_render_without_submissions(self):
        """The panel should not be shown if the number of submission is zero."""
        self.assertFalse(self.panel.is_shown())


class TestFormResponsesPanelWithCustomSubmissionClass(TestCase, WagtailTestUtils):
    def setUp(self):
        self.request = RequestFactory().get("/")
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user

        # Create a form page
        self.form_page = make_form_page_with_custom_submission()

        self.FormPageForm = get_form_for_model(
            FormPageWithCustomSubmission,
            form_class=WagtailAdminPageForm,
            fields=["title", "slug", "to_address", "from_address", "subject"],
        )

        self.test_user = self.create_user(username="user-n1kola", password="123")

        panel = FormSubmissionsPanel().bind_to_model(FormPageWithCustomSubmission)
        self.panel = panel.get_bound_panel(
            instance=self.form_page, form=self.FormPageForm(), request=self.request
        )

    def test_render_with_submissions(self):
        """Show the panel with the count of submission and a link to the list_submissions view."""
        new_form_submission = CustomFormPageSubmission.objects.create(
            user=self.test_user,
            page=self.form_page,
            form_data={
                "your_email": "email@domain.com",
                "your_message": "hi joe",
                "your_choices": {"foo": "", "bar": "", "baz": ""},
            },
        )
        new_form_submission.submit_time = "2017-08-29T12:00:00.000Z"
        new_form_submission.save()

        self.assertTrue(self.panel.is_shown())
        result = self.panel.render_html()

        url = reverse("wagtailforms:list_submissions", args=(self.form_page.id,))
        link = '<a href="{}">1</a>'.format(url)

        self.assertIn(link, result)

    def test_render_without_submissions(self):
        """The panel should not be shown if the number of submission is zero."""
        self.assertFalse(self.panel.is_shown())


class TestFormsIndex(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.login(username="siteeditor", password="password")
        self.form_page = Page.objects.get(url_path="/home/contact-us/")

    def make_form_pages(self):
        """
        This makes 100 form pages and adds them as children to 'contact-us'
        This is used to test pagination on the forms index
        """
        for i in range(100):
            self.form_page.add_child(
                instance=FormPage(
                    title="Form " + str(i), slug="form-" + str(i), live=True
                )
            )

    def test_forms_index(self):
        response = self.client.get(reverse("wagtailforms:index"))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index.html")

    def test_forms_index_pagination(self):
        # Create some more form pages to make pagination kick in
        self.make_form_pages()

        # Get page two
        response = self.client.get(reverse("wagtailforms:index"), {"p": 2})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index.html")

        # Check that we got the correct page
        self.assertEqual(response.context["page_obj"].number, 2)

    def test_forms_index_pagination_invalid(self):
        # Create some more form pages to make pagination kick in
        self.make_form_pages()

        # Get page two
        response = self.client.get(reverse("wagtailforms:index"), {"p": "Hello world!"})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index.html")

        # Check that it got page one
        self.assertEqual(response.context["page_obj"].number, 1)

    def test_forms_index_pagination_out_of_range(self):
        # Create some more form pages to make pagination kick in
        self.make_form_pages()

        # Get page two
        response = self.client.get(reverse("wagtailforms:index"), {"p": 99999})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index.html")

        # Check that it got the last page
        self.assertEqual(
            response.context["page_obj"].number, response.context["paginator"].num_pages
        )

    def test_cannot_see_forms_without_permission(self):
        # Login with as a user without permission to see forms
        self.login(username="eventeditor", password="password")

        response = self.client.get(reverse("wagtailforms:index"))

        # Check that the user cannot see the form page
        self.assertNotIn(self.form_page, response.context["form_pages"])

    def test_can_see_forms_with_permission(self):
        response = self.client.get(reverse("wagtailforms:index"))

        # Check that the user can see the form page
        self.assertIn(self.form_page, response.context["form_pages"])

    def test_cant_see_forms_after_filter_form_submissions_for_user_hook(self):
        # Hook allows to see forms only to superusers
        def construct_forms_for_user(user, queryset):
            if not user.is_superuser:
                queryset = queryset.none()

            return queryset

        response = self.client.get(reverse("wagtailforms:index"))

        # Check that an user can see the form page
        self.assertIn(self.form_page, response.context["form_pages"])

        with self.register_hook(
            "filter_form_submissions_for_user", construct_forms_for_user
        ):
            response = self.client.get(reverse("wagtailforms:index"))

        # Check that an user can't see the form page
        self.assertNotIn(self.form_page, response.context["form_pages"])


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestFormsIndexWithLocalisationEnabled(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.login(username="superuser", password="password")
        self.form_page = Page.objects.get(url_path="/home/contact-us/")
        self.en_locale = Locale.get_default()

        self.fr_locale = Locale.objects.create(language_code="fr")
        self.fr_form_page = self.form_page.copy_for_translation(
            self.fr_locale, copy_parents=True
        )
        self.fr_form_page.save()

        self.forms_index_url = reverse("wagtailforms:index")

    def make_form_pages(self, num=100, parent=None):
        """
        This makes 100 form pages and adds them as children to 'contact-us'
        This is used to test pagination on the forms index
        """
        if parent is None:
            parent = self.form_page

        for i in range(num):
            suffix = f"{i} [{parent.locale.get_display_name()}]"
            parent.add_child(
                instance=FormPage(
                    title=f"Form {suffix}",
                    slug=f"form-{i}-{parent.locale_id}",
                    live=True,
                    locale_id=parent.locale_id,
                )
            )

    def get_switch_current_locale_markup(self, locale):
        return f'<a href="javascript:void(0)" aria-label="{locale.get_display_name()}" class="c-dropdown__button u-btn-current w-no-underline">'

    def get_switch_link_markup(self, locale):
        return f'<a href="{self.forms_index_url}?locale={locale.language_code}" aria-label="{locale.get_display_name()}" class="u-link is-live w-no-underline">'

    def test_forms_index(self):
        response = self.client.get(self.forms_index_url)

        # Check response
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response, self.get_switch_current_locale_markup(self.en_locale)
        )
        self.assertContains(response, self.get_switch_link_markup(self.fr_locale))

        response = self.client.get(
            self.forms_index_url, {"locale": self.fr_locale.language_code}
        )
        self.assertContains(
            response, self.get_switch_current_locale_markup(self.fr_locale)
        )
        self.assertContains(response, self.get_switch_link_markup(self.en_locale))

    def test_forms_index_pagination(self):
        # Create some more form pages to make pagination kick in
        self.make_form_pages(parent=self.form_page, num=20)
        self.make_form_pages(parent=self.fr_form_page, num=20)

        # Get page two
        response = self.client.get(self.forms_index_url, {"p": 2})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index.html")

        # Check that we got the correct page
        self.assertEqual(response.context["page_obj"].number, 2)

        response = self.client.get(self.forms_index_url, {"p": 3})
        self.assertEqual(response.context["page_obj"].number, 2)

        # now check the French pages.
        response = self.client.get(
            self.forms_index_url, {"p": 2, "locale": self.fr_locale.language_code}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 2)

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_switcher_doesnt_show_with_i18n_disabled(self):
        response = self.client.get(self.forms_index_url)

        self.assertNotContains(
            response, self.get_switch_current_locale_markup(self.en_locale)
        )
        self.assertNotContains(response, self.get_switch_link_markup(self.fr_locale))


class TestFormsSubmissionsList(TestCase, WagtailTestUtils):
    def setUp(self):
        # Create a form page
        self.form_page = make_form_page()

        # Add a couple of form submissions
        # (save new_form_submission first, so that we're more likely to reveal bugs where
        # we're relying on the database's internal ordering instead of explicitly ordering
        # by submit_time)

        new_form_submission = FormSubmission.objects.create(
            page=self.form_page,
            form_data={
                "your_email": "new@example.com",
                "your_message": "this is a fairly new message",
                "your_choices": ["foo", "baz"],
            },
        )
        new_form_submission.submit_time = "2014-01-01T12:00:00.000Z"
        new_form_submission.save()

        old_form_submission = FormSubmission.objects.create(
            page=self.form_page,
            form_data={
                "your_email": "old@example.com",
                "your_message": "this is a really old message",
            },
        )
        old_form_submission.submit_time = "2013-01-01T12:00:00.000Z"
        old_form_submission.save()

        # Login
        self.login()

    def make_list_submissions(self):
        """
        This makes 100 submissions to test pagination on the forms submissions page
        """
        for i in range(100):
            submission = FormSubmission(
                page=self.form_page, form_data={"hello": "world"}
            )
            submission.save()

    def test_list_submissions(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,))
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index_submissions.html")
        self.assertEqual(len(response.context["data_rows"]), 2)

        # check display of list values within form submissions
        self.assertContains(response, "foo, baz")

    def test_list_submissions_after_filter_form_submissions_for_user_hook(self):
        # Hook forbids to delete form submissions for everyone
        def construct_forms_for_user(user, queryset):
            return queryset.none()

        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,))
        )

        # An user can see form submissions without the hook
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index_submissions.html")
        self.assertEqual(len(response.context["data_rows"]), 2)

        with self.register_hook(
            "filter_form_submissions_for_user", construct_forms_for_user
        ):
            response = self.client.get(
                reverse("wagtailforms:list_submissions", args=(self.form_page.id,))
            )

        # An user can't see form submissions with the hook
        self.assertRedirects(response, "/admin/")

    def test_list_submissions_filtering_date_from(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"date_from": "01/01/2014"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index_submissions.html")
        self.assertEqual(len(response.context["data_rows"]), 1)

    def test_list_submissions_filtering_date_to(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"date_to": "12/31/2013"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index_submissions.html")
        self.assertEqual(len(response.context["data_rows"]), 1)

    def test_list_submissions_filtering_range(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"date_from": "12/31/2013", "date_to": "01/02/2014"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index_submissions.html")
        self.assertEqual(len(response.context["data_rows"]), 1)

    def test_list_submissions_pagination(self):
        self.make_list_submissions()

        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"p": 2},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index_submissions.html")

        # Check that we got the correct page
        self.assertEqual(response.context["page_obj"].number, 2)

    def test_list_submissions_pagination_invalid(self):
        self.make_list_submissions()

        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"p": "Hello World!"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index_submissions.html")

        # Check that we got page one
        self.assertEqual(response.context["page_obj"].number, 1)

    def test_list_submissions_pagination_out_of_range(self):
        self.make_list_submissions()

        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"p": 99999},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index_submissions.html")

        # Check that we got the last page
        self.assertEqual(
            response.context["page_obj"].number, response.context["paginator"].num_pages
        )

    def test_list_submissions_default_order(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,))
        )
        # check default ordering, most recent responses first
        first_row_values = response.context["data_rows"][0]["fields"]
        self.assertIn("this is a fairly new message", first_row_values)

    def test_list_submissions_url_params_ordering_recent_first(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"order_by": "-submit_time"},
        )
        # check ordering matches '-submit_time' (most recent first)
        first_row_values = response.context["data_rows"][0]["fields"]
        self.assertIn("this is a fairly new message", first_row_values)

    def test_list_submissions_url_params_ordering_oldest_first(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"order_by": "submit_time"},
        )
        # check ordering matches 'submit_time' (oldest first)
        first_row_values = response.context["data_rows"][0]["fields"]
        self.assertIn("this is a really old message", first_row_values)


class TestFormsSubmissionsExport(TestCase, WagtailTestUtils):
    def setUp(self):
        # Create a form page
        self.form_page = make_form_page()

        # Add a couple of form submissions
        old_form_submission = FormSubmission.objects.create(
            page=self.form_page,
            form_data={
                "your_email": "old@example.com",
                "your_message": "this is a really old message",
                "your_choices": ["foo", "baz"],
            },
        )
        if settings.USE_TZ:
            old_form_submission.submit_time = "2013-01-01T12:00:00.000Z"
        else:
            old_form_submission.submit_time = "2013-01-01T12:00:00"
        old_form_submission.save()

        new_form_submission = FormSubmission.objects.create(
            page=self.form_page,
            form_data={
                "your_email": "new@example.com",
                "your_message": "this is a fairly new message",
            },
        )
        if settings.USE_TZ:
            new_form_submission.submit_time = "2014-01-01T12:00:00.000Z"
        else:
            new_form_submission.submit_time = "2014-01-01T12:00:00"
        new_form_submission.save()

        # Login
        self.login()

    def test_list_submissions_csv_export(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"export": "csv"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data_lines = response.getvalue().decode().split("\n")

        self.assertEqual(
            data_lines[0], "Submission date,Your email,Your message,Your choices\r"
        )
        if settings.USE_TZ:
            self.assertEqual(
                data_lines[1],
                '2013-01-01 12:00:00+00:00,old@example.com,this is a really old message,"foo, baz"\r',
            )
            self.assertEqual(
                data_lines[2],
                "2014-01-01 12:00:00+00:00,new@example.com,this is a fairly new message,None\r",
            )
        else:
            self.assertEqual(
                data_lines[1],
                '2013-01-01 12:00:00,old@example.com,this is a really old message,"foo, baz"\r',
            )
            self.assertEqual(
                data_lines[2],
                "2014-01-01 12:00:00,new@example.com,this is a fairly new message,None\r",
            )

    def test_list_submissions_xlsx_export(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"export": "xlsx"},
        )

        self.assertEqual(response.status_code, 200)
        workbook_data = response.getvalue()
        worksheet = load_workbook(filename=BytesIO(workbook_data))["Sheet1"]
        cell_array = [[cell.value for cell in row] for row in worksheet.rows]
        self.assertEqual(
            cell_array[0],
            ["Submission date", "Your email", "Your message", "Your choices"],
        )
        self.assertEqual(
            cell_array[1],
            [
                datetime.datetime(2013, 1, 1, 12, 0),
                "old@example.com",
                "this is a really old message",
                "foo, baz",
            ],
        )
        self.assertEqual(
            cell_array[2],
            [
                datetime.datetime(2014, 1, 1, 12, 0),
                "new@example.com",
                "this is a fairly new message",
                "None",
            ],
        )
        self.assertEqual(len(cell_array), 3)

    def test_list_submissions_csv_large_export(self):
        for i in range(100):
            new_form_submission = FormSubmission.objects.create(
                page=self.form_page,
                form_data={
                    "your-email": "new@example-%s.com" % i,
                    "your-message": "I like things x %s" % i,
                },
            )
            if settings.USE_TZ:
                new_form_submission.submit_time = "2014-01-01T12:00:00.000Z"
            else:
                new_form_submission.submit_time = "2014-01-01T12:00:00"
            new_form_submission.save()

        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"export": "csv"},
        )

        # Check that csv export is not paginated
        self.assertEqual(response.status_code, 200)
        data_lines = response.getvalue().decode().split("\n")
        self.assertEqual(104, len(data_lines))

    def test_list_submissions_csv_export_after_filter_form_submissions_for_user_hook(
        self,
    ):
        # Hook forbids to delete form submissions for everyone
        def construct_forms_for_user(user, queryset):
            return queryset.none()

        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"export": "csv"},
        )

        # An user can export form submissions without the hook
        self.assertEqual(response.status_code, 200)
        data_lines = response.getvalue().decode().split("\n")

        self.assertEqual(
            data_lines[0], "Submission date,Your email,Your message,Your choices\r"
        )
        if settings.USE_TZ:
            self.assertEqual(
                data_lines[1],
                '2013-01-01 12:00:00+00:00,old@example.com,this is a really old message,"foo, baz"\r',
            )
            self.assertEqual(
                data_lines[2],
                "2014-01-01 12:00:00+00:00,new@example.com,this is a fairly new message,None\r",
            )
        else:
            self.assertEqual(
                data_lines[1],
                '2013-01-01 12:00:00,old@example.com,this is a really old message,"foo, baz"\r',
            )
            self.assertEqual(
                data_lines[2],
                "2014-01-01 12:00:00,new@example.com,this is a fairly new message,None\r",
            )

        with self.register_hook(
            "filter_form_submissions_for_user", construct_forms_for_user
        ):
            response = self.client.get(
                reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
                {"export": "csv"},
            )

        # An user can't export form submission with the hook
        self.assertRedirects(response, "/admin/")

    def test_list_submissions_csv_export_with_date_from_filtering(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"export": "csv", "date_from": "01/01/2014"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data_lines = response.getvalue().decode().split("\n")

        self.assertEqual(
            data_lines[0], "Submission date,Your email,Your message,Your choices\r"
        )
        if settings.USE_TZ:
            self.assertEqual(
                data_lines[1],
                "2014-01-01 12:00:00+00:00,new@example.com,this is a fairly new message,None\r",
            )
        else:
            self.assertEqual(
                data_lines[1],
                "2014-01-01 12:00:00,new@example.com,this is a fairly new message,None\r",
            )

    def test_list_submissions_csv_export_with_date_to_filtering(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"export": "csv", "date_to": "12/31/2013"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data_lines = response.getvalue().decode().split("\n")

        self.assertEqual(
            data_lines[0], "Submission date,Your email,Your message,Your choices\r"
        )
        if settings.USE_TZ:
            self.assertEqual(
                data_lines[1],
                '2013-01-01 12:00:00+00:00,old@example.com,this is a really old message,"foo, baz"\r',
            )
        else:
            self.assertEqual(
                data_lines[1],
                '2013-01-01 12:00:00,old@example.com,this is a really old message,"foo, baz"\r',
            )

    def test_list_submissions_csv_export_with_range_filtering(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"export": "csv", "date_from": "12/31/2013", "date_to": "01/02/2014"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data_lines = response.getvalue().decode().split("\n")

        self.assertEqual(
            data_lines[0], "Submission date,Your email,Your message,Your choices\r"
        )
        if settings.USE_TZ:
            self.assertEqual(
                data_lines[1],
                "2014-01-01 12:00:00+00:00,new@example.com,this is a fairly new message,None\r",
            )
        else:
            self.assertEqual(
                data_lines[1],
                "2014-01-01 12:00:00,new@example.com,this is a fairly new message,None\r",
            )

    def test_list_submissions_csv_export_with_unicode_in_submission(self):
        unicode_form_submission = FormSubmission.objects.create(
            page=self.form_page,
            form_data={
                "your_email": "unicode@example.com",
                "your_message": "こんにちは、世界",
            },
        )
        unicode_form_submission.submit_time = "2014-01-02T12:00:00.000Z"
        unicode_form_submission.save()

        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"date_from": "01/02/2014", "export": "csv"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data_line = response.getvalue().decode("utf-8").split("\n")[1]
        self.assertIn("こんにちは、世界", data_line)

    def test_list_submissions_csv_export_with_unicode_in_field(self):
        FormField.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Выберите самую любимую IDE для разработке на Python",
            help_text="Вы можете выбрать только один вариант",
            field_type="radio",
            required=True,
            choices="PyCharm,vim,nano",
        )
        unicode_form_submission = FormSubmission.objects.create(
            page=self.form_page,
            form_data={
                "your_email": "unicode@example.com",
                "your_message": "We don't need unicode here",
                "u0412u044bu0431u0435u0440u0438u0442u0435_u0441u0430u043cu0443u044e_u043bu044eu0431u0438u043cu0443u044e_ide_u0434u043bu044f_u0440u0430u0437u0440u0430u0431u043eu0442u043au0435_u043du0430_python": "vim",
            },
        )
        unicode_form_submission.submit_time = "2014-01-02T12:00:00.000Z"
        unicode_form_submission.save()

        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"date_from": "01/02/2014", "export": "csv"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)

        data_lines = response.getvalue().decode("utf-8").split("\n")
        self.assertIn(
            "Выберите самую любимую IDE для разработке на Python", data_lines[0]
        )
        self.assertIn("vim", data_lines[1])


class TestCustomFormsSubmissionsExport(TestCase, WagtailTestUtils):
    def create_test_user_without_admin(self, username):
        return self.create_user(username=username, password="123")

    def setUp(self):
        # Create a form page
        self.form_page = make_form_page_with_custom_submission()

        # Add a couple of form submissions
        old_form_submission = CustomFormPageSubmission.objects.create(
            user=self.create_test_user_without_admin("user-john"),
            page=self.form_page,
            form_data={
                "your_email": "old@example.com",
                "your_message": "this is a really old message",
            },
        )
        if settings.USE_TZ:
            old_form_submission.submit_time = "2013-01-01T12:00:00.000Z"
        else:
            old_form_submission.submit_time = "2013-01-01T12:00:00"
        old_form_submission.save()

        new_form_submission = CustomFormPageSubmission.objects.create(
            user=self.create_test_user_without_admin("user-m1kola"),
            page=self.form_page,
            form_data={
                "your_email": "new@example.com",
                "your_message": "this is a fairly new message",
            },
        )
        if settings.USE_TZ:
            new_form_submission.submit_time = "2014-01-01T12:00:00.000Z"
        else:
            new_form_submission.submit_time = "2014-01-01T12:00:00"
        new_form_submission.save()

        # Login
        self.login()

    def test_list_submissions_csv_export(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"export": "csv"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data_lines = response.getvalue().decode().split("\n")

        self.assertEqual(
            data_lines[0],
            "User email,Submission date,Your email,Your message,Your choices\r",
        )
        if settings.USE_TZ:
            self.assertEqual(
                data_lines[1],
                "user-john@example.com,2013-01-01 12:00:00+00:00,old@example.com,this is a really old message,None\r",
            )
            self.assertEqual(
                data_lines[2],
                "user-m1kola@example.com,2014-01-01 12:00:00+00:00,new@example.com,this is a fairly new message,None\r",
            )
        else:
            self.assertEqual(
                data_lines[1],
                "user-john@example.com,2013-01-01 12:00:00,old@example.com,this is a really old message,None\r",
            )
            self.assertEqual(
                data_lines[2],
                "user-m1kola@example.com,2014-01-01 12:00:00,new@example.com,this is a fairly new message,None\r",
            )

    def test_list_submissions_csv_export_with_date_from_filtering(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"export": "csv", "date_from": "01/01/2014"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data_lines = response.getvalue().decode().split("\n")

        self.assertEqual(
            data_lines[0],
            "User email,Submission date,Your email,Your message,Your choices\r",
        )
        if settings.USE_TZ:
            self.assertEqual(
                data_lines[1],
                "user-m1kola@example.com,2014-01-01 12:00:00+00:00,new@example.com,this is a fairly new message,None\r",
            )
        else:
            self.assertEqual(
                data_lines[1],
                "user-m1kola@example.com,2014-01-01 12:00:00,new@example.com,this is a fairly new message,None\r",
            )

    def test_list_submissions_csv_export_with_date_to_filtering(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"export": "csv", "date_to": "12/31/2013"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data_lines = response.getvalue().decode().split("\n")

        self.assertEqual(
            data_lines[0],
            "User email,Submission date,Your email,Your message,Your choices\r",
        )
        if settings.USE_TZ:
            self.assertEqual(
                data_lines[1],
                "user-john@example.com,2013-01-01 12:00:00+00:00,old@example.com,this is a really old message,None\r",
            )
        else:
            self.assertEqual(
                data_lines[1],
                "user-john@example.com,2013-01-01 12:00:00,old@example.com,this is a really old message,None\r",
            )

    def test_list_submissions_csv_export_with_range_filtering(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"export": "csv", "date_from": "12/31/2013", "date_to": "01/02/2014"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data_lines = response.getvalue().decode().split("\n")

        self.assertEqual(
            data_lines[0],
            "User email,Submission date,Your email,Your message,Your choices\r",
        )
        if settings.USE_TZ:
            self.assertEqual(
                data_lines[1],
                "user-m1kola@example.com,2014-01-01 12:00:00+00:00,new@example.com,this is a fairly new message,None\r",
            )
        else:
            self.assertEqual(
                data_lines[1],
                "user-m1kola@example.com,2014-01-01 12:00:00,new@example.com,this is a fairly new message,None\r",
            )

    def test_list_submissions_csv_export_with_unicode_in_submission(self):
        unicode_form_submission = CustomFormPageSubmission.objects.create(
            user=self.create_test_user_without_admin("user-bob"),
            page=self.form_page,
            form_data={
                "your_email": "unicode@example.com",
                "your_message": "こんにちは、世界",
            },
        )
        unicode_form_submission.submit_time = "2014-01-02T12:00:00.000Z"
        unicode_form_submission.save()

        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"date_from": "01/02/2014", "export": "csv"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data_line = response.getvalue().decode("utf-8").split("\n")[1]
        self.assertIn("こんにちは、世界", data_line)

    def test_list_submissions_csv_export_with_unicode_in_field(self):
        FormFieldWithCustomSubmission.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Выберите самую любимую IDE для разработке на Python",
            help_text="Вы можете выбрать только один вариант",
            field_type="radio",
            required=True,
            choices="PyCharm,vim,nano",
        )
        unicode_form_submission = CustomFormPageSubmission.objects.create(
            user=self.create_test_user_without_admin("user-bob"),
            page=self.form_page,
            form_data={
                "your-email": "unicode@example.com",
                "your-message": "We don't need unicode here",
                "u0412u044bu0431u0435u0440u0438u0442u0435_u0441u0430u043cu0443u044e_u043bu044eu0431u0438u043cu0443u044e_ide_u0434u043bu044f_u0440u0430u0437u0440u0430u0431u043eu0442u043au0435_u043du0430_python": "vim",
            },
        )
        unicode_form_submission.submit_time = "2014-01-02T12:00:00.000Z"
        unicode_form_submission.save()

        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"date_from": "01/02/2014", "export": "csv"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)

        data_lines = response.getvalue().decode("utf-8").split("\n")
        self.assertIn(
            "Выберите самую любимую IDE для разработке на Python", data_lines[0]
        )
        self.assertIn("vim", data_lines[1])


class TestCustomFormsSubmissionsList(TestCase, WagtailTestUtils):
    def create_test_user_without_admin(self, username):
        return self.create_user(username=username, password="123")

    def setUp(self):
        # Create a form page
        self.form_page = make_form_page_with_custom_submission()

        # Add a couple of form submissions
        old_form_submission = CustomFormPageSubmission.objects.create(
            user=self.create_test_user_without_admin("user-john"),
            page=self.form_page,
            form_data={
                "your_email": "old@example.com",
                "your_message": "this is a really old message",
            },
        )
        old_form_submission.submit_time = "2013-01-01T12:00:00.000Z"
        old_form_submission.save()

        new_form_submission = CustomFormPageSubmission.objects.create(
            user=self.create_test_user_without_admin("user-m1kola"),
            page=self.form_page,
            form_data={
                "your_email": "new@example.com",
                "your_message": "this is a fairly new message",
            },
        )
        new_form_submission.submit_time = "2014-01-01T12:00:00.000Z"
        new_form_submission.save()

        # Login
        self.login()

    def make_list_submissions(self):
        """
        This makes 100 submissions to test pagination on the forms submissions page
        """
        for i in range(100):
            submission = CustomFormPageSubmission(
                user=self.create_test_user_without_admin("generated-username-%s" % i),
                page=self.form_page,
                form_data={
                    "your_email": "generated-your-email-%s" % i,
                    "your_message": "generated-your-message-%s" % i,
                },
            )
            submission.save()

    def test_list_submissions(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,))
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index_submissions.html")
        self.assertEqual(len(response.context["data_rows"]), 2)

        # CustomFormPageSubmission have custom field. This field should appear in the listing
        self.assertContains(
            response, '<th id="useremail" class="">User email</th>', html=True
        )
        self.assertContains(response, "<td>user-m1kola@example.com</td>", html=True)
        self.assertContains(response, "<td>user-john@example.com</td>", html=True)

    def test_list_submissions_filtering_date_from(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"date_from": "01/01/2014"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index_submissions.html")
        self.assertEqual(len(response.context["data_rows"]), 1)

        # CustomFormPageSubmission have custom field. This field should appear in the listing
        self.assertContains(
            response, '<th id="useremail" class="">User email</th>', html=True
        )
        self.assertContains(response, "<td>user-m1kola@example.com</td>", html=True)

    def test_list_submissions_filtering_date_to(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"date_to": "12/31/2013"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index_submissions.html")
        self.assertEqual(len(response.context["data_rows"]), 1)

        # CustomFormPageSubmission have custom field. This field should appear in the listing
        self.assertContains(
            response, '<th id="useremail" class="">User email</th>', html=True
        )
        self.assertContains(response, "<td>user-john@example.com</td>", html=True)

    def test_list_submissions_filtering_range(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"date_from": "12/31/2013", "date_to": "01/02/2014"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index_submissions.html")
        self.assertEqual(len(response.context["data_rows"]), 1)

        # CustomFormPageSubmission have custom field. This field should appear in the listing
        self.assertContains(
            response, '<th id="useremail" class="">User email</th>', html=True
        )
        self.assertContains(response, "<td>user-m1kola@example.com</td>", html=True)

    def test_list_submissions_pagination(self):
        self.make_list_submissions()

        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"p": 2},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index_submissions.html")

        # Check that we got the correct page
        self.assertEqual(response.context["page_obj"].number, 2)

        # CustomFormPageSubmission have custom field. This field should appear in the listing
        self.assertContains(
            response, '<th id="useremail" class="">User email</th>', html=True
        )
        self.assertContains(response, "generated-username-", count=20)

    def test_list_submissions_pagination_invalid(self):
        self.make_list_submissions()

        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"p": "Hello World!"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index_submissions.html")

        # Check that we got page one
        self.assertEqual(response.context["page_obj"].number, 1)

    def test_list_submissions_pagination_out_of_range(self):
        self.make_list_submissions()

        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"p": 99999},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index_submissions.html")

        # Check that we got the last page
        self.assertEqual(
            response.context["page_obj"].number, response.context["paginator"].num_pages
        )


class TestDeleteFormSubmission(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.login(username="siteeditor", password="password")
        self.form_page = Page.objects.get(url_path="/home/contact-us/")

    def test_delete_submission_show_confirmation(self):
        response = self.client.get(
            reverse("wagtailforms:delete_submissions", args=(self.form_page.id,))
            + "?selected-submissions={}".format(FormSubmission.objects.first().id)
        )
        # Check show confirm page when HTTP method is GET
        self.assertTemplateUsed(response, "wagtailforms/confirm_delete.html")

        # Check that the deletion has not happened with GET request
        self.assertEqual(FormSubmission.objects.count(), 2)

    def test_delete_submission_with_permissions(self):
        response = self.client.post(
            reverse("wagtailforms:delete_submissions", args=(self.form_page.id,))
            + "?selected-submissions={}".format(FormSubmission.objects.first().id)
        )

        # Check that the submission is gone
        self.assertEqual(FormSubmission.objects.count(), 1)
        # Should be redirected to list of submissions
        self.assertRedirects(
            response,
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
        )

    def test_delete_multiple_submissions_with_permissions(self):
        response = self.client.post(
            reverse("wagtailforms:delete_submissions", args=(self.form_page.id,))
            + "?selected-submissions={}&selected-submissions={}".format(
                FormSubmission.objects.first().id, FormSubmission.objects.last().id
            )
        )

        # Check that both submissions are gone
        self.assertEqual(FormSubmission.objects.count(), 0)
        # Should be redirected to list of submissions
        self.assertRedirects(
            response,
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
        )

    def test_delete_submission_bad_permissions(self):
        self.login(username="eventeditor", password="password")

        response = self.client.post(
            reverse("wagtailforms:delete_submissions", args=(self.form_page.id,))
            + "?selected-submissions={}".format(FormSubmission.objects.first().id)
        )

        # Check that the user received a permission denied response
        self.assertRedirects(response, "/admin/")

        # Check that the deletion has not happened
        self.assertEqual(FormSubmission.objects.count(), 2)

    def test_delete_submission_after_filter_form_submissions_for_user_hook(self):
        # Hook forbids to delete form submissions for everyone
        def construct_forms_for_user(user, queryset):
            return queryset.none()

        with self.register_hook(
            "filter_form_submissions_for_user", construct_forms_for_user
        ):
            response = self.client.post(
                reverse("wagtailforms:delete_submissions", args=(self.form_page.id,))
                + "?selected-submissions={}".format(FormSubmission.objects.first().id)
            )

        # An user can't delete a from submission with the hook
        self.assertRedirects(response, "/admin/")
        self.assertEqual(FormSubmission.objects.count(), 2)

        # An user can delete a form submission without the hook
        response = self.client.post(
            reverse("wagtailforms:delete_submissions", args=(self.form_page.id,))
            + "?selected-submissions={}".format(
                CustomFormPageSubmission.objects.first().id
            )
        )
        self.assertEqual(FormSubmission.objects.count(), 1)
        self.assertRedirects(
            response,
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
        )


class TestDeleteCustomFormSubmission(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.login(username="siteeditor", password="password")
        self.form_page = Page.objects.get(url_path="/home/contact-us-one-more-time/")

    def test_delete_submission_show_confirmation(self):
        response = self.client.get(
            reverse("wagtailforms:delete_submissions", args=(self.form_page.id,))
            + "?selected-submissions={}".format(
                CustomFormPageSubmission.objects.first().id
            )
        )

        # Check show confirm page when HTTP method is GET
        self.assertTemplateUsed(response, "wagtailforms/confirm_delete.html")

        # Check that the deletion has not happened with GET request
        self.assertEqual(CustomFormPageSubmission.objects.count(), 2)

    def test_delete_submission_with_permissions(self):
        response = self.client.post(
            reverse("wagtailforms:delete_submissions", args=(self.form_page.id,))
            + "?selected-submissions={}".format(
                CustomFormPageSubmission.objects.first().id
            )
        )

        # Check that the submission is gone
        self.assertEqual(CustomFormPageSubmission.objects.count(), 1)
        # Should be redirected to list of submissions
        self.assertRedirects(
            response,
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
        )

    def test_delete_multiple_submissions_with_permissions(self):
        response = self.client.post(
            reverse("wagtailforms:delete_submissions", args=(self.form_page.id,))
            + "?selected-submissions={}&selected-submissions={}".format(
                CustomFormPageSubmission.objects.first().id,
                CustomFormPageSubmission.objects.last().id,
            )
        )

        # Check that both submissions are gone
        self.assertEqual(CustomFormPageSubmission.objects.count(), 0)
        # Should be redirected to list of submissions
        self.assertRedirects(
            response,
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
        )

    def test_delete_submission_bad_permissions(self):
        self.login(username="eventeditor", password="password")

        response = self.client.post(
            reverse("wagtailforms:delete_submissions", args=(self.form_page.id,))
            + "?selected-submissions={}".format(
                CustomFormPageSubmission.objects.first().id
            )
        )

        # Check that the user received a permission denied response
        self.assertRedirects(response, "/admin/")

        # Check that the deletion has not happened
        self.assertEqual(CustomFormPageSubmission.objects.count(), 2)


class TestFormsWithCustomSubmissionsList(TestCase, WagtailTestUtils):
    def create_test_user_without_admin(self, username):
        return self.create_user(username=username, password="123")

    def setUp(self):
        # Create a form page

        home_page = Page.objects.get(url_path="/home/")
        self.form_page = home_page.add_child(
            instance=FormPageWithCustomSubmissionListView(
                title="Willy Wonka Chocolate Ideas",
                slug="willy-wonka-chocolate-ideas",
                to_address="willy@wonka.com",
                from_address="info@wonka.com",
                subject="Chocolate Idea Submitted!",
            )
        )
        FormFieldForCustomListViewPage.objects.create(
            page=self.form_page,
            sort_order=1,
            label="Your email",
            field_type="email",
            required=True,
        )
        FormFieldForCustomListViewPage.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Chocolate",
            field_type="singleline",
            required=True,
        )
        FormFieldForCustomListViewPage.objects.create(
            page=self.form_page,
            sort_order=3,
            label="Ingredients",
            field_type="multiline",
            required=True,
        )
        self.choices = [
            "What is chocolate?",
            "Mediocre",
            "Much excitement",
            "Wet my pants excited!",
        ]
        FormFieldForCustomListViewPage.objects.create(
            page=self.form_page,
            sort_order=4,
            label="Your Excitement",
            field_type="radio",
            required=True,
            choices=",".join(self.choices),
        )

        self.test_user_1 = self.create_test_user_without_admin("user-chocolate-maniac")
        self.test_user_2 = self.create_test_user_without_admin("user-chocolate-guy")

        # add a couple of initial form submissions for testing ordering
        new_form_submission = CustomFormPageSubmission.objects.create(
            page=self.form_page,
            user=self.test_user_1,
            form_data={
                "your_email": "new@example.com",
                "chocolate": "White Chocolate",
                "ingredients": "White colouring",
                "your_excitement": self.choices[2],
            },
        )
        if settings.USE_TZ:
            new_form_submission.submit_time = "2017-10-01T12:00:00.000Z"
        else:
            new_form_submission.submit_time = "2017-10-01T12:00:00"
        new_form_submission.save()

        old_form_submission = CustomFormPageSubmission.objects.create(
            page=self.form_page,
            user=self.test_user_2,
            form_data={
                "your_email": "old@example.com",
                "chocolate": "Dark Chocolate",
                "ingredients": "Charcoal",
                "your_excitement": self.choices[0],
            },
        )
        if settings.USE_TZ:
            old_form_submission.submit_time = "2017-01-01T12:00:00.000Z"
        else:
            old_form_submission.submit_time = "2017-01-01T12:00:00"
        old_form_submission.save()

        self.login()

    def make_list_submissions(self):
        """Make 100 submissions to test pagination on the forms submissions page"""
        for i in range(120):
            submission = CustomFormPageSubmission(
                page=self.form_page,
                user=self.test_user_1,
                form_data={
                    "your_email": "foo-%s@bar.com" % i,
                    "chocolate": "Chocolate No.%s" % i,
                    "your_excitement": self.choices[3],
                },
            )
            submission.save()

    def test_list_submissions(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,))
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index_submissions.html")
        self.assertEqual(len(response.context["data_rows"]), 2)

        # check display of list values within form submissions
        self.assertContains(response, "Much excitement")
        self.assertContains(response, "White Chocolate")
        self.assertContains(response, "Dark Chocolate")

    def test_list_submissions_pagination(self):
        self.make_list_submissions()

        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"p": 2},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index_submissions.html")

        # test that paginate by 50 is working, should be 3 max pages (~120 values)
        self.assertContains(response, "Page 2 of 3")
        self.assertContains(response, "Wet my pants excited!", count=50)
        self.assertEqual(response.context["page_obj"].number, 2)

    def test_list_submissions_csv_export(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,)),
            {"export": "csv"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data_lines = response.getvalue().decode().split("\n")
        self.assertIn(
            'filename="%s-export' % self.form_page.slug,
            response.get("Content-Disposition"),
        )
        self.assertEqual(
            data_lines[0],
            "User email,Submission date,Your email,Chocolate,Ingredients,Your Excitement\r",
        )
        # first result should be the most recent as order_csv has been reversed
        if settings.USE_TZ:
            self.assertEqual(
                data_lines[1],
                "user-chocolate-maniac@example.com,2017-10-01 12:00:00+00:00,new@example.com,White Chocolate,White colouring,Much excitement\r",
            )
            self.assertEqual(
                data_lines[2],
                "user-chocolate-guy@example.com,2017-01-01 12:00:00+00:00,old@example.com,Dark Chocolate,Charcoal,What is chocolate?\r",
            )
        else:
            self.assertEqual(
                data_lines[1],
                "user-chocolate-maniac@example.com,2017-10-01 12:00:00,new@example.com,White Chocolate,White colouring,Much excitement\r",
            )
            self.assertEqual(
                data_lines[2],
                "user-chocolate-guy@example.com,2017-01-01 12:00:00,old@example.com,Dark Chocolate,Charcoal,What is chocolate?\r",
            )

    def test_list_submissions_ordering(self):
        form_submission = CustomFormPageSubmission.objects.create(
            page=self.form_page,
            user=self.create_test_user_without_admin("user-aaa-aaa"),
            form_data={
                "your_email": "new@example.com",
                "chocolate": "Old chocolate idea",
                "ingredients": "Sugar",
                "your_excitement": self.choices[2],
            },
        )
        form_submission.submit_time = "2016-01-01T12:00:00.000Z"
        form_submission.save()

        # check ordering matches default which is overridden to be 'submit_time' (oldest first)
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,))
        )
        first_row_values = response.context["data_rows"][0]["fields"]
        self.assertIn("Old chocolate idea", first_row_values)


class TestFormsWithCustomFormBuilderSubmissionsList(TestCase, WagtailTestUtils):
    def setUp(self):
        home_page = Page.objects.get(url_path="/home/")
        form_page = home_page.add_child(
            instance=FormPageWithCustomFormBuilder(
                title="Support Request",
                slug="support-request",
                to_address="it@jenkins.com",
                from_address="support@jenkins.com",
                subject="Support Request Submitted",
            )
        )
        ExtendedFormField.objects.create(
            page=form_page,
            sort_order=1,
            label="Name",
            field_type="singleline",  # singleline field will be max_length 120
            required=True,
        )
        ExtendedFormField.objects.create(
            page=form_page,
            sort_order=1,
            label="Device IP Address",
            field_type="ipaddress",
            required=True,
        )

        for i in range(20):
            submission = FormSubmission.objects.create(
                page=form_page,
                form_data={
                    "name": "John %s" % i,
                    "device_ip_address": "192.0.2.%s" % i,
                },
            )
            submission.save()
        self.form_page = form_page
        # Login
        self.login()

    def test_list_submissions(self):
        response = self.client.get(
            reverse("wagtailforms:list_submissions", args=(self.form_page.id,))
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailforms/index_submissions.html")
        self.assertEqual(len(response.context["data_rows"]), 20)

        # check display of list values within form submissions
        self.assertContains(response, "192.0.2.1")
        self.assertContains(response, "192.0.2.15")


class TestDuplicateFormFieldLabels(TestCase, WagtailTestUtils):
    """
    If a user creates two fields with the same label, data cannot be saved correctly.
    See: https://github.com/wagtail/wagtail/issues/585
    """

    fixtures = ["test.json"]

    def setUp(self):

        self.login(username="superuser", password="password")
        # Find root page
        self.root_page = Page.objects.get(id=2)

    def test_adding_duplicate_form_labels(self):
        post_data = {
            "title": "Form page!",
            "content": "Some content",
            "slug": "contact-us",
            "form_fields-TOTAL_FORMS": "3",
            "form_fields-INITIAL_FORMS": "3",
            "form_fields-MIN_NUM_FORMS": "0",
            "form_fields-MAX_NUM_FORMS": "1000",
            "form_fields-0-id": "",
            "form_fields-0-label": "foo",
            "form_fields-0-field_type": "singleline",
            "form_fields-1-id": "",
            "form_fields-1-label": "foo",
            "form_fields-1-field_type": "singleline",
            "form_fields-2-id": "",
            "form_fields-2-label": "bar",
            "form_fields-2-field_type": "singleline",
        }
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:add", args=("tests", "formpage", self.root_page.id)
            ),
            post_data,
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            text="There is another field with the label foo, please change one of them.",
        )

    def test_adding_duplicate_form_labels_as_cleaned_name(self):
        """
        Ensure form submission fails when attempting to create labels that will resolve
        to the same internal clean_name on the form field.
        """

        post_data = {
            "title": "Form page!",
            "content": "Some content",
            "slug": "contact-us",
            "form_fields-TOTAL_FORMS": "3",
            "form_fields-INITIAL_FORMS": "3",
            "form_fields-MIN_NUM_FORMS": "0",
            "form_fields-MAX_NUM_FORMS": "1000",
            "form_fields-0-id": "",
            "form_fields-0-label": "LOW EARTH ORBIT",
            "form_fields-0-field_type": "singleline",
            "form_fields-1-id": "",
            "form_fields-1-label": "low earth orbit",
            "form_fields-1-field_type": "singleline",
            "form_fields-2-id": "",
            "form_fields-2-label": "bar",
            "form_fields-2-field_type": "singleline",
        }
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:add", args=("tests", "formpage", self.root_page.id)
            ),
            post_data,
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            text="There is another field with the label LOW EARTH ORBIT, please change one of them.",
        )

    def test_adding_duplicate_form_labels_using_override_clean_name(self):
        """
        Ensure form submission fails when attempting to create labels that will resolve
        to the same clean_name that already exists when using a custom `get_field_clean_name` method
        """

        post_data = {
            "title": "Form page!",
            "content": "Some content",
            "slug": "contact-us",
            "form_fields-TOTAL_FORMS": "3",
            "form_fields-INITIAL_FORMS": "3",
            "form_fields-MIN_NUM_FORMS": "0",
            "form_fields-MAX_NUM_FORMS": "1000",
            "form_fields-0-id": "",
            "form_fields-0-label": "duplicate 1",
            "form_fields-0-field_type": "singleline",
            "form_fields-1-id": "",
            "form_fields-1-label": "duplicate 2",
            "form_fields-1-field_type": "singleline",
            "form_fields-2-id": "",
            "form_fields-2-label": "bar",
            "form_fields-2-field_type": "singleline",
        }
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "formpagewithcustomformbuilder", self.root_page.id),
            ),
            post_data,
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            text="There is another field with the label duplicate 1, please change one of them.",
        )
