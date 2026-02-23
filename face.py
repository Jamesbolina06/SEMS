import cv2
import time
import os
import sqlite3
import PIL.Image, PIL.ImageTk
import customtkinter as ctk
from datetime import datetime

# --- SETTINGS ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SEMSApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Title updated per your specific project requirements
        self.title("SMART EXAMINATION MONITORING SYSTEM USING MOTION DETECTION FOR ACADEMIC INTEGRITY ASSURANCE")
        self.geometry("1100x700")

        # --- DATABASE SETUP ---
        self.db_conn = self.init_db()
        
        # --- DETECTOR SETUP ---
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        
        # FIX: Using CAP_DSHOW and setting resolution to fix grabFrame errors and stuttering
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # --- LOGIC VARIABLES ---
        self.initial_x = None
        self.turn_start_time = None
        self.alert_active = False
        self.last_alert_time = 0
        
        # FIX: Balanced sensitivity at 0.15 to ensure the left side scans without stuttering
        self.RIGHT_SENSITIVITY = 0.15
        self.LEFT_SENSITIVITY = 0.15  
        self.TURN_DURATION = 3

        # --- UI LAYOUT ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar for stats
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="SEMS MONITOR", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(pady=20)

        self.status_card = ctk.CTkFrame(self.sidebar, fg_color="#2b2b2b")
        self.status_card.pack(pady=10, padx=20, fill="x")
        
        self.status_label = ctk.CTkLabel(self.status_card, text="STATUS: OK", text_color="#2ecc71", font=("Arial", 14, "bold"))
        self.status_label.pack(pady=10)

        self.log_box = ctk.CTkTextbox(self.sidebar, width=200, height=300)
        self.log_box.pack(pady=20, padx=10)
        self.log_box.insert("0.0", "System Logs:\n" + "-"*20 + "\n")

        # Video Feed Area
        self.video_frame = ctk.CTkFrame(self, fg_color="black")
        self.video_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.video_label = ctk.CTkLabel(self.video_frame, text="") 
        self.video_label.pack(expand=True)

        self.btn_quit = ctk.CTkButton(self.sidebar, text="STOP SYSTEM", fg_color="#e74c3c", hover_color="#c0392b", command=self.on_closing)
        self.btn_quit.pack(side="bottom", pady=20)

        self.update_frame()

    def init_db(self):
        conn = sqlite3.connect('sems_database.db')
        conn.execute('''CREATE TABLE IF NOT EXISTS incidents 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, violation_type TEXT, snapshot_path TEXT)''')
        conn.commit()
        return conn

    def log_incident(self, direction, frame):
        os.makedirs("snapshots", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"snapshots/alert_{ts}.jpg"
        cv2.imwrite(path, frame)
        
        cursor = self.db_conn.cursor()
        cursor.execute("INSERT INTO incidents (timestamp, violation_type, snapshot_path) VALUES (?, ?, ?)",
                       (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), direction, path))
        self.db_conn.commit()
        
        self.log_box.insert("end", f"[{ts[-6:]}] Alert: {direction}\n")
        self.log_box.see("end")

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # --- VISION LOGIC ---
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # FIX: Adjusted ScaleFactor and minNeighbors to improve detection in low light and reduce stuttering
            faces = self.face_cascade.detectMultiScale(gray, 1.05, 3, minSize=(50, 50))
            profiles = self.profile_cascade.detectMultiScale(gray, 1.1, 15)
            
            is_looking_away = False
            current_direction = "FORWARD"

            if len(faces) > 0:
                (x, y, cw, ch) = faces[0]
                center_x = x + cw // 2
                if self.initial_x is None: self.initial_x = center_x
                
                move_x = center_x - self.initial_x
                
                # Balanced logic for smooth Left/Right detection
                if move_x > (cw * self.RIGHT_SENSITIVITY):
                    current_direction, is_looking_away = "RIGHT", True
                elif move_x < (cw * self.LEFT_SENSITIVITY * -1):
                    current_direction, is_looking_away = "LEFT", True
                
                cv2.rectangle(frame, (x, y), (x + cw, y + ch), (46, 204, 113), 2)

            if len(profiles) > 0:
                is_looking_away, current_direction = True, "SIDE LOOK"

            # --- ALERT LOGIC ---
            if is_looking_away:
                if self.turn_start_time is None: self.turn_start_time = time.time()
                elapsed = time.time() - self.turn_start_time
                self.status_label.configure(text=f"SUSPICIOUS: {elapsed:.1f}s", text_color="#e67e22")
                
                if elapsed > self.TURN_DURATION and not self.alert_active:
                    self.alert_active = True
                    self.log_incident(current_direction, frame)
            else:
                self.turn_start_time = None
                self.alert_active = False
                self.status_label.configure(text="STATUS: OK", text_color="#2ecc71")

            # Final conversion for display
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = PIL.Image.fromarray(frame)
            imgtk = PIL.ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        self.after(10, self.update_frame)

    def on_closing(self):
        self.cap.release()
        self.db_conn.close()
        self.destroy()

if __name__ == "__main__":
    app = SEMSApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()