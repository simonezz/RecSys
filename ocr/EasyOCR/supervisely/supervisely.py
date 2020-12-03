import os
import sys
import numpy as np
import obj_template
import supervisely_lib as sly  # Supervisely Python SDK
import json                    # Add Python JSON module for pretty-printing.
import argparse
import pprint
import cv2
from copy import deepcopy
from matplotlib import pyplot as plt
from easyocr import coordinates as coord
from utils import general_utils as utils
from utils import imgproc_utils as img_utils
from easyocr import craft_file_utils as file_utils
from system import system_ocr



_this_folder_ = os.path.dirname(os.path.abspath(__file__))
_this_basename_ = os.path.splitext(os.path.basename(__file__))[0]


def display_images(images, figsize=None):
    plt.figure(figsize=(figsize if (figsize is not None) else (15, 15)))
    for i, img in enumerate(images, start=1):
        plt.subplot(1, len(images), i)
        plt.imshow(img)

def extract_ocr_results_from_dict(dict):
    bboxes = []
    texts = []
    objects = dict['objects']
    print('Loaded annotation has {} objects.'.format(len(objects)))
    # pprint.pprint(objects)
    for obj in objects:
        class_name = obj['classTitle']
        if class_name == 'korean':
            continue
        [x1, y1], [x2, y2] = obj['points']['exterior']
        text = obj['description']
        # print(obj['points']['exterior'])
        # print(obj['description'])
        x_min, y_min, x_max, y_max = int(min(x1, x2)), int(min(y1, y2)), int(max(x1, x2)), int(max(y1, y2))
        if x_max - x_min <= 0 or y_max - y_min <= 0:
            continue

        bboxes.append([(x_min, y_min), (x_max, y_max)])
        texts.append(text)
    return bboxes, texts

def convert_to_white_area_by_bboxes(img, bboxes):
    raw_img = deepcopy(img)
    if len(bboxes) == 0:
        update_img = img
    else:
        for i, box in enumerate(bboxes):
            left_top, right_bottom = box[0], box[1]
            white = (255, 255, 255)
            update_img = cv2.rectangle(raw_img, left_top, right_bottom, white, -1)
    return update_img

def remove_empty_ocr_result(bboxes, texts, blocklist=['', ' ']):
    for i in reversed(range(len(texts))):
        text = texts[i]
        if text in blocklist:
            del texts[i]
            del bboxes[i]
    return bboxes, texts

def update_obj_data(obj_data, id, classId, description, geometryType, labelerLogin, createdAt, updatedAt, tags, classTitle, points):
    obj_data['id'] = id
    obj_data['classId'] = classId
    obj_data['description'] = description
    obj_data['geometryType'] = geometryType
    obj_data['labelerLogin'] = labelerLogin
    obj_data['createdAt'] = createdAt
    obj_data['updatedAt'] = updatedAt
    obj_data['tags'] = tags
    obj_data['classTitle'] = classTitle
    obj_data['classId'] = classId
    obj_data['points'] = points
    return obj_data

def main(args):
    ini = utils.get_ini_parameters(args.ini_fname)
    logger = utils.setup_logger_with_ini(ini['LOGGER'],
                                         logging_=args.logging_, console_=args.console_logging_)
    if args.op_mode == 'UPDATE_JSON':
        # Init OCR engine.
        sys_ocr = system_ocr.SysOCR(ini=utils.get_ini_parameters(ini['SUPERVISELY']['system_ocr_ini_fname']))
        sys_ocr.init_logger(logger=logger)
        sys_ocr.init_functions()

        # Load the project meta-data.
        project = sly.Project(args.dataset_path, sly.OpenMode.READ)

        # Print basic project metadata.
        logger.info("Project name : {}, Total images : {}".format(project.name, project.total_items))

        for dataset in project:
            logger.info("Dataset: {}".format(dataset.name))
            # if dataset.name != '라이트쎈_중2-1_부록': # '': ## CPR_기하-문제
            #     continue
            # else:
            #     pass

            # 존재하는 데이터셋 pass
            rst_path = dataset.directory.replace(os.path.dirname(args.dataset_path), os.path.dirname(OUT_PATH))
            if os.path.exists(rst_path):
                continue

            for file_idx, img_fname in enumerate(dataset):
                img_path = dataset.get_img_path(img_fname)
                ann_path = dataset.get_ann_path(img_fname)
                # ann = sly.Annotation.load_json_file(ann_path, project.meta)

                img = utils.imread(img_path, color_fmt='RGB')
                with open(ann_path) as json_file:
                    json_data = json.load(json_file)

                bboxes, texts = extract_ocr_results_from_dict(json_data)

                # 1) 사전 작업된 Box 영역을 white pixel로 변환
                convert_img = convert_to_white_area_by_bboxes(img, bboxes)

                # 2) 변환된 이미지로 OCR 수행 (한국어 모델)
                img_dir, core_name, img_ext = utils.split_fname(img_path)
                ann_dir, _, ann_ext = utils.split_fname(ann_path)

                rst_img_path = img_dir.replace(os.path.dirname(args.dataset_path), os.path.dirname(OUT_PATH))
                rst_ann_path = ann_dir.replace(os.path.dirname(args.dataset_path), os.path.dirname(OUT_PATH))

                # Run OCR engine.
                ocr_results, derot_img = sys_ocr.run(convert_img, rst_path=rst_img_path, core_name=core_name)

                bboxes, texts, scores = system_ocr.split_result(ocr_results)

                rst_img, rst_bboxes = sys_ocr.adjust_reuslt_by_save_mode(mode=sys_ocr.save_mode, img=img,
                                                                         derot_img=derot_img, derot_angle=sys_ocr.derot_angle, bboxes=bboxes)

                # 3) 인식 결과에서 빈영역 제거
                remove_bboxes, remove_texts = remove_empty_ocr_result(rst_bboxes, texts, blocklist=['', ' '])

                # 3) 추출된 OCR 정보(bboxes, texts)를 json에 업데이트
                if len(json_data['objects']) == 0:
                    id = 1000000000
                else:
                    id = 1000000000 + json_data['objects'][-1]['id']
                classId = 2034583
                geometryType = 'rectangle'
                createdAt = '2020-10-12T09:15:40.271Z'
                updatedAt = '2020-10-12T09:15:40.271Z'
                classTitle = 'korean'
                for i in range(len(remove_texts)):
                    bbox = remove_bboxes[i]
                    text = remove_texts[i]
                    obj_data = {}
                    update_obj = update_obj_data(obj_data,
                                                 id=id, classId=classId, description=text, geometryType=geometryType,
                                                 labelerLogin='freewheelin', createdAt=createdAt, updatedAt=updatedAt, classTitle=classTitle,
                                                 tags=[],
                                                 points={
                                                     'exterior' : [bbox[0], bbox[2]],
                                                     'interior': [[]],
                                                 })
                    json_data['objects'].append(update_obj)
                    id += 1
                if sys_ocr.save_rst_:
                    rst_img_fpath = os.path.join(rst_img_path, core_name + img_ext)
                    rst_ann_fpath = os.path.join(rst_ann_path, core_name + img_ext + ann_ext)
                    utils.imwrite(img, rst_img_fpath)

                    if not os.path.exists(rst_ann_path):
                        os.makedirs(rst_ann_path)
                    with open(rst_ann_fpath, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=4)

                    logger.info(" # Json saved : {}/{}".format(file_idx+1, len(dataset)))

            logger.info(" # Json update complete !!!")
    else:
        print(" @ Error: op_mode, {}, is incorrect.".format(args.op_mode))

    return True

def parse_arguments(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument("--op_mode", required=True, choices=['UPDATE_JSON', 'CHECK_JSON'], help="operation mode")
    parser.add_argument("--ini_fname", required=True, help="Supervisely code ini filename")
    parser.add_argument("--dataset_path", required=True, type=str, help="Dataset directory")

    parser.add_argument("--logging_", default=False, action='store_true', help="Activate logging")
    parser.add_argument("--console_logging_", default=False, action='store_true', help="Activate logging")

    args = parser.parse_args(argv)

    return args


SELF_TEST_ = True
OP_MODE = 'UPDATE_JSON' # UPDATE_JSON / CHECK_JSON
INI_FNAME = _this_basename_ + ".ini"
DATASET_PATH = "../Input/시중교재_new/"
OUT_PATH = "../Output/시중교재_korean/"


if __name__ == "__main__":
    if len(sys.argv) == 1:
        if SELF_TEST_:
            sys.argv.extend(["--op_mode", OP_MODE])
            sys.argv.extend(["--ini_fname", INI_FNAME])
            sys.argv.extend(["--dataset_path", DATASET_PATH])

            sys.argv.extend(["--logging_"])
            sys.argv.extend(["--console_logging_"])
        else:
            sys.argv.extend(["--help"])

    main(parse_arguments(sys.argv[1:]))