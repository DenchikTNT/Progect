import socket, threading

def get_my_ip():
    # Автоматично знаходить твою IP адресу в мережі
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.connect(('8.8.8.8', 80)); ip = s.getsockname()[0]
    except: ip = '192.168.31.112'
    finally: s.close()
    return ip

clients = []

def handle_client(conn, p_id):
    try:
        conn.send(f"id|{p_id} ".encode())
        while True:
            data = conn.recv(1024)
            if not data: break
            for c in clients:
                if c != conn: c.send(data)
    except: pass
    if conn in clients: clients.remove(conn)
    conn.close()

MY_IP = get_my_ip()
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('192.168.31.112', 6666))
s.listen(2)

print("="*30)
print(f"СЕРВЕР ЗАПУЩЕНО!")
print(f"ТВІЙ IP ДЛЯ ГРИ: {MY_IP}")
print(f"Скажи цей номер другому гравцю")
print("="*30)

while True:
    conn, addr = s.accept()
    if len(clients) < 2:
        pid = len(clients)
        clients.append(conn)
        threading.Thread(target=handle_client, args=(conn, pid), daemon=True).start()
