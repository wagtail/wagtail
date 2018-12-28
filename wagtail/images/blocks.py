from django.utils.functional import cached_property

from wagtail.core.blocks import ChooserBlock, IntegerBlock, StructBlock

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


# HT START
class SelectCropChooserBlock(ImageChooserBlock):
    @cached_property
    def widget(self):
        from .widgets import SelectCropAdminImageChooser
        return SelectCropAdminImageChooser


class SelectCropBlock(StructBlock):

    # using get_context to add things to the context at run time and then checking for appropriate values in the context in the images tag
    # Note that if the image value of this block is passed to the image tag directly by another block
    # e.g. `image value.my_field_referencing_this_block.image max-300x200`, this block's get_context isn't called and hence cropping doesn't work.
    # This block must render itself and an image spec template should be passed to it in the constructor.
    # If we wrote a special template tag to allow variables to be passed to a spec filter they could also write something like:
    # `crop_image_tag value.field_ref_this_block.image value.field-ref_this_block.focal_point_x value.field-ref_this_block.focal_point_y \
    # value.field-ref_this_block.focal_point_width value.field-ref_this_block.focal_point_height | other_filters_string`
    # but its a bit ponderous and in general it seems better applying crop values automatically if they've been selected in the admin.
    # All in all asking the consumer to specify a simple template to the constructor is the best I've come up with so far.
    # Open to better ideas

    image = SelectCropChooserBlock(required=True)
    focal_point_x = IntegerBlock(required=False, group="hidden-input", label="focal_point_x")
    focal_point_y = IntegerBlock(required=False, group="hidden-input", label="focal_point_y")
    focal_point_width = IntegerBlock(required=False, group="hidden-input", label="focal_point_width")
    focal_point_height = IntegerBlock(required=False, group="hidden-input", label="focal_point_height")

    crop_point_x = IntegerBlock(required=False, group="hidden-input", label="crop_point_x")
    crop_point_y = IntegerBlock(required=False, group="hidden-input", label="crop_point_y")
    crop_point_width = IntegerBlock(required=False, group="hidden-input", label="crop_point_width")
    crop_point_height = IntegerBlock(required=False, group="hidden-input", label="crop_point_height")

    def add_area_info(self, value, context):
        area_labels = ['crop_point_x', 'crop_point_y', 'crop_point_width', 'crop_point_height']

        if context.get('children'):
            for name, block in context['children'].items():
                if name in area_labels and not isinstance(block.value, int):
                    old_key = name.replace('crop', 'focal')
                    existing_value = context['children'].get(old_key)
                    block.value = existing_value # updates the block value (which will now be picked up in the crop_etc fields of the form and hence the jcrop api)
                    context[name] = existing_value # makes these same values available directly in the template context
                    value[name] = existing_value # updates the parrallel StructValues that wagtail provides 
        else: # we're not in the admin and children isn't populated...
            for name in area_labels:
                v = value.get(name)
                if not isinstance(v, int):
                    v = value.get(name.replace('crop', 'focal'))
                context[k] = v
        
        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        # here we're copying the values from the focal_etc blocks to the crop_ blocks purely for the purposes of preserving the data automatically
        # this whole block can be lost along with the focal_ fields once the pages have been loaded and saved...
        # the entire function can be swopped for the lines below...
        # area_labels = ['crop_point_x', 'crop_point_y', 'crop_point_width', 'crop_point_height']
        # for k in area_labels:
        #     context[k] = value.get(k)
            

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        self.add_area_info(value, context)
        return context

    def get_form_context(self, value, prefix='', errors=None):
        context = super().get_form_context(value, prefix=prefix, errors=errors)
        self.add_area_info(value, context)
        return context

    class Meta:
        icon = "image"
        template = "wagtailimages/widgets/select_crop_no_template.html"  # to provide instructions in case they don't provide a template..
        form_classname = "select-crop-image-block struct-block"
        form_template = "wagtailimages/widgets/select_crop_block.html"
# HT END
