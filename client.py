import socket
from argparse import ArgumentParser

from protocol import ControlStream

"""
usage examplei:
python cliente.py <ServerIP> <ServerPort> <PuertoVLC>

<ServerIP>: Dirección IP del servidor al que se desea conectar, por ejemplo 127.0.0.1
<ServerPort>: Puerto del servidor al que se desea conectar, por ejemplo 2023
<PuertoVLC>: Puerto de la instancia de VLC del cliente usada para reproducir el stream
"""


class ClientControlTCP:
    """
    Sera usado por los usuarios finales para iniciar, interrumpir,
    continuar y cerrar su sesión de streaming

    El cliente debe implementar una consola de texto para leer comandos
    especificados por el usuario, que permiten controlar la reproducción. Se deben
    implementar los comandos CONECTAR, INTERRUMPIR, CONTINUAR y
    DESCONECTAR.
    """

    def __init__(self, server_ip, server_port, vlc_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.vlc_port = vlc_port

        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.connect((self.server_ip, self.server_port))

    def send_message(self, message):
        print(f"[CLIENT] {message}")
        message += "\n"
        self.tcp_socket.send(message.encode())
        response = self.tcp_socket.recv(1024).decode()
        return response

    def connect(self):
        """
        Solicita al servidor la reproducción del stream.
        Solicita el envío del stream a la dirección IP del cliente y el puerto <puerto-udp-cliente>.
        """
        return self.send_message(f"{ControlStream.CONNECT} {self.vlc_port}")

    def interrupt(self):
        """
        Solicita al servidor que suspenda momentáneamente la
        transmisión.
        """
        return self.send_message(ControlStream.INTERRUPT)

    def continue_stream(self):
        """
        Solicita al servidor que retome la transmisión luego de haber
        ejecutado el comando INTERRUMPIR.
        La continuación se realiza a partir del
        próximo datagrama del stream recibido por el server luego de recibir el comando
        CONTINUAR
        """
        return self.send_message(ControlStream.CONTINUE)

    def disconnect(self):
        """
        Solicita al servidor la finalización de la transmisión.
        Después de ejecutar el comando DESCONECTAR, se debe cerrar del cliente.
        """
        response = self.send_message(ControlStream.DISCONNECT)
        self.tcp_socket.close()
        return response

    def run(self):
        print(self.connect())

        while True:
            command = input("Command> ")

            if command not in ControlStream.__members__.values():
                print(f"Unknown command {command}. Supported commands:")
                print(*ControlStream.__members__.values())
                continue

            if command == ControlStream.CONNECT:
                response = self.connect()
            elif command == ControlStream.INTERRUPT:
                response = self.interrupt()
            elif command == ControlStream.CONTINUE:
                response = self.continue_stream()
            elif command == ControlStream.DISCONNECT:
                response = self.disconnect()
                print(f"[SERVER] {response}")
                break

            print(f"[SERVER] {response}")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "server_ip",
        help="Dirección IP del servidor al que se desea conectar",
        default="127.0.0.1",
    )
    parser.add_argument(
        "server_port",
        help="Puerto del servidor al que se desea conectar",
        default=32768,
        type=int,
    )
    parser.add_argument(
        "vlc_port",
        help="Puerto de la instancia de VLC del cliente usada para reproducir el stream",
    )
    args = parser.parse_args()

    client = ClientControlTCP(args.server_ip, args.server_port, args.vlc_port)
    try:
        client.run()
    except KeyboardInterrupt:
        client.disconnect()
