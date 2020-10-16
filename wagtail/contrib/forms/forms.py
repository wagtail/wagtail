from collections import OrderedDict

import django.forms

from django.conf import settings
from django.utils.html import conditional_escape
from django.utils.translation import gettext_lazy as _

from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.contrib.forms.utils import get_field_clean_name


class BaseForm(django.forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')

        self.user = kwargs.pop('user', None)
        self.page = kwargs.pop('page', None)

        super().__init__(*args, **kwargs)


class FormBuilder:
    def __init__(self, fields):
        self.fields = fields

    def create_singleline_field(self, field, options):
        # TODO: This is a default value - it may need to be changed
        options['max_length'] = 255
        return django.forms.CharField(**options)

    def create_multiline_field(self, field, options):
        return django.forms.CharField(widget=django.forms.Textarea, **options)

    def create_date_field(self, field, options):
        return django.forms.DateField(**options)

    def create_datetime_field(self, field, options):
        return django.forms.DateTimeField(**options)

    def create_email_field(self, field, options):
        return django.forms.EmailField(**options)

    def create_url_field(self, field, options):
        return django.forms.URLField(**options)

    def create_number_field(self, field, options):
        return django.forms.DecimalField(**options)

    def create_dropdown_field(self, field, options):
        options['choices'] = map(
            lambda x: (x.strip(), x.strip()),
            field.choices.split(',')
        )
        return django.forms.ChoiceField(**options)

    def create_multiselect_field(self, field, options):
        options['choices'] = map(
            lambda x: (x.strip(), x.strip()),
            field.choices.split(',')
        )
        return django.forms.MultipleChoiceField(**options)

    def create_radio_field(self, field, options):
        options['choices'] = map(
            lambda x: (x.strip(), x.strip()),
            field.choices.split(',')
        )
        return django.forms.ChoiceField(widget=django.forms.RadioSelect, **options)

    def create_checkboxes_field(self, field, options):
        options['choices'] = [(x.strip(), x.strip()) for x in field.choices.split(',')]
        options['initial'] = [x.strip() for x in field.default_value.split(',')]
        return django.forms.MultipleChoiceField(
            widget=django.forms.CheckboxSelectMultiple, **options
        )

    def create_checkbox_field(self, field, options):
        return django.forms.BooleanField(**options)

    def create_hidden_field(self, field, options):
        return django.forms.CharField(widget=django.forms.HiddenInput, **options)

    def get_create_field_function(self, type):
        """
            Takes string of field type and returns a Django Form Field Instance.
            Assumes form field creation functions are in the format:
            'create_fieldtype_field'
        """
        create_field_function = getattr(self, 'create_%s_field' % type, None)
        if create_field_function:
            return create_field_function
        else:
            import inspect
            method_list = [
                f[0] for f in
                inspect.getmembers(self.__class__, inspect.isfunction)
                if f[0].startswith('create_') and f[0].endswith('_field')
            ]
            raise AttributeError(
                "Could not find function matching format \
                create_<fieldname>_field for type: " + type,
                "Must be one of: " + ", ".join(method_list)
            )

    @property
    def formfields(self):
        formfields = OrderedDict()

        for field in self.fields:
            options = self.get_field_options(field)
            create_field = self.get_create_field_function(field.field_type)
            formfields[field.clean_name] = create_field(field, options)

        return formfields

    def get_field_options(self, field):
        options = {}
        options['label'] = field.label
        if getattr(settings, 'WAGTAILFORMS_HELP_TEXT_ALLOW_HTML', False):
            options['help_text'] = field.help_text
        else:
            options['help_text'] = conditional_escape(field.help_text)
        options['required'] = field.required
        options['initial'] = field.default_value
        return options

    def get_form_class(self):
        return type(str('WagtailForm'), (BaseForm,), self.formfields)


class SelectDateForm(django.forms.Form):
    date_from = django.forms.DateTimeField(
        required=False,
        widget=django.forms.DateInput(attrs={'placeholder': _('Date from')})
    )
    date_to = django.forms.DateTimeField(
        required=False,
        widget=django.forms.DateInput(attrs={'placeholder': _('Date to')})
    )


class WagtailAdminFormPageForm(WagtailAdminPageForm):

    def clean(self):

        super().clean()

        # Check for dupe form field labels - fixes #585
        if 'form_fields' in self.formsets:
            _forms = self.formsets['form_fields'].forms
            for f in _forms:
                f.is_valid()

            for i, form in enumerate(_forms):
                if 'label' in form.changed_data:
                    label = form.cleaned_data.get('label')
                    clean_name = get_field_clean_name(label)
                    for idx, ff in enumerate(_forms):
                        # Exclude self
                        ff_clean_name = get_field_clean_name(ff.cleaned_data.get('label'))
                        if idx != i and clean_name == ff_clean_name:
                            form.add_error(
                                'label',
                                django.forms.ValidationError(_('There is another field with the label %s, please change one of them.') % label)
                            )
