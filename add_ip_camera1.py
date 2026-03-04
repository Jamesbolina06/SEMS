import customtkinter as ctk

class AddIPCameraPopup(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        # --- Window Setup ---
        self.title("Add IP Camera")
        self.geometry("400x350") 
        self.resizable(False, False)
        self.configure(fg_color="#3a3a3b") 
        
        # Modal Settings
        self.attributes("-topmost", True)
        self.grab_set() 

        # Center logic
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (400 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (350 // 2)
        self.geometry(f"+{x}+{y}")

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Explicit fonts para iwas sa "Too early to use font" error
        self.default_font = ("Segoe UI", 13)
        self.header_font = ("Segoe UI", 16)
        self.button_font = ("Segoe UI", 15, "bold")

        self.setup_ui()

    def setup_ui(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(expand=True, fill="both", padx=40, pady=20)

        # IP Address / Stream URL Section
        ctk.CTkLabel(self.main_frame, text="IP Address / URL:", font=self.header_font, text_color="white").pack(pady=(15, 5), anchor="w")
        self.ent_ip = ctk.CTkEntry(self.main_frame, width=280, height=35, placeholder_text="rtsp://192.168...", fg_color="#aaaaaa", text_color="black", border_width=0, font=self.default_font)
        self.ent_ip.pack(pady=5)

        # Room Name Section
        ctk.CTkLabel(self.main_frame, text="Room Name:", font=self.header_font, text_color="white").pack(pady=(15, 5), anchor="w")
        self.ent_room = ctk.CTkEntry(self.main_frame, width=280, height=35, fg_color="#aaaaaa", text_color="black", border_width=0, font=self.default_font)
        self.ent_room.pack(pady=5)

        # Confirm Button
        self.btn_confirm = ctk.CTkButton(self.main_frame, text="Connect IP Cam", 
                                        fg_color="#1f538d", hover_color="#163e6a", 
                                        width=180, height=45, corner_radius=10,
                                        font=self.button_font,
                                        command=self.confirm_action)
        self.btn_confirm.pack(pady=(30, 10))

    def confirm_action(self):
        room_name = self.ent_room.get()
        ip_url = self.ent_ip.get()
        if room_name.strip() and ip_url.strip():
            # Tatawagin ang function sa dashboard para magdagdag ng live card
            self.master.add_camera_card_live(room_name, is_live=True)
            print(f"DEBUG: Connecting to IP Camera at {ip_url}")
        self.on_close()

    def on_close(self):
        self.grab_release()
        self.destroy()