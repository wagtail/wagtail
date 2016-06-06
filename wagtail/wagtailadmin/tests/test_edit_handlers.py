from __future__ import absolute_import, unicode_literals

import warnings
from datetime import date

import mock
from django import forms
from django.core import checks
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from wagtail.tests.testapp.forms import ValidatedPageForm
from wagtail.tests.testapp.models import (
    EventPage, EventPageChooserModel, EventPageSpeaker, PageChooserModel, SimplePage, ValidatedPage)
from wagtail.tests.utils import WagtailTestUtils
from wagtail.utils.deprecation import RemovedInWagtail17Warning
from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel, InlinePanel, ObjectList, PageChooserPanel, RichTextFieldPanel, TabbedInterface,
    extract_panel_definitions_from_model_class, get_form_for_model)
from wagtail.wagtailadmin.forms import WagtailAdminModelForm, WagtailAdminPageForm
from wagtail.wagtailadmin.rich_text import HalloRichTextArea
from wagtail.wagtailadmin.widgets import AdminAutoHeightTextInput, AdminDateInput, AdminPageChooser
from wagtail.wagtailcore.models import Page, Site
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel


class TestGetFormForModel(TestCase):
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
        self.assertEqual(type(event_form.fields['body'].widget), HalloRichTextArea)

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


def clear_edit_handler(page_cls):
    def decorator(fn):
        def decorated(self):
            # Clear any old EditHandlers generated
            page_cls.get_edit_handler.cache_clear()
            fn(self)
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
        EditHandler = EventPage.get_edit_handler()
        EventPageForm = EditHandler.get_form_class(EventPage)

        # The generated form should inherit from WagtailAdminPageForm
        self.assertTrue(issubclass(EventPageForm, WagtailAdminPageForm))

    @clear_edit_handler(ValidatedPage)
    def test_get_form_for_page_with_custom_base(self):
        """
        ValidatedPage sets a custom base_form_class. This should be used as the
        base class when constructing a form for ValidatedPages
        """
        EditHandler = ValidatedPage.get_edit_handler()
        GeneratedValidatedPageForm = EditHandler.get_form_class(ValidatedPage)

        # The generated form should inherit from ValidatedPageForm, because
        # ValidatedPage.base_form_class == ValidatedPageForm
        self.assertTrue(issubclass(GeneratedValidatedPageForm, ValidatedPageForm))

    @clear_edit_handler(ValidatedPage)
    def test_check_invalid_base_form_class(self):
        class BadFormClass(object):
            pass

        invalid_base_form = checks.Error(
            "ValidatedPage.base_form_class does not extend WagtailAdminPageForm",
            hint="Ensure that wagtail.wagtailadmin.tests.test_edit_handlers.BadFormClass extends WagtailAdminPageForm",
            obj=ValidatedPage,
            id='wagtailadmin.E001')

        invalid_edit_handler = checks.Error(
            "ValidatedPage.get_edit_handler().get_form_class(ValidatedPage) does not extend WagtailAdminPageForm",
            hint="Ensure that the EditHandler for ValidatedPage creates a subclass of WagtailAdminPageForm",
            obj=ValidatedPage,
            id='wagtailadmin.E002')

        with mock.patch.object(ValidatedPage, 'base_form_class', new=BadFormClass):
            errors = checks.run_checks()

            # ignore CSS loading errors (to avoid spurious failures on CI servers that
            # don't build the CSS)
            errors = [e for e in errors if e.id != 'wagtailadmin.W001']

            self.assertEqual(errors, [invalid_base_form, invalid_edit_handler])

    @clear_edit_handler(ValidatedPage)
    def test_custom_edit_handler_form_class(self):
        """
        Set a custom edit handler on a Page class, but dont customise
        ValidatedPage.base_form_class, or provide a custom form class for the
        edit handler. Check the generated form class is of the correct type.
        """
        ValidatedPage.edit_handler = TabbedInterface([])
        with mock.patch.object(ValidatedPage, 'edit_handler', new=TabbedInterface([]), create=True):
            form_class = ValidatedPage.get_edit_handler().get_form_class(ValidatedPage)
            self.assertTrue(issubclass(form_class, WagtailAdminPageForm))
            errors = ValidatedPage.check()
            self.assertEqual(errors, [])


class TestExtractPanelDefinitionsFromModelClass(TestCase):
    def test_can_extract_panel_property(self):
        # A class with a 'panels' property defined should return that list
        result = extract_panel_definitions_from_model_class(EventPageSpeaker)
        self.assertEqual(len(result), 4)
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
        # a custom tabbed interface for EventPage
        self.EventPageTabbedInterface = TabbedInterface([
            ObjectList([
                FieldPanel('title', widget=forms.Textarea),
                FieldPanel('date_from'),
                FieldPanel('date_to'),
            ], heading='Event details', classname="shiny"),
            ObjectList([
                InlinePanel('speakers', label="Speakers"),
            ], heading='Speakers'),
        ]).bind_to_model(EventPage)

    def test_get_form_class(self):
        EventPageForm = self.EventPageTabbedInterface.get_form_class(EventPage)
        form = EventPageForm()

        # form must include the 'speakers' formset required by the speakers InlinePanel
        self.assertIn('speakers', form.formsets)

        # form must respect any overridden widgets
        self.assertEqual(type(form.fields['title'].widget), forms.Textarea)

    def test_render(self):
        EventPageForm = self.EventPageTabbedInterface.get_form_class(EventPage)
        event = EventPage(title='Abergavenny sheepdog trials')
        form = EventPageForm(instance=event)

        tabbed_interface = self.EventPageTabbedInterface(
            instance=event,
            form=form
        )

        result = tabbed_interface.render()

        # result should contain tab buttons
        self.assertIn('<a href="#event-details" class="active">Event details</a>', result)
        self.assertIn('<a href="#speakers" class="">Speakers</a>', result)

        # result should contain tab panels
        self.assertIn('<div class="tab-content">', result)
        self.assertIn('<section id="event-details" class="shiny active">', result)
        self.assertIn('<section id="speakers" class=" ">', result)

        # result should contain rendered content from descendants
        self.assertIn('Abergavenny sheepdog trials</textarea>', result)

        # this result should not include fields that are not covered by the panel definition
        self.assertNotIn('signup_link', result)

    def test_required_fields(self):
        # required_fields should report the set of form fields to be rendered recursively by children of TabbedInterface
        result = set(self.EventPageTabbedInterface.required_fields())
        self.assertEqual(result, set(['title', 'date_from', 'date_to']))

    def test_render_form_content(self):
        EventPageForm = self.EventPageTabbedInterface.get_form_class(EventPage)
        event = EventPage(title='Abergavenny sheepdog trials')
        form = EventPageForm(instance=event)

        tabbed_interface = self.EventPageTabbedInterface(
            instance=event,
            form=form
        )

        result = tabbed_interface.render_form_content()
        # rendered output should contain field content as above
        self.assertIn('Abergavenny sheepdog trials</textarea>', result)
        # rendered output should NOT include fields that are in the model but not represented
        # in the panel definition
        self.assertNotIn('signup_link', result)


class TestObjectList(TestCase):
    def setUp(self):
        # a custom ObjectList for EventPage
        self.EventPageObjectList = ObjectList([
            FieldPanel('title', widget=forms.Textarea),
            FieldPanel('date_from'),
            FieldPanel('date_to'),
            InlinePanel('speakers', label="Speakers"),
        ], heading='Event details', classname="shiny").bind_to_model(EventPage)

    def test_get_form_class(self):
        EventPageForm = self.EventPageObjectList.get_form_class(EventPage)
        form = EventPageForm()

        # form must include the 'speakers' formset required by the speakers InlinePanel
        self.assertIn('speakers', form.formsets)

        # form must respect any overridden widgets
        self.assertEqual(type(form.fields['title'].widget), forms.Textarea)

    def test_render(self):
        EventPageForm = self.EventPageObjectList.get_form_class(EventPage)
        event = EventPage(title='Abergavenny sheepdog trials')
        form = EventPageForm(instance=event)

        object_list = self.EventPageObjectList(
            instance=event,
            form=form
        )

        result = object_list.render()

        # result should contain ObjectList furniture
        self.assertIn('<ul class="objects">', result)

        # result should contain h2 headings (including labels) for children
        self.assertInHTML('<h2><label for="id_date_from">Start date</label></h2>', result)

        # result should include help text for children
        self.assertIn('<div class="object-help help">Not required if event is on a single day</div>', result)

        # result should contain rendered content from descendants
        self.assertIn('Abergavenny sheepdog trials</textarea>', result)

        # this result should not include fields that are not covered by the panel definition
        self.assertNotIn('signup_link', result)


class TestFieldPanel(TestCase):
    def setUp(self):
        self.EventPageForm = get_form_for_model(
            EventPage, form_class=WagtailAdminPageForm, formsets=[])
        self.event = EventPage(title='Abergavenny sheepdog trials',
                               date_from=date(2014, 7, 20), date_to=date(2014, 7, 21))

        self.EndDatePanel = FieldPanel('date_to', classname='full-width').bind_to_model(EventPage)

    def test_render_as_object(self):
        form = self.EventPageForm(
            {'title': 'Pontypridd sheepdog trials', 'date_from': '2014-07-20', 'date_to': '2014-07-22'},
            instance=self.event)

        form.is_valid()

        field_panel = self.EndDatePanel(
            instance=self.event,
            form=form
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

        field_panel = self.EndDatePanel(
            instance=self.event,
            form=form
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
        result = self.EndDatePanel.required_fields()
        self.assertEqual(result, ['date_to'])

    def test_error_message_is_rendered(self):
        form = self.EventPageForm(
            {'title': 'Pontypridd sheepdog trials', 'date_from': '2014-07-20', 'date_to': '2014-07-33'},
            instance=self.event)

        form.is_valid()

        field_panel = self.EndDatePanel(
            instance=self.event,
            form=form
        )
        result = field_panel.render_as_field()

        self.assertIn('<p class="error-message">', result)
        self.assertIn('<span>Enter a valid date.</span>', result)


class TestPageChooserPanel(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        model = PageChooserModel  # a model with a foreign key to Page which we want to render as a page chooser

        # a PageChooserPanel class that works on PageChooserModel's 'page' field
        self.EditHandler = ObjectList([PageChooserPanel('page')]).bind_to_model(PageChooserModel)
        self.MyPageChooserPanel = self.EditHandler.children[0]

        # build a form class containing the fields that MyPageChooserPanel wants
        self.PageChooserForm = self.EditHandler.get_form_class(PageChooserModel)

        # a test instance of PageChooserModel, pointing to the 'christmas' page
        self.christmas_page = Page.objects.get(slug='christmas')
        self.events_index_page = Page.objects.get(slug='events')
        self.test_instance = model.objects.create(page=self.christmas_page)

        self.form = self.PageChooserForm(instance=self.test_instance)
        self.page_chooser_panel = self.MyPageChooserPanel(instance=self.test_instance, form=self.form)

    def test_page_chooser_uses_correct_widget(self):
        self.assertEqual(type(self.form.fields['page'].widget), AdminPageChooser)

    def test_render_js_init(self):
        result = self.page_chooser_panel.render_as_field()
        expected_js = 'createPageChooser("{id}", ["{model}"], {parent}, false);'.format(
            id="id_page", model="wagtailcore.page", parent=self.events_index_page.id)

        self.assertIn(expected_js, result)

    def test_render_js_init_with_can_choose_root_true(self):
        # construct an alternative page chooser panel object, with can_choose_root=True

        MyPageObjectList = ObjectList([
            PageChooserPanel('page', can_choose_root=True)
        ]).bind_to_model(PageChooserModel)
        MyPageChooserPanel = MyPageObjectList.children[0]
        PageChooserForm = MyPageObjectList.get_form_class(EventPageChooserModel)

        form = PageChooserForm(instance=self.test_instance)
        page_chooser_panel = MyPageChooserPanel(instance=self.test_instance, form=form)
        result = page_chooser_panel.render_as_field()

        # the canChooseRoot flag on createPageChooser should now be true
        expected_js = 'createPageChooser("{id}", ["{model}"], {parent}, true);'.format(
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
            '<a href="/admin/pages/%d/edit/" class="edit-link button button-small button-secondary" target="_blank">'
            'Edit this page</a>' % self.christmas_page.id,
            result)

    def test_render_as_empty_field(self):
        test_instance = PageChooserModel()
        form = self.PageChooserForm(instance=test_instance)
        page_chooser_panel = self.MyPageChooserPanel(instance=test_instance, form=form)
        result = page_chooser_panel.render_as_field()

        self.assertIn('<p class="help">help text</p>', result)
        self.assertIn('<span class="title"></span>', result)
        self.assertIn('Choose a page', result)

    def test_render_error(self):
        form = self.PageChooserForm({'page': ''}, instance=self.test_instance)
        self.assertFalse(form.is_valid())

        page_chooser_panel = self.MyPageChooserPanel(instance=self.test_instance, form=form)
        self.assertIn('<span>This field is required.</span>', page_chooser_panel.render_as_field())

    def test_override_page_type(self):
        # Model has a foreign key to Page, but we specify EventPage in the PageChooserPanel
        # to restrict the chooser to that page type
        MyPageObjectList = ObjectList([
            PageChooserPanel('page', 'tests.EventPage')
        ]).bind_to_model(EventPageChooserModel)
        MyPageChooserPanel = MyPageObjectList.children[0]
        PageChooserForm = MyPageObjectList.get_form_class(EventPageChooserModel)
        form = PageChooserForm(instance=self.test_instance)
        page_chooser_panel = MyPageChooserPanel(instance=self.test_instance, form=form)

        result = page_chooser_panel.render_as_field()
        expected_js = 'createPageChooser("{id}", ["{model}"], {parent}, false);'.format(
            id="id_page", model="tests.eventpage", parent=self.events_index_page.id)

        self.assertIn(expected_js, result)

    def test_autodetect_page_type(self):
        # Model has a foreign key to EventPage, which we want to autodetect
        # instead of specifying the page type in PageChooserPanel
        MyPageObjectList = ObjectList([PageChooserPanel('page')]).bind_to_model(EventPageChooserModel)
        MyPageChooserPanel = MyPageObjectList.children[0]
        PageChooserForm = MyPageObjectList.get_form_class(EventPageChooserModel)
        form = PageChooserForm(instance=self.test_instance)
        page_chooser_panel = MyPageChooserPanel(instance=self.test_instance, form=form)

        result = page_chooser_panel.render_as_field()
        expected_js = 'createPageChooser("{id}", ["{model}"], {parent}, false);'.format(
            id="id_page", model="tests.eventpage", parent=self.events_index_page.id)

        self.assertIn(expected_js, result)

    def test_target_models(self):
        result = PageChooserPanel(
            'barbecue',
            'wagtailcore.site'
        ).bind_to_model(PageChooserModel).target_models()
        self.assertEqual(result, [Site])

    def test_target_models_malformed_type(self):
        result = PageChooserPanel(
            'barbecue',
            'snowman'
        ).bind_to_model(PageChooserModel)
        self.assertRaises(ImproperlyConfigured,
                          result.target_models)

    def test_target_models_nonexistent_type(self):
        result = PageChooserPanel(
            'barbecue',
            'snowman.lorry'
        ).bind_to_model(PageChooserModel)
        self.assertRaises(ImproperlyConfigured,
                          result.target_models)

    def test_target_content_type(self):
        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter('always')

            result = PageChooserPanel(
                'barbecue',
                'wagtailcore.site'
            ).bind_to_model(PageChooserModel).target_content_type()[0]
            self.assertEqual(result.name, 'site')

            self.assertEqual(len(ws), 1)
            self.assertIs(ws[0].category, RemovedInWagtail17Warning)

    def test_target_content_type_malformed_type(self):
        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter('always')

            result = PageChooserPanel(
                'barbecue',
                'snowman'
            ).bind_to_model(PageChooserModel)
            self.assertRaises(ImproperlyConfigured,
                              result.target_content_type)

            self.assertEqual(len(ws), 1)
            self.assertIs(ws[0].category, RemovedInWagtail17Warning)

    def test_target_content_type_nonexistent_type(self):
        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter('always')

            result = PageChooserPanel(
                'barbecue',
                'snowman.lorry'
            ).bind_to_model(PageChooserModel)
            self.assertRaises(ImproperlyConfigured,
                              result.target_content_type)
            self.assertEqual(len(ws), 1)
            self.assertIs(ws[0].category, RemovedInWagtail17Warning)


class TestInlinePanel(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def test_render(self):
        """
        Check that the inline panel renders the panels set on the model
        when no 'panels' parameter is passed in the InlinePanel definition
        """
        SpeakerObjectList = ObjectList([InlinePanel('speakers', label="Speakers")]).bind_to_model(EventPage)
        SpeakerInlinePanel = SpeakerObjectList.children[0]
        EventPageForm = SpeakerObjectList.get_form_class(EventPage)

        # SpeakerInlinePanel should instruct the form class to include a 'speakers' formset
        self.assertEqual(['speakers'], list(EventPageForm.formsets.keys()))

        event_page = EventPage.objects.get(slug='christmas')

        form = EventPageForm(instance=event_page)
        panel = SpeakerInlinePanel(instance=event_page, form=form)

        result = panel.render_as_field()

        self.assertIn('<label for="id_speakers-0-first_name">Name:</label>', result)
        self.assertIn('value="Father"', result)
        self.assertIn('<label for="id_speakers-0-last_name">Surname:</label>', result)
        self.assertIn('<label for="id_speakers-0-image">Image:</label>', result)
        self.assertIn('Choose an image', result)

        # rendered panel must also contain hidden fields for id, DELETE and ORDER
        self.assertIn('<input id="id_speakers-0-id" name="speakers-0-id" type="hidden"', result)
        self.assertIn('<input id="id_speakers-0-DELETE" name="speakers-0-DELETE" type="hidden"', result)
        self.assertIn('<input id="id_speakers-0-ORDER" name="speakers-0-ORDER" type="hidden"', result)

        # rendered panel must contain maintenance form for the formset
        self.assertIn('<input id="id_speakers-TOTAL_FORMS" name="speakers-TOTAL_FORMS" type="hidden"', result)

        # render_js_init must provide the JS initializer
        self.assertIn('var panel = InlinePanel({', panel.render_js_init())

    def test_render_with_panel_overrides(self):
        """
        Check that inline panel renders the panels listed in the InlinePanel definition
        where one is specified
        """
        SpeakerObjectList = ObjectList([
            InlinePanel('speakers', label="Speakers", panels=[
                FieldPanel('first_name', widget=forms.Textarea),
                ImageChooserPanel('image'),
            ]),
        ]).bind_to_model(EventPage)
        SpeakerInlinePanel = SpeakerObjectList.children[0]
        EventPageForm = SpeakerObjectList.get_form_class(EventPage)

        # SpeakerInlinePanel should instruct the form class to include a 'speakers' formset
        self.assertEqual(['speakers'], list(EventPageForm.formsets.keys()))

        event_page = EventPage.objects.get(slug='christmas')

        form = EventPageForm(instance=event_page)
        panel = SpeakerInlinePanel(instance=event_page, form=form)

        result = panel.render_as_field()

        # rendered panel should contain first_name rendered as a text area, but no last_name field
        self.assertIn('<label for="id_speakers-0-first_name">Name:</label>', result)
        self.assertIn('Father</textarea>', result)
        self.assertNotIn('<label for="id_speakers-0-last_name">Surname:</label>', result)

        # test for #338: surname field should not be rendered as a 'stray' label-less field
        self.assertNotIn('<input id="id_speakers-0-last_name"', result)

        self.assertIn('<label for="id_speakers-0-image">Image:</label>', result)
        self.assertIn('Choose an image', result)

        # rendered panel must also contain hidden fields for id, DELETE and ORDER
        self.assertIn('<input id="id_speakers-0-id" name="speakers-0-id" type="hidden"', result)
        self.assertIn('<input id="id_speakers-0-DELETE" name="speakers-0-DELETE" type="hidden"', result)
        self.assertIn('<input id="id_speakers-0-ORDER" name="speakers-0-ORDER" type="hidden"', result)

        # rendered panel must contain maintenance form for the formset
        self.assertIn('<input id="id_speakers-TOTAL_FORMS" name="speakers-TOTAL_FORMS" type="hidden"', result)

        # render_js_init must provide the JS initializer
        self.assertIn('var panel = InlinePanel({', panel.render_js_init())

    def test_invalid_inlinepanel_declaration(self):
        with self.ignore_deprecation_warnings():
            self.assertRaises(TypeError, lambda: InlinePanel(label="Speakers"))
            self.assertRaises(TypeError, lambda: InlinePanel(EventPage, 'speakers', 'bacon', label="Speakers"))
            self.assertRaises(TypeError, lambda: InlinePanel(EventPage, 'speakers', label="Speakers", bacon="chunky"))
