import customtkinter as ctk
import tkinter as tk
import socket
import threading
import time

class StandoffClient(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Vision Studio: Standoff 2D")
        self.geometry("900x650")
        self.configure(fg_color="#1a1a1a")

        # Игровые параметры
        self.hp = 100
        self.enemy_hp = 100
        self.last_dir = (1, 0)
        self.weapons = {
            "Glock": {"damage": 15, "speed": 15, "color": "gray"},
            "AK-47": {"damage": 25, "speed": 22, "color": "orange"},
            "AWM": {"damage": 100, "speed": 40, "color": "green"}
        }
        self.current_weapon = self.weapons["AK-47"]

        # Окно Меню
        self.show_menu()

    def show_menu(self):
        self.menu_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=15)
        self.menu_frame.pack(expand=True, padx=50, pady=50)

        ctk.CTkLabel(self.menu_frame, text="VISION STUDIO", font=("Impact", 40), text_color="#ff8c00").pack(pady=20)
        
        self.weapon_var = ctk.StringVar(value="AK-47")
        self.weapon_menu = ctk.CTkOptionMenu(self.menu_frame, values=["Glock", "AK-47", "AWM"], 
                                             variable=self.weapon_var, fg_color="#ff8c00", button_hover_color="#cc7000")
        self.weapon_menu.pack(pady=10)

        self.btn_connect = ctk.CTkButton(self.menu_frame, text="ПОДКЛЮЧИТЬСЯ", command=self.connect_server, 
                                         font=("Arial", 16, "bold"), fg_color="#1f6aa5")
        self.btn_connect.pack(pady=20)

    def connect_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect(('127.0.0.1', 5555))
            self.current_weapon = self.weapons[self.weapon_var.get()]
            self.start_game_ui()
        except:
            self.btn_connect.configure(text="СЕРВЕР ОФФЛАЙН")

    def start_game_ui(self):
        self.menu_frame.pack_forget()
        self.canvas = tk.Canvas(self, width=900, height=600, bg="#121212", highlightthickness=0)
        self.canvas.pack()

        # Игроки и полоски HP
        self.player = self.canvas.create_rectangle(100, 300, 140, 340, fill="#3498db", outline="white")
        self.enemy = self.canvas.create_rectangle(750, 300, 790, 340, fill="#e74c3c", outline="white")
        
        self.p_hp_bar = self.canvas.create_rectangle(100, 290, 140, 295, fill="#2ecc71")
        self.e_hp_bar = self.canvas.create_rectangle(750, 290, 790, 295, fill="#2ecc71")

        self.bind("<KeyPress>", self.handle_move)
        self.bind("<space>", lambda e: self.shoot())
        
        threading.Thread(target=self.receive_data, daemon=True).start()

    def handle_move(self, event):
        key = event.keysym.lower()
        dx, dy = 0, 0
        step = 12
        if key == 'w': dy = -step; self.last_dir = (0, -1)
        elif key == 's': dy = step; self.last_dir = (0, 1)
        elif key == 'a': dx = -step; self.last_dir = (-1, 0)
        elif key == 'd': dx = step; self.last_dir = (1, 0)

        self.canvas.move(self.player, dx, dy)
        self.canvas.move(self.p_hp_bar, dx, dy)
        pos = self.canvas.coords(self.player)
        self.send_msg(f"m|{pos[0]}|{pos[1]}")

    def shoot(self):
        p_pos = self.canvas.coords(self.player)
        x = (p_pos[0] + p_pos[2]) / 2
        y = (p_pos[1] + p_pos[3]) / 2
        
        bullet = self.canvas.create_oval(x-4, y-4, x+4, y+4, fill=self.current_weapon["color"])
        self.send_msg(f"s|{x}|{y}|{self.last_dir[0]}|{self.last_dir[1]}|{self.current_weapon['color']}")
        threading.Thread(target=self.bullet_logic, args=(bullet, self.last_dir, True)).start()

    def bullet_logic(self, bullet, direction, is_mine):
        for _ in range(40):
            time.sleep(0.02)
            self.canvas.move(bullet, direction[0]*self.current_weapon["speed"], direction[1]*self.current_weapon["speed"])
            b_pos = self.canvas.coords(bullet)
            
            target = self.enemy if is_mine else self.player
            t_pos = self.canvas.coords(target)

            if b_pos[0] > t_pos[0] and b_pos[2] < t_pos[2] and b_pos[1] > t_pos[1] and b_pos[3] < t_pos[3]:
                self.canvas.delete(bullet)
                if is_mine:
                    self.enemy_hp -= self.current_weapon["damage"]
                    self.send_msg(f"h|{self.enemy_hp}")
                    self.update_bars()
                return
        self.canvas.delete(bullet)

    def update_bars(self):
        # Логика полосок HP
        if self.enemy_hp <= 0: self.canvas.create_text(450, 300, text="ПОБЕДА!", fill="orange", font=("Impact", 60))

    def send_msg(self, msg):
        try: self.sock.send(msg.encode())
        except: pass

    def receive_data(self):
        while True:
            try:
                data = self.sock.recv(1024).decode().split('|')
                if data[0] == 'm':
                    x, y = float(data[1]), float(data[2])
                    self.canvas.coords(self.enemy, x, y, x+40, y+40)
                    self.canvas.coords(self.e_hp_bar, x, y-10, x+40, y-5)
                elif data[0] == 's':
                    bx, by, dx, dy, col = float(data[1]), float(data[2]), float(data[3]), float(data[4]), data[5]
                    bullet = self.canvas.create_oval(bx-4, by-4, bx+4, by+4, fill=col)
                    threading.Thread(target=self.bullet_logic, args=(bullet, (dx, dy), False)).start()
                elif data[0] == 'h':
                    self.hp = int(data[1])
                    if self.hp <= 0: self.canvas.create_text(450, 300, text="ТЫ ПРОИГРАЛ", fill="red", font=("Impact", 60))
            except: break

if __name__ == "__main__":
    app = StandoffClient()
    app.mainloop()