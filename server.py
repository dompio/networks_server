import socket
import select
import sys


# Some constants
CLRF = '\r\n'
ADDRESS = '127.0.0.1'
PORT = 6667
VERSION = 'MyIrc-1.0'
CREATED_AT = 'sometime'

# Server class responsible for spawning and handling socket connections
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
            # Get sockets which are ready to read/write data
            (ready_read, ready_write, _) = select.select(
                [self.s, *client_sockets], client_sockets, [], 10)

            for sock in ready_read:
                if sock in self.clients:
                    # Read data, if unsucessful remove socket from the client list
                    ok = self.clients[sock].read()
                    if not ok:
                        self.clients.pop(sock)
                else:
                    # Socket is not in the clients, accept the connection and create a new client
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
                # Socket is ready to write, write message if it has one
                if sock in self.clients:
                    self.clients[sock].send()


# Simple Channel class which stores channel name and members
# Could use dict instead but class allows for easier future extensions
class Channel:

    def __init__(self, name: str):
        self.name = name
        self.members = set()

# Client class responsible for communicating with irc clients using sockets
class Client:

    def __init__(self, server: Server, socket: socket.socket):
        self.server = server
        self.socket = socket
        self.nickname = None
        self.user = None
        self.realname = None
        (self.host, self.port) = socket.getpeername()
        self.channels = set()
        self._sendmsg = ''
        self.greeted = False

    # Property allows to set a getter/setter
    # Which is helpful since you dont have to manually add CRLF breaks 
    @property
    def sendmsg(self):
        return self._sendmsg

    @sendmsg.setter
    def sendmsg(self, val):
        if val != '':
            self._sendmsg = val + CLRF
        else:
            self._sendmsg = val

    @sendmsg.deleter
    def sendmsg(self):
        del self._sendmsg

    def get_prefix(self):
        return '%s!%s@%s' % (self.nickname, self.user, self.host)

    # Parses message and returns prefix (empty if none), command and parameters (arguments)
    def parse_msg(self, msg: str):
        prefix = ''
        command = ''
        params = []

        if len(msg.split(' ')) == 1:
            return '', msg, []
        if msg[0] == ':':
            prefix, msg = msg[1:].split(' ', 1)
        command, msg = msg.split(' ', 1)
        if msg.find(' :') != -1:
            msg, trail = msg.split(' :', 1)
            params.append(trail)
        params = [*msg.split(' '), *params]
        return prefix, command, params

    # Reads data and runs command if we have a handler for it
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
                elif cmd == 'PING':
                    self.handlePING(params)
                elif cmd == 'JOIN':
                    self.handleJOIN(params)
                elif cmd == 'PRIVMSG':
                    self.handlePRIVMSG(params)
                elif cmd == 'PART':
                    self.handlePART(params)
                # print(prefix, cmd, params)

            return True

        except Exception as e:
            print(e)
            return False

    # Adds a message for socket to send when ready
    def msg_code_nick(self, code: str, message: str):
        if self.nickname == None:
            nick = '*'
        else:
            nick = self.nickname
        message = ':%s %s %s %s' % (
            self.server.name, code, nick, message)
        self.sendmsg += (message)

    # Adds an more params error message for socket to send
    def errNeedMoreParams(self, cmd: str):
        self.sendmsg += ':%s %s :Not enough parameters' % (
            self.server.name, cmd)

    #   params: <nickname> [ <hopcount> ]
    def handleNICK(self, params: list):
        if len(params) == 0:
            self.msg_code_nick('431', ':No nickname given')
        nickname = params[0]
        # if nickname already exists for some other user
        if nickname in self.server.nicknames:
            if self.server.nicknames[nickname] is not self:
                self.msg_code_nick(
                    '433', '%s :Nickname is already in use' % nickname)
                return
        elif self.nickname and self.nickname != nickname:
                # Changed nickname
            self.server.nicknames.pop(self.nickname)
            self.sendmsg += (
                (':%s NICK %s' % (self.get_prefix(), nickname)))
        self.server.nicknames[nickname] = self
        self.nickname = nickname
        if not self.greeted:
            self.greet()

    #   params: <username> <hostname> <servername> <realname>
    def handleUSER(self, params: list):
        if len(params) < 4:
            # ERR_NEEDMOREPARAMS
            self.errNeedMoreParams('USER')
            return
        elif self.user and self.realname:
            self.msg_code_nick(
                '462', ':Unauthorized command (already registered)')
            return
        # New user; send greeting
        self.user = params[0]
        self.realname = params[3]
        if self.user and self.nickname:
            self.greet()

    # Client has left, remove it from our data structures and close socket
    def handleQUIT(self, params):
        self.server.nicknames.pop(self.nickname)
        self.server.clients.pop(self.socket)
        self.socket.close()

    # Respond to PING commands
    def handlePING(self, params):
        self.sendmsg += ':%s PONG %s :%s' % (self.server.name,
                                             self.server.name, params[0])

    def handleJOIN(self, params):
        if len(params) == 0:
            self.errNeedMoreParams('JOIN')
            return
        if len(params) == 2:
            keys = params[1].split(',')
        channels = params[0].split(',')
        # password handling not needed here
        for c in channels:
            if c[0].isalnum():
                self.msg_code_nick('476', '%s :Bad Channel Mask' % c)
                return
            if c not in self.channels:
                if c in self.server.channels:
                    self.server.channels[c].members.add(self)
                else:
                    # create channel
                    chn = Channel(c)
                    chn.members.add(self)
                    self.server.channels[c] = chn
                self.channels.add(c)
                self.sendmsg += ':%s JOIN %s' % (self.get_prefix(), c)

    def handlePRIVMSG(self, params):
        if len(params) == 0:
            # ERR_NORECIPIENT
            self.msg_code_nick('411', ':No recipient given (PRIVMSG)')
            return
        if len(params) == 1:
            # ERR_NOTEXTTOSEND
            self.msg_code_nick('412', ':No text to send')
            return
        if len(params) != 2:
            return

        target, text = params

        if target in self.channels:
            self.msg_channel(self.server.channels[target], text)
        elif target in self.server.nicknames:
            self.server.nicknames[target].sendmsg += ':%s PRIVMSG %s :%s' % (
                self.get_prefix(), target, text)
        else:
            self.msg_code_nick('401', '%s :No such nick/channel' % target)

    def handlePART(self, params):
        if len(params) == 0:
            self.errNeedMoreParams('PART')
            return
        channels, message = params
        for c in channels.split(','):
            if c not in self.server.channels:
                self.msg_code_nick('403', '%s :No such channel' % c)
                return
            if c not in self.channels:
                self.msg_code_nick(
                    '442', '%s :You\'re not on that channel' % c)
                return
            self.msg_channel(
                self.server.channels[c], message, cmd='PART', andSelf=True)
            self.channels.remove(c)
            self.server.channels[c].members.remove(self)
            if len(self.server.channels[c].members) == 0:
                self.server.channels.pop(c)

    def msg_channel(self, channel: Channel, msg: str, cmd='PRIVMSG', andSelf=False):
        for member in channel.members:
            if member != self or andSelf:
                member.sendmsg += ':%s %s %s :%s' % (
                    self.get_prefix(), cmd, channel.name, msg)

    def greet(self):
        self.msg_code_nick(
            '001', ':Welcome to the Internet Relay Network %s' % self.get_prefix())
        self.msg_code_nick('002', ':Your host is %s, running version %s' % (
            self.server.name, VERSION))
        self.msg_code_nick('003', ':This server was created %s' % CREATED_AT)
        self.msg_code_nick('004', ':%s %s 0 0' % (self.server.name, VERSION))
        self.greeted = True

    def send(self):
        if self.sendmsg:
            try:
                self.socket.send(self.sendmsg.encode())
                self.sendmsg = ''
            except socket.error as e:
                print(e)


srv = Server()
srv.run()
