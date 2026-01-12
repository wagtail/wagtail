(image_rendition_field)=

# ImageRenditionField

`ImageRenditionField` is a Django REST Framework field used in Wagtail's API to generate and serialize image renditions. It creates a new version of an image with specified transformations applied (such as resizing, cropping, or format conversion) and returns the rendition details as a structured dictionary.

## Basic usage

The field is typically used in serializers when building custom API endpoints:

```python
from rest_framework import serializers
from wagtail.images.api.fields import ImageRenditionField


class MyPageSerializer(serializers.ModelSerializer):
    thumbnail = ImageRenditionField('fill-100x100', source='photo')
    hero_image = ImageRenditionField('width-800|format-webp', source='photo')
    
    class Meta:
        model = MyPage
        fields = ['title', 'thumbnail', 'hero_image']
```

## Output format

The field serializes to a dictionary containing the following properties:

```json
{
    "url": "/media/images/myimage.max-165x165.jpg",
    "full_url": "https://media.example.com/media/images/myimage.max-165x165.jpg",
    "width": 165,
    "height": 100,
    "alt": "Image alt text"
}
```

If there is an error with the source image, the field will return an error indicator:

```json
{
    "error": "SourceImageIOError"
}
```

## Arguments

### `filter_spec`

**Required.** A string specifying the image transformations to apply. The filter spec consists of one or more operations separated by the pipe (`|`) character.

#### Available operations

The filter spec supports the same operations available in Wagtail's image template tags. For a comprehensive list of resizing methods, see [](available_resizing_methods).

**Resize operations:**

- `max-<width>x<height>` - Fit within the given dimensions
- `min-<width>x<height>` - Cover the given dimensions
- `width-<width>` - Resize to the specified width
- `height-<height>` - Resize to the specified height
- `scale-<percentage>` - Scale to a percentage of original size
- `fill-<width>x<height>` - Crop and resize to exact dimensions
- `original` - Use the original image without resizing

**Format operations:**

- `format-jpeg` - Convert to JPEG format
- `format-png` - Convert to PNG format
- `format-webp` - Convert to WebP format
- `format-avif` - Convert to AVIF format
- `format-gif` - Convert to GIF format
- `format-ico` - Convert to ICO format (useful for favicons)
- `format-webp-lossless` - Convert to lossless WebP
- `format-avif-lossless` - Convert to lossless AVIF

See [](output_image_format) for more details on format conversion.

**Quality operations:**

- `jpegquality-<quality>` - Set JPEG quality (0-100)
- `webpquality-<quality>` - Set WebP quality (0-100)
- `avifquality-<quality>` - Set AVIF quality (0-100)

See [](image_quality) for more information about quality settings.

**Other operations:**

- `bgcolor-<hex>` - Set background color for transparent images (see [](image_background_colour))
- Custom operations registered via the `register_image_operations` hook (see [](custom_image_filters))

#### Chaining operations

Multiple operations can be chained together using the pipe (`|`) character. Operations are applied in the order they appear:

```python
# Resize to 400px wide, convert to WebP, and set quality to 60
ImageRenditionField('width-400|format-webp|webpquality-60')

# Create a 200x200 thumbnail in AVIF format with quality 50
ImageRenditionField('fill-200x200|format-avif|avifquality-50')
```

#### Examples

```python
from wagtail.images.api.fields import ImageRenditionField

class BlogPageSerializer(serializers.ModelSerializer):
    # Simple resize
    thumbnail = ImageRenditionField('fill-100x100', source='header_image')
    
    # Resize with format conversion
    hero_webp = ImageRenditionField('max-1200x800|format-webp', source='header_image')
    
    # Multiple formats for responsive images
    thumbnail_avif = ImageRenditionField('fill-200x200|format-avif|avifquality-50', source='header_image')
    thumbnail_webp = ImageRenditionField('fill-200x200|format-webp|webpquality-60', source='header_image')
    thumbnail_jpeg = ImageRenditionField('fill-200x200|format-jpeg|jpegquality-80', source='header_image')
    
    class Meta:
        model = BlogPage
        fields = ['title', 'thumbnail', 'hero_webp', 'thumbnail_avif', 'thumbnail_webp', 'thumbnail_jpeg']
```

### `preserve_svg`

**Optional.** Boolean, defaults to `False`.

When set to `True`, if the source image is an SVG, only operations that are safe for SVGs will be applied. Operations that would normally rasterize the image (such as format conversion) will be skipped.

The following operations are considered "SVG-safe" and will be applied even when `preserve_svg=True`:

- `max`
- `min`
- `width`
- `height`
- `scale`

```python
class MySerializer(serializers.ModelSerializer):
    # For SVG images, only the resize will be applied
    # For raster images, both resize and format conversion will be applied
    image = ImageRenditionField('width-400|format-webp', preserve_svg=True, source='logo')
```

This is particularly useful when you have a mix of SVG and raster images and want to apply format conversions to raster images while preserving SVGs in their original format.

See [](svg_images) for more information about SVG handling in Wagtail.

## See also

- [](image_tag) - Using images in templates
- [](available_resizing_methods) - Complete list of resize operations
- [](output_image_format) - Image format conversion options
- [](image_quality) - Quality settings for different formats
- [](custom_image_filters) - Creating custom image operations
- [](svg_images) - Working with SVG images
