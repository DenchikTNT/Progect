import customtkinter as ctk
import tkinter as tk
import socket, threading, time, pygame, os
from PIL import Image, ImageTk

W, H = 1000, 600

class NeonBattle(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("NEON BATTLE PRO")
        self.geometry(f"{W}x{H}")
        self.configure(fg_color="#0d0d0d")
        
        # Ініціалізація звуку та зображень
        pygame.mixer.init()
        self.sounds = {}
        self.bg_image_raw = None
        self.p1_ship_raw = None
        self.p2_ship_raw = None
        
        # Розміри кораблів для відображення
        self.ship_size = (40, 40)
        
        self.load_resources()

        self.my_id = None
        self.score, self.enemy_score = 0, 0
        self.keys = {}
        self.last_dir = (1, 0)
        self.can_move = True
        
        self.setup_menu()

    def load_resources(self):
        """Завантаження всіх медіа-файлів"""
        try:
            # Звуки
            if os.path.exists("music.mp3"):
                pygame.mixer.music.load("music.mp3")
                pygame.mixer.music.set_volume(0.3)
                pygame.mixer.music.play(-1)
            
            if os.path.exists("shoot.wav"): self.sounds['shoot'] = pygame.mixer.Sound("shoot.wav")
            if os.path.exists("hit.wav"): self.sounds['hit'] = pygame.mixer.Sound("hit.wav")
            
            # Зображення
            if os.path.exists("background.png"):
                self.bg_image_raw = Image.open("background.png")
            else:
                print("Файл background.png не знайдено!")

            if os.path.exists("player1_ship.png"):
                self.p1_ship_raw = Image.open("player1_ship.png").resize(self.ship_size, Image.Resampling.LANCZOS)
            else:
                print("Файл player1_ship.png не знайдено! Використовуватиметься прямокутник.")

            if os.path.exists("player2_ship.png"):
                self.p2_ship_raw = Image.open("player2_ship.png").resize(self.ship_size, Image.Resampling.LANCZOS)
            else:
                print("Файл player2_ship.png не знайдено! Використовуватиметься прямокутник.")

        except Exception as e:
            print(f"Помилка завантаження ресурсів: {e}")

    def setup_menu(self):
        self.f = ctk.CTkFrame(self, fg_color="#0d0d0d")
        self.f.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(self.f, text="NEON BATTLE", font=("Impact", 80), text_color="#00f2ff").pack(pady=20)
        self.ip_ent = ctk.CTkEntry(self.f, width=300, height=45, font=("Arial", 20), justify="center")
        self.ip_ent.insert(0, "127.0.0.1") 
        self.ip_ent.pack(pady=10)
        self.btn = ctk.CTkButton(self.f, text="CONNECT", width=250, height=55, font=("Impact", 25), command=self.connect)
        self.btn.pack(pady=20)

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((self.ip_ent.get(), 6666))
            threading.Thread(target=self.recv, daemon=True).start()
            self.f.destroy()
            self.init_game()
        except:
            self.btn.configure(text="IP ERROR")

    def init_game(self):
        self.cv = tk.Canvas(self, bg="#050505", highlightthickness=0)
        self.cv.pack(fill="both", expand=True)
        
        # Створюємо фон (спочатку порожній об'єкт)
        self.bg_canvas_id = self.cv.create_image(0, 0, anchor="nw", tags="bg")
        
        # Примусове перше малювання фону
        self.update() 
        self.resize_bg()

        # Оновлення при зміні розміру
        self.bind("<Configure>", lambda e: self.resize_bg())

        # Очікування ID
        while self.my_id is None:
            self.update()
            time.sleep(0.01)

        # Підготовка зображень кораблів для Canvas
        if self.p1_ship_raw: self.p1_ship_photo = ImageTk.PhotoImage(self.p1_ship_raw)
        if self.p2_ship_raw: self.p2_ship_photo = ImageTk.PhotoImage(self.p2_ship_raw)

        # Стіна
        self.wall = self.cv.create_rectangle(490, 150, 510, 450, fill="#1a1a1a", outline="#00f2ff", tags="obj")
        
        # Позиції та малюнки кораблів
        p_x, e_x = (80, 920) if self.my_id == 0 else (920, 80)
        
        # Створення мого корабля (зображення або прямокутник)
        if self.my_id == 0 and self.p1_ship_raw:
            self.p = self.cv.create_image(p_x, 300, image=self.p1_ship_photo, tags=("obj", "player"))
        elif self.my_id == 1 and self.p2_ship_raw:
            self.p = self.cv.create_image(p_x, 300, image=self.p2_ship_photo, tags=("obj", "player"))
        else:
            p_clr = "#00f2ff" if self.my_id == 0 else "#ff007f"
            self.p = self.cv.create_rectangle(p_x-20, 280, p_x+20, 320, fill=p_clr, outline="white", tags=("obj", "player"))

        # Створення корабля ворога (зображення або прямокутник)
        if self.my_id == 0 and self.p2_ship_raw:
            self.e = self.cv.create_image(e_x, 300, image=self.p2_ship_photo, tags=("obj", "enemy"))
        elif self.my_id == 1 and self.p1_ship_raw:
            self.e = self.cv.create_image(e_x, 300, image=self.p1_ship_photo, tags=("obj", "enemy"))
        else:
            e_clr = "#ff007f" if self.my_id == 0 else "#00f2ff"
            self.e = self.cv.create_rectangle(e_x-20, 280, e_x+20, 320, fill=e_clr, outline="white", tags=("obj", "enemy"))

        self.st = self.cv.create_text(500, 50, text="0 : 0", fill="white", font=("Impact", 50), tags="obj")
        
        self.bind("<KeyPress>", lambda e: self.keys.update({e.keysym.lower(): True}))
        self.bind("<KeyRelease>", lambda e: self.keys.update({e.keysym.lower(): False}))
        self.game_loop()

    def resize_bg(self, event=None):
        """Розтягує фон на все вікно"""
        if self.bg_image_raw:
            w = event.width if event else self.winfo_width()
            h = event.height if event else self.winfo_height()
            if w > 10 and h > 10:
                img = self.bg_image_raw.resize((w, h), Image.Resampling.LANCZOS)
                self.bg_photo = ImageTk.PhotoImage(img)
                self.cv.itemconfig(self.bg_canvas_id, image=self.bg_photo)
                self.cv.tag_lower("bg")

    def get_coords(self, item):
        """Універсальний метод отримання координат для зображень та прямокутників"""
        item_type = self.cv.type(item)
        if item_type == "image":
            x, y = self.cv.coords(item)
            return [x - self.ship_size[0]/2, y - self.ship_size[1]/2, x + self.ship_size[0]/2, y + self.ship_size[1]/2]
        else:
            return self.cv.coords(item)

    def game_loop(self):
        if self.can_move:
            dx, dy = 0, 0
            s = 7
            if self.keys.get('w') or self.keys.get('up'): dy = -s; self.last_dir = (0, -1)
            elif self.keys.get('s') or self.keys.get('down'): dy = s; self.last_dir = (0, 1)
            elif self.keys.get('a') or self.keys.get('left'): dx = -s; self.last_dir = (-1, 0)
            elif self.keys.get('d') or self.keys.get('right'): dx = s; self.last_dir = (1, 0)
            
            if dx or dy:
                self.cv.move(self.p, dx, dy)
                pos = self.get_coords(self.p)
                win_w, win_h = self.winfo_width(), self.winfo_height()
                
                # Перевірка стіни та меж
                if self.wall in self.cv.find_overlapping(*pos) or pos[0]<0 or pos[2]>win_w or pos[1]<0 or pos[3]>win_h:
                    self.cv.move(self.p, -dx, -dy)
                
                curr_pos = self.cv.coords(self.p)
                # Передаємо центральні координати (x, y)
                self.send(f"m|{curr_pos[0]}|{curr_pos[1]}")
                
            if self.keys.get('space'):
                self.shoot()
                self.keys['space'] = False
        self.after(16, self.game_loop)

    def shoot(self):
        if 'shoot' in self.sounds: self.sounds['shoot'].play()
        pos = self.cv.coords(self.p)
        # pos - це центр корабля (x, y) для зображень
        cx, cy = pos[0], pos[1]
        b_clr = "#00f2ff" if self.my_id == 0 else "#ff007f"
        b = self.cv.create_oval(cx-4, cy-4, cx+4, cy+4, fill="white", outline=b_clr, tags="bullet")
        self.send(f"s|{cx}|{cy}|{self.last_dir[0]}|{self.last_dir[1]}")
        threading.Thread(target=self.bullet_move, args=(b, self.last_dir, True), daemon=True).start()

    def bullet_move(self, b, d, mine):
        for _ in range(70):
            time.sleep(0.015)
            try:
                self.cv.move(b, d[0]*16, d[1]*16)
                c = self.cv.coords(b)
                hits = self.cv.find_overlapping(*c)
                if self.wall in hits: break
                target = self.e if mine else self.p
                if target in hits:
                    if 'hit' in self.sounds: self.sounds['hit'].play()
                    if mine:
                        self.score += 1
                        self.send("hit|")
                        if self.score >= 3: self.over("VICTORY")
                    self.update_ui()
                    break
            except: break
        self.cv.delete(b)

    def recv(self):
        while True:
            try:
                data = self.sock.recv(1024).decode()
                if not data: break
                for pk in data.split(' '):
                    if not pk: continue
                    d = pk.split('|')
                    if d[0] == 'id': self.my_id = int(d[1])
                    elif d[0] == 'm':
                        # Оновлюємо позицію ворога (d[1], d[2] - це центральні координати x, y)
                        self.cv.coords(self.e, float(d[1]), float(d[2]))
                    elif d[0] == 's':
                        e_b_clr = "#ff007f" if self.my_id == 0 else "#00f2ff"
                        eb = self.cv.create_oval(float(d[1])-4, float(d[2])-4, float(d[1])+4, float(d[2])+4, fill="white", outline=e_b_clr, tags="bullet")
                        threading.Thread(target=self.bullet_move, args=(eb, (float(d[3]), float(d[4])), False), daemon=True).start()
                    elif d[0] == 'hit':
                        if 'hit' in self.sounds: self.sounds['hit'].play()
                        self.enemy_score += 1
                        self.update_ui()
                        if self.enemy_score >= 3: self.over("DEFEAT")
            except: break

    def update_ui(self):
        self.cv.itemconfig(self.st, text=f"{self.score} : {self.enemy_score}")

    def over(self, txt):
        self.can_move = False
        self.cv.create_text(self.winfo_width()/2, self.winfo_height()/2, text=txt, fill="yellow", font=("Impact", 90), tags="end")
        self.after(3000, self.reset)

    def reset(self):
        self.score, self.enemy_score = 0, 0
        self.cv.delete("end")
        self.cv.delete("bullet")
        self.update_ui()
        p_x = 80 if self.my_id == 0 else self.winfo_width() - 80
        # Скидання позиції (x, y) центра корабля
        self.cv.coords(self.p, p_x, 300)
        self.can_move = True

    def send(self, m):
        try: self.sock.send((m + " ").encode())
        except: pass

if __name__ == "__main__":
    app = NeonBattle()
    app.mainloop()