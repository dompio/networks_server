# IRC bot - a simple client connecting to a server and replying to messages
#
# Created as part of the AC31008 Networks module at the University of Dundee, November 2019
#config file
#
# Group members: Dominika Piosik, Justas Samoulis, Ben Hawke

from datetime import date
from datetime import datetime
import socket

# Variables
botnick = "ProBot"
server_ip = '10.0.42.17'
port = 6667
server_address = (server_ip, port)
channel = "#test"
exitcode = "exit"

# Create a TCP socket
ircbot = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Establish socket connection to the port
def connect():
    ircbot.connect(server_address)

# Register the bot
def register():
    ircbot.send(bytes("USER" + botnick + "networksbot server" + botnick + "\n", "UTF-8"))
    ircbot.send(bytes("NICK "+ botnick +"\n", "UTF-8"))

# Join channel
def join():
    ircbot.send(bytes("JOIN "+ channel +"\n", "UTF-8"))

# Respond to PINGs
def ping(): 
    ircbot.send(bytes("PONG :pingisn", "UTF-8"))

# Run the bot
connect()
register()
join()
while 1:
    message = ircbot.recv(2048).decode("UTF-8")
    print(message)
    # if message.find("PRIVMSG") != -1:  and then split???
    if message == exitcode:
        ircbot.send(bytes("PRIVMSG "+ channel +" :"+ "Exiting..." +"\n", "UTF-8"))
        ircbot.send(bytes("QUIT n", "UTF-8"))
    
    if message.find('!day') != -1:
        today = date.today()
        # Full month day, year
        this_day = today.strftime("%B %d, %Y")
        ircbot.send(bytes("PRIVMSG "+ channel +" :"+ "Today is " + this_day +"\n", "UTF-8"))
        
    if message.find('!time') != -1:
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        ircbot.send(bytes("PRIVMSG "+ channel +" :"+ "Current time " + current_time +"\n", "UTF-8"))





