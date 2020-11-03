import argparse
import json
import socket
import threading

import twins_get_server


def handle_client(client_list, conn, address):
    # json은 key가 string이여야하고, conn.sendall은 바이트형식으로 보내야해서 형식 변환 과정이 있음.

    recv = conn.recv(1024).decode('utf-8')  # 문제 ID 받음

    book_prob_id, start, end = map(int, recv.split('/'))

    prob_id, sim_list = twins_get_server.find_similar_pb(book_prob_id)

    entry = dict(zip(['book_prob_id', 'prob_id', 'address', 'port', 'totalCount', 'IDList'],
                     [book_prob_id, prob_id, address[0], address[1], len(sim_list), sim_list[start:end + 1]]))
    client_list[book_prob_id] = entry

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


def client(book_prob_id, start, end):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((socket.gethostname(), 5000))
    s.send((book_prob_id + '/' + start + '/' + end).encode())
    data = s.recv(1024)
    result = json.loads(data)
    print(json.dumps(result, indent=4))


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest='client', action='store_true')
    parser.add_argument('-bi', dest='book_prob_id', type=str)
    parser.add_argument('-s', dest='start', type=str)  # 몇번째 순위부터 가져올건지
    parser.add_argument('-e', dest='end', type=str)  # 몇번째 순위까지 가져올건지
    result = parser.parse_args()
    return result


def main():
    client_list = dict()
    args = parse_arguments()
    if args.client:
        client(args.book_prob_id, args.start, args.end)
    else:
        try:
            server(client_list)
        except KeyboardInterrupt:
            print("Keyboard interrupt")


if __name__ == '__main__':
    main()
