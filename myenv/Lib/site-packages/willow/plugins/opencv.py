import os

from willow.image import Image, RGBImageBuffer


def _cv2():
    try:
        import cv2
    except ImportError:
        from cv import cv2
    return cv2


def _numpy():
    import numpy

    return numpy


class BaseOpenCVImage(Image):
    def __init__(self, image, size):
        self.image = image
        self.size = size

    @classmethod
    def check(cls):
        _cv2()

    @Image.operation
    def get_size(self):
        return self.size

    @Image.operation
    def get_frame_count(self):
        # Animation is not supported by OpenCV
        return 1

    @Image.operation
    def has_alpha(self):
        # Alpha is not supported by OpenCV
        return False

    @Image.operation
    def has_animation(self):
        # Animation is not supported by OpenCV
        return False


class OpenCVColorImage(BaseOpenCVImage):
    @classmethod
    def check(cls):
        super().check()
        _numpy()

    @classmethod
    @Image.converter_from(RGBImageBuffer)
    def from_buffer_rgb(cls, image_buffer):
        """
        Converts a Color Image buffer into a numpy array suitable for use with OpenCV
        """
        numpy = _numpy()
        cv2 = _cv2()

        image = numpy.frombuffer(image_buffer.data, dtype=numpy.uint8)
        image = image.reshape(image_buffer.size[1], image_buffer.size[0], 3)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        return cls(image, image_buffer.size)


class OpenCVGrayscaleImage(BaseOpenCVImage):
    face_haar_flags = 0
    face_min_neighbors = 3
    face_haar_scale = 1.1
    face_min_size = (40, 40)

    @Image.operation
    def detect_features(self):
        """
        Find interesting features of an image suitable for cropping to.
        """
        numpy = _numpy()
        cv2 = _cv2()
        points = cv2.goodFeaturesToTrack(self.image, 20, 0.04, 1.0)
        if points is None:
            return []
        else:
            points = numpy.reshape(
                points, (-1, 2)
            )  # Numpy returns it with an extra third dimension
            return points.tolist()

    @Image.operation
    def detect_faces(self, cascade_filename="haarcascade_frontalface_alt2.xml"):
        """
        Run OpenCV face detection on the image. Returns a list of coordinates representing a box around each face.
        """
        cv2 = _cv2()
        cascade_filename = self._find_cascade(cascade_filename)
        cascade = cv2.CascadeClassifier(cascade_filename)
        equalised_image = cv2.equalizeHist(self.image)
        faces = cascade.detectMultiScale(
            equalised_image,
            self.face_haar_scale,
            self.face_min_neighbors,
            self.face_haar_flags,
            self.face_min_size,
        )
        return [
            (
                face[0],
                face[1],
                face[0] + face[2],
                face[1] + face[3],
            )
            for face in faces
        ]

    def _find_cascade(self, cascade_filename):
        """
        Find the requested OpenCV cascade file.  If a relative path was provided, check local cascades directory.
        """
        if not os.path.isabs(cascade_filename):
            cascade_filename = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data/cascades",
                cascade_filename,
            )
        return cascade_filename

    @classmethod
    @Image.converter_from(OpenCVColorImage)
    def from_color(cls, colour_image):
        """
        Convert OpenCVColorImage to an OpenCVGrayscaleImage.
        """
        cv2 = _cv2()
        image = cv2.cvtColor(colour_image.image, cv2.COLOR_BGR2GRAY)
        return cls(image, colour_image.size)


willow_image_classes = [OpenCVColorImage, OpenCVGrayscaleImage]
