import customtkinter as ctk

class AddIPCameraPopup(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        # --- Window Setup ---
        self.title("Add IP Camera")
        # Increased height to 520 to fit the new fields
        self.geometry("400x520") 
        self.resizable(False, False)
        self.configure(fg_color="#3a3a3b") 
        
        # Modal Settings
        self.attributes("-topmost", True)
        self.grab_set() 

        # Center logic
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (400 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (520 // 2)
        self.geometry(f"+{x}+{y}")

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Explicit fonts para iwas sa "Too early to use font" error
        self.default_font = ("Segoe UI", 13)
        self.header_font = ("Segoe UI", 14, "bold")
        self.button_font = ("Segoe UI", 15, "bold")

        self.setup_ui()

    def setup_ui(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(expand=True, fill="both", padx=40, pady=10)

        # IP Address Section
        ctk.CTkLabel(self.main_frame, text="Camera IP Address:", font=self.header_font, text_color="white").pack(pady=(10, 2), anchor="w")
        self.ent_ip = ctk.CTkEntry(self.main_frame, width=280, height=35, placeholder_text="e.g., 192.168.1.50", fg_color="#aaaaaa", text_color="black", border_width=0, font=self.default_font)
        self.ent_ip.pack(pady=2)

        # RTSP Username Section
        ctk.CTkLabel(self.main_frame, text="Username:", font=self.header_font, text_color="white").pack(pady=(10, 2), anchor="w")
        self.ent_user = ctk.CTkEntry(self.main_frame, width=280, height=35, placeholder_text="admin", fg_color="#aaaaaa", text_color="black", border_width=0, font=self.default_font)
        self.ent_user.pack(pady=2)

        # RTSP Password Section (Hidden text)
        ctk.CTkLabel(self.main_frame, text="Password:", font=self.header_font, text_color="white").pack(pady=(10, 2), anchor="w")
        self.ent_pass = ctk.CTkEntry(self.main_frame, width=280, height=35, placeholder_text="password", fg_color="#aaaaaa", text_color="black", border_width=0, font=self.default_font, show="*")
        self.ent_pass.pack(pady=2)

        # Room Name Section
        ctk.CTkLabel(self.main_frame, text="Room Name:", font=self.header_font, text_color="white").pack(pady=(10, 2), anchor="w")
        self.ent_room = ctk.CTkEntry(self.main_frame, width=280, height=35, fg_color="#aaaaaa", text_color="black", border_width=0, font=self.default_font)
        self.ent_room.pack(pady=2)

        # Confirm Button
        self.btn_confirm = ctk.CTkButton(self.main_frame, text="Connect IP Cam", 
                                        fg_color="#1f538d", hover_color="#163e6a", 
                                        width=180, height=45, corner_radius=10,
                                        font=self.button_font,
                                        command=self.confirm_action)
        self.btn_confirm.pack(pady=(25, 10))

    def confirm_action(self):
        ip_address = self.ent_ip.get().strip()
        username = self.ent_user.get().strip()
        password = self.ent_pass.get().strip()
        room_name = self.ent_room.get().strip()
        
        # Check if all fields have been filled out
        if ip_address and username and password and room_name:
            
            # Construct the RTSP URL format standard for Tapo C5 and most IP Cameras
            rtsp_url = f"rtsp://{username}:{password}@{ip_address}:554/stream1"
            
            print(f"DEBUG: Constructed RTSP Link: {rtsp_url}")
            
            # Send the room name and the constructed URL back to the main dashboard
            # Note: We will need to update your dashboard to accept the rtsp_url next!
            self.master.add_camera_card_live(room_name) 
            
            self.on_close()

    def on_close(self):
        self.grab_release()
        self.destroy()