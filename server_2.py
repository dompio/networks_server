import socket
import select
import sys

clients = set()
channels = set()
address = '127.0.0.1'
port = 6667
CLRF = '\r\n'


# parse message as per https://tools.ietf.org/html/rfc2812#section-2.3.1
def parse_msg(msg: str):
    prefix = ''
    command = ''
    params = []

    if msg[0] == ':':
        # has prefix
        prefix, msg = msg[1:].split(' ', 1)
    command, msg = msg.split(' ', 1)
    if msg.find(' :') != -1:
        msg, trail = msg.split(' :', 1)
        params.append(trail)
    params = [*msg.split(' '), *params]
    return prefix, command, params


def socket_read(sock: socket.socket):
    try:
        data = [*sock.recv(2 ** 10).decode().split(CLRF)]

        for d in data:
            if d == '':
                continue
            (prefix, cmd, params) = parse_msg(d)

        return True
    except Exception:
        return False


server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    server_sock.bind((address, port))
except socket.error as e:
    print('Error occured while binding %s:%s - %s' % (address, port, e))
    sys.exit(1)

server_sock.listen()
print('Listening on port %d...' % port)

while True:
    (ready_read, ready_write, _) = select.select(
        [server_sock, *clients], clients, [], 10)

    for sock in ready_read:
        if sock in clients:
            print('In clients, wants to read')
            ok = socket_read(sock)
            if not ok:
                clients.remove(sock)
        else:
            (conn, addr) = sock.accept()

            try:
                clients.add(conn)
                print('Accepted connection from %s:%s' % (addr[0], addr[1]))
            except socket.error as e:
                print('Error accepting %s:%s - %s' % (addr[0], addr[1], e))
                try:
                    conn.close()
                except Exception:
                    pass
