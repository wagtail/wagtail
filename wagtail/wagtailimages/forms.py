from django import forms
from django.forms.models import modelform_factory
from django.utils.translation import ugettext as _

from wagtail.wagtailimages.models import get_image_model
from wagtail.wagtailimages.formats import get_image_formats


def get_image_form():
    return modelform_factory(
        get_image_model(),
        # set the 'file' widget to a FileInput rather than the default ClearableFileInput
        # so that when editing, we don't get the 'currently: ...' banner which is
        # a bit pointless here
        widgets={
            'file': forms.FileInput(),
            'focal_point_x': forms.HiddenInput(attrs={'class': 'focal_point_x'}),
            'focal_point_y': forms.HiddenInput(attrs={'class': 'focal_point_y'}),
            'focal_point_width': forms.HiddenInput(attrs={'class': 'focal_point_width'}),
            'focal_point_height': forms.HiddenInput(attrs={'class': 'focal_point_height'}),
        })


def get_image_form_for_multi():
    # exclude the file widget
    return modelform_factory(get_image_model(), exclude=('file',), widgets={
        'focal_point_x': forms.HiddenInput(attrs={'class': 'focal_point_x'}),
        'focal_point_y': forms.HiddenInput(attrs={'class': 'focal_point_y'}),
        'focal_point_width': forms.HiddenInput(attrs={'class': 'focal_point_width'}),
        'focal_point_height': forms.HiddenInput(attrs={'class': 'focal_point_height'}),
    })


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


class URLGeneratorForm(forms.Form):
    filter_method = forms.ChoiceField(
        label=_("Filter"),
        choices=(
            ('original', _("Original size")),
            ('width', _("Resize to width")),
            ('height', _("Resize to height")),
            ('min', _("Resize to min")),
            ('max', _("Resize to max")),
            ('fill', _("Resize to fill")),
        ),
    )
    width = forms.IntegerField(_("Width"), min_value=0)
    height = forms.IntegerField(_("Height"), min_value=0)
    closeness = forms.IntegerField(_("Closeness"), min_value=0, initial=0)
