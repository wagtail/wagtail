from django import forms
from django.forms.models import modelform_factory

from wagtail.wagtailimages.models import get_image_model
from wagtail.wagtailimages.formats import get_image_formats


def get_image_form():
    return modelform_factory(
        get_image_model(),
        # set the 'file' widget to a FileInput rather than the default ClearableFileInput
        # so that when editing, we don't get the 'currently: ...' banner which is
        # a bit pointless here
        widgets={'file': forms.FileInput()})


def get_image_form_for_multi():
    # exclude the file widget
    return modelform_factory( get_image_model(), exclude=('file',))


class ImageInsertionForm(forms.Form):
    """
    Form for selecting parameters of the image (e.g. format) prior to insertion
    into a rich text area
    """
    format = forms.ChoiceField(
        choices=[(format.name, format.label) for format in get_image_formats()],
        widget=forms.RadioSelect
    )
    alt_text = forms.CharField()
