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

class SEMSApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SEMS - SMART EXAMINATION MONITORING SYSTEM")
        self.geometry("1200x800")

        # --- DATABASE SETUP ---
        # NOTE: If you still get a 'column detail' error, delete D:\SEMS\sems_database.db manually.
        self.db_path = r"D:\SEMS\sems_database.db"
        self.db_conn = self.init_db() 
        
        # Detector Setup
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Camera Setup
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # Logic Variables for Clear Motion Detection
        self.person_data = {} 
        self.SMOOTHING_FACTOR = 0.3 # Lower = smoother, higher = faster response
        self.DEAD_ZONE = 0.15      # Ignore head shifts < 15% of face width
        self.RIGHT_SENSITIVITY = 0.20
        self.LEFT_SENSITIVITY = 0.20  
        self.TURN_DURATION = 3.0

        self.setup_main_ui()
        self.update_frame()

    def init_db(self):
        """Creates database and ensures column names match logic."""
        if not os.path.exists(r"D:\SEMS"): 
            os.makedirs(r"D:\SEMS")
        
        conn = sqlite3.connect(self.db_path)
        # Fixes the 'detail' column error
        conn.execute('''CREATE TABLE IF NOT EXISTS incidents 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         timestamp TEXT, 
                         detail TEXT, 
                         path TEXT)''')
        conn.commit()
        return conn

    def setup_main_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR (Clean UI) ---
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0, fg_color="#121212")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Logo Integration
        try:
            logo_path = r"D:\SEMS\images\logo.png"
            raw_img = PIL.Image.open(logo_path)
            logo_img = ctk.CTkImage(light_image=raw_img, dark_image=raw_img, size=(240, 120))
            self.logo_label = ctk.CTkLabel(self.sidebar, image=logo_img, text="")
            self.logo_label.pack(pady=(30, 10))
        except:
            self.logo_label = ctk.CTkLabel(self.sidebar, text="SEMS", font=("Arial", 30, "bold"))
            self.logo_label.pack(pady=30)

        # --- SYSTEM STATUS SECTION ---
        self.status_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.status_container.pack(pady=20, padx=25, fill="x")

        self.line = ctk.CTkFrame(self.status_container, width=2, fg_color="#FFFFFF")
        self.line.pack(side="left", padx=(0, 15), fill="y")

        self.status_text_inner = ctk.CTkFrame(self.status_container, fg_color="transparent")
        self.status_text_inner.pack(side="left")

        ctk.CTkLabel(self.status_text_inner, text="SYSTEM STATUS", 
                     font=ctk.CTkFont(size=14, weight="bold"), 
                     anchor="w", text_color="#FFFFFF").pack(fill="x")

        self.status_label = ctk.CTkLabel(self.status_text_inner, text="SYNCHRONIZED", 
                                         text_color="#2ecc71", font=("Arial", 11), anchor="w")
        self.status_label.pack(fill="x")

        self.count_label = ctk.CTkLabel(self.sidebar, text="ACTIVE USERS: 0", 
                                        font=("Arial", 12, "bold"), text_color="#888888")
        self.count_label.pack(pady=(5, 0))

        # --- LOG BOX ---
        self.log_box = ctk.CTkTextbox(self.sidebar, width=260, height=350, fg_color="#0a0a0a", border_width=1)
        self.log_box.pack(pady=20, padx=15)
        self.log_box.insert("0.0", "> SYSTEM BOOT SUCCESSFUL\n" + "-"*25 + "\n")

        # --- VIDEO VIEWPORT ---
        self.video_frame = ctk.CTkFrame(self, fg_color="#000000", corner_radius=15)
        self.video_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.video_label = ctk.CTkLabel(self.video_frame, text="") 
        self.video_label.pack(expand=True, fill="both", padx=5, pady=5)

        self.btn_quit = ctk.CTkButton(self.sidebar, text="TERMINATE SESSION", fg_color="#991b1b", 
                                      hover_color="#7f1d1d", command=self.on_closing)
        self.btn_quit.pack(side="bottom", pady=30, padx=30, fill="x")

    def log_incident(self, student_id, direction, frame):
        save_dir = r"D:\SEMS\snapshots"
        if not os.path.exists(save_dir): 
            os.makedirs(save_dir)
        
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(save_dir, f"{student_id}_{ts}.jpg")
        cv2.imwrite(path, frame)
        
        cursor = self.db_conn.cursor()
        # Ensure column 'detail' matches init_db
        cursor.execute("INSERT INTO incidents (timestamp, detail, path) VALUES (?, ?, ?)",
                       (datetime.now().strftime("%H:%M:%S"), f"{student_id}: {direction}", path))
        self.db_conn.commit()
        
        self.log_box.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] ALERT: {student_id}\n")
        self.log_box.see("end")

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.05, 5, minSize=(30, 30))
            
            self.count_label.configure(text=f"ACTIVE USERS: {len(faces)}")

            for i, (x, y, cw, ch) in enumerate(faces):
                student_id = f"USER_{i+1:02d}"
                center_x = x + cw // 2
                
                # --- CLEAR MOTION LOGIC ---
                if student_id not in self.person_data:
                    self.person_data[student_id] = {"smooth_x": center_x, "initial_x": center_x, "start_time": None, "alert_active": False}

                # Apply smoothing to center_x to prevent box jitter
                curr_smooth = self.person_data[student_id]["smooth_x"]
                new_smooth = (self.SMOOTHING_FACTOR * center_x) + ((1 - self.SMOOTHING_FACTOR) * curr_smooth)
                self.person_data[student_id]["smooth_x"] = new_smooth

                move_ratio = (new_smooth - self.person_data[student_id]["initial_x"]) / cw 
                
                is_looking_away = False
                status_color = (46, 204, 113) # Default Green (Active)

                # Threshold check for clear head turns
                if abs(move_ratio) > self.DEAD_ZONE:
                    direction = "RIGHT" if move_ratio > self.RIGHT_SENSITIVITY else "LEFT"
                    if abs(move_ratio) > self.RIGHT_SENSITIVITY:
                        is_looking_away = True
                        status_color = (245, 158, 11) # Amber Warning

                if is_looking_away:
                    if self.person_data[student_id]["start_time"] is None:
                        self.person_data[student_id]["start_time"] = time.time()
                    elapsed = time.time() - self.person_data[student_id]["start_time"]
                    
                    if elapsed > self.TURN_DURATION:
                        status_color = (220, 38, 38) # Red Violation
                        if not self.person_data[student_id]["alert_active"]:
                            self.person_data[student_id]["alert_active"] = True
                            self.log_incident(student_id, direction, frame)
                    cv2.putText(frame, f"SUSPICIOUS: {elapsed:.1f}s", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, status_color, 1)
                else:
                    self.person_data[student_id]["start_time"] = None
                    self.person_data[student_id]["alert_active"] = False

                # Draw clear bounding boxes
                cv2.rectangle(frame, (x, y), (x + cw, y + ch), status_color, 1)
                cv2.putText(frame, student_id, (x, y + ch + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            ctk_img = ctk.CTkImage(PIL.Image.fromarray(rgb_frame), size=(850, 640))
            self.video_label.configure(image=ctk_img)
            self.video_label.image = ctk_img

        self.after(10, self.update_frame)

    def on_closing(self):
        self.cap.release()
        if hasattr(self, 'db_conn'):
            self.db_conn.close()
        self.destroy()

if __name__ == "__main__":
    app = SEMSApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()