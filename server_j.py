import socket
import select

class Server:

    # example client creation: clients[conn] = Client(self, conn)
    def __init__(self):
        self.address = '127.0.0.1'
        self.port = 6667
        self.channels = {}  # channel name -> Channel
        self.clients = {}   # socket -> Client
        self.nicknames = {}  # nickname -> Client
        print('IRCServer instance created.')

    # given nickname find Client instance
    def locate_client(self, nickname):
        return self.nicknames.get(nickname)

    # given channel name find/create and return Channel instance
    def locate_channel(self, channelname):
        if channelname in self.channels:
            channel = self.channels[channelname]
        else:
            channel = Channel(self, channelname)
            self.channels[channelname] = channel
        return channel

    def relayMessage(self, message, recipient):
        # relay message to recipient
        pass

    def run(self):
        # get and handle connections
        # every n miliseconds for each client send its messagebuffer (if not empty)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            s.bind((self.address, self.port))
        except socket.error as e:
            print('Error occured while binding %s:%s - %s' % (self.address, self.port, e))
            # exit (sys.exit?)
        s.listen()
        print('Listening on port %d...' % self.port)

        while True:
            client_sockets = [x.socket for x in self.clients.values()]
            (rread, rwrite, rexc) = select.select([s, *client_sockets], client_sockets, [], 10)

            for sock in rread:
                if sock in self.clients:
                    print('already in clients, wants to read')
                    self.clients[sock].recv_data()
                else:
                    (conn, addr) = sock.accept()

                    try:
                        self.clients[conn] = Client(self, conn)
                        print('Accepted connection from %s:%s.' % (addr[0], addr[1]))
                    except socket.error as e:
                        print('Error accepting %s:%s - %s' % (addr[0], addr[1], e))
                        try:
                            conn.close()
                        except Exception:
                            pass

class Channel:

    def __init__(self, server: Server, name: str):
        self.server = server
        self.name = name
        self.members = set()


class Client:

    def __init__(self, server: Server, socket: socket.socket):
        self.server = server
        self.socket = socket
        self.channels = {}
        self.nickname = None
        self.prefix = None  # just nickname or nickname + host from sockets?
        self.messagebuffer = None # buffer to send every server refresh

    def message_channel(self, channel: Channel, message: str):
        msg = ':%s %s' % (self.prefix, message)
        for client in channel.members:
            # dont send a message to self
            if client is not self:
                client.message(msg)

    def message(self, message: str):
        self.messagebuffer += message.encode()

    def recv_data(self):
        data = self.socket.recv(2 ** 10).decode()
        print(data)
        # parse data here
        # perform actions based on command

    


srv = Server()
srv.run()