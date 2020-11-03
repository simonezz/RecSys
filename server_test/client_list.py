import argparse
import json
import socket
import threading

def handle_client(client_list, conn, address):
    #json은 key가 string이여야하고, conn.sendall은 바이트형식으로 보내야해서 형식 변환 과정이 있음.

    name = conn.recv(1024)
    # print(name)
    entry = dict(zip(['name', 'address', 'port'], [name.decode('utf-8'), address[0], address[1]]))
    client_list[name.decode('utf-8')] = entry
    # print(client_list)
    conn.sendall(bytes(json.dumps(client_list), encoding='utf-8'))
    conn.shutdown(socket.SHUT_RDWR)
    conn.close()

def server(client_list):
    print("Starting server...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('127.0.0.1', 5000))
    s.listen(5)
    while True:
        (conn, address) = s.accept()
        t = threading.Thread(target=handle_client, args=(client_list, conn, address))
        t.daemon = True
        t.start()

def client(name):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 5000))
    s.send(name.encode())
    data = s.recv(1024)
    result = json.loads(data)
    print(json.dumps(result, indent=4))

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest='client', action='store_true')
    parser.add_argument('-n', dest='name', type=str, default='name')
    result = parser.parse_args()
    return result

def main():
    client_list = dict()
    args = parse_arguments()
    if args.client:
        client(args.name)
    else:
        try:
            server(client_list)
        except KeyboardInterrupt:
            print("Keyboard interrupt")

if __name__ == '__main__':
    main()