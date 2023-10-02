import argparse
import socket
import threading

# Server configuration
parser = argparse.ArgumentParser(description="Server for streaming video")

parser.add_argument(
    "-a",
    "--ip",
    type=str,
    default="179.24.154.92",
    help="IP address of the server",
)
parser.add_argument(
    "-p", "--port", type=int, default=32768, help="TCP port of the server"
)

args = parser.parse_args()

server_ip = args.ip
server_port = args.port

UDP_PORT = 65534


# Create clients list
connected_clients = [{"ip": "127.0.0.1", "port": 32769, "vlc_port": 65531}]


# Create a UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.bind((server_ip, UDP_PORT))

print("UDP socket listening on port", UDP_PORT)


# Create a TCP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((server_ip, server_port))
server_socket.listen(5)

print("TCP socket listening on port", server_port)


def receive_stream():
    while True:
        # Receive a datagram from VLC media player
        data, client_addr = udp_socket.recvfrom(32768)
        print("Received datagram from", client_addr)

        # Send the datagram to all connected clients
        for client in connected_clients:
            udp_socket.sendto(data, (client["ip"], client["vlc_port"]))


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

        # Process the message
        if "CONECTAR" in message:
            # Add the client to the list
            client_ip, client_port = client_skt.getpeername()
            client_vlc_port = message.split(" ")[1].split("\\")[0]
            client = {"ip": client_ip, "port": client_port, "vlc_port": client_vlc_port}
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

        if "DESCONECTAR" in message:
            # Remove the client from the list and close the connection
            connected_clients.remove(client)
            print("Client", client, "disconnected")
            client_skt.close()
            break


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
