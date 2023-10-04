import socket
import threading
from argparse import ArgumentParser

import os

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

print(f"Server running on {HOST}:{TCP_PORT}")

# os.system(
#    "cvlc -vvv \"../video.mp4\" --sout \"#transcode{vcodec=mp4v,acodec=mpga}:rtp{proto=udp, mux=ts, dst=127.0.0.1, port=65534}\" --loop --ttl 1")

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
        data, client_addr = udp_socket.recvfrom(32768)
        # print("Received datagram from", client_addr)

        # Send the datagram to all connected clients (TODO?: create a thread for each client)
        for client in connected_clients:
            # print("Sending datagram to", client)
            udp_socket.sendto(data, (client["ip"], int(client["vlc_port"])))


def receive_connections():
    while True:
        # Accept a connection from a client
        client_skt, client_addr = server_socket.accept()
        print("Accepted connection from", client_addr)

        # Create a thread to attend the client
        thread = threading.Thread(target=attend_client, args=(client_skt,))
        thread.start()


def attend_client(client_skt: socket.socket):
    client = {}
    while True:
        # Receive a message from the client
        message = client_skt.recv(1024).decode("utf-8")

        # Send response to the client "OK\n"
        client_skt.send("OK\n".encode("utf-8"))

        if "DESCONECTAR" in message:
            # Remove the client from the list and close the connection
            connected_clients.remove(client)
            print("Client", client, "disconnected")
            client_skt.close()
            break

        # Process the message
        if "CONECTAR" in message:
            # Add the client to the list
            client_ip, client_port = client_skt.getpeername()
            client_vlc_port = message.split(" ")[1].split("\\")[0]
            client = {
                "ip": client_ip,
                "port": client_port,
                "vlc_port": client_vlc_port
            }
            connected_clients.append(client)
            print("Client", client, "connected")
            continue

        if "INTERRUMPIR" in message:
            # Remove the client from the list
            connected_clients.remove(client)
            print("Client", client, "interrupted")
            continue

        if "CONTINUAR" in message:
            # Add the client to the list
            connected_clients.append(client)
            print("Client", client, "continued")
            continue


# Create 2 threads to handle UDP and TCP requests
thread1 = threading.Thread(target=receive_stream)
thread1.start()

thread2 = threading.Thread(target=receive_connections)
thread2.start()

thread1.join()
thread2.join()

udp_socket.close()
server_socket.close()

print("Server closed")
