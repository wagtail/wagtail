import os.path
from io import BytesIO

from wagtail.wagtailimages.rect import Rect


class ImageBabel(object):
    operations = []

    def __init__(self, initial_backend):
        self.backend = initial_backend

    def __getattr__(self, attr):
        operation = self.find_operation(attr, preferred_backend=type(self.backend))

        if operation is not None:
            backend, func = operation

            def operation(*args, **kwargs):
                if backend is not type(self.backend):
                    self.switch_backend(backend)

                return func(self.backend, *args, **kwargs)

            return operation
        else:
            raise AttributeError("%r object has no attribute %r" % (
                self.__class__.__name__, attr
            ))

    def switch_backend(self, new_backend):
        if type(self.backend) is new_backend:
            return

        if hasattr(new_backend, 'from_buffer') and hasattr(self.backend, 'to_buffer'):
            buf = self.backend.to_buffer()
            self.backend = new_backend.from_buffer(buf)
            return

        if hasattr(new_backend, 'from_file') and hasattr(self.backend, 'to_file'):
            f = BytesIO()
            self.backend.to_file(f)
            self.backend = new_backend.from_file(f)
            return

    @classmethod
    def from_file(cls, f, initial_backend=None):
        # TODO: Make this extensible
        from wagtail.wagtailimages.backends.pillow import PillowBackend
        from wagtail.wagtailimages.backends.wand import WandBackend
        if not initial_backend:
            # Work out best initial backend based on file extension
            pil_exts = ['.jpg', '.jpeg', '.png']
            wand_exts = ['.gif']

            if PillowBackend is None:
                wand_exts += pil_exts

            if WandBackend is None:
                pil_exts += wand_exts

            ext = os.path.splitext(f.name)[1].lower()
            if PillowBackend is not None and ext in pil_exts:
                initial_backend = PillowBackend
            elif WandBackend is not None and ext in wand_exts:
                initial_backend = WandBackend

        if initial_backend:
            return cls(initial_backend.from_file(f))

    backends = []

    @classmethod
    def register_backend(cls, backend):
        if backend not in cls.backends:
            cls.backends.append(backend)

    @classmethod
    def check_backends(cls, backends):
        available_backends = []
        unavailable_backends = []

        for backend in backends:
            try:
                backend.check()
            except Exception as e:
                error = "%s: %s" % (type(e).__name__, str(e))
                unavailable_backends.append((backend, error))
            else:
                available_backends.append(backend)

        return available_backends, unavailable_backends

    @classmethod
    def find_operation(cls, operation_name, preferred_backend=None):
        # Try finding the operation in the preferred backend
        if preferred_backend is not None:
            if operation_name in preferred_backend.operations.keys():
                return preferred_backend, preferred_backend.operations[operation_name]

        # Operation doesn't exist in preferred backend, find all backends that implement it
        backends = [backend for backend in cls.backends if operation_name in backend.operations]
        if backends:
            # Now filter that list to only include backends that are available
            available_backends, unavailable_backends = cls.check_backends(backends)

            if available_backends:
                # TODO: Think of a way to select the best backend if multiple backends are found
                # Select the first available backend
                return available_backends[0], available_backends[0].operations[operation_name]

            elif unavailable_backends:
                # Some backends were found but none of them are available, raise an error
                message = '\n'.join([
                    "The operation '%s' is available in the following backends but they all returned an error:" % operation_name
                ] + [
                    "%s -- %s" % (backend.__name__, error)
                    for backend, error in unavailable_backends
                ])
                raise RuntimeError(message)


# Register builtin image backends
from wagtail.wagtailimages.backends.pillow import PillowBackend
from wagtail.wagtailimages.backends.wand import WandBackend
from wagtail.wagtailimages.backends.opencv import OpenCVBackend

ImageBabel.register_backend(PillowBackend)
ImageBabel.register_backend(WandBackend)
ImageBabel.register_backend(OpenCVBackend)
