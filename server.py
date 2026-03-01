import socket
import threading

# Настройки подключения
HOST = '192.168.0.174'
PORT = 6666

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(2)

clients = []

def broadcast(message, current_conn):
    """Отправка сообщения всем, кроме отправителя"""
    for client in clients:
        if client != current_conn:
            try:
                client.send(message)
            except:
                clients.remove(client)

def handle_client(conn, addr):
    print(f"[LOG] Игрок {addr} вошел в сеть")
    while True:
        try:
            data = conn.recv(1024)
            if not data: break
            broadcast(data, conn)
        except:
            break
    print(f"[LOG] Игрок {addr} покинул игру")
    clients.remove(conn)
    conn.close()

print("--- СЕРВЕР стрилялки ЗАПУЩЕН ---")
while True:
    conn, addr = server.accept()
    clients.append(conn)
    threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()