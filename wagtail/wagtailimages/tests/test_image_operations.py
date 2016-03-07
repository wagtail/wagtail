from mock import Mock

from django.test import TestCase
from django.utils.six import BytesIO
from wagtail.wagtailcore import hooks
from wagtail.wagtailimages import image_operations
from wagtail.wagtailimages.exceptions import InvalidFilterSpecError
from wagtail.wagtailimages.models import Image, Filter
from wagtail.wagtailimages.tests.utils import get_test_image_file


class WillowOperationRecorder(object):
    """
    This class pretends to be a Willow image but instead, it records
    the operations that have been performed on the image for testing
    """
    format_name = 'jpeg'

    def __init__(self, start_size):
        self.ran_operations = []
        self.start_size = start_size

    def __getattr__(self, attr):
        def operation(*args, **kwargs):
            self.ran_operations.append((attr, args, kwargs))
            return self

        return operation

    def get_size(self):
        size = self.start_size

        for operation in self.ran_operations:
            if operation[0] == 'resize':
                size = operation[1][0]
            elif operation[0] == 'crop':
                crop = operation[1][0]
                size = crop[2] - crop[0], crop[3] - crop[1]

        return size


class ImageOperationTestCase(TestCase):
    operation_class = None
    filter_spec_tests = []
    filter_spec_error_tests = []
    run_tests = []

    @classmethod
    def make_filter_spec_test(cls, filter_spec, expected_output):
        def test_filter_spec(self):
            operation = self.operation_class(*filter_spec.split('-'))

            # Check the attributes are set correctly
            for attr, value in expected_output.items():
                self.assertEqual(getattr(operation, attr), value)

        test_name = 'test_filter_%s' % filter_spec
        test_filter_spec.__name__ = test_name
        return test_filter_spec

    @classmethod
    def make_filter_spec_error_test(cls, filter_spec):
        def test_filter_spec_error(self):
            self.assertRaises(InvalidFilterSpecError, self.operation_class, *filter_spec.split('-'))

        test_name = 'test_filter_%s_raises_%s' % (filter_spec, InvalidFilterSpecError.__name__)
        test_filter_spec_error.__name__ = test_name
        return test_filter_spec_error

    @classmethod
    def make_run_test(cls, filter_spec, image_kwargs, expected_output):
        def test_run(self):
            image = Image(**image_kwargs)

            # Make operation
            operation = self.operation_class(*filter_spec.split('-'))

            # Make operation recorder
            operation_recorder = WillowOperationRecorder((image.width, image.height))

            # Run
            operation.run(operation_recorder, image)

            # Check
            self.assertEqual(operation_recorder.ran_operations, expected_output)

        test_name = 'test_run_%s' % filter_spec
        test_run.__name__ = test_name
        return test_run

    @classmethod
    def setup_test_methods(cls):
        if cls.operation_class is None:
            return

        # Filter spec tests
        for args in cls.filter_spec_tests:
            filter_spec_test = cls.make_filter_spec_test(*args)
            setattr(cls, filter_spec_test.__name__, filter_spec_test)

        # Filter spec error tests
        for filter_spec in cls.filter_spec_error_tests:
            filter_spec_error_test = cls.make_filter_spec_error_test(filter_spec)
            setattr(cls, filter_spec_error_test.__name__, filter_spec_error_test)

        # Running tests
        for args in cls.run_tests:
            run_test = cls.make_run_test(*args)
            setattr(cls, run_test.__name__, run_test)


class TestDoNothingOperation(ImageOperationTestCase):
    operation_class = image_operations.DoNothingOperation

    filter_spec_tests = [
        ('original', dict()),
        ('blahblahblah', dict()),
        ('123456', dict()),
    ]

    filter_spec_error_tests = [
        'cannot-take-multiple-parameters',
    ]

    run_tests = [
        ('original', dict(width=1000, height=1000), []),
    ]

TestDoNothingOperation.setup_test_methods()


class TestFillOperation(ImageOperationTestCase):
    operation_class = image_operations.FillOperation

    filter_spec_tests = [
        ('fill-800x600', dict(width=800, height=600, crop_closeness=0)),
        ('hello-800x600', dict(width=800, height=600, crop_closeness=0)),
        ('fill-800x600-c0', dict(width=800, height=600, crop_closeness=0)),
        ('fill-800x600-c100', dict(width=800, height=600, crop_closeness=1)),
        ('fill-800x600-c50', dict(width=800, height=600, crop_closeness=0.5)),
        ('fill-800x600-c1000', dict(width=800, height=600, crop_closeness=1)),
        ('fill-800000x100', dict(width=800000, height=100, crop_closeness=0)),
    ]

    filter_spec_error_tests = [
        'fill',
        'fill-800',
        'fill-abc',
        'fill-800xabc',
        'fill-800x600-',
        'fill-800x600x10',
        'fill-800x600-d100',
    ]

    run_tests = [
        # Basic usage
        ('fill-800x600', dict(width=1000, height=1000), [
            ('crop', ((0, 125, 1000, 875), ), {}),
            ('resize', ((800, 600), ), {}),
        ]),

        # Basic usage with an oddly-sized original image
        # This checks for a rounding precision issue (#968)
        ('fill-200x200', dict(width=539, height=720), [
            ('crop', ((0, 90, 539, 630), ), {}),
            ('resize', ((200, 200), ), {}),
        ]),

        # Closeness shouldn't have any effect when used without a focal point
        ('fill-800x600-c100', dict(width=1000, height=1000), [
            ('crop', ((0, 125, 1000, 875), ), {}),
            ('resize', ((800, 600), ), {}),
        ]),

        # Should always crop towards focal point. Even if no closeness is set
        ('fill-80x60', dict(
            width=1000,
            height=1000,
            focal_point_x=1000,
            focal_point_y=500,
            focal_point_width=0,
            focal_point_height=0,
        ), [
            # Crop the largest possible crop box towards the focal point
            ('crop', ((0, 125, 1000, 875), ), {}),

            # Resize it down to final size
            ('resize', ((80, 60), ), {}),
        ]),

        # Should crop as close as possible without upscaling
        ('fill-80x60-c100', dict(
            width=1000,
            height=1000,
            focal_point_x=1000,
            focal_point_y=500,
            focal_point_width=0,
            focal_point_height=0,
        ), [
            # Crop as close as possible to the focal point
            ('crop', ((920, 470, 1000, 530), ), {}),

            # No need to resize, crop should've created an 80x60 image
        ]),

        # Ditto with a wide image
        # Using a different filter so method name doesn't clash
        ('fill-100x60-c100', dict(
            width=2000,
            height=1000,
            focal_point_x=2000,
            focal_point_y=500,
            focal_point_width=0,
            focal_point_height=0,
        ), [
            # Crop to the right hand side
            ('crop', ((1900, 470, 2000, 530), ), {}),
        ]),

        # Make sure that the crop box never enters the focal point
        ('fill-50x50-c100', dict(
            width=2000,
            height=1000,
            focal_point_x=1000,
            focal_point_y=500,
            focal_point_width=100,
            focal_point_height=20,
        ), [
            # Crop a 100x100 box around the entire focal point
            ('crop', ((950, 450, 1050, 550), ), {}),

            # Resize it down to 50x50
            ('resize', ((50, 50), ), {}),
        ]),

        # Test that the image is never upscaled
        ('fill-1000x800', dict(width=100, height=100), [
            ('crop', ((0, 10, 100, 90), ), {}),
        ]),

        # Test that the crop closeness gets capped to prevent upscaling
        ('fill-1000x800-c100', dict(
            width=1500,
            height=1000,
            focal_point_x=750,
            focal_point_y=500,
            focal_point_width=0,
            focal_point_height=0,
        ), [
            # Crop a 1000x800 square out of the image as close to the
            # focal point as possible. Will not zoom too far in to
            # prevent upscaling
            ('crop', ((250, 100, 1250, 900), ), {}),
        ]),

        # Test for an issue where a ZeroDivisionError would occur when the
        # focal point size, image size and filter size match
        # See: #797
        ('fill-1500x1500-c100', dict(
            width=1500,
            height=1500,
            focal_point_x=750,
            focal_point_y=750,
            focal_point_width=1500,
            focal_point_height=1500,
        ), [
            # This operation could probably be optimised out
            ('crop', ((0, 0, 1500, 1500), ), {}),
        ]),


        # A few tests for single pixel images

        ('fill-100x100', dict(
            width=1,
            height=1,
        ), [
            ('crop', ((0, 0, 1, 1), ), {}),
        ]),

        # This one once gave a ZeroDivisionError
        ('fill-100x150', dict(
            width=1,
            height=1,
        ), [
            ('crop', ((0, 0, 1, 1), ), {}),
        ]),

        ('fill-150x100', dict(
            width=1,
            height=1,
        ), [
            ('crop', ((0, 0, 1, 1), ), {}),
        ]),
    ]

TestFillOperation.setup_test_methods()


class TestMinMaxOperation(ImageOperationTestCase):
    operation_class = image_operations.MinMaxOperation

    filter_spec_tests = [
        ('min-800x600', dict(method='min', width=800, height=600)),
        ('max-800x600', dict(method='max', width=800, height=600)),
    ]

    filter_spec_error_tests = [
        'min',
        'min-800',
        'min-abc',
        'min-800xabc',
        'min-800x600-',
        'min-800x600-c100',
        'min-800x600x10',
    ]

    run_tests = [
        # Basic usage of min
        ('min-800x600', dict(width=1000, height=1000), [
            ('resize', ((800, 800), ), {}),
        ]),
        # Basic usage of max
        ('max-800x600', dict(width=1000, height=1000), [
            ('resize', ((600, 600), ), {}),
        ]),
    ]

TestMinMaxOperation.setup_test_methods()


class TestWidthHeightOperation(ImageOperationTestCase):
    operation_class = image_operations.WidthHeightOperation

    filter_spec_tests = [
        ('width-800', dict(method='width', size=800)),
        ('height-600', dict(method='height', size=600)),
    ]

    filter_spec_error_tests = [
        'width',
        'width-800x600',
        'width-abc',
        'width-800-c100',
    ]

    run_tests = [
        # Basic usage of width
        ('width-400', dict(width=1000, height=500), [
            ('resize', ((400, 200), ), {}),
        ]),
        # Basic usage of height
        ('height-400', dict(width=1000, height=500), [
            ('resize', ((800, 400), ), {}),
        ]),
    ]

TestWidthHeightOperation.setup_test_methods()


class TestCacheKey(TestCase):
    def test_cache_key(self):
        image = Image(width=1000, height=1000)
        fil = Filter(spec='max-100x100')
        cache_key = fil.get_cache_key(image)

        self.assertEqual(cache_key, '')

    def test_cache_key_fill_filter(self):
        image = Image(width=1000, height=1000)
        fil = Filter(spec='fill-100x100')
        cache_key = fil.get_cache_key(image)

        self.assertEqual(cache_key, '2e16d0ba')

    def test_cache_key_fill_filter_with_focal_point(self):
        image = Image(
            width=1000,
            height=1000,
            focal_point_width=100,
            focal_point_height=100,
            focal_point_x=500,
            focal_point_y=500,
        )
        fil = Filter(spec='fill-100x100')
        cache_key = fil.get_cache_key(image)

        self.assertEqual(cache_key, '0bbe3b2f')


class TestFilter(TestCase):

    operation_instance = Mock()

    def test_runs_operations(self):
        self.operation_instance.run = Mock()

        fil = Filter(spec='operation1|operation2')
        image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )
        fil.run(image, BytesIO())

        self.assertEqual(self.operation_instance.run.call_count, 2)


@hooks.register('register_image_operations')
def register_image_operations():
    return [
        ('operation1', Mock(return_value=TestFilter.operation_instance)),
        ('operation2', Mock(return_value=TestFilter.operation_instance))
    ]
