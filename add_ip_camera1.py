import customtkinter as ctk

class AddIPCameraPopup(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.main_app = parent  # <--- FIX 1: Explicitly save the main dashboard
        self.title("Add IP Camera")
        
        # --- Centering Logic ---
        width, height = 400, 550
        self.geometry(f"{width}x{height}")
        
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")
        # -----------------------

        self.configure(fg_color="#3a3a3b")
        self.attributes("-topmost", True)
        self.grab_set()
        self.setup_ui()

    def setup_ui(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(expand=True, fill="both", padx=40, pady=20)

        # Room Name
        ctk.CTkLabel(main, text="Room Name:", font=("Segoe UI", 14)).pack(pady=(10, 2), anchor="w")
        self.ent_room = ctk.CTkEntry(main, width=250, placeholder_text="e.g. Room 101")
        self.ent_room.pack(pady=5)

        # Username
        ctk.CTkLabel(main, text="Username:", font=("Segoe UI", 14)).pack(pady=(10, 2), anchor="w")
        self.ent_user = ctk.CTkEntry(main, width=250, placeholder_text="Camera Username")
        self.ent_user.pack(pady=5)

        # Password
        ctk.CTkLabel(main, text="Password:", font=("Segoe UI", 14)).pack(pady=(10, 2), anchor="w")
        self.ent_pass = ctk.CTkEntry(main, width=250, show="*", placeholder_text="Camera Password")
        self.ent_pass.pack(pady=5)

        # IP Address / URL
        ctk.CTkLabel(main, text="IP Address / RTSP Path:", font=("Segoe UI", 14)).pack(pady=(10, 2), anchor="w")
        self.ent_url = ctk.CTkEntry(main, width=250, placeholder_text="192.168.1.100:554")
        self.ent_url.pack(pady=5)

        # Camera Type
        ctk.CTkLabel(main, text="Camera Type:", font=("Segoe UI", 14)).pack(pady=(10, 2), anchor="w")
        self.option_type = ctk.CTkOptionMenu(main, values=["Exam Monitoring", "Room Decorum"], width=250)
        self.option_type.pack(pady=5)

        # Confirm Button
        ctk.CTkButton(main, text="Confirm & Connect", fg_color="#1f538d", 
                      hover_color="#14375e", command=self.confirm_action).pack(pady=30)

    def confirm_action(self):
        room = self.ent_room.get()
        user = self.ent_user.get()
        password = self.ent_pass.get()
        path = self.ent_url.get()
        cam_type = self.option_type.get()

        if room and path:
            # FIX 2: Tapo cameras need "/stream1". This automatically adds it if you forgot!
            if not path.endswith("/stream1") and not path.endswith("/stream2"):
                path = f"{path}/stream1"

            if user and password:
                full_url = f"rtsp://{user}:{password}@{path}"
            else:
                full_url = f"rtsp://{path}"

            print(f"DEBUG: Connecting to {full_url}")
            
            # FIX 3: Use self.main_app to successfully send data back to the dashboard
            self.main_app.add_camera_card_live(room, cam_type, url=full_url)
            self.destroy()