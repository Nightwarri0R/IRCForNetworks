import socket
import select
import sys
import string
import datetime



HEADER_LENGTH = 10

Channel= {}
# Code found in: https://pythonprogramming.net/server-chatroom-sockets-tutorial-python-3/
# Create a socket
# socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
# socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw IP packets
class server_connection():
    IP = "127.0.0.1"
    PORT = 6667
    def connection_to_server(self, IP, PORT):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # SO_ - socket option   
        # SOL_ - socket option level
        # Sets REUSEADDR (as a socket option) to 1 on socket
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Random seed to pick numbers which will be used later on to generate sockets

        # Bind, so server informs operating system that it's going to use given IP and port
        # For a server using 0.0.0.0 means to listen on all available interfaces, useful to connect locally to 127.0.0.1 and remotely to LAN interface IP
        self.server_socket.bind((IP, PORT))
        # This makes server listen to new connections
        self.server_socket.listen(10)

        # List of sockets for select.select()
        self.sockets_list = [server_socket]

        # List of connected clients - socket as a key, user header and name as data
        clients = {}

    def run(connection_to_server):
        for x in clients:
            print("List of current clients", clients)



# Handles message receiving
class current_channels(Object):
    current_channel_users = {}

    def __init__(self, name, server_connection):

        self.channel_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.channel_socket = socket.socket(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.channel_socket.bind(('localhost',server_connection.self.socket_list))

        self.channel_socket.listen(15)

    # Method for adding users to the object of channell 
    def add_users(NICK ,current_users = server_connection()):
        current_channel_users = ['NICK', current_users.self.clients]


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
            read_sockets, _, exception_sockets = select.select(channel_socket, [], channel_socket)


        # Iterate over notified sockets
        for notified_socket in read_sockets:

            # If notified socket is a server socket -new connection, accept it
            if notified_socket == server_socket:

                # Accept new connection
                # That gives us new socket - client socket, connected to this given client only, it's unique for that client
                # The other returned object is ip/port set
                client_socket, client_address = server_socket.accept()

                # creating_new_channel(client_socket)
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

                print('Accepted new connection from {}:{}, username: {}'.format(*client_address, user['data'].decode('utf-8')))

            # Else existing socket is sending a message
            else:

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
                


class message_commands():
        # JOIN <channels>
        # Makes the client join the channels in the comma-separated list <channels>. If the channel(s) do not exist
        # then they will be created.
        if message["data"].decode("utf-8").find("JOIN") != -1:
            parse = message["data"].decode("utf-8").split(" ", 1)
            channels = parse[1]
            #join(channels)
            #break

        # PART <channels>
        # Causes a user to leave the channels in the comma-separated list <channels>
        elif message["data"].decode("utf-8").find("PART") != -1:
            parse = message["data"].decode("utf-8").split(" ", 1)
            channels = parse[1]
            #part(channels)
            #break

        # PRIVMSG <msgtarget> <message>
        # Sends <message> to <msgtarget>, which is usually a user or channel.
        elif message["data"].decode("utf-8").find("PRIVMSG") != -1:
            # parse = message["data"].decode("utf-8").split(" ", 2)
            # target = parse[1]
            # msg = parse[2]
            # privatemsg(target, msg)
            message="whatever"
            message = message.encode('utf-8')
            message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
            client_socket.send(user['header'] + user['data'] + message_header + message)

        # QUIT function
        elif message["data"].decode("utf-8").find("QUIT") != -1:
            # sys.exit() HAS TO FINISH THE CLIENT FILE NOT SERVER
            break
        # LIST function (lists all clients connected to the server)
        elif message["data"].decode("utf-8").find("LIST") != -1:
            # sys.exit() HAS TO FINISH THE CLIENT FILE NOT SERVER
            for client_socket in clients:
                clients[client_socket] = user
                print('Accepted new connection from {}:{}, username: {}'.format(*client_address, user['data'].decode('utf-8')))

        # DAY function
        # Shows the date when !day is entered
        elif message["data"].decode("utf-8").find("!day") != -1:
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
        elif message["data"].decode("utf-8").find("!time") != -1:
            time = datetime.datetime.now()
            print(time.strftime("%H:%M"))

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


