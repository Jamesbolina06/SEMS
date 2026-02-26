import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import time
import os

# ==========================================
# 1. SEMS SPLASH SCREEN
# ==========================================
class SEMSSplashScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True) 
        self.root.configure(bg="black")
        
        width, height = 600, 350
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        logo_path = r"C:\Users\My PC\Logos\logo.png"
        try:
            img = Image.open(logo_path) 
            img = img.resize((600, 300), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(img)
            self.label = tk.Label(self.root, image=self.photo, bg="black", bd=0)
            self.label.pack()
        except:
            self.label = tk.Label(self.root, text="SEMS", fg="#2ecc71", bg="black", font=("Arial", 40, "bold"))
            self.label.pack(pady=80)

        style = ttk.Style()
        style.theme_use('default')
        style.configure("green.Horizontal.TProgressbar", foreground='#2ecc71', background='#2ecc71', thickness=5)
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=580, mode="determinate", style="green.Horizontal.TProgressbar")
        self.progress.pack(pady=5)
        
        self.step = 0
        self.update_progress()
        self.root.mainloop()

    def update_progress(self):
        if self.step < 100:
            self.step += 10
            self.progress['value'] = self.step
            self.root.after(30, self.update_progress)
        else:
            self.root.destroy()
            start_main_system()

# ==========================================
# 2. MAIN SEMS PRECISION MONITOR
# ==========================================
class SEMSPrecisionMonitor:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        self.window.configure(bg="#000000")

        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')

        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.frame_to_process = None
        
        # Siguradong list ang initial values
        self.detected_data = {"faces": [], "profiles_r": [], "profiles_l": []}
        
        self.look_start_time = None
        self.VIOLATION_DELAY = 2.0 # Tinaasan ko na rin ng konti para hindi masyadong sensitive
        
        if not os.path.exists("exam_violations"):
            os.makedirs("exam_violations")

        self.canvas = tk.Canvas(window, width=960, height=540, bg="#000000", highlightthickness=0)
        self.canvas.pack(padx=10, pady=10)
        
        self.stop_event = threading.Event()
        self.ai_thread = threading.Thread(target=self.detection_engine, daemon=True)
        self.ai_thread.start()
        
        self.update_ui()
        self.window.protocol("WM_DELETE_WINDOW", self.cleanup)

    def detection_engine(self):
        while not self.stop_event.is_set():
            if self.frame_to_process is not None:
                frame = self.frame_to_process.copy()
                proc_w = 400
                proc_h = int(frame.shape[0] * (proc_w / frame.shape[1]))
                small_gray = cv2.cvtColor(cv2.resize(frame, (proc_w, proc_h)), cv2.COLOR_BGR2GRAY)
                
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                small_gray = clahe.apply(small_gray)

                # Force convert results to list para iwas TypeError
                faces = self.face_cascade.detectMultiScale(small_gray, 1.1, 6, minSize=(25, 25))
                self.detected_data["faces"] = list(faces) if len(faces) > 0 else []

                profiles_l = self.profile_cascade.detectMultiScale(small_gray, 1.1, 10, minSize=(25, 25))
                self.detected_data["profiles_l"] = list(profiles_l) if len(profiles_l) > 0 else []
                
                flipped_gray = cv2.flip(small_gray, 1)
                temp_r = self.profile_cascade.detectMultiScale(flipped_gray, 1.1, 10, minSize=(25, 25))
                
                profiles_r = []
                if len(temp_r) > 0:
                    for (rx, ry, rw, rh) in temp_r:
                        profiles_r.append((proc_w - rx - rw, ry, rw, rh))
                self.detected_data["profiles_r"] = profiles_r
                
                # Violation Logic
                if len(profiles_r) > 0 or len(self.detected_data["profiles_l"]) > 0:
                    if self.look_start_time is None:
                        self.look_start_time = time.time()
                    else:
                        elapsed = time.time() - self.look_start_time
                        if elapsed >= self.VIOLATION_DELAY:
                            cv2.imwrite(f"exam_violations/sustained_{int(time.time())}.jpg", frame)
                            self.look_start_time = time.time() 
                else:
                    self.look_start_time = None

            time.sleep(0.05)

    def update_ui(self):
        if not self.stop_event.is_set():
            ret, frame = self.cap.read()
            if ret:
                self.frame_to_process = frame
                display_frame = cv2.resize(frame, (960, 540))
                scale = 960 / 400

                # Drawing Green
                for (x, y, w, h) in self.detected_data["faces"]:
                    cx, cy = int((x + w/2) * scale), int((y + h/2) * scale)
                    cv2.circle(display_frame, (cx, cy), int((w/2) * scale), (0, 255, 0), 1)

                # Drawing Red (Dito yung fix sa concatenation)
                all_profiles = self.detected_data["profiles_r"] + self.detected_data["profiles_l"]
                for (x, y, w, h) in all_profiles:
                    cx, cy = int((x + w/2) * scale), int((y + h/2) * scale)
                    cv2.circle(display_frame, (cx, cy), int((w/2) * scale), (0, 0, 255), 2)

                img = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                img_tk = ImageTk.PhotoImage(image=Image.fromarray(img))
                self.canvas.imgtk = img_tk
                self.canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
            
            self.window.after(15, self.update_ui)

    def cleanup(self):
        self.stop_event.set()
        self.cap.release()
        self.window.destroy()

def start_main_system():
    main_root = tk.Tk()
    app = SEMSPrecisionMonitor(main_root, "SEMS Classroom CCTV v13.1")
    main_root.mainloop()

if __name__ == "__main__":
    SEMSSplashScreen()