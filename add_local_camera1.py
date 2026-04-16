import customtkinter as ctk
from tkinter import messagebox

class AddLocalCameraPopup(ctk.CTkToplevel):
    def __init__(self, parent_dashboard):
        super().__init__()
        
        self.parent_dashboard = parent_dashboard
        self.title("Add LAN Camera (Direct Connection)")
        
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

        ctk.CTkLabel(self, text="LAN Camera Configuration", font=("Segoe UI", 18, "bold")).pack(pady=(20, 10))
        ctk.CTkLabel(self, text="Connect Tapo directly to laptop via Ethernet", font=("Segoe UI", 11), text_color="#777777").pack(pady=(0, 20))

        ctk.CTkLabel(self, text="Room Name:", anchor="w").pack(fill="x", padx=40)
        self.room_name_entry = ctk.CTkEntry(self, placeholder_text="e.g. Defense Room")
        self.room_name_entry.pack(fill="x", padx=40, pady=(0, 15))

        ctk.CTkLabel(self, text="Static LAN IP Address:", anchor="w").pack(fill="x", padx=40)
        self.ip_entry = ctk.CTkEntry(self, placeholder_text="e.g. 192.168.254.10")
        # Tinanggal natin yung .insert() para blangko siya pag-open
        self.ip_entry.pack(fill="x", padx=40, pady=(0, 15))

        cred_frame = ctk.CTkFrame(self, fg_color="transparent")
        cred_frame.pack(fill="x", padx=40, pady=(0, 15))
        cred_frame.columnconfigure(0, weight=1)
        cred_frame.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(cred_frame, text="Tapo Username:", anchor="w").grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.user_entry = ctk.CTkEntry(cred_frame, placeholder_text="Username")
        self.user_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5))
        
        # --- PASSWORD WITH EYE ICON ---
        ctk.CTkLabel(cred_frame, text="Tapo Password:", anchor="w").grid(row=0, column=1, sticky="ew", padx=(5, 0))
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
        ctk.CTkButton(btn_frame, text="Connect LAN", fg_color="#28a745", hover_color="#218838", width=100, command=self.submit_camera).pack(side="right", expand=True)

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
        ip_address = self.ip_entry.get().strip()
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()
        cam_type = self.cam_type_combobox.get()

        # Validation kung may naiwang blangko
        if not room or not ip_address or not username or not password:
            # FIX: Patayin muna ang topmost para makita ang warning popup!
            self.attributes("-topmost", False) 
            messagebox.showwarning("Incomplete Data", "Please fill in all fields (Room, IP, Username, Password).")
            self.attributes("-topmost", True) # Ibalik ang topmost pagka-click ng OK
            self.focus_force()
            return

        # Kusa na niyang bubuuin ang RTSP link
        rtsp_link = f"rtsp://{username}:{password}@{ip_address}:554/stream1"

        try:
            # I-pasa ang nabuong RTSP link sa Dashboard mo
            self.parent_dashboard.add_camera_card_live(room_name=room, cam_type=cam_type, url=rtsp_link)
            
            # --- THE FIX: BURAHIN MUNA ANG FORM BAGO MAG-MESSAGEBOX ---
            self.destroy() 
            messagebox.showinfo("Success", f"Camera for {room} connected via LAN successfully!")
            
        except Exception as e:
            # FIX: Patayin muna ang topmost para makita ang error popup!
            self.attributes("-topmost", False)
            messagebox.showerror("Connection Error", f"Failed to connect to LAN Camera.\nError: {e}")
            self.attributes("-topmost", True)
            self.focus_force()