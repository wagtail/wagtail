from __future__ import absolute_import, unicode_literals

from collections import OrderedDict

import django.forms
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin.forms import WagtailAdminPageForm


class BaseForm(django.forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')

        self.user = kwargs.pop('user', None)
        self.page = kwargs.pop('page', None)

        super(BaseForm, self).__init__(*args, **kwargs)


class FormBuilder(object):
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

    FIELD_TYPES = {
        'singleline': create_singleline_field,
        'multiline': create_multiline_field,
        'date': create_date_field,
        'datetime': create_datetime_field,
        'email': create_email_field,
        'url': create_url_field,
        'number': create_number_field,
        'dropdown': create_dropdown_field,
        'multiselect': create_multiselect_field,
        'radio': create_radio_field,
        'checkboxes': create_checkboxes_field,
        'checkbox': create_checkbox_field,
    }

    @property
    def formfields(self):
        formfields = OrderedDict()

        for field in self.fields:
            options = self.get_field_options(field)

            if field.field_type in self.FIELD_TYPES:
                formfields[field.clean_name] = self.FIELD_TYPES[field.field_type](self, field, options)
            else:
                raise Exception("Unrecognised field type: " + field.field_type)

        return formfields

    def get_field_options(self, field):
        options = {}
        options['label'] = field.label
        options['help_text'] = field.help_text
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

        super(WagtailAdminFormPageForm, self).clean()

        # Check for dupe form field labels - fixes #585
        if 'form_fields' in self.formsets:
            _forms = self.formsets['form_fields'].forms
            for f in _forms:
                f.is_valid()

            for i, form in enumerate(_forms):
                if 'label' in form.changed_data:
                    label = form.cleaned_data.get('label')
                    for idx, ff in enumerate(_forms):
                        # Exclude self
                        if idx != i and label == ff.cleaned_data.get('label'):
                            form.add_error(
                                'label',
                                django.forms.ValidationError(_('There is another field with the label %s, please change one of them.' % label))
                            )
