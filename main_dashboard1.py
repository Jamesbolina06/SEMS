import customtkinter as ctk
import cv2
import numpy as np
import threading
import time  # <--- ADDED: Required for the 10-second timer
from PIL import Image
import ctypes  

# --- Fix for Windows Scaling (DPI Awareness) ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

from reports1 import ReportsFrame
from replay_system1 import ReplaySystemFrame
from add_local_camera1 import AddLocalCameraPopup
from add_ip_camera1 import AddIPCameraPopup

# --- Load Classifiers ---
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')

class VideoStream:
    def __init__(self, src):
        # FIX: Check if the source is a local webcam (integer like 0) or IP camera (RTSP string)
        if isinstance(src, int):
            # Local webcam: Let Windows use its default USB camera driver
            self.cap = cv2.VideoCapture(src)
        else:
            # IP Camera: Force FFMPEG for RTSP network streams
            self.cap = cv2.VideoCapture(src, cv2.CAP_FFMPEG)
            
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.grabbed, self.frame = self.cap.read()
        self.started = False
        self.read_lock = threading.Lock()

    def start(self):
        if self.started: return
        self.started = True
        self.thread = threading.Thread(target=self.update, args=(), daemon=True)
        self.thread.start()
        return self

    def update(self):
        while self.started:
            grabbed, frame = self.cap.read()
            if grabbed:
                with self.read_lock:
                    self.grabbed, self.frame = grabbed, frame

    def read(self):
        with self.read_lock:
            if self.frame is not None:
                return self.grabbed, self.frame.copy()
            return False, None

    def stop(self):
        self.started = False
        if hasattr(self, 'thread'): self.thread.join()
        self.cap.release()

class SEMSDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SEMS (Smart Examination Monitoring System)")
        self.geometry("1200x750")
        self.configure(fg_color="#1a1a1b")
        
        self.active_cameras = []
        self.fullscreen_cam_data = None 
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color="#111112")
        self.sidebar.pack(side="left", fill="y")
        ctk.CTkLabel(self.sidebar, text="SEMS", font=("Arial", 35, "bold"), text_color="white").pack(pady=(50, 5))
        ctk.CTkLabel(self.sidebar, text="● System Active", font=("Segoe UI", 11, "bold"), text_color="#00FF00").pack(pady=(0, 40))
        
        self.btn_dash = self.create_nav_btn("📊 Dashboard", self.show_dashboard)
        self.btn_reports = self.create_nav_btn("📋 Reports", self.show_reports)
        self.btn_replay = self.create_nav_btn("🔄 Replay System", self.show_replay)

        self.session_info = ctk.CTkLabel(
            self.sidebar, 
            text="Currently Monitored Session\n\nSmart Examination and\nRoom Decorum Monitoring System",
            font=("Segoe UI", 11), text_color="#777777", justify="left"
        )
        self.session_info.pack(side="bottom", pady=30, padx=20, anchor="w")

        # --- Main Content Container ---
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(side="right", expand=True, fill="both")

        # Initialize Frames
        self.dashboard_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.setup_dashboard_ui()
        
        self.fullscreen_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.setup_fullscreen_ui() 
        
        self.reports_frame = ReportsFrame(self.container)
        self.replay_frame = ReplaySystemFrame(self.container)

        # Force initial state
        self.show_dashboard()
        self.update_loop()

    def create_nav_btn(self, text, command):
        btn = ctk.CTkButton(self.sidebar, text=text, anchor="w", fg_color="transparent", hover_color="#2d2d2e", height=45, command=command)
        btn.pack(fill="x", padx=15, pady=4)
        return btn

    def setup_dashboard_ui(self):
        header = ctk.CTkFrame(self.dashboard_frame, height=80, fg_color="transparent")
        header.pack(side="top", fill="x", padx=30, pady=(20, 10))
        ctk.CTkLabel(header, text="Camera Monitoring", font=("Segoe UI", 26, "bold"), text_color="white").pack(side="left")
        ctk.CTkButton(header, text="+ Add IP Camera", fg_color="#1f538d", width=140, command=self.open_add_ip_popup).pack(side="right", padx=5)
        ctk.CTkButton(header, text="+ Add Local Camera", fg_color="#3a3a3b", width=140, command=self.open_add_local_popup).pack(side="right", padx=5)
        
        self.scroll = ctk.CTkScrollableFrame(self.dashboard_frame, fg_color="transparent")
        self.scroll.pack(expand=True, fill="both", padx=20, pady=10)
        self.grid_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.grid_frame.pack(expand=True, fill="both")
        self.grid_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="col")

    def setup_fullscreen_ui(self):
        header = ctk.CTkFrame(self.fullscreen_frame, height=60, fg_color="transparent")
        header.pack(side="top", fill="x", padx=30, pady=15)
        self.fs_title = ctk.CTkLabel(header, text="Room Monitoring", font=("Segoe UI", 24, "bold"), text_color="white")
        self.fs_title.pack(side="left")
        
        # Action Buttons
        ctk.CTkButton(header, text="✖ Stop Monitoring", fg_color="#ff4d4d", hover_color="#cc0000", command=self.exit_fullscreen).pack(side="right")
        ctk.CTkButton(header, text="💾 Saved Monitoring", fg_color="#28a745", hover_color="#218838", command=self.save_monitoring_action).pack(side="right", padx=10)
        
        self.fs_video_label = ctk.CTkLabel(self.fullscreen_frame, text="", fg_color="black")
        self.fs_video_label.pack(expand=True, fill="both", padx=30, pady=(0, 30))

    def save_monitoring_action(self):
        if self.fullscreen_cam_data:
            print(f"DEBUG: Saving monitoring for {self.fullscreen_cam_data['room_name']}")

    # --- Strict Tab Switching Logic ---
    def hide_all_frames(self):
        """Strictly clears the container before switching tabs to prevent overlap."""
        try: self.dashboard_frame.pack_forget()
        except: pass
        try: self.fullscreen_frame.pack_forget()
        except: pass
        try: self.reports_frame.pack_forget()
        except: pass
        try: self.replay_frame.pack_forget()
        except: pass

    def show_dashboard(self):
        self.hide_all_frames()
        if self.fullscreen_cam_data:
            self.fullscreen_frame.pack(expand=True, fill="both")
        else:
            self.dashboard_frame.pack(expand=True, fill="both")

    def show_reports(self):
        self.hide_all_frames()
        self.reports_frame.pack(expand=True, fill="both")

    def show_replay(self):
        self.hide_all_frames()
        self.replay_frame.pack(expand=True, fill="both")

    # --- Camera Logic ---
    def add_camera_card_live(self, room_name, cam_type, url=None):
        # If the popup sends an IP URL, use it. Otherwise, use the local webcam index (0, 1, etc.)
        if url:
            source = url
        else:
            source = len(self.active_cameras)
        index = len(self.active_cameras)
        row, col = index // 3, index % 3
        card = ctk.CTkFrame(self.grid_frame, fg_color="#252526", corner_radius=12)
        card.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")
        
        view = ctk.CTkFrame(card, fg_color="#000000", height=180, width=280)
        view.pack(expand=True, fill="both", padx=8, pady=8)
        view.pack_propagate(False) 
        video_label = ctk.CTkLabel(view, text="Connecting...")
        video_label.pack(expand=True, fill="both")
        
        stream = VideoStream(source).start()
        
        cam_data = {
            "stream": stream, 
            "label": video_label, 
            "card": card, 
            "room_name": room_name, 
            "type": cam_type,
            "tracked_faces": {}  
        }
        self.active_cameras.append(cam_data)
        video_label.bind("<Button-1>", lambda event, c=cam_data: self.enter_fullscreen(c))
        
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(info, text=f"{room_name} ({cam_type})", font=("Segoe UI", 12)).pack(side="left")
        ctk.CTkButton(info, text="✖", width=25, height=25, fg_color="#ff4d4d", command=lambda c=cam_data: self.remove_camera(c)).pack(side="right")

    def update_loop(self):
        current_time = time.time() # Get the current exact time
        
        for cam in self.active_cameras:
            ret, frame = cam["stream"].read()
            if ret and frame is not None:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # ----------------------------------------------------
                # EXAM MONITORING LOGIC (Optical Ghost Box Tracker)
                # ----------------------------------------------------
                if cam["type"] == "Exam Monitoring":
                    
                    # STRICTER DETECTION (Unchanged - Keeps it highly accurate!)
                    faces = face_cascade.detectMultiScale(gray, 1.1, 7, minSize=(80, 80))
                    
                    if not hasattr(cam, "face_id_counter"):
                        cam["face_id_counter"] = 0
                    
                    # 1. Update our memory with newly found straight faces
                    for (x, y, w, h) in faces:
                        cx, cy = x + w/2, y + h/2
                        matched_id = None
                        
                        for face_id, data in cam["tracked_faces"].items():
                            ox, oy = data["center"]
                            if abs(cx - ox) < 100 and abs(cy - oy) < 100:
                                matched_id = face_id
                                break
                        
                        # Grab a safe crop of the face to use as our visual template
                        safe_y1, safe_y2 = max(0, y), min(gray.shape[0], y+h)
                        safe_x1, safe_x2 = max(0, x), min(gray.shape[1], x+w)
                        face_template = gray[safe_y1:safe_y2, safe_x1:safe_x2].copy()
                        
                        if matched_id:
                            cam["tracked_faces"][matched_id]["box"] = (x, y, w, h)
                            cam["tracked_faces"][matched_id]["center"] = (cx, cy)
                            cam["tracked_faces"][matched_id]["last_seen"] = current_time
                            cam["tracked_faces"][matched_id]["missing_start"] = None
                            if face_template.size > 0:
                                cam["tracked_faces"][matched_id]["template"] = face_template
                        else:
                            cam["face_id_counter"] += 1
                            cam["tracked_faces"][cam["face_id_counter"]] = {
                                "box": (x, y, w, h),
                                "center": (cx, cy),
                                "last_seen": current_time,
                                "first_seen": current_time,
                                "missing_start": None,
                                "template": face_template
                            }
                            
                    # 2. Check all faces in memory and draw boxes
                    faces_to_keep = {}
                    for face_id, data in cam["tracked_faces"].items():
                        x, y, w, h = data["box"]
                        time_since_last_seen = current_time - data["last_seen"]
                        time_alive = current_time - data["first_seen"]
                        
                        if time_since_last_seen < 0.5:
                            # Face looking straight (Green)
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                            faces_to_keep[face_id] = data
                            
                        elif time_since_last_seen < 15: # Face missing!
                            if time_alive > 1.0: 
                                if data["missing_start"] is None:
                                    data["missing_start"] = current_time
                                    
                                missing_duration = current_time - data["missing_start"]
                                
                                # --- ADDED OPTICAL TRACKING FOR YELLOW BOX ---
                                template = data.get("template")
                                if template is not None and template.shape[0] > 10 and template.shape[1] > 10:
                                    # Create a search window around where the head used to be
                                    pad = 60
                                    y1, y2 = max(0, y - pad), min(gray.shape[0], y + h + pad)
                                    x1, x2 = max(0, x - pad), min(gray.shape[1], x + w + pad)
                                    search_window = gray[y1:y2, x1:x2]

                                    if search_window.shape[0] >= template.shape[0] and search_window.shape[1] >= template.shape[1]:
                                        # Use OpenCV to find where the pixels moved!
                                        res = cv2.matchTemplate(search_window, template, cv2.TM_CCOEFF_NORMED)
                                        _, max_val, _, max_loc = cv2.minMaxLoc(res)

                                        # If it finds a good match, move the box!
                                        if max_val > 0.4:
                                            new_x = x1 + max_loc[0]
                                            new_y = y1 + max_loc[1]
                                            
                                            data["box"] = (new_x, new_y, w, h)
                                            data["center"] = (new_x + w/2, new_y + h/2)
                                            x, y = new_x, new_y # Update variables for drawing
                                            
                                            # Update the template so it slowly adapts to the turning head
                                            data["template"] = gray[new_y:new_y+h, new_x:new_x+w].copy()
                                # ---------------------------------------------
                                
                                if missing_duration >= 10:
                                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                    cv2.putText(frame, "SUSPICIOUS!", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                                else:
                                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
                                    cv2.putText(frame, f"Head Turned: {int(missing_duration)}s", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                                
                                faces_to_keep[face_id] = data
                            
                    cam["tracked_faces"] = faces_to_keep

                # ----------------------------------------------------
                # ROOM DECORUM LOGIC
                # ----------------------------------------------------
                elif cam["type"] == "Room Decorum":
                    bodies = body_cascade.detectMultiScale(gray, 1.1, 3, minSize=(50, 100))
                    for (x, y, w, h) in bodies:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 165, 0), 2)

                # --- Render to UI ---
                if self.fullscreen_cam_data == cam: 
                    self.render_video(frame, self.fs_video_label)
                elif not self.fullscreen_cam_data: 
                    self.render_video(frame, cam["label"])
                    
        self.after(10, self.update_loop)

    def render_video(self, frame, label):
        try:
            w, h = label.winfo_width(), label.winfo_height()
            if w < 100: w, h = 280, 180
            img = Image.fromarray(cv2.cvtColor(cv2.resize(frame, (w, h)), cv2.COLOR_BGR2RGB))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(w, h))
            label.configure(image=ctk_img, text="")
            label.image = ctk_img
        except: pass

    def enter_fullscreen(self, cam_data):
        self.fullscreen_cam_data = cam_data
        self.show_dashboard()

    def exit_fullscreen(self):
        self.fullscreen_cam_data = None
        self.show_dashboard()

    def remove_camera(self, cam_data):
        # 1. Stop the video stream and destroy the UI card
        cam_data["stream"].stop()
        cam_data["card"].destroy()
        
        # 2. Remove it from the active list
        self.active_cameras.remove(cam_data)
        
        # 3. FIX: Re-calculate the grid positions for all remaining cameras
        # This forces the 2nd camera to slide into the 1st camera's slot!
        for index, cam in enumerate(self.active_cameras):
            row, col = index // 3, index % 3
            cam["card"].grid(row=row, column=col, padx=12, pady=12, sticky="nsew")

    def on_closing(self):
        for cam in self.active_cameras: cam["stream"].stop()
        self.destroy()

    def open_add_local_popup(self): AddLocalCameraPopup(self)
    def open_add_ip_popup(self): AddIPCameraPopup(self)

if __name__ == "__main__":
    app = SEMSDashboard()
    app.mainloop()