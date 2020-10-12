#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import general_utils as utils
import socket_utils as utils_socket
import template_server

_this_folder_ = os.path.dirname(os.path.abspath(__file__))
_this_basename_ = os.path.splitext(os.path.basename(__file__))[0]


def main(args):
    this = template_server.SysRecommend(ini=utils.get_ini_parameters(args.ini_fname))
    this.logger = utils.setup_logger_with_ini(this.ini['LOGGER'],
                                              logging_=args.logging_, console_=args.console_logging_)
    this.init_logger(logger=this.logger)

    this.logger.info(" # Recommend_client starts ...")

    # 테스트할 이미지 로드
    utils.check_directory_existence(args.out_folder, exit_=False, create_=True)
    # img_fnames = utils.get_filenames(args.img_path, extensions=utils.IMG_EXTENSIONS)
    # this.logger.info(" # {:d} image files detected...".format(len(img_fnames)))
    # this.logger.info("")

    # for img_fname in img_fnames:
    this.logger.info("")
    img = utils.imread(args.img_path)


    request_dict = {"id": args.ID, "img": img, "unitCode": args.unit_code, "problemLevel": args.problem_level}

    recv_dict, proc_time \
       = utils_socket.send_run_request_and_recv_response(this.this_server.ip,
                                                              this.this_server.port,
                                                              request_dict,
                                                              show_send_dat_=True,
                                                              show_recv_dat_=True,
                                                              prefix=" Client #",
                                                              logger=this.logger)

    if recv_dict:
       if recv_dict['result'] == "success":
           pass

       else:
            this.logger.error(" @ Error: result is not success, {}.".format(recv_dict['result']))
            this.logger.error(" % recv_dict is {},".format(str(recv_dict)))

    else:
        this.logger.error(" @ Error: response is \"{}\".".format(recv_dict))


