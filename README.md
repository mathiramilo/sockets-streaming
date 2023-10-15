## Sockets Streaming

Servidor de streaming de video y cliente que consume el video con determinadas acciones de control. Proyecto para el curso de Redes de Computadoras de la Facultad de Ingenieria UDELAR.

### Instrucciones

1. Ejecutar el servidor con el comando `python server.py` en Windows o `python3 server.py` en Linux.
2. Iniciar el streaming de video con la herramienta VLC hacia el servidor, para esto se debe ejecutar el sigiuente comando por consola `vlc -vvv videoplayback.mp4 --sout "#transcode{vcodec=mp4v,acodec=mpga}:rtp{proto=udp, mux=ts, dst=127.0.0.1, port=65534}" --loop --ttl 1`
3. Iniciar el cliente VLC con el comando `vlc rtp://<ip_cliente>:<puerto_elegido>`.
4. Ejecutar el cliente con el comando `python client.py <ip_servidor> <puerto_servidor> <puerto_vlc>`.
5. Enviar comandos del cliente al servidor para controlar el streaming.
