from datetime import date, datetime
from functools import wraps
from unittest import mock

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core import checks
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.test import RequestFactory, TestCase, override_settings
from django.utils.html import json_script
from freezegun import freeze_time
from pytz import utc

from wagtail.admin.edit_handlers import (
    CommentPanel, FieldPanel, FieldRowPanel, InlinePanel, ObjectList, PageChooserPanel,
    RichTextFieldPanel, TabbedInterface, extract_panel_definitions_from_model_class,
    get_form_for_model)
from wagtail.admin.forms import WagtailAdminModelForm, WagtailAdminPageForm
from wagtail.admin.rich_text import DraftailRichTextArea
from wagtail.admin.widgets import AdminAutoHeightTextInput, AdminDateInput, AdminPageChooser
from wagtail.core.models import Comment, CommentReply, Page, Site
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.tests.testapp.forms import ValidatedPageForm
from wagtail.tests.testapp.models import (
    EventPage, EventPageChooserModel, EventPageSpeaker, PageChooserModel, RestaurantPage,
    RestaurantTag, SimplePage, ValidatedPage)
from wagtail.tests.utils import WagtailTestUtils


class TestGetFormForModel(TestCase):
    def test_get_form_without_model(self):
        edit_handler = ObjectList()
        with self.assertRaisesMessage(
                AttributeError,
                'ObjectList is not bound to a model yet. '
                'Use `.bind_to(model=model)` before using this method.'):
            edit_handler.get_form_class()

    def test_get_form_for_model(self):
        EventPageForm = get_form_for_model(EventPage, form_class=WagtailAdminPageForm)
        form = EventPageForm()

        # form should be a subclass of WagtailAdminModelForm
        self.assertTrue(issubclass(EventPageForm, WagtailAdminModelForm))
        # form should contain a title field (from the base Page)
        self.assertEqual(type(form.fields['title']), forms.CharField)
        # and 'date_from' from EventPage
        self.assertEqual(type(form.fields['date_from']), forms.DateField)
        # the widget should be overridden with AdminDateInput as per FORM_FIELD_OVERRIDES
        self.assertEqual(type(form.fields['date_from'].widget), AdminDateInput)

        # treebeard's 'path' field should be excluded
        self.assertNotIn('path', form.fields)

        # all child relations become formsets by default
        self.assertIn('speakers', form.formsets)
        self.assertIn('related_links', form.formsets)

    def test_direct_form_field_overrides(self):
        # Test that field overrides defined through DIRECT_FORM_FIELD_OVERRIDES
        # are applied

        SimplePageForm = get_form_for_model(SimplePage, form_class=WagtailAdminPageForm)
        simple_form = SimplePageForm()
        # plain TextFields should use AdminAutoHeightTextInput as the widget
        self.assertEqual(type(simple_form.fields['content'].widget), AdminAutoHeightTextInput)

        # This override should NOT be applied to subclasses of TextField such as
        # RichTextField - they should retain their default widgets
        EventPageForm = get_form_for_model(EventPage, form_class=WagtailAdminPageForm)
        event_form = EventPageForm()
        self.assertEqual(type(event_form.fields['body'].widget), DraftailRichTextArea)

    def test_get_form_for_model_with_specific_fields(self):
        EventPageForm = get_form_for_model(
            EventPage, form_class=WagtailAdminPageForm, fields=['date_from'],
            formsets=['speakers'])
        form = EventPageForm()

        # form should contain date_from but not title
        self.assertEqual(type(form.fields['date_from']), forms.DateField)
        self.assertEqual(type(form.fields['date_from'].widget), AdminDateInput)
        self.assertNotIn('title', form.fields)

        # formsets should include speakers but not related_links
        self.assertIn('speakers', form.formsets)
        self.assertNotIn('related_links', form.formsets)

    def test_get_form_for_model_with_excluded_fields(self):
        EventPageForm = get_form_for_model(
            EventPage, form_class=WagtailAdminPageForm,
            exclude=['title'], exclude_formsets=['related_links'])
        form = EventPageForm()

        # form should contain date_from but not title
        self.assertEqual(type(form.fields['date_from']), forms.DateField)
        self.assertEqual(type(form.fields['date_from'].widget), AdminDateInput)
        self.assertNotIn('title', form.fields)

        # 'path' is not excluded any more, as the excluded fields were overridden
        self.assertIn('path', form.fields)

        # formsets should include speakers but not related_links
        self.assertIn('speakers', form.formsets)
        self.assertNotIn('related_links', form.formsets)

    def test_get_form_for_model_with_widget_overides_by_class(self):
        EventPageForm = get_form_for_model(
            EventPage, form_class=WagtailAdminPageForm,
            widgets={'date_from': forms.PasswordInput})
        form = EventPageForm()

        self.assertEqual(type(form.fields['date_from']), forms.DateField)
        self.assertEqual(type(form.fields['date_from'].widget), forms.PasswordInput)

    def test_get_form_for_model_with_widget_overides_by_instance(self):
        EventPageForm = get_form_for_model(
            EventPage, form_class=WagtailAdminPageForm,
            widgets={'date_from': forms.PasswordInput()})
        form = EventPageForm()

        self.assertEqual(type(form.fields['date_from']), forms.DateField)
        self.assertEqual(type(form.fields['date_from'].widget), forms.PasswordInput)

    def test_tag_widget_is_passed_tag_model(self):
        RestaurantPageForm = get_form_for_model(
            RestaurantPage, form_class=WagtailAdminPageForm
        )
        form_html = RestaurantPageForm().as_p()
        self.assertIn('/admin/tag\\u002Dautocomplete/tests/restauranttag/', form_html)

        # widget should pick up the free_tagging=False attribute on the tag model
        # and set itself to autocomplete only
        self.assertIn('"autocompleteOnly": true', form_html)

        # Free tagging should also be disabled at the form field validation level
        RestaurantTag.objects.create(name='Italian', slug='italian')
        RestaurantTag.objects.create(name='Indian', slug='indian')

        form = RestaurantPageForm({
            'title': 'Buonasera',
            'slug': 'buonasera',
            'tags': "Italian, delicious",
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['tags'], ["Italian"])


def clear_edit_handler(page_cls):
    def decorator(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            # Clear any old EditHandlers generated
            page_cls.get_edit_handler.cache_clear()
            try:
                fn(*args, **kwargs)
            finally:
                # Clear the bad EditHandler generated just now
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
            id='wagtailadmin.E001')

        invalid_edit_handler = checks.Error(
            "ValidatedPage.get_edit_handler().get_form_class() does not extend WagtailAdminPageForm",
            hint="Ensure that the EditHandler for ValidatedPage creates a subclass of WagtailAdminPageForm",
            obj=ValidatedPage,
            id='wagtailadmin.E002')

        with mock.patch.object(ValidatedPage, 'base_form_class', new=BadFormClass):
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
        with mock.patch.object(ValidatedPage, 'edit_handler', new=TabbedInterface(), create=True):
            form_class = ValidatedPage.get_edit_handler().get_form_class()
            self.assertTrue(issubclass(form_class, WagtailAdminPageForm))
            errors = ValidatedPage.check()
            self.assertEqual(errors, [])

    @clear_edit_handler(ValidatedPage)
    def test_repr(self):
        edit_handler = ValidatedPage.get_edit_handler()

        handler_handler_repr = repr(edit_handler)

        self.assertIn("model=<class 'wagtail.tests.testapp.models.ValidatedPage'>", handler_handler_repr)
        self.assertIn('instance=None', handler_handler_repr)
        self.assertIn("request=None", handler_handler_repr)
        self.assertIn('form=None', handler_handler_repr)


class TestExtractPanelDefinitionsFromModelClass(TestCase):
    def test_can_extract_panel_property(self):
        # A class with a 'panels' property defined should return that list
        result = extract_panel_definitions_from_model_class(EventPageSpeaker)
        self.assertEqual(len(result), 5)
        self.assertTrue(any([isinstance(panel, ImageChooserPanel) for panel in result]))

    def test_exclude(self):
        panels = extract_panel_definitions_from_model_class(Site, exclude=['hostname'])
        for panel in panels:
            self.assertNotEqual(panel.field_name, 'hostname')

    def test_can_build_panel_list(self):
        # EventPage has no 'panels' definition, so one should be derived from the field list
        panels = extract_panel_definitions_from_model_class(EventPage)

        self.assertTrue(any([
            isinstance(panel, FieldPanel) and panel.field_name == 'date_from'
            for panel in panels
        ]))

        # returned panel types should respect modelfield.get_panel() - used on RichTextField
        self.assertTrue(any([
            isinstance(panel, RichTextFieldPanel) and panel.field_name == 'body'
            for panel in panels
        ]))


class TestTabbedInterface(TestCase):
    def setUp(self):
        self.request = RequestFactory().get('/')
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user

        # a custom tabbed interface for EventPage
        self.event_page_tabbed_interface = TabbedInterface([
            ObjectList([
                FieldPanel('title', widget=forms.Textarea),
                FieldPanel('date_from'),
                FieldPanel('date_to'),
            ], heading='Event details', classname="shiny"),
            ObjectList([
                InlinePanel('speakers', label="Speakers"),
            ], heading='Speakers'),
        ]).bind_to(model=EventPage, request=self.request)

    def test_get_form_class(self):
        EventPageForm = self.event_page_tabbed_interface.get_form_class()
        form = EventPageForm()

        # form must include the 'speakers' formset required by the speakers InlinePanel
        self.assertIn('speakers', form.formsets)

        # form must respect any overridden widgets
        self.assertEqual(type(form.fields['title'].widget), forms.Textarea)

    def test_render(self):
        EventPageForm = self.event_page_tabbed_interface.get_form_class()
        event = EventPage(title='Abergavenny sheepdog trials')
        form = EventPageForm(instance=event)

        tabbed_interface = self.event_page_tabbed_interface.bind_to(
            instance=event,
            form=form,
        )

        result = tabbed_interface.render()

        # result should contain tab buttons
        self.assertIn('<a href="#tab-event-details" class="active" data-tab="event-details">Event details</a>', result)
        self.assertIn('<a href="#tab-speakers" class="" data-tab="speakers">Speakers</a>', result)

        # result should contain tab panels
        self.assertIn('<div class="tab-content">', result)
        self.assertIn('<section id="tab-event-details" class="shiny active" role="tabpanel" aria-labelledby="tab-label-event-details" data-tab="event-details">', result)
        self.assertIn('<section id="tab-speakers" class=" " role="tabpanel" aria-labelledby="tab-label-speakers" data-tab="speakers">', result)

        # result should contain rendered content from descendants
        self.assertIn('Abergavenny sheepdog trials</textarea>', result)

        # this result should not include fields that are not covered by the panel definition
        self.assertNotIn('signup_link', result)

    def test_required_fields(self):
        # required_fields should report the set of form fields to be rendered recursively by children of TabbedInterface
        result = set(self.event_page_tabbed_interface.required_fields())
        self.assertEqual(result, set(['title', 'date_from', 'date_to']))

    def test_render_form_content(self):
        EventPageForm = self.event_page_tabbed_interface.get_form_class()
        event = EventPage(title='Abergavenny sheepdog trials')
        form = EventPageForm(instance=event)

        tabbed_interface = self.event_page_tabbed_interface.bind_to(
            instance=event,
            form=form,
        )

        result = tabbed_interface.render_form_content()
        # rendered output should contain field content as above
        self.assertIn('Abergavenny sheepdog trials</textarea>', result)
        # rendered output should NOT include fields that are in the model but not represented
        # in the panel definition
        self.assertNotIn('signup_link', result)


class TestObjectList(TestCase):
    def setUp(self):
        self.request = RequestFactory().get('/')
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user
        # a custom ObjectList for EventPage
        self.event_page_object_list = ObjectList([
            FieldPanel('title', widget=forms.Textarea),
            FieldPanel('date_from'),
            FieldPanel('date_to'),
            InlinePanel('speakers', label="Speakers"),
        ], heading='Event details', classname="shiny").bind_to(
            model=EventPage, request=self.request)

    def test_get_form_class(self):
        EventPageForm = self.event_page_object_list.get_form_class()
        form = EventPageForm()

        # form must include the 'speakers' formset required by the speakers InlinePanel
        self.assertIn('speakers', form.formsets)

        # form must respect any overridden widgets
        self.assertEqual(type(form.fields['title'].widget), forms.Textarea)

    def test_render(self):
        EventPageForm = self.event_page_object_list.get_form_class()
        event = EventPage(title='Abergavenny sheepdog trials')
        form = EventPageForm(instance=event)

        object_list = self.event_page_object_list.bind_to(
            instance=event,
            form=form,
        )

        result = object_list.render()

        # result should contain ObjectList furniture
        self.assertIn('<ul class="objects">', result)

        # result should contain labels for children
        self.assertInHTML('<label for="id_date_from">Start date</label>', result)

        # result should include help text for children
        self.assertInHTML('<div class="object-help help"> <svg class="icon icon-help default" aria-hidden="true" focusable="false"><use href="#icon-help"></use></svg> Not required if event is on a single day</div>', result)

        # result should contain rendered content from descendants
        self.assertIn('Abergavenny sheepdog trials</textarea>', result)

        # this result should not include fields that are not covered by the panel definition
        self.assertNotIn('signup_link', result)


class TestFieldPanel(TestCase):
    def setUp(self):
        self.request = RequestFactory().get('/')
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user

        self.EventPageForm = get_form_for_model(
            EventPage, form_class=WagtailAdminPageForm, formsets=[])
        self.event = EventPage(title='Abergavenny sheepdog trials',
                               date_from=date(2014, 7, 20), date_to=date(2014, 7, 21))

        self.end_date_panel = (FieldPanel('date_to', classname='full-width')
                               .bind_to(model=EventPage, request=self.request))

    def test_non_model_field(self):
        # defining a FieldPanel for a field which isn't part of a model is OK,
        # because it might be defined on the form instead
        field_panel = FieldPanel('barbecue').bind_to(model=Page)

        # however, accessing db_field will fail
        with self.assertRaises(FieldDoesNotExist):
            field_panel.db_field

    def test_override_heading(self):
        # unless heading is specified in keyword arguments, an edit handler with bound form should take its
        # heading from the bound field label
        bound_panel = self.end_date_panel.bind_to(form=self.EventPageForm())
        self.assertEqual(bound_panel.heading, bound_panel.bound_field.label)

        # if heading is explicitly provided to constructor, that heading should be taken in
        # preference to the field's label
        end_date_panel_with_overridden_heading = (FieldPanel('date_to', classname='full-width', heading="New heading")
                                                  .bind_to(model=EventPage, request=self.request, form=self.EventPageForm()))
        self.assertEqual(end_date_panel_with_overridden_heading.heading, "New heading")

    def test_render_as_object(self):
        form = self.EventPageForm(
            {'title': 'Pontypridd sheepdog trials', 'date_from': '2014-07-20', 'date_to': '2014-07-22'},
            instance=self.event)

        form.is_valid()

        field_panel = self.end_date_panel.bind_to(
            instance=self.event,
            form=form,
        )
        result = field_panel.render_as_object()

        # check that label appears as a legend in the 'object' wrapper,
        # but not as a field label (that would be provided by ObjectList instead)
        self.assertIn('<legend>End date</legend>', result)
        self.assertNotIn('<label for="id_date_to">End date:</label>', result)

        # check that help text is not included (it's provided by ObjectList instead)
        self.assertNotIn('Not required if event is on a single day', result)

        # check that the populated form field is included
        self.assertIn('value="2014-07-22"', result)

        # there should be no errors on this field
        self.assertNotIn('<p class="error-message">', result)

    def test_render_as_field(self):
        form = self.EventPageForm(
            {'title': 'Pontypridd sheepdog trials', 'date_from': '2014-07-20', 'date_to': '2014-07-22'},
            instance=self.event)

        form.is_valid()

        field_panel = self.end_date_panel.bind_to(
            instance=self.event,
            form=form,
        )
        result = field_panel.render_as_field()

        # check that label is output in the 'field' style
        self.assertIn('<label for="id_date_to">End date:</label>', result)
        self.assertNotIn('<legend>End date</legend>', result)

        # check that help text is included
        self.assertIn('Not required if event is on a single day', result)

        # check that the populated form field is included
        self.assertIn('value="2014-07-22"', result)

        # there should be no errors on this field
        self.assertNotIn('<p class="error-message">', result)

    def test_required_fields(self):
        result = self.end_date_panel.required_fields()
        self.assertEqual(result, ['date_to'])

    def test_error_message_is_rendered(self):
        form = self.EventPageForm(
            {'title': 'Pontypridd sheepdog trials', 'date_from': '2014-07-20', 'date_to': '2014-07-33'},
            instance=self.event)

        form.is_valid()

        field_panel = self.end_date_panel.bind_to(
            instance=self.event,
            form=form,
        )
        result = field_panel.render_as_field()

        self.assertIn('<p class="error-message">', result)
        self.assertIn('<span>Enter a valid date.</span>', result)

    def test_repr(self):
        form = self.EventPageForm()
        field_panel = self.end_date_panel.bind_to(
            form=form,
        )

        field_panel_repr = repr(field_panel)

        self.assertIn("model=<class 'wagtail.tests.testapp.models.EventPage'>", field_panel_repr)
        self.assertIn('instance=None', field_panel_repr)
        self.assertIn("request=<WSGIRequest: GET '/'>", field_panel_repr)
        self.assertIn('form=EventPageForm', field_panel_repr)


class TestFieldRowPanel(TestCase):
    def setUp(self):
        self.request = RequestFactory().get('/')
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user

        self.EventPageForm = get_form_for_model(
            EventPage, form_class=WagtailAdminPageForm, formsets=[])
        self.event = EventPage(title='Abergavenny sheepdog trials',
                               date_from=date(2014, 7, 20), date_to=date(2014, 7, 21))

        self.dates_panel = FieldRowPanel([
            FieldPanel('date_from', classname='col4'),
            FieldPanel('date_to', classname='coltwo'),
        ]).bind_to(model=EventPage, request=self.request)

    def test_render_as_object(self):
        form = self.EventPageForm(
            {'title': 'Pontypridd sheepdog trials', 'date_from': '2014-07-20', 'date_to': '2014-07-22'},
            instance=self.event)

        form.is_valid()

        field_panel = self.dates_panel.bind_to(
            instance=self.event,
            form=form,
        )
        result = field_panel.render_as_object()

        # check that the populated form field is included
        self.assertIn('value="2014-07-22"', result)

        # there should be no errors on this field
        self.assertNotIn('<p class="error-message">', result)

    def test_render_as_field(self):
        form = self.EventPageForm(
            {'title': 'Pontypridd sheepdog trials', 'date_from': '2014-07-20', 'date_to': '2014-07-22'},
            instance=self.event)

        form.is_valid()

        field_panel = self.dates_panel.bind_to(
            instance=self.event,
            form=form,
        )
        result = field_panel.render_as_field()

        # check that label is output in the 'field' style
        self.assertIn('<label for="id_date_to">End date:</label>', result)
        self.assertNotIn('<legend>End date</legend>', result)

        # check that help text is included
        self.assertIn('Not required if event is on a single day', result)

        # check that the populated form field is included
        self.assertIn('value="2014-07-22"', result)

        # there should be no errors on this field
        self.assertNotIn('<p class="error-message">', result)

    def test_error_message_is_rendered(self):
        form = self.EventPageForm(
            {'title': 'Pontypridd sheepdog trials', 'date_from': '2014-07-20', 'date_to': '2014-07-33'},
            instance=self.event)

        form.is_valid()

        field_panel = self.dates_panel.bind_to(
            instance=self.event,
            form=form,
        )
        result = field_panel.render_as_field()

        self.assertIn('<p class="error-message">', result)
        self.assertIn('<span>Enter a valid date.</span>', result)

    def test_add_col_when_wrong_in_panel_def(self):
        form = self.EventPageForm(
            {'title': 'Pontypridd sheepdog trials', 'date_from': '2014-07-20', 'date_to': '2014-07-33'},
            instance=self.event)

        form.is_valid()

        field_panel = self.dates_panel.bind_to(
            instance=self.event,
            form=form,
        )

        result = field_panel.render_as_field()

        self.assertIn('<li class="field-col coltwo col6', result)

    def test_added_col_doesnt_change_siblings(self):
        form = self.EventPageForm(
            {'title': 'Pontypridd sheepdog trials', 'date_from': '2014-07-20', 'date_to': '2014-07-33'},
            instance=self.event)

        form.is_valid()

        field_panel = self.dates_panel.bind_to(
            instance=self.event,
            form=form,
        )

        result = field_panel.render_as_field()

        self.assertIn('<li class="field-col col4', result)


class TestFieldRowPanelWithChooser(TestCase):
    def setUp(self):
        self.request = RequestFactory().get('/')
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user

        self.EventPageForm = get_form_for_model(
            EventPage, form_class=WagtailAdminPageForm, formsets=[])
        self.event = EventPage(title='Abergavenny sheepdog trials',
                               date_from=date(2014, 7, 19), date_to=date(2014, 7, 21))

        self.dates_panel = FieldRowPanel([
            FieldPanel('date_from'),
            ImageChooserPanel('feed_image'),
        ]).bind_to(model=EventPage, request=self.request)

    def test_render_as_object(self):
        form = self.EventPageForm(
            {'title': 'Pontypridd sheepdog trials', 'date_from': '2014-07-20', 'date_to': '2014-07-22'},
            instance=self.event)

        form.is_valid()

        field_panel = self.dates_panel.bind_to(
            instance=self.event,
            form=form,
        )
        result = field_panel.render_as_object()

        # check that the populated form field is included
        self.assertIn('value="2014-07-20"', result)

        # there should be no errors on this field
        self.assertNotIn('<p class="error-message">', result)


class TestPageChooserPanel(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.request = RequestFactory().get('/')
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user

        model = PageChooserModel  # a model with a foreign key to Page which we want to render as a page chooser

        # a PageChooserPanel class that works on PageChooserModel's 'page' field
        self.edit_handler = (ObjectList([PageChooserPanel('page')])
                             .bind_to(model=PageChooserModel,
                                      request=self.request))
        self.my_page_chooser_panel = self.edit_handler.children[0]

        # build a form class containing the fields that MyPageChooserPanel wants
        self.PageChooserForm = self.edit_handler.get_form_class()

        # a test instance of PageChooserModel, pointing to the 'christmas' page
        self.christmas_page = Page.objects.get(slug='christmas')
        self.events_index_page = Page.objects.get(slug='events')
        self.test_instance = model.objects.create(page=self.christmas_page)

        self.form = self.PageChooserForm(instance=self.test_instance)
        self.page_chooser_panel = self.my_page_chooser_panel.bind_to(
            instance=self.test_instance, form=self.form)

    def test_page_chooser_uses_correct_widget(self):
        self.assertEqual(type(self.form.fields['page'].widget), AdminPageChooser)

    def test_render_js_init(self):
        result = self.page_chooser_panel.render_as_field()
        expected_js = 'createPageChooser("{id}", {parent}, {{"model_names": ["{model}"], "can_choose_root": false, "user_perms": null}});'.format(
            id="id_page", model="wagtailcore.page", parent=self.events_index_page.id)

        self.assertIn(expected_js, result)

    def test_render_js_init_with_can_choose_root_true(self):
        # construct an alternative page chooser panel object, with can_choose_root=True

        my_page_object_list = ObjectList([
            PageChooserPanel('page', can_choose_root=True)
        ]).bind_to(model=PageChooserModel)
        my_page_chooser_panel = my_page_object_list.children[0]
        PageChooserForm = my_page_object_list.get_form_class()

        form = PageChooserForm(instance=self.test_instance)
        page_chooser_panel = my_page_chooser_panel.bind_to(
            instance=self.test_instance, form=form, request=self.request)
        result = page_chooser_panel.render_as_field()

        # the canChooseRoot flag on createPageChooser should now be true
        expected_js = 'createPageChooser("{id}", {parent}, {{"model_names": ["{model}"], "can_choose_root": true, "user_perms": null}});'.format(
            id="id_page", model="wagtailcore.page", parent=self.events_index_page.id)
        self.assertIn(expected_js, result)

    def test_get_chosen_item(self):
        result = self.page_chooser_panel.get_chosen_item()
        self.assertEqual(result, self.christmas_page)

    def test_render_as_field(self):
        result = self.page_chooser_panel.render_as_field()
        self.assertIn('<p class="help">help text</p>', result)
        self.assertIn('<span class="title">Christmas</span>', result)
        self.assertIn(
            '<a href="/admin/pages/%d/edit/" class="edit-link button button-small button-secondary" target="_blank" rel="noopener noreferrer">'
            'Edit this page</a>' % self.christmas_page.id,
            result)

    def test_render_as_empty_field(self):
        test_instance = PageChooserModel()
        form = self.PageChooserForm(instance=test_instance)
        page_chooser_panel = self.my_page_chooser_panel.bind_to(
            instance=test_instance, form=form, request=self.request)
        result = page_chooser_panel.render_as_field()

        self.assertIn('<p class="help">help text</p>', result)
        self.assertIn('<span class="title"></span>', result)
        self.assertIn('Choose a page', result)

    def test_render_error(self):
        form = self.PageChooserForm({'page': ''}, instance=self.test_instance)
        self.assertFalse(form.is_valid())

        page_chooser_panel = self.my_page_chooser_panel.bind_to(
            instance=self.test_instance, form=form, request=self.request)
        self.assertIn('<span>This field is required.</span>', page_chooser_panel.render_as_field())

    def test_override_page_type(self):
        # Model has a foreign key to Page, but we specify EventPage in the PageChooserPanel
        # to restrict the chooser to that page type
        my_page_object_list = ObjectList([
            PageChooserPanel('page', 'tests.EventPage')
        ]).bind_to(model=EventPageChooserModel)
        my_page_chooser_panel = my_page_object_list.children[0]
        PageChooserForm = my_page_object_list.get_form_class()
        form = PageChooserForm(instance=self.test_instance)
        page_chooser_panel = my_page_chooser_panel.bind_to(
            instance=self.test_instance, form=form, request=self.request)

        result = page_chooser_panel.render_as_field()
        expected_js = 'createPageChooser("{id}", {parent}, {{"model_names": ["{model}"], "can_choose_root": false, "user_perms": null}});'.format(
            id="id_page", model="tests.eventpage", parent=self.events_index_page.id)

        self.assertIn(expected_js, result)

    def test_autodetect_page_type(self):
        # Model has a foreign key to EventPage, which we want to autodetect
        # instead of specifying the page type in PageChooserPanel
        my_page_object_list = (ObjectList([PageChooserPanel('page')])
                               .bind_to(model=EventPageChooserModel,
                                        request=self.request))
        my_page_chooser_panel = my_page_object_list.children[0]
        PageChooserForm = my_page_object_list.get_form_class()
        form = PageChooserForm(instance=self.test_instance)
        page_chooser_panel = my_page_chooser_panel.bind_to(
            instance=self.test_instance, form=form)

        result = page_chooser_panel.render_as_field()
        expected_js = 'createPageChooser("{id}", {parent}, {{"model_names": ["{model}"], "can_choose_root": false, "user_perms": null}});'.format(
            id="id_page", model="tests.eventpage", parent=self.events_index_page.id
        )

        self.assertIn(expected_js, result)

    def test_target_models(self):
        result = PageChooserPanel(
            'page',
            'wagtailcore.site'
        ).bind_to(model=PageChooserModel).target_models()
        self.assertEqual(result, [Site])

    def test_target_models_malformed_type(self):
        result = PageChooserPanel(
            'page',
            'snowman'
        ).bind_to(model=PageChooserModel)
        self.assertRaises(ImproperlyConfigured,
                          result.target_models)

    def test_target_models_nonexistent_type(self):
        result = PageChooserPanel(
            'page',
            'snowman.lorry'
        ).bind_to(model=PageChooserModel)
        self.assertRaises(ImproperlyConfigured,
                          result.target_models)


class TestInlinePanel(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.request = RequestFactory().get('/')
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user

    def test_render(self):
        """
        Check that the inline panel renders the panels set on the model
        when no 'panels' parameter is passed in the InlinePanel definition
        """
        speaker_object_list = ObjectList([
            InlinePanel('speakers', label="Speakers", classname="classname-for-speakers")
        ]).bind_to(model=EventPage, request=self.request)
        EventPageForm = speaker_object_list.get_form_class()

        # SpeakerInlinePanel should instruct the form class to include a 'speakers' formset
        self.assertEqual(['speakers'], list(EventPageForm.formsets.keys()))

        event_page = EventPage.objects.get(slug='christmas')

        form = EventPageForm(instance=event_page)
        panel = speaker_object_list.bind_to(instance=event_page, form=form)

        result = panel.render_as_field()

        self.assertIn('<li class="object classname-for-speakers">', result)
        self.assertIn('<label for="id_speakers-0-first_name">Name:</label>', result)
        self.assertIn('value="Father"', result)
        self.assertIn('<label for="id_speakers-0-last_name">Surname:</label>', result)
        self.assertIn('<label for="id_speakers-0-image">Image:</label>', result)
        self.assertIn('Choose an image', result)

        # rendered panel must also contain hidden fields for id, DELETE and ORDER
        self.assertTagInHTML(
            '<input id="id_speakers-0-id" name="speakers-0-id" type="hidden">',
            result, allow_extra_attrs=True
        )
        self.assertTagInHTML(
            '<input id="id_speakers-0-DELETE" name="speakers-0-DELETE" type="hidden">',
            result, allow_extra_attrs=True
        )
        self.assertTagInHTML(
            '<input id="id_speakers-0-ORDER" name="speakers-0-ORDER" type="hidden">',
            result, allow_extra_attrs=True
        )

        # rendered panel must contain maintenance form for the formset
        self.assertTagInHTML(
            '<input id="id_speakers-TOTAL_FORMS" name="speakers-TOTAL_FORMS" type="hidden">',
            result, allow_extra_attrs=True
        )

        # rendered panel must include the JS initializer
        self.assertIn('var panel = InlinePanel({', result)

    def test_render_with_panel_overrides(self):
        """
        Check that inline panel renders the panels listed in the InlinePanel definition
        where one is specified
        """
        speaker_object_list = ObjectList([
            InlinePanel('speakers', label="Speakers", panels=[
                FieldPanel('first_name', widget=forms.Textarea),
                ImageChooserPanel('image'),
            ]),
        ]).bind_to(model=EventPage, request=self.request)
        speaker_inline_panel = speaker_object_list.children[0]
        EventPageForm = speaker_object_list.get_form_class()

        # speaker_inline_panel should instruct the form class to include a 'speakers' formset
        self.assertEqual(['speakers'], list(EventPageForm.formsets.keys()))

        event_page = EventPage.objects.get(slug='christmas')

        form = EventPageForm(instance=event_page)
        panel = speaker_inline_panel.bind_to(instance=event_page, form=form)

        result = panel.render_as_field()

        # rendered panel should contain first_name rendered as a text area, but no last_name field
        self.assertIn('<label for="id_speakers-0-first_name">Name:</label>', result)
        self.assertIn('Father</textarea>', result)
        self.assertNotIn('<label for="id_speakers-0-last_name">Surname:</label>', result)

        # test for #338: surname field should not be rendered as a 'stray' label-less field
        self.assertTagInHTML('<input id="id_speakers-0-last_name">', result, count=0, allow_extra_attrs=True)

        self.assertIn('<label for="id_speakers-0-image">Image:</label>', result)
        self.assertIn('Choose an image', result)

        # rendered panel must also contain hidden fields for id, DELETE and ORDER
        self.assertTagInHTML(
            '<input id="id_speakers-0-id" name="speakers-0-id" type="hidden">',
            result, allow_extra_attrs=True
        )
        self.assertTagInHTML(
            '<input id="id_speakers-0-DELETE" name="speakers-0-DELETE" type="hidden">',
            result, allow_extra_attrs=True
        )
        self.assertTagInHTML(
            '<input id="id_speakers-0-ORDER" name="speakers-0-ORDER" type="hidden">',
            result, allow_extra_attrs=True
        )

        # rendered panel must contain maintenance form for the formset
        self.assertTagInHTML(
            '<input id="id_speakers-TOTAL_FORMS" name="speakers-TOTAL_FORMS" type="hidden">',
            result, allow_extra_attrs=True
        )

        # render_js_init must provide the JS initializer
        self.assertIn('var panel = InlinePanel({', panel.render_js_init())

    @override_settings(USE_L10N=True, USE_THOUSAND_SEPARATOR=True)
    def test_no_thousand_separators_in_js(self):
        """
        Test that the USE_THOUSAND_SEPARATOR setting does not screw up the rendering of numbers
        (specifically maxForms=1000) in the JS initializer:
        https://github.com/wagtail/wagtail/pull/2699
        https://github.com/wagtail/wagtail/issues/3227
        """
        speaker_object_list = ObjectList([
            InlinePanel('speakers', label="Speakers", panels=[
                FieldPanel('first_name', widget=forms.Textarea),
                ImageChooserPanel('image'),
            ]),
        ]).bind_to(model=EventPage, request=self.request)
        speaker_inline_panel = speaker_object_list.children[0]
        EventPageForm = speaker_object_list.get_form_class()
        event_page = EventPage.objects.get(slug='christmas')
        form = EventPageForm(instance=event_page)
        panel = speaker_inline_panel.bind_to(instance=event_page, form=form)

        self.assertIn('maxForms: 1000', panel.render_js_init())

    def test_invalid_inlinepanel_declaration(self):
        with self.ignore_deprecation_warnings():
            self.assertRaises(TypeError, lambda: InlinePanel(label="Speakers"))
            self.assertRaises(TypeError, lambda: InlinePanel(EventPage, 'speakers', label="Speakers", bacon="chunky"))


class TestInlinePanelRelatedModelPanelConfigChecks(TestCase):

    def setUp(self):
        self.original_panels = EventPageSpeaker.panels
        delattr(EventPageSpeaker, 'panels')

        def get_checks_result():
            # run checks only with the 'panels' tag
            checks_result = checks.run_checks(tags=['panels'])
            return [warning for warning in checks_result if warning.obj == EventPageSpeaker]

        self.warning_id = 'wagtailadmin.W002'
        self.get_checks_result = get_checks_result

    def tearDown(self):
        EventPageSpeaker.panels = self.original_panels

    def test_page_with_inline_model_with_tabbed_panel_only(self):
        """Test that checks will warn against setting single tabbed panel on InlinePanel model"""

        EventPageSpeaker.settings_panels = [FieldPanel('first_name'), FieldPanel('last_name')]

        warning = checks.Warning(
            "EventPageSpeaker.settings_panels will have no effect on InlinePanel model editing",
            hint="""Ensure that EventPageSpeaker uses `panels` instead of `settings_panels`.
There are no tabs on non-Page model editing within InlinePanels.""",
            obj=EventPageSpeaker,
            id=self.warning_id,
        )

        checks_results = self.get_checks_result()

        self.assertIn(warning, checks_results)

        delattr(EventPageSpeaker, 'settings_panels')

    def test_page_with_inline_model_with_two_tabbed_panels(self):
        """Test that checks will warn against multiple tabbed panels on InlinePanel models"""

        EventPageSpeaker.content_panels = [FieldPanel('first_name')]
        EventPageSpeaker.promote_panels = [FieldPanel('last_name')]

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

        delattr(EventPageSpeaker, 'content_panels')
        delattr(EventPageSpeaker, 'promote_panels')

    def test_page_with_inline_model_with_edit_handler(self):
        """Checks should NOT warn if InlinePanel models use tabbed panels AND edit_handler"""

        EventPageSpeaker.content_panels = [FieldPanel('first_name')]
        EventPageSpeaker.edit_handler = TabbedInterface([
            ObjectList([FieldPanel('last_name')], heading='test')
        ])

        # should not be any errors
        self.assertEqual(self.get_checks_result(), [])

        # clean up for future checks
        delattr(EventPageSpeaker, 'edit_handler')
        delattr(EventPageSpeaker, 'content_panels')


class TestCommentPanel(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.commenting_user = get_user_model().objects.get(pk=7)
        self.other_user = get_user_model().objects.get(pk=6)
        self.request = RequestFactory().get('/')
        self.request.user = self.commenting_user
        self.object_list = ObjectList([
            CommentPanel()
        ]).bind_to(model=EventPage, request=self.request)
        self.tabbed_interface = TabbedInterface([self.object_list])
        self.EventPageForm = self.object_list.get_form_class()
        self.event_page = EventPage.objects.get(slug='christmas')
        self.comment = Comment.objects.create(page=self.event_page, text='test', user=self.other_user, contentpath='test_contentpath')
        self.reply_1 = CommentReply.objects.create(comment=self.comment, text='reply_1', user=self.other_user)
        self.reply_2 = CommentReply.objects.create(comment=self.comment, text='reply_2', user=self.commenting_user)

    def test_comments_toggle_enabled(self):
        """
        Test that the comments toggle is enabled for a TabbedInterface containing CommentPanel, and disabled otherwise
        """
        self.assertTrue(self.tabbed_interface.show_comments_toggle)
        self.assertFalse(TabbedInterface([ObjectList(self.event_page.content_panels)]).show_comments_toggle)

    @override_settings(WAGTAILADMIN_COMMENTS_ENABLED=False)
    def test_comments_disabled_setting(self):
        """
        Test that the comment panel is missing if WAGTAILADMIN_COMMENTS_ENABLED=False
        """
        self.assertFalse(any(isinstance(panel, CommentPanel) for panel in Page.settings_panels))
        self.assertFalse(Page.get_edit_handler().show_comments_toggle)

    def test_comments_enabled_setting(self):
        """
        Test that the comment panel is present by default
        """
        self.assertTrue(any(isinstance(panel, CommentPanel) for panel in Page.settings_panels))
        self.assertTrue(Page.get_edit_handler().show_comments_toggle)

    def test_context(self):
        """
        Test that the context contains the data about existing comments necessary to initialize the commenting app
        """
        form = self.EventPageForm(instance=self.event_page)
        panel = self.object_list.bind_to(instance=self.event_page, form=form).children[0]
        data = panel.get_context()['comments_data']

        self.assertEqual(data['user'], self.commenting_user.pk)

        self.assertEqual(len(data['comments']), 1)
        self.assertEqual(data['comments'][0]['user'], self.comment.user.pk)

        self.assertEqual(len(data['comments'][0]['replies']), 2)
        self.assertEqual(data['comments'][0]['replies'][0]['user'], self.reply_1.user.pk)
        self.assertEqual(data['comments'][0]['replies'][1]['user'], self.reply_2.user.pk)

        self.assertIn(str(self.commenting_user.pk), data['authors'])
        self.assertIn(str(self.other_user.pk), data['authors'])

        try:
            json_script(data, 'comments-data')
        except TypeError:
            self.fail("Failed to serialize comments data. This is likely due to a custom user model using an unsupported field.")

    def test_form(self):
        """
        Check that the form has the comments/replies formsets, and that the
        user has been set on each CommentForm/CommentReplyForm subclass
        """
        form = self.EventPageForm(instance=self.event_page)

        self.assertIn('comments', form.formsets)

        comments_formset = form.formsets['comments']
        self.assertEqual(len(comments_formset.forms), 1)
        self.assertEqual(comments_formset.forms[0].user, self.commenting_user)

        replies_formset = comments_formset.forms[0].formsets['replies']
        self.assertEqual(len(replies_formset.forms), 2)
        self.assertEqual(replies_formset.forms[0].user, self.commenting_user)

    def test_comment_form_validation(self):

        form = self.EventPageForm({
            'comments-TOTAL_FORMS': 2,
            'comments-INITIAL_FORMS': 1,
            'comments-MIN_NUM_FORMS': 0,
            'comments-MAX_NUM_FORMS': 1000,
            'comments-0-id': self.comment.pk,
            'comments-0-text': 'edited text',  # Try to edit an existing comment from another user
            'comments-0-contentpath': self.comment.contentpath,
            'comments-0-replies-TOTAL_FORMS': 0,
            'comments-0-replies-INITIAL_FORMS': 0,
            'comments-0-replies-MIN_NUM_FORMS': 0,
            'comments-0-replies-MAX_NUM_FORMS': 1000,
            'comments-1-id': '',
            'comments-1-text': 'new comment',  # Add a new comment
            'comments-1-contentpath': 'new.path',
            'comments-1-replies-TOTAL_FORMS': 0,
            'comments-1-replies-INITIAL_FORMS': 0,
            'comments-1-replies-MIN_NUM_FORMS': 0,
            'comments-1-replies-MAX_NUM_FORMS': 1000,
        },
            instance=self.event_page
        )

        comment_form = form.formsets['comments'].forms[0]
        self.assertFalse(comment_form.is_valid())
        # The existing comment was from another user, so should not be editable

        comment_form = form.formsets['comments'].forms[1]
        self.assertTrue(comment_form.is_valid())
        self.assertEqual(comment_form.instance.user, self.commenting_user)
        # The commenting user should be able to add a new comment, and the new comment's user should be set to request.user

        form = self.EventPageForm({
            'comments-TOTAL_FORMS': 1,
            'comments-INITIAL_FORMS': 1,
            'comments-MIN_NUM_FORMS': 0,
            'comments-MAX_NUM_FORMS': 1000,
            'comments-0-id': self.comment.pk,
            'comments-0-text': self.comment.text,
            'comments-0-contentpath': self.comment.contentpath,
            'comments-0-DELETE': 1,  # Try to delete a comment from another user
            'comments-0-replies-TOTAL_FORMS': 0,
            'comments-0-replies-INITIAL_FORMS': 0,
            'comments-0-replies-MIN_NUM_FORMS': 0,
            'comments-0-replies-MAX_NUM_FORMS': 1000,
        },
            instance=self.event_page
        )

        comment_form = form.formsets['comments'].forms[0]
        self.assertFalse(comment_form.is_valid())
        # Users cannot delete comments from other users

    def test_users_can_edit_comment_positions(self):
        form = self.EventPageForm({
            'comments-TOTAL_FORMS': 1,
            'comments-INITIAL_FORMS': 1,
            'comments-MIN_NUM_FORMS': 0,
            'comments-MAX_NUM_FORMS': 1000,
            'comments-0-id': self.comment.pk,
            'comments-0-text': self.comment.text,
            'comments-0-contentpath': self.comment.contentpath,
            'comments-0-position': 'a_new_position',  # Try to change the position of a comment
            'comments-0-DELETE': 0,
            'comments-0-replies-TOTAL_FORMS': 0,
            'comments-0-replies-INITIAL_FORMS': 0,
            'comments-0-replies-MIN_NUM_FORMS': 0,
            'comments-0-replies-MAX_NUM_FORMS': 1000,
        },
            instance=self.event_page
        )

        comment_form = form.formsets['comments'].forms[0]
        self.assertTrue(comment_form.is_valid())
        # Users can change the positions of other users' comments within a field
        # eg by editing a rich text field

    @freeze_time("2017-01-01 12:00:00")
    def test_comment_resolve(self):
        form = self.EventPageForm({
            'comments-TOTAL_FORMS': 1,
            'comments-INITIAL_FORMS': 1,
            'comments-MIN_NUM_FORMS': 0,
            'comments-MAX_NUM_FORMS': 1000,
            'comments-0-id': self.comment.pk,
            'comments-0-text': self.comment.text,
            'comments-0-contentpath': self.comment.contentpath,
            'comments-0-resolved': 1,
            'comments-0-replies-TOTAL_FORMS': 0,
            'comments-0-replies-INITIAL_FORMS': 0,
            'comments-0-replies-MIN_NUM_FORMS': 0,
            'comments-0-replies-MAX_NUM_FORMS': 1000,
        },
            instance=self.event_page
        )
        comment_form = form.formsets['comments'].forms[0]
        self.assertTrue(comment_form.is_valid())
        comment_form.save()
        resolved_comment = Comment.objects.get(pk=self.comment.pk)
        self.assertEqual(resolved_comment.resolved_by, self.commenting_user)

        if settings.USE_TZ:
            self.assertEqual(resolved_comment.resolved_at, datetime(2017, 1, 1, 12, 0, 0, tzinfo=utc))
        else:
            self.assertEqual(resolved_comment.resolved_at, datetime(2017, 1, 1, 12, 0, 0))

    def test_comment_reply_form_validation(self):

        form = self.EventPageForm({
            'comments-TOTAL_FORMS': 1,
            'comments-INITIAL_FORMS': 1,
            'comments-MIN_NUM_FORMS': 0,
            'comments-MAX_NUM_FORMS': 1000,
            'comments-0-id': self.comment.pk,
            'comments-0-text': self.comment.text,
            'comments-0-contentpath': self.comment.contentpath,
            'comments-0-replies-TOTAL_FORMS': 3,
            'comments-0-replies-INITIAL_FORMS': 2,
            'comments-0-replies-MIN_NUM_FORMS': 0,
            'comments-0-replies-MAX_NUM_FORMS': 1000,
            'comments-0-replies-0-id': self.reply_1.pk,
            'comments-0-replies-0-text': 'edited_text',  # Try to edit someone else's reply
            'comments-0-replies-1-id': self.reply_2.pk,
            'comments-0-replies-1-text': "Edited text 2",  # Try to edit own reply
            'comments-0-replies-2-id': "",  # Add new reply
            'comments-0-replies-2-text': "New reply",
        },
            instance=self.event_page
        )

        comment_form = form.formsets['comments'].forms[0]

        reply_forms = comment_form.formsets['replies'].forms

        self.assertFalse(reply_forms[0].is_valid())
        # The existing reply was from another user, so should not be editable

        self.assertTrue(reply_forms[1].is_valid())
        # The existing reply was from the same user, so should be editable

        self.assertTrue(reply_forms[2].is_valid())
        self.assertEqual(reply_forms[2].instance.user, self.commenting_user)
        # Should be able to add new reply, and user should be set correctly

        form = self.EventPageForm({
            'comments-TOTAL_FORMS': 1,
            'comments-INITIAL_FORMS': 1,
            'comments-MIN_NUM_FORMS': 0,
            'comments-MAX_NUM_FORMS': 1000,
            'comments-0-id': self.comment.pk,
            'comments-0-text': self.comment.text,
            'comments-0-contentpath': self.comment.contentpath,
            'comments-0-replies-TOTAL_FORMS': 2,
            'comments-0-replies-INITIAL_FORMS': 2,
            'comments-0-replies-MIN_NUM_FORMS': 0,
            'comments-0-replies-MAX_NUM_FORMS': 1000,
            'comments-0-replies-0-id': self.reply_1.pk,
            'comments-0-replies-0-text': self.reply_1.text,
            'comments-0-replies-0-DELETE': 1,  # Try to delete someone else's reply
            'comments-0-replies-1-id': self.reply_2.pk,
            'comments-0-replies-1-text': "Edited text 2",
            'comments-0-replies-1-DELETE': 1,  # Try to delete own reply
        },
            instance=self.event_page
        )

        comment_form = form.formsets['comments'].forms[0]

        reply_forms = comment_form.formsets['replies'].forms

        self.assertFalse(reply_forms[0].is_valid())
        # The existing reply was from another user, so should not be deletable

        self.assertTrue(reply_forms[1].is_valid())
        # The existing reply was from the same user, so should be deletable
