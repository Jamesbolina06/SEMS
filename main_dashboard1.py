import customtkinter as ctk
import cv2
from PIL import Image
from reports1 import ReportsFrame
from replay_system1 import ReplaySystemFrame
from add_local_camera1 import AddLocalCameraPopup
from add_ip_camera1 import AddIPCameraPopup

class SEMSDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SEMS (Smart Examination Monitoring System)")
        self.geometry("1200x750")
        self.configure(fg_color="#1a1a1b")
        
        # --- List to hold active camera dictionaries ---
        self.active_cameras = []
        self.fullscreen_cam_data = None # Tracks which camera is currently in full screen
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color="#111112")
        self.sidebar.pack(side="left", fill="y")
        
        ctk.CTkLabel(self.sidebar, text="SEMS", font=("Segoe UI", 35, "bold"), text_color="white").pack(pady=(50, 5))
        ctk.CTkLabel(self.sidebar, text="● System Active", font=("Segoe UI", 11, "bold"), text_color="#00FF00").pack(pady=(0, 40))
        
        self.btn_dash = self.create_nav_btn("📊 Dashboard", self.show_dashboard)
        self.btn_reports = self.create_nav_btn("📋 Reports", self.show_reports)
        self.btn_replay = self.create_nav_btn("🔄 Replay System", self.show_replay)

        self.session_info = ctk.CTkLabel(self.sidebar, 
            text="Currently Monitored Session\nSession ID: 20251119-001\nUser: Admin\nMidterm Exam",
            font=("Segoe UI", 11), text_color="#777777", justify="left")
        self.session_info.pack(side="bottom", pady=30, padx=20, anchor="w")

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(side="right", expand=True, fill="both")

        # Initialize Content Frames
        self.dashboard_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.setup_dashboard_ui()
        
        self.fullscreen_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.setup_fullscreen_ui() # Setup the new full screen layout
        
        self.reports_frame = ReportsFrame(self.container)
        self.replay_frame = ReplaySystemFrame(self.container)

        self.show_dashboard()
        
        # Start the video update loop
        self.update_cameras()

    def setup_dashboard_ui(self):
        header = ctk.CTkFrame(self.dashboard_frame, height=80, fg_color="transparent")
        header.pack(side="top", fill="x", padx=30, pady=(20, 10))
        ctk.CTkLabel(header, text="Camera Monitoring", font=("Segoe UI", 26, "bold"), text_color="white").pack(side="left")

        ctk.CTkButton(header, text="+ Add IP Camera", fg_color="#1f538d", width=140, 
                      command=self.open_add_ip_popup).pack(side="right", padx=5)
        
        ctk.CTkButton(header, text="+ Add Local Camera", fg_color="#3a3a3b", width=140, 
                      command=self.open_add_local_popup).pack(side="right", padx=5)

        self.scroll = ctk.CTkScrollableFrame(self.dashboard_frame, fg_color="transparent")
        self.scroll.pack(expand=True, fill="both", padx=20, pady=10)
        self.grid_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.grid_frame.pack(expand=True, fill="both")
        
        # Force a strict 3-column layout
        self.grid_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="col")

    def setup_fullscreen_ui(self):
        # Header for full screen
        header = ctk.CTkFrame(self.fullscreen_frame, height=60, fg_color="transparent")
        header.pack(side="top", fill="x", padx=30, pady=15)
        
        self.fs_title = ctk.CTkLabel(header, text="Room Monitoring", font=("Segoe UI", 24, "bold"), text_color="white")
        self.fs_title.pack(side="left")
        
        btn_back = ctk.CTkButton(header, text="✖ Stop Monitoring", fg_color="#ff4d4d", hover_color="#cc0000", command=self.exit_fullscreen)
        btn_back.pack(side="right")
        
        # Large Video Container
        self.fs_video_container = ctk.CTkFrame(self.fullscreen_frame, fg_color="#000000")
        self.fs_video_container.pack(expand=True, fill="both", padx=30, pady=(0, 30))
        
        self.fs_video_label = ctk.CTkLabel(self.fs_video_container, text="")
        self.fs_video_label.pack(expand=True, fill="both")

    def add_camera_card_live(self, room_name):
        index = len(self.active_cameras)
        row = index // 3
        col = index % 3
        
        card = ctk.CTkFrame(self.grid_frame, fg_color="#252526", corner_radius=12)
        card.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")
        
        view = ctk.CTkFrame(card, fg_color="#000000", height=180, width=280)
        view.pack(expand=True, fill="both", padx=8, pady=8)
        view.pack_propagate(False) 
        
        video_label = ctk.CTkLabel(view, text="")
        video_label.pack(expand=True, fill="both")
        
        # Initialize the webcam 
        cap_index = len(self.active_cameras) 
        cap = cv2.VideoCapture(cap_index)
        
        cam_data = {
            "cap": cap,
            "label": video_label,
            "card": card,
            "room_name": room_name
        }
        self.active_cameras.append(cam_data)
        
        # Make the video label clickable for Full Screen
        video_label.bind("<Button-1>", lambda event, c=cam_data: self.enter_fullscreen(c))
        
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(info_frame, text=room_name, font=("Segoe UI", 14, "bold"), text_color="#eeeeee").pack(side="left")
        
        btn_remove = ctk.CTkButton(info_frame, text="✖", width=25, height=25, 
                                   fg_color="#ff4d4d", hover_color="#cc0000", 
                                   corner_radius=12,
                                   command=lambda c=cam_data: self.remove_camera(c))
        btn_remove.pack(side="right")

    def enter_fullscreen(self, cam_data):
        self.fullscreen_cam_data = cam_data
        self.fs_title.configure(text=f"{cam_data['room_name']} - Full Screen Monitoring")
        
        self.dashboard_frame.pack_forget()
        self.fullscreen_frame.pack(expand=True, fill="both")

    def exit_fullscreen(self):
        self.fullscreen_cam_data = None
        self.fullscreen_frame.pack_forget()
        self.dashboard_frame.pack(expand=True, fill="both")

    def remove_camera(self, cam_data):
        if cam_data["cap"].isOpened():
            cam_data["cap"].release()
        cam_data["card"].destroy()
        self.active_cameras.remove(cam_data)
        self.rearrange_grid()
        
        # If the removed camera was in full screen, exit full screen
        if self.fullscreen_cam_data == cam_data:
            self.exit_fullscreen()

    def rearrange_grid(self):
        for index, cam in enumerate(self.active_cameras):
            row = index // 3
            col = index % 3
            cam["card"].grid(row=row, column=col, padx=12, pady=12, sticky="nsew")

    def update_cameras(self):
        # Loop through all cameras. We MUST read from all of them so buffers don't overflow.
        for cam in self.active_cameras:
            cap = cam["cap"]
            
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    if self.fullscreen_cam_data and self.fullscreen_cam_data == cam:
                        # Full-Screen Resizing
                        fs_width = self.fs_video_label.winfo_width()
                        fs_height = self.fs_video_label.winfo_height()
                        
                        if fs_width < 100 or fs_height < 100:
                            fs_width, fs_height = 800, 500

                        fs_frame = cv2.resize(frame, (fs_width, fs_height))
                        rgb_fs = cv2.cvtColor(fs_frame, cv2.COLOR_BGR2RGB)
                        img_fs = Image.fromarray(rgb_fs)
                        ctk_img_fs = ctk.CTkImage(light_image=img_fs, dark_image=img_fs, size=(fs_width, fs_height))
                        
                        self.fs_video_label.configure(image=ctk_img_fs)
                        self.fs_video_label.image = ctk_img_fs
                    
                    elif not self.fullscreen_cam_data:
                        # --- FIX: Dynamic Grid Resizing ---
                        grid_width = cam["label"].winfo_width()
                        grid_height = cam["label"].winfo_height()
                        
                        # Fallback in case UI is still booting up
                        if grid_width < 100 or grid_height < 100:
                            grid_width, grid_height = 280, 180

                        # Stretch the video to fill the current black container
                        small_frame = cv2.resize(frame, (grid_width, grid_height))
                        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                        img_small = Image.fromarray(rgb_small)
                        ctk_img_small = ctk.CTkImage(light_image=img_small, dark_image=img_small, size=(grid_width, grid_height))
                        
                        cam["label"].configure(image=ctk_img_small)
                        cam["label"].image = ctk_img_small

        self.after(15, self.update_cameras)

    def open_add_local_popup(self): 
        AddLocalCameraPopup(self)

    def open_add_ip_popup(self):
        AddIPCameraPopup(self)
    
    def create_nav_btn(self, text, command):
        btn = ctk.CTkButton(self.sidebar, text=text, anchor="w", fg_color="transparent", hover_color="#2d2d2e", height=45, command=command)
        btn.pack(fill="x", padx=15, pady=4)
        return btn

    def show_dashboard(self):
        self.reports_frame.pack_forget()
        self.replay_frame.pack_forget()
        
        # Check if we are in full screen or not
        if self.fullscreen_cam_data:
            self.fullscreen_frame.pack(expand=True, fill="both")
        else:
            self.dashboard_frame.pack(expand=True, fill="both")
            
        self.update_btn_style(self.btn_dash)

    def show_reports(self):
        self.dashboard_frame.pack_forget()
        self.replay_frame.pack_forget()
        self.fullscreen_frame.pack_forget() # Hide full screen if active
        self.reports_frame.pack(expand=True, fill="both")
        self.update_btn_style(self.btn_reports)

    def show_replay(self):
        self.dashboard_frame.pack_forget()
        self.reports_frame.pack_forget()
        self.fullscreen_frame.pack_forget() # Hide full screen if active
        self.replay_frame.pack(expand=True, fill="both")
        self.update_btn_style(self.btn_replay)

    def update_btn_style(self, active_btn):
        for b in [self.btn_dash, self.btn_reports, self.btn_replay]: 
            b.configure(fg_color="transparent")
        active_btn.configure(fg_color="#2d2d2e")

    def on_closing(self):
        for cam in self.active_cameras:
            if cam["cap"].isOpened():
                cam["cap"].release()
        self.destroy()

if __name__ == "__main__":
    app = SEMSDashboard()
    app.mainloop()