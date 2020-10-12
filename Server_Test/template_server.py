import os
import general_utils as utils
import socket_utils as utils_socket

_this_folder_ = os.path.dirname(os.path.abspath(__file__))
_this_basename_ = os.path.splitext(os.path.basename(__file__))[0]


class SysRecommend:
    def __init__(self, ini=None, logger=None):
        self.ini = ini
        self.logger = logger

    def init_server(self):
        self.this_server = utils_socket.ServerFeature(ini=self.ini['SERVER_MODE'])

    def init_logger(self, logger):
        self.logger = logger

    def process_request(self, request_dict, logger=utils.get_stdout_logger()):
        # noinspection PyBroadException
        try:
            pass

        except Exception as e:
            logger.error(e)
            logger.error(" # {} processing : Failed".format(self.this_server.acronym))
            # logger.error(traceback.print_exc())
            return None


def main(args):
    this = SysRecommend(ini=utils.get_ini_parameters(args.ini_fname))
    this.logger = utils.setup_logger_with_ini(this.ini['LOGGER'],
                                              logging_=args.logging_, console_=args.console_logging_)
    this.init_logger(logger=this.logger)

    if args.op_mode == 'server':
        this.init_server()

        this.logger.info('proc_offset:{}. listen: {}, {}'.format(args.proc_offset,
                                                                 this.this_server.ip, this.this_server.port))

        sock = utils_socket.get_server_socket(
            this.this_server.ip, this.this_server.port,
            logger=this.logger,
            proc_name=_this_basename_,
            listen_num=5
        )

        while True:
            try:
                ret, _ = utils_socket.handle_command_request(sock, func=this.process_request, logger=this.logger)

                if not ret:
                    break
            except Exception as e:
                this.logger.error(" # handle_command_request.exception : {}".format(e))

                try:
                    sock.close()
                except Exception as ce:
                    this.logger.error(" # close.exception : {}".format(ce))

                sock = utils_socket.get_server_socket(
                    this.this_server.ip, this.this_server.port,
                    logger=this.logger,
                    proc_name=_this_basename_,
                    listen_num=5
                )

        this.logger.info(" # {} in {} mode finished.".format(_this_basename_, args.op_mode))

        return True