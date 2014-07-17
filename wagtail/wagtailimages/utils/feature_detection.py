try:
    import cv

    opencv_available = True
except ImportError:
    try:
        import cv2.cv as cv

        opencv_available = True
    except ImportError:
        opencv_available = False


from wagtail.wagtailimages.utils.focal_point import FocalPoint


def detect_features(image_size, image_mode, image_data):
    if opencv_available:
        image = cv.CreateImageHeader(image_size, cv.IPL_DEPTH_8U, 3)
        cv.SetData(image, image_data)

        gray_image = cv.CreateImage(image_size, 8, 1)
        convert_mode = getattr(cv, 'CV_%s2GRAY' % image_mode)
        cv.CvtColor(image, gray_image, convert_mode)
        image = gray_image
        rows = image_size[0]
        cols = image_size[1]

        eig_image = cv.CreateMat(rows, cols, cv.CV_32FC1)
        temp_image = cv.CreateMat(rows, cols, cv.CV_32FC1)
        points = cv.GoodFeaturesToTrack(image, eig_image, temp_image, 20, 0.04, 1.0, useHarris=False)

        if points:
            return [FocalPoint(x, y, 1) for x, y in points]

    return []
