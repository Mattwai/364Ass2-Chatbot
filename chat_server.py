import select
import socket
import sys
import signal
import argparse
import ssl
import bcrypt

from utils import *

SERVER_HOST = "localhost"


class ChatServer(object):
    """An example chat server using select"""

    def __init__(self, port, backlog=5):
        self.clients = 0
        self.clientmap = {}
        self.outputs = []  # list output sockets

        self.load_user_credentials()
        self.user_credentials = {}

        self.context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        self.context.load_cert_chain(certfile="cert.pem", keyfile="cert.pem")
        self.context.load_verify_locations("cert.pem")
        self.context.set_ciphers("AES128-SHA")

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((SERVER_HOST, port))
        self.server.listen(backlog)
        self.server = self.context.wrap_socket(self.server, server_side=True)

        # Catch keyboard interrupts
        signal.signal(signal.SIGINT, self.sighandler)

        print(f"Server listening to port: {port} ...")

    def load_user_credentials(self):
        try:
            with open("user_credentials.p", "rb") as file:
                self.user_credentials = pickle.load(file)
        except FileNotFoundError:
            print("No file found")

    def save_user_credentials(self):
        # Save user credentials to a pickled file
        with open("user_credentials.p", "wb") as file:
            pickle.dump(self.user_credentials, file)

    def sighandler(self, signum, frame):
        """Clean up client outputs"""
        print("Shutting down server...")

        # Close existing client sockets
        for output in self.outputs:
            output.close()

        self.server.close()

    def get_client_name(self, client):
        """Return the name of the client"""
        info = self.clientmap[client]
        name = info[1]
        return name

    def list_clients(self, client_sock):
        """Send a list of connected clients to the requesting client"""
        client_names = [self.get_client_name(sock) for sock in self.clientmap]
        client_list = "Online Users:\n" + "\n".join(client_names)
        send(client_sock, client_list)

    def login(self, client_sock, user_info):
        username = user_info.strip()
        if username in self.user_credentials:
            # Username exists, request password
            send(client_sock, "Existing user.")
            received_password = receive(client_sock).split("Password: ")[1]
            stored_password = self.user_credentials[username]
            if bcrypt.checkpw(received_password.encode("utf-8"), stored_password):
                send(client_sock, "Login successful")
                return True
            else:
                send(client_sock, "Login failed. Incorrect password.")
                return False
        else:
            send(client_sock, "Username not recognized.")
            # Username doesn't exist, allow registration
            new_password = receive(client_sock).split("Registered password: ")[1]

            # Hash the new password before storing it
            hashed_password = bcrypt.hashpw(
                new_password.encode("utf-8"), bcrypt.gensalt()
            )

            # Write the new user's credentials to the file
            self.user_credentials[username] = hashed_password
            self.save_user_credentials()

            send(client_sock, "Registration successful.")
            return True

    def send_message_to_client(self, sender_username, target_username, message):
        for client_sock, (address, username) in self.clientmap.items():
            if username == target_username:
                # Found the target client, send them the message with sender's username
                msg = f"\n{sender_username}: {message}"
                send(client_sock, msg)
                return
        # If the target client is not found, handle the error accordingly
        error_msg = f"\nServer: Client '{target_username}' not found or not connected."
        print(error_msg)

    def run(self):
        # inputs = [self.server, sys.stdin]
        inputs = [self.server]
        self.outputs = []
        running = True
        while running:
            try:
                readable, writeable, exceptional = select.select(
                    inputs, self.outputs, []
                )
            except select.error as e:
                break

            for sock in readable:
                sys.stdout.flush()
                if sock == self.server:
                    # handle the server socket
                    client, address = self.server.accept()

                    print(
                        f"Chat server: got connection {client.fileno()} from {address}"
                    )
                    # Read the login name
                    cname = receive(client).split("USERNAME: ")[1]
                    if self.login(client, cname):
                        # Compute client name and send back
                        self.clients += 1
                        send(client, f"CLIENT: {str(address[0])}")
                        inputs.append(client)

                        self.clientmap[client] = (address, cname)
                        # Send joining information to other clients
                        msg = f"\n(Connected: ({self.clients}) is online from {self.get_client_name(client)})"
                        for output in self.outputs:
                            send(output, msg)
                        self.outputs.append(client)
                    else:
                        # If login fails, close the connection
                        client.close()

                else:
                    # handle all other sockets
                    try:
                        data = receive(sock)
                        if data:
                            if data == "-list":
                                self.list_clients(
                                    sock
                                )  # Handle the client's request for the list
                            elif data.startswith("-sendto"):
                                target_username, message = data[
                                    len("-sendto ") :
                                ].split(" ", 1)
                                self.send_message_to_client(
                                    self.get_client_name(sock), target_username, message
                                )
                            else:
                                # Send as new client's message...
                                msg = f"\n{self.get_client_name(sock)}: {data}"

                                # Send data to all except ourself
                                for output in self.outputs:
                                    if output != sock:
                                        send(output, msg)
                        else:
                            print(f"Chat server: {sock.fileno()} hung up")
                            self.clients -= 1
                            sock.close()
                            inputs.remove(sock)
                            self.outputs.remove(sock)

                            # Sending client leaving information to others
                            msg = f"\n(Now hung up: Client from {self.get_client_name(sock)})"

                            for output in self.outputs:
                                send(output, msg)
                    except socket.error as e:
                        # Remove
                        inputs.remove(sock)
                        self.outputs.remove(sock)

        self.server.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Socket Server Example with Select")
    parser.add_argument("--name", action="store", dest="name", required=True)
    parser.add_argument("--port", action="store", dest="port", type=int, required=True)
    given_args = parser.parse_args()
    port = given_args.port
    name = given_args.name

    server = ChatServer(port)
    server.run()
