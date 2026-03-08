import socket
import threading

HOST = '192.168.0.174' 
PORT = 6666

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(2)

clients = []
lock = threading.Lock()

def broadcast(msg, sender):
    with lock:
        for c in clients:
            if c != sender:
                try: c.send(msg)
                except: clients.remove(c)

def handle(conn, addr):
    print(f"[+] Игрок подключен: {addr}")
    with lock: clients.append(conn)
    while True:
        try:
            data = conn.recv(1024)
            if not data: break
            broadcast(data, conn)
        except: break
    with lock: 
        if conn in clients: clients.remove(conn)
    conn.close()

print(f"--- SERVER STARTED ---")
while True:
    conn, addr = server.accept()
    threading.Thread(target=handle, args=(conn, addr), daemon=True).start()