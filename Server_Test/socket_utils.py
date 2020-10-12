#! /usr/bin/env python
# -*- coding: utf-8 -*-

import time
import sys
import socket
import json
import psutil
import signal
import traceback

import general_utils as utils


class ServerFeature:
    def __init__(self, ini=None):

        self.name = None
        self.ip = None
        self.port = None
        self.mmap_fname = None
        self.acronym = None

        if ini:
            self.init_ini(ini)

    def init_ini(self, ini):

        self.ip = ini['ip']
        self.port = int(ini['port'])

        try:
            self.name = ini['name']
        except KeyError:
            self.name = ''

        try:
            self.mmap_fname = ini['mmap_fname']
        except KeyError:
            self.mmap_fname = ''

        try:
            self.acronym = ini['acronym']
        except KeyError:
            self.acronym = ''


def get_server_socket(ip, port, logger=utils.get_stdout_logger(), proc_name='', listen_num=5):
    logger.info(" # Getting server socket...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (ip, port)
    # logger.info(server_address)
    # check = check_port(ip, port, logger=logger)
    # logger.info(check)
    # if check:
    if check_port(ip, port):    # , logger=logger):
        logger.info(" # Port, {:d}, was already taken. "
                    "The process using {:d} will be killed first.".format(port, port))
        kill_process(port, name=proc_name)

    logger.info(" # Starting up \"{}\" SERVER on {}:{:d}...".format(proc_name, ip, port))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(server_address)
    sock.listen(listen_num)

    return sock


def check_port(ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # noinspection PyBroadException
        try:
            s.bind((ip, port))
            return False
        except Exception as e:
            print(e)
            return True


def kill_process(port, name="", logger=None):
    for proc in psutil.process_iter():
        try:
            for conns in proc.connections(kind='inet'):
                if conns.laddr.port == port:
                    # noinspection PyBroadException
                    try:
                        proc.send_signal(signal.SIGTERM)
                        proc.send_signal(signal.SIGKILL)
                    except Exception as e:
                        print(e)
                    if logger:
                        logger.info(" > Killed the process {} using {:d} port\n".format(name, port))
                    time.sleep(1)
        except psutil.AccessDenied as ad:
            print(ad)
        except psutil.ZombieProcess as zp:
            print(zp)
        except Exception as e:
            print(e)


def handle_command_request(sock, func=None, response_=True, logger=utils.get_stdout_logger()):
    logger.info('')
    logger.info(' # Waiting for a connection...')

    con, client_address = sock.accept()
    logger.info(" # Connected with {} at {}.".format(client_address, utils.get_datetime()[:-3]))

    ret_ = True
    sent_msg = ''
    dict_dat = {}
    try:
        str_dat = utils.recv_all(con, recv_buf_size=4092, logger=None).decode('utf-8')
        logger.info(" # Received {:d} bytes.".format(len(str_dat)))
        # logger.info(" # Received: \"{}\"".format(str_dat))
        if utils.is_json(str_dat):
            dict_dat = json.loads(str_dat)
            cmd = dict_dat['cmd'].lower()
            if cmd == 'check':
                logger.info(" # Received \"check\" command")
                sent_msg = '{"state":"healthy"}'
            elif cmd == 'stop':
                logger.info(" # Received \"stop\" command")
                sent_msg = '{"state":"Bye"}'
                ret_ = False
            elif cmd == 'run':
                if func:
                    stt_time = time.time()
                    resp = func(dict_dat['request'], logger=logger)
                    proc_time = time.time() - stt_time
                else:
                    resp, proc_time = None, 0
                sent_msg = json.dumps({"state": "Done", "response": resp, "proc_time": proc_time})
            else:
                logger.error(" @ Invalid command, {}.".format(cmd))
                sent_msg = '{"state":"Invalid"}'
        else:
            sent_msg = '{"state":"Not json"}'
    except Exception as e:
        logger.error(str(e) + "\n" + traceback.format_exc())
        sent_msg = '{"state":"' + str(e) + '"}'

    finally:
        if response_:
            con.sendall(sent_msg.encode('utf-8'))
            logger.info(" # Sent: {:d} bytes, {}".format(len(sent_msg), sent_msg))
        con.close()

    return ret_, dict_dat


def send_run_request_and_recv_response(ip, port, request,
                                       show_send_dat_=True,
                                       show_recv_dat_=True,
                                       exit_=False,
                                       desc="",
                                       recv_=True,
                                       logger=utils.get_stdout_logger()):
    send_dat = {"cmd": "run", "request": request}
    ret, recv_dat = socket_client(ip, port, json.dumps(send_dat),
                                  show_send_dat_=show_send_dat_,
                                  show_recv_dat_=show_recv_dat_,
                                  prefix=desc,
                                  recv_=recv_,
                                  logger=logger)

    if not ret:
        logger.error(" @ Error in process request and response method : Socket failed. port={}".format(port))
        if exit_:
            sys.exit(1)
        else:
            return None, None

    if recv_:
        assert(recv_dat is not None)

        try:
            recv_dict = json.loads(recv_dat)
        except Exception as e:
            logger.error("{} @ Error: load json : {}".format(desc, e))
            if exit_:
                sys.exit(1)
            else:
                return None, None

        # if 'response' not in recv_dict:
        #     a = 2
        resp_dict = recv_dict['response']
        proc_time = recv_dict['proc_time']

        if not recv_dict['state'] == "Done":
            logger.error(" @ Error in process request and response method : Response failed. port={}".format(port))
            if exit_:
                sys.exit(1)
            else:
                return None, None

        return resp_dict, proc_time
    else:
        return recv_dat, None


def socket_client_bytes(ip, port, send_dat,
                        logger=utils.get_stdout_logger(),
                        show_send_dat_=False,
                        show_recv_dat_=False,
                        prefix=" #",
                        recv_=True):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (ip, port)

    try:
        if logger:
            logger.info(prefix + " Connecting socket to %s port %s..." % server_address)
        sock.connect(server_address)
    except Exception as e:

        if logger:
            logger.error(e)
        return False, None

    recv_dat = None

    try:

        # sock.sendall(send_dat.encode('utf-8'))
        sock.sendall(send_dat)
        if logger:
            logger.info(prefix + " Sent {} bytes".format(len(send_dat)))
        if show_send_dat_ and logger is not None:
            logger.info(prefix + " Sent data: {}".format(send_dat))

        if recv_:
            recv_dat = utils.recv_all(sock, logger=logger if show_recv_dat_ else None).decode('utf-8')
            if not recv_dat:
                if logger:
                    logger.error(prefix + " failed to received")
                return False, None
            if logger:
                logger.info(prefix + " Received {} bytes".format(len(recv_dat)))
            if show_recv_dat_ and logger is not None:
                logger.info(prefix + " Received data:  {}".format(recv_dat))
        else:
            recv_dat = {'state': "Done"}
    except Exception as e:
        if logger:
            logger.error(e)
        return False, recv_dat
    finally:
        if logger:
            logger.info(prefix + " Closing socket.")
        sock.close()
        return True, recv_dat


def socket_client(ip, port, send_dat,
                  logger=utils.get_stdout_logger(),
                  show_send_dat_=False,
                  show_recv_dat_=False,
                  prefix=" #",
                  recv_=True):
    return socket_client_bytes(ip, port, send_dat.encode('utf-8'),
                               logger=logger,
                               show_send_dat_=show_send_dat_,
                               show_recv_dat_=show_recv_dat_,
                               prefix=prefix,
                               recv_=recv_)
