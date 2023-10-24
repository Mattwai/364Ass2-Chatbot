pip install bcrypt, and any other dependencies not on in environment from file imports. Make sure to use python 3.7 or above

To run the chat application, first run the server code below in folder command line:
Can rename 'server' in server arguments, and change port, however server and clients must be on the same port for clients to use the server to communicate.
After successfully starting up the server, run the client code below.
Run client code and enter username and password to register or login.
Each client must be initialised one at a time, MUST LOG IN WITH CLIENT BEFORE INITIALISING ANOTHER.

Run server:
python chat_server.py --name=server --port=9988

In another terminal, run client/s:
python chat_client.py --port=9988

Enter a registered username to login and enter password or enter a new username and password to register.
Once logged in, can communicate with other client.
In the command line type "-list" to see all user online on the server
To send a direct 1-1 message type "-sendto [username of client] [message]"
