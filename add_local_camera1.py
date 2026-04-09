import customtkinter as ctk

class AddLocalCameraPopup(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.main_app = parent  # <--- FIX 1: Explicitly save the main dashboard
        self.title("Add Local Camera")
        
        # --- Centering Logic ---
        width, height = 400, 450
        self.geometry(f"{width}x{height}")
        
        # Calculate coordinates relative to parent
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
        ctk.CTkLabel(main, text="Room Name:", font=("Segoe UI", 14)).pack(pady=5, anchor="w")
        self.ent_room = ctk.CTkEntry(main, width=250)
        self.ent_room.pack(pady=5)
        ctk.CTkLabel(main, text="Monitoring Type:", font=("Segoe UI", 14)).pack(pady=5, anchor="w")
        self.option_type = ctk.CTkOptionMenu(main, values=["Exam Monitoring", "Room Decorum"], width=250)
        self.option_type.pack(pady=5)
        ctk.CTkButton(main, text="Confirm", command=self.confirm_action).pack(pady=30)

    def confirm_action(self):
        room = self.ent_room.get()
        cam_type = self.option_type.get()
        if room:
            # FIX 2: Use self.main_app instead of self.master to send data
            self.main_app.add_camera_card_live(room, cam_type, url=None)
            self.destroy()