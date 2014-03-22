import django.forms
from django.utils.datastructures import SortedDict
from django.utils.text import slugify
from unidecode import unidecode

class FormBuilder():
    formfields = SortedDict()
    def __init__(self, fields):
        for field in fields:
            options = self.get_options(field)
            f = getattr(self, "create_"+field.field_type+"_field" )(field, options)
            # unidecode will return an ascii string while slugify wants a unicode string
            # on the other hand, slugify returns a safe-string which will be converted
            # to a normal str
            field_name = str(slugify(unicode(unidecode(field.label))))
            self.formfields[field_name] = f

    def get_options(self, field):
        options = {}
        options['label'] = field.label
        options['help_text'] = field.help_text
        options['required'] = field.required
        options['initial'] = field.default_value
        return options

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
        options['choices'] = map(lambda x: (x.strip(),x.strip()), field.choices.split(','))
        return django.forms.ChoiceField(**options)
    
    def create_radio_field(self, field, options):
        options['choices'] = map(lambda x: (x.strip(),x.strip()), field.choices.split(','))
        return django.forms.ChoiceField(widget=django.forms.RadioSelect, **options)
        
    def create_checkboxes_field(self, field, options):
        options['choices'] = [ (x.strip(), x.strip()) for x in field.choices.split(',')]
        options['initial'] = [ x.strip() for x in field.default_value.split(',') ]
        return django.forms.MultipleChoiceField(widget=django.forms.CheckboxSelectMultiple, **options)
    
    def create_checkbox_field(self, field, options):
        return django.forms.BooleanField(**options)
        
    def get_form_class(self):   
        return type('WagtailForm', (django.forms.Form,), self.formfields )
        
class SelectDateForm(django.forms.Form):
    date_from = django.forms.DateField(required=False, widget=django.forms.DateInput(attrs={'placeholder':'Date from'}))
    date_to = django.forms.DateField(required=False, widget=django.forms.DateInput(attrs={'placeholder':'Date to'}))