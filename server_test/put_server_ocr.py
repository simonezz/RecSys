import argparse
import math
import os
import re
import sys
import time

import tensorflow as tf
import tensorflow.keras.layers as layers
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from sklearn.preprocessing import normalize
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.models import Model
from tqdm import tqdm

sys.path.insert(0, '../utils')
sys.path.insert(0, '../ocr/EasyOCR')

import cv2
import numpy as np
import requests
from easyocr import craft_file_utils as file_utils
from easyocr.utils import group_text_box_by_ths
from utility import general_utils as utils
from utility import mysql_handler as mysql
from system.system_ocr import SysOCR
from PyKomoran import *

_this_folder_ = os.path.dirname(os.path.abspath(__file__))
_this_basename_ = os.path.splitext(os.path.basename(__file__))[0]


# data 불러옴
# def get_all_info(prob_db, unitCode):
#     curs = prob_db.cursor(pymysql.cursors.DictCursor)  # to make a dataframe
#
#     sql = f"SELECT ID, unitCode, problemLevel, problemURL, DateTime_Add FROM iclass.Table_middle_problems where DateTime_Add >= str_to_date({DateTime},'%Y%m%d')"
#
#     curs.execute(sql)
#     df = pd.DataFrame(curs.fetchall())
#
#     return df

def split_result(result):
    bboxes, texts, scores = [], [], []
    for zipped in result:
        if len(zipped) == 2:
            bboxes.append(zipped[0])
            texts.append(zipped[1])
            scores = None
        else:
            bboxes.append(zipped[0])
            texts.append(zipped[1])
            scores.append(zipped[2])
    return bboxes, texts, scores


def preprocess_from_url(content, input_shape):
    img = tf.io.decode_png(content, channels=3, name="jpeg_reader")
    img = tf.image.resize(img, input_shape[:2])
    img = preprocess_input(img)

    return img


def main(args):
    komoran = Komoran(DEFAULT_MODEL['FULL'])
    komoran.set_user_dic('../utils/komoran_dict.tsv')

    word_classes = ['NNP', 'NNG', 'VV', 'EC', 'JKB', 'MAG', 'MM', 'VA', 'XSV', 'EP', 'JX']

    this = SysOCR(ini=utils.get_ini_parameters(args.ini_fname))
    this.logger = utils.setup_logger_with_ini(this.ini['LOGGER'],
                                              logging_=args.logging_, console_=args.console_logging_)
    this.init_logger(logger=this.logger)
    this.init_functions()

    dim = 1280
    bs = 50

    es = Elasticsearch(hosts=["localhost:9200"])

    # Index 생성
    es.indices.delete(index=args.index_name, ignore=[404])  # Delete if already exists

    # mappings 정의
    with open(args.index_file) as index_file:
        source = index_file.read().strip()
        es.indices.create(index=args.index_name, body=source)  # Create ES index
    print("Elasticsearch Index :", args.index_name, "created!")

    input_shape = (224, 224, 3)

    base = tf.keras.applications.MobileNetV2(input_shape=input_shape,
                                             include_top=False,
                                             weights='imagenet')
    base.trainable = False

    model = Model(inputs=base.input, outputs=layers.GlobalAveragePooling2D()(base.output))

    this.logger.info(" [SYS-OCR] # {} in {} mode started!".format(_this_basename_, args.op_mode))

    if args.op_mode == 'standalone':
        utils.folder_exists(args.out_path, create_=True)
        utils.folder_exists(DEBUG_PATH, create_=True)
        if os.path.isdir(args.img_path):
            utils.copy_folder_structure(args.img_path, args.out_path)
            utils.copy_folder_structure(DEBUG_PATH, args.out_path)

        img_fnames = utils.get_filenames(args.img_path, extensions=utils.IMG_EXTENSIONS)
        img_fnames = sorted(img_fnames, key=lambda x: int(x.replace(".jpg", "").split('_')[-1]))
        this.logger.info(" [SYS-OCR] # Total file number to be processed: {:d}.".format(len(img_fnames)))

        for idx, fname in enumerate(img_fnames):
            this.logger.info(" [SYS-OCR] # Processing {} ({:d}/{:d})".format(fname, (idx + 1), len(img_fnames)))
            dir_name, core_name, ext = utils.split_fname(fname)
            rst_path = dir_name.replace(os.path.dirname(args.img_path), os.path.dirname(args.out_path))
            this.time_arr = [time.time()]

            # Run OCR
            img = utils.imread(fname, color_fmt='RGB')
            ocr_results, derot_img = this.run(img, rst_path, core_name)
            this.logger.info(" # OCR results : {}".format(ocr_results))

            # # Group text boxes by height, width_ths
            group_ocr_results = group_text_box_by_ths(ocr_results, ycenter_ths=this.detect_ycenter_ths,
                                                      height_ths=this.detect_ycenter_ths, width_ths=1.5)

            bboxes, texts, scores = split_result(group_ocr_results)

            rst_fname = "".join(['res_', core_name, ext])
            rst_img, rst_bboxes = this.adjust_reuslt_by_save_mode(mode=this.coord_mode, img=img,
                                                                  derot_img=derot_img, derot_angle=this.derot_angle,
                                                                  bboxes=bboxes)
            if this.save_rst_:
                file_utils.saveResult(rst_fname, rst_img, rst_bboxes, dirname=rst_path, texts=texts,
                                      mode=SaveImageMode[this.background_mode].name)
                # ,scores=scores)
            this.logger.info(" # Saved image at {}".format(os.path.join(rst_path, rst_fname)))

            this.time_arr.append(time.time())

            time_arr_str = ["{:5.3f}".format(this.time_arr[i + 1] - this.time_arr[i])
                            for i in range(len(this.time_arr) - 1)]
            this.logger.info(" [SYS-OCR] # Done {:d}/{:d}-th frame : {}".format(idx + 1, len(img_fnames), time_arr_str))


    elif args.op_mode == 'standalone-s3':
        utils.folder_exists(args.out_path, create_=True)
        # utils.folder_exists(DEBUG_PATH, create_=True)

        # Set db handler
        db = mysql.MysqlHandler(this.mysql_user_name,
                                this.mysql_passwd,
                                hostname=this.mysql_host_name,
                                port=int(this.mysql_port),
                                database=this.mysql_db_name,
                                logger=None,
                                show_=True)
        db_column_names = db.select_column_names(this.mysql_table_name)
        print("DB column names : {}".format(db_column_names))

        # set db filter cond.
        cond_list = ["{0}={1}".format('unitCode', '332000036'), ]

        filter_string = db.create_filter_string()
        # print(filter_string)

        # 데이터 정보 가져옴

        if this.mysql_table_name == "Table_middle_problems":  # 문제은행

            db_data = db.select_with_filter(this.mysql_table_name, filter_string=filter_string,
                                            col_names=['ID', 'problemURL', 'unitCode', 'problemLevel'])

            db_data.set_index("ID", inplace=True)  # 문제은행

        else:  # 시중문제
            db_data = db.select_with_filter(this.mysql_table_name, filter_string=filter_string,
                                            col_names=['ID', 'BookNameCode'], dictionary=True)  # 시중문제

            db_data.set_index("ID", inplace=True)  # 문제은행

        print("DB data size : {}".format(len(db_data)))

        nloop = math.ceil(db_data.shape[0] / bs)

        this.logger.info(" [SYS-OCR] # Total file number to be processed: {:d}.".format(len(db_data)))

        for loop in tqdm(range(nloop)):  # batch size 만큼씩 집어넣음

            this.logger.info(f"{loop + 1}th/{nloop} loop start")

            img_list = []
            id_list = []
            text_list = []

            for ID in (list((db_data.iloc[loop * bs: min((loop + 1) * bs, db_data.shape[0])]).index)):

                if this.mysql_table_name == "Table_middle_problems":  # 문제은행
                    prob_url = ("https://s3.ap-northeast-2.amazonaws.com/mathflat" + db_data.loc[
                        ID, 'problemURL'] + "p.png").replace("/math_problems/", "/math_problems/ng/")
                else:  # 시중문제
                    prob_url = f"https://mathflat.s3.ap-northeast-2.amazonaws.com/math_problems/book/{db_data.loc[ID, 'BookNameCode']}/{ID}.png"

                # this.logger.info(" [SYS-OCR] # Processing {} (ID : {})".format(prob_url, (ID)))
                # dir_name, core_name, ext = utils.split_fname(img_url)
                core_name = str(ID)  # 저장 이름을 아이디로 바꿈

                rst_path = args.out_path
                this.time_arr = [time.time()]
                try:
                    res = requests.get(prob_url, stream=True).raw
                    img = np.asarray(bytearray(res.read()), dtype="uint8")
                    img = cv2.imdecode(img, cv2.IMREAD_COLOR)

                    img_list.append(preprocess_input(tf.image.resize(img, input_shape[:2])))
                    id_list.append(ID)

                except:
                    continue  # png파일이 존재하지 않음

                # Run OCR
                # img = utils.imread(img_url, color_fmt='RGB')
                #     if img is None:  # or idx <= 34:
                #         continue

                ocr_results, derot_img = this.run(img, rst_path, core_name)
                # this.logger.info(" # OCR results : {}".format(ocr_results))

                # # Group text boxes by height, width_ths
                group_ocr_results = group_text_box_by_ths(ocr_results, ycenter_ths=this.detect_ycenter_ths,
                                                          height_ths=this.detect_ycenter_ths, width_ths=1.5)

                bboxes, texts, scores = split_result(group_ocr_results)
                # text_list.append(texts)
                text_list.append(
                    ' '.join(komoran.get_morphes_by_tags(re.sub('[^ 가-힣]', '', " ".join(texts)), word_classes)))

                # # rst_fname = "".join(['res_', core_name, ext])
                # rst_fname = core_name
                #
                # rst_img, rst_bboxes = this.adjust_reuslt_by_save_mode(mode=this.coord_mode, img=img,
                #                                                       derot_img=derot_img, derot_angle=this.derot_angle,
                #                                                       bboxes=bboxes)
                # if this.save_rst_:
                #     file_utils.saveResult(rst_fname, rst_img, rst_bboxes, dirname=rst_path, texts=texts),
                #     # mode=SaveImageMode[this.background_mode].name)
                #     # ,scores=scores)
                # this.logger.info(" # Saved image at {}".format(os.path.join(rst_path, rst_fname)))
                this.time_arr.append(time.time())

                time_arr_str = ["{:5.3f}".format(this.time_arr[i + 1] - this.time_arr[i])
                                for i in range(len(this.time_arr) - 1)]
                # this.logger.info(" [SYS-OCR] # Done {:d}/{:d}-th frame : {}".format(idx + 1, len(img_urls), time_arr_str))

                # this.logger.info(" # {} in {} mode finished.".format(_this_basename_, args.op_mode))

            fvecs = model.predict(tf.convert_to_tensor(img_list))

            bulk(es, [{'_index': args.index_name,
                       '_id': id_list[i], 'fvec': list(normalize(fvecs[i:i + 1])[0].tolist()),
                       'unitCode': db_data.loc[id_list[i], 'unitCode'],
                       'problemLevel': db_data.loc[id_list[i], 'problemLevel'],
                       'ocr_text': text_list[i]}
                      for i in range(len(id_list))])
            this.logger.info("{} data bulked to index {}".format(len(id_list), (args.index_name)))

    es.indices.refresh(args.index_name)

    print(es.cat.indices(v=True))

    return True


def parse_arguments(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument("--op_mode", required=True, choices=['standalone', 'standalone-s3', 'server'],
                        help="operation mode")
    parser.add_argument("--ini_fname", required=True, help="System code ini filename")
    # parser.add_argument("--img_path", required=True, type=str, help="input file")
    parser.add_argument("--out_path", default=".", help="Output folder")

    parser.add_argument("--logging_", default=False, action='store_true', help="Activate logging")
    parser.add_argument("--console_logging_", default=False, action='store_true', help="Activate logging")

    parser.add_argument("--index_name", default=False)
    parser.add_argument("--index_file", default=False)

    args = parser.parse_args(argv)

    return args


SELF_TEST_ = True
OP_MODE = 'standalone-s3'  # standalone / standalone-s3 / server
# INI_FNAME = _this_basename_ + ".ini"
INI_FNAME = "../ocr/EasyOCR/system/system_ocr.ini"
# DEBUG_PATH = "../Debug/IMGs/쎈_수학(상)2/"
# IMG_PATH = "../Input/시중교재_new/쎈_수학(상)/img/"
# OUT_PATH = "../Output/시중교재_new/쎈_수학(상)/img/"
# IMG_PATH = "../Input/시중교재_problem/"
# OUT_PATH = "../Output/s3/"
# IMG_PATH = "../Input/test/crop_problem.png"
# OUT_PATH = "../Output/test/"
# IMG_PATH = "../Input/test/라이트쎈 중2-1 부록_15.jpg"
OUT_PATH = "../Output/test/"
INDEX_NAME = "ocr_test"
INDEX_FILE = '../test2/system/mapping_whole_img_text.json'

if __name__ == "__main__":
    if len(sys.argv) == 1:
        if SELF_TEST_:
            sys.argv.extend(["--op_mode", OP_MODE])
            sys.argv.extend(["--ini_fname", INI_FNAME])
            # sys.argv.extend(["--img_path", IMG_PATH])
            sys.argv.extend(["--out_path", OUT_PATH])
            sys.argv.extend(["--logging_"])
            sys.argv.extend(["--console_logging_"])

            sys.argv.extend(["--index_name", INDEX_NAME])
            sys.argv.extend(["--index_file", INDEX_FILE])

        else:
            sys.argv.extend(["--help"])

    main(parse_arguments(sys.argv[1:]))
