#!/usr/bin/env python3

import base64
import json
import os

import cv2
import requests
from utility import general_utils as g_utils

#
# Common module for calling Mathpix OCR service from Python.
#
# N.B.: Set your credentials in environment variables APP_ID and APP_KEY,
# either once via setenv or on the command line as in
# APP_ID=my-id APP_KEY=my-key python3 simple.py 
#

env = os.environ

default_headers = {
    'app_id': env.get('APP_ID', 'frewheelin_ocr_mathflat_com_d1de2d'),
    'app_key': env.get('APP_KEY', '381155226dea39da90e8'),
    'Content-type': 'application/json'
}

service = 'https://api.mathpix.com/v3/latex'


# Return the base64 encoding of an image with the given filename.
def image_uri(filename, numpy=False):
    if numpy:
        image = filename.copy()
        if not os.path.exists('tmp'):
            os.mkdir('tmp')
        filename = 'tmp/crop_tmp.jpg'
        tmp = cv2.imwrite('tmp/crop_tmp.jpg', image)
    image_data = open(filename, "rb").read()
    return "data:image/jpg;base64," + base64.b64encode(image_data).decode()


# Call the Mathpix service with the given arguments, headers, and timeout.
def latex(args, headers=default_headers, timeout=30):
    r = requests.post(service,
                      data=json.dumps(args), headers=headers, timeout=timeout)
    return json.loads(r.text)


def recognize_textline_by_mathpix(image):
    # Text recognition routine
    # Convert all math expressions to text
    global text_result
    res = latex({
        'src': image_uri(image, numpy=True),
        'ocr': ['math'],
        'formats': ["text",
                    "latex_simplified",
                    "latex_styled",
                    "mathml",
                    "asciimath",
                    "latex_list"]
    })

    # Add result to list
    try:
        pos = res['position']
        tl_x, tl_y, width, height = pos['top_left_x'], pos['top_left_y'], pos['width'], pos['height']
        tr_x, tr_y = (tl_x + width), (tl_y + height)

        box = [[tl_x, tl_y], [tr_x, tr_y], [tr_x, tr_y + height], [tl_x, tl_y + height]]
        text = res['text']  # text / latex_simplified / latex_styled / asciimath
        conf = res['latex_confidence']
        # conf = res['latex_confidence']

    except:
        box = [[-1, -1], [-1, -1], [-1, -1], [-1, -1]]
        text = ''
        conf = -1
        pass

    return box, text, conf


def main():
    IMG_PATH = "../Input/test/crop_problem.png"
    # img = Image.open(IMG_PATH)
    img = g_utils.imread(IMG_PATH, 'RGB')
    img_cv_grey = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    text_result = recognize_textline_by_mathpix(img_cv_grey)
    text_result = text_result
    print(text_result)
    pass


if __name__ == "__main__":
    main()
