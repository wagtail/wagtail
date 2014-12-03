import unittest
from wagtail.wagtailimages import image_operations


class ImageOperationTestCase(unittest.TestCase):
    operation_class = None
    filter_spec_tests = []
    filter_spec_error_tests = []

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
    def make_filter_spec_error_test(cls, filter_spec, expected_exception):
        def test_filter_spec_error(self):
            self.assertRaises(expected_exception, self.operation_class, *filter_spec.split('-'))

        test_name = 'test_filter_%s_raises_%s' % (filter_spec, expected_exception.__name__)
        test_filter_spec_error.__name__ = test_name
        return test_filter_spec_error
 
    @classmethod
    def setup_test_methods(cls):
        if cls.operation_class is None:
            return

        # Filter spec tests
        for filter_spec, expected_output in cls.filter_spec_tests:
            filter_spec_test = cls.make_filter_spec_test(filter_spec, expected_output)
            setattr(cls, filter_spec_test.__name__, filter_spec_test)

        # Filter spec error tests
        for filter_spec, expected_exception in cls.filter_spec_error_tests:
            filter_spec_error_test = cls.make_filter_spec_error_test(filter_spec, expected_exception)
            setattr(cls, filter_spec_error_test.__name__, filter_spec_error_test)


class TestDoNothingOperation(ImageOperationTestCase):
    operation_class = image_operations.DoNothingOperation

    filter_spec_tests = [
        ('original', dict()),
        ('blahblahblah', dict()),
        ('123456', dict()),
    ]

    filter_spec_error_tests = [
        ('cannot-take-multiple-parameters', TypeError),
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
        ('fill', TypeError),
        ('fill-800', ValueError),
        ('fill-abc', ValueError),
        ('fill-800xabc', ValueError),
        ('fill-800x600-', ValueError),
        ('fill-800x600x10', ValueError),
        ('fill-800x600-d100', ValueError),
    ]

TestFillOperation.setup_test_methods()


class TestMinMaxOperation(ImageOperationTestCase):
    operation_class = image_operations.MinMaxOperation

    filter_spec_tests = [
        ('min-800x600', dict(method='min', width=800, height=600)),
        ('max-800x600', dict(method='max', width=800, height=600)),
    ]

    filter_spec_error_tests = [
        ('min', TypeError),
        #('hello-800x600', ValueError),
        ('min-800', ValueError),
        ('min-abc', ValueError),
        ('min-800xabc', ValueError),
        ('min-800x600-', TypeError),
        ('min-800x600-c100', TypeError),
        ('min-800x600x10', ValueError),
    ]

TestMinMaxOperation.setup_test_methods()


class TestWidthHeightOperation(ImageOperationTestCase):
    operation_class = image_operations.WidthHeightOperation

    filter_spec_tests = [
        ('width-800', dict(method='width', size=800)),
        ('height-600', dict(method='height', size=600)),
    ]

    filter_spec_error_tests = [
        ('width', TypeError),
        #('hello-800', ValueError),
        ('width-800x600', ValueError),
        ('width-abc', ValueError),
        ('width-800-c100', TypeError),
    ]

TestWidthHeightOperation.setup_test_methods()
