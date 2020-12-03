#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
from collections import OrderedDict

import cv2
import numpy as np
from PIL import ImageFont, ImageDraw, Image
from system.system_ocr import SaveImageMode
from utility import general_utils as utils

FONT_PATH = "../easyocr/fonts/SourceHanSerifK-Regular.otf"


# borrowed from https://github.com/lengstrom/fast-style-transfer/blob/master/src/utils.py
def get_files(img_dir):
    imgs, masks, xmls = list_files(img_dir)
    return imgs, masks, xmls


def list_files(in_path):
    img_files = []
    mask_files = []
    gt_files = []
    for (dirpath, dirnames, filenames) in os.walk(in_path):
        for file in filenames:
            filename, ext = os.path.splitext(file)
            ext = str.lower(ext)
            if ext == '.jpg' or ext == '.jpeg' or ext == '.gif' or ext == '.png' or ext == '.pgm':
                img_files.append(os.path.join(dirpath, file))
            elif ext == '.bmp':
                mask_files.append(os.path.join(dirpath, file))
            elif ext == '.xml' or ext == '.gt' or ext == '.txt':
                gt_files.append(os.path.join(dirpath, file))
            elif ext == '.zip':
                continue
    # img_files.sort()
    # mask_files.sort()
    # gt_files.sort()
    return img_files, mask_files, gt_files


def saveResult(img_file, img, boxes, dirname='./Output/', verticals=None, texts=None, scores=None,
               mode=SaveImageMode.origin.name):
    """ save text detection result one by one
        Args:
            img_file (str): image file name
            img (array): raw image context
            boxes (array): array of result file
                Shape: [num_detections, 4] for BB output / [num_detections, 4] for QUAD output
        Return:
            None
        """

    # make result file list
    filename, file_ext = os.path.splitext(os.path.basename(img_file))

    # Result file path
    rst_txt_fpath = os.path.join(dirname, filename + '.txt')
    rst_img_fpath = os.path.join(dirname, filename + '.jpg')

    if not os.path.isdir(dirname):
        os.makedirs(dirname, exist_ok=True)

    # Fill bg. by white value
    if mode is SaveImageMode.white.name:
        h, w, c = img.shape
        img = np.zeros([h, w, c], dtype=np.uint8)
        img.fill(255)  # or img[:] = 255
        text_color = get_color_array('blue')
    else:
        box_color = get_color_array('blue')
        text_color = get_color_array('red')

    with open(rst_txt_fpath, 'w') as f:
        for i, box in enumerate(boxes):
            poly = np.array(box).astype(np.int32).reshape((-1))
            strResult = ','.join([str(p) for p in poly]) + '\r\n'
            f.write(strResult)

            poly = poly.reshape(-1, 2)

            if mode is not SaveImageMode.white.name:
                cv2.polylines(img, [poly.reshape((-1, 1, 2))], True, color=box_color, thickness=2)

            ptColor = (0, 255, 255)
            if verticals is not None:
                if verticals[i]:
                    ptColor = (255, 0, 0)

            if texts is not None:
                # Pillow ver.
                font = ImageFont.truetype(FONT_PATH, 10)
                margin = 10
                pil_img = Image.fromarray(img)
                draw = ImageDraw.Draw(pil_img)
                if scores is not None:
                    draw.text(xy=(poly[0][0] + 1, poly[0][1] + 1 - margin),
                              text='[{}] : '.format(i + 1) + texts[i] + ' : ' + '{:4.2f}'.format(scores[i]),
                              font=font, fill=text_color)
                else:
                    draw.text(xy=(poly[0][0] + 1, poly[0][1] + 1 - margin),
                              text=texts[i], font=font, fill=text_color)
            else:
                continue

            img = np.array(pil_img)

    # Save result image
    utils.imwrite(img, rst_img_fpath)
    print(rst_img_fpath, "저장 완료!")
    return True


def get_color_array(color):
    colors = OrderedDict({
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "black": (0, 0, 0),
        "white": (255, 255, 255),
    })
    return colors[color]
