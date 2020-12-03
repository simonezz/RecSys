import argparse
import os
import sys
import time
from enum import Enum

import cv2
import easyocr
import numpy as np
import requests
from easyocr import craft_file_utils as file_utils
from easyocr.utils import group_text_box_by_ths
from utility import general_utils as utils
from utility import imgproc_utils as img_utils
from utility import mysql_handler as mysql

_this_folder_ = os.path.dirname(os.path.abspath(__file__))
_this_basename_ = os.path.splitext(os.path.basename(__file__))[0]


class SaveImageMode(Enum):
    origin = 1
    white = 2

class SysOCR:
    def __init__(self, ini=None, logger=None):
        self.ini = ini
        self.logger = logger

        self.textarea_detection_algorithm = None
        self.text_detection_algorithm = None
        self.text_recognition_algorithm = None
        self.textarea_detection_ini = None
        self.easyocr_ini = None
        self.enable_mathpix_ = None
        self.convert_plain_ = None
        self.min_height = None
        self.coord_mode = None
        self.save_rst_ = None

        self.text_reader_inst = None
        self.text_detect_inst = None
        self.text_recog_inst = None
        self.text_convert_inst = None
        # self.text_decode_inst = None

        self.lang = []
        self.gpu = None

        self.img = None
        self.derot_img = None
        self.derot_angle = None
        self.ocr_results = []

        self.time_arr = []
        self.init_variables()

        if self.ini:
            self.init_ini(self.ini['SYS_OCR'])

    def init_variables(self):
        # De-rotation variables
        self.derot_inside_margin_ratio = None
        self.derot_max_angle = None
        self.derot_max_angle_candidates = None
        self.derot_angle_resolution = None
        self.derot_pause_sec = None
        self.derot_save_img_ = None

        # CRAFT variables
        self.detect_min_size = None
        self.detect_text_threshold = None
        self.detect_low_text = None
        self.detect_link_threshold = None
        self.detect_canvas_size = None
        self.detect_mag_ratio = None
        self.detect_slope_ths = None
        self.detect_ycenter_ths = None
        self.detect_height_ths = None
        self.detect_width_ths = None
        self.detect_add_margin = None
        
        # CRNN variables
        self.recog_decoder = None
        self.recog_beamWidth = None
        self.recog_batch_size = None
        self.recog_workers = None
        self.recog_allowlist = []
        self.recog_blocklist = []
        self.recog_detail = None
        self.recog_paragraph = False
        self.recog_contrast_ths = None
        self.recog_adjust_contrast = None
        self.recog_filter_ths = None

        # MYSQL variables
        self.mysql_user_name = None
        self.mysql_passwd = None
        self.mysql_host_name = None
        self.mysql_port = None
        self.mysql_db_name = None
        self.mysql_table_name = None

        # AWS S3 variables
        self.s3_url = None
        self.s3_resol = None

    def init_ini(self, ini):
        self.textarea_detection_algorithm = ini['textarea_detection_algorithm']
        self.text_detection_algorithm = ini['text_detection_algorithm']
        self.text_recognition_algorithm = ini['text_recognition_algorithm']
        self.textarea_detection_ini = utils.get_ini_parameters(os.path.join(_this_folder_, ini['textarea_detection_ini_fname']))
        self.easyocr_ini = utils.get_ini_parameters(os.path.join(_this_folder_, ini['ocr_ini_fname']))
        self.enable_mathpix_ = True if ini['enable_mathpix_'] == 'True' else False
        self.convert_plain_ = True if ini['convert_plain_'] == 'True' else False
        self.min_height = int(ini['min_height'])
        self.coord_mode = ini['coord_mode']
        self.background_mode = ini['background_mode']
        self.save_rst_ = True if ini['save_rst_'] == 'True' else False

        langs = self.easyocr_ini['EASY_OCR']['lang'].split(',')
        self.lang = [lang.strip() for lang in langs]
        self.gpu = True if self.easyocr_ini['EASY_OCR']['gpu'] == 'True' else False

        self.init_craft_ini(self.easyocr_ini['CRAFT'])
        self.init_crnn_ini(self.easyocr_ini['CRNN'])

    def init_craft_ini(self, ini):
        self.detect_min_size = int(ini['min_size'])
        self.detect_text_threshold = float(ini['text_threshold'])
        self.detect_low_text = float(ini['low_text'])
        self.detect_link_threshold = float(ini['link_threshold'])
        self.detect_canvas_size = int(ini['canvas_size'])
        self.detect_mag_ratio = float(ini['mag_ratio'])
        self.detect_slope_ths = float(ini['slope_ths'])
        self.detect_ycenter_ths = float(ini['ycenter_ths'])
        self.detect_height_ths = float(ini['height_ths'])
        self.detect_width_ths = float(ini['width_ths'])
        self.detect_add_margin = float(ini['add_margin'])

    def init_crnn_ini(self, ini):
        self.recog_decoder = ini['decoder']
        self.recog_beamWidth = int(ini['beamWidth'])
        self.recog_batch_size = int(ini['batch_size'])
        self.recog_workers = int(ini['workers'])
        self.recog_allowlist = ini['allowlist']
        self.recog_blocklist = ini['blocklist']
        self.recog_detail = int(ini['detail'])
        self.recog_paragraph = True if ini['paragraph'] == 'True' else False
        self.recog_contrast_ths = float(ini['contrast_ths'])
        self.recog_adjust_contrast = float(ini['adjust_contrast'])
        self.recog_filter_ths = float(ini['filter_ths'])

    def init_logger(self, logger):
        self.logger = logger

    def init_functions(self):
        self.init_derotation(self.ini['DEROTATION'])
        self.init_split_area(self.ini['SPLIT_AREA'])
        self.init_mysql(self.ini['MYSQL'])
        self.init_aws_s3(self.ini['AWS_S3'])
        self.init_text_reader()
        self.init_text_detection()
        self.init_text_recognition()

    def init_derotation(self, ini):
        self.derot_inside_margin_ratio = float(ini['inside_margin_ratio'])
        self.derot_max_angle = float(ini['max_angle'])
        self.derot_max_angle_candidates = int(ini['max_angle_candidates'])
        self.derot_angle_resolution = float(ini['angle_resolution'])
        self.derot_pause_sec = int(ini['pause_sec'])
        self.derot_save_img_ = True if ini['save_img_'] == 'True' else False

    def init_split_area(self, ini):
        self.split_enable_ = True if ini['enable_'] == 'True' else False
        self.split_mode = ini['mode']
        self.line_detection_algorithm = ini['line_detection_algorithm']
        self.split_roi_ratio = float(ini['roi_ratio'])
        self.split_pause_sec = int(ini['pause_sec'])
        self.split_save_img_ = True if ini['save_img_'] == 'True' else False

    def init_mysql(self, ini):
        self.mysql_user_name = ini['user_name']
        self.mysql_passwd = ini['password']
        self.mysql_host_name = ini['host_name']
        self.mysql_port = ini['port']
        self.mysql_db_name = ini['db_name']
        self.mysql_table_name = ini['table_name']

    def init_aws_s3(self, ini):
        self.s3_url = ini['url']
        self.s3_resol = ini['resol']

    def init_text_reader(self):
        self.text_reader_inst = easyocr.Reader(lang_list=self.lang, gpu=self.gpu, download_enabled=False, model_storage_directory='../model')

    def init_text_detection(self):
        self.text_det_inst = self.text_reader_inst.detector

    def init_text_recognition(self):
        self.text_recog_inst = self.text_reader_inst.recognizer
        self.text_convert_inst = self.text_reader_inst.converter

    def run(self, img, rst_path='', core_name=''):
        global split_imgs, horizontal_list, free_list

        img_h, img_w, img_c = img.shape
        ts = time.time()

        # De-rotate image
        try:
            self.derot_img, self.derot_angle = img_utils.derotate_image(img, inside_margin_ratio=self.derot_inside_margin_ratio,
                                                                        max_angle=self.derot_max_angle, max_angle_candidates=self.derot_max_angle_candidates,
                                                                        angle_resolution=self.derot_angle_resolution, check_time_=True,
                                                                        pause_sec=self.derot_pause_sec, save_img_=self.derot_save_img_,
                                                                        save_fpath=os.path.join(rst_path, core_name), logger=self.logger)
        except Exception as dre:
            self.logger.error(" # run.derotate_image.exception : {}".format(dre))

        self.time_arr.append(time.time())
        
        if img_h < self.min_height:            
            split_imgs = [img]
        else:
            # Split area by line detection
            try:
                split_imgs, split_ = img_utils.split_area_by_condition(self.derot_img, enable_=self.split_enable_,
                                                                       mode=self.split_mode, line_detection_algorithm=self.line_detection_algorithm,
                                                                       pause_sec=self.split_pause_sec, save_img_=self.split_save_img_,
                                                                       save_fpath=os.path.join(rst_path, core_name), roi_ratio=self.split_roi_ratio,
                                                                       check_time_=True, logger=self.logger)
            except Exception as e:
                self.logger.error(" # run.split_area_in_image.exception : {}".format(e))

        self.time_arr.append(time.time())

        curr_x, curr_y = 0, 0
        self.ocr_results = []
        for i, split_img in enumerate(split_imgs):
            # Detect texts in image - CRAFT
            detect_start_time = time.time()
            try:
                horizontal_list, free_list = self.text_reader_inst.detect(split_img,
                                                                          min_size=self.detect_min_size, text_threshold=self.detect_text_threshold, low_text=self.detect_low_text,
                                                                          link_threshold=self.detect_link_threshold, canvas_size=self.detect_canvas_size, mag_ratio=self.detect_mag_ratio,
                                                                          slope_ths=self.detect_slope_ths, ycenter_ths=self.detect_ycenter_ths, height_ths=self.detect_height_ths,
                                                                          width_ths=self.detect_width_ths, add_margin=self.detect_add_margin, reformat=False)
            except Exception as e:
                self.logger.error(" # run.text_detection.exception : {}".format(e))

            self.time_arr.append(time.time())
            self.logger.info(" [TEXT-DETECT] # {}/{}-th elapsed time : {:.3f} sec.".format(i+1, len(split_imgs), time.time() - detect_start_time))

            # 검출 좌표 업데이트
            horizontal_list = [[box[0]+curr_x, box[1]+curr_x, box[2]+curr_y, box[3]+curr_y] for box in horizontal_list]

            # Recognize texts in text detection results - CRNN
            try:
                img_cv_grey = cv2.cvtColor(self.derot_img, cv2.COLOR_RGB2GRAY)

                recog_start_time = time.time()
                ocr_results = self.text_reader_inst.recognize(img_cv_grey, horizontal_list, free_list,
                                                              decoder=self.recog_decoder, beamWidth=self.recog_beamWidth, batch_size=self.recog_batch_size,
                                                              workers=self.recog_workers, allowlist=self.recog_allowlist, blocklist=self.recog_blocklist,
                                                              detail=self.recog_detail, paragraph=self.recog_paragraph, contrast_ths=self.recog_contrast_ths,
                                                              adjust_contrast=self.recog_adjust_contrast, filter_ths=self.recog_filter_ths, reformat=False,
                                                              enable_mathpix_=self.enable_mathpix_, convert_plain_=self.convert_plain_)
                self.time_arr.append(time.time())
                self.logger.info(" [TEXT-RECOG] # {}/{}-th elapsed time : {:.3f} sec.".format(i+1, len(split_imgs), time.time() - recog_start_time))
                self.ocr_results += ocr_results
            except Exception as e:
                self.logger.error(" # run.text_recognition.exception : {}".format(e))

            curr_x, curr_y = get_page_position_by_index([curr_x, curr_y], i, split_img)

        self.logger.info(" [SYS-OCR] # elapsed time : {:.3f} sec.".format(time.time() - ts))
        return self.ocr_results, self.derot_img

    def adjust_reuslt_by_save_mode(self, mode, img, derot_img, derot_angle, bboxes):
        if mode == 'origin':
            rst_img = img
            rst_bboxes = img_utils.transform_bboxes(bboxes, derot_angle, derot_img.shape, img.shape)
        elif mode == 'derotate':
            rst_img = derot_img
            rst_bboxes = bboxes
        return rst_img, rst_bboxes

def get_page_position_by_index(curr_pos, idx, img):
    curr_x, curr_y = curr_pos
    if idx + 1 == 1:
        curr_y += img.shape[0]
    elif idx + 1 == 2:
        curr_x += img.shape[1]
    return curr_x, curr_y

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


def main(args):
    this = SysOCR(ini=utils.get_ini_parameters(args.ini_fname))
    this.logger = utils.setup_logger_with_ini(this.ini['LOGGER'],
                                              logging_=args.logging_, console_=args.console_logging_)
    this.init_logger(logger=this.logger)
    this.init_functions()

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
            ocr_results, derot_img  = this.run(img, rst_path, core_name)
            this.logger.info(" # OCR results : {}".format(ocr_results))

            # # Group text boxes by height, width_ths
            group_ocr_results = group_text_box_by_ths(ocr_results, ycenter_ths=this.detect_ycenter_ths, height_ths=this.detect_ycenter_ths, width_ths=1.5)

            bboxes, texts, scores = split_result(group_ocr_results)

            rst_fname = "".join(['res_', core_name, ext])
            rst_img, rst_bboxes = this.adjust_reuslt_by_save_mode(mode=this.coord_mode, img=img,
                                                                  derot_img=derot_img, derot_angle=this.derot_angle,
                                                                  bboxes=bboxes)
            if this.save_rst_:
                file_utils.saveResult(rst_fname, rst_img, rst_bboxes, dirname=rst_path, texts=texts, mode=SaveImageMode[this.background_mode].name)
                                      #,scores=scores)
            this.logger.info(" # Saved image at {}".format(os.path.join(rst_path, rst_fname)))

            this.time_arr.append(time.time())

            time_arr_str = ["{:5.3f}".format(this.time_arr[i + 1] - this.time_arr[i])
                            for i in range(len(this.time_arr) - 1)]
            this.logger.info(" [SYS-OCR] # Done {:d}/{:d}-th frame : {}".format(idx+1, len(img_fnames), time_arr_str))


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
        cond_list = ["{0}={1}".format('unitCode', '212072'), ]

        filter_string = db.create_filter_string(cond_list=cond_list)
        print(filter_string)

        if this.mysql_table_name == "Table_middle_problems":  # 시중문제
            db_data = db.select_with_filter(this.mysql_table_name, filter_string=filter_string,
                                            col_names=['ID', 'problemURL'])  # 문제은행

            img_ext = 'p.png'

            img_urls = [
                img_base_url + p_url[1].replace('/math_problems/', '/math_problems/{}/'.format(this.s3_resol)) + img_ext
                for p_url in db_data]
            img_urls = img_base_url + p_url.replace('/math_problems/',
                                                    '/math_problems/{}/'.format(this.s3_resol)) + img_ext

        else:  # 문제은행
            db_data = db.select_with_filter(this.mysql_table_name, filter_string=filter_string,
                                            col_names=['ID', 'BookNameCode'])  # 시중문제
            img_urls = [f"https://mathflat.s3.ap-northeast-2.amazonaws.com/math_problems/book/{p_url[1]}/{p_url[0]}.png"
                        for p_url in db_data]  # 시중문제 볼 때 옵션

        print("DB data size : {}".format(len(db_data)))

        img_base_url = os.path.join(this.s3_url, 'mathflat')
        img_ext = 'p.png'
        img_urls = [
            img_base_url + p_url[0].replace('/math_problems/', '/math_problems/{}/'.format(this.s3_resol)) + img_ext for
            p_url in db_data]
        # img_fnames = sorted(img_fnames, key=lambda x: int(x.replace(".jpg", "").split('_')[-1]))
        this.logger.info(" [SYS-OCR] # Total file number to be processed: {:d}.".format(len(img_urls)))

        for idx, img_url in enumerate(img_urls):
            this.logger.info(" [SYS-OCR] # Processing {} ({:d}/{:d})".format(img_url, (idx + 1), len(img_urls)))
            dir_name, core_name, ext = utils.split_fname(img_url)
            rst_path = args.out_path
            this.time_arr = [time.time()]

            res = requests.get(img_url, stream=True).raw
            img = np.asarray(bytearray(res.read()), dtype="uint8")
            img = cv2.imdecode(img, cv2.IMREAD_COLOR)

            # Run OCR
            # img = utils.imread(img_url, color_fmt='RGB')
            if img is None:# or idx <= 34:
                continue

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
                file_utils.saveResult(rst_fname, rst_img, rst_bboxes, dirname=rst_path, texts=texts),
                                      # mode=SaveImageMode[this.background_mode].name)
                # ,scores=scores)
            this.logger.info(" # Saved image at {}".format(os.path.join(rst_path, rst_fname)))

            this.time_arr.append(time.time())

            time_arr_str = ["{:5.3f}".format(this.time_arr[i + 1] - this.time_arr[i])
                            for i in range(len(this.time_arr) - 1)]
            this.logger.info(" [SYS-OCR] # Done {:d}/{:d}-th frame : {}".format(idx + 1, len(img_urls), time_arr_str))

    this.logger.info(" # {} in {} mode finished.".format(_this_basename_, args.op_mode))

    return True

def parse_arguments(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument("--op_mode", required=True, choices=['standalone', 'standalone-s3', 'server'], help="operation mode")
    parser.add_argument("--ini_fname", required=True, help="System code ini filename")
    parser.add_argument("--img_path", required=True, type=str, help="input file")
    parser.add_argument("--out_path", default=".", help="Output folder")

    parser.add_argument("--logging_", default=False, action='store_true', help="Activate logging")
    parser.add_argument("--console_logging_", default=False, action='store_true', help="Activate logging")

    args = parser.parse_args(argv)

    return args


SELF_TEST_ = True
OP_MODE = 'standalone-s3'  # standalone / standalone-s3 / server
INI_FNAME = _this_basename_ + ".ini"
DEBUG_PATH = "../Debug/IMGs/쎈_수학(상)2/"
# IMG_PATH = "../Input/시중교재_new/쎈_수학(상)/img/"
# OUT_PATH = "../Output/시중교재_new/쎈_수학(상)/img/"
IMG_PATH = "../Input/시중교재_problem/"
OUT_PATH = "../Output/s3/"
# IMG_PATH = "../Input/test/crop_problem.png"
# OUT_PATH = "../Output/test/"
# IMG_PATH = "../Input/test/라이트쎈 중2-1 부록_15.jpg"
# OUT_PATH = "../Output/test/"


if __name__ == "__main__":
    if len(sys.argv) == 1:
        if SELF_TEST_:
            sys.argv.extend(["--op_mode", OP_MODE])
            sys.argv.extend(["--ini_fname", INI_FNAME])
            sys.argv.extend(["--img_path", IMG_PATH])
            sys.argv.extend(["--out_path", OUT_PATH])
            sys.argv.extend(["--logging_"])
            sys.argv.extend(["--console_logging_"])
        else:
            sys.argv.extend(["--help"])

    main(parse_arguments(sys.argv[1:]))
