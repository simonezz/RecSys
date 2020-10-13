import argparse
import json
import socket
import threading

import get_server


def handle_client(client_list, conn, address):
    # json은 key가 string이여야하고, conn.sendall은 바이트형식으로 보내야해서 형식 변환 과정이 있음.

    recv = conn.recv(1024).decode('utf-8')  # 문제 ID 받음

    ID, start, end = map(int, recv.split('/'))

    sim_list = get_server.find_similar_pb(ID)[start:end + 1]

    entry = dict(zip(['ID', 'address', 'port', 'IDList'], [ID, address[0], address[1], sim_list]))
    client_list[ID] = entry

    conn.sendall(bytes(json.dumps(client_list), encoding='utf-8'))
    conn.shutdown(socket.SHUT_RDWR)
    conn.close()

def server(client_list):
    print("Starting server...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((socket.gethostname(), 5000))
    s.listen(5)
    while True:
        (conn, address) = s.accept()
        t = threading.Thread(target=handle_client, args=(client_list, conn, address))
        t.daemon = True
        t.start()


def client(ID, start, end):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((socket.gethostname(), 5000))
    s.send((ID + '/' + start + '/' + end).encode())
    data = s.recv(1024)
    result = json.loads(data)
    print(json.dumps(result, indent=4))

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest='client', action='store_true')
    parser.add_argument('-id', dest='ID', type=str)
    parser.add_argument('-s', dest='start', type=str)  # 몇번째 순위부터 가져올건지
    parser.add_argument('-e', dest='end', type=str)  # 몇번째 순위까지 가져올건지
    result = parser.parse_args()
    return result

def main():
    client_list = dict()
    args = parse_arguments()
    if args.client:
        client(args.ID, args.start, args.end)
    else:
        try:
            server(client_list)
        except KeyboardInterrupt:
            print("Keyboard interrupt")

if __name__ == '__main__':
    main()