import socket
import select
import sys

# There is no need to implement a full IRC server to understand how sockets works on the server
# side, thus it should only provide the functionalities of the protocol which are strictly required
# to achieve the following task:
# • Allowing clients to connect, choosing there username and realname
# • Allowing clients to join channels
# • Allowing clients to talk to others users in a channel
# • Allowing clients to talk directly to each other in private

CLRF = '\r\n'
ADDRESS = '127.0.0.1'
PORT = 6667
VERSION = 'MyIrc-1.0'
CREATED_AT = 'sometime'


class Server:

    def __init__(self):
        self.clients = {}  # socket -> Client
        self.channels = {}  # name -> Channel
        self.nicknames = {}  # nickname -> Client
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # get server name of up to 63 (RFC) length
        self.name = socket.getfqdn(ADDRESS)[:63]

    def run(self):
        try:
            self.s.bind((ADDRESS, PORT))
        except socket.error as e:
            print('Error occured while binding %s:%s - %s' %
                  (ADDRESS, PORT, e))
            sys.exit(1)

        self.s.listen()
        print('Listening on port %d...' % PORT)

        while True:
            client_sockets = self.clients.keys()
            (ready_read, ready_write, _) = select.select(
                [self.s, *client_sockets], client_sockets, [], 10)

            for sock in ready_read:
                if sock in self.clients:
                    ok = self.clients[sock].read()
                    if not ok:
                        self.clients.pop(sock)
                else:
                    (conn, addr) = sock.accept()

                    try:
                        newClient = Client(self, conn)
                        self.clients[conn] = newClient
                        print('Accepted connection from %s:%s' %
                              (addr[0], addr[1]))
                    except socket.error as e:
                        print('Error accepting %s:%s - %s' %
                              (addr[0], addr[1], e))
                        try:
                            conn.close()
                        except Exception:
                            pass
            for sock in ready_write:
                if sock in self.clients:
                    self.clients[sock].send()


class Channel:

    def __init__(self, server: Server, name: str):
        self.server = server
        self.name = name
        self.members = set()


class Client:

    def __init__(self, server: Server, socket: socket.socket):
        self.server = server
        self.socket = socket
        self.nickname = None
        self.user = None
        self.realname = None
        (self.host, self.port) = socket.getpeername()
        self.channels = {}
        self.sendmsg = ''

    def get_prefix(self):
        return '%s!%s@%s' % (self.nickname, self.user, self.host)

    def parse_msg(self, msg: str):
        prefix = ''
        command = ''
        params = []

        if msg[0] == ':':
            prefix, msg = msg[1:].split(' ', 1)
        command, msg = msg.split(' ', 1)
        if msg.find(' :') != -1:
            msg, trail = msg.split(' :', 1)
            params.append(trail)
        params = [*msg.split(' '), *params]
        return prefix, command, params

    def read(self):
        try:

            data = [*self.socket.recv(2 ** 10).decode().split(CLRF)]

            for d in data:
                if d == '':
                    continue
                (prefix, cmd, params) = self.parse_msg(d)

                if cmd == 'NICK':
                    self.handleNICK(params)
                elif cmd == 'USER':
                    self.handleUSER(params)
                elif cmd == 'QUIT':
                    self.handleQUIT(params)
                print(prefix, cmd, params)

            return True

        except Exception as e:
            print(e)
            return False

    def msg_code_nick(self, code: str, message: str):
        message = ':%s %s %s :%s' % (
            self.server.name, code, self.nickname, message)
        print(message)
        self.sendmsg += (message)

    def reply(self, msg, notSelf=False):
        text = ':%s %s' % (self.server.name, msg)
        if len(self.channels) > 0:
            for c in self.channels:
                for m in self.server.channels[c].members:
                    if notSelf and m is self:
                        continue
                    m.socket.send(text)
        else:
            self.sendmsg += (text)

    #   Parameters: <nickname> [ <hopcount> ]
    def handleNICK(self, params: list):
        nickname = params[0]
        # if nickname already exists for some other user
        if nickname in self.server.nicknames:
            if self.server.nicknames[nickname] is not self:
                print('Nick collision & not self')
                return
            else:
                # Changed nickname
                self.server.nicknames.pop(self.nickname)
                self.sendmsg += (
                    (':%s NICK %s' % (self.get_prefix(), nickname)))
        self.server.nicknames[nickname] = self
        self.nickname = nickname

    #   Parameters: <username> <hostname> <servername> <realname>
    def handleUSER(self, params: list):
        if len(params) < 4:
            # ERR_NEEDMOREPARAMS
            self.sendmsg += (
                (':%s 461 USER :Not enough parameters' % self.server.name))
            return
        # New user; send greeting
        self.user = params[0]
        self.realname = params[3]
        self.greet()

    def handleQUIT(self, params):
        self.server.nicknames.pop(self.nickname)
        self.server.clients.pop(self.socket)

    def greet(self):
        self.msg_code_nick(
            '001', 'Welcome to the Internet Relay Network %s' % self.get_prefix())
        self.msg_code_nick('002', 'Your host is %s, running version %s' % (
            self.server.name, VERSION))
        self.msg_code_nick('003', 'This server was created %s' % CREATED_AT)
        self.msg_code_nick('004', '%s %s 0 0' % (self.server.name, VERSION))

    def send(self):
        if self.sendmsg:
            try:
                self.socket.send(self.sendmsg.encode())
                self.sendmsg = ''
            except socket.error as e:
                print(e)


# :samuo1!~samuo@92.238.3.145 NICK :samuo2
# nick!user@userhost


srv = Server()
srv.run()
