import cv2
import time
import os
import sqlite3
import numpy as np
import PIL.Image
import customtkinter as ctk
from datetime import datetime

# --- SETTINGS ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class LoadingScreen(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Splash screen settings
        self.overrideredirect(True)
        width, height = 600, 400
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.attributes("-topmost", True)
        self.configure(fg_color="#000000") 

        # --- LOGO INTEGRATION FROM D: DRIVE ---
        logo_path = r"D:\SEMS\images\open.png"
        try:
            raw_img = PIL.Image.open(logo_path) 
            logo_img = ctk.CTkImage(light_image=raw_img, dark_image=raw_img, size=(580, 280))
            self.logo_label = ctk.CTkLabel(self, image=logo_img, text="")
            self.logo_label.pack(pady=(20, 10))
        except Exception as e:
            self.logo_label = ctk.CTkLabel(self, text="SEMS", font=ctk.CTkFont(size=50, weight="bold"))
            self.logo_label.pack(pady=50)
            print(f"Path Error: Ensure logo is at {logo_path}")

        self.loading_text = ctk.CTkLabel(self, text="Initializing Smart Monitoring...", font=("Arial", 12))
        self.loading_text.pack()

        self.progress = ctk.CTkProgressBar(self, width=400, height=15, corner_radius=5)
        self.progress.pack(pady=20)
        self.progress.set(0)
        self.progress.start()

class SEMSApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Hide main window during loading
        self.withdraw()
        self.loading_window = LoadingScreen(self)

        self.title("SEMS - SMART EXAMINATION MONITORING SYSTEM")
        self.geometry("1100x700")

        # --- DATABASE SETUP (Stored on D: Drive) ---
        self.db_path = r"D:\SEMS\sems_database.db"
        self.db_conn = self.init_db()
        
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # Logic Variables (Clean Multi-Person)
        self.person_data = {} 
        self.SMOOTHING_FACTOR = 0.3 
        self.DEAD_ZONE = 0.15        
        self.RIGHT_SENSITIVITY = 0.20
        self.LEFT_SENSITIVITY = 0.20  
        self.TURN_DURATION = 3.0

        self.setup_main_ui()

        # Show main app after loading
        self.after(4000, self.finish_loading)

    def setup_main_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Sidebar Logo
        try:
            side_raw = PIL.Image.open(r"D:\SEMS\images\logo.png")
            side_logo = ctk.CTkImage(light_image=side_raw, dark_image=side_raw, size=(200, 100))
            self.side_img_label = ctk.CTkLabel(self.sidebar, image=side_logo, text="")
            self.side_img_label.pack(pady=20)
        except:
            self.logo_label = ctk.CTkLabel(self.sidebar, text="SEMS", font=("Arial", 24, "bold"))
            self.logo_label.pack(pady=20)

        self.status_card = ctk.CTkFrame(self.sidebar, fg_color="#2b2b2b")
        self.status_card.pack(pady=10, padx=20, fill="x")
        self.status_label = ctk.CTkLabel(self.status_card, text="MONITORING: 0", text_color="#2ecc71", font=("Arial", 14, "bold"))
        self.status_label.pack(pady=10)

        self.log_box = ctk.CTkTextbox(self.sidebar, width=200, height=250)
        self.log_box.pack(pady=20, padx=10)

        self.video_frame = ctk.CTkFrame(self, fg_color="black")
        self.video_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.video_label = ctk.CTkLabel(self.video_frame, text="") 
        self.video_label.pack(expand=True)

        self.btn_quit = ctk.CTkButton(self.sidebar, text="STOP SYSTEM", fg_color="#e74c3c", command=self.on_closing)
        self.btn_quit.pack(side="bottom", pady=20)

    def finish_loading(self):
        self.loading_window.destroy()
        self.deiconify()
        self.update_frame()

    def init_db(self):
        if not os.path.exists(r"D:\SEMS"): os.makedirs(r"D:\SEMS")
        conn = sqlite3.connect(self.db_path)
        conn.execute('CREATE TABLE IF NOT EXISTS incidents (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, detail TEXT, path TEXT)')
        conn.commit()
        return conn

    def log_incident(self, student_id, direction, frame):
        save_dir = r"D:\SEMS\snapshots"
        if not os.path.exists(save_dir): os.makedirs(save_dir)
        
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(save_dir, f"{student_id}_{ts}.jpg")
        cv2.imwrite(path, frame)
        
        cursor = self.db_conn.cursor()
        cursor.execute("INSERT INTO incidents (timestamp, detail, path) VALUES (?, ?, ?)",
                       (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), f"{student_id}: {direction}", path))
        self.db_conn.commit()
        self.log_box.insert("end", f"[{ts[-6:]}] {student_id} ALERT: {direction}\n")
        self.log_box.see("end")

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.05, 5, minSize=(30, 30))
            self.status_label.configure(text=f"MONITORING: {len(faces)}")

            for i, (x, y, cw, ch) in enumerate(faces):
                student_id = f"S_{i+1}"
                center_x = x + cw // 2
                
                if student_id not in self.person_data:
                    self.person_data[student_id] = {"smooth_x": center_x, "initial_x": center_x, "start_time": None, "alert_active": False}

                curr_smooth = self.person_data[student_id]["smooth_x"]
                new_smooth = (self.SMOOTHING_FACTOR * center_x) + ((1 - self.SMOOTHING_FACTOR) * curr_smooth)
                self.person_data[student_id]["smooth_x"] = new_smooth

                move_x = new_smooth - self.person_data[student_id]["initial_x"]
                move_ratio = move_x / cw 
                
                is_looking_away = False
                status_color = (46, 204, 113) 

                if abs(move_ratio) > self.DEAD_ZONE:
                    if move_ratio > self.RIGHT_SENSITIVITY:
                        direction, is_looking_away = "RIGHT", True
                        status_color = (0, 165, 255) 
                    elif move_ratio < (self.LEFT_SENSITIVITY * -1):
                        direction, is_looking_away = "LEFT", True
                        status_color = (0, 165, 255) 

                if is_looking_away:
                    if self.person_data[student_id]["start_time"] is None:
                        self.person_data[student_id]["start_time"] = time.time()
                    elapsed = time.time() - self.person_data[student_id]["start_time"]
                    if elapsed > self.TURN_DURATION:
                        status_color = (0, 0, 255) 
                        if not self.person_data[student_id]["alert_active"]:
                            self.person_data[student_id]["alert_active"] = True
                            self.log_incident(student_id, direction, frame)
                    cv2.putText(frame, f"{elapsed:.1f}s", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, status_color, 1)
                else:
                    self.person_data[student_id]["start_time"] = None
                    self.person_data[student_id]["alert_active"] = False

                cv2.rectangle(frame, (x, y), (x + cw, y + ch), status_color, 1)
                cv2.putText(frame, student_id, (x, y + ch + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            ctk_img = ctk.CTkImage(PIL.Image.fromarray(rgb_frame), size=(800, 600))
            self.video_label.configure(image=ctk_img)
            self.video_label.image = ctk_img

        self.after(10, self.update_frame)

    def on_closing(self):
        self.cap.release()
        self.db_conn.close()
        self.destroy()

if __name__ == "__main__":
    app = SEMSApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()