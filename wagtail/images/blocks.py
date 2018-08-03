from django.utils.functional import cached_property

from wagtail.core.blocks import ChooserBlock
from wagtail.core.blocks import StructBlock, IntegerBlock #HT START END

from .shortcuts import get_rendition_or_not_found


class ImageChooserBlock(ChooserBlock):
    @cached_property
    def target_model(self):
        from wagtail.images import get_image_model
        return get_image_model()

    @cached_property
    def widget(self):
        from wagtail.images.widgets import AdminImageChooser
        return AdminImageChooser

    def render_basic(self, value, context=None):
        if value:
            return get_rendition_or_not_found(value, 'original').img_tag()
        else:
            return ''

    class Meta:
        icon = "image"

#HT START
class SelectCropChooserBlock(ImageChooserBlock):
    @cached_property
    def widget(self):
        from .widgets import SelectCropAdminImageChooser
        return SelectCropAdminImageChooser

class SelectCropBlock(StructBlock):

    #using get_context to add things to the context at run time and then checking for appropriate values in the context in the images tag
    # works fine when this block is rendering itself.  But if the image value
    # of this block is passed to the image tag directly by another block (as in `image value.my_field_referencing_this_block.image max-300x200` )
    #this block's get_context isn't called and hence cropping doesn't work.  Hence this block must render itself, with the caller providing
    #an image spec template to it in the constructor. 
    #If we wrote a special template tag to allow variables to be passed to a spec filter they could also write something like:
    #`crop_image_tag value.field_ref_this_block.image value.field-ref_this_block.focal_point_x value.field-ref_this_block.focal_point_y \
    #value.field-ref_this_block.focal_point_width value.field-ref_this_block.focal_point_height | other_filters_string`
    #but its a bit ponderous and plus looses the lovely aspect of it just applying crop values automatically if they've been selected in the admin.
    #All in all asking the consumer to specify a simple template to the constructor is the best I've come up with so far.
    #Open to better ideas

    image = SelectCropChooserBlock(required=True)
    focal_point_x = IntegerBlock(required=False, group="hidden-input", label="focal_point_x")
    focal_point_y = IntegerBlock(required=False, group="hidden-input", label="focal_point_y")
    focal_point_width = IntegerBlock(required=False, group="hidden-input", label="focal_point_width")
    focal_point_height = IntegerBlock(required=False, group="hidden-input", label="focal_point_height")

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context) 
        if value['focal_point_x']:
            context['focal_point_x'] = value['focal_point_x']
            context['focal_point_y'] = value['focal_point_y']
            context['focal_point_width'] = value['focal_point_width']
            context['focal_point_height'] = value['focal_point_height']
        #if these values don't exist the crop probably hasn't been selected - just return the context - this means the image tag won't attempt to crop first
        return context

    class Meta:
        icon = "image"
        template = "wagtailimages/widgets/select_crop_no_template.html"#to provide instructions in case they don't provide a template..
        form_classname = "select-crop-image-block struct-block"
        form_template = "wagtailimages/widgets/select_crop_block.html"
#HT END
