import six


class ImageBackendBase(type):
    def __init__(cls, name, bases, dct):
        super(ImageBackendBase, cls).__init__(name, bases, dct)

        # Make sure all backends have their own operations attribute
        cls.operations = {}


class ImageBackend(six.with_metaclass(ImageBackendBase)):
    @classmethod
    def register_operation(cls, operation_name):
        def wrapper(func):
            cls.operations[operation_name] = func

            return func

        return wrapper

    @classmethod
    def check(cls):
        pass
