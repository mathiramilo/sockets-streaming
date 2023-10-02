from enum import StrEnum


class ControlStream(StrEnum):
    CONNECT = "CONECTAR"
    INTERRUPT = "INTERRUMPIR"
    CONTINUE = "CONTINUAR"
    DISCONNECT = "DESCONECTAR"
