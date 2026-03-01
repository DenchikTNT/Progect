import customtkinter as ctk
import tkinter as tk
import socket
import threading
import time

HOST = '192.168.0.174'
PORT =6666

def run_internal_server():
    """Запускает сервер, если он еще не запущен"""
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((HOST, PORT))
        server.listen(2)
        clients = []

        def broadcast(msg, sender):
            for c in clients:
                if c != sender:
                    try: c.send(msg)
                    except: clients.remove(c)

        def handle(conn):
            while True:
                try:
                    data = conn.recv(1024)
                    if not data: break
                    broadcast(data, conn)
                except: break
            conn.close()

        while True:
            conn, addr = server.accept()
            clients.append(conn)
            threading.Thread(target=handle, args=(conn,), daemon=True).start()
    except:
        pass 


class VisionShooter(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VISION STUDIO: Standoff 2D")
        self.geometry("900x600")
        self.configure(fg_color="#101217")

        self.hp = 100
        self.enemy_hp = 100
        self.last_dir = (1, 0) 
        self.sock = None

        self.menu = ctk.CTkFrame(self, corner_radius=20, fg_color="#1c1f26")
        self.menu.pack(expand=True, padx=50, pady=50)

        ctk.CTkLabel(self.menu, text="VISION STUDIO", font=("Impact", 45), text_color="#ff8c00").pack(pady=20)
        
        self.info = ctk.CTkLabel(self.menu, text="Запустите 2 копии этого файла", font=("Arial", 14))
        self.info.pack(pady=5)

        self.btn = ctk.CTkButton(self.menu, text="ВСТУПИТЬ В БОЙ", font=("Arial", 20, "bold"),
                                 fg_color="#ff8c00", hover_color="#cc7000", height=50,
                                 command=self.start_connection)
        self.btn.pack(pady=30, padx=60)

    def start_connection(self):
       
        threading.Thread(target=run_internal_server, daemon=True).start()
        time.sleep(0.5)

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))
            self.setup_game_field()
        except:
            self.info.configure(text="Ошибка подключения!", text_color="red")

    def setup_game_field(self):
        self.menu.pack_forget()
        
       
        self.canvas = tk.Canvas(self, width=900, height=600, bg="#12141a", highlightthickness=0)
        self.canvas.pack()

        self.walls = [
            self.canvas.create_rectangle(400, 150, 500, 450, fill="#2d333b", outline="#444c56")
        ]

        
        self.player = self.canvas.create_rectangle(100, 280, 140, 320, fill="#3498db", outline="white", width=2)
        self.enemy = self.canvas.create_rectangle(760, 280, 800, 320, fill="#e74c3c", outline="white", width=2)
        
        
        self.p_hp_bar = self.canvas.create_rectangle(100, 270, 140, 275, fill="#2ecc71")
        self.e_hp_bar = self.canvas.create_rectangle(760, 270, 800, 275, fill="#2ecc71")

        
        self.bind("<KeyPress>", self.move)
        self.bind("<space>", lambda e: self.shoot())
        
        
        threading.Thread(target=self.receive, daemon=True).start()

    def move(self, event):
        key = event.keysym.lower()
        dx, dy = 0, 0
        speed = 15

        if key in ['w', 'up']: dy = -speed; self.last_dir = (0, -1)
        elif key in ['s', 'down']: dy = speed; self.last_dir = (0, 1)
        elif key in ['a', 'left']: dx = -speed; self.last_dir = (-1, 0)
        elif key in ['d', 'right']: dx = speed; self.last_dir = (1, 0)

    
        old_pos = self.canvas.coords(self.player)
        self.canvas.move(self.player, dx, dy)
        self.canvas.move(self.p_hp_bar, dx, dy)
        
        new_pos = self.canvas.coords(self.player)
        if any(self.canvas.find_overlapping(*new_pos) and w in self.canvas.find_overlapping(*new_pos) for w in self.walls):
            self.canvas.coords(self.player, *old_pos)
            self.canvas.coords(self.p_hp_bar, old_pos[0], old_pos[1]-10, old_pos[2], old_pos[1]-5)
        
        p_pos = self.canvas.coords(self.player)
        self.send(f"m|{p_pos[0]}|{p_pos[1]}")

    def shoot(self):
        pos = self.canvas.coords(self.player)
        x, y = (pos[0]+pos[2])/2, (pos[1]+pos[3])/2
        bullet = self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="yellow")
        
        self.send(f"s|{x}|{y}|{self.last_dir[0]}|{self.last_dir[1]}")
        threading.Thread(target=self.bullet_physics, args=(bullet, self.last_dir, True)).start()

    def bullet_physics(self, bullet, direction, is_mine):
        for _ in range(40):
            time.sleep(0.02)
            self.canvas.move(bullet, direction)