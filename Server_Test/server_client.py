import argparse
import json
import socket
import threading

import Get_server


def handle_client(client_list, conn, address):
    #json은 key가 string이여야하고, conn.sendall은 바이트형식으로 보내야해서 형식 변환 과정이 있음.

    ID = conn.recv(1024)#문제 ID 받음
    # print(ID)
    sim_list = Get_server.find_similar_pb(ID.decode('utf-8'))

    entry = dict(zip(['ID', 'address', 'port', 'IDList'], [ID.decode('utf-8'), address[0], address[1], sim_list]))
    client_list[ID.decode('utf-8')] = entry
    # print(client_list)
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

def client(ID):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 5000))
    s.send(ID.encode())
    data = s.recv(1024)
    result = json.loads(data)
    print(json.dumps(result, indent=4))

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest='client', action='store_true')
    parser.add_argument('-id', dest='ID', type=str)
    result = parser.parse_args()
    return result

def main():
    client_list = dict()
    args = parse_arguments()
    if args.client:
        client(args.ID)
    else:
        try:
            server(client_list)
        except KeyboardInterrupt:
            print("Keyboard interrupt")

if __name__ == '__main__':
    main()