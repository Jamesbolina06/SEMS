import customtkinter as ctk

class LiveMonitorView:
    def __init__(self, parent_frame, zoom_command):
        # Header
        header = ctk.CTkFrame(parent_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(header, text="Live Feed", font=("Arial", 22, "bold")).pack(side="left")

        # Grid system for 6 cameras
        grid_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=20, pady=10)

        camera_status = [1, 1, 0, 1, 0, 0]

        for i in range(6):
            r, c = divmod(i, 3)
            room_num = i + 1
            
            cam_box = ctk.CTkButton(
                grid_frame, text="", fg_color="#222222", corner_radius=12, border_width=1, border_color="#444444",
                hover_color="#2a2a2a", command=lambda r_id=room_num: zoom_command(r_id)
            )
            cam_box.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
            
            # Status Indicator
            color = "#2ecc71" if camera_status[i] == 1 else "#e74c3c"
            status_lbl = ctk.CTkLabel(cam_box, text=f"● {'LIVE' if camera_status[i] == 1 else 'OFFLINE'}", 
                                      text_color=color, font=("Arial", 10, "bold"))
            status_lbl.place(relx=0.05, rely=0.08)
            
            ctk.CTkLabel(cam_box, text=f"ROOM {room_num}", font=("Arial", 14, "bold")).place(relx=0.5, rely=0.5, anchor="center")

        grid_frame.grid_columnconfigure((0,1,2), weight=1)
        grid_frame.grid_rowconfigure((0,1), weight=1)