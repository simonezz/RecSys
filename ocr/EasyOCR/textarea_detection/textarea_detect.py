#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import time
from utility import general_utils as g_utils
from textarea_detection import yolov5_tad
sys.path.append('yolov5')

_this_folder_ = os.path.dirname(os.path.abspath(__file__))
_this_basename_ = os.path.splitext(os.path.basename(__file__))[0]


class TextareaDetect:
    def __init__(self, ini=None, logger=None):
        self.ini = ini
        self.logger = logger

        self.acronym = None

        self.handler = None

        if self.ini is not None:
            self.init_ini(ini['TEXTAREA_DETECT'])

    def init_ini(self, ini):
        self.acronym = ini['acronym']

    def init_handler(self, handler_type='yolov5', logger=g_utils.get_stdout_logger()):
        if handler_type == 'yolov5':
            self.handler = yolov5_tad.YOLOv5_TAD(ini=self.ini, logger=logger)
            pass


def main(args):
    this = TextareaDetect(ini=g_utils.get_ini_parameters(args.ini_fname))
    this.logger = g_utils.setup_logger_with_ini(this.ini['LOGGER'],
                                                logging_=args.logging_, console_=args.console_logging_)

    this.logger.info(" # Starting {}.".format(_this_basename_))

    this.init_handler(args.handler_type, logger=this.logger)
    if os.path.isdir(args.img_path):
        g_utils.copy_folder_structure(args.img_path, args.out_path)
    g_utils.folder_exists(args.out_path, create_=True)

    img_fnames = sorted(g_utils.get_filenames(args.img_path, extensions=g_utils.IMG_EXTENSIONS,
                                            recursive_=True, exit_=True))
    this.logger.info(" # Total file number to be processed: {:d}.".format(len(img_fnames)))

    for idx, fname in enumerate(img_fnames):

        this.time_arr = [time.time()]
        # img = g_utils.imread(fname, color_fmt='RGB')

        if args.handler_type == 'yolov5':
            problem_results, graph_results = this.handler.run(fname)

            this.time_arr.append(time.time())

            dir_name, core_name, ext = g_utils.split_fname(fname)
            # file_utils.saveResult(core_name + '.jpg', img, polys, dirname='./Output/')

        time_arr_str = ["{:5.3f}".format(this.time_arr[i+1] - this.time_arr[i]) for i in range(len(this.time_arr)-1)]
        this.logger.info(" # Textarea detection processing : {:d}-th frame : {}".format(idx + 1, time_arr_str))

    this.logger.info(" # {} finished.".format(_this_basename_))


def parse_arguments(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument("--ini_fname", required=True, help="ini filename")
    parser.add_argument("--img_path", default=None, help="Input image path")
    parser.add_argument("--out_path", default=None, help="Output path")
    parser.add_argument("--handler_type", default='yolov5', choices=['yolov5'], help="Input image path")

    parser.add_argument("--logging_", default=False, action='store_true', help="Logging flag")
    parser.add_argument("--console_logging_", default=False, action='store_true', help="Console logging flag")

    args = parser.parse_args(argv)

    return args


SELF_TEST_ = True

INI_FNAME = _this_basename_ + ".ini"
IMG_PATH = "../Input/시중교재_new/쎈_수학(상)2/img/[SSEN] 2 (상) 본문 (2018) [좋은책신사고]_46.jpg"
OUT_PATH = os.path.join(_this_folder_, "../Output/")
HANDLER_TYPE = 'yolov5'


if __name__ == "__main__":
    if len(sys.argv) == 1:
        if SELF_TEST_:
            sys.argv.extend(["--ini_fname", INI_FNAME])
            sys.argv.extend(["--img_path", IMG_PATH])
            sys.argv.extend(["--out_path", OUT_PATH])
            sys.argv.extend(["--handler_type", HANDLER_TYPE])

            sys.argv.extend(["--logging_"])
            sys.argv.extend(["--console_logging_"])
        else:
            sys.argv.extend(["--help"])

    main(parse_arguments(sys.argv[1:]))
