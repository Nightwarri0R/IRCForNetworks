#!/usr/bin/python
import re
from datetime import datetime
import socket
import select
import errno
import sys
import time
import argparse
# python .\miniircd --debug 
# dictionary[new_key] = new_thing_in_dictionary

# Client class in the server side is purposed to deal with users and user input, whenever they are connected to the server
class Client(object):

    linesep_regexp = re.compile(r"\r?\n")
    valid_channelname_regexp = re.compile(r"^[&#+!][^\x00\x07\x0a\x0d ,:]{0,50}$")
    
    # Constructor for the Client class, where required variables are initialised for later use in the class itself
    def __init__(self, server, client_socket):
        self.socket = client_socket
        self.server = server
        self.channels = {}
        self.host, self.port = client_socket.getpeername()
        self.hostname = socket.getfqdn(self.host)
        self.rec_buffer = ""
        self.write_buffer = ""
        self.nickname = ""
        self.realname = ""
        self.user = ""
        self.handle_command = self.registration_handler
        self.registered = False
    
    """
    This function takes user input and separates it with the help of built in regular expression, as well as checks for errors such 
    as if the user input is an empty string. If not it carries on to search for space and splits from there. 
    Once that is done the command_handler function is called to check if the given command exists.
    """
    def parse_read_buffer(self):
        lines = self.linesep_regexp.split(self.rec_buffer)
        self.rec_buffer = lines[-1]
        lines = lines[:-1]
        for line in lines:
            print(line)
            if not line:
                # Empty line. Ignore.
                continue
            x = line.split(" ", 1)
            command = x[0].upper()
            if len(x) == 1:
                arguments = []
            else:
                if len(x[1]) > 0 and x[1][0] == ":":
                    arguments = [x[1][1:]]
                else:
                    y = x[1].split(" :", 1)
                    arguments = y[0].split()
                    if len(y) == 2:
                        arguments.append(y[1])
            if(self.registered):
                self.command_handler(command, arguments)
            else:
                self.registration_handler(command, arguments)

    """
    Takes self parameter, reads the socket from the user and gets the information.
    That information is then sent to parse function.
    """
    def socket_readable(self):
        data = ""
        data = self.socket.recv(1024)
        self.rec_buffer += data.decode()
        self.parse_read_buffer()

    """
    Takes self paramater and writes encoded data from send(socket) to local variable that is then passed to 
    write_buffer(socket), which has the information where to send this data.
    """
    def socket_write(self):
        amountBuffer = self.socket.send(self.write_buffer.encode())
        self.write_buffer = self.write_buffer[amountBuffer:]

    """
    After all the parsing has been performed the registration_handler checks if it does contain any of the given
    user commands. If it does it calls the respective function.
    """
    def registration_handler(self, command, arguments):
        server = self.server
        if command == "NICK":
            if len(arguments) < 1:
                self.reply("431 :No nickname given")
                return
            nick = arguments[0]
            if server.get_client(nick):
                self.reply("433 * %s :Nickname is already in use" % nick)
            else:
                self.nickname = nick
                server.client_changed_nickname(self, None)
                print("nickname set")
        elif command == "USER":
            if len(arguments) < 4:
                self.reply_461("USER")
                return
            self.user = arguments[0]
            self.realname = arguments[3]
            print("user set")
        elif command == "QUIT":
            self.disconnect("Client quit")
            return
        if(self.nickname!="" and self.user != ""):
            self.registered = True
            # send messages here 001, 002
            self.reply_001()
            self.reply_002()
            self.reply_003()
            self.reply_004()
            self.reply_251()
            self.reply_422()

    """
    Function that takes paramaters self, channel, command, message, include_self and allows
    the user to communicate over the given channel with the present users. It also displays user information.
    """
    def message_channel(self, channel, command, message, include_self=False):
        line = ":%s!%s@%s %s %s" % (self.nickname, self.user, self.hostname, command, message)
        for client in channel.members.values():
            if client != self or include_self:
                client.message(line)

    """
    Takes self and quitmsg parameter. If the user has disconnected, it will display information of
    the user that just left and remove the client socket. 
    """
    def disconnect(self, quitmsg):
        self.message("ERROR :%s" % quitmsg)
        self.socket.close()

    """
    Takes two parameters self and msg. Prints user message, then assigns the outcome from write_buffer function to msg string.
    """
    def message(self, msg):
        print(msg)
        self.write_buffer += msg + "\r\n"


    # Automatically runs function when user connects and instantly greets the user with "Welcome" and their info.
    def reply_001(self):
        self.reply(": %s 001 %s : Welcome" % (self.hostname, self.nickname))


    # Automatically runs function when user connects and displays the running version of the server.
    def reply_002(self):
        self.reply(": %s 002 %s : Your host is %s, running version 3.0" % (self.hostname, self.nickname, self.hostname))

    # Automatically runs function when user connects, then prints whenever the server is created.
    def reply_003(self):
        self.reply(": %s 003 %s : The server was created sometime" % (self.hostname, self.nickname))

    # Automatically runs function when user connects, then prints the version of the server.
    # In our case this is just generic statement.
    def reply_004(self):
        self.reply(": %s 004 %s : %s version 0" % (self.hostname, self.nickname, self.hostname))

    # Automatically runs function when user connects, then displays the current users on the server.
    def reply_251(self):
        users=0
        for user in self.server.client_sockets:
            users = users + 1
        self.reply(": %s 251 %s : there are %s users" % (self.hostname, self.nickname, users))

    # Automatically runs function when user connects, then prints the message of the day (MOTD).
    def reply_422(self):
        self.reply(": %s 422 %s : no MOTD" % (self.hostname, self.nickname)) 
    
    """
    Method that is used to validate channel names based on user input. 
    Taking paramters (self, arguments, for_join), user input and based on that checks if the channel exists.
    If the channel name if already on the list it just joins that channel, otherwise it creates a new channel.
    """
    def send_names(self, arguments, for_join=False):
        server = self.server
        valid_channel_re = self.valid_channelname_regexp
        if len(arguments) > 0:
            channelnames = arguments[0].split(",")
        else:
            channelnames = sorted(self.channels.keys())
        if len(arguments) > 1:
            keys = arguments[1].split(",")
        else:
            keys = []
        keys.extend((len(channelnames) - len(keys)) * [None])
        for (i, channelname) in enumerate(channelnames):
            if for_join and channelname in self.channels:
                continue
            if not valid_channel_re.match(channelname):
                self.reply_403(channelname)
                continue
            channel = server.get_channel(channelname)

            if for_join:
                channel.members[self.nickname] = self
                self.channels[channelname] = channel
                self.message_channel(channel, "JOIN", channelname, True)

                if channel.topic:
                    self.reply("332 %s %s :%s"
                               % (self.nickname, channel.name, channel.topic))
                else:
                    self.reply("331 %s %s :No topic is set"
                               % (self.nickname, channel.name))
            names_prefix = "353 %s = %s :" % (self.nickname, channelname)
            names = ""
            # Max length: reply prefix ":server_name(space)" plus CRLF in
            # the end.
            names_max_len = 512 - (len(server.hostname) + 2 + 2)
            for name in sorted(x.nickname for x in channel.members.values()):
                if not names:
                    names = names_prefix + name
                # Using >= to include the space between "names" and "name".
                elif len(names) + len(name) >= names_max_len:
                    self.reply(names)
                    names = names_prefix + name
                else:
                    names += " " + name
            if names:
                self.reply(names)
            self.reply("366 %s %s :End of NAMES list"
                       % (self.nickname, channelname))
            

    # Function that returns the leng of the write_buffer/message to be sent to the user
    def write_queue_size(self):
        return len(self.write_buffer)
    
    # Assigns the outcome from write_buffer to the msg string
    def message(self, msg):
        self.write_buffer += msg + "\r\n"

    # Sends the message to the users
    def reply(self, msg):
        self.message(":%s %s" % (self.server.hostname, msg))

    # Error checking in the event that channel does not exist
    def reply_403(self, channel):
        self.reply("403 %s %s :No such channel" % (self.nickname, channel))

    # It is triggered when the user has not inputed enough arguments
    def reply_461(self, command):
        nickname = self.nickname or "*"
        self.reply("461 %s %s :Not enough parameters" % (nickname, command))
    
    """
    Method that checks for the commands in messages and handles them.
    All of valid commands are stored in a dictionary called handler_table.
    """
    # START OF command_handler
    def command_handler(self, command, arguments):
        print(command)
        print(arguments)

        # Creates a new channel or joins existing one. It also deals with users leaving channel
        def join_handler():
            if len(arguments) < 1:
                self.reply_461("JOIN")
                return
            if arguments[0] == "0":
                for (channelname, channel) in self.channels.items():
                    self.message_channel(channel, "PART", channelname, True)
                    self.channel_log(channel, "left", meta=True)
                    #server.remove_member_from_channel(self, channelname)
                self.channels = {}
                return
            self.send_names(arguments, for_join=True)

        """
        Prompt user for nickname and takes it as an argument.
        If user does not enter a nickname an error message is displayed.'
        """
        def nick_handler():
            if len(arguments) < 1:
                self.reply("431 :No nickname given")
                return
            newnick = arguments[0]
            client = server.get_client(newnick)
            if newnick == self.nickname:
                pass
            elif client and client is not self:
                self.reply("433 %s %s :Nickname is already in use"
                           % (self.nickname, newnick))
            else:
                oldnickname = self.nickname
                self.nickname = newnick
                server.client_changed_nickname(self, oldnickname)

        """
        Called when user wants to chat with another user privately, it takes one argument.
        If user specifies the recipient it allows the users to chat privately.
        """
        def notice_and_privmsg_handler():
            if len(arguments) == 0:
                self.reply("411 %s :No recipient given (%s)"
                           % (self.nickname, command))
                return
            if len(arguments) == 1:
                self.reply("412 %s :No text to send" % self.nickname)
                return
            targetname = arguments[0]
            message = arguments[1]
            client = server.get_client(targetname)
            if client:
                client.message(":%s!%s@%s %s %s :%s"
                               % (self.nickname, self.user, self.hostname, command, targetname, message))
            elif targetname in self.channels:
                channel = server.get_channel(targetname)
                self.message_channel(
                    channel, command, "%s :%s" % (channel.name, message))
            else:
                self.reply("401 %s %s :No such nick/channel"
                           % (self.nickname, targetname))

        """
        This function is called when the user wants to leave a channel.
        If the user is not in that channel it displays an error message.
        """
        def part_handler():
            if len(arguments) < 1:
                self.reply_461("PART")
                return
            if len(arguments) > 1:
                partmsg = arguments[1]
            else:
                partmsg = self.nickname
            for channelname in arguments[0].split(","):
                if not valid_channel_re.match(channelname):
                    self.reply_403(channelname)
                elif not channelname in self.channels:
                    self.reply("442 %s %s :You're not on that channel"
                               % (self.nickname, channelname))
                else:
                    channel = self.channels[channelname]
                    self.message_channel(
                        channel, "PART", "%s :%s" % (channelname, partmsg),
                        True)
                    del self.channels[channelname]

        """
        Called to check if the connection between the user and the server is stil alive, 
        takes destination address as an argument.
        """
        def ping_handler():
            if len(arguments) < 1:
                self.reply("409 %s :No origin specified" % self.nickname)
                return
            self.reply("PONG %s :%s" % (server.hostname, arguments[0]))

        # This function was not implemented
        def pong_handler():
            pass


        # This function handles when a user disconnects from the server 
        def quit_handler():
            if len(arguments) < 1:
                quitmsg = self.nickname
            else:
                quitmsg = arguments[0]
            self.disconnect(quitmsg)

        # Contains the command dictionary that is used to for various functionalities of the channels
        # Also checks if the command is a valid one
        handler_table = {
            "JOIN": join_handler,
            "NICK": nick_handler,
            "PART": part_handler,
            "PING": ping_handler,
            "PONG": pong_handler,
            "PRIVMSG": notice_and_privmsg_handler,
            "QUIT": quit_handler,
        }
        server = self.server
        valid_channel_re = self.valid_channelname_regexp
        try:
            handler_table[command]()
        except KeyError:
            self.reply("421 %s %s :Unknown command" % (self.nickname, command))
# END OF command_handler

"""
Users are connected to the Server class, before starting to create/use channels and use commands.
"""
class Server(object):
    # Server constructor to initialises the attributes of this class
    def __init__(self):
        self.ip = "10.0.42.17"
        self.port = 6667
        self.channel_list = {}
        self.rec_buffer = ""
        self.client_sockets = {}
        self.nickname_list = {}
        self.hostname = socket.getfqdn(socket.gethostname())
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.regex = re.compile(r"\r?\n")
        
    # Setting up server's socket and listening for new connections
    def run(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.ip, self.port))
        self.socket.listen()
        list_sockets = []
        list_sockets.append(self.socket)
        self.connect_socket(list_sockets)

    """
    Takes two parameters (self and list_sockets). The current function handles accepting new user connection,
    by checking user sockets and addresses.
    If client already exists in client_socket dictionary changes the socket to readable. 
    If it's a new client then takes the user socket, appends it to list_sockets and prints out 
    the message and where is the new connection from.
    """
    def connect_socket(self, list_sockets):
        while True:
            ready_to_read, ready_to_write, errorIn = select.select(list_sockets, list_sockets, list_sockets)
            for client in ready_to_read:
                if client in self.client_sockets:
                    self.client_sockets[client].socket_readable()
                else:
                    connection, address = client.accept()
                    list_sockets.append(connection)
                    try:
                        self.client_sockets[connection] = Client(self, connection)
                        print("Accepted connection from %s:%s." % (address[0], address[1]))
                        #self.reply("Accepted connection from %s:%s." % (address[0], address[1]))
                        #self.client_sockets[connection].socket_readable()
                    except socket.error:
                        try:
                            connection.close()
                        except Exception:
                            pass
            for client in ready_to_write:
                if client in self.client_sockets:  # client may have been disconnected
                    self.client_sockets[client].socket_write()
                    
    # Function that returns the client nickname
    def get_client(self, nickname):
        return self.nickname_list.get(nickname)
    
    # Function that returns the channel name
    def get_channel(self, channelname):
        if channelname in self.channel_list:
            channel = self.channel_list[channelname]
        else:
            channel = Channel(channelname)
            self.channel_list[channelname] = channel
        return channel
    
    # Function that calls change nickname handler 
    def client_changed_nickname(self, client, oldnickname):
        if oldnickname:
            del self.nickname_list[oldnickname]
        self.nickname_list[client.nickname] = client
        
# Channel class which includes channel constructor and initialises the attributes of this class
class Channel(object):
     def __init__(self, name):
        self.name = name
        self.members = {}
        self.topic = ""
        
# Main method for running the server
def main():
    myServer = Server()
    myServer.run()

if __name__== "__main__":
    main()
