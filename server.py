# Streaming Server Implementation
import socket

# Server configuration
HOST = "127.0.0.1"
PORT = 65432

# Create a server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the host and port
server_socket.bind((HOST, PORT))

# Listen for incoming connections
server_socket.listen(5)
