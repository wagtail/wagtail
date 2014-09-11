import os
from django.conf import settings

# only try to import OpenCV if WAGTAILIMAGES_FEATURE_DETECTION_ENABLED is True -
# avoids spurious "libdc1394 error: Failed to initialize libdc1394" errors on sites that
# don't even use OpenCV
if getattr(settings, 'WAGTAILIMAGES_FEATURE_DETECTION_ENABLED', False):
    try:
        import cv

        opencv_available = True
    except ImportError:
        try:
            import cv2.cv as cv

            opencv_available = True
        except ImportError:
            opencv_available = False
else:
    opencv_available = False


from wagtail.wagtailimages.utils.focal_point import FocalPoint, combine_focal_points


class FeatureDetector(object):
    def __init__(self, image_size, image_mode, image_data):
        self.image_size = image_size
        self.image_mode = image_mode
        self.image_data = image_data

    def opencv_grey_image(self):
        image = cv.CreateImageHeader(self.image_size, cv.IPL_DEPTH_8U, 3)
        cv.SetData(image, self.image_data)

        gray_image = cv.CreateImage(self.image_size, 8, 1)
        convert_mode = getattr(cv, 'CV_%s2GRAY' % self.image_mode)
        cv.CvtColor(image, gray_image, convert_mode)

        return gray_image

    def detect_features(self):
        if opencv_available:
            image = self.opencv_grey_image()
            rows = self.image_size[0]
            cols = self.image_size[1]

            eig_image = cv.CreateMat(rows, cols, cv.CV_32FC1)
            temp_image = cv.CreateMat(rows, cols, cv.CV_32FC1)
            points = cv.GoodFeaturesToTrack(image, eig_image, temp_image, 20, 0.04, 1.0, useHarris=False)

            if points:
                return [FocalPoint(x, y, 1) for x, y in points]

        return []

    def detect_faces(self):
        if opencv_available:
            cascade_filename = os.path.join(os.path.dirname(__file__), 'face_detection', 'haarcascade_frontalface_alt2.xml')
            cascade = cv.Load(cascade_filename)
            image = self.opencv_grey_image()

            cv.EqualizeHist(image, image)

            min_size = (40, 40)
            haar_scale = 1.1
            min_neighbors = 3
            haar_flags = 0

            faces = cv.HaarDetectObjects(
                image, cascade, cv.CreateMemStorage(0),
                haar_scale, min_neighbors, haar_flags, min_size
            )

            if faces:
                return [FocalPoint.from_square(face[0][0], face[0][1], face[0][2], face[0][3]) for face in faces]

        return []

    def get_focal_point(self):
        # Face detection
        faces = self.detect_faces()

        if faces:
            return combine_focal_points(faces)

        # Feature detection
        features = self.detect_features()

        if features:
            return combine_focal_points(features)
