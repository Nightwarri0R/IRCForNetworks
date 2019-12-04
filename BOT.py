import sys
import socket
import string
import datetime

# IP Address of Local Host
HOST = "127.0.0.1"

# IP Address for the Virtual Machine:
# HOST = " 10.0.42.17"

# default Connection Port
PORT = 6667

# nickname of the Bot
NICK = "ProBot"

# username of the Bot
USERNAME = "ProBotUserName"

# real Name of the bot
REALNAME = "RealBot"

# buffer for the messages sent to the channel that the bot is connected to
readbuffer = ""

# channel #test that the bot will automatically connect to once it starts running
CHANNEL = "#test"

# socket that the bot will use to communicate to the server
botSocket = socket.socket()

# connection to the server
botSocket.connect((HOST, PORT))

# bot sends automatically the username and the real name of the Bot to the server
botSocket.send(bytes("USER " + USERNAME + " " + USERNAME + " " + USERNAME + " :" + REALNAME + "\r\n", "UTF-8"))

# bot sends automatically the nickname of the Bot to the server
botSocket.send(bytes("NICK " + NICK + "\r\n", "UTF-8"))

# bot automatically joins the channel set in advance, on the server
botSocket.send(bytes("JOIN %s" % (CHANNEL) + "\r\n", "UTF-8"))

# while loop used to run the bot indefinitely until the bot is stopped
while 1:

    # buffer that stores the messages from the channel
    readbuffer = readbuffer + botSocket.recv(1024).decode("UTF-8")
    # variable to store and split the messages from the buffer
    temp = str.split(readbuffer, "\n")
    # popping from the temp variable
    readbuffer = temp.pop()
    # for loop to iterate through the different lines in temp
    for line in temp:
        # striping the line
        line = str.rstrip(line)
        # splitting the line
        line = str.split(line)
        # checking if a private message is being sent to the bot
        if (line[1] == "PRIVMSG"):
            # variable to store the sender of the private message
            sender = ""
            # iterating through every character in the first element of the line array
            for char in line[0]:
                # break if an exclamation sign is found in the first element of the line array
                if (char == "!"):
                    break
                # checking if there is any colon, set the sender to the character
                if (char != ":"):
                    sender += char
            # if any user inputs !day the bot will send the date in a day/month/year format back to the channel and #
            # on a private message to the user that asked for it
            if line[3] == ":!day":
                date = datetime.datetime.now()
                message = date.strftime("%d/%m/%Y")
                botSocket.send(bytes("PRIVMSG %s %s" % (CHANNEL, message) + "\r\n", "UTF-8"))
                botSocket.send(bytes("PRIVMSG %s %s" % (sender, message) + "\r\n", "UTF-8"))
            # if any user inputs !time the bot will send the time in a hour/minute/second format back to the channel #
            # and on a private message to the user that asked for it
            elif line[3] == ":!time":
                time = datetime.datetime.now()
                message = time.strftime("%H:%M:%S")
                botSocket.send(bytes("PRIVMSG %s %s" % (CHANNEL, message) + "\r\n", "UTF-8"))
                botSocket.send(bytes("PRIVMSG %s %s" % (sender, message) + "\r\n", "UTF-8"))
            # if the user sends anything else to the bot that is not !day or !time, the user will receive a #
            # personalised private message
            else:
                import random
                # random number used to choose which random fact it will be displayed
                number = random.randint(1, 6)
                # function that displays a random fact depending on a number i, it works using a switcher
                def fact(i):
                    # switcher used to choose the random fact
                    switcher = {
                        1: 'Did you know that most toilets flush in E flat?',
                        2: 'Did you know that sloths can held breath longer than dolphins can?',
                        3: 'Did you know that Scotland has 421 words for "snow"?',
                        4: 'Did you know octopuses have three hearts?',
                        5: 'Did you know that Empire State Building has its own post code?',
                        6: 'Did you know that the Eiffel Tower was originally intended for Barcelona?'
                    }
                    return switcher.get(i, "Not valid number")
                # Random fact that will be displayed to the user
                fact = fact(number)
                # Displaying the random fact to the user
                botSocket.send(bytes("PRIVMSG %s :%s" % (sender, fact) + "\r\n", "UTF-8"))
