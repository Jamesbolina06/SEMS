import customtkinter as ctk
from tkinter import messagebox

class ReplaySystemFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(20, 10))
        ctk.CTkLabel(header, text="Replay System", font=("Segoe UI", 32), text_color="white").pack(side="left")
        
        # Ibinalik ang Line Separator
        line = ctk.CTkFrame(self, height=1, fg_color="#444444")
        line.pack(fill="x", padx=30, pady=(0, 20))

        self.scroll_view = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_view.pack(expand=True, fill="both", padx=20)
        
        self.grid_frame = ctk.CTkFrame(self.scroll_view, fg_color="transparent")
        self.grid_frame.pack(expand=True, fill="both")

        sample_data = [("Room 1", "11/20/2025"), ("Room 2", "11/20/2025")]
        for i, (room, date) in enumerate(sample_data):
            self.add_replay_card(room, date, i)

    def add_replay_card(self, room_name, date, index):
        row, col = index // 3, index % 3
        card_container = ctk.CTkFrame(self.grid_frame, fg_color="transparent")
        card_container.grid(row=row, column=col, padx=15, pady=20)
        
        btn_card = ctk.CTkButton(card_container, fg_color="#2b2b2b", hover_color="#3d3d3e",
                                 text="", width=270, height=220, corner_radius=10,
                                 command=lambda r=room_name: self.play_video(r))
        btn_card.grid(row=0, column=0) 

        thumb = ctk.CTkFrame(btn_card, width=240, height=130, fg_color="#888888", corner_radius=4)
        thumb.grid(row=0, column=0, padx=15, pady=(15, 5))
        thumb.grid_propagate(False)

        ctk.CTkLabel(btn_card, text=f"{room_name}\n({date})", font=("Segoe UI", 13), text_color="white").grid(row=1, column=0, pady=(0, 15))

    def play_video(self, room_name):
        messagebox.showinfo("Replay System", f"Playing video for {room_name}...")