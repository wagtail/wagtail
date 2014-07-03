from mock import MagicMock

from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured
from django.forms.widgets import HiddenInput

from wagtail.wagtailadmin.edit_handlers import (
    get_form_for_model,
    extract_panel_definitions_from_model_class,
    BaseFieldPanel,
    FieldPanel,
    RichTextFieldPanel,
    EditHandler,
    WagtailAdminModelForm,
    BaseTabbedInterface,
    TabbedInterface,
    BaseObjectList,
    ObjectList,
    PageChooserPanel,
    InlinePanel
)
from wagtail.wagtailcore.models import Page, Site


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


class TestTabbedInterface(TestCase):
    class FakeChild(object):
        class FakeGrandchild(object):
            def render_js(self):
                return "rendered js"

            def rendered_fields(self):
                return ["rendered fields"]

        def widget_overrides(self):
            return {'foo': 'bar'}

        def required_formsets(self):
            return {'baz': 'quux'}

        def __call__(self, *args, **kwargs):
            fake_grandchild = self.FakeGrandchild()
            return fake_grandchild

    def setUp(self):
        fake_child = self.FakeChild()
        self.TabbedInterfaceClass = TabbedInterface([fake_child])
        self.tabbed_interface = self.TabbedInterfaceClass(instance=True,
                                                          form=True)

    def test_tabbed_interface(self):
        self.assertTrue(issubclass(self.TabbedInterfaceClass,
                                   BaseTabbedInterface))

    def test_widget_overrides(self):
        result = self.tabbed_interface.widget_overrides()
        self.assertEqual(result, {'foo': 'bar'})

    def test_required_formsets(self):
        result = self.tabbed_interface.required_formsets()
        self.assertEqual(result, ['baz'])

    def test_render(self):
        result = self.tabbed_interface.render()
        self.assertIn('<div class="tab-content">', result)

    def test_render_js(self):
        result = self.tabbed_interface.render_js()
        self.assertEqual(result, 'rendered js')

    def test_rendered_fields(self):
        result = self.tabbed_interface.rendered_fields()
        self.assertEqual(result, ["rendered fields"])


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

    def test_render_js(self):
        result = self.field_panel.render_js()
        self.assertEqual(result, "")

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

            name = 'fake page'

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
        self.assertEqual(result,
                         "createPageChooser(fixPrefix('id for label'), 'wagtailcore.page', 1);")

    def test_get_chosen_item(self):
        result = self.page_chooser_panel.get_chosen_item()
        self.assertEqual(result.name, 'fake page')

    def test_render_as_field(self):
        result = self.page_chooser_panel.render_as_field()
        self.assertIn('<p class="help">help text</p>', result)
        self.assertIn('<span>errors</span>', result)

    def test_widget_overrides(self):
        result = self.page_chooser_panel.widget_overrides()
        self.assertEqual(result, {'barbecue': HiddenInput})

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

                def __repr__(self):
                    return 'fake form'

            forms = [FakeForm()]
            empty_form = FakeForm()
            can_order = True

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

    def setUp(self):
        self.fake_field = self.FakeField()
        self.fake_instance = self.FakeInstance()
        self.mock_panel = MagicMock()
        self.mock_panel.name = 'mock panel'
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

    def test_render_js(self):
        inline_panel = InlinePanel(self.mock_model,
                                   'formset')(
            instance=self.fake_instance,
            form=self.fake_field)
        self.assertIn('var panel = InlinePanel({',
                      inline_panel.render_js())
