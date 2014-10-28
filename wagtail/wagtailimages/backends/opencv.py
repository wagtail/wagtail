import os

from wagtail.wagtailimages.rect import Rect
from .base import ImageBackend


class OpenCVBackend(ImageBackend):
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
        cv = self.get_opencv()

        image = cv.CreateImageHeader(self.image_size, cv.IPL_DEPTH_8U, 3)
        cv.SetData(image, self.image_data)

        grey_image = cv.CreateImage(self.image_size, 8, 1)
        convert_mode = getattr(cv, 'CV_%s2GRAY' % self.image_mode)
        cv.CvtColor(image, grey_image, convert_mode)

        return grey_image

    @classmethod
    def get_opencv(cls):
        try:
            import cv
        except ImportError:
            import cv2.cv as cv

        return cv

    @classmethod
    def check(cls):
        cls.get_opencv()


@OpenCVBackend.register_operation('detect_features')
def opencv_detect_features(backend):
    cv = backend.get_opencv()

    image = backend.opencv_grey_image()
    rows = backend.image_size[0]
    cols = backend.image_size[1]

    eig_image = cv.CreateMat(rows, cols, cv.CV_32FC1)
    temp_image = cv.CreateMat(rows, cols, cv.CV_32FC1)
    points = cv.GoodFeaturesToTrack(
        image, eig_image, temp_image, 20, 0.04, 1.0, useHarris=False)

    return points


@OpenCVBackend.register_operation('detect_faces')
def detect_faces(backend):
    cv = backend.get_opencv()

    cascade_filename = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'face_detection',
        'haarcascade_frontalface_alt2.xml',
    )
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

    return [
        Rect(
            face[0][0],
            face[0][1],
            face[0][0] + face[0][2],
            face[0][1] + face[0][3],
        ) for face in faces
    ]
