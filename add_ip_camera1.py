import customtkinter as ctk
from tkinter import messagebox

class AddIPCameraPopup(ctk.CTkToplevel):
    def __init__(self, parent_dashboard):
        super().__init__()
        
        self.parent_dashboard = parent_dashboard
        self.title("Add IP Camera (Wi-Fi)")
        
        window_width = 450
        window_height = 450
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_cordinate = int((screen_width / 2) - (window_width / 2))
        y_cordinate = int((screen_height / 2) - (window_height / 2))
        self.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")
        
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.focus_force()

        ctk.CTkLabel(self, text="IP Camera Configuration", font=("Segoe UI", 18, "bold")).pack(pady=(20, 10))
        ctk.CTkLabel(self, text="Connect Tapo or any IP Camera via Wi-Fi", font=("Segoe UI", 11), text_color="#777777").pack(pady=(0, 20))

        ctk.CTkLabel(self, text="Room Name:", anchor="w").pack(fill="x", padx=40)
        self.room_name_entry = ctk.CTkEntry(self, placeholder_text="e.g. Room 101")
        self.room_name_entry.pack(fill="x", padx=40, pady=(0, 15))

        ctk.CTkLabel(self, text="Camera IP Address / RTSP Link:", anchor="w").pack(fill="x", padx=40)
        self.ip_entry = ctk.CTkEntry(self, placeholder_text="e.g. 192.168.8.105")
        self.ip_entry.pack(fill="x", padx=40, pady=(0, 15))

        cred_frame = ctk.CTkFrame(self, fg_color="transparent")
        cred_frame.pack(fill="x", padx=40, pady=(0, 15))
        cred_frame.columnconfigure(0, weight=1)
        cred_frame.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(cred_frame, text="Username:", anchor="w").grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.user_entry = ctk.CTkEntry(cred_frame, placeholder_text="Username")
        self.user_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5))
        
        # --- PASSWORD WITH EYE ICON ---
        ctk.CTkLabel(cred_frame, text="Password:", anchor="w").grid(row=0, column=1, sticky="ew", padx=(5, 0))
        pass_container = ctk.CTkFrame(cred_frame, fg_color="transparent")
        pass_container.grid(row=1, column=1, sticky="ew", padx=(5, 0))
        pass_container.columnconfigure(0, weight=1)

        self.pass_entry = ctk.CTkEntry(pass_container, placeholder_text="Password", show="*")
        self.pass_entry.grid(row=0, column=0, sticky="ew")

        self.show_btn = ctk.CTkButton(pass_container, text="👁", width=30, fg_color="#3a3a3b", hover_color="#4a4a4a", command=self.toggle_pass)
        self.show_btn.grid(row=0, column=1, padx=(5, 0))

        ctk.CTkLabel(self, text="Monitoring Type:", anchor="w").pack(fill="x", padx=40)
        self.cam_type_combobox = ctk.CTkComboBox(self, values=["Exam Monitoring", "Room Decorum"])
        self.cam_type_combobox.pack(fill="x", padx=40, pady=(0, 20))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=40, pady=10)
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="#4a4a4a", hover_color="#333333", width=100, command=self.destroy).pack(side="left", expand=True)
        ctk.CTkButton(btn_frame, text="Connect IP", fg_color="#28a745", hover_color="#218838", width=100, command=self.submit_camera).pack(side="right", expand=True)

    # Function para i-show/hide ang password
    def toggle_pass(self):
        if self.pass_entry.cget("show") == "*":
            self.pass_entry.configure(show="")
            self.show_btn.configure(text="Hide") 
        else:
            self.pass_entry.configure(show="*")
            self.show_btn.configure(text="👁")

    def submit_camera(self):
        room = self.room_name_entry.get().strip()
        ip_input = self.ip_entry.get().strip() 
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()
        cam_type = self.cam_type_combobox.get()

        if not room or not ip_input:
            # FIX: Patayin muna ang topmost para hindi mag-hide ang warning
            self.attributes("-topmost", False)
            messagebox.showwarning("Incomplete Data", "Please fill in the Room Name and IP/RTSP Link.")
            self.attributes("-topmost", True)
            self.focus_force()
            return

        # SMART RTSP LOGIC
        if ip_input.lower().startswith("rtsp://"):
            rtsp_link = ip_input 
        else:
            if not username or not password:
                # FIX: Patayin muna ang topmost 
                self.attributes("-topmost", False)
                messagebox.showwarning("Incomplete Data", "Username and Password are required for Tapo IP Addresses.")
                self.attributes("-topmost", True)
                self.focus_force()
                return
            rtsp_link = f"rtsp://{username}:{password}@{ip_input}:554/stream1"

        try:
            self.parent_dashboard.add_camera_card_live(room_name=room, cam_type=cam_type, url=rtsp_link)
            
            # --- THE FIX: BURAHIN MUNA ANG FORM BAGO MAG-MESSAGEBOX ---
            self.destroy() 
            messagebox.showinfo("Success", f"Camera for {room} connected via Wi-Fi successfully!")
            
        except Exception as e:
            # FIX: Patayin muna ang topmost para sa error popup
            self.attributes("-topmost", False)
            messagebox.showerror("Connection Error", f"Failed to connect to IP Camera.\nError: {e}")
            self.attributes("-topmost", True)
            self.focus_force()