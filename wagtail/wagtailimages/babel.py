import os.path
from io import BytesIO

from wagtail.wagtailimages.rect import Rect


class ImageBabel(object):
    operations = []

    def __init__(self, initial_backend):
        self.backend = initial_backend

    def __getattr__(self, attr):
        operation = self.find_operation(attr, type(self.backend))

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
        if not initial_backend:
            # Work out best initial backend based on file extension
            pil_exts = ['.jpg', '.jpeg', '.png']
            wand_exts = ['.gif']

            if PILBackend is None:
                wand_exts += pil_exts

            if WandBackend is None:
                pil_exts += wand_exts

            ext = os.path.splitext(f.name)[1].lower()
            if PILBackend is not None and ext in pil_exts:
                initial_backend = PILBackend
            elif WandBackend is not None and ext in wand_exts:
                initial_backend = WandBackend

        if initial_backend:
            return cls(initial_backend.from_file(f))

    @classmethod
    def find_operation(cls, name, preferred_backend):
        # Try finding in the preferred backend
        for backend_class, operation_name, func in cls.operations:
            if operation_name == name and backend_class == preferred_backend:
                return backend_class, func

        # Try finding in any other backend
        for backend_class, operation_name, func in cls.operations:
            if operation_name == name:
                return backend_class, func

    @classmethod
    def operation(cls, backend_class, operation_name):
        def wrapper(func):
            cls.operations.append((backend_class, operation_name, func))

            return func

        return wrapper


# PIL

try:
    import PIL.Image


    class PILBackend(object):
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


    @ImageBabel.operation(PILBackend, 'get_size')
    def pil_get_size(backend):
        return backend.image.size


    @ImageBabel.operation(PILBackend, 'resize')
    def pil_resize(backend, width, height):
        if backend.image.mode in ['1', 'P']:
            backend.image = backend.image.convert('RGB')

        backend.image = backend.image.resize((width, height), PIL.Image.ANTIALIAS)


    @ImageBabel.operation(PILBackend, 'crop')
    def pil_crop(backend, left, top, right, bottom):
        backend.image = backend.image.crop((left, top, right, bottom))


    @ImageBabel.operation(PILBackend, 'save_as_jpeg')
    def pil_save_as_jpeg(backend, f, quality=85):
        backend.image.save(f, 'JPEG', quality=quality)


    @ImageBabel.operation(PILBackend, 'save_as_png')
    def pil_save_as_png(backend, f):
        backend.image.save(f, 'PNG')

except ImportError:
    PILBackend = None


# Wand

try:
    from wand.image import Image
    from wand.api import library


    class WandBackend(object):
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


    @ImageBabel.operation(WandBackend, 'get_size')
    def wand_get_size(backend):
        return backend.image.size


    @ImageBabel.operation(WandBackend, 'resize')
    def wand_resize(backend, width, height):
        backend.image.resize(width, height)


    @ImageBabel.operation(WandBackend, 'crop')
    def wand_crop(backend, left, top, right, bottom):
        backend.image.crop(left=left, top=top, right=right, bottom=bottom)

except ImportError:
    WandBackend = None


# OpenCV

try:
    try:
        import cv
    except ImportError:
        import cv2.cv as cv


    class OpenCVBackend(object):
        def __init__(self, image_mode, image_size, image_data):
            self.image_mode = image_mode
            self.image_size = image_size
            self.image_data = image_data

        def to_buffer(self):
            return self.image_mode, self.image_size, self.image_data

        @classmethod
        def from_buffer(cls, buf):
            mode, size, data = buf
            return cls(mode, size, data)

        def opencv_grey_image(self):
            image = cv.CreateImageHeader(self.image_size, cv.IPL_DEPTH_8U, 3)
            cv.SetData(image, self.image_data)

            grey_image = cv.CreateImage(self.image_size, 8, 1)
            convert_mode = getattr(cv, 'CV_%s2GRAY' % self.image_mode)
            cv.CvtColor(image, grey_image, convert_mode)

            return grey_image


    @ImageBabel.operation(OpenCVBackend, 'detect_features')
    def opencv_detect_features(backend):
        image = backend.opencv_grey_image()
        rows = backend.image_size[0]
        cols = backend.image_size[1]

        eig_image = cv.CreateMat(rows, cols, cv.CV_32FC1)
        temp_image = cv.CreateMat(rows, cols, cv.CV_32FC1)
        points = cv.GoodFeaturesToTrack(image, eig_image, temp_image, 20, 0.04, 1.0, useHarris=False)

        return points


    @ImageBabel.operation(OpenCVBackend, 'detect_faces')
    def detect_faces(backend):
        cascade_filename = os.path.join(os.path.dirname(__file__), 'face_detection', 'haarcascade_frontalface_alt2.xml')
        cascade = cv.Load(cascade_filename)
        image = backend.opencv_grey_image()

        cv.EqualizeHist(image, image)

        min_size = (40, 40)
        haar_scale = 1.1
        min_neighbors = 3
        haar_flags = 0

        faces = cv.HaarDetectObjects(
            image, cascade, cv.CreateMemStorage(0),
            haar_scale, min_neighbors, haar_flags, min_size
        )

        return [Rect(face[0][0], face[0][1], face[0][0] + face[0][2], face[0][1] + face[0][3]) for face in faces]

except ImportError:
    OpenCVBackend = None
