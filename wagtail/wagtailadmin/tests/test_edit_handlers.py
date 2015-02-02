from datetime import date

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django import forms

from wagtail.wagtailadmin.edit_handlers import (
    get_form_for_model,
    extract_panel_definitions_from_model_class,
    BaseFieldPanel,
    FieldPanel,
    BaseRichTextFieldPanel,
    TabbedInterface,
    ObjectList,
    PageChooserPanel,
    InlinePanel,
)

from wagtail.wagtailadmin.widgets import AdminPageChooser, AdminDateInput
from wagtail.wagtailimages.edit_handlers import BaseImageChooserPanel, ImageChooserPanel
from wagtail.wagtailcore.models import Page, Site
from wagtail.tests.models import PageChooserModel, EventPage, EventPageSpeaker


class TestGetFormForModel(TestCase):
    def test_get_form_for_model(self):
        EventPageForm = get_form_for_model(EventPage)
        form = EventPageForm()

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

    def test_get_form_for_model_with_specific_fields(self):
        EventPageForm = get_form_for_model(EventPage, fields=['date_from'], formsets=['speakers'])
        form = EventPageForm()

        # form should contain date_from but not title
        self.assertEqual(type(form.fields['date_from']), forms.DateField)
        self.assertEqual(type(form.fields['date_from'].widget), AdminDateInput)
        self.assertNotIn('title', form.fields)

        # formsets should include speakers but not related_links
        self.assertIn('speakers', form.formsets)
        self.assertNotIn('related_links', form.formsets)

    def test_get_form_for_model_with_excluded_fields(self):
        EventPageForm = get_form_for_model(EventPage, exclude=['title'], exclude_formsets=['related_links'])
        form = EventPageForm()

        # form should contain date_from but not title
        self.assertEqual(type(form.fields['date_from']), forms.DateField)
        self.assertEqual(type(form.fields['date_from'].widget), AdminDateInput)
        self.assertNotIn('title', form.fields)

        # 'path' should still be excluded even though it isn't explicitly in the exclude list
        self.assertNotIn('path', form.fields)

        # formsets should include speakers but not related_links
        self.assertIn('speakers', form.formsets)
        self.assertNotIn('related_links', form.formsets)

    def test_get_form_for_model_with_widget_overides_by_class(self):
        EventPageForm = get_form_for_model(EventPage, widgets={'date_from': forms.PasswordInput})
        form = EventPageForm()

        self.assertEqual(type(form.fields['date_from']), forms.DateField)
        self.assertEqual(type(form.fields['date_from'].widget), forms.PasswordInput)

    def test_get_form_for_model_with_widget_overides_by_instance(self):
        EventPageForm = get_form_for_model(EventPage, widgets={'date_from': forms.PasswordInput()})
        form = EventPageForm()

        self.assertEqual(type(form.fields['date_from']), forms.DateField)
        self.assertEqual(type(form.fields['date_from'].widget), forms.PasswordInput)


class TestExtractPanelDefinitionsFromModelClass(TestCase):
    def test_can_extract_panel_property(self):
        # A class with a 'panels' property defined should return that list
        result = extract_panel_definitions_from_model_class(EventPageSpeaker)
        self.assertEqual(len(result), 4)
        #print repr(result)
        self.assertTrue(any([issubclass(panel, BaseImageChooserPanel) for panel in result]))

    def test_exclude(self):
        panels = extract_panel_definitions_from_model_class(Site, exclude=['hostname'])
        for panel in panels:
            self.assertNotEqual(panel.field_name, 'hostname')

    def test_can_build_panel_list(self):
        # EventPage has no 'panels' definition, so one should be derived from the field list
        panels = extract_panel_definitions_from_model_class(EventPage)

        self.assertTrue(any([
            issubclass(panel, BaseFieldPanel) and panel.field_name == 'date_from'
            for panel in panels
        ]))

        # returned panel types should respect modelfield.get_panel() - used on RichTextField
        self.assertTrue(any([
            issubclass(panel, BaseRichTextFieldPanel) and panel.field_name == 'body'
            for panel in panels
        ]))

        # treebeard fields should be excluded
        self.assertFalse(any([
            issubclass(panel, BaseFieldPanel) and panel.field_name == 'path'
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
                InlinePanel(EventPage, 'speakers', label="Speakers"),
            ], heading='Speakers'),
        ])

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

    def test_rendered_fields(self):
        EventPageForm = self.EventPageTabbedInterface.get_form_class(EventPage)
        event = EventPage(title='Abergavenny sheepdog trials')
        form = EventPageForm(instance=event)

        tabbed_interface = self.EventPageTabbedInterface(
            instance=event,
            form=form
        )

        # rendered_fields should report the set of form fields rendered recursively as part of TabbedInterface
        result = set(tabbed_interface.rendered_fields())
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
        # rendered output should also contain all other fields that are in the form but not represented
        # in the panel definition
        self.assertIn('signup_link', result)


class TestObjectList(TestCase):
    def setUp(self):
        # a custom ObjectList for EventPage
        self.EventPageObjectList = ObjectList([
            FieldPanel('title', widget=forms.Textarea),
            FieldPanel('date_from'),
            FieldPanel('date_to'),
            InlinePanel(EventPage, 'speakers', label="Speakers"),
        ], heading='Event details', classname="shiny")

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

        # result should contain h2 headings for children
        self.assertIn('<h2>Start date</h2>', result)

        # result should contain rendered content from descendants
        self.assertIn('Abergavenny sheepdog trials</textarea>', result)

        # this result should not include fields that are not covered by the panel definition
        self.assertNotIn('signup_link', result)


class TestFieldPanel(TestCase):
    def setUp(self):
        self.EventPageForm = get_form_for_model(EventPage, formsets = [])
        self.event = EventPage(title='Abergavenny sheepdog trials',
            date_from=date(2014, 7, 20), date_to=date(2014, 7, 21))

        self.EndDatePanel = FieldPanel('date_to', classname='full-width')

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

        # check that label appears in the 'object' wrapper as well as the field
        self.assertIn('<legend>End date</legend>', result)
        self.assertIn('<label for="id_date_to">End date:</label>', result)

        # check that help text is included
        self.assertIn('Not required if event is on a single day', result)

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

    def test_rendered_fields(self):
        form = self.EventPageForm(
            {'title': 'Pontypridd sheepdog trials', 'date_from': '2014-07-20', 'date_to': '2014-07-22'},
            instance=self.event)
        field_panel = self.EndDatePanel(
            instance=self.event,
            form=form
        )
        result = field_panel.rendered_fields()
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
        self.MyPageChooserPanel = PageChooserPanel('page', 'tests.EventPage')

        # build a form class containing the fields that MyPageChooserPanel wants
        self.PageChooserForm = self.MyPageChooserPanel.get_form_class(PageChooserModel)

        # a test instance of PageChooserModel, pointing to the 'christmas' page
        self.christmas_page = Page.objects.get(slug='christmas')
        self.events_index_page = Page.objects.get(slug='events')
        self.test_instance = model.objects.create(page=self.christmas_page)

        self.form = self.PageChooserForm(instance=self.test_instance)
        # self.form.errors['page'] = self.form.error_class(['errors'])  # FIXME: wat
        self.page_chooser_panel = self.MyPageChooserPanel(instance=self.test_instance,
                                                                form=self.form)

    def test_page_chooser_uses_correct_widget(self):
        self.assertEqual(type(self.form.fields['page'].widget), AdminPageChooser)

    def test_render_js_init(self):
        result = self.page_chooser_panel.render_as_field()
        expected_js = 'createPageChooser("{id}", "{model}", {parent});'.format(
            id="id_page", model="tests.eventpage", parent=self.events_index_page.id)

        self.assertIn(expected_js, result)

    def test_get_chosen_item(self):
        result = self.page_chooser_panel.get_chosen_item()
        self.assertEqual(result, self.christmas_page)

    def test_render_as_field(self):
        result = self.page_chooser_panel.render_as_field()
        self.assertIn('<p class="help">help text</p>', result)

    def test_render_error(self):
        form = self.PageChooserForm({'page': ''}, instance=self.test_instance)
        self.assertFalse(form.is_valid())

        page_chooser_panel = self.MyPageChooserPanel(instance=self.test_instance,
                                                                form=form)
        self.assertIn('<span>This field is required.</span>', page_chooser_panel.render_as_field())

    def test_target_content_type(self):
        result = PageChooserPanel(
            'barbecue',
            'wagtailcore.site'
        ).target_content_type()
        self.assertEqual(result.name, 'site')

    def test_target_content_type_malformed_type(self):
        result = PageChooserPanel(
            'barbecue',
            'snowman'
        )
        self.assertRaises(ImproperlyConfigured,
                          result.target_content_type)

    def test_target_content_type_nonexistent_type(self):
        result = PageChooserPanel(
            'barbecue',
            'snowman.lorry'
        )
        self.assertRaises(ImproperlyConfigured,
                          result.target_content_type)


class TestInlinePanel(TestCase):
    fixtures = ['test.json']

    def test_render(self):
        """
        Check that the inline panel renders the panels set on the model
        when no 'panels' parameter is passed in the InlinePanel definition
        """
        SpeakerInlinePanel = InlinePanel(EventPage, 'speakers', label="Speakers")
        EventPageForm = SpeakerInlinePanel.get_form_class(EventPage)

        # SpeakerInlinePanel should instruct the form class to include a 'speakers' formset
        self.assertEqual(['speakers'], list(EventPageForm.formsets.keys()))

        event_page = EventPage.objects.get(slug='christmas')

        form = EventPageForm(instance=event_page)
        panel = SpeakerInlinePanel(instance=event_page, form=form)

        result = panel.render_as_field()

        self.assertIn('<label for="id_speakers-0-first_name">Name:</label>', result)
        self.assertIn('<label for="id_speakers-0-last_name">Surname:</label>', result)
        self.assertIn('<label for="id_speakers-0-image">Image:</label>', result)
        self.assertIn('value="Choose an image"', result)

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
        SpeakerInlinePanel = InlinePanel(EventPage, 'speakers', label="Speakers", panels=[
            FieldPanel('first_name'),
            ImageChooserPanel('image'),
        ])
        EventPageForm = SpeakerInlinePanel.get_form_class(EventPage)

        # SpeakerInlinePanel should instruct the form class to include a 'speakers' formset
        self.assertEqual(['speakers'], list(EventPageForm.formsets.keys()))

        event_page = EventPage.objects.get(slug='christmas')

        form = EventPageForm(instance=event_page)
        panel = SpeakerInlinePanel(instance=event_page, form=form)

        result = panel.render_as_field()

        self.assertIn('<label for="id_speakers-0-first_name">Name:</label>', result)
        self.assertNotIn('<label for="id_speakers-0-last_name">Surname:</label>', result)

        # surname field is still rendered as a 'stray' label-less field: see #338.
        # (Temporarily adding a test for this, so that we can verify that it fails when #338 is fixed...)
        self.assertIn('<input id="id_speakers-0-last_name"', result)

        self.assertIn('<label for="id_speakers-0-image">Image:</label>', result)
        self.assertIn('value="Choose an image"', result)

        # rendered panel must also contain hidden fields for id, DELETE and ORDER
        self.assertIn('<input id="id_speakers-0-id" name="speakers-0-id" type="hidden"', result)
        self.assertIn('<input id="id_speakers-0-DELETE" name="speakers-0-DELETE" type="hidden"', result)
        self.assertIn('<input id="id_speakers-0-ORDER" name="speakers-0-ORDER" type="hidden"', result)

        # rendered panel must contain maintenance form for the formset
        self.assertIn('<input id="id_speakers-TOTAL_FORMS" name="speakers-TOTAL_FORMS" type="hidden"', result)

        # render_js_init must provide the JS initializer
        self.assertIn('var panel = InlinePanel({', panel.render_js_init())
