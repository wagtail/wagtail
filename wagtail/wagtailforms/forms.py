import django.forms
from django.utils.datastructures import SortedDict


class BaseForm(django.forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        return super(BaseForm, self).__init__(*args, **kwargs)


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

    @property
    def formfields(self):
        """Create django form fields for each AbstractFormField. """
        formfields = SortedDict()

        for field in self.fields:
            options = self.get_field_options(field)

            # Get the list of available field types from the
            # AbstractFormField.
            field_types = (choice[0] for choice in field.FORM_FIELD_CHOICES)

            if field.field_type not in field_types:
                raise Exception("Invalid Field Type: " + form.field_type)

            # The field type is defined implicitly by a naming convention.
            field_type_fn = "create_%s_field" % (field.field_type,)

            # If the field creation function is not defined, we should tell 
            # the developer before anything else happens.
            if not hasattr(self, field_type_fn):
                raise Exception("Function %s.%s is not defined." %
                        (self.__class__field_type_fn, form.field_type))

            # Create a field
            _fn = getattr(self, field_type_fn)
            formfields[field.clean_name] = _fn(field, options)
        return formfields

    def get_field_options(self, field):
        options = {}
        options['label'] = field.label
        options['help_text'] = field.help_text
        options['required'] = field.required
        options['initial'] = field.default_value
        return options

    def get_form_class(self):
        return type('WagtailForm', (BaseForm,), self.formfields)


class SelectDateForm(django.forms.Form):
    date_from = django.forms.DateTimeField(
        required=False,
        widget=django.forms.DateInput(attrs={'placeholder': 'Date from'})
    )
    date_to = django.forms.DateTimeField(
        required=False,
        widget=django.forms.DateInput(attrs={'placeholder': 'Date to'})
    )
