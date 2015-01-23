from mock import MagicMock

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django import forms

from wagtail.wagtailadmin.edit_handlers import (
    get_form_for_model,
    extract_panel_definitions_from_model_class,
    BaseFieldPanel,
    FieldPanel,
    BaseRichTextFieldPanel,
    WagtailAdminModelForm,
    BaseTabbedInterface,
    TabbedInterface,
    BaseObjectList,
    ObjectList,
    PageChooserPanel,
    InlinePanel,
)

from wagtail.wagtailadmin.widgets import AdminPageChooser, AdminDateInput
from wagtail.wagtailimages.edit_handlers import BaseImageChooserPanel
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


class TestObjectList(TestCase):
    def test_object_list(self):
        object_list = ObjectList(['foo'])
        self.assertTrue(issubclass(object_list, BaseObjectList))


class TestFieldPanel(TestCase):
    class FakeClass(object):
        required = False
        widget = 'fake widget'

    class FakeField(object):
        label = 'label'
        help_text = 'help text'
        errors = ['errors']
        id_for_label = 'id for label'

    class FakeForm(dict):
        def __init__(self, *args, **kwargs):
            self.fields = self.fields_iterator()

        def fields_iterator(self):
            for i in self:
                yield i

    def setUp(self):
        fake_field = self.FakeField()
        fake_field.field = self.FakeClass()
        self.field_panel = FieldPanel('barbecue', 'snowman')(
            instance=True,
            form={'barbecue': fake_field})

    def test_render_as_object(self):
        result = self.field_panel.render_as_object()
        self.assertIn('<legend>label</legend>',
                      result)
        self.assertIn('<p class="error-message">',
                      result)

    def test_render_as_field(self):
        field = self.FakeField()
        bound_field = self.FakeField()
        bound_field.field = field
        self.field_panel.bound_field = bound_field
        result = self.field_panel.render_as_field()
        self.assertIn('<p class="help">help text</p>',
                      result)
        self.assertIn('<span>errors</span>',
                      result)

    def test_rendered_fields(self):
        result = self.field_panel.rendered_fields()
        self.assertEqual(result, ['barbecue'])

    def test_field_type(self):
        fake_object = self.FakeClass()
        another_fake_object = self.FakeClass()
        fake_object.field = another_fake_object
        self.field_panel.bound_field = fake_object
        self.assertEqual(self.field_panel.field_type(), 'fake_class')

    def test_widget_overrides(self):
        result = FieldPanel('barbecue', 'snowman').widget_overrides()
        self.assertEqual(result, {})

    def test_required_formsets(self):
        result = FieldPanel('barbecue', 'snowman').required_formsets()
        self.assertEqual(result, [])

    def test_get_form_class(self):
        result = FieldPanel('barbecue', 'snowman').get_form_class(Page)
        self.assertTrue(issubclass(result, WagtailAdminModelForm))

    def test_render_missing_fields(self):
        fake_form = self.FakeForm()
        fake_form["foo"] = "bar"
        self.field_panel.form = fake_form
        self.assertEqual(self.field_panel.render_missing_fields(), "bar")

    def test_render_form_content(self):
        fake_form = self.FakeForm()
        fake_form["foo"] = "bar"
        self.field_panel.form = fake_form
        self.assertIn("bar", self.field_panel.render_form_content())


class TestPageChooserPanel(TestCase):

    def setUp(self):
        model = PageChooserModel
        self.chosen_page = Page.objects.get(pk=2)
        test_instance = model.objects.create(page=self.chosen_page)
        self.dotted_model = model._meta.app_label + '.' + model._meta.model_name

        self.page_chooser_panel_class = PageChooserPanel('page', model)

        form_class = get_form_for_model(model, widgets=self.page_chooser_panel_class.widget_overrides())
        form = form_class(instance=test_instance)
        form.errors['page'] = form.error_class(['errors'])

        self.page_chooser_panel = self.page_chooser_panel_class(instance=test_instance,
                                                                form=form)

    def test_render_js_init(self):
        result = self.page_chooser_panel.render_as_field()
        self.assertIn(
            'createPageChooser("{id}", "{model}", {parent});'.format(
                id="id_page", model=self.dotted_model, parent=self.chosen_page.get_parent().id),
            result)

    def test_get_chosen_item(self):
        result = self.page_chooser_panel.get_chosen_item()
        self.assertEqual(result, self.chosen_page)

    def test_render_as_field(self):
        result = self.page_chooser_panel.render_as_field()
        self.assertIn('<p class="help">help text</p>', result)
        self.assertIn('<span>errors</span>', result)

    def test_widget_overrides(self):
        result = self.page_chooser_panel.widget_overrides()
        self.assertIsInstance(result['page'], AdminPageChooser)

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
    class FakeField(object):
        class FakeFormset(object):
            class FakeForm(object):
                class FakeInstance(object):
                    def __repr__(self):
                        return 'fake instance'
                fields = {'DELETE': MagicMock(),
                          'ORDER': MagicMock()}
                instance = FakeInstance()

                cleaned_data = {
                    'ORDER': 0,
                }

                def __repr__(self):
                    return 'fake form'

            forms = [FakeForm()]
            empty_form = FakeForm()
            can_order = True

            def is_valid(self):
                return True

        label = 'label'
        help_text = 'help text'
        errors = ['errors']
        id_for_label = 'id for label'
        formsets = {'formset': FakeFormset()}

    class FakeInstance(object):
        class FakePage(object):
            class FakeParent(object):
                id = 1

            name = 'fake page'

            def get_parent(self):
                return self.FakeParent()

        def __init__(self):
            fake_page = self.FakePage()
            self.barbecue = fake_page

    class FakePanel(object):
        name = 'mock panel'

        class FakeChild(object):
            def rendered_fields(self):
                return ["rendered fields"]

        def init(*args, **kwargs):
            pass

        def __call__(self, *args, **kwargs):
            fake_child = self.FakeChild()
            return fake_child

    def setUp(self):
        self.fake_field = self.FakeField()
        self.fake_instance = self.FakeInstance()
        self.mock_panel = self.FakePanel()
        self.mock_model = MagicMock()
        self.mock_model.formset.related.model.panels = [self.mock_panel]

    def test_get_panel_definitions_no_panels(self):
        """
        Check that get_panel_definitions returns the panels set on the model
        when no panels are set on the InlinePanel
        """
        inline_panel = InlinePanel(self.mock_model, 'formset')(
            instance=self.fake_instance,
            form=self.fake_field)
        result = inline_panel.get_panel_definitions()
        self.assertEqual(result[0].name, 'mock panel')

    def test_get_panel_definitions(self):
        """
        Check that get_panel_definitions returns the panels set on
        InlinePanel
        """
        other_mock_panel = MagicMock()
        other_mock_panel.name = 'other mock panel'
        inline_panel = InlinePanel(self.mock_model,
                                   'formset',
                                   panels=[other_mock_panel])(
            instance=self.fake_instance,
            form=self.fake_field)
        result = inline_panel.get_panel_definitions()
        self.assertEqual(result[0].name, 'other mock panel')

    def test_required_formsets(self):
        inline_panel = InlinePanel(self.mock_model, 'formset')(
            instance=self.fake_instance,
            form=self.fake_field)
        self.assertEqual(inline_panel.required_formsets(), ['formset'])

    def test_render(self):
        inline_panel = InlinePanel(self.mock_model,
                                   'formset',
                                   label='foo')(
            instance=self.fake_instance,
            form=self.fake_field)
        self.assertIn('Add foo', inline_panel.render())

    def test_render_js_init(self):
        inline_panel = InlinePanel(self.mock_model,
                                   'formset')(
            instance=self.fake_instance,
            form=self.fake_field)
        self.assertIn('var panel = InlinePanel({',
                      inline_panel.render_js_init())
