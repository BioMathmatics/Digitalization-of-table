import cv2
import numpy as np


def align_image(img: np.array) -> np.array:
    """
    This method align image find corner table and performs affine transform
    """
    gray = cv2.cvtColor(img.copy(), cv2.COLOR_BGR2GRAY)
    binary_img = cv2.adaptiveThreshold(gray, 255,
                                       cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, 11, 2)

    contours, _ = cv2.findContours(binary_img,
                                   method=cv2.CHAIN_APPROX_SIMPLE,
                                   mode=cv2.RETR_EXTERNAL)
    # find contour of the table
    max_size = -1
    max_bbox = None
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 30 and h > 20:
            if w * h > max_size:
                max_bbox = cnt
                max_size = w * h

    rect = cv2.minAreaRect(max_bbox)
    box = cv2.boxPoints(rect)

    # getting coordinates corners of the table
    pts1 = np.float32(box)
    pts1 = sorted(pts1.tolist(), key=lambda x: x[0])

    '''
    after sorted pts1 contein coordinates corners table,
    first two -- coordinates two left corners
    second two -- coordinates two right corners
    '''

    left_top = min(pts1[0:2], key=lambda x: x[1])
    left_bottom = max(pts1[0:2], key=lambda x: x[1])
    right_top = min(pts1[2:4], key=lambda x: x[1])
    right_bottom = max(pts1[2:4], key=lambda x: x[1])

    pts1 = np.array([left_top, right_top,
                     left_bottom, right_bottom], np.float32)

    _, _, height, width = cv2.boundingRect(max_bbox)

    pts2 = np.float32([[0, 0], [height, 0],
                       [0, width], [height, width]])

    # align image
    M = cv2.getPerspectiveTransform(pts1, pts2)
    dst = cv2.warpPerspective(img, M, (height, width))

    cv2.rectangle(dst, (2, 2), (height - 2, width - 2), color=(0, 0, 0), thickness=2)

    return dst
