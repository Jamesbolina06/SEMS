import customtkinter as ctk
import cv2
import numpy as np
import threading
import time  
from PIL import Image
import ctypes  
import mediapipe as mp 
import os

# --- Force OpenCV to use TCP for RTSP (Fixes Blurry/Gray Video Streams) ---
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

# --- Fix for Windows Scaling (DPI Awareness) ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

from reports1 import ReportsFrame
from replay_system1 import ReplaySystemFrame
from add_local_camera1 import AddLocalCameraPopup
from add_ip_camera1 import AddIPCameraPopup

# --- Load Deep Learning Models (MobileNet-SSD) ---
try:
    person_net = cv2.dnn.readNetFromCaffe("MobileNetSSD_deploy.prototxt", "MobileNetSSD_deploy.caffemodel")
    print("SUCCESS: MobileNet-SSD Loaded for Exam & Decorum Monitoring!")
except Exception as e:
    print(f"ERROR: MobileNet files missing! Error: {e}")
    person_net = None

# --- MediaPipe Initializers ---
mp_pose = mp.solutions.pose
mp_face_detection = mp.solutions.face_detection 
mp_drawing = mp.solutions.drawing_utils

class VideoStream:
    def __init__(self, src):
        if isinstance(src, int):
            self.cap = cv2.VideoCapture(src)
        else:
            self.cap = cv2.VideoCapture(src, cv2.CAP_FFMPEG)
            
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
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

        self.dashboard_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.setup_dashboard_ui()
        self.fullscreen_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.setup_fullscreen_ui() 
        self.reports_frame = ReportsFrame(self.container)
        self.replay_frame = ReplaySystemFrame(self.container)

        self.show_dashboard()
        
        # BAGO: I-load agad ang mga saved cameras pagka-open ng system!
        self.load_saved_cameras() 
        
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
        ctk.CTkButton(header, text="+ Add Lan Camera", fg_color="#3a3a3b", width=140, command=self.open_add_local_popup).pack(side="right", padx=5)
        
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
        ctk.CTkButton(header, text="✖ Stop Monitoring", fg_color="#ff4d4d", hover_color="#cc0000", command=self.exit_fullscreen).pack(side="right")
        
        # BAGO: Recording Toggle Button
        self.record_btn = ctk.CTkButton(header, text="⏺ Start Recording", fg_color="#28a745", hover_color="#218838", command=self.toggle_recording)
        self.record_btn.pack(side="right", padx=10)
        
        self.fs_video_label = ctk.CTkLabel(self.fullscreen_frame, text="", fg_color="black")
        self.fs_video_label.pack(expand=True, fill="both", padx=30, pady=(0, 30))

    def toggle_recording(self):
        cam = self.fullscreen_cam_data
        if not cam: return

        if not cam.get("is_recording", False):
            # --- START RECORDING ---
            import datetime
            import os
            
            # Sinisigurado ng system na may "replays" folder. Kung wala, gagawa siya auto.
            if not os.path.exists("replays"):
                os.makedirs("replays")
                
            date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"record_{cam['room_name'].replace(' ', '_')}_{date_str}.avi"
            
            # BAGO: Pinagsama natin ang folder name at filename (e.g. replays/record_Room1_date.avi)
            filepath = os.path.join("replays", filename) 
            
            ret, frame = cam["stream"].read()
            if ret:
                h, w = frame.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                
                # BAGO: Ginamit natin ang 'filepath' imbes na 'filename' lang
                cam["video_writer"] = cv2.VideoWriter(filepath, fourcc, 20.0, (w, h))
                cam["is_recording"] = True
                
                # BAGO: Ise-save natin ang buong path para mahanap siya ng Replay System
                cam["record_filepath"] = filepath 
                cam["record_start_time"] = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
                
                self.record_btn.configure(text="⏹ Stop & Save", fg_color="#ff4d4d", hover_color="#cc0000")
        else:
            # --- STOP RECORDING ---
            cam["is_recording"] = False
            if "video_writer" in cam and cam["video_writer"] is not None:
                cam["video_writer"].release()
                cam["video_writer"] = None
            
            self.record_btn.configure(text="⏺ Start Recording", fg_color="#28a745", hover_color="#218838")
            
            room = cam['room_name']
            cam_type = cam['type']
            start_date = cam["record_start_time"]
            saved_filepath = cam["record_filepath"] 
            
            # --- BAGO: ISAVE SA DATABASE ---
            from sems_db import Database
            db = Database()
            db_id = db.insert_record(room, cam_type, start_date, saved_filepath)
            
           # Ipasa ang totoong Database ID (db_id) pabalik sa UI natin
            self.replay_frame.add_recorded_video(db_id, room, start_date, saved_filepath)
            
            from tkinter import messagebox
            import os
            just_filename = os.path.basename(saved_filepath)
            messagebox.showinfo("Monitoring Saved", f"Video '{just_filename}' successfully saved to replay system!")

    def hide_all_frames(self):
        for frame in [self.dashboard_frame, self.fullscreen_frame, self.reports_frame, self.replay_frame]:
            frame.pack_forget()

    def show_dashboard(self):
        self.hide_all_frames()
        if self.fullscreen_cam_data: self.fullscreen_frame.pack(expand=True, fill="both")
        else: self.dashboard_frame.pack(expand=True, fill="both")

    def show_reports(self):
        self.hide_all_frames()
        self.reports_frame.pack(expand=True, fill="both")

    def show_replay(self):
        self.hide_all_frames()
        self.replay_frame.pack(expand=True, fill="both")

    # --- BAGO: Camera Database Management ---
    def load_saved_cameras(self):
        from sems_db import Database
        db = Database()
        saved_cams = db.fetch_all_cameras()
        db.close()
        
        for cam in saved_cams:
            room, cam_type, url = cam
            # Kung local IP camera, string siya. Kung web camera ng laptop, convert to int.
            source = int(url) if url.isdigit() else url 
            self.add_camera_card_live(room, cam_type, source, is_loading_from_db=True)

    def save_camera_to_db(self, room_name, cam_type, url):
        from sems_db import Database
        db = Database()
        db.insert_camera(room_name, cam_type, str(url))
        db.close()

    def add_camera_card_live(self, room_name, cam_type, url=None, is_loading_from_db=False):
        source = url if url is not None else 0 # Default sa 0 (built-in cam) kung walang url
        
        # I-save sa database kapag manual na idinagdag (hindi galing sa loading)
        if not is_loading_from_db:
            self.save_camera_to_db(room_name, cam_type, source)
            
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
        
        pose_detector = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) if cam_type == "Room Decorum" else None
        face_detector = mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.3) if cam_type == "Exam Monitoring" else None

        cam_data = {
            "stream": stream, "label": video_label, "card": card, "room_name": room_name, "type": cam_type,
            "tracked_faces": {}, "face_id_counter": 0, "pose_detector": pose_detector,
            "face_detector": face_detector, "decorum_timers": {"standing_start": None}, "student_memory": []
        }
        self.active_cameras.append(cam_data)
        video_label.bind("<Button-1>", lambda event, c=cam_data: self.enter_fullscreen(c))
        
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(info, text=f"{room_name} ({cam_type})", font=("Segoe UI", 12)).pack(side="left")
        ctk.CTkButton(info, text="✖", width=25, height=25, fg_color="#ff4d4d", command=lambda c=cam_data: self.remove_camera(c)).pack(side="right")

    def update_loop(self):
        current_time = time.time() 
        for cam in self.active_cameras:
            ret, frame = cam["stream"].read()
            if ret and frame is not None:
                ih, iw, _ = frame.shape
                
                # =========================================================================
                # EXAM MONITORING LOGIC (MobileNet + Face Fusion)
                # =========================================================================
                if cam["type"] == "Exam Monitoring":
                    current_frame_candidates = []
                    turned_faces = []

                    # 1. FACE AI
                    if cam["face_detector"]:
                        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        res = cam["face_detector"].process(rgb)
                        if res.detections:
                            for det in res.detections:
                                b = det.location_data.relative_bounding_box
                                fx, fy = int(b.xmin * iw), int(b.ymin * ih)
                                fw, fh = int(b.width * iw), int(b.height * ih)
                                
                                is_t = False
                                kp = det.location_data.relative_keypoints
                                if len(kp) >= 6:
                                    nx, rx, lx = kp[2].x, kp[4].x, kp[5].x
                                    if abs(rx - lx) > 0.01:
                                        rat = (nx - min(rx, lx)) / abs(rx - lx)
                                        if rat < 0.10 or rat > 0.90: is_t = True
                                        
                                turned_faces.append((fx, fy, fw, fh, is_t))
                                # Binawasan natin ang padding at ginawang 1.5 na lang ang haba imbes na 3
                                current_frame_candidates.append([max(0, fx - 10), max(0, fy - 20), fw + 20, int(fh * 1.5), is_t])

                    # 2. MOBILENET SSD
                    if person_net:
                        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
                        person_net.setInput(blob)
                        dets = person_net.forward()
                        for i in range(dets.shape[2]):
                            conf = dets[0, 0, i, 2]
                            if int(dets[0, 0, i, 1]) == 15 and conf > 0.35: 
                                box = dets[0, 0, i, 3:7] * np.array([iw, ih, iw, ih])
                                sx, sy, ex, ey = box.astype("int")
                                bw, bh = ex - sx, ey - sy
                                
                                if bw > 30 and bh > 60:
                                    is_turning = False
                                    for (fx, fy, fw, fh, t) in turned_faces:
                                        fcx, fcy = fx + fw/2, fy + fh/2
                                        if sx < fcx < ex and sy < fcy < ey:
                                            if t: is_turning = True
                                    current_frame_candidates.append([sx, sy, bw, bh, is_turning])

                    # 3. TRACKING & UI RENDER
                    current_frame_candidates = sorted(current_frame_candidates, key=lambda x: x[2]*x[3], reverse=True)[:15]
                    m_ids = set()
                    
                    for (nx, ny, nw, nh, is_t) in current_frame_candidates:
                        ncx, ncy = nx + nw/2, ny + nh/2
                        mid = None
                        min_dist = 150 
                        
                        for sid, d in cam["tracked_faces"].items():
                            if sid not in m_ids:
                                dist = np.linalg.norm(np.array([ncx, ncy]) - np.array(d["center"]))
                                if dist < min_dist:
                                    min_dist = dist
                                    mid = sid
                        
                        if mid:
                            d = cam["tracked_faces"][mid]
                            px, py, pw, ph = d["box"]
                            sx = int(px * 0.6 + nx * 0.4)
                            sy = int(py * 0.6 + ny * 0.4)
                            sw = int(pw * 0.6 + nw * 0.4)
                            sh = int(ph * 0.6 + nh * 0.4)
                            
                            d.update({"box": (sx, sy, sw, sh), "center": (ncx, ncy), "last_seen": current_time})
                            
                            if "buf" not in d: d["buf"] = []
                            d["buf"].append(is_t)
                            d["buf"] = d["buf"][-10:]
                            d["is_t"] = sum(d["buf"]) > 6
                            m_ids.add(mid)
                        else:
                            cam["face_id_counter"] += 1
                            cam["tracked_faces"][cam["face_id_counter"]] = {
                                "box": (nx, ny, nw, nh), "center": (ncx, ncy), 
                                "last_seen": current_time, "t_start": None, "is_t": is_t, "buf": [is_t],
                                "snapshot_saved": False  # BAGO ITO
                            }

                    new_f = {}
                    for sid, d in cam["tracked_faces"].items():
                        if current_time - d["last_seen"] < 1.0: 
                            x, y, w, h = d["box"]
                            lbl, clr = "Student", (0, 255, 0)
                            
                            # Siguraduhin na may video_buffer list ang bawat student
                            if "video_buffer" not in d:
                                d["video_buffer"] = []

                            if d["is_t"]:
                                if d["t_start"] is None: 
                                    d["t_start"] = current_time
                                    d["snapshot_saved"] = False
                                    d["video_buffer"] = [] # I-clear ang buffer kapag nag-start ang timer
                                elap = current_time - d["t_start"]
                                if elap >= 7: 
                                    lbl, clr = "SUSPICIOUS!", (0, 0, 255)
                                else: 
                                    lbl, clr = f"Looking Around ({int(7-elap)}s)", (0, 255, 255)
                            else: 
                                d["t_start"] = None
                                d["snapshot_saved"] = False
                                d["video_buffer"] = [] # Burahin ang record kapag bumalik ang tingin sa tama
                            
                            # I-drawing ang box at text sa frame
                            cv2.rectangle(frame, (x, y), (x+w, y+h), clr, 2)
                            cv2.putText(frame, lbl, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, clr, 2)
                            
                            # BAGO: I-save ang bawat frame sa buffer habang tumatakbo ang timer!
                            if d["t_start"] is not None and not d.get("snapshot_saved"):
                                # Limitahan sa 300 frames para hindi mapuno ang RAM ng laptop
                                if len(d["video_buffer"]) < 300: 
                                    d["video_buffer"].append(frame.copy())
                            
                            # --- BAGO: VIDEO RECORD TRIGGER ---
                            if d["is_t"] and d["t_start"] is not None and (current_time - d["t_start"]) >= 7:
                                if not d.get("snapshot_saved"):
                                    import os, datetime
                                    
                                    abs_folder = os.path.abspath("violations")
                                    if not os.path.exists(abs_folder): 
                                        os.makedirs(abs_folder)
                                    
                                    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                                    room_clean = cam['room_name'].replace(' ', '_')
                                    # Pinalitan natin ng .avi imbes na .jpg
                                    filename = f"violation_{room_clean}_std{sid}_{date_str}.avi" 
                                    full_filepath = os.path.join(abs_folder, filename)
                                    
                                    # I-compile ang mga naipong frames at i-save bilang Video!
                                    if len(d["video_buffer"]) > 0:
                                        h_frame, w_frame = d["video_buffer"][0].shape[:2]
                                        # 10.0 FPS para sakto sa speed ng AI monitoring
                                        out = cv2.VideoWriter(full_filepath, cv2.VideoWriter_fourcc(*'XVID'), 10.0, (w_frame, h_frame))
                                        for bf in d["video_buffer"]:
                                            out.write(bf)
                                        out.release()
                                    
                                    # Ipasok sa Database!
                                    from sems_db import Database
                                    db = Database()
                                    # BAGO: Ipinasa natin yung context string!
                                    violation_context = " Student Looking Around (7s)"
                                    db.insert_violation(cam['room_name'], cam['type'], violation_context, datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p"), full_filepath)
                                    
                                    # I-update ang Reports Table nang live!
                                    self.reports_frame.add_report_entry()
                                    
                                    d["snapshot_saved"] = True
                                    d["video_buffer"] = [] # Linisin ang memory pagkatapos mag-save

                            new_f[sid] = d
                    cam["tracked_faces"] = new_f

               # =========================================================================
                # ROOM DECORUM LOGIC (MobileNet-SSD Body + MediaPipe Skeleton)
                # =========================================================================
                elif cam["type"] == "Room Decorum":
                    roi_y = int(ih * 0.20)  # Red Line (Restricted Zone)
                    seat_limit_y = int(ih * 0.40) # Yellow Line (Para sa limit ng upo)
                    
                    cv2.line(frame, (0, roi_y), (iw, roi_y), (0, 0, 255), 2)
                    cv2.putText(frame, "RESTRICTED ZONE", (10, roi_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    cv2.line(frame, (0, seat_limit_y), (iw, seat_limit_y), (0, 255, 255), 1)

                    if "decorum_state" not in cam: 
                        cam["decorum_state"] = {
                            "continuous_start": None, 
                            "burst_start": None,
                            "is_burst_locked": False,
                            "snapshot_saved": False,
                            "video_buffer": [], 
                            "current_v_name": ""
                        }
                    
                    ds = cam["decorum_state"]

                    is_continuous_v = False
                    is_burst_v = False
                    violation_detected = ""

                    # A. MobileNet-SSD (Multiple People Tracking - Area & Seating)
                    if person_net:
                        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
                        person_net.setInput(blob)
                        dets = person_net.forward()
                        for i in range(dets.shape[2]):
                            conf = dets[0, 0, i, 2]
                            
                            # Confidence set at 0.20
                            if int(dets[0, 0, i, 1]) == 15 and conf > 0.20: 
                                box = dets[0, 0, i, 3:7] * np.array([iw, ih, iw, ih])
                                sx, sy, ex, ey = box.astype("int")
                                
                                sx, sy = max(0, sx), max(0, sy)
                                ex, ey = min(iw, ex), min(ih, ey)
                                bw, bh = ex - sx, ey - sy
                                
                                if bw > 30 and bh > 50:
                                    cv2.rectangle(frame, (sx, sy), (ex, ey), (0, 255, 0), 2)
                                    cv2.putText(frame, f"Student {int(conf*100)}%", (sx, sy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                                    
                                    # --- BAGO: RESTRICTED AREA CHECK (Gamit ang Green Box) ---
                                    if sy < roi_y:
                                        is_continuous_v = True
                                        violation_detected = "Restricted Area Access"
                                    
                                    # --- IMPROPER SEATING CHECK ---
                                    # Kung hindi umabot sa red line pero lumampas sa yellow line
                                    elif sy < seat_limit_y:
                                        is_continuous_v = True
                                        violation_detected = "Improper Seating Detected"

                    # B. Skeletal Tracking (MediaPipe Pose - PARA SA FIGHTING/VELOCITY NALANG)
                    if cam["pose_detector"]:
                        rgb_decor = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        res_decor = cam["pose_detector"].process(rgb_decor)
                        
                        if res_decor.pose_landmarks:
                            mp_drawing.draw_landmarks(frame, res_decor.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                            lm = res_decor.pose_landmarks.landmark
                            
                            # Tinanggal na natin dito yung Restricted Area check!
                            
                            # --- HIGH-VELOCITY CHECK (Kamay lang) ---
                            current_l_wrist = np.array([lm[15].x, lm[15].y])
                            current_r_wrist = np.array([lm[16].x, lm[16].y])
                            
                            if "prev_wrists" in ds and ds["prev_wrists"] is not None:
                                prev_l_wrist, prev_r_wrist = ds["prev_wrists"]
                                dist_l = np.linalg.norm(current_l_wrist - prev_l_wrist)
                                dist_r = np.linalg.norm(current_r_wrist - prev_r_wrist)
                                
                                if dist_l > 0.50 or dist_r > 0.65:
                                    is_burst_v = True
                                    violation_detected = "High-Velocity Commotion (Fighting)"
                            
                            ds["prev_wrists"] = (current_l_wrist, current_r_wrist)
  
                    # =======================================================
                    # C. DUAL-LOGIC TIMER & VIDEO SAVING
                    # =======================================================
                    
                    # 1. FIGHTING LOGIC (Burst & Locked)
                    if is_burst_v and not ds["is_burst_locked"]:
                        ds["is_burst_locked"] = True
                        ds["burst_start"] = current_time
                        ds["video_buffer"] = []
                        ds["current_v_name"] = violation_detected

                    if ds["is_burst_locked"]:
                        elap = current_time - ds["burst_start"]
                        cv2.putText(frame, f"[RECORDING] {ds['current_v_name']} ({int(5-elap)}s)", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
                        if len(ds["video_buffer"]) < 300:
                            ds["video_buffer"].append(frame.copy())

                        if elap >= 5:
                            import os, datetime
                            abs_folder = os.path.abspath("violations")
                            if not os.path.exists(abs_folder): os.makedirs(abs_folder)
                            date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            full_filepath = os.path.join(abs_folder, f"decorum_{cam['room_name'].replace(' ', '_')}_{date_str}.avi")
                            
                            if len(ds["video_buffer"]) > 0:
                                h_f, w_f = ds["video_buffer"][0].shape[:2]
                                out = cv2.VideoWriter(full_filepath, cv2.VideoWriter_fourcc(*'XVID'), 10.0, (w_f, h_f))
                                for bf in ds["video_buffer"]: out.write(bf)
                                out.release()
                            
                            from sems_db import Database
                            db = Database()
                            db.insert_violation(cam['room_name'], cam['type'], ds['current_v_name'], datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p"), full_filepath)
                            self.reports_frame.add_report_entry()
                            
                            ds["is_burst_locked"] = False
                            ds["burst_start"] = None
                            ds["video_buffer"] = []

                    # 2. AREA & SEATING LOGIC (Continuous) 
                    elif not ds["is_burst_locked"]: 
                        if is_continuous_v:
                            if ds["continuous_start"] is None:
                                ds["continuous_start"] = current_time
                                ds["video_buffer"] = []
                                ds["snapshot_saved"] = False
                                ds["current_v_name"] = violation_detected
                            
                            elap = current_time - ds["continuous_start"]
                            
                            if elap >= 5:
                                cv2.putText(frame, f"{ds['current_v_name']} Violation!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)
                            else:
                                cv2.putText(frame, f"Warning: {ds['current_v_name']} ({int(5-elap)}s)", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                            
                            if not ds.get("snapshot_saved", False) and len(ds["video_buffer"]) < 300:
                                ds["video_buffer"].append(frame.copy())
                                
                            if elap >= 5 and not ds.get("snapshot_saved", False):
                                import os, datetime
                                abs_folder = os.path.abspath("violations")
                                if not os.path.exists(abs_folder): os.makedirs(abs_folder)
                                date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                                full_filepath = os.path.join(abs_folder, f"decorum_{cam['room_name'].replace(' ', '_')}_{date_str}.avi")
                                
                                if len(ds["video_buffer"]) > 0:
                                    h_f, w_f = ds["video_buffer"][0].shape[:2]
                                    out = cv2.VideoWriter(full_filepath, cv2.VideoWriter_fourcc(*'XVID'), 10.0, (w_f, h_f))
                                    for bf in ds["video_buffer"]: out.write(bf)
                                    out.release()
                                
                                from sems_db import Database
                                db = Database()
                                db.insert_violation(cam['room_name'], cam['type'], f"{ds['current_v_name']} (5s)", datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p"), full_filepath)
                                self.reports_frame.add_report_entry()
                                
                                ds["snapshot_saved"] = True
                                ds["video_buffer"] = []
                        else:
                            ds["continuous_start"] = None
                            ds["snapshot_saved"] = False
                            ds["video_buffer"] = []

                # --- ACTUAL VIDEO RECORDING CAPTURE ---
                # BAGO: Kapag naka-on ang recording, ise-save niya yung frame (kasama green boxes) sa .avi file!
                if cam.get("is_recording") and cam.get("video_writer"):
                    cam["video_writer"].write(frame)

                # --- Final Render to Dashboard ---
                if self.fullscreen_cam_data == cam:
                    self.render_video(frame, self.fs_video_label)
                elif not self.fullscreen_cam_data:
                    self.render_video(frame, cam["label"])
                    
        self.after(10, self.update_loop)

    def render_video(self, frame, label):
        try:
            tw, th = label.winfo_width(), label.winfo_height()
            if tw < 100: tw, th = 280, 180
            
            # --- FORCE ALL-ZOOM (Removes Black Letterboxing) ---
            resized = cv2.resize(frame, (tw, th), interpolation=cv2.INTER_AREA)
            img = Image.fromarray(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(tw, th))
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
        # BAGO: Burahin din sa Database!
        from sems_db import Database
        db = Database()
        db.delete_camera_by_name(cam_data["room_name"])
        db.close()

        cam_data["stream"].stop()
        if cam_data["face_detector"]: cam_data["face_detector"].close()
        if cam_data["pose_detector"]: cam_data["pose_detector"].close()
        cam_data["card"].destroy()
        self.active_cameras.remove(cam_data)
        
        # I-realign ang natitirang cameras
        for index, cam in enumerate(self.active_cameras):
            row, col = index // 3, index % 3
            cam["card"].grid(row=row, column=col, padx=12, pady=12, sticky="nsew")

    def on_closing(self):
        for cam in self.active_cameras: 
            cam["stream"].stop()
            if cam["face_detector"]: cam["face_detector"].close()
            if cam["pose_detector"]: cam["pose_detector"].close()
        self.destroy()

    def open_add_local_popup(self): 
        # Kung may bukas nang popup, isara muna
        if hasattr(self, 'active_popup') and self.active_popup is not None and self.active_popup.winfo_exists():
            self.active_popup.destroy()
        self.active_popup = AddLocalCameraPopup(self)

    def open_add_ip_popup(self): 
        # Kung may bukas nang popup, isara muna
        if hasattr(self, 'active_popup') and self.active_popup is not None and self.active_popup.winfo_exists():
            self.active_popup.destroy()
        self.active_popup = AddIPCameraPopup(self)

if __name__ == "__main__":
    app = SEMSDashboard()
    app.mainloop()