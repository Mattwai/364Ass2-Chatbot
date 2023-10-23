import select
import socket
import sys
import signal
import argparse
import threading
import ssl

from utils import *

SERVER_HOST = "localhost"

stop_thread = False


def get_and_send(client):
    while not stop_thread:
        data = sys.stdin.readline().strip()
        if data:
            send(client.sock, data)


class ChatClient:
    """A command line chat client using select"""

    def __init__(self, port, host=SERVER_HOST):
        self.connected = False
        self.host = host
        self.port = port

        self.context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

        # Initial prompt
        self.prompt = None
        self.name = None

        # Connect to server at port
        self.connect_to_server()
        threading.Thread(target=get_and_send, args=(self,)).start()

    def connect_to_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock = self.context.wrap_socket(self.sock, server_hostname=self.host)

            self.sock.connect((self.host, self.port))
            print(f"Now connected to chat server@ port {self.port}")
            self.connected = True

            # Send my name...
            print("Login")
            self.name = input("Username: ")
            send(self.sock, "USERNAME: " + self.name)
            data = receive(self.sock)
            if data.startswith("Username not recognized"):
                self.password = input("Username not recognized. Create a password: ")
                send(self.sock, "Registered password: " + self.password)
                rego_data = receive(self.sock)
                if rego_data.startswith("Registration successful"):
                    print(rego_data)
                    self.prompt = "Me: "
                else:
                    print("Registration failed")
                    self.connected = False
            elif data.startswith("Existing user"):
                self.password = input("Enter your password: ")
                send(self.sock, "Password: " + self.password)
                login_data = receive(self.sock)
                if login_data.startswith("Login failed"):
                    print(login_data)
                    self.connected = False
                    self.cleanup()
                elif login_data.startswith("Login successful"):
                    print(login_data)
                    self.prompt = "Me: "
                else:
                    print(login_data)
                    self.connected = False
                    self.cleanup()
            else:
                print(login_data)
                self.connected = False
                self.cleanup()

        except socket.error as e:
            print(f"Failed to connect to chat server @ port {self.port}")
            sys.exit(1)

    def cleanup(self):
        """Close the connection and wait for the thread to terminate."""
        self.sock.close()

    def run(self):
        """Chat client main loop"""
        while self.connected:
            try:
                sys.stdout.write(self.prompt)
                sys.stdout.flush()

                # Wait for input from stdin and socket
                # readable, writeable, exceptional = select.select([0, self.sock], [], [])
                readable, writeable, exceptional = select.select([self.sock], [], [])

                for sock in readable:
                    if sock == self.sock:
                        data = receive(self.sock)
                        if not data:
                            print("Client shutting down.")
                            self.connected = False
                            break
                        else:
                            sys.stdout.write(data + "\n")
                            sys.stdout.flush()
                    elif sock == sys.stdin:
                        data = sys.stdin.readline().strip()
                        if data:
                            if data == "-list":
                                self.send_list_request()  # Send a request for the list of clients
                            else:
                                send(self.sock, data)

            except KeyboardInterrupt:
                print(" Client interrupted. " "")
                stop_thread = True
                self.cleanup()
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", action="store", dest="port", type=int, required=True)
    given_args = parser.parse_args()

    port = given_args.port

    client = ChatClient(port=port)
    client.run()
