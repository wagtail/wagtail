import os.path
from io import BytesIO


class ImageBabel(object):
    operations = []

    def __init__(self, initial_state):
        self.state = initial_state

    def __getattr__(self, attr):
        operation = self.find_operation(attr, type(self.state))

        if operation is not None:
            state, func = operation

            def operation(*args, **kwargs):
                if state is not type(self.state):
                    self.switch_state(state)

                return func(self.state, *args, **kwargs)

            return operation
        else:
            raise AttributeError("%r object has no attribute %r" % (
                self.__class__.__name__, attr
            ))

    def switch_state(self, new_state):
        if type(self.state) is new_state:
            return

        if hasattr(new_state, 'from_buffer') and hasattr(self.state, 'to_buffer'):
            buf = self.state.to_buffer()
            self.state = new_state.from_buffer(buf)
            return

        if hasattr(new_state, 'from_file') and hasattr(self.state, 'to_file'):
            f = BytesIO()
            self.state.to_file(f)
            self.state = new_state.from_file(f)
            return

    @classmethod
    def from_file(cls, f, initial_state=None):
        if not initial_state:
            # Work out best initial state based on file extension
            pil_exts = ['.jpg', '.jpeg', '.png']
            wand_exts = ['.gif']

            if PILState is None:
                wand_exts += pil_exts

            if WandState is None:
                pil_exts += wand_exts

            ext = os.path.splitext(f.name)[1].lower()
            if PILState is not None and ext in pil_exts:
                initial_state = PILState
            elif WandState is not None and ext in wand_exts:
                initial_state = WandState

        if initial_state:
            return cls(initial_state.from_file(f))

    @classmethod
    def find_operation(cls, name, preferred_state):
        # Try finding in the preferred state
        for state_class, operation_name, func in cls.operations:
            if operation_name == name and state_class == preferred_state:
                return state_class, func

        # Try finding in any other state
        for state_class, operation_name, func in cls.operations:
            if operation_name == name:
                return state_class, func

    @classmethod
    def operation(cls, state_class, operation_name):
        def wrapper(func):
            cls.operations.append((state_class, operation_name, func))

            return func

        return wrapper


# PIL

try:
    import PIL.Image


    class PILState(object):
        def __init__(self, image):
            self.image = image

        def to_buffer(self):
            image = self.image

            if image.mode not in ['RGB', 'RGBA']:
                if 'A' in image.mode:
                    image = image.convert('RGBA')
                else:
                    image = image.convert('RGB')

            return image.mode, image.size, image.tobytes()

        @classmethod
        def from_buffer(cls, buf):
            mode, size, data = buf
            return cls(PIL.Image.frombytes(mode, size, data))

        def to_file(self, f):
            return self.image.save(f, 'PNG')

        @classmethod
        def from_file(cls, f):
            f.seek(0)
            return cls(PIL.Image.open(f))


    @ImageBabel.operation(PILState, 'get_size')
    def pil_get_size(state):
        return state.image.size


    @ImageBabel.operation(PILState, 'resize')
    def pil_resize(state, width, height):
        if state.image.mode in ['1', 'P']:
            state.image = state.image.convert('RGB')

        state.image = state.image.resize((width, height), PIL.Image.ANTIALIAS)


    @ImageBabel.operation(PILState, 'crop')
    def pil_crop(state, left, top, right, bottom):
        state.image = state.image.crop((left, top, right, bottom))


    @ImageBabel.operation(PILState, 'save_as_jpeg')
    def pil_save_as_jpeg(state, f, quality=85):
        state.image.save(f, 'JPEG', quality=quality)


    @ImageBabel.operation(PILState, 'save_as_png')
    def pil_save_as_png(state, f):
        state.image.save(f, 'PNG')

except ImportError:
    PILState = None


# Wand

try:
    from wand.image import Image
    from wand.api import library


    class WandState(object):
        def __init__(self, image):
            self.image = image

        def to_buffer(self):
            return 'RGB', self.image.size, self.image.make_blob('RGB')

# DOESNT WORK. SEE: https://github.com/dahlia/wand/issues/123
#        @classmethod
#        def from_buffer(cls, buf):
#            mode, size, data = buf
#            return cls(Image(blob=data, format=mode, width=size[0], height=size[1]))

        @classmethod
        def from_file(cls, f):
            f.seek(0)

            image = Image(file=f)
            image.wand = library.MagickCoalesceImages(image.wand)
            return cls(image)


    @ImageBabel.operation(WandState, 'get_size')
    def wand_get_size(state):
        return state.image.size


    @ImageBabel.operation(WandState, 'resize')
    def wand_resize(state, width, height):
        state.image.resize(width, height)


    @ImageBabel.operation(WandState, 'crop')
    def wand_crop(state, left, top, right, bottom):
        state.image.crop(left=left, top=top, right=right, bottom=bottom)

except ImportError:
    WandState = None


# OpenCV

try:
    try:
        import cv
    except ImportError:
        import cv2.cv as cv


    class OpenCVState(object):
        def __init__(self, image):
            self.image = image

        @classmethod
        def from_buffer(cls, buf):
            pass


    @ImageBabel.operation(OpenCVState, 'detect_faces')
    def opencv_detect_faces(state):
        pass


    @ImageBabel.operation(OpenCVState, 'detect_features')
    def opencv_detect_features(state):
        pass

except ImportError:
    OpenCVState = None
