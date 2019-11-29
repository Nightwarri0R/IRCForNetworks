import socket
import select
import threading 
import sys
import re
import string
import datetime

IP = "127.0.0.1"
PORT = 1234

class Server: 

        HEADER_LENGTH = 10
        # Code found in: https://pythonprogramming.net/server-chatroom-sockets-tutorial-python-3/
        # Create a socket
        # socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
        # socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw IP packets
        def __init__(self, IP, PORT):
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # SO_ - socket option
            # SOL_ - socket option level
            # Sets REUSEADDR (as a socket option) to 1 on socket
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Random seed to pick numbers which will be used later on to generate sockets

            # Bind, so server informs operating system that it's going to use given IP and port
            # For a server using 0.0.0.0 means to listen on all available interfaces, useful to connect locally to 127.0.0.1 and remotely to LAN interface IP
            server_socket.bind((IP, PORT))
            # This makes server listen to new connections
            server_socket.listen(10)



            # List of sockets for select.select()
            sockets_list = [server_socket]

            # List of connected clients - socket as a key, user header and name as data
            clients = []
            # print(f'Listening for connections on {IP}:{PORT}...')

        # Handles message receiving
        def receive_message(self):

            try:

                # Receive our "header" containing message length, it's size is defined and constant
                message_header = client_socket.recv(HEADER_LENGTH)

                # If we received no data, client gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
                if not len(message_header):
                    return False

                # Convert header to int value
                message_length = int(message_header.decode('utf-8').strip())

                # Return an object of message header and message data
                return {'header': message_header, 'data': client_socket.recv(message_length)}

            except:

                # If we are here, client closed connection violently, for example by pressing ctrl+c on his script
                # or just lost his connection
                # socket.close() also invokes socket.shutdown(socket.SHUT_RDWR) what sends information about closing the socket (shutdown read/write)
                # and that's also a cause when we receive an empty message
                return False

        
            while True:

            # Calls Unix select() system call or Windows select() WinSock call with three parameters:
            #   - rlist - sockets to be monitored for incoming data
            #   - wlist - sockets for data to be send to (checks if for example buffers are not full and socket is ready to send some data)
            #   - xlist - sockets to be monitored for exceptions (we want to monitor all sockets for errors, so we can use rlist)
            # Returns lists:
            #   - reading - sockets we received some data on (that way we don't have to check sockets manually)
            #   - writing - sockets ready for data to be send thru them
            #   - errors  - sockets with some exceptions
            # This is a blocking call, code execution will "wait" here and "get" notified in case any action should be taken
                read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)


            # Iterate over notified sockets
            for notified_socket in read_sockets:

                # If notified socket is a server socket - new connection, accept it
                if notified_socket == server_socket:

                    # Accept new connection
                    # That gives us new socket - client socket, connected to this given client only, it's unique for that client
                    # The other returned object is ip/port set
                    client_socket, client_address = server_socket.accept()

                    #print(accept())
                    # Client should send his name right away, receive it
                    user = receive_message(client_socket)

                    # If False - client disconnected before he sent his name
                    if user is False:
                        continue

                    # Add accepted socket to select.select() list
                    sockets_list.append(client_socket)

                    # Also save username and username header
                    clients[client_socket] = user

        # join channel(s).
        channel = "##bot-testing"

        def joinchan():
            print ("Hello what")
            #server_socket.send(bytes("JOIN " + channel + "n", "UTF-8"))
            #ircmsg = ""
            #while ircmsg.find("End of /NAMES list.") == -1:
                #ircmsg = server_socket.recv(2048).decode("UTF-8")
                #ircmsg = ircmsg.strip('nr')
                #print(ircmsg)

        def sendmsg(msg, target=channel):  # sends messages to the target.
            server_socket.send(bytes("PRIVMSG " + target + " :" + msg + "n", "UTF-8"))

        # Handles message receiving
        def receive_message(client_socket):
                    print('Accepted new connection from {}:{}, username: {}'.format(*client_address, user['data'].decode('utf-8')))

                # Else existing socket is sending a message

                    # Receive message
                    message = receive_message(notified_socket)

                    # If False, client disconnected, cleanup
                    if message is False:
                        print('Closed connection from: {}'.format(clients[notified_socket]['data'].decode('utf-8')))

                        # Remove from list for socket.socket()
                        sockets_list.remove(notified_socket)

                        # Remove from our list of users
                        del clients[notified_socket]

                        continue

                    # Get user by notified socket, so we will know who sent the message
                    user = clients[notified_socket]

                    print(f'Received message from {user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}')
                    

                    # Iterate over connected clients and broadcast message
                    for client_socket in clients:
                        # But don't sent it to sender
                        if client_socket != notified_socket:

                            # Send user and message (both with their headers)
                            # We are reusing here message header sent by sender, and saved username header send by user when he connected
                            client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])

                    # It's not really necessary to have this, but will handle some socket exceptions just in case
                        for notified_socket in exception_sockets:

                            # Remove from list for socket.socket()
                            sockets_list.remove(notified_socket)

                            # Remove from our list of users
                            del clients[notified_socket]
                            # class for #
        def run(self):
            Server.receive_message(self)


class Channel:
    #channel_server = Server.connections: 
    
    # initialising the name of the channel
    def __init__(self, name):
        self.name = name
    # list of users
    userList = []

    # function to check if a user is already in the channel
    def checkUser(userToBeChecked):
        if userToBeChecked in userList:
            return True
        if userToBeChecked not in userList:
            return False

            # JOIN <channels>
            # Makes the client join the channels in the comma-separated list <channels>. If the channel(s) do not exist
            # then they will be created.
            if message["data"].decode("utf-8").find("JOIN") != -1:
                join()

            # PART <channels>
            # Causes a user to leave the channels in the comma-separated list <channels>
            if message["data"].decode("utf-8").find("PART") != -1:
                part()

            # PRIVMSG <msgtarget> <message>
            # Sends <message> to <msgtarget>, which is usually a user or channel.
            if message["data"].decode("utf-8").find("PRIVMSG") != -1:
                privatemessage()

            # QUIT function
            if message["data"].decode("utf-8").find("QUIT") != -1:
                sys.exit()

            # DAY function
            # Shows the date when !day is entered
            if message["data"].decode("utf-8").find("!day") != -1:
                date = datetime.datetime.now()
                print(date.strftime("%d/%m/%Y"))
                # Wait for user to input a message
                #message = date.strftime("%x")
                # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
                #message = message.encode('utf-8')
                #message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
                #client_socket.send(message + message_header)

            # TIME function
            # Shows the time when !time is entered
            if message["data"].decode("utf-8").find("!time") != -1:
                time = datetime.datetime.now()
                print(time.strftime("%H:%M"))

            # Iterate over connected clients and broadcast message
            for client_socket in clients:
                # But don't sent it to sender
                if client_socket != notified_socket:

    # function to remove an user from the channel
    def removeUser(userToBeDeleted):
        if(checkUser(userToBeDeleted)==1):
            userList.remove(userToBeDeleted)
        else:
            print("User is not in the channel, therefore the user cannot be removed")

    def returnUsers(): 
        return userList 

    # method to display all the users in a channel
while True:

    server1 = Server(IP, PORT)
    server_thread = threading.Thread(name='main_channel', target=server1.run())
    server_thread.start()
