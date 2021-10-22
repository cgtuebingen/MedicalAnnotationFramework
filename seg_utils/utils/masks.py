from typing import List, Tuple
import cv2
import numpy as np
import os.path as osp
from PIL import Image


import matplotlib.pyplot as plt


def create_binary_maks(base_path: str, label_list: List[Tuple[str, List[dict]]]) -> List[List[np.ndarray]]:
    r"""This function creates a binary mask array for each label present in the label_list.
    If the same label category is present, individual masks are created with instance segmentation in mind
    rather than semantic segmentation.

    Intended to be called with database.get_labels()
    """
    binary_mask = []
    # multiple images in the label_list
    for _image_idx, _image in enumerate(label_list):
        bm = []
        image_size = get_image_size(base_path, _image[0])
        # per image, there might be several labels/shapes
        for _label in _image[1]:
            _bm = []
            _mask = np.zeros(image_size, dtype=np.int32)
            if 'points' in _label:
                # now distinction between the individual shapes
                points = np.asarray(_label['points'], dtype=np.int32)
                if _label['shape_type'] == 'polygon':
                    cv2.fillPoly(_mask, [points], 1)
                elif _label['shape_type'] == 'circle':
                    # The ellipse is stored as the bounding rectangle with upper left and lower right corner
                    center = np.int32(points[0] + 0.5 * (points[1] - points[0]))
                    size = np.asarray([points[1][0] - points[0][0], points[1][1] - points[0][1]], dtype=np.int32)
                    _mask = cv2.ellipse(_mask, center, size, 0, 0, 360, 1, -1)
                elif _label['shape_type'] == 'rectangle':
                    # Rectangles are right now stored as the 4 edge points
                    # I only need the upper left and lower right
                    _mask = cv2.rectangle(_mask, points[0], points[2], 1, -1)
                _bm = _mask
            bm.append(_bm)
        binary_mask.append(bm)
    return binary_mask


def get_image_size(base_path: str, image_path: str) -> List[int]:
    r"""Get the image size of an image specified by the image_path and the base path
    (the parent directory of the database)"""

    path = osp.join(base_path, image_path)
    image = Image.open(path)
    return [image.width, image.height]

