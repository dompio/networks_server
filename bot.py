# IRC bot - a simple client connecting to a server and replying to messages
#
# Created as part of the AC31008 Networks module at the University of Dundee, November 2019
#config file
#
# Group members: Dominika Piosik, Justas Samoulis, Ben Hawke

from datetime import date
from datetime import datetime
import socket
import random

# Variables
botnick = "ProBot"
server_ip = 'localhost' #set to 10.0.42.17 or 'localhost' for testing
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
    print('PONG')
    
# Receive and respond to messages
def respond():
    while 1:
        # Listen for messages
        message = ircbot.recv(2048).decode("UTF-8")
    
        # Print message in console
        print(message)
    
        # Respond to user commands
        # if message.find("PRIVMSG") != -1:  and then split???
        if message.find('PING :') != -1:
            ping()
    
        elif message.find('!day') != -1:
            today = date.today()
            # Respond with month day, year
            this_day = today.strftime("%B %d, %Y")
            ircbot.send(bytes("PRIVMSG "+ channel +" :"+ "Today is " + this_day +"\n", "UTF-8"))
        
        elif message.find('!time') != -1:
            now = datetime.now()
            # Respond with hh:mm:ss
            current_time = now.strftime("%H:%M:%S")
            ircbot.send(bytes("PRIVMSG "+ channel +" :"+ "Current time " + current_time +"\n", "UTF-8"))
        
        elif message == exitcode:
            ircbot.send(bytes("PRIVMSG "+ channel +" :"+ "Exiting..." +"\n", "UTF-8"))
            ircbot.send(bytes("QUIT n", "UTF-8"))
        
        elif message.find('PRIVMSG Probot'):
            #Respond to private messages with fun facts
            # Define the fun facts
            random_facts = [
                "a bolt of lightning contains enough energy to toast 100,000 slices of bread.",
                "you can hear a blue whale's heartbeat from two miles away.",
                "nearly 30,000 rubber ducks were lost a sea in 1992 and are still being discovered today."
                ]
            
            # Extract user nickname
            nick = message[message.find(':')+len(":"):message.rfind('!')]
            
            # Reply with a fun fact
            ircbot.send(bytes("PRIVMSG "+ nick + " Did you know that " + random_facts[random.randint(0,2)] + "\n", "UTF-8"))
    

# Run the bot
connect()
register()
join()
respond()
        





