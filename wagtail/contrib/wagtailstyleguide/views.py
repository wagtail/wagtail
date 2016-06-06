from __future__ import absolute_import, unicode_literals

from django import forms
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.translation import ugettext as _
from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailadmin.rich_text import get_rich_text_editor_widget
from wagtail.wagtailadmin.widgets import (
    AdminAutoHeightTextInput, AdminDateInput, AdminDateTimeInput, AdminPageChooser, AdminTimeInput)
from wagtail.wagtailcore.models import Page
from wagtail.wagtaildocs.widgets import AdminDocumentChooser
from wagtail.wagtailimages.widgets import AdminImageChooser
from wagtail.wagtailsnippets.widgets import AdminSnippetChooser


class ExampleForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ExampleForm, self).__init__(*args, **kwargs)
        self.fields['page_chooser'].widget = AdminPageChooser()
        self.fields['image_chooser'].widget = AdminImageChooser()
        self.fields['document_chooser'].widget = AdminDocumentChooser()
        self.fields['snippet_chooser'].widget = AdminSnippetChooser(Page)
        self.fields['date'].widget = AdminDateInput()
        self.fields['time'].widget = AdminTimeInput()
        self.fields['datetime'].widget = AdminDateTimeInput()
        self.fields['auto_height_text'].widget = AdminAutoHeightTextInput()
        self.fields['default_rich_text'].widget = get_rich_text_editor_widget('default')

    CHOICES = (
        ('choice1', 'choice 1'),
        ('choice2', 'choice 2'),
    )

    text = forms.CharField(required=True, help_text="help text")
    auto_height_text = forms.CharField(required=True)
    default_rich_text = forms.CharField(required=True)
    url = forms.URLField(required=True)
    email = forms.EmailField(max_length=254)
    date = forms.DateField()
    time = forms.TimeField()
    datetime = forms.DateTimeField()
    select = forms.ChoiceField(choices=CHOICES)
    radio_select = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect)
    boolean = forms.BooleanField(required=False)
    page_chooser = forms.BooleanField(required=True)
    image_chooser = forms.BooleanField(required=True)
    document_chooser = forms.BooleanField(required=True)
    snippet_chooser = forms.BooleanField(required=True)


def index(request):

    form = SearchForm(placeholder=_("Search something"))

    example_form = ExampleForm()

    messages.success(request, _("Success message"), buttons=[
        messages.button('', _('View live')),
        messages.button('', _('Edit'))
    ])
    messages.warning(request, _("Warning message"), buttons=[
        messages.button('', _('View live')),
        messages.button('', _('Edit'))
    ])
    messages.error(request, _("Error message"), buttons=[
        messages.button('', _('View live')),
        messages.button('', _('Edit'))
    ])

    paginator = Paginator(list(range(100)), 10)
    page = paginator.page(2)

    return render(request, 'wagtailstyleguide/base.html', {
        'search_form': form,
        'example_form': example_form,
        'example_page': page,
    })
