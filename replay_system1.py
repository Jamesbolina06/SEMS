import customtkinter as ctk
import cv2
from PIL import Image
import os
from tkinter import messagebox
from sems_db import Database

class ReplaySystemFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self.db = Database()

        # Set para i-store kung aling mga video ID ang naka-check
        self.selected_records = set()

        # --- HEADER SECTION ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(20, 10))
        ctk.CTkLabel(header, text="Replay System", font=("Segoe UI", 32, "bold"), text_color="white").pack(side="left")

        # --- BAGO: Delete Selected Button (Nasa taas na) ---
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")
        self.del_btn = ctk.CTkButton(btn_frame, text="Delete", fg_color="#ff4d4d", hover_color="#cc0000", command=self.delete_selected)
        self.del_btn.pack(side="left", padx=5)

        # --- BAGO: SEARCH BAR SECTION ---
        search_container = ctk.CTkFrame(self, fg_color="transparent")
        search_container.pack(fill="x", padx=30, pady=(0, 10))
        
        ctk.CTkLabel(search_container, text="🔍 Search Room:", font=("Segoe UI", 14, "bold"), text_color="#aaaaaa").pack(side="left", padx=(0, 10))
        self.search_entry = ctk.CTkEntry(search_container, placeholder_text="Enter room name...", width=300)
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", self.search_records)

        # --- MAIN SCROLLABLE CONTAINER ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(expand=True, fill="both", padx=20, pady=10)
        
        # BAGO: Ginawang 4 Columns at naka-center ang distribute ng space
        self.scroll_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.load_from_db()

    def load_from_db(self, search_query=""):
        # I-clear ang mga na-check na boxes tuwing nagre-refresh
        self.selected_records.clear()

        # Linisin muna ang loob ng scroll frame
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        records = self.db.fetch_all()
        
        # Filter kung may tinype sa search bar
        if search_query:
            records = [rec for rec in records if search_query in str(rec[1]).lower()]

        # BAGO: Centered Empty Label (Ginamit ang grid at columnspan=4 para gitnang-gitna!)
        if not records:
            empty_label = ctk.CTkLabel(self.scroll_frame, text="No recorded monitoring yet.", font=("Segoe UI", 16), text_color="#777777")
            empty_label.grid(row=0, column=0, columnspan=4, pady=150, sticky="nsew") 
            return

        # Gumawa ng cards para sa bawat video
        for index, rec in enumerate(records):
            db_id, room, cam_type, date_time, file_path = rec
            self.create_video_card(db_id, room, date_time, file_path, index)

    def search_records(self, event=None):
        query = self.search_entry.get().lower()
        self.load_from_db(search_query=query)

    def add_recorded_video(self, db_id, room, start_date, saved_filepath):
        self.search_entry.delete(0, 'end')
        self.load_from_db()

    # BAGO: Logic para mag-add/remove ng db_id kapag kiniclick ang Checkbox
    def toggle_select(self, db_id):
        if db_id in self.selected_records:
            self.selected_records.remove(db_id)
        else:
            self.selected_records.add(db_id)

    def create_video_card(self, db_id, room, date_time, file_path, index):
        # 4 na column para maganda spacing sa Full Screen
        row = index // 4
        col = index % 4
        
        card = ctk.CTkFrame(self.scroll_frame, fg_color="#252526", corner_radius=12)
        # BAGO: sticky="n" keeps it centered horizontally in its column, no more stretching!
        card.grid(row=row, column=col, padx=15, pady=15, sticky="n")
        
        img_ctk = None
        if os.path.exists(file_path):
            cap = cv2.VideoCapture(file_path)
            ret, frame = cap.read()
            cap.release()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (280, 160))
                pil_img = Image.fromarray(frame)
                img_ctk = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(280, 160))

        thumb_label = ctk.CTkLabel(card, text="No Preview" if not img_ctk else "", image=img_ctk, fg_color="black", width=280, height=160, corner_radius=8)
        thumb_label.pack(padx=10, pady=(10, 5))
        thumb_label.bind("<Button-1>", lambda e, p=file_path: self.play_video(p))
        
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        text_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(text_frame, text=room, font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ctk.CTkLabel(text_frame, text=date_time, font=("Segoe UI", 11), text_color="#aaaaaa").pack(anchor="w")
        
        # BAGO: Checkbox imbes na maliit na 'X' button
        checkbox = ctk.CTkCheckBox(info_frame, text="", width=24, command=lambda id=db_id: self.toggle_select(id))
        checkbox.pack(side="right", padx=(5, 0))

    def play_video(self, file_path):
        abs_path = os.path.abspath(file_path)
        if os.path.exists(abs_path):
            os.startfile(abs_path)
        else:
            messagebox.showerror("Error", f"Video file not found:\n{abs_path}")

    # BAGO: Delete Selected Logic
    def delete_selected(self):
        if not self.selected_records:
            messagebox.showwarning("Select Record", "Please select at least one recording to delete.")
            return

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {len(self.selected_records)} selected recording(s)?"):
            
            # Kukunin lahat ng records tapos hahanapin yung mga nag-match sa na-check mo
            records = self.db.fetch_all()
            for rec in records:
                db_id, _, _, _, file_path = rec
                
                if db_id in self.selected_records:
                    # Burahin sa DB
                    self.db.delete_record(db_id)
                    # Burahin yung mismong .avi file
                    abs_path = os.path.abspath(file_path)
                    if os.path.exists(abs_path):
                        try: os.remove(abs_path)
                        except: pass
            
            # I-reload yung UI pagkatapos burahin
            self.load_from_db(search_query=self.search_entry.get().lower())