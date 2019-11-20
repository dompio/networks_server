# IRC bot - a simple client connecting to a server and replying to messages
#
# Created as part of the AC31008 Networks module at the University of Dundee, November 2019
#
# Group members: Dominika Piosik, Justas Samoulis, Ben Hawke

import sys
import time
import socket

# Variables
botnick = 'awesomebot'
# allow the user to type the server ip
server_ip = "irc.freenode.net"
port = 6667
server_address = (server_ip, port)
channel = "##test"
exitcode = "exit"

# Create a TCP socket
ircbot = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Establish socket connection to the port
ircbot.connect(server_address)
ircbot.send(bytes("USER "+ botnick +" "+ botnick +" "+ botnick + " " + botnick + "n", "UTF-8"))
ircbot.send(bytes("NICK "+ botnick +"n", "UTF-8"))

# Join channel
# Do we need the UTF-8 encoding
ircbot.send(bytes("JOIN "+ chan +"n", "UTF-8"))

while 1:
    message = ircbot.recv(2048).decode("UTF-8")
    print(message)
    # if message.find("PRIVMSG") != -1:  and then split???
    if message == exitcode:
        sendmsg("Exiting...")
        ircbot.send(bytes("QUIT n", "UTF-8"))
        return





