import json

from django import forms
from django.conf import settings
from django.forms.models import modelform_factory
from django.utils.text import capfirst
from django.utils.translation import gettext as _

from wagtail.admin.forms.collections import (
    BaseCollectionMemberForm,
    CollectionChoiceField,
    collection_member_permission_formset_factory,
)
from wagtail.admin.forms.tags import validate_tag_length
from wagtail.admin.widgets import AdminTagWidget
from wagtail.images.fields import WagtailImageField
from wagtail.images.formats import get_image_formats
from wagtail.images.models import Image
from wagtail.images.permissions import permission_policy as images_permission_policy
from wagtail.models import Collection
from wagtail.search import index as search_index


# Callback to allow us to override the default form field for the image file field and collection field.
def formfield_for_dbfield(db_field, **kwargs):
    # Check if this is the file field
    if db_field.name == "file":
        return WagtailImageField(label=capfirst(db_field.verbose_name), **kwargs)
    elif db_field.name == "collection":
        return CollectionChoiceField(
            label=_("Collection"),
            queryset=Collection.objects.all(),
            empty_label=None,
            **kwargs,
        )

    # For all other fields, just call its formfield() method.
    return db_field.formfield(**kwargs)


class BaseImageForm(BaseCollectionMemberForm):
    permission_policy = images_permission_policy

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_file = self.instance.file

    def save(self, commit=True):
        if "file" in self.changed_data:
            self.instance._set_image_file_metadata()

        super().save(commit=commit)

        if commit:
            if "file" in self.changed_data and self.original_file:
                # if providing a new image file, delete the old one and all renditions.
                # NB Doing this via original_file.delete() clears the file field,
                # which definitely isn't what we want...
                self.original_file.storage.delete(self.original_file.name)
                self.instance.renditions.all().delete()

            # Reindex the image to make sure all tags are indexed
            search_index.insert_or_update_object(self.instance)

        return self.instance

    class Meta:
        # set the 'file' widget to a FileInput rather than the default ClearableFileInput
        # so that when editing, we don't get the 'currently: ...' banner which is
        # a bit pointless here
        widgets = {
            "tags": AdminTagWidget,
            "file": forms.FileInput(),
            "focal_point_x": forms.HiddenInput(attrs={"class": "focal_point_x"}),
            "focal_point_y": forms.HiddenInput(attrs={"class": "focal_point_y"}),
            "focal_point_width": forms.HiddenInput(
                attrs={"class": "focal_point_width"}
            ),
            "focal_point_height": forms.HiddenInput(
                attrs={"class": "focal_point_height"}
            ),
        }

    def clean_tags(self):
        tags = self.cleaned_data["tags"]
        validate_tag_length(tags)
        return tags


def get_image_base_form():
    base_form_override = getattr(settings, "WAGTAILIMAGES_IMAGE_FORM_BASE", "")
    if base_form_override:
        from django.utils.module_loading import import_string

        base_form = import_string(base_form_override)
    else:
        base_form = BaseImageForm
    return base_form


def get_image_form(model):
    fields = model.admin_form_fields
    if "collection" not in fields:
        # force addition of the 'collection' field, because leaving it out can
        # cause dubious results when multiple collections exist (e.g adding the
        # document to the root collection where the user may not have permission) -
        # and when only one collection exists, it will get hidden anyway.
        fields = list(fields) + ["collection"]

    BaseForm = get_image_base_form()

    # If the base form specifies the 'tags' widget as a plain unconfigured AdminTagWidget,
    # substitute one that correctly passes the tag model used on the image model.
    # (If the widget has been overridden via WAGTAILIMAGES_IMAGE_FORM_BASE, leave it
    # alone and trust that they know what they're doing)
    widgets = None
    if BaseForm._meta.widgets.get("tags") == AdminTagWidget:
        tag_model = model._meta.get_field("tags").related_model
        widgets = BaseForm._meta.widgets.copy()
        widgets["tags"] = AdminTagWidget(tag_model=tag_model)

    return modelform_factory(
        model,
        form=BaseForm,
        fields=fields,
        widgets=widgets,
        formfield_callback=formfield_for_dbfield,
    )


def get_image_multi_form(model_class):
    # edit form for use within the multiple uploader
    ImageForm = get_image_form(model_class)

    # Make a new form with the file and focal point fields excluded
    class ImageEditForm(ImageForm):
        class Meta(ImageForm.Meta):
            model = model_class
            exclude = (
                "file",
                "focal_point_x",
                "focal_point_y",
                "focal_point_width",
                "focal_point_height",
            )

    return ImageEditForm


class ImageInsertionForm(forms.Form):
    """
    Form for selecting parameters of the image (e.g. format) prior to insertion
    into a rich text area
    """

    format = forms.ChoiceField(
        label=_("Format"),
        choices=[(format.name, format.label) for format in get_image_formats()],
        widget=forms.RadioSelect,
    )
    image_is_decorative = forms.BooleanField(
        required=False, label=_("Image is decorative")
    )
    alt_text = forms.CharField(required=False, label=_("Alt text"))

    def clean_alt_text(self):
        alt_text = self.cleaned_data["alt_text"]
        image_is_decorative = self.cleaned_data["image_is_decorative"]

        # Empty the alt text value if the image is set to be decorative
        if image_is_decorative:
            return ""
        else:
            # Alt text is required if image is not decorative.
            if not alt_text:
                msg = _(
                    "Please add some alt text for your image or mark it as decorative"
                )
                self.add_error("alt_text", msg)
        return alt_text


class URLGeneratorForm(forms.Form):
    filter_method = forms.ChoiceField(
        label=_("Filter"),
        choices=(
            ("original", _("Original size")),
            ("width", _("Resize to width")),
            ("height", _("Resize to height")),
            ("min", _("Resize to min")),
            ("max", _("Resize to max")),
            ("fill", _("Resize to fill")),
        ),
    )
    width = forms.IntegerField(
        label=_("Width"),
        min_value=0,
        widget=forms.NumberInput(
            attrs={
                "disabled": True,
                "data-w-rules-target": "enable",
                "data-w-rules": json.dumps(
                    {"filter_method": ["width", "max", "min", "fill"]}
                ),
            },
        ),
    )
    height = forms.IntegerField(
        label=_("Height"),
        min_value=0,
        widget=forms.NumberInput(
            attrs={
                "disabled": True,
                "data-w-rules-target": "enable",
                "data-w-rules": json.dumps(
                    {"filter_method": ["height", "max", "min", "fill"]}
                ),
            }
        ),
    )
    closeness = forms.IntegerField(
        label=_("Closeness"),
        min_value=0,
        initial=0,
        widget=forms.NumberInput(
            attrs={
                "disabled": True,
                "data-w-rules-target": "enable",
                "data-w-rules": json.dumps({"filter_method": ["fill"]}),
            }
        ),
    )


GroupImagePermissionFormSet = collection_member_permission_formset_factory(
    Image,
    [
        ("add_image", _("Add"), _("Add/edit images you own")),
        ("change_image", _("Edit"), _("Edit any image")),
        ("choose_image", _("Choose"), _("Select images in choosers")),
    ],
    "wagtailimages/permissions/includes/image_permissions_formset.html",
)
