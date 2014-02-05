from django.core.files import File
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.utils.safestring import mark_safe
from django.utils.html import escape

import StringIO
import PIL.Image
import os.path

from taggit.managers import TaggableManager

from wagtail.wagtailadmin.taggable import TagSearchable
from wagtail.wagtailimages import image_ops


class AbstractImage(models.Model, TagSearchable):
    title = models.CharField(max_length=255)

    def get_upload_to(self, filename):
        folder_name = 'original_images'
        filename = self.file.field.storage.get_valid_name(filename)

        # replace non-ascii characters in filename with _ , to sidestep issues with filesystem encoding
        filename = "".join((i if ord(i)<128 else '_') for i in filename)

        while len(os.path.join(folder_name, filename)) >= 95:
            prefix, dot, extension = filename.rpartition('.')
            filename = prefix[:-1] + dot + extension
        return os.path.join(folder_name, filename)

    def file_extension_validator(ffile):
        extension = ffile.name.split(".")[-1].lower()
        if extension not in ["gif", "jpg", "jpeg", "png"]:
            raise ValidationError("Not a valid image format. Please use a gif, jpeg or png file instead.")

    file = models.ImageField(upload_to=get_upload_to, width_field='width', height_field='height', validators=[file_extension_validator])
    width = models.IntegerField(editable=False)
    height = models.IntegerField(editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_by_user = models.ForeignKey('auth.User', null=True, blank=True, editable=False)

    tags = TaggableManager(help_text=None, blank=True)

    indexed_fields = {
        'uploaded_by_user_id': {
            'type': 'integer',
            'store': 'yes',
            'indexed': 'no',
            'boost': 0,
        },
    }

    def __unicode__(self):
        return self.title

    def get_rendition(self, filter):
        if not hasattr(filter, 'process_image'):
            # assume we've been passed a filter spec string, rather than a Filter object
            # TODO: keep an in-memory cache of filters, to avoid a db lookup
            filter, created = Filter.objects.get_or_create(spec=filter)

        try:
            rendition = self.renditions.get(filter=filter)
        except ObjectDoesNotExist:
            file_field = self.file
            generated_image_file = filter.process_image(file_field.file)

            rendition, created = self.renditions.get_or_create(
                filter=filter, defaults={'file': generated_image_file})

        return rendition

    def is_portrait(self):
        return (self.width < self.height)
    def is_landscape(self):
        return (self.height < self.width)

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def default_alt_text(self):
        # by default the alt text field (used in rich text insertion) is populated
        # from the title. Subclasses might provide a separate alt field, and
        # override this
        return self.title

    def is_editable_by_user(self, user):
        if user.has_perm('wagtailimages.change_image'):
            # user has global permission to change images
            return True
        elif user.has_perm('wagtailimages.add_image') and self.uploaded_by_user == user:
            # user has image add permission, which also implicitly provides permission to edit their own images
            return True
        else:
            return False

    class Meta:
        abstract=True

class Image(AbstractImage):
    pass


# Receive the pre_delete signal and delete the file associated with the model instance.
@receiver(pre_delete, sender=Image)
def image_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)


def get_image_model():
    from django.conf import settings
    from django.db.models import get_model

    try:
        app_label, model_name = settings.WAGTAILIMAGES_IMAGE_MODEL.split('.')
    except AttributeError:
        return Image
    except ValueError:
        raise ImproperlyConfigured("WAGTAILIMAGES_IMAGE_MODEL must be of the form 'app_label.model_name'")

    image_model = get_model(app_label, model_name)
    if image_model is None:
        raise ImproperlyConfigured("WAGTAILIMAGES_IMAGE_MODEL refers to model '%s' that has not been installed" % settings.WAGTAILIMAGES_IMAGE_MODEL)
    return image_model


class Filter(models.Model):
    """
    Represents an operation that can be applied to an Image to produce a rendition
    appropriate for final display on the website. Usually this would be a resize operation,
    but could potentially involve colour processing, etc.
    """
    spec = models.CharField(max_length=255, db_index=True)

    OPERATION_NAMES = {
        'max': image_ops.resize_to_max,
        'min': image_ops.resize_to_min,
        'width': image_ops.resize_to_width,
        'height': image_ops.resize_to_height,
        'fill': image_ops.resize_to_fill,
    }

    def __init__(self, *args, **kwargs):
        super(Filter, self).__init__(*args, **kwargs)
        self.method = None  # will be populated when needed, by parsing the spec string

    def _parse_spec_string(self):
        # parse the spec string, which is formatted as (method)-(arg),
        # and save the results to self.method and self.method_arg
        try:
            (method_name, method_arg_string) = self.spec.split('-')
            self.method = Filter.OPERATION_NAMES[method_name]

            if method_name in ('max', 'min', 'fill'):
                # method_arg_string is in the form 640x480
                (width, height) = [int(i) for i in method_arg_string.split('x')]
                self.method_arg = (width, height)
            else:
                # method_arg_string is a single number
                self.method_arg = int(method_arg_string)

        except (ValueError, KeyError):
            raise ValueError("Invalid image filter spec: %r" % self.spec)

    def process_image(self, input_file):
        """
        Given an input image file as a django.core.files.File object,
        generate an output image with this filter applied, returning it
        as another django.core.files.File object
        """
        if not self.method:
            self._parse_spec_string()

        input_file.open()
        image = PIL.Image.open(input_file)
        file_format = image.format

        # perform the resize operation
        image = self.method(image, self.method_arg)

        output = StringIO.StringIO()
        image.save(output, file_format)

        # generate new filename derived from old one, inserting the filter spec string before the extension
        input_filename_parts = os.path.basename(input_file.name).split('.')
        filename_without_extension = '.'.join(input_filename_parts[:-1])
        filename_without_extension = filename_without_extension[:60]  # trim filename base so that we're well under 100 chars
        output_filename_parts = [filename_without_extension, self.spec] + input_filename_parts[-1:]
        output_filename = '.'.join(output_filename_parts)

        output_file = File(output, name=output_filename)
        input_file.close()

        return output_file


class AbstractRendition(models.Model):
    filter = models.ForeignKey('Filter', related_name='+')
    file = models.ImageField(upload_to='images', width_field='width', height_field='height')
    width = models.IntegerField(editable=False)
    height = models.IntegerField(editable=False)

    @property
    def url(self):
        return self.file.url

    def img_tag(self):
        return mark_safe(
            '<img src="%s" width="%d" height="%d" alt="%s">' % (escape(self.url), self.width, self.height, escape(self.image.title))
        )

    class Meta:
        abstract=True


class Rendition(AbstractRendition):
    image = models.ForeignKey('Image', related_name='renditions')

    class Meta:
        unique_together = (
            ('image', 'filter'),
        )

# Receive the pre_delete signal and delete the file associated with the model instance.
@receiver(pre_delete, sender=Rendition)
def rendition_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)
