import socket, threading

def get_my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

clients = []

def handle_client(conn, p_id):
    try:
        conn.send(f"id|{p_id} ".encode())
        while True:
            data = conn.recv(1024)
            if not data: break
            # Пересилаємо дані всім іншим клієнтам
            for c in clients:
                if c != conn:
                    try: c.send(data)
                    except: pass
    except: pass
    if conn in clients: clients.remove(conn)
    conn.close()

MY_IP = get_my_ip()
PORT = 6666
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', PORT))
s.listen(2)

print("="*30)
print(f"СЕРВЕР ЗАПУЩЕНО!")
print(f"ТВІЙ IP ДЛЯ ГРИ: {MY_IP}")
print(f"ПОРТ: {PORT}")
print("Чекаємо на підключення гравців...")
print("="*30)

while True:
    conn, addr = s.accept()
    if len(clients) < 2:
        pid = len(clients)
        clients.append(conn)
        threading.Thread(target=handle_client, args=(conn, pid), daemon=True).start()
        print(f"Гравець {pid} підключився: {addr}")