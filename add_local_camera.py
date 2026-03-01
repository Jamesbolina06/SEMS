import customtkinter as ctk

class AddLocalCameraPopup(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        # --- Window Setup ---
        self.title("Add Local Camera")
        self.geometry("400x350") # Medyo nilakihan ko para hindi siksikan
        self.resizable(False, False)
        self.configure(fg_color="#3a3a3b") 
        
        # Gawing Modal
        self.attributes("-topmost", True)
        self.grab_set() 

        # I-center sa dashboard
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (400 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (350 // 2)
        self.geometry(f"+{x}+{y}")

        # Protocol para sa "X" button
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # --- THE REAL FIX ---
        # Hintayin muna natin na maging "visible" ang window bago i-load ang widgets.
        # Ito ang gamot sa "Too early to use font" error.
        self.wait_visibility() 
        self.setup_ui()

    def setup_ui(self):
        # Frame para sa organization
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(expand=True, fill="both", padx=40, pady=20)

        # Camera Name Section
        self.lbl_cam = ctk.CTkLabel(self.main_frame, text="Camera Name:", font=("Segoe UI", 16), text_color="white")
        self.lbl_cam.pack(pady=(15, 5), anchor="w")
        
        self.ent_cam = ctk.CTkEntry(self.main_frame, width=250, height=35, fg_color="#aaaaaa", text_color="black", border_width=0)
        self.ent_cam.pack(pady=5)

        # Room Name Section
        self.lbl_room = ctk.CTkLabel(self.main_frame, text="Room Name:", font=("Segoe UI", 16), text_color="white")
        self.lbl_room.pack(pady=(15, 5), anchor="w")
        
        self.ent_room = ctk.CTkEntry(self.main_frame, width=250, height=35, fg_color="#aaaaaa", text_color="black", border_width=0)
        self.ent_room.pack(pady=5)

        # Confirm Button
        self.btn_confirm = ctk.CTkButton(self.main_frame, text="Confirm", 
                                        fg_color="#222222", hover_color="#111111", 
                                        width=180, height=45, corner_radius=10,
                                        font=("Segoe UI", 15, "bold"),
                                        command=self.confirm_action)
        self.btn_confirm.pack(pady=(30, 10))

    def confirm_action(self):
        # Print sa terminal para makita mong gumagana
        print(f"DEBUG: Saved {self.ent_cam.get()} at {self.ent_room.get()}")
        self.on_close()

    def on_close(self):
        self.grab_release() # Napaka-importante nito para ma-close ang window
        self.destroy()