from datetime import date, datetime
from functools import wraps
from unittest import mock

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Permission
from django.core import checks
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils.html import json_script
from freezegun import freeze_time
from pytz import utc

from wagtail.admin.forms import WagtailAdminModelForm, WagtailAdminPageForm
from wagtail.admin.panels import (
    CommentPanel,
    FieldPanel,
    FieldRowPanel,
    InlinePanel,
    MultiFieldPanel,
    ObjectList,
    PageChooserPanel,
    PublishingPanel,
    TabbedInterface,
    extract_panel_definitions_from_model_class,
    get_form_for_model,
)
from wagtail.admin.rich_text import DraftailRichTextArea
from wagtail.admin.widgets import (
    AdminAutoHeightTextInput,
    AdminDateInput,
    AdminPageChooser,
)
from wagtail.models import Comment, CommentReply, Page, Site
from wagtail.test.testapp.forms import ValidatedPageForm
from wagtail.test.testapp.models import (
    EventPage,
    EventPageChooserModel,
    EventPageSpeaker,
    PageChooserModel,
    RestaurantPage,
    RestaurantTag,
    SimplePage,
    ValidatedPage,
)
from wagtail.test.utils import WagtailTestUtils


class TestGetFormForModel(TestCase):
    def test_get_form_without_model(self):
        edit_handler = ObjectList()
        with self.assertRaisesMessage(
            AttributeError,
            "ObjectList is not bound to a model yet. "
            "Use `.bind_to_model(model)` before using this method.",
        ):
            edit_handler.get_form_class()

    def test_get_form_for_model_without_explicit_fields(self):
        # Failing to pass a 'fields' argument to get_form_for_model IS valid, and should result in
        # a form with no fields.
        EventPageForm = get_form_for_model(
            EventPage,
            form_class=WagtailAdminPageForm,
        )
        self.assertTrue(issubclass(EventPageForm, WagtailAdminPageForm))
        form = EventPageForm()
        self.assertNotIn("title", form.fields)
        self.assertNotIn("path", form.fields)

    def test_get_form_for_model_without_formsets(self):
        EventPageForm = get_form_for_model(
            EventPage,
            form_class=WagtailAdminPageForm,
            fields=["title", "slug", "date_from", "date_to"],
        )
        form = EventPageForm()

        # form should be a subclass of WagtailAdminModelForm
        self.assertTrue(issubclass(EventPageForm, WagtailAdminModelForm))
        # form should contain a title field (from the base Page)
        self.assertEqual(type(form.fields["title"]), forms.CharField)
        # and 'date_from' from EventPage
        self.assertEqual(type(form.fields["date_from"]), forms.DateField)
        # the widget should be overridden with AdminDateInput as per FORM_FIELD_OVERRIDES
        self.assertEqual(type(form.fields["date_from"].widget), AdminDateInput)

        # treebeard's 'path' field should be excluded
        self.assertNotIn("path", form.fields)

    def test_get_form_for_model_with_formsets(self):
        EventPageForm = get_form_for_model(
            EventPage,
            form_class=WagtailAdminPageForm,
            fields=["title", "slug", "date_from", "date_to"],
            formsets=["speakers", "related_links"],
        )
        form = EventPageForm()

        # all child relations become formsets by default
        self.assertIn("speakers", form.formsets)
        self.assertIn("related_links", form.formsets)

    def test_direct_form_field_overrides(self):
        # Test that field overrides defined through DIRECT_FORM_FIELD_OVERRIDES
        # are applied

        SimplePageForm = get_form_for_model(
            SimplePage,
            form_class=WagtailAdminPageForm,
            fields=["title", "slug", "content"],
        )
        self.assertTrue(issubclass(SimplePageForm, WagtailAdminPageForm))
        simple_form = SimplePageForm()
        # plain TextFields should use AdminAutoHeightTextInput as the widget
        self.assertEqual(
            type(simple_form.fields["content"].widget), AdminAutoHeightTextInput
        )

        # This override should NOT be applied to subclasses of TextField such as
        # RichTextField - they should retain their default widgets
        EventPageForm = get_form_for_model(
            EventPage, form_class=WagtailAdminPageForm, fields=["title", "slug", "body"]
        )
        event_form = EventPageForm()
        self.assertEqual(type(event_form.fields["body"].widget), DraftailRichTextArea)

    def test_get_form_for_model_with_specific_fields(self):
        EventPageForm = get_form_for_model(
            EventPage,
            form_class=WagtailAdminPageForm,
            fields=["date_from"],
            formsets=["speakers"],
        )
        form = EventPageForm()

        # form should contain date_from but not title
        self.assertEqual(type(form.fields["date_from"]), forms.DateField)
        self.assertEqual(type(form.fields["date_from"].widget), AdminDateInput)
        self.assertNotIn("title", form.fields)

        # formsets should include speakers but not related_links
        self.assertIn("speakers", form.formsets)
        self.assertNotIn("related_links", form.formsets)

    def test_get_form_for_model_without_explicit_formsets(self):
        # omitting the 'formsets' argument from get_form_for_model should return a form with no
        # formsets, rather than a form with ALL OF THE FORMSETS which somehow seemed like a good
        # idea once
        EventPageForm = get_form_for_model(
            EventPage,
            form_class=WagtailAdminPageForm,
            fields=["date_from"],
        )
        form = EventPageForm()

        self.assertNotIn("speakers", form.formsets)
        self.assertNotIn("related_links", form.formsets)

    def test_get_form_for_model_with_excluded_fields(self):
        EventPageForm = get_form_for_model(
            EventPage,
            form_class=WagtailAdminPageForm,
            exclude=["title"],
            exclude_formsets=["related_links"],
        )
        form = EventPageForm()

        # form should contain date_from but not title
        self.assertEqual(type(form.fields["date_from"]), forms.DateField)
        self.assertEqual(type(form.fields["date_from"].widget), AdminDateInput)
        self.assertNotIn("title", form.fields)

        # formsets should include speakers but not related_links
        self.assertIn("speakers", form.formsets)
        self.assertNotIn("related_links", form.formsets)

    def test_get_form_for_model_with_widget_overides_by_class(self):
        EventPageForm = get_form_for_model(
            EventPage,
            form_class=WagtailAdminPageForm,
            fields=["date_to", "date_from"],
            widgets={"date_from": forms.PasswordInput},
        )
        form = EventPageForm()

        self.assertEqual(type(form.fields["date_from"]), forms.DateField)
        self.assertEqual(type(form.fields["date_from"].widget), forms.PasswordInput)

    def test_get_form_for_model_with_widget_overides_by_instance(self):
        EventPageForm = get_form_for_model(
            EventPage,
            form_class=WagtailAdminPageForm,
            fields=["date_to", "date_from"],
            widgets={"date_from": forms.PasswordInput()},
        )
        form = EventPageForm()

        self.assertEqual(type(form.fields["date_from"]), forms.DateField)
        self.assertEqual(type(form.fields["date_from"].widget), forms.PasswordInput)

    def test_tag_widget_is_passed_tag_model(self):
        RestaurantPageForm = get_form_for_model(
            RestaurantPage,
            form_class=WagtailAdminPageForm,
            fields=["title", "slug", "tags"],
        )
        form_html = RestaurantPageForm().as_p()
        self.assertIn("/admin/tag\\u002Dautocomplete/tests/restauranttag/", form_html)

        # widget should pick up the free_tagging=False attribute on the tag model
        # and set itself to autocomplete only
        self.assertIn('"autocompleteOnly": true', form_html)

        # Free tagging should also be disabled at the form field validation level
        RestaurantTag.objects.create(name="Italian", slug="italian")
        RestaurantTag.objects.create(name="Indian", slug="indian")

        form = RestaurantPageForm(
            {
                "title": "Buonasera",
                "slug": "buonasera",
                "tags": "Italian, delicious",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["tags"], ["Italian"])


def clear_edit_handler(page_cls):
    def decorator(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            # Clear any old panel definitions generated
            page_cls.get_edit_handler.cache_clear()
            try:
                fn(*args, **kwargs)
            finally:
                # Clear the bad panel definition generated just now
                page_cls.get_edit_handler.cache_clear()

        return decorated

    return decorator


class TestPageEditHandlers(TestCase):
    @clear_edit_handler(EventPage)
    def test_get_edit_handler(self):
        """
        Forms for pages should have a base class of WagtailAdminPageForm.
        """
        edit_handler = EventPage.get_edit_handler()
        EventPageForm = edit_handler.get_form_class()

        # The generated form should inherit from WagtailAdminPageForm
        self.assertTrue(issubclass(EventPageForm, WagtailAdminPageForm))

    @clear_edit_handler(ValidatedPage)
    def test_get_form_for_page_with_custom_base(self):
        """
        ValidatedPage sets a custom base_form_class. This should be used as the
        base class when constructing a form for ValidatedPages
        """
        edit_handler = ValidatedPage.get_edit_handler()
        GeneratedValidatedPageForm = edit_handler.get_form_class()

        # The generated form should inherit from ValidatedPageForm, because
        # ValidatedPage.base_form_class == ValidatedPageForm
        self.assertTrue(issubclass(GeneratedValidatedPageForm, ValidatedPageForm))

    @clear_edit_handler(ValidatedPage)
    def test_check_invalid_base_form_class(self):
        class BadFormClass:
            pass

        invalid_base_form = checks.Error(
            "ValidatedPage.base_form_class does not extend WagtailAdminPageForm",
            hint="Ensure that wagtail.admin.tests.test_edit_handlers.BadFormClass extends WagtailAdminPageForm",
            obj=ValidatedPage,
            id="wagtailadmin.E001",
        )

        invalid_edit_handler = checks.Error(
            "ValidatedPage.get_edit_handler().get_form_class() does not extend WagtailAdminPageForm",
            hint="Ensure that the panel definition for ValidatedPage creates a subclass of WagtailAdminPageForm",
            obj=ValidatedPage,
            id="wagtailadmin.E002",
        )

        with mock.patch.object(ValidatedPage, "base_form_class", new=BadFormClass):
            errors = checks.run_checks()

            # Only look at errors (e.g. ignore warnings about CSS not being built)
            errors = [e for e in errors if e.level >= checks.ERROR]

            # Errors may appear out of order, so sort them by id
            errors.sort(key=lambda e: e.id)

            self.assertEqual(errors, [invalid_base_form, invalid_edit_handler])

    @clear_edit_handler(ValidatedPage)
    def test_custom_edit_handler_form_class(self):
        """
        Set a custom edit handler on a Page class, but dont customise
        ValidatedPage.base_form_class, or provide a custom form class for the
        edit handler. Check the generated form class is of the correct type.
        """
        ValidatedPage.edit_handler = TabbedInterface()
        with mock.patch.object(
            ValidatedPage, "edit_handler", new=TabbedInterface(), create=True
        ):
            form_class = ValidatedPage.get_edit_handler().get_form_class()
            self.assertTrue(issubclass(form_class, WagtailAdminPageForm))
            errors = ValidatedPage.check()
            self.assertEqual(errors, [])

    @clear_edit_handler(ValidatedPage)
    def test_repr(self):
        edit_handler = ValidatedPage.get_edit_handler()

        handler_repr = repr(edit_handler)

        self.assertIn(
            "model=<class 'wagtail.test.testapp.models.ValidatedPage'>",
            handler_repr,
        )

        bound_handler = edit_handler.get_bound_panel(
            instance=None, request=None, form=None
        )
        bound_handler_repr = repr(bound_handler)
        self.assertIn(
            "model=<class 'wagtail.test.testapp.models.ValidatedPage'>",
            bound_handler_repr,
        )

        self.assertIn("instance=None", bound_handler_repr)
        self.assertIn("request=None", bound_handler_repr)
        self.assertIn("form=None", bound_handler_repr)


class TestExtractPanelDefinitionsFromModelClass(TestCase):
    def test_can_extract_panel_property(self):
        # A class with a 'panels' property defined should return that list
        result = extract_panel_definitions_from_model_class(EventPageSpeaker)
        self.assertEqual(len(result), 5)
        self.assertTrue(any([isinstance(panel, MultiFieldPanel) for panel in result]))

    def test_exclude(self):
        panels = extract_panel_definitions_from_model_class(Site, exclude=["hostname"])
        for panel in panels:
            self.assertNotEqual(panel.field_name, "hostname")

    def test_can_build_panel_list(self):
        # EventPage has no 'panels' definition, so one should be derived from the field list
        panels = extract_panel_definitions_from_model_class(EventPage)

        self.assertTrue(
            any(
                [
                    isinstance(panel, FieldPanel) and panel.field_name == "date_from"
                    for panel in panels
                ]
            )
        )


class TestTabbedInterface(TestCase, WagtailTestUtils):
    def setUp(self):
        self.request = RequestFactory().get("/")
        user = self.create_superuser(username="admin")
        self.request.user = user
        self.user = self.login()
        self.other_user = self.create_user(username="admin2", email="test2@email.com")
        p = Permission.objects.get(codename="custom_see_panel_setting")
        self.other_user.user_permissions.add(p)
        # a custom tabbed interface for EventPage
        self.event_page_tabbed_interface = TabbedInterface(
            [
                ObjectList(
                    [
                        FieldPanel("title", widget=forms.Textarea),
                        FieldPanel("date_from"),
                        FieldPanel("date_to"),
                    ],
                    heading="Event details",
                    classname="shiny",
                ),
                ObjectList(
                    [
                        InlinePanel("speakers", label="Speakers"),
                    ],
                    heading="Speakers",
                ),
                ObjectList(
                    [
                        FieldPanel("cost", permission="superuser"),
                    ],
                    heading="Secret",
                ),
                ObjectList(
                    [
                        FieldPanel("cost"),
                    ],
                    permission="tests.custom_see_panel_setting",
                    heading="Custom Setting",
                ),
                ObjectList(
                    [
                        FieldPanel("cost"),
                    ],
                    permission="tests.other_custom_see_panel_setting",
                    heading="Other Custom Setting",
                ),
            ]
        ).bind_to_model(EventPage)

    def test_get_form_class(self):
        EventPageForm = self.event_page_tabbed_interface.get_form_class()
        form = EventPageForm()

        # form must include the 'speakers' formset required by the speakers InlinePanel
        self.assertIn("speakers", form.formsets)

        # form must respect any overridden widgets
        self.assertEqual(type(form.fields["title"].widget), forms.Textarea)

    def test_render(self):
        EventPageForm = self.event_page_tabbed_interface.get_form_class()
        event = EventPage(title="Abergavenny sheepdog trials")
        form = EventPageForm(instance=event)

        tabbed_interface = self.event_page_tabbed_interface.get_bound_panel(
            instance=event,
            form=form,
            request=self.request,
        )

        result = tabbed_interface.render_html()

        # result should contain tab buttons
        self.assertIn(
            '<a id="tab-label-event_details" href="#tab-event_details" class="w-tabs__tab shiny" role="tab" aria-selected="false" tabindex="-1">',
            result,
        )
        self.assertIn(
            '<a id="tab-label-speakers" href="#tab-speakers" class="w-tabs__tab " role="tab" aria-selected="false" tabindex="-1">',
            result,
        )

        # result should contain tab panels
        self.assertIn('aria-labelledby="tab-label-event_details"', result)
        self.assertIn('aria-labelledby="tab-label-speakers"', result)

        # result should contain rendered content from descendants
        self.assertIn("Abergavenny sheepdog trials</textarea>", result)

        # this result should not include fields that are not covered by the panel definition
        self.assertNotIn("signup_link", result)

    def test_required_fields(self):
        # get_form_options should report the set of form fields to be rendered recursively by children of TabbedInterface
        result = set(self.event_page_tabbed_interface.get_form_options()["fields"])
        self.assertEqual(result, {"title", "date_from", "date_to", "cost"})

    def test_render_form_content(self):
        EventPageForm = self.event_page_tabbed_interface.get_form_class()
        event = EventPage(title="Abergavenny sheepdog trials")
        form = EventPageForm(instance=event)

        tabbed_interface = self.event_page_tabbed_interface.get_bound_panel(
            instance=event,
            form=form,
            request=self.request,
        )

        result = tabbed_interface.render_form_content()
        # rendered output should contain field content as above
        self.assertIn("Abergavenny sheepdog trials</textarea>", result)
        # rendered output should NOT include fields that are in the model but not represented
        # in the panel definition
        self.assertNotIn("signup_link", result)

    def test_tabs_permissions(self):
        """
        test that three tabs show when the current user has permission to see all three
        test that two tabs show when the current user does not have permission to see all three
        """

        EventPageForm = self.event_page_tabbed_interface.get_form_class()
        event = EventPage(title="Abergavenny sheepdog trials")
        form = EventPageForm(instance=event)

        with self.subTest("Super user test"):
            # when signed in as a superuser all tabs should be visible
            tabbed_interface = self.event_page_tabbed_interface.get_bound_panel(
                instance=event,
                form=form,
                request=self.request,
            )
            result = tabbed_interface.render_html()
            self.assertIn(
                '<a id="tab-label-event_details" href="#tab-event_details" class="w-tabs__tab shiny" role="tab" aria-selected="false" tabindex="-1">',
                result,
            )
            self.assertIn(
                '<a id="tab-label-speakers" href="#tab-speakers" class="w-tabs__tab " role="tab" aria-selected="false" tabindex="-1">',
                result,
            )
            self.assertIn(
                '<a id="tab-label-secret" href="#tab-secret" ',
                result,
            )
            self.assertIn(
                '<a id="tab-label-custom_setting" href="#tab-custom_setting" ',
                result,
            )
            self.assertIn(
                '<a id="tab-label-other_custom_setting" href="#tab-other_custom_setting" ',
                result,
            )

        with self.subTest("Not superuser permissions"):
            """
            The super user panel should not show, nor should the panel they dont have
            permission for.
            """
            self.request.user = self.other_user

            tabbed_interface = self.event_page_tabbed_interface.get_bound_panel(
                instance=event,
                form=form,
                request=self.request,
            )
            result = tabbed_interface.render_html()
            self.assertIn(
                '<a id="tab-label-event_details" href="#tab-event_details" class="w-tabs__tab shiny" role="tab" aria-selected="false" tabindex="-1">',
                result,
            )
            self.assertIn(
                '<a id="tab-label-speakers" href="#tab-speakers" class="w-tabs__tab " role="tab" aria-selected="false" tabindex="-1">',
                result,
            )
            self.assertNotIn(
                '<a id="tab-label-secret" href="#tab-secret" ',
                result,
            )
            self.assertIn(
                '<a id="tab-label-custom_setting" href="#tab-custom_setting" ',
                result,
            )
            self.assertNotIn(
                '<a id="tab-label-other_custom_setting" href="#tab-other-custom_setting" ',
                result,
            )

        with self.subTest("Non superuser"):
            # Login as non superuser to check that the third tab does not show
            user = (
                AnonymousUser()
            )  # technically, Anonymous users cannot access the admin
            self.request.user = user
            tabbed_interface = self.event_page_tabbed_interface.get_bound_panel(
                instance=event,
                form=form,
                request=self.request,
            )
            result = tabbed_interface.render_html()
            self.assertIn(
                '<a id="tab-label-event_details" href="#tab-event_details" class="w-tabs__tab shiny" role="tab" aria-selected="false" tabindex="-1">',
                result,
            )
            self.assertIn(
                '<a id="tab-label-speakers" href="#tab-speakers" class="w-tabs__tab " role="tab" aria-selected="false" tabindex="-1">',
                result,
            )
            self.assertNotIn(
                '<a id="tab-label-secret" href="#tab-secret" ',
                result,
            )
            self.assertNotIn(
                '<a id="tab-label-custom_setting" href="#tab-custom_setting" ',
                result,
            )
            self.assertNotIn(
                '<a id="tab-label-other_custom_setting" href="#tab-other-custom_setting" ',
                result,
            )


class TestObjectList(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/")
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user
        # a custom ObjectList for EventPage
        self.event_page_object_list = ObjectList(
            [
                FieldPanel("title", widget=forms.Textarea),
                FieldPanel("date_from"),
                FieldPanel("date_to"),
                InlinePanel("speakers", label="Speakers"),
            ],
            heading="Event details",
            classname="shiny",
        ).bind_to_model(EventPage)

    def test_get_form_class(self):
        EventPageForm = self.event_page_object_list.get_form_class()
        form = EventPageForm()

        # form must include the 'speakers' formset required by the speakers InlinePanel
        self.assertIn("speakers", form.formsets)

        # form must respect any overridden widgets
        self.assertEqual(type(form.fields["title"].widget), forms.Textarea)

    def test_render(self):
        EventPageForm = self.event_page_object_list.get_form_class()
        event = EventPage(title="Abergavenny sheepdog trials")
        form = EventPageForm(instance=event)

        object_list = self.event_page_object_list.get_bound_panel(
            instance=event,
            form=form,
            request=self.request,
        )

        result = object_list.render_html()

        # result should contain ObjectList furniture
        self.assertIn('<div class="w-panel__header">', result)

        # result should contain labels for children
        self.assertIn(
            '<label for="id_date_from" id="id_date_from-label">',
            result,
        )

        # result should include help text for children
        self.assertInHTML(
            '<div class="help">Not required if event is on a single day</div>',
            result,
        )

        # result should contain rendered content from descendants
        self.assertIn("Abergavenny sheepdog trials</textarea>", result)

        # this result should not include fields that are not covered by the panel definition
        self.assertNotIn("signup_link", result)


class TestFieldPanel(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/")
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user

        self.EventPageForm = get_form_for_model(
            EventPage,
            form_class=WagtailAdminPageForm,
            fields=["title", "slug", "date_from", "date_to"],
            formsets=[],
        )
        self.event = EventPage(
            title="Abergavenny sheepdog trials",
            date_from=date(2014, 7, 20),
            date_to=date(2014, 7, 21),
        )

        self.end_date_panel = FieldPanel(
            "date_to", classname="full-width"
        ).bind_to_model(EventPage)

    def test_non_model_field(self):
        # defining a FieldPanel for a field which isn't part of a model is OK,
        # because it might be defined on the form instead
        field_panel = FieldPanel("barbecue").bind_to_model(Page)

        # however, accessing db_field will fail
        with self.assertRaises(FieldDoesNotExist):
            field_panel.db_field

    def test_override_heading(self):
        # unless heading is specified in keyword arguments, an edit handler with bound form should take its
        # heading from the bound field label
        bound_panel = self.end_date_panel.get_bound_panel(
            form=self.EventPageForm(), request=self.request, instance=self.event
        )
        self.assertEqual(bound_panel.heading, bound_panel.bound_field.label)

        # if heading is explicitly provided to constructor, that heading should be taken in
        # preference to the field's label
        end_date_panel_with_overridden_heading = FieldPanel(
            "date_to", classname="full-width", heading="New heading"
        ).bind_to_model(EventPage)
        end_date_panel_with_overridden_heading = (
            end_date_panel_with_overridden_heading.get_bound_panel(
                request=self.request, form=self.EventPageForm(), instance=self.event
            )
        )
        self.assertEqual(end_date_panel_with_overridden_heading.heading, "New heading")
        self.assertEqual(
            end_date_panel_with_overridden_heading.bound_field.label, "New heading"
        )

    def test_render_html(self):
        form = self.EventPageForm(
            {
                "title": "Pontypridd sheepdog trials",
                "date_from": "2014-07-20",
                "date_to": "2014-07-22",
            },
            instance=self.event,
        )

        form.is_valid()

        field_panel = self.end_date_panel.get_bound_panel(
            instance=self.event,
            form=form,
            request=self.request,
        )
        result = field_panel.render_html()

        self.assertIn("Not required if event is on a single day", result)

        # check that the populated form field is included
        self.assertIn('value="2014-07-22"', result)

        # there should be no errors on this field
        self.assertNotIn("error-message", result)

    def test_required_fields(self):
        result = self.end_date_panel.get_form_options()["fields"]
        self.assertEqual(result, ["date_to"])

    def test_error_message_is_rendered(self):
        form = self.EventPageForm(
            {
                "title": "Pontypridd sheepdog trials",
                "date_from": "2014-07-20",
                "date_to": "2014-07-33",
            },
            instance=self.event,
        )

        form.is_valid()

        field_panel = self.end_date_panel.get_bound_panel(
            instance=self.event,
            form=form,
            request=self.request,
        )
        result = field_panel.render_html()

        self.assertIn("Enter a valid date.", result)

    def test_repr(self):
        form = self.EventPageForm()
        field_panel = self.end_date_panel.get_bound_panel(
            form=form,
            instance=self.event,
            request=self.request,
        )

        field_panel_repr = repr(field_panel)

        self.assertIn(
            "model=<class 'wagtail.test.testapp.models.EventPage'>", field_panel_repr
        )
        self.assertIn("instance=Abergavenny sheepdog trials", field_panel_repr)
        self.assertIn("request=<WSGIRequest: GET '/'>", field_panel_repr)
        self.assertIn("form=EventPageForm", field_panel_repr)


class TestFieldRowPanel(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/")
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user

        self.EventPageForm = get_form_for_model(
            EventPage,
            form_class=WagtailAdminPageForm,
            fields=["title", "slug", "date_from", "date_to"],
            formsets=[],
        )
        self.event = EventPage(
            title="Abergavenny sheepdog trials",
            date_from=date(2014, 7, 20),
            date_to=date(2014, 7, 21),
        )

        self.dates_panel = FieldRowPanel(
            [
                FieldPanel("date_from", classname="col4", heading="Start"),
                FieldPanel("date_to", classname="coltwo"),
            ],
            help_text="Confirmed event dates only",
        ).bind_to_model(EventPage)

    def test_render_html(self):
        form = self.EventPageForm(
            {
                "title": "Pontypridd sheepdog trials",
                "date_from": "2014-07-20",
                "date_to": "2014-07-22",
            },
            instance=self.event,
        )

        form.is_valid()

        field_panel = self.dates_panel.get_bound_panel(
            instance=self.event,
            form=form,
            request=self.request,
        )
        result = field_panel.render_html()

        # check that label is output in the 'field' style
        self.assertIn(
            '<label class="w-field__label" for="id_date_to" id="id_date_to-label">',
            result,
        )

        # check that field help text is included
        self.assertIn("Not required if event is on a single day", result)

        # check that row help text is included
        self.assertIn("Confirmed event dates only", result)

        # check that the populated form field is included
        self.assertIn('value="2014-07-22"', result)

        # there should be no errors on this field
        self.assertNotIn("error-message", result)

    def test_error_message_is_rendered(self):
        form = self.EventPageForm(
            {
                "title": "Pontypridd sheepdog trials",
                "date_from": "2014-07-20",
                "date_to": "2014-07-33",
            },
            instance=self.event,
        )

        form.is_valid()

        field_panel = self.dates_panel.get_bound_panel(
            instance=self.event,
            form=form,
            request=self.request,
        )
        result = field_panel.render_html()

        self.assertIn("Enter a valid date.", result)


class TestFieldRowPanelWithChooser(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/")
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user

        self.EventPageForm = get_form_for_model(
            EventPage,
            form_class=WagtailAdminPageForm,
            fields=["title", "slug", "date_from", "date_to"],
            formsets=[],
        )
        self.event = EventPage(
            title="Abergavenny sheepdog trials",
            date_from=date(2014, 7, 19),
            date_to=date(2014, 7, 21),
        )

        self.dates_panel = FieldRowPanel(
            [
                FieldPanel("date_from"),
                FieldPanel("feed_image"),
            ]
        ).bind_to_model(EventPage)

    def test_render_html(self):
        form = self.EventPageForm(
            {
                "title": "Pontypridd sheepdog trials",
                "date_from": "2014-07-20",
                "date_to": "2014-07-22",
            },
            instance=self.event,
        )

        form.is_valid()

        field_panel = self.dates_panel.get_bound_panel(
            instance=self.event,
            form=form,
            request=self.request,
        )
        result = field_panel.render_html()

        # check that the populated form field is included
        self.assertIn('value="2014-07-20"', result)

        # there should be no errors on this field
        self.assertNotIn("error-message", result)


class TestPageChooserPanel(TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.request = RequestFactory().get("/")
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user

        model = PageChooserModel  # a model with a foreign key to Page which we want to render as a page chooser

        # a PageChooserPanel class that works on PageChooserModel's 'page' field
        self.edit_handler = ObjectList([PageChooserPanel("page")]).bind_to_model(
            PageChooserModel
        )
        self.my_page_chooser_panel = self.edit_handler.children[0]

        # build a form class containing the fields that MyPageChooserPanel wants
        self.PageChooserForm = self.edit_handler.get_form_class()

        # a test instance of PageChooserModel, pointing to the 'christmas' page
        self.christmas_page = Page.objects.get(slug="christmas")
        self.events_index_page = Page.objects.get(slug="events")
        self.test_instance = model.objects.create(page=self.christmas_page)

        self.form = self.PageChooserForm(instance=self.test_instance)
        self.page_chooser_panel = self.my_page_chooser_panel.get_bound_panel(
            instance=self.test_instance, form=self.form, request=self.request
        )

    def test_page_chooser_uses_correct_widget(self):
        self.assertEqual(type(self.form.fields["page"].widget), AdminPageChooser)

    def test_render_js_init(self):
        result = self.page_chooser_panel.render_html()
        expected_js = 'new PageChooser("{id}", {{"modelNames": ["{model}"], "canChooseRoot": false, "userPerms": null, "modalUrl": "/admin/choose-page/", "parentId": {parent}}});'.format(
            id="id_page", model="wagtailcore.page", parent=self.events_index_page.id
        )

        self.assertIn(expected_js, result)

    def test_render_js_init_with_can_choose_root_true(self):
        # construct an alternative page chooser panel object, with can_choose_root=True

        my_page_object_list = ObjectList(
            [PageChooserPanel("page", can_choose_root=True)]
        ).bind_to_model(PageChooserModel)
        my_page_chooser_panel = my_page_object_list.children[0]
        PageChooserForm = my_page_object_list.get_form_class()

        form = PageChooserForm(instance=self.test_instance)
        page_chooser_panel = my_page_chooser_panel.get_bound_panel(
            instance=self.test_instance, form=form, request=self.request
        )
        result = page_chooser_panel.render_html()

        # the canChooseRoot flag on PageChooser should now be true
        expected_js = 'new PageChooser("{id}", {{"modelNames": ["{model}"], "canChooseRoot": true, "userPerms": null, "modalUrl": "/admin/choose-page/", "parentId": {parent}}});'.format(
            id="id_page", model="wagtailcore.page", parent=self.events_index_page.id
        )
        self.assertIn(expected_js, result)

    def test_render_html(self):
        result = self.page_chooser_panel.render_html()
        self.assertIn('<div class="help">help text</div>', result)
        self.assertIn(
            '<div class="chooser__title" data-chooser-title id="id_page-title">Christmas</div>',
            result,
        )
        self.assertIn(
            '<a href="/admin/pages/%d/edit/" aria-describedby="id_page-title" class="edit-link button button-small button-secondary" target="_blank" rel="noreferrer">Edit this page</a>'
            % self.christmas_page.id,
            result,
        )

    def test_render_as_empty_field(self):
        test_instance = PageChooserModel()
        form = self.PageChooserForm(instance=test_instance)
        page_chooser_panel = self.my_page_chooser_panel.get_bound_panel(
            instance=test_instance, form=form, request=self.request
        )
        result = page_chooser_panel.render_html()

        self.assertIn('<div class="help">help text</div>', result)
        self.assertIn(
            '<div class="chooser__title" data-chooser-title id="id_page-title"></div>',
            result,
        )
        self.assertIn("Choose a page", result)

    def test_render_error(self):
        form = self.PageChooserForm({"page": ""}, instance=self.test_instance)
        self.assertFalse(form.is_valid())

        page_chooser_panel = self.my_page_chooser_panel.get_bound_panel(
            instance=self.test_instance, form=form, request=self.request
        )
        self.assertIn("error-message", page_chooser_panel.render_html())

    def test_override_page_type(self):
        # Model has a foreign key to Page, but we specify EventPage in the PageChooserPanel
        # to restrict the chooser to that page type
        my_page_object_list = ObjectList(
            [PageChooserPanel("page", "tests.EventPage")]
        ).bind_to_model(EventPageChooserModel)
        my_page_chooser_panel = my_page_object_list.children[0]
        PageChooserForm = my_page_object_list.get_form_class()
        form = PageChooserForm(instance=self.test_instance)
        page_chooser_panel = my_page_chooser_panel.get_bound_panel(
            instance=self.test_instance, form=form, request=self.request
        )

        result = page_chooser_panel.render_html()
        expected_js = 'new PageChooser("{id}", {{"modelNames": ["{model}"], "canChooseRoot": false, "userPerms": null, "modalUrl": "/admin/choose-page/", "parentId": {parent}}});'.format(
            id="id_page", model="tests.eventpage", parent=self.events_index_page.id
        )

        self.assertIn(expected_js, result)

    def test_autodetect_page_type(self):
        # Model has a foreign key to EventPage, which we want to autodetect
        # instead of specifying the page type in PageChooserPanel
        my_page_object_list = ObjectList([PageChooserPanel("page")]).bind_to_model(
            EventPageChooserModel,
        )
        my_page_chooser_panel = my_page_object_list.children[0]
        PageChooserForm = my_page_object_list.get_form_class()
        form = PageChooserForm(instance=self.test_instance)
        page_chooser_panel = my_page_chooser_panel.get_bound_panel(
            instance=self.test_instance, form=form, request=self.request
        )

        result = page_chooser_panel.render_html()
        expected_js = 'new PageChooser("{id}", {{"modelNames": ["{model}"], "canChooseRoot": false, "userPerms": null, "modalUrl": "/admin/choose-page/", "parentId": {parent}}});'.format(
            id="id_page", model="tests.eventpage", parent=self.events_index_page.id
        )

        self.assertIn(expected_js, result)

    def test_target_models(self):
        panel = PageChooserPanel("page", "wagtailcore.site").bind_to_model(
            PageChooserModel
        )
        widget = panel.get_form_options()["widgets"]["page"]
        self.assertEqual(widget.target_models, [Site])

    def test_target_models_malformed_type(self):
        panel = PageChooserPanel("page", "snowman").bind_to_model(PageChooserModel)
        self.assertRaises(ImproperlyConfigured, panel.get_form_options)

    def test_target_models_nonexistent_type(self):
        panel = PageChooserPanel("page", "snowman.lorry").bind_to_model(
            PageChooserModel
        )
        self.assertRaises(ImproperlyConfigured, panel.get_form_options)


class TestInlinePanel(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.request = RequestFactory().get("/")
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user

    def test_render(self):
        """
        Check that the inline panel renders the panels set on the model
        when no 'panels' parameter is passed in the InlinePanel definition
        """
        speaker_object_list = ObjectList(
            [
                InlinePanel(
                    "speakers", label="Speakers", classname="classname-for-speakers"
                )
            ]
        ).bind_to_model(EventPage)
        EventPageForm = speaker_object_list.get_form_class()

        # SpeakerInlinePanel should instruct the form class to include a 'speakers' formset
        self.assertEqual(["speakers"], list(EventPageForm.formsets.keys()))

        event_page = EventPage.objects.get(slug="christmas")

        form = EventPageForm(instance=event_page)
        panel = speaker_object_list.get_bound_panel(
            instance=event_page, form=form, request=self.request
        )

        result = panel.render_html()

        # FIXME: reinstate when we pass classnames to the template again
        # self.assertIn('<li class="object classname-for-speakers">', result)
        self.assertIn(
            '<label class="w-field__label" for="id_speakers-0-first_name" id="id_speakers-0-first_name-label">',
            result,
        )
        self.assertIn('value="Father"', result)
        self.assertIn(
            '<label class="w-field__label" for="id_speakers-0-last_name" id="id_speakers-0-last_name-label">',
            result,
        )
        self.assertIn(
            '<label class="w-field__label" for="id_speakers-0-image" id="id_speakers-0-image-label">',
            result,
        )
        self.assertIn("Choose an image", result)

        # rendered panel must also contain hidden fields for id, DELETE and ORDER
        self.assertTagInHTML(
            '<input id="id_speakers-0-id" name="speakers-0-id" type="hidden">',
            result,
            allow_extra_attrs=True,
        )
        self.assertTagInHTML(
            '<input id="id_speakers-0-DELETE" name="speakers-0-DELETE" type="hidden">',
            result,
            allow_extra_attrs=True,
        )
        self.assertTagInHTML(
            '<input id="id_speakers-0-ORDER" name="speakers-0-ORDER" type="hidden">',
            result,
            allow_extra_attrs=True,
        )

        # rendered panel must contain maintenance form for the formset
        self.assertTagInHTML(
            '<input id="id_speakers-TOTAL_FORMS" name="speakers-TOTAL_FORMS" type="hidden">',
            result,
            allow_extra_attrs=True,
        )

        # rendered panel must include the JS initializer
        self.assertIn("var panel = new InlinePanel({", result)

    def test_render_with_panel_overrides(self):
        """
        Check that inline panel renders the panels listed in the InlinePanel definition
        where one is specified
        """
        speaker_object_list = ObjectList(
            [
                InlinePanel(
                    "speakers",
                    label="Speakers",
                    panels=[
                        FieldPanel("first_name", widget=forms.Textarea),
                        FieldPanel("image"),
                    ],
                ),
            ]
        ).bind_to_model(EventPage)
        speaker_inline_panel = speaker_object_list.children[0]
        EventPageForm = speaker_object_list.get_form_class()

        # speaker_inline_panel should instruct the form class to include a 'speakers' formset
        self.assertEqual(["speakers"], list(EventPageForm.formsets.keys()))

        event_page = EventPage.objects.get(slug="christmas")

        form = EventPageForm(instance=event_page)
        panel = speaker_inline_panel.get_bound_panel(
            instance=event_page, form=form, request=self.request
        )

        result = panel.render_html()

        # rendered panel should contain first_name rendered as a text area, but no last_name field
        self.assertIn(
            '<label class="w-field__label" for="id_speakers-0-first_name" id="id_speakers-0-first_name-label">',
            result,
        )
        self.assertIn("Father</textarea>", result)
        self.assertNotIn(
            '<label class="w-field__label" for="id_speakers-0-last_name" id="id_speakers-0-last_name-label">',
            result,
        )

        # test for #338: surname field should not be rendered as a 'stray' label-less field
        self.assertTagInHTML(
            '<input id="id_speakers-0-last_name">',
            result,
            count=0,
            allow_extra_attrs=True,
        )

        self.assertIn(
            '<label class="w-field__label" for="id_speakers-0-image" id="id_speakers-0-image-label">',
            result,
        )
        self.assertIn("Choose an image", result)

        # rendered panel must also contain hidden fields for id, DELETE and ORDER
        self.assertTagInHTML(
            '<input id="id_speakers-0-id" name="speakers-0-id" type="hidden">',
            result,
            allow_extra_attrs=True,
        )
        self.assertTagInHTML(
            '<input id="id_speakers-0-DELETE" name="speakers-0-DELETE" type="hidden">',
            result,
            allow_extra_attrs=True,
        )
        self.assertTagInHTML(
            '<input id="id_speakers-0-ORDER" name="speakers-0-ORDER" type="hidden">',
            result,
            allow_extra_attrs=True,
        )

        # rendered panel must contain maintenance form for the formset
        self.assertTagInHTML(
            '<input id="id_speakers-TOTAL_FORMS" name="speakers-TOTAL_FORMS" type="hidden">',
            result,
            allow_extra_attrs=True,
        )

        # render_js_init must provide the JS initializer
        self.assertIn("var panel = new InlinePanel({", panel.render_html())

    @override_settings(USE_L10N=True, USE_THOUSAND_SEPARATOR=True)
    def test_no_thousand_separators_in_js(self):
        """
        Test that the USE_THOUSAND_SEPARATOR setting does not screw up the rendering of numbers
        (specifically maxForms=1000) in the JS initializer:
        https://github.com/wagtail/wagtail/pull/2699
        https://github.com/wagtail/wagtail/issues/3227
        """
        speaker_object_list = ObjectList(
            [
                InlinePanel(
                    "speakers",
                    label="Speakers",
                    panels=[
                        FieldPanel("first_name", widget=forms.Textarea),
                        FieldPanel("image"),
                    ],
                ),
            ]
        ).bind_to_model(EventPage)
        speaker_inline_panel = speaker_object_list.children[0]
        EventPageForm = speaker_object_list.get_form_class()
        event_page = EventPage.objects.get(slug="christmas")
        form = EventPageForm(instance=event_page)
        panel = speaker_inline_panel.get_bound_panel(
            instance=event_page, form=form, request=self.request
        )

        self.assertIn("maxForms: 1000", panel.render_html())

    def test_invalid_inlinepanel_declaration(self):
        with self.ignore_deprecation_warnings():
            self.assertRaises(TypeError, lambda: InlinePanel(label="Speakers"))
            self.assertRaises(
                TypeError,
                lambda: InlinePanel(
                    EventPage, "speakers", label="Speakers", bacon="chunky"
                ),
            )


class TestInlinePanelGetComparison(TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.request = RequestFactory().get("/")
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user

    def test_get_comparison(self):
        # Test whether the InlinePanel passes it's label in get_comparison

        page = Page.objects.get(id=4).specific
        comparison = (
            page.get_edit_handler()
            .bind_to(instance=page, request=self.request)
            .get_comparison()
        )

        comparison = [comp(page, page) for comp in comparison]
        field_labels = [comp.field_label() for comp in comparison]
        self.assertIn("Speakers", field_labels)


class TestInlinePanelRelatedModelPanelConfigChecks(TestCase):
    def setUp(self):
        self.original_panels = EventPageSpeaker.panels
        delattr(EventPageSpeaker, "panels")

        def get_checks_result():
            # run checks only with the 'panels' tag
            checks_result = checks.run_checks(tags=["panels"])
            return [
                warning for warning in checks_result if warning.obj == EventPageSpeaker
            ]

        self.warning_id = "wagtailadmin.W002"
        self.get_checks_result = get_checks_result

    def tearDown(self):
        EventPageSpeaker.panels = self.original_panels

    def test_page_with_inline_model_with_tabbed_panel_only(self):
        """Test that checks will warn against setting single tabbed panel on InlinePanel model"""

        EventPageSpeaker.settings_panels = [
            FieldPanel("first_name"),
            FieldPanel("last_name"),
        ]

        warning = checks.Warning(
            "EventPageSpeaker.settings_panels will have no effect on InlinePanel model editing",
            hint="""Ensure that EventPageSpeaker uses `panels` instead of `settings_panels`.
There are no tabs on non-Page model editing within InlinePanels.""",
            obj=EventPageSpeaker,
            id=self.warning_id,
        )

        checks_results = self.get_checks_result()

        self.assertIn(warning, checks_results)

        delattr(EventPageSpeaker, "settings_panels")

    def test_page_with_inline_model_with_two_tabbed_panels(self):
        """Test that checks will warn against multiple tabbed panels on InlinePanel models"""

        EventPageSpeaker.content_panels = [FieldPanel("first_name")]
        EventPageSpeaker.promote_panels = [FieldPanel("last_name")]

        warning_1 = checks.Warning(
            "EventPageSpeaker.content_panels will have no effect on InlinePanel model editing",
            hint="""Ensure that EventPageSpeaker uses `panels` instead of `content_panels`.
There are no tabs on non-Page model editing within InlinePanels.""",
            obj=EventPageSpeaker,
            id=self.warning_id,
        )
        warning_2 = checks.Warning(
            "EventPageSpeaker.promote_panels will have no effect on InlinePanel model editing",
            hint="""Ensure that EventPageSpeaker uses `panels` instead of `promote_panels`.
There are no tabs on non-Page model editing within InlinePanels.""",
            obj=EventPageSpeaker,
            id=self.warning_id,
        )

        checks_results = self.get_checks_result()

        self.assertIn(warning_1, checks_results)
        self.assertIn(warning_2, checks_results)

        delattr(EventPageSpeaker, "content_panels")
        delattr(EventPageSpeaker, "promote_panels")

    def test_page_with_inline_model_with_edit_handler(self):
        """Checks should NOT warn if InlinePanel models use tabbed panels AND edit_handler"""

        EventPageSpeaker.content_panels = [FieldPanel("first_name")]
        EventPageSpeaker.edit_handler = TabbedInterface(
            [ObjectList([FieldPanel("last_name")], heading="test")]
        )

        # should not be any errors
        self.assertEqual(self.get_checks_result(), [])

        # clean up for future checks
        delattr(EventPageSpeaker, "edit_handler")
        delattr(EventPageSpeaker, "content_panels")


class TestCommentPanel(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.commenting_user = get_user_model().objects.get(pk=7)
        self.other_user = get_user_model().objects.get(pk=6)
        self.request = RequestFactory().get("/")
        self.request.user = self.commenting_user

        unbound_object_list = ObjectList([CommentPanel()])
        self.object_list = unbound_object_list.bind_to_model(EventPage)
        self.tabbed_interface = TabbedInterface([unbound_object_list]).bind_to_model(
            EventPage
        )

        self.EventPageForm = self.object_list.get_form_class()
        self.event_page = EventPage.objects.get(slug="christmas")
        self.comment = Comment.objects.create(
            page=self.event_page,
            text="test",
            user=self.other_user,
            contentpath="test_contentpath",
        )
        self.reply_1 = CommentReply.objects.create(
            comment=self.comment, text="reply_1", user=self.other_user
        )
        self.reply_2 = CommentReply.objects.create(
            comment=self.comment, text="reply_2", user=self.commenting_user
        )

    def test_comments_toggle_enabled(self):
        """
        Test that the comments toggle is enabled for a TabbedInterface containing CommentPanel, and disabled otherwise
        """
        form_class = self.tabbed_interface.get_form_class()
        form = form_class()
        self.assertTrue(form.show_comments_toggle)

        tabbed_interface_without_content_panel = TabbedInterface(
            [ObjectList(self.event_page.content_panels)]
        ).bind_to_model(EventPage)
        form_class = tabbed_interface_without_content_panel.get_form_class()
        form = form_class()
        self.assertFalse(form.show_comments_toggle)

    @override_settings(WAGTAILADMIN_COMMENTS_ENABLED=False)
    def test_comments_disabled_setting(self):
        """
        Test that the comment panel is missing if WAGTAILADMIN_COMMENTS_ENABLED=False
        """
        self.assertFalse(
            any(isinstance(panel, CommentPanel) for panel in Page.settings_panels)
        )
        form_class = Page.get_edit_handler().get_form_class()
        form = form_class()
        self.assertFalse(form.show_comments_toggle)

    def test_comments_enabled_setting(self):
        """
        Test that the comment panel is present by default
        """
        self.assertTrue(
            any(isinstance(panel, CommentPanel) for panel in Page.settings_panels)
        )
        form_class = Page.get_edit_handler().get_form_class()
        form = form_class()
        self.assertTrue(form.show_comments_toggle)

    def test_context(self):
        """
        Test that the context contains the data about existing comments necessary to initialize the commenting app
        """
        form = self.EventPageForm(instance=self.event_page)
        panel = self.object_list.get_bound_panel(
            request=self.request, instance=self.event_page, form=form
        ).children[0]
        data = panel.get_context_data()["comments_data"]

        self.assertEqual(data["user"], self.commenting_user.pk)

        self.assertEqual(len(data["comments"]), 1)
        self.assertEqual(data["comments"][0]["user"], self.comment.user.pk)

        self.assertEqual(len(data["comments"][0]["replies"]), 2)
        self.assertEqual(
            data["comments"][0]["replies"][0]["user"], self.reply_1.user.pk
        )
        self.assertEqual(
            data["comments"][0]["replies"][1]["user"], self.reply_2.user.pk
        )

        self.assertIn(str(self.commenting_user.pk), data["authors"])
        self.assertIn(str(self.other_user.pk), data["authors"])

        try:
            json_script(data, "comments-data")
        except TypeError:
            self.fail(
                "Failed to serialize comments data. This is likely due to a custom user model using an unsupported field."
            )

    def test_form(self):
        """
        Check that the form has the comments/replies formsets, and that the
        user has been set on each CommentForm/CommentReplyForm instance
        """
        form = self.EventPageForm(
            instance=self.event_page, for_user=self.commenting_user
        )

        self.assertIn("comments", form.formsets)

        comments_formset = form.formsets["comments"]
        self.assertEqual(len(comments_formset.forms), 1)
        self.assertEqual(comments_formset.forms[0].for_user, self.commenting_user)

        replies_formset = comments_formset.forms[0].formsets["replies"]
        self.assertEqual(len(replies_formset.forms), 2)
        self.assertEqual(replies_formset.forms[0].for_user, self.commenting_user)

    def test_comment_form_validation(self):

        form = self.EventPageForm(
            {
                "comments-TOTAL_FORMS": 2,
                "comments-INITIAL_FORMS": 1,
                "comments-MIN_NUM_FORMS": 0,
                "comments-MAX_NUM_FORMS": 1000,
                "comments-0-id": self.comment.pk,
                "comments-0-text": "edited text",  # Try to edit an existing comment from another user
                "comments-0-contentpath": self.comment.contentpath,
                "comments-0-replies-TOTAL_FORMS": 0,
                "comments-0-replies-INITIAL_FORMS": 0,
                "comments-0-replies-MIN_NUM_FORMS": 0,
                "comments-0-replies-MAX_NUM_FORMS": 1000,
                "comments-1-id": "",
                "comments-1-text": "new comment",  # Add a new comment
                "comments-1-contentpath": "new.path",
                "comments-1-replies-TOTAL_FORMS": 0,
                "comments-1-replies-INITIAL_FORMS": 0,
                "comments-1-replies-MIN_NUM_FORMS": 0,
                "comments-1-replies-MAX_NUM_FORMS": 1000,
            },
            instance=self.event_page,
            for_user=self.commenting_user,
        )

        comment_form = form.formsets["comments"].forms[0]
        self.assertFalse(comment_form.is_valid())
        # The existing comment was from another user, so should not be editable

        comment_form = form.formsets["comments"].forms[1]
        self.assertTrue(comment_form.is_valid())
        self.assertEqual(comment_form.instance.user, self.commenting_user)
        # The commenting user should be able to add a new comment, and the new comment's user should be set to request.user

        form = self.EventPageForm(
            {
                "comments-TOTAL_FORMS": 1,
                "comments-INITIAL_FORMS": 1,
                "comments-MIN_NUM_FORMS": 0,
                "comments-MAX_NUM_FORMS": 1000,
                "comments-0-id": self.comment.pk,
                "comments-0-text": self.comment.text,
                "comments-0-contentpath": self.comment.contentpath,
                "comments-0-DELETE": 1,  # Try to delete a comment from another user
                "comments-0-replies-TOTAL_FORMS": 0,
                "comments-0-replies-INITIAL_FORMS": 0,
                "comments-0-replies-MIN_NUM_FORMS": 0,
                "comments-0-replies-MAX_NUM_FORMS": 1000,
            },
            instance=self.event_page,
            for_user=self.commenting_user,
        )

        comment_form = form.formsets["comments"].forms[0]
        self.assertFalse(comment_form.is_valid())
        # Users cannot delete comments from other users

    def test_users_can_edit_comment_positions(self):
        form = self.EventPageForm(
            {
                "comments-TOTAL_FORMS": 1,
                "comments-INITIAL_FORMS": 1,
                "comments-MIN_NUM_FORMS": 0,
                "comments-MAX_NUM_FORMS": 1000,
                "comments-0-id": self.comment.pk,
                "comments-0-text": self.comment.text,
                "comments-0-contentpath": self.comment.contentpath,
                "comments-0-position": "a_new_position",  # Try to change the position of a comment
                "comments-0-DELETE": 0,
                "comments-0-replies-TOTAL_FORMS": 0,
                "comments-0-replies-INITIAL_FORMS": 0,
                "comments-0-replies-MIN_NUM_FORMS": 0,
                "comments-0-replies-MAX_NUM_FORMS": 1000,
            },
            instance=self.event_page,
            for_user=self.commenting_user,
        )

        comment_form = form.formsets["comments"].forms[0]
        self.assertTrue(comment_form.is_valid())
        # Users can change the positions of other users' comments within a field
        # eg by editing a rich text field

    @freeze_time("2017-01-01 12:00:00")
    def test_comment_resolve(self):
        form = self.EventPageForm(
            {
                "comments-TOTAL_FORMS": 1,
                "comments-INITIAL_FORMS": 1,
                "comments-MIN_NUM_FORMS": 0,
                "comments-MAX_NUM_FORMS": 1000,
                "comments-0-id": self.comment.pk,
                "comments-0-text": self.comment.text,
                "comments-0-contentpath": self.comment.contentpath,
                "comments-0-resolved": 1,
                "comments-0-replies-TOTAL_FORMS": 0,
                "comments-0-replies-INITIAL_FORMS": 0,
                "comments-0-replies-MIN_NUM_FORMS": 0,
                "comments-0-replies-MAX_NUM_FORMS": 1000,
            },
            instance=self.event_page,
            for_user=self.commenting_user,
        )
        comment_form = form.formsets["comments"].forms[0]
        self.assertTrue(comment_form.is_valid())
        comment_form.save()
        resolved_comment = Comment.objects.get(pk=self.comment.pk)
        self.assertEqual(resolved_comment.resolved_by, self.commenting_user)

        if settings.USE_TZ:
            self.assertEqual(
                resolved_comment.resolved_at, datetime(2017, 1, 1, 12, 0, 0, tzinfo=utc)
            )
        else:
            self.assertEqual(
                resolved_comment.resolved_at, datetime(2017, 1, 1, 12, 0, 0)
            )

    def test_comment_reply_form_validation(self):

        form = self.EventPageForm(
            {
                "comments-TOTAL_FORMS": 1,
                "comments-INITIAL_FORMS": 1,
                "comments-MIN_NUM_FORMS": 0,
                "comments-MAX_NUM_FORMS": 1000,
                "comments-0-id": self.comment.pk,
                "comments-0-text": self.comment.text,
                "comments-0-contentpath": self.comment.contentpath,
                "comments-0-replies-TOTAL_FORMS": 3,
                "comments-0-replies-INITIAL_FORMS": 2,
                "comments-0-replies-MIN_NUM_FORMS": 0,
                "comments-0-replies-MAX_NUM_FORMS": 1000,
                "comments-0-replies-0-id": self.reply_1.pk,
                "comments-0-replies-0-text": "edited_text",  # Try to edit someone else's reply
                "comments-0-replies-1-id": self.reply_2.pk,
                "comments-0-replies-1-text": "Edited text 2",  # Try to edit own reply
                "comments-0-replies-2-id": "",  # Add new reply
                "comments-0-replies-2-text": "New reply",
            },
            instance=self.event_page,
            for_user=self.commenting_user,
        )

        comment_form = form.formsets["comments"].forms[0]

        reply_forms = comment_form.formsets["replies"].forms

        self.assertFalse(reply_forms[0].is_valid())
        # The existing reply was from another user, so should not be editable

        self.assertTrue(reply_forms[1].is_valid())
        # The existing reply was from the same user, so should be editable

        self.assertTrue(reply_forms[2].is_valid())
        self.assertEqual(reply_forms[2].instance.user, self.commenting_user)
        # Should be able to add new reply, and user should be set correctly

        form = self.EventPageForm(
            {
                "comments-TOTAL_FORMS": 1,
                "comments-INITIAL_FORMS": 1,
                "comments-MIN_NUM_FORMS": 0,
                "comments-MAX_NUM_FORMS": 1000,
                "comments-0-id": self.comment.pk,
                "comments-0-text": self.comment.text,
                "comments-0-contentpath": self.comment.contentpath,
                "comments-0-replies-TOTAL_FORMS": 2,
                "comments-0-replies-INITIAL_FORMS": 2,
                "comments-0-replies-MIN_NUM_FORMS": 0,
                "comments-0-replies-MAX_NUM_FORMS": 1000,
                "comments-0-replies-0-id": self.reply_1.pk,
                "comments-0-replies-0-text": self.reply_1.text,
                "comments-0-replies-0-DELETE": 1,  # Try to delete someone else's reply
                "comments-0-replies-1-id": self.reply_2.pk,
                "comments-0-replies-1-text": "Edited text 2",
                "comments-0-replies-1-DELETE": 1,  # Try to delete own reply
            },
            instance=self.event_page,
            for_user=self.commenting_user,
        )

        comment_form = form.formsets["comments"].forms[0]

        reply_forms = comment_form.formsets["replies"].forms

        self.assertFalse(reply_forms[0].is_valid())
        # The existing reply was from another user, so should not be deletable

        self.assertTrue(reply_forms[1].is_valid())
        # The existing reply was from the same user, so should be deletable


class TestPublishingPanel(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.user = self.login()

        unbound_object_list = ObjectList([PublishingPanel()])
        self.object_list = unbound_object_list.bind_to_model(EventPage)
        self.tabbed_interface = TabbedInterface([unbound_object_list]).bind_to_model(
            EventPage
        )

        self.EventPageForm = self.object_list.get_form_class()
        self.event_page = EventPage.objects.get(slug="christmas")

    def test_schedule_publishing_toggle_toggle_shown(self):
        """
        Test that the schedule publishing toggle is shown for a TabbedInterface containing PublishingPanel, and disabled otherwise
        """
        form_class = self.tabbed_interface.get_form_class()
        form = form_class()
        self.assertTrue(form.show_schedule_publishing_toggle)

        tabbed_interface_without_publishing_panel = TabbedInterface(
            [ObjectList(self.event_page.content_panels)]
        ).bind_to_model(EventPage)
        form_class = tabbed_interface_without_publishing_panel.get_form_class()
        form = form_class()
        self.assertFalse(form.show_schedule_publishing_toggle)

    def test_publishing_panel_shown_by_default(self):
        """
        Test that the publishing panel is present by default
        """
        self.assertTrue(
            any(isinstance(panel, PublishingPanel) for panel in Page.settings_panels)
        )
        form_class = Page.get_edit_handler().get_form_class()
        form = form_class()
        self.assertTrue(form.show_schedule_publishing_toggle)

    def test_form(self):
        """
        Check that the form has the scheduled publishing fields
        """
        form = self.EventPageForm(instance=self.event_page, for_user=self.user)

        self.assertIn("go_live_at", form.base_fields)
        self.assertIn("expire_at", form.base_fields)


class TestMultipleChooserPanel(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Login
        self.user = self.login()

    def test_can_render_panel(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "gallerypage", self.root_page.id),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="gallery_images-TOTAL_FORMS"')
        self.assertContains(response, 'chooserFieldName: "image"')
