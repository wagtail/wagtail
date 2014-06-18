from mock import MagicMock

from django.test import TestCase
from django.core.exceptions import ValidationError

from wagtail.wagtailadmin.edit_handlers import (
    FriendlyDateInput,
    FriendlyTimeInput,
    FriendlyTimeField,
    LocalizedTimeInput,
    LocalizedDateInput,
    LocalizedTimeField,
    get_form_for_model,
    extract_panel_definitions_from_model_class,
    BaseFieldPanel,
    FieldPanel,
    RichTextFieldPanel,
    EditHandler,
    WagtailAdminModelForm,
    BaseCompositeEditHandler,
    BaseTabbedInterface,
    TabbedInterface,
    BaseObjectList,
    ObjectList,
    PageChooserPanel
)
from wagtail.wagtailcore.models import Page, Site


class TestFriendlyDateInput(TestCase):
    def test_attrs(self):
        """
        When the attrs argument is passed to FriendlyDateInput's
        constructor, they should be set on the FriendlyDateInput
        object along with the default attrs
        """
        friendly = FriendlyDateInput(attrs={'awesome': 'sauce'})
        self.assertEqual(friendly.attrs, {'class': 'friendly_date',
                                          'awesome': 'sauce'})


class TestFriendlyTimeInput(TestCase):
    def test_attrs(self):
        """
        When the attrs argument is passed to FriendlyDateInput's
        constructor, they should be set on the FriendlyDateInput
        object along with the default attrs
        """
        friendly = FriendlyTimeInput(attrs={'awesome': 'sauce'})
        self.assertEqual(friendly.attrs, {'class': 'friendly_time',
                                          'awesome': 'sauce'})


class TestFriendlyTimeField(TestCase):
    def setUp(self):
        self.friendly = FriendlyTimeField()

    def test_no_time_string(self):
        """
        to_python() should return None if it is passed an empty
        string
        """
        result = self.friendly.to_python('')
        self.assertEqual(result, None)

    def test_invalid_time_string(self):
        """
        to_python() should raise a ValidationError if it is passed
        an invalid time string
        """
        self.assertRaises(ValidationError, self.friendly.to_python, 'bacon')

    def test_afternoon_time_string(self):
        """
        to_python() should convert a time string that ends with 'pm'
        to a 24-hour time in the afternoon
        """
        python_time = self.friendly.to_python('3:49pm')
        self.assertEqual(str(python_time), '15:49:00')

    def test_morning_time_string(self):
        """
        to_python() should convert a time string that ends with 'am'
        to a 24-hour time in the morning
        """
        python_time = self.friendly.to_python('3:49am')
        self.assertEqual(str(python_time), '03:49:00')

    def test_no_minutes_time_string(self):
        """
        If minutes are not specified in the time string, they should
        default to zero
        """
        python_time = self.friendly.to_python('3am')
        self.assertEqual(str(python_time), '03:00:00')


class TestLocalizedDateInput(TestCase):
    def test_attrs(self):
        """
        When the attrs argument is passed to LocalizedDateInput's
        constructor, they should be set on the LocalizedDateInput
        object along with the default attrs
        """
        localized = LocalizedDateInput(attrs={'awesome': 'sauce'})
        self.assertEqual(localized.attrs, {'class': 'localized_date',
                                           'localize': True,
                                           'awesome': 'sauce'})


class TestLocalizedTimeInput(TestCase):
    def test_attrs(self):
        """
        When the attrs argument is passed to LocalizedTimeInput's
        constructor, they should be set on the LocalizedTimeInput
        object along with the default attrs
        """
        localized = LocalizedTimeInput(attrs={'awesome': 'sauce'})
        self.assertEqual(localized.attrs, {'class': 'localized_time',
                                          'awesome': 'sauce'})


class TestLocalizedTimeField(TestCase):
    def setUp(self):
        self.localized = LocalizedTimeField()

    def test_no_time_string(self):
        """
        to_python() should return None if it is passed an empty
        string
        """
        result = self.localized.to_python('')
        self.assertEqual(result, None)

    def test_non_time_string(self):
        """
        to_python() should raise a ValidationError if it is passed
        a string that does not represent a time
        """
        self.assertRaises(ValidationError, self.localized.to_python, 'bacon')

    def test_invalid_time_string(self):
        """
        to_python() should raise a ValidationError if it is passed
        an invalid time string
        """
        self.assertRaises(ValidationError, self.localized.to_python, '99:99')

    def test_afternoon_time_string(self):
        """
        to_python() should understand 24-hour time
        """
        python_time = self.localized.to_python('15:49')
        self.assertEqual(str(python_time), '15:49:00')

    def test_morning_time_string(self):
        """
        to_python() should understand 24-hour time
        """
        python_time = self.localized.to_python('3:49')
        self.assertEqual(str(python_time), '03:49:00')

    def test_no_minutes_time_string(self):
        """
        If minutes are not specified in the time string, they should
        default to zero
        """
        python_time = self.localized.to_python('3')
        self.assertEqual(str(python_time), '03:00:00')


class TestGetFormForModel(TestCase):
    class FakeClass(object):
        _meta = MagicMock()

    def setUp(self):
        self.mock_exclude = MagicMock()

    def test_get_form_for_model(self):
        form = get_form_for_model(self.FakeClass,
                                  fields=[],
                                  exclude=[self.mock_exclude],
                                  formsets=['baz'],
                                  exclude_formsets=['quux'],
                                  widgets=['bacon'])
        self.assertEqual(form.Meta.exclude, [self.mock_exclude])
        self.assertEqual(form.Meta.formsets, ['baz'])
        self.assertEqual(form.Meta.exclude_formsets, ['quux'])
        self.assertEqual(form.Meta.widgets, ['bacon'])


class TestExtractPanelDefinitionsFromModelClass(TestCase):
    class FakePage(Page):
        pass

    def test_can_extract_panels(self):
        mock = MagicMock()
        mock.panels = 'foo'
        result = extract_panel_definitions_from_model_class(mock)
        self.assertEqual(result, 'foo')

    def test_exclude(self):
        panels = extract_panel_definitions_from_model_class(Site, exclude=['hostname'])
        for panel in panels:
            self.assertNotEqual(panel.field_name, 'hostname')

    def test_extracted_objects_are_panels(self):
        panels = extract_panel_definitions_from_model_class(self.FakePage)
        for panel in panels:
            self.assertTrue(issubclass(panel, BaseFieldPanel))


class TestEditHandler(TestCase):
    class FakeForm(dict):
        def __init__(self, *args, **kwargs):
            self.fields = self.fields_iterator()

        def fields_iterator(self):
            for i in self:
                yield i

    def setUp(self):
        self.edit_handler = EditHandler(form=True, instance=True)
        self.edit_handler.render = lambda: "foo"

    def test_widget_overrides(self):
        result = EditHandler.widget_overrides()
        self.assertEqual(result, {})

    def test_required_formsets(self):
        result = EditHandler.required_formsets()
        self.assertEqual(result, [])

    def test_get_form_class(self):
        result = EditHandler.get_form_class(Page)
        self.assertTrue(issubclass(result, WagtailAdminModelForm))

    def test_edit_handler_init_no_instance(self):
        self.assertRaises(ValueError, EditHandler, form=True)

    def test_edit_handler_init_no_form(self):
        self.assertRaises(ValueError, EditHandler, instance=True)

    def test_object_classnames(self):
        result = self.edit_handler.object_classnames()
        self.assertEqual(result, "")

    def test_field_classnames(self):
        result = self.edit_handler.field_classnames()
        self.assertEqual(result, "")

    def test_field_type(self):
        result = self.edit_handler.field_type()
        self.assertEqual(result, "")

    def test_render_as_object(self):
        result = self.edit_handler.render_as_object()
        self.assertEqual(result, "foo")

    def test_render_as_field(self):
        result = self.edit_handler.render_as_field()
        self.assertEqual(result, "foo")

    def test_render_js(self):
        result = self.edit_handler.render_js()
        self.assertEqual(result, "")

    def test_rendered_fields(self):
        result = self.edit_handler.rendered_fields()
        self.assertEqual(result, [])

    def test_render_missing_fields(self):
        fake_form = self.FakeForm()
        fake_form["foo"] = "bar"
        self.edit_handler.form = fake_form
        self.assertEqual(self.edit_handler.render_missing_fields(), "bar")

    def test_render_form_content(self):
        fake_form = self.FakeForm()
        fake_form["foo"] = "bar"
        self.edit_handler.form = fake_form
        self.assertEqual(self.edit_handler.render_form_content(), "foobar")


class TestBaseCompositeEditHandler(TestCase):
    def setUp(self):
        mock = MagicMock()
        mock.widget_overrides.return_value = {'foo': 'bar'}
        mock.required_formsets.return_value = {'baz': 'quux'}
        BaseCompositeEditHandler.children = [mock]
        self.base_composite_edit_handler = BaseCompositeEditHandler(
            instance=True,
            form=True)

    def tearDown(self):
        BaseCompositeEditHandler.children = None

    def test_object_classnames_no_classname(self):
        result = self.base_composite_edit_handler.object_classnames()
        self.assertEqual(result, "multi-field")

    def test_object_classnames(self):
        self.base_composite_edit_handler.classname = "foo"
        result = self.base_composite_edit_handler.object_classnames()
        self.assertEqual(result, "multi-field foo")

    def test_widget_overrides(self):
        result = self.base_composite_edit_handler.widget_overrides()
        self.assertEqual(result, {'foo': 'bar'})

    def test_required_formsets(self):
        result = self.base_composite_edit_handler.required_formsets()
        self.assertEqual(result, ['baz'])


class TestBaseTabbedInterface(TestCase):
    class FakeChild(object):
        class FakeGrandchild(object):
            def render_js(self):
                return "foo"

            def rendered_fields(self):
                return ["bar"]

        def __call__(self, *args, **kwargs):
            fake_grandchild = self.FakeGrandchild()
            return fake_grandchild

    def test_render(self):
        mock = MagicMock()
        BaseTabbedInterface.children = [mock]
        self.base_tabbed_interface = BaseTabbedInterface(
            instance=True,
            form=True)
        result = self.base_tabbed_interface.render()
        self.assertRegexpMatches(result, '<ul')
        self.assertRegexpMatches(result, '<li')
        self.assertRegexpMatches(result, '<div')

    def test_render_js(self):
        fake_child = self.FakeChild()
        BaseTabbedInterface.children = [fake_child]
        self.base_tabbed_interface = BaseTabbedInterface(
            instance=True,
            form=True)
        result = self.base_tabbed_interface.render_js()
        self.assertEqual(result, "foo")

    def test_rendered_fields(self):
        fake_child = self.FakeChild()
        BaseTabbedInterface.children = [fake_child]
        self.base_tabbed_interface = BaseTabbedInterface(
            instance=True,
            form=True)
        result = self.base_tabbed_interface.rendered_fields()
        self.assertEqual(result, ["bar"])


class TestTabbedInterface(TestCase):
    def test_tabbed_interface(self):
        tabbed_interface = TabbedInterface(['foo'])
        self.assertTrue(issubclass(tabbed_interface, BaseTabbedInterface))


class TestObjectList(TestCase):
    def test_object_list(self):
        object_list = ObjectList(['foo'])
        self.assertTrue(issubclass(object_list, BaseObjectList))


class TestBaseFieldPanel(TestCase):
    class FakeClass(object):
        required = False

    class FakeField(object):
        label = 'label'
        help_text = 'help text'

    def setUp(self):
        fake_field = self.FakeField()
        BaseFieldPanel.field_name = 'barbecue'
        self.base_field_panel = BaseFieldPanel(
            instance=True,
            form={'barbecue': fake_field})

    def test_object_classnames_no_classname(self):
        result = self.base_field_panel.object_classnames()
        self.assertEqual(result, "single-field")

    def test_object_classnames(self):
        self.base_field_panel.classname = "bar"
        result = self.base_field_panel.object_classnames()
        self.assertEqual(result, "single-field bar")

    def test_field_type(self):
        fake_object = self.FakeClass()
        another_fake_object = self.FakeClass()
        fake_object.field = another_fake_object
        self.base_field_panel.bound_field = fake_object
        self.assertEqual(self.base_field_panel.field_type(), 'fake_class')

    def test_field_classnames(self):
        fake_object = self.FakeClass()
        another_fake_object = self.FakeClass()
        another_fake_object.required = True
        fake_object.errors = True
        fake_object.field = another_fake_object
        self.base_field_panel.bound_field = fake_object
        self.assertEqual(self.base_field_panel.field_classnames(),
                         'fake_class required error')


class TestFieldPanel(TestCase):
    class FakeClass(object):
        required = False

    class FakeField(object):
        label = 'label'
        help_text = 'help text'
        errors = ['errors']
        id_for_label = 'id for label'

    def setUp(self):
        fake_field = self.FakeField()
        fake_field.field = self.FakeClass()
        self.field_panel = FieldPanel('barbecue', 'snowman')(
            instance=True,
            form={'barbecue': fake_field})

    def test_render_as_object(self):
        result = self.field_panel.render_as_object()
        self.assertRegexpMatches(result,
                                 '<legend>label</legend>')
        self.assertRegexpMatches(result,
                                 '<li class="fake_class error">')
        self.assertRegexpMatches(result,
                                 '<p class="error-message">')

    def test_render_js(self):
        field = self.FakeField()
        bound_field = self.FakeField()
        widget = FriendlyDateInput()
        field.widget = widget
        bound_field.field = field
        self.field_panel.bound_field = bound_field
        result = self.field_panel.render_js()
        self.assertEqual(result,
                         "initFriendlyDateChooser(fixPrefix('id for label'));")

    def test_render_js_unknown_widget(self):
        field = self.FakeField()
        bound_field = self.FakeField()
        widget = self.FakeField()
        field.widget = widget
        bound_field.field = field
        self.field_panel.bound_field = bound_field
        result = self.field_panel.render_js()
        self.assertEqual(result,
                         '')

    def test_render_as_field(self):
        field = self.FakeField()
        bound_field = self.FakeField()
        bound_field.field = field
        self.field_panel.bound_field = bound_field
        result = self.field_panel.render_as_field()
        self.assertRegexpMatches(result,
                                 '<p class="help">help text</p>')
        self.assertRegexpMatches(result,
                                 '<span>errors</span>')

    def test_rendered_fields(self):
        result = self.field_panel.rendered_fields()
        self.assertEqual(result, ['barbecue'])


class TestRichTextFieldPanel(TestCase):
    class FakeField(object):
        label = 'label'
        help_text = 'help text'
        errors = ['errors']
        id_for_label = 'id for label'

    def test_render_js(self):
        fake_field = self.FakeField()
        rich_text_field_panel = RichTextFieldPanel('barbecue')(
            instance=True,
            form={'barbecue': fake_field})
        result = rich_text_field_panel.render_js()
        self.assertEqual(result,
                         "makeRichTextEditable(fixPrefix('id for label'));")


class TestPageChooserPanel(TestCase):
    class FakeField(object):
        label = 'label'
        help_text = 'help text'
        errors = ['errors']
        id_for_label = 'id for label'

    class FakeInstance(object):
        class FakePage(object):
            class FakeParent(object):
                id = 1

            def get_parent(self):
                return self.FakeParent()

        def __init__(self):
            fake_page = self.FakePage()
            self.barbecue = fake_page


    def setUp(self):
        fake_field = self.FakeField()
        fake_instance = self.FakeInstance()
        self.page_chooser_panel = PageChooserPanel('barbecue')(
            instance=fake_instance,
            form={'barbecue': fake_field})

    def test_render_js(self):
        result = self.page_chooser_panel.render_js()
        self.assertEqual(result, "createPageChooser(fixPrefix('id for label'), 'wagtailcore.page', 1);")
