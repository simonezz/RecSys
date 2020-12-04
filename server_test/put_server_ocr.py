import argparse
import math
import os
import sys
import time

import pandas as pd
import pymysql
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

_this_folder_ = os.path.dirname(os.path.abspath(__file__))
_this_basename_ = os.path.splitext(os.path.basename(__file__))[0]


# data 불러옴
def get_all_info(prob_db, unitCode):
    curs = prob_db.cursor(pymysql.cursors.DictCursor)  # to make a dataframe

    sql = f"SELECT ID, unitCode, problemLevel, problemURL, DateTime_Add FROM iclass.Table_middle_problems where DateTime_Add >= str_to_date({DateTime},'%Y%m%d')"

    curs.execute(sql)
    df = pd.DataFrame(curs.fetchall())

    return df


def preprocess_from_url(content, input_shape):
    img = tf.io.decode_png(content, channels=3, name="jpeg_reader")
    img = tf.image.resize(img, input_shape[:2])
    img = preprocess_input(img)

    return img


# batch별로 데이터 elasticsearch에 넣음
def bulk_batchwise(es, part_df, INDEX_NAME, model, input_shape):
    batch_size = 100

    part_df.set_index("ID", inplace=True)

    id_list = []
    img_list = []
    for i in list(part_df.index):

        url = "https://s3.ap-northeast-2.amazonaws.com/mathflat" + part_df.loc[i, 'problemURL'] + "p.png"
        url = url.replace("/math_problems/", "/math_problems/d/")
        try:
            res = requests.get(url)

            img_list.append(preprocess_from_url(res.content, input_shape))
            id_list.append(i)
        except:
            print(f'ID : {i} 의 url이 유효하지 않습니다.')
            pass

    list_ds = tf.data.Dataset.from_tensor_slices(img_list)
    dataset = list_ds.batch(batch_size).prefetch(-1)

    for batch in dataset:
        fvecs = model.predict(batch)

    bulk(es, [{'_index': INDEX_NAME,
               '_id': id_list[i], 'fvec': list(normalize(fvecs[i:i + 1])[0].tolist()),
               'unitCode': part_df.loc[id_list[i], 'unitCode'], 'problemLevel': part_df.loc[id_list[i], 'problemLevel']}
              for i in range(len(id_list))])

    return


# 모든 데이터를 넣음
def bulk_all(df, INDEX_FILE, INDEX_NAME):
    es = Elasticsearch(hosts=['localhost:9200'])
    dim = 1280
    bs = 10
    nloop = math.ceil(df.shape[0] / bs)

    input_shape = (224, 224, 3)
    base = tf.keras.applications.MobileNetV2(input_shape=input_shape,
                                             include_top=False,
                                             weights='imagenet')
    base.trainable = False

    model = Model(inputs=base.input, outputs=layers.GlobalAveragePooling2D()(base.output))

    for k in tqdm(range(nloop)):
        bulk_batchwise(es, df.loc[k * bs:min((k + 1) * bs, df.shape[0])], INDEX_NAME, model, input_shape)

    es.indices.refresh(index=INDEX_NAME)
    print(es.cat.indices(v=True))


def put_data(date_time):
    prob_db = pymysql.connect(
        user='real',
        passwd='vmfl515!dnlf',
        host='sorinegi-cluster.cluster-ro-ce1us4oyptfa.ap-northeast-2.rds.amazonaws.com',
        db='iclass',
        charset='utf8'
    )

    # print(f'{date_time}이후로 추가된 문제를 가져옵니다.')

    print(f'{unitCode}의 문제들을 가져옵니다.')
    df = get_all_info(prob_db, unitCode)

    INDEX_FILE = '../test2/system/mapping_whole_img.json'
    INDEX_NAME = 'ocr_test'

    bulk_start = time.time()

    bulk_all(df, INDEX_FILE, INDEX_NAME)

    print(f'총 데이터 {df.shape[0]}개 bulk 소요시간은 {time.time() - bulk_start}')
    print("Success!")


def main(args):
    this = SysOCR(ini=utils.get_ini_parameters(args.ini_fname))
    this.logger = utils.setup_logger_with_ini(this.ini['LOGGER'],
                                              logging_=args.logging_, console_=args.console_logging_)
    this.init_logger(logger=this.logger)
    this.init_functions()

    dim = 1280
    bs = 50
    nloop = math.ceil(df.shape[0] / bs)

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
        utils.folder_exists(DEBUG_PATH, create_=True)

        # Set db handler
        db = mysql.MysqlHandler(this.mysql_user_name,
                                this.mysql_passwd,
                                hostname=this.mysql_host_name,
                                port=int(this.mysql_port),
                                database=this.mysql_db_name,
                                logger=None,
                                show_=True)
        db_colum_names = db.select_column_names(this.mysql_table_name)
        print("DB column names : {}".format(db_colum_names))

        # set db filter cond.
        cond_list = ["{0}={1}".format('unitCode', '332000036'), ]

        filter_string = db.create_filter_string(cond_list=cond_list)
        print(filter_string)

        # 데이터 정보 가져옴

        if this.mysql_table_name == "Table_middle_problems":  # 문제은행
            db_data = db.select_with_filter(this.mysql_table_name, filter_string=filter_string,
                                            col_names=['ID', 'problemURL', 'unitCode', 'problemLevel'])  # 문제은행

            img_ext = 'p.png'

            img_urls = [
                img_base_url + p_url[1].replace('/math_problems/', '/math_problems/{}/'.format(this.s3_resol)) + img_ext
                for p_url in db_data]
            img_urls = img_base_url + p_url.replace('/math_problems/',
                                                    '/math_problems/{}/'.format(this.s3_resol)) + img_ext

        else:  # 시중문제
            db_data = db.select_with_filter(this.mysql_table_name, filter_string=filter_string,
                                            col_names=['ID', 'BookNameCode'])  # 시중문제
            img_urls = [f"https://mathflat.s3.ap-northeast-2.amazonaws.com/math_problems/book/{p_url[1]}/{p_url[0]}.png"
                        for p_url in db_data]  # 시중문제 볼 때 옵션

        img_ids = [p_url[0] for p_url in db_data]  # 문제 아이디 리스트

        print("DB data size : {}".format(len(db_data)))

        # img_fnames = sorted(img_fnames, key=lambda x: int(x.replace(".jpg", "").split('_')[-1]))
        this.logger.info(" [SYS-OCR] # Total file number to be processed: {:d}.".format(len(img_urls)))

        for loop in tqdm(range(nloop)):  # batch size 만큼씩 집어넣음
            batch_img_urls = img_urls[loop * bs: min((loop + 1) * bs, len(img_urls))]

        for idx, img_url in enumerate(img_urls):
            this.logger.info(" [SYS-OCR] # Processing {} ({:d}/{:d})".format(img_url, (idx + 1), len(img_urls)))
            # dir_name, core_name, ext = utils.split_fname(img_url)
            core_name = img_ids[idx]  # 저장 이름을 아이디로 바꿈

            rst_path = args.out_path
            this.time_arr = [time.time()]

            res = requests.get(img_url, stream=True).raw
            img = np.asarray(bytearray(res.read()), dtype="uint8")
            img = cv2.imdecode(img, cv2.IMREAD_COLOR)

            # Run OCR
            # img = utils.imread(img_url, color_fmt='RGB')
            if img is None:  # or idx <= 34:
                continue

            ocr_results, derot_img = this.run(img, rst_path, core_name)
            this.logger.info(" # OCR results : {}".format(ocr_results))

            # # Group text boxes by height, width_ths
            group_ocr_results = group_text_box_by_ths(ocr_results, ycenter_ths=this.detect_ycenter_ths,
                                                      height_ths=this.detect_ycenter_ths, width_ths=1.5)

            bboxes, texts, scores = split_result(group_ocr_results)

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
            this.logger.info(" [SYS-OCR] # Done {:d}/{:d}-th frame : {}".format(idx + 1, len(img_urls), time_arr_str))

    this.logger.info(" # {} in {} mode finished.".format(_this_basename_, args.op_mode))

    return True


def parse_arguments(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument("--op_mode", required=True, choices=['standalone', 'standalone-s3', 'server'],
                        help="operation mode")
    parser.add_argument("--ini_fname", required=True, help="System code ini filename")
    # parser.add_argument("--img_path", required=True, type=str, help="input file")
    # parser.add_argument("--out_path", default=".", help="Output folder")

    parser.add_argument("--logging_", default=False, action='store_true', help="Activate logging")
    parser.add_argument("--console_logging_", default=False, action='store_true', help="Activate logging")

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
# OUT_PATH = "../Output/test/"


if __name__ == "__main__":
    if len(sys.argv) == 1:
        if SELF_TEST_:
            sys.argv.extend(["--op_mode", OP_MODE])
            sys.argv.extend(["--ini_fname", INI_FNAME])
            # sys.argv.extend(["--img_path", IMG_PATH])
            # sys.argv.extend(["--out_path", OUT_PATH])
            sys.argv.extend(["--logging_"])
            sys.argv.extend(["--console_logging_"])
        else:
            sys.argv.extend(["--help"])

    main(parse_arguments(sys.argv[1:]))
