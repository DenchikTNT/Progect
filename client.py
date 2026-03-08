import customtkinter as ctk
import tkinter as tk
import socket
import threading
import time
import random

PORT = 6666
MAP_WIDTH, MAP_HEIGHT = 1000, 650

class NeonProDuel(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ULTRA NEON DUEL")
        self.geometry(f"{MAP_WIDTH}x{MAP_HEIGHT}")
        
        self.score, self.enemy_score = 0, 0
        self.last_dir = (1, 0)
        self.can_move = True
        
        # --- СЛОВАРЬ НАЖАТЫХ КЛАВИШ ---
        self.pressed_keys = {} 
        
        self.show_launcher()

    def show_launcher(self):
        if hasattr(self, 'f'): self.f.destroy()
        self.f = ctk.CTkFrame(self, fg_color="#0a0a0a", border_width=2, border_color="#00f2ff")
        self.f.pack(expand=True, padx=50, pady=50)
        ctk.CTkLabel(self.f, text="SMOOTH DUEL", font=("Impact", 50), text_color="#00f2ff").pack(pady=20)
        self.ip = ctk.CTkEntry(self.f, placeholder_text="IP СЕРВЕРА", width=250)
        self.ip.insert(0, "192.168.0.174")
        self.ip.pack(pady=10)
        self.btn = ctk.CTkButton(self.f, text="В БОЙ", command=self.connect)
        self.btn.pack(pady=20)

    def connect(self):
        threading.Thread(target=self._try, args=(self.ip.get(),), daemon=True).start()

    def _try(self, ip):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, PORT))
            self.after(0, self.start_game)
        except: pass

    def start_game(self):
        self.f.pack_forget()
        self.cv = tk.Canvas(self, width=MAP_WIDTH, height=MAP_HEIGHT, bg="#050505", highlightthickness=0)
        self.cv.pack()

        # Лабиринт
        self.walls = [
            self.cv.create_rectangle(200, 100, 230, 300, fill="#1a1a1a", outline="#00f2ff"),
            self.cv.create_rectangle(770, 350, 800, 550, fill="#1a1a1a", outline="#00f2ff"),
            self.cv.create_rectangle(485, 250, 515, 400, fill="#1a1a1a", outline="#00f2ff")
        ]

        self.draw_p(80, 310, "#00f2ff", "player")
        self.draw_p(890, 310, "#ff007f", "enemy")
        self.ui_score = self.cv.create_text(500, 35, text="0 : 0", fill="white", font=("Impact", 30))
        
        # --- БИНДЫ НА НАЖАТИЕ И ОТПУСКАНИЕ ---
        self.bind("<KeyPress>", self.key_down)
        self.bind("<KeyRelease>", self.key_up)
        
        threading.Thread(target=self.recv, daemon=True).start()
        self.game_loop() # Запуск постоянного цикла обновления

    def draw_p(self, x, y, color, tag):
        self.cv.create_rectangle(x, y, x+30, y+35, fill=color, outline="white", tags=(tag, f"{tag}_body"))
        self.cv.create_rectangle(x+5, y-15, x+25, y, fill="#000", outline=color, width=2, tags=(tag, f"{tag}_head"))
        self.cv.create_rectangle(x+25, y+12, x+45, y+22, fill="#555", outline="white", tags=(tag, f"{tag}_gun"))

    def key_down(self, e):
        self.pressed_keys[e.keysym.lower()] = True

    def key_up(self, e):
        self.pressed_keys[e.keysym.lower()] = False

    def game_loop(self):
        """Профессиональный игровой цикл: работает 60 раз в секунду"""
        if self.can_move:
            dx, dy = 0, 0
            speed = 8 # Скорость стала меньше, но движений больше (плавность!)
            
            # Управление Игрока 1 (WASD) и Игрока 2 (Стрелки)
            if self.pressed_keys.get('w') or self.pressed_keys.get('up'): dy = -speed; self.last_dir = (0, -1)
            if self.pressed_keys.get('s') or self.pressed_keys.get('down'): dy = speed; self.last_dir = (0, 1)
            if self.pressed_keys.get('a') or self.pressed_keys.get('left'): dx = -speed; self.last_dir = (-1, 0)
            if self.pressed_keys.get('d') or self.pressed_keys.get('right'): dx = speed; self.last_dir = (1, 0)
            
            if self.pressed_keys.get('space') or self.pressed_keys.get('return'):
                self.shoot()
                self.pressed_keys['space'] = False # Чтобы не спамить пулями
                self.pressed_keys['return'] = False

            if dx != 0 or dy != 0:
                self.cv.move("player", dx, dy)
                pos = self.cv.coords(self.cv.find_withtag("player_body")[0])
                # Проверка столкновения
                if any(w in self.cv.find_overlapping(*pos) for w in self.walls):
                    self.cv.move("player", -dx, -dy)
                
                self.update_gun("player", dx, dy)
                pos = self.cv.coords(self.cv.find_withtag("player_body")[0])
                self.send(f"m|{pos[0]}|{pos[1]}|{dx}|{dy}")

        self.after(16, self.game_loop) # ~60 FPS

    def update_gun(self, tag, dx, dy):
        p_id = self.cv.find_withtag(f"{tag}_body")[0]
        pos = self.cv.coords(p_id)
        x, y = pos[0], pos[1]
        gun = self.cv.find_withtag(f"{tag}_gun")[0]
        if dx > 0: self.cv.coords(gun, x+25, y+12, x+45, y+22)
        elif dx < 0: self.cv.coords(gun, x-15, y+12, x+5, y+22)
        elif dy < 0: self.cv.coords(gun, x+10, y-25, x+20, y-5)
        elif dy > 0: self.cv.coords(gun, x+10, y+35, x+20, y+55)

    def shoot(self):
        gun_id = self.cv.find_withtag("player_gun")[0]
        gp = self.cv.coords(gun_id)
        x, y = (gp[0]+gp[2])/2, (gp[1]+gp[3])/2
        b = self.cv.create_oval(x-4, y-4, x+4, y+4, fill="#00f2ff", outline="white")
        self.send(f"s|{x}|{y}|{self.last_dir[0]}|{self.last_dir[1]}")
        threading.Thread(target=self.bullet_phys, args=(b, self.last_dir, True), daemon=True).start()

    def bullet_phys(self, b, d, mine):
        for _ in range(80):
            time.sleep(0.01)
            try:
                self.cv.move(b, d[0]*25, d[1]*25)
                co = self.cv.coords(b)
                hits = self.cv.find_overlapping(*co)
                if any(w in hits for w in self.walls): break
                target = "enemy" if mine else "player"
                for item in hits:
                    if target in self.cv.gettags(item):
                        if mine: self.send("win|")
                        self.cv.delete(b); return
            except: break
        self.cv.delete(b)

    def recv(self):
        while True:
            try:
                data = self.sock.recv(1024).decode()
                for pk in data.split(' '):
                    if not pk: continue
                    d = pk.split('|')
                    if d[0] == 'm':
                        x, y, dx, dy = float(d[1]), float(d[2]), float(d[3]), float(d[4])
                        self.cv.coords(self.cv.find_withtag("enemy_body")[0], x, y, x+30, y+35)
                        self.cv.coords(self.cv.find_withtag("enemy_head")[0], x+5, y-15, x+25, y)
                        self.update_gun("enemy", dx, dy)
                    elif d[0] == 's':
                        eb = self.cv.create_oval(float(d[1])-4, float(d[2])-4, float(d[1])+4, float(d[2])+4, fill="#ff007f")
                        threading.Thread(target=self.bullet_phys, args=(eb, (float(d[3]), float(d[4])), False), daemon=True).start()
                    elif d[0] == 'win':
                        self.enemy_score += 1
                        self.flash("ПРОИГРЫШ!", "#ff007f")
                    elif d[0] == 'iwin':
                        self.score += 1
                        self.flash("ПОБЕДА!", "#00f2ff")
            except: break

    def flash(self, txt, clr):
        self.can_move = False
        self.cv.itemconfig(self.ui_score, text=f"{self.score} : {self.enemy_score}")
        m = self.cv.create_text(500, 325, text=txt, fill=clr, font=("Impact", 80), tags="msg")
        self.pressed_keys = {} # Сброс клавиш
        self.after(1500, self.reset)

    def reset(self):
        self.cv.delete("msg")
        self.cv.coords(self.cv.find_withtag("player_body")[0], 80, 310, 110, 345)
        self.cv.coords(self.cv.find_withtag("player_head")[0], 85, 295, 105, 310)
        self.update_gun("player", 1, 0)
        self.send("m|80|310|1|0")
        self.can_move, self.last_dir = True, (1, 0)

    def send(self, m):
        if m == "win|": m = "iwin|"
        try: self.sock.send((m + " ").encode())
        except: pass

if __name__ == "__main__":
    NeonProDuel().mainloop()