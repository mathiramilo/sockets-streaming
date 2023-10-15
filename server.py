import socket
import sys
import threading
from argparse import ArgumentParser

from protocol import ControlStream

import logging

# Parse and get arguments
parser = ArgumentParser(description="Video streaming server")

parser.add_argument(
    "ip",
    type=str,
    default="127.0.0.1",
    help="IP address of the server",
)
parser.add_argument(
    "port", type=int, default=32768, help="TCP port of the server"
)
parser.add_argument(
    "--log_level", type=str, default="DEBUG", help="Logging level (WARNING, INFO, DEBUG)"
)

args = parser.parse_args()
logging.basicConfig(level=getattr(logging, args.log_level.upper()),
                    format='[%(levelname)s] (%(threadName)-9s) %(message)s',)

HOST = args.ip
TCP_PORT = args.port
UDP_PORT = 65534
UDP_BUFFER_SIZE = 32768

logging.info(f"Server running on {HOST}:{TCP_PORT}")


# Create a Lock to control the access to the clients list
clients_lock = threading.Lock()

# Create clients list
connected_clients = []


# Create a UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.bind((HOST, UDP_PORT))

logging.info(f"UDP socket listening on port {UDP_PORT}")


# Create a TCP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, TCP_PORT))
server_socket.listen(5)

logging.info(f"TCP socket listening on port {TCP_PORT}")


def receive_stream():
    while True:
        try:
            # Receive a datagram from VLC media player
            data, client_addr = udp_socket.recvfrom(UDP_BUFFER_SIZE)

            # Send the datagram to all connected clients
            # mutex for connected_client
            for client in connected_clients:
                udp_socket.sendto(
                    data, (client["ip"], int(client["vlc_port"])))
        except Exception as e:
            logging.debug(e)


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
                        "[BAD REQUEST] VLC Port must be a number\n".encode(
                            "utf-8")
                    )
                    continue

                client = {
                    "ip": client_ip,
                    "port": client_port,
                    "vlc_port": client_vlc_port,
                }

                with clients_lock:
                    if client not in connected_clients:
                        connected_clients.append(client)

                logging.info(f"Client {client} connected")
                logging.info(
                    f"{len(connected_clients)} connected clients: {connected_clients}"
                )
                client_skt.send("OK\n".encode("utf-8"))
                continue

            if message not in ControlStream.__members__.values():
                client_skt.send(
                    "[BAD REQUEST] Unknown command\n".encode("utf-8"))
                continue

            if message == ControlStream.DISCONNECT:
                # Remove the client from the list and close the connection
                with clients_lock:
                    if client in connected_clients:
                        connected_clients.remove(client)

                logging.info(f"Client {client} disconnected")
                logging.info(
                    f"{len(connected_clients)} connected clients: {connected_clients}"
                )
                client_skt.send("OK\n".encode("utf-8"))
                client_skt.close()
                logging.debug(f"Closing connection with {client}")
                break

            if message == ControlStream.INTERRUPT:
                # Remove the client from the list
                with clients_lock:
                    if client in connected_clients:
                        connected_clients.remove(client)

                logging.info(f"Client {client} interrupted")
                logging.info(
                    f"{len(connected_clients)} connected clients: {connected_clients}"
                )
                client_skt.send("OK\n".encode("utf-8"))
                continue

            if message == ControlStream.CONTINUE:
                # Add the client to the list
                with clients_lock:
                    if client not in connected_clients:
                        connected_clients.append(client)

                logging.info(f"Client {client} continued")
                logging.info(
                    f"{len(connected_clients)} connected clients: {connected_clients}"
                )
                client_skt.send("OK\n".encode("utf-8"))
                continue
        except Exception as e:
            logging.debug(e)


if __name__ == "__main__":
    try:
        # Create a thread to handle video streaming
        streaming_thread = threading.Thread(target=receive_stream)
        streaming_thread.start()

        while True:
            # Accept a connection from a client
            client_skt, client_addr = server_socket.accept()
            logging.info(f"Accepted connection from {client_addr}")

            # Create a thread to attend the client
            thread = threading.Thread(target=attend_client, args=(client_skt,))
            thread.start()
    except KeyboardInterrupt:
        logging.info("Closing server...")
        logging.debug(f"Closing {server_socket} and {udp_socket}")
        server_socket.close()
        udp_socket.close()
        logging.info("Resources released.")
        sys.exit(0)
