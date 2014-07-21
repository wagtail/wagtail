import os

try:
    import cv

    opencv_available = True
except ImportError:
    try:
        import cv2.cv as cv

        opencv_available = True
    except ImportError:
        opencv_available = False


from wagtail.wagtailimages.utils.focal_point import FocalPoint, combine_points


def get_cv_gray_image(image_size, image_mode, image_data):
    image = cv.CreateImageHeader(image_size, cv.IPL_DEPTH_8U, 3)
    cv.SetData(image, image_data)

    gray_image = cv.CreateImage(image_size, 8, 1)
    convert_mode = getattr(cv, 'CV_%s2GRAY' % image_mode)
    cv.CvtColor(image, gray_image, convert_mode)

    return gray_image


def detect_features(image_size, image_mode, image_data):
    if opencv_available:
        image = get_cv_gray_image(image_size, image_mode, image_data)
        rows = image_size[0]
        cols = image_size[1]

        eig_image = cv.CreateMat(rows, cols, cv.CV_32FC1)
        temp_image = cv.CreateMat(rows, cols, cv.CV_32FC1)
        points = cv.GoodFeaturesToTrack(image, eig_image, temp_image, 20, 0.04, 1.0, useHarris=False)

        if points:
            return [FocalPoint(x, y, 1) for x, y in points]

    return []


def detect_faces(image_size, image_mode, image_data):
    if opencv_available:
        cascade_filename = os.path.join(os.path.dirname(__file__), 'face_detection', 'haarcascade_frontalface_alt2.xml')
        cascade = cv.Load(cascade_filename)
        image = get_cv_gray_image(image_size, image_mode, image_data)

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


def get_focal_point(image_size, image_mode, image_data):
    # Face detection
    faces = feature_detection.detect_faces(image_size, image_mode, image_data)

    if faces:
        return combine_points(faces)

    # Feature detection
    features = feature_detection.detect_features(image_size, image_mode, image_data)

    if features:
        return focal_point.combine_points(features)
