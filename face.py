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

class MonitoringWindow(ctk.CTkToplevel):
    def __init__(self, parent, room_num, camera_source, db_conn):
        super().__init__(parent)
        self.title(f"ROOM {room_num} - ACTIVE MONITORING")
        self.geometry("950x800")
        
        self.room_num = room_num
        self.db_conn = db_conn
        
        # Only open camera for Room 1
        if self.room_num == 1:
            self.cap = cv2.VideoCapture(camera_source, cv2.CAP_DSHOW)
        else:
            self.cap = None

        # --- KEPT: YOUR ORIGINAL LOGIC VARIABLES ---
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.person_data = {} 
        self.SMOOTHING_FACTOR = 0.3 
        self.DEAD_ZONE = 0.15 
        self.RIGHT_SENSITIVITY = 0.20 
        self.LEFT_SENSITIVITY = 0.20 
        self.TURN_DURATION = 3.0 
        self.prev_face_gray = None

        video_text = "Connecting..." if self.room_num == 1 else "ROOM OFFLINE - NO CAMERA ACCESS"
        self.video_label = ctk.CTkLabel(self, text=video_text, fg_color="black")
        self.video_label.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.status_label = ctk.CTkLabel(self, text="STATUS: OK", text_color="#2ecc71", font=("Arial", 18, "bold"))
        self.status_label.pack(pady=10)

        self.protocol("WM_DELETE_WINDOW", self.close_window)
        if self.cap:
            self.update_monitoring()

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

    def update_monitoring(self):
        if not self.cap: return
        ret, frame = self.cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.05, 5, minSize=(30, 30))
            
            for i, (x, y, cw, ch) in enumerate(faces):
                student_id = f"R{self.room_num}_S{i+1}"
                center_x = x + cw // 2
                
                # --- MOTION DETECTION ROI ---
                face_roi = gray[y:y+ch, x:x+cw]
                if self.prev_face_gray is not None and self.prev_face_gray.shape == face_roi.shape:
                    diff = cv2.absdiff(self.prev_face_gray, face_roi)
                    if np.sum(diff > 25) / (cw * ch) > 50:
                        cv2.putText(frame, "MOTION", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                self.prev_face_gray = face_roi

                # --- SMOOTHING & TURN LOGIC ---
                if student_id not in self.person_data:
                    self.person_data[student_id] = {"smooth_x": center_x, "initial_x": center_x, "start_time": None, "alert_active": False}
                curr_smooth = self.person_data[student_id]["smooth_x"]
                new_smooth = (self.SMOOTHING_FACTOR * center_x) + ((1 - self.SMOOTHING_FACTOR) * curr_smooth)
                self.person_data[student_id]["smooth_x"] = new_smooth
                move_x = new_smooth - self.person_data[student_id]["initial_x"]
                move_ratio = move_x / cw
                
                status_color = (46, 204, 113) 
                if abs(move_ratio) > self.DEAD_ZONE:
                    if move_ratio > self.RIGHT_SENSITIVITY:
                        direction, is_looking_away = "RIGHT", True
                        status_color = (0, 165, 255)
                    elif move_ratio < (self.LEFT_SENSITIVITY * -1):
                        direction, is_looking_away = "LEFT", True
                        status_color = (0, 165, 255)
                    
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
            self.video_label.configure(image=ctk_img, text="")
            self.video_label.image = ctk_img
        self.after(10, self.update_monitoring)

    def close_window(self):
        if self.cap: self.cap.release()
        self.destroy()

class SEMSApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SEMS Dashboard")
        self.geometry("1200x700")
        self.db_path = r"D:\SEMS\sems_database.db"
        self.db_conn = self.init_db()
        self.setup_main_ui()

    def init_db(self):
        if not os.path.exists(r"D:\SEMS"): os.makedirs(r"D:\SEMS")
        conn = sqlite3.connect(self.db_path)
        conn.execute('CREATE TABLE IF NOT EXISTS incidents (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, detail TEXT, path TEXT)')
        conn.commit()
        return conn

    def setup_main_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar - exactly matching the photo
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#242424")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # SEMS Header with dot
        ctk.CTkLabel(self.sidebar, text="SEMS", font=("Arial", 28, "bold")).pack(anchor="w", padx=20, pady=(30, 5))
        ctk.CTkLabel(self.sidebar, text="● System Active", text_color="#2ecc71", font=("Arial", 12)).pack(anchor="w", padx=20, pady=(0, 5))
        ctk.CTkLabel(self.sidebar, text="Dashboard (Active View)", font=("Arial", 12), text_color="#3498db").pack(anchor="w", padx=20, pady=2)
        ctk.CTkLabel(self.sidebar, text="Reports", font=("Arial", 12), text_color="gray").pack(anchor="w", padx=20, pady=2)
        
        # Currently Monitored Session section
        ctk.CTkLabel(self.sidebar, text="Currently Monitored Session", font=("Arial", 11, "bold"), text_color="gray").pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(self.sidebar, text="Session ID: 20251119-001", font=("Arial", 11)).pack(anchor="w", padx=20, pady=2)
        ctk.CTkLabel(self.sidebar, text="User: Admin", font=("Arial", 11)).pack(anchor="w", padx=20, pady=2)
        ctk.CTkLabel(self.sidebar, text="Midterm Exam", font=("Arial", 11)).pack(anchor="w", padx=20, pady=2)
        
        # Rooms section
        ctk.CTkLabel(self.sidebar, text="Rooms", font=("Arial", 11, "bold"), text_color="gray").pack(anchor="w", padx=20, pady=(20, 5))
        for i in range(1, 7):
            ctk.CTkLabel(self.sidebar, text=f"Room {i}", font=("Arial", 11)).pack(anchor="w", padx=20, pady=2)
        
        # Confirmed Incidents
        ctk.CTkLabel(self.sidebar, text="Confirmed Incidents Report - 1", font=("Arial", 11), text_color="orange").pack(anchor="w", padx=20, pady=(20, 5))

        # Main content area
        self.main_view = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=0)
        self.main_view.grid(row=0, column=1, sticky="nsew")
        
        # Top bar with buttons and warning volume
        top_bar = ctk.CTkFrame(self.main_view, fg_color="#242424", height=60, corner_radius=0)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)
        
        # Left side buttons
        button_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        button_frame.pack(side="left", padx=20, pady=10)
        
        ctk.CTkButton(button_frame, text="Add Local Camera", width=120, height=35, fg_color="#3498db", hover_color="#2980b9").pack(side="left", padx=(0, 10))
        ctk.CTkButton(button_frame, text="Add IP Camera", width=120, height=35, fg_color="#3498db", hover_color="#2980b9").pack(side="left")
        
        # Right side warning volume
        warning_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        warning_frame.pack(side="right", padx=20, pady=10)
        
        ctk.CTkLabel(warning_frame, text="Live Feed", font=("Arial", 14, "bold")).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(warning_frame, text="Warning Volume:", font=("Arial", 12)).pack(side="left")
        
        # Volume slider
        volume_slider = ctk.CTkSlider(warning_frame, from_=0, to=100, width=100, height=15, progress_color="#e74c3c")
        volume_slider.pack(side="left", padx=(5, 0))
        volume_slider.set(50)
        
        # Camera grid section - 2x3 grid
        self.grid_container = ctk.CTkFrame(self.main_view, fg_color="#1a1a1a")
        self.grid_container.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Configure grid for 2 rows and 3 columns
        for i in range(3):
            self.grid_container.grid_columnconfigure(i, weight=1, uniform="col")
        for i in range(2):
            self.grid_container.grid_rowconfigure(i, weight=1, uniform="row")
        
        # Create room buttons/camera feeds
        for i in range(1, 7):
            row, col = (i-1)//3, (i-1)%3
            
            # Create frame for each room
            room_frame = ctk.CTkFrame(self.grid_container, fg_color="#2d2d2d", corner_radius=8)
            room_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Room header with number
            header_frame = ctk.CTkFrame(room_frame, fg_color="transparent", height=30)
            header_frame.pack(fill="x", padx=10, pady=(5, 0))
            
            # Room number on left
            ctk.CTkLabel(header_frame, text=f"Room {i}", font=("Arial", 14, "bold")).pack(side="left")
            
            # Camera indicator icon (simulated with colored circle)
            if i == 1:  # Room 1 has active camera
                camera_indicator = ctk.CTkLabel(header_frame, text="●", text_color="#2ecc71", font=("Arial", 16))
                camera_indicator.pack(side="right")
            else:
                camera_indicator = ctk.CTkLabel(header_frame, text="●", text_color="#7f8c8d", font=("Arial", 16))
                camera_indicator.pack(side="right")
            
            # Camera feed placeholder
            feed_frame = ctk.CTkFrame(room_frame, fg_color="#1a1a1a", height=150, corner_radius=4)
            feed_frame.pack(fill="both", expand=True, padx=10, pady=10)
            feed_frame.pack_propagate(False)
            
            if i == 1:
                # Room 1 has a placeholder for actual feed
                feed_label = ctk.CTkLabel(feed_frame, text="Live Feed", font=("Arial", 12), text_color="#3498db")
            else:
                # Other rooms show offline
                feed_label = ctk.CTkLabel(feed_frame, text="Camera Offline", font=("Arial", 12), text_color="#7f8c8d")
            feed_label.pack(expand=True)
            
            # Status bar at bottom of room frame
            status_frame = ctk.CTkFrame(room_frame, fg_color="transparent", height=25)
            status_frame.pack(fill="x", padx=10, pady=(0, 5))
            
            if i == 1:
                ctk.CTkLabel(status_frame, text="Active - 3 Students", font=("Arial", 10), text_color="#2ecc71").pack(side="left")
            else:
                ctk.CTkLabel(status_frame, text="Inactive", font=("Arial", 10), text_color="#7f8c8d").pack(side="left")
            
            # Make the entire room frame clickable (opens monitoring window)
            room_frame.bind("<Button-1>", lambda e, r=i: MonitoringWindow(self, r, 0, self.db_conn))
            header_frame.bind("<Button-1>", lambda e, r=i: MonitoringWindow(self, r, 0, self.db_conn))
            feed_frame.bind("<Button-1>", lambda e, r=i: MonitoringWindow(self, r, 0, self.db_conn))
            
            # Change cursor to indicate clickable
            room_frame.configure(cursor="hand2")

if __name__ == "__main__":
    app = SEMSApp()
    app.mainloop()