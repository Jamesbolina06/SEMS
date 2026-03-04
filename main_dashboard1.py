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
        # Changed this to a list of dicts to easily track the capture, label, and UI card
        self.active_cameras = []
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

    def add_camera_card_live(self, room_name):
        # Calculate row and column based on current number of active cameras
        index = len(self.active_cameras)
        row = index // 3
        col = index % 3
        
        card = ctk.CTkFrame(self.grid_frame, fg_color="#252526", corner_radius=12)
        card.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")
        
        # Video View Area (Fixed size to prevent UI stretching)
        view = ctk.CTkFrame(card, fg_color="#000000", height=180, width=280)
        view.pack(expand=True, fill="both", padx=8, pady=8)
        view.pack_propagate(False) # Prevents the frame from shrinking/expanding
        
        # Create a label to hold the video stream
        video_label = ctk.CTkLabel(view, text="")
        video_label.pack(expand=True, fill="both")
        
        # Initialize the webcam (0 for first camera, 1 for second, etc.)
        # Note: In a real scenario, you might want to specify the index or let the user choose
        cap_index = len(self.active_cameras) 
        cap = cv2.VideoCapture(cap_index)
        
        # Store all components in a dictionary
        cam_data = {
            "cap": cap,
            "label": video_label,
            "card": card,
            "room_name": room_name
        }
        self.active_cameras.append(cam_data)
        
        # Info row at the bottom of the card
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(info_frame, text=room_name, font=("Segoe UI", 14, "bold"), text_color="#eeeeee").pack(side="left")
        
        # --- NEW: The 'X' Button to remove the camera ---
        btn_remove = ctk.CTkButton(info_frame, text="✖", width=25, height=25, 
                                   fg_color="#ff4d4d", hover_color="#cc0000", 
                                   corner_radius=12,
                                   command=lambda c=cam_data: self.remove_camera(c))
        btn_remove.pack(side="right")

    def remove_camera(self, cam_data):
        # 1. Stop the video capture
        if cam_data["cap"].isOpened():
            cam_data["cap"].release()
        
        # 2. Destroy the UI card widget
        cam_data["card"].destroy()
        
        # 3. Remove from our active list
        self.active_cameras.remove(cam_data)
        
        # 4. Re-draw the grid so there are no empty gaps
        self.rearrange_grid()

    def rearrange_grid(self):
        # Loop through remaining active cameras and update their grid positions
        for index, cam in enumerate(self.active_cameras):
            row = index // 3
            col = index % 3
            cam["card"].grid(row=row, column=col, padx=12, pady=12, sticky="nsew")

    def update_cameras(self):
        # Continuously fetch frames for all active cameras
        for cam in self.active_cameras:
            cap = cam["cap"]
            label = cam["label"]
            
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    # Resize to fit the UI card nicely
                    frame = cv2.resize(frame, (280, 180))
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(rgb_frame)
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(280, 180))
                    
                    label.configure(image=ctk_img)
                    label.image = ctk_img

        # Refresh every ~15ms
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
        self.dashboard_frame.pack(expand=True, fill="both")
        self.update_btn_style(self.btn_dash)

    def show_reports(self):
        self.dashboard_frame.pack_forget()
        self.replay_frame.pack_forget()
        self.reports_frame.pack(expand=True, fill="both")
        self.update_btn_style(self.btn_reports)

    def show_replay(self):
        self.dashboard_frame.pack_forget()
        self.reports_frame.pack_forget()
        self.replay_frame.pack(expand=True, fill="both")
        self.update_btn_style(self.btn_replay)

    def update_btn_style(self, active_btn):
        for b in [self.btn_dash, self.btn_reports, self.btn_replay]: 
            b.configure(fg_color="transparent")
        active_btn.configure(fg_color="#2d2d2e")

    def on_closing(self):
        # Release all webcams when the app is closed
        for cam in self.active_cameras:
            if cam["cap"].isOpened():
                cam["cap"].release()
        self.destroy()

if __name__ == "__main__":
    app = SEMSDashboard()
    app.mainloop()