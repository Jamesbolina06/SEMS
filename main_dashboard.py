import customtkinter as ctk

class SEMSDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Configuration ---
        self.title("SEMS - Smart Examination Monitoring System")
        self.geometry("1200x750")
        self.configure(fg_color="#1a1a1b")

        # --- Theme Colors ---
        self.sidebar_color = "#111112"
        self.card_color = "#252526"
        self.accent_blue = "#1f538d"
        self.offline_red = "#ff4d4d"
        self.overlay_bg = "#000000" # Background ng overlay

        # --- 1. SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=self.sidebar_color)
        self.sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(self.sidebar, text="SEMS", font=("Segoe UI", 35, "bold"), text_color="white").pack(pady=(50, 5))
        ctk.CTkLabel(self.sidebar, text="● SYSTEM STANDBY", font=("Segoe UI", 11, "bold"), text_color="#aaaaaa").pack(pady=(0, 40))

        for text in ["📊  Dashboard", "📋  Reports", "⚙️  Settings"]:
            ctk.CTkButton(self.sidebar, text=text, anchor="w", fg_color="transparent", hover_color="#2d2d2e", height=45).pack(fill="x", padx=15, pady=4)

        self.user_info = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.user_info.pack(side="bottom", fill="x", padx=25, pady=30)
        ctk.CTkLabel(self.user_info, text="ADMINISTRATOR", font=("Segoe UI", 12, "bold"), text_color="white").pack(anchor="w")
        ctk.CTkLabel(self.user_info, text="Session: Midterm-2026\nID: 20251119-001", font=("Segoe UI", 11), text_color="#777777", justify="left").pack(anchor="w")

        # --- 2. MAIN CONTENT AREA ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(side="right", expand=True, fill="both")

        # Header
        self.header = ctk.CTkFrame(self.main_container, height=80, fg_color="transparent")
        self.header.pack(side="top", fill="x", padx=30, pady=(20, 10))
        ctk.CTkLabel(self.header, text="Camera Monitoring", font=("Segoe UI", 26, "bold"), text_color="white").pack(side="left")

        ctk.CTkButton(self.header, text="+ Add IP Camera", fg_color=self.accent_blue, width=140).pack(side="right", padx=5)
        
        # Open Popup Button
        self.btn_local = ctk.CTkButton(self.header, text="+ Add Local Camera", fg_color="#3a3a3b", width=140, command=self.show_local_popup)
        self.btn_local.pack(side="right", padx=5)

        # Scrollable Camera Grid
        self.scroll_view = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        self.scroll_view.pack(expand=True, fill="both", padx=20, pady=10)
        
        self.grid_frame = ctk.CTkFrame(self.scroll_view, fg_color="transparent")
        self.grid_frame.pack(expand=True, fill="both")

        # Default 6 Offline slots
        self.camera_count = 0
        for i in range(6):
            self.add_camera_card(f"Room 0{i+1}", is_live=False)

        # --- 3. THE POPUP OVERLAY (Semi-Transparent Fix) ---
        # Ginamit ang master 'self' para maplace ito sa ibabaw ng dashboard
        self.overlay = ctk.CTkFrame(self, fg_color=self.overlay_bg, corner_radius=0)
        
        # Center box (Add Local Camera Form)
        self.popup_box = ctk.CTkFrame(self.overlay, width=400, height=380, fg_color="#3a3a3b", corner_radius=15)
        self.popup_box.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(self.popup_box, text="Add Local Camera", font=("Segoe UI", 20, "bold"), text_color="white").pack(pady=(30, 20))

        # Input Text fields with padding (para hindi sagad sa gilid)
        ctk.CTkLabel(self.popup_box, text="Camera Name:", font=("Segoe UI", 14), text_color="white").pack(pady=(5, 0), padx=40, anchor="w")
        self.ent_cam = ctk.CTkEntry(self.popup_box, width=320, height=35, fg_color="#aaaaaa", text_color="black", border_width=0)
        self.ent_cam.pack(pady=(5, 15), padx=40)

        ctk.CTkLabel(self.popup_box, text="Room Name:", font=("Segoe UI", 14), text_color="white").pack(pady=(5, 0), padx=40, anchor="w")
        self.ent_room = ctk.CTkEntry(self.popup_box, width=320, height=35, fg_color="#aaaaaa", text_color="black", border_width=0)
        self.ent_room.pack(pady=(5, 15), padx=40)

        # Buttons Row
        self.btn_frame = ctk.CTkFrame(self.popup_box, fg_color="transparent")
        self.btn_frame.pack(pady=(20, 20))

        self.btn_cancel = ctk.CTkButton(self.btn_frame, text="Cancel", fg_color="#555555", width=120, height=35, command=self.hide_local_popup)
        self.btn_cancel.pack(side="left", padx=10)

        self.btn_confirm = ctk.CTkButton(self.btn_frame, text="Confirm", fg_color="#222222", hover_color="#111111", width=120, height=35, command=self.handle_confirm)
        self.btn_confirm.pack(side="left", padx=10)

    def add_camera_card(self, room_name, is_live=False):
        # Logic para ilagay sa grid ang bagong card
        row = self.camera_count // 3
        col = self.camera_count % 3
        
        card = ctk.CTkFrame(self.grid_frame, fg_color=self.card_color, corner_radius=12, border_width=1, border_color="#333334")
        card.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")
        self.grid_frame.grid_columnconfigure(col, weight=1)
        
        # Video View Area
        view = ctk.CTkFrame(card, fg_color="#000000", height=180)
        view.pack(expand=True, fill="both", padx=8, pady=8)
        
        status_text = "LIVE FEED" if is_live else "NO SIGNAL"
        status_color = "#333333" if not is_live else "#1a1a1b"
        ctk.CTkLabel(view, text=status_text, font=("Segoe UI", 10, "bold"), text_color=status_color).place(relx=0.5, rely=0.5, anchor="center")
        
        # Info Bar
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(fill="x", padx=12, pady=(0, 10))
        
        ctk.CTkLabel(info, text=room_name, font=("Segoe UI", 14, "bold"), text_color="#eeeeee").pack(side="left")
        
        # Label Status
        dot_color = "#00FF00" if is_live else self.offline_red
        dot_text = "● LIVE" if is_live else "○ OFFLINE"
        ctk.CTkLabel(info, text=dot_text, font=("Segoe UI", 11, "bold"), text_color=dot_color).pack(side="right")
        
        self.camera_count += 1

    def show_local_popup(self):
        # Gawing semi-transparent background sa dashboard
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.overlay.lift()

    def hide_local_popup(self):
        self.overlay.place_forget()

    def handle_confirm(self):
        room_input = self.ent_room.get()
        if room_input.strip(): # Check kung hindi empty
            self.add_camera_card(room_input, is_live=True)
            self.hide_local_popup()
            # Reset inputs
            self.ent_cam.delete(0, 'end')
            self.ent_room.delete(0, 'end')

if __name__ == "__main__":
    app = SEMSDashboard()
    app.mainloop()