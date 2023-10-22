To run the chat application, first run the server code below:
Can rename 'server', and change port, however server and clients must be on the same port.
After successfully starting up the server, run the client code below.
Run client code and enter username one at a time.

pip install bcrypt

Run server:
python chat_server.py --name=server --port=9988

Run client/s:
python chat_client.py --port=9988