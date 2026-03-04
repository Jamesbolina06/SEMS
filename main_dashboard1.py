import customtkinter as ctk
from reports1 import ReportsFrame
from replay_system1 import ReplaySystemFrame
from add_local_camera1 import AddLocalCameraPopup
from add_ip_camera1 import AddIPCameraPopup # Idinagdag natin ito para sa bagong popup

class SEMSDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SEMS (Smart Examination Monitoring System)")
        self.geometry("1200x750")
        self.configure(fg_color="#1a1a1b")

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

    def setup_dashboard_ui(self):
        header = ctk.CTkFrame(self.dashboard_frame, height=80, fg_color="transparent")
        header.pack(side="top", fill="x", padx=30, pady=(20, 10))
        ctk.CTkLabel(header, text="Camera Monitoring", font=("Segoe UI", 26, "bold"), text_color="white").pack(side="left")

        # --- FIX SA INDENTATION DITO ---
        ctk.CTkButton(header, text="+ Add IP Camera", fg_color="#1f538d", width=140, 
                      command=self.open_add_ip_popup).pack(side="right", padx=5)
        
        ctk.CTkButton(header, text="+ Add Local Camera", fg_color="#3a3a3b", width=140, 
                      command=self.open_add_local_popup).pack(side="right", padx=5)

        self.scroll = ctk.CTkScrollableFrame(self.dashboard_frame, fg_color="transparent")
        self.scroll.pack(expand=True, fill="both", padx=20, pady=10)
        self.grid_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.grid_frame.pack(expand=True, fill="both")

        self.room_count = 0
        for i in range(3): 
            self.add_camera_card_live(f"Room 0{i+1}", is_live=False)

    def add_camera_card_live(self, room_name, is_live=True):
        row, col = self.room_count // 3, self.room_count % 3
        card = ctk.CTkFrame(self.grid_frame, fg_color="#252526", corner_radius=12)
        card.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")
        self.grid_frame.grid_columnconfigure(col, weight=1)
        
        view = ctk.CTkFrame(card, fg_color="#000000", height=180)
        view.pack(expand=True, fill="both", padx=8, pady=8)
        ctk.CTkLabel(view, text="OFFLINE", font=("Segoe UI", 12), text_color="#333333").place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(card, text=room_name, font=("Segoe UI", 14, "bold"), text_color="#eeeeee").pack(pady=(0, 10), padx=12, anchor="w")
        self.room_count += 1

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

if __name__ == "__main__":
    app = SEMSDashboard()
    app.mainloop()