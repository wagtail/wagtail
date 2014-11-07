from django import forms
from django.shortcuts import render
from django.utils.translation import ugettext as _
from wagtail.wagtailadmin import messages
from django.contrib.auth.decorators import permission_required

from wagtail.wagtailadmin.forms import SearchForm


CHOICES = (
    ('choice1', 'choice 1'),
    ('choice2', 'choice 2'),
)

class ExampleForm(forms.Form):
    text = forms.CharField(required=True, help_text="help text")
    url = forms.URLField(required=True)
    email = forms.EmailField(max_length=254)
    date = forms.DateField()
    time = forms.TimeField()
    select = forms.ChoiceField(choices=CHOICES)
    boolean = forms.BooleanField(required=False)

@permission_required('wagtailadmin.access_admin')
def index(request):

    form = SearchForm(placeholder=_("Search something"))

    example_form = ExampleForm()

    messages.success(request, _("Success message"), buttons = [
        messages.button('', _('View live')),
        messages.button('', _('Edit'))
    ])
    messages.warning(request, _("Warning message"), buttons = [
        messages.button('', _('View live')),
        messages.button('', _('Edit'))
    ])
    messages.error(request, _("Error message"), buttons = [
        messages.button('', _('View live')),
        messages.button('', _('Edit'))
    ])

    fake_pagination = {
        'number': 1,
        'previous_page_number': 1,
        'next_page_number': 2,
        'has_previous': True,
        'has_next': True,
        'paginator': {
            'num_pages': 10,
        },
    }
   

    return render(request, 'wagtailstyleguide/base.html', {
        'search_form': form,
        'example_form': example_form,
        'fake_pagination': fake_pagination,
    })
