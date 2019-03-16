from io import BytesIO

from django import forms
from django.core.files.images import ImageFile
from django.forms.models import modelform_factory
from django.utils.text import capfirst
from django.utils.translation import ugettext as _

from wagtail.admin import widgets
from wagtail.admin.forms.collections import (
    BaseCollectionMemberForm, collection_member_permission_formset_factory)
from wagtail.images.fields import WagtailImageField
from wagtail.images.formats import get_image_formats
from wagtail.images.models import Image
from wagtail.images.permissions import permission_policy as images_permission_policy


# Callback to allow us to override the default form field for the image file field
def formfield_for_dbfield(db_field, **kwargs):
    # Check if this is the file field
    if db_field.name == 'file':
        return WagtailImageField(label=capfirst(db_field.verbose_name), **kwargs)

    # For all other fields, just call its formfield() method.
    return db_field.formfield(**kwargs)


class BaseImageForm(BaseCollectionMemberForm):
    permission_policy = images_permission_policy

    rotation = forms.IntegerField(
        widget=forms.HiddenInput(attrs={'class': 'rotation'}),
        help_text="Press to rotate this image clockwise by 90 degrees.",
        required=False,
    )

    def rotated_willow_image(self, willow_image):
        """
        Return a rotated image, of matching file type
        for the image passed in.
        """

        file_extension = self.instance.filename.split(".")[-1].lower()

        formats = {
            "gif":  willow_image.save_as_gif,
            "jpg": willow_image.save_as_jpeg,
            "jpeg": willow_image.save_as_jpeg,
            "png": willow_image.save_as_png,
            "webp": willow_image.save_as_webp,
        }

        res = formats[file_extension](BytesIO())

        return ImageFile(res.f, name=self.instance.file.name)


    def remove_stale_image_files(self):
        """
        Remove old non-rotated renditions, if they exist
        """
        self.instance.renditions.all().delete()
        self.instance.file.storage.delete(self.instance.file.name)


    def save(self, *args, **kwargs):
        """
        Save form, handling case for rotating images
        """

        if 'rotation' in self.changed_data:
            degrees = self.cleaned_data['rotation']
            # rotate the new image, and then put the new
            # image in place of the previous one
            willow_image = self.instance.rotate(degrees)
            rotated_image_file = self.rotated_willow_image(willow_image)

            self.remove_stale_image_files()
            file_name = self.instance.file.name.split('/')[-1]

            self.instance.file.save(file_name, rotated_image_file, save=True)

            super(BaseImageForm, self).save(*args, **kwargs)

            # update_hash


def get_image_form(model):
    fields = model.admin_form_fields

    if 'collection' not in fields:
        # force addition of the 'collection' field, because leaving it out can
        # cause dubious results when multiple collections exist (e.g adding the
        # document to the root collection where the user may not have permission) -
        # and when only one collection exists, it will get hidden anyway.
        fields = list(fields) + ['collection']

    return modelform_factory(
        model,
        form=BaseImageForm,
        fields=fields,
        formfield_callback=formfield_for_dbfield,
        # set the 'file' widget to a FileInput rather than the default ClearableFileInput
        # so that when editing, we don't get the 'currently: ...' banner which is
        # a bit pointless here
        widgets={
            'tags': widgets.AdminTagWidget,
            'file': forms.FileInput(),
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
    width = forms.IntegerField(label=_("Width"), min_value=0)
    height = forms.IntegerField(label=_("Height"), min_value=0)
    closeness = forms.IntegerField(label=_("Closeness"), min_value=0, initial=0)


GroupImagePermissionFormSet = collection_member_permission_formset_factory(
    Image,
    [
        ('add_image', _("Add"), _("Add/edit images you own")),
        ('change_image', _("Edit"), _("Edit any image")),
    ],
    'wagtailimages/permissions/includes/image_permissions_formset.html'
)
