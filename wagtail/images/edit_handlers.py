from django.template.loader import render_to_string

from wagtail.admin.compare import ForeignObjectComparison
from wagtail.admin.edit_handlers import BaseChooserPanel, InlinePanel

from .widgets import AdminImageChooser


class ImageChooserPanel(BaseChooserPanel):
    object_type_name = "image"

    def widget_overrides(self):
        return {self.field_name: AdminImageChooser}

    def get_comparison_class(self):
        return ImageFieldComparison


class ImageFieldComparison(ForeignObjectComparison):
    def htmldiff(self):
        image_a, image_b = self.get_objects()

        return render_to_string("wagtailimages/widgets/compare.html", {
            'image_a': image_a,
            'image_b': image_b,
        })


class MultipleImagesPanel(InlinePanel):
    template = "wagtailimages/edit_handlers/multiple_images_panel.html"
    js_template = "wagtailimages/edit_handlers/multiple_images_panel.js"

    def __init__(self, relation_name, image_field_name=None, *args, **kwargs):
        kwargs['relation_name'] = relation_name
        super().__init__(*args, **kwargs)
        self.image_field_name = image_field_name

    def clone(self):
        # Need to track changes to this method in the InlinePanel class
        return self.__class__(
            relation_name=self.relation_name,
            image_field_name=self.image_field_name,
            panels=self.panels,
            heading=self.heading,
            label=self.label,
            help_text=self.help_text,
            min_num=self.min_num,
            max_num=self.max_num,
            classname=self.classname,
        )

    def render_extension(self):
        from . import get_image_model
        from .permissions import permission_policy
        from .fields import ALLOWED_EXTENSIONS
        from .forms import get_image_form

        Image = get_image_model()
        ImageForm = get_image_form(Image)

        collections_to_choose = None

        collections = permission_policy.collections_user_has_permission_for(self.request.user, 'add')
        if len(collections) > 1:
            collections_to_choose = collections
        else:
            # no need to show a collections chooser
            collections_to_choose = None

        form = ImageForm(user=self.request.user)

        return {
            'max_filesize': form.fields['file'].max_upload_size,
            'help_text': form.fields['file'].help_text,
            'allowed_extensions': ALLOWED_EXTENSIONS,
            'error_max_file_size': form.fields['file'].error_messages['file_too_large_unknown_size'],
            'error_accepted_file_types': form.fields['file'].error_messages['invalid_image'],
            'collections': collections_to_choose,
        }

    def render_extension_js_init(self):
        return self.render_extension()

    class Media:
        css = {
            'screen': ('wagtailimages/css/add-multiple.css',)
        }

        js = (
            'wagtailimages/js/vendor/load-image.min.js',
            'wagtailimages/js/vendor/canvas-to-blob.min.js',
            'wagtailadmin/js/vendor/jquery.iframe-transport.js',
            'wagtailadmin/js/vendor/jquery.fileupload.js',
            'wagtailadmin/js/vendor/jquery.fileupload-process.js',
            'wagtailimages/js/vendor/jquery.fileupload-image.js',
            'wagtailimages/js/vendor/jquery.fileupload-validate.js',
            'wagtailadmin/js/vendor/tag-it.js'
        )
