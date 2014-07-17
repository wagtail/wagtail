from wagtail.wagtailimages.backends import get_image_backend
from wagtail.wagtailimages.utils import parse_filter_spec


def process_image(input_file, output_file, filter_spec, backend_name='default'):
    # Get the image backend
    backend = get_image_backend(backend_name)

    # Parse the filter spec
    method_name, method_arg = parse_filter_spec(filter_spec)

    # Load image
    image = backend.open_image(input_file)
    file_format = image.format

    # Call method
    method = getattr(backend, method_name)
    image = method(image, method_arg)

    # Save image
    backend.save_image(image, output_file, file_format) 

    return output_file
