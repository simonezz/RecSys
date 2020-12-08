import argparse
import socket
import sys
import threading

import put_server


def handle_client(client_list, conn, address):
    # json은 key가 string이여야하고, conn.sendall은 바이트형식으로 보내야해서 형식 변환 과정이 있음.

    date_time = conn.recv(1024)  # 문제 ID 받음

    # date_time이후의 문제들을 elasticsearch에 넣음
    put_server.put_data(date_time.decode('utf-8'))
    conn.shutdown(socket.SHUT_RDWR)
    conn.close()


def server(client_list):
    print("Starting server...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((socket.gethostname(), 5001))
    s.listen(5)
    while True:
        (conn, address) = s.accept()
        t = threading.Thread(target=handle_client, args=(client_list, conn, address))
        t.daemon = True
        t.start()


def client(date_time):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((socket.gethostname(), 5001))
    s.send(date_time.encode())


def parse_arguments(argv):
    parser = argparse.ArgumentParser()
    # parser.add_argument('-c', dest='client', action='store_true')
    # parser.add_argument('-d', dest='date_time', type=str)
    parser.add_argument("--mode", default=False, choices=['client', 'server'])
    parser.add_argument("--datetime", required=True)

    args = parser.parse_args(argv)

    return args


def main(args):
    client_list = dict()
    # args = parse_arguments()
    if args.mode == "client":
        client(args.datetime)
    else:
        try:
            server(client_list)
        except KeyboardInterrupt:
            print("Keyboard interrupt")


SELF_TEST_ = True
SERVER_MODE = "client"
DATETIME = "20201123"

if __name__ == '__main__':
    if len(sys.argv) == 1:
        if SELF_TEST_:
            sys.argv.extend(["--mode", SERVER_MODE])
            sys.argv.extend(["--datetime", DATETIME])
        else:
            print("INPUTS NEEDED")
    main(parse_arguments(sys.argv[1:]))
