import socket

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
            client.message(msg)

    def message(self, message: str):
        self.writebuffer += message.encode()


class Server:

    # example client creation: clients[conn] = Client(self, conn)
    def __init__(self):
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
        # every n miliseconds for each client send its writebuffer (if not empty)
        pass
