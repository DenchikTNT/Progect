import customtkinter as ctk
import tkinter as tk
import socket, threading, time

W, H = 1000, 600

class NeonBattle(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("NEON BATTLE PRO")
        self.geometry(f"{W}x{H}")
        self.configure(fg_color="#0d0d0d")
        self.my_id = None
        self.score, self.enemy_score = 0, 0
        self.keys = {}
        self.last_dir = (1, 0)
        self.can_move = True
        self.setup_menu()

    def setup_menu(self):
        self.f = ctk.CTkFrame(self, fg_color="#0d0d0d")
        self.f.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(self.f, text="NEON BATTLE", font=("Impact", 80), text_color="#00f2ff").pack(pady=20)
        
        self.ip_ent = ctk.CTkEntry(self.f, width=300, height=45, font=("Arial", 20), justify="center")
        self.ip_ent.insert(0, "192.168.0.174") # Введи тут IP з вікна сервера
        self.ip_ent.pack(pady=10)
        
        self.btn = ctk.CTkButton(self.f, text="CONNECT", width=250, height=55, 
                                 font=("Impact", 25), fg_color="#00f2ff", text_color="#000", command=self.connect)
        self.btn.pack(pady=20)

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.ip_ent.get(), 6666))
            threading.Thread(target=self.recv, daemon=True).start()
            self.f.destroy(); self.init_game()
        except: self.btn.configure(text="IP ERROR")

    def init_game(self):
        self.cv = tk.Canvas(self, bg="#050505", highlightthickness=0); self.cv.pack(fill="both", expand=True)
        while self.my_id is None: time.sleep(0.05)

        self.wall = self.cv.create_rectangle(490, 150, 510, 450, fill="#1a1a1a", outline="#00f2ff")
        
        # Початкові позиції
        p_x, e_x = (80, 920) if self.my_id == 0 else (920, 80)
        p_clr, e_clr = ("#00f2ff", "#ff007f") if self.my_id == 0 else ("#ff007f", "#00f2ff")

        self.p = self.cv.create_rectangle(p_x, 280, p_x+35, 315, fill=p_clr, outline="white")
        self.e = self.cv.create_rectangle(e_x, 280, e_x+35, 315, fill=e_clr, outline="white")
        self.st = self.cv.create_text(500, 50, text="0 : 0", fill="white", font=("Impact", 50))
        
        self.bind("<KeyPress>", lambda e: self.keys.update({e.keysym.lower(): True}))
        self.bind("<KeyRelease>", lambda e: self.keys.update({e.keysym.lower(): False}))
        self.game_loop()

    def game_loop(self):
        if self.can_move:
            dx, dy = 0, 0
            s = 8
            if self.keys.get('w') or self.keys.get('up'): dy = -s; self.last_dir = (0, -1)
            elif self.keys.get('s') or self.keys.get('down'): dy = s; self.last_dir = (0, 1)
            elif self.keys.get('a') or self.keys.get('left'): dx = -s; self.last_dir = (-1, 0)
            elif self.keys.get('d') or self.keys.get('right'): dx = s; self.last_dir = (1, 0)
            
            if dx or dy:
                self.cv.move(self.p, dx, dy)
                pos = self.cv.coords(self.p)
                if self.wall in self.cv.find_overlapping(*pos) or pos<0 or pos>W or pos<0 or pos>H:
                    self.cv.move(self.p, -dx, -dy)
                new_p = self.cv.coords(self.p)
                self.send(f"m|{new_p}|{new_p}")
            if self.keys.get('space'): self.shoot(); self.keys['space'] = False
        self.after(16, self.game_loop)

    def shoot(self):
        p = self.cv.coords(self.p)
        cx, cy = (p+p)/2, (p+p)/2 # Стріляємо рівно з середини
        b = self.cv.create_oval(cx-4, cy-4, cx+4, cy+4, fill="white", outline="#00f2ff")
        self.send(f"s|{cx}|{cy}|{self.last_dir}|{self.last_dir}")
        threading.Thread(target=self.bullet_move, args=(b, self.last_dir, True), daemon=True).start()

    def bullet_move(self, b, d, mine):
        for _ in range(60):
            time.sleep(0.015)
            try:
                self.cv.move(b, d*20, d*20)
                c = self.cv.coords(b); hits = self.cv.find_overlapping(*c)
                if self.wall in hits: break
                target = self.e if mine else self.p
                if target in hits:
                    if mine:
                        self.score += 1; self.send("hit|")
                        if self.score >= 3: self.over("VICTORY")
                    self.update_ui(); self.cv.delete(b); return
            except: break
        self.cv.delete(b)

    def recv(self):
        while True:
            try:
                raw = self.sock.recv(1024).decode().split(' ')
                for pk in raw:
                    if not pk: continue
                    d = pk.split('|')
                    if d == 'id': self.my_id = int(d)
                    elif d == 'm': self.cv.coords(self.e, float(d), float(d), float(d)+35, float(d)+35)
                    elif d == 's':
                        eb = self.cv.create_oval(float(d)-4, float(d)-4, float(d)+4, float(d)+4, fill="red")
                        threading.Thread(target=self.bullet_move, args=(eb, (float(d), float(d)), False), daemon=True).start()
                    elif d == 'hit':
                        self.enemy_score += 1; self.update_ui()
                        if self.enemy_score >= 3: self.over("DEFEAT")
            except: break

    def update_ui(self):
        self.cv.itemconfig(self.st, text=f"{self.score} : {self.enemy_score}")

    def over(self, txt):
        self.can_move = False
        self.cv.create_text(500, 300, text=txt, fill="yellow", font=("Impact", 90), tags="end")
        self.after(3000, self.reset)

    def reset(self):
        self.score, self.enemy_score = 0, 0
        self.cv.delete("end"); self.update_ui()
        p_x = 80 if self.my_id == 0 else 920
        e_x = 920 if self.my_id == 0 else 80
        self.cv.coords(self.p, p_x, 280, p_x+35, 315)
        self.cv.coords(self.e, e_x, 280, e_x+35, 315)
        self.can_move = True

    def send(self, m):
        try: self.sock.send((m + " ").encode())
        except: pass

if __name__ == "__main__":
    NeonBattle().mainloop()
