import socket
import threading
from argparse import ArgumentParser

from protocol import ControlStream

import sys

# Parse and get arguments
parser = ArgumentParser(description="Video streaming server")

parser.add_argument(
    "ip",
    type=str,
    nargs="?",
    default="127.0.0.1",
    help="IP address of the server",
)
parser.add_argument(
    "port", type=int, nargs="?", default=32768, help="TCP port of the server"
)

args = parser.parse_args()

HOST = args.ip
TCP_PORT = args.port
UDP_PORT = 65534
UDP_BUFFER_SIZE = 32768

print(f"Server running on {HOST}:{TCP_PORT}")


# Create a Lock to control the access to the clients list
clients_lock = threading.Lock()

# Create clients list
connected_clients = []


# Create a UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.bind((HOST, UDP_PORT))

print("UDP socket listening on port", UDP_PORT)


# Create a TCP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, TCP_PORT))
server_socket.listen(5)

print("TCP socket listening on port", TCP_PORT)


def receive_stream():
    while True:
        # Receive a datagram from VLC media player
        data, client_addr = udp_socket.recvfrom(UDP_BUFFER_SIZE)
        # print("Received datagram from", client_addr)

        # Send the datagram to all connected clients
        # mutex for connected_client
        for client in connected_clients:
            udp_socket.sendto(
                data, (client["ip"], int(client["vlc_port"])))


def attend_client(client_skt: socket.socket):
    client = {}
    while True:
        try:
            # Receive a message from the client
            message = client_skt.recv(1024).decode("utf-8")

            message = message.strip()

            # Process the message
            if message.split(" ")[0] == ControlStream.CONNECT:
                # Add the client to the list
                client_ip, client_port = client_skt.getpeername()
                message = message.split(" ")
                if len(message) != 2:
                    client_skt.send(
                        "[BAD REQUEST] VLC Port missing\n".encode("utf-8"))
                    continue
                client_vlc_port = message[1].split("\\")[0]
                try:
                    client_vlc_port = int(client_vlc_port)
                except:
                    client_skt.send(
                        "[BAD REQUEST] VLC Port must be a number\n".encode("utf-8"))
                    continue
                client = {"ip": client_ip, "port": client_port,
                          "vlc_port": client_vlc_port}

                with clients_lock:
                    if client not in connected_clients:
                        connected_clients.append(client)

                print("Client", client, "connected")
                print(connected_clients)
                continue

            if message not in ControlStream.__members__.values():
                print(f"Unknown command {message}. Supported commands:")
                print(*ControlStream.__members__.values())
                client_skt.send(
                    "[BAD REQUEST] Unknown command\n".encode("utf-8"))
                continue

            client_skt.send("OK\n".encode("utf-8"))

            if message == ControlStream.DISCONNECT:
                # Remove the client from the list and close the connection
                with clients_lock:
                    if client in connected_clients:
                        connected_clients.remove(client)

                print("Client", client, "disconnected")
                client_skt.close()
                print(connected_clients)
                break

            if message == ControlStream.INTERRUPT:
                # Remove the client from the list
                with clients_lock:
                    if client in connected_clients:
                        connected_clients.remove(client)

                print("Client", client, "interrupted")
                print(connected_clients)
                continue

            if message == ControlStream.CONTINUE:
                # Add the client to the list
                with clients_lock:
                    if client not in connected_clients:
                        connected_clients.append(client)

                print("Client", client, "continued")
                print(connected_clients)
                continue
        except Exception as e:
            print(e)


# Create 2 threads to handle UDP and TCP requests
thread1 = threading.Thread(target=receive_stream)
thread1.start()

if __name__ == "__main__":
    try:
        while True:
            # Accept a connection from a client
            client_skt, client_addr = server_socket.accept()
            print("Accepted connection from", client_addr)

            # Create a thread to attend the client
            thread = threading.Thread(target=attend_client, args=(client_skt,))
            thread.start()
    except KeyboardInterrupt:
        print("Closing server...")
        server_socket.close()
        udp_socket.close()
        print("Resources released.")
        sys.exit(0)
