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
class Client(object):

    linesep_regexp = re.compile(r"\r?\n")
    valid_channelname_regexp = re.compile(r"^[&#+!][^\x00\x07\x0a\x0d ,:]{0,50}$")
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
    
    def write_queue_size(self):
        return len(self.write_buffer)
    
    def message(self, msg):
        self.write_buffer += msg + "\r\n"

    def reply(self, msg):
        self.message(":%s %s" % (self.server.hostname, msg))

    def reply_403(self, channel):
        self.reply("403 %s %s :No such channel" % (self.nickname, channel))

    def reply_461(self, command):
        nickname = self.nickname or "*"
        self.reply("461 %s %s :Not enough parameters" % (nickname, command))
    
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

    def socket_readable(self):
        data = ""
        data = self.socket.recv(1024)
        self.rec_buffer += data.decode()
        self.parse_read_buffer()

    def socket_write(self):

        amountBuffer = self.socket.send(self.write_buffer.encode())
        self.write_buffer = self.write_buffer[amountBuffer:]

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

    def message_channel(self, channel, command, message, include_self=False):
        line = ":%s!%s@%s %s %s" % (self.nickname, self.user, self.hostname, command, message)
        for client in channel.members.values():
            if client != self or include_self:
                client.message(line)

    def disconnect(self, quitmsg):
        self.message("ERROR :%s" % quitmsg)
        self.server.print_info(
            "Disconnected connection from %s:%s (%s)." % (
                self.host, self.port, quitmsg))
        self.socket.close()
        self.server.remove_client(self, quitmsg)

    def message(self, msg):
        print(msg)
        self.write_buffer += msg + "\r\n"



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
# START OF command_handler
    def command_handler(self, command, arguments):
        print(command)
        print(arguments)
        def join_handler():
            if len(arguments) < 1:
                self.reply_461("JOIN")
                return
            if arguments[0] == "0":
                for (channelname, channel) in self.channels.items():
                    self.message_channel(channel, "PART", channelname, True)
                    self.channel_log(channel, "left", meta=True)
                    server.remove_member_from_channel(self, channelname)
                self.channels = {}
                return
            self.send_names(arguments, for_join=True)

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
                for x in self.channels.values():
                    self.channel_log(
                        x, "changed nickname to %s" % newnick, meta=True)
                oldnickname = self.nickname
                self.nickname = newnick
                server.client_changed_nickname(self, oldnickname)

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
                    self.channel_log(channel, "left (%s)" % partmsg, meta=True)
                    del self.channels[channelname]
                    server.remove_member_from_channel(self, channelname)

        def ping_handler():
            if len(arguments) < 1:
                self.reply("409 %s :No origin specified" % self.nickname)
                return
            self.reply("PONG %s :%s" % (server.name, arguments[0]))

        def pong_handler():
            pass

        def quit_handler():
            if len(arguments) < 1:
                quitmsg = self.nickname
            else:
                quitmsg = arguments[0]
            self.disconnect(quitmsg)

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
# evince - document viewer
class Server(object):

    def __init__(self):
        self.ip = "127.0.0.1"
        self.port = 6667
        self.channel_list = {}
        self.rec_buffer = ""
        self.client_sockets = {}
        self.nickname_list = {}
        self.hostname = socket.getfqdn(socket.gethostname())
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.regex = re.compile(r"\r?\n")

    def run(self):
        
        # Setting up server's socket and listening for new connections
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.ip, self.port))
        self.socket.listen()
        list_sockets = []
        list_sockets.append(self.socket)
        self.connect_socket(list_sockets)

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

    def get_client(self, nickname):
        return self.nickname_list.get(nickname)

    def get_channel(self, channelname):
        if channelname in self.channel_list:
            channel = self.channel_list[channelname]
        else:
            channel = Channel(channelname)
            self.channel_list[channelname] = channel
        return channel

    def client_changed_nickname(self, client, oldnickname):
        if oldnickname:
            del self.nickname_list[oldnickname]
        self.nickname_list[client.nickname] = client

class Channel(object):
     def __init__(self, name):
        self.name = name
        self.members = {}
        self.topic = ""

def main():

    myServer = Server()
    myServer.run()

if __name__== "__main__": # lookup how to run main in python
    main()