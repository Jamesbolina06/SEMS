import customtkinter as ctk
from tkinter import ttk, messagebox
import os
from sems_db import Database

class ReportsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        
        self.db = Database()

        # --- HEADER SECTION ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(20, 10))
        ctk.CTkLabel(header, text="Exam Violations Report", font=("Segoe UI", 32, "bold"), text_color="white").pack(side="left")
        
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")
        
        self.view_btn = ctk.CTkButton(btn_frame, text="View Video Evidence", fg_color="#1f538d", command=self.view_snapshot)
        self.view_btn.pack(side="left", padx=5)
        
        self.del_btn = ctk.CTkButton(btn_frame, text="Delete", fg_color="#ff4d4d", hover_color="#cc0000", command=self.delete_record)
        self.del_btn.pack(side="left", padx=5)

        # --- SEARCH BAR SECTION ---
        search_container = ctk.CTkFrame(self, fg_color="transparent")
        search_container.pack(fill="x", padx=30, pady=(0, 10))
        
        ctk.CTkLabel(search_container, text="🔍 Search Room:", font=("Segoe UI", 14, "bold"), text_color="#aaaaaa").pack(side="left", padx=(0, 10))
        self.search_entry = ctk.CTkEntry(search_container, placeholder_text="Enter room name...", width=300)
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", self.search_records)

        self.setup_table()
        self.load_from_db()

    def setup_table(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0, rowheight=35)
        style.configure("Treeview.Heading", background="#3a3a3b", foreground="white", relief="flat")
        style.map("Treeview", background=[('selected', '#1f538d')])

        tree_frame = ctk.CTkFrame(self, fg_color="transparent")
        tree_frame.pack(expand=True, fill="both", padx=30, pady=(0, 10))

        tree_scroll_y = ctk.CTkScrollbar(tree_frame, orientation="vertical")
        tree_scroll_y.pack(side="right", fill="y")
        
        tree_scroll_x = ctk.CTkScrollbar(tree_frame, orientation="horizontal")
        tree_scroll_x.pack(side="bottom", fill="x")

        # BAGO: Dinagdag ang "Room Type" sa columns
        self.tree = ttk.Treeview(tree_frame, columns=("DB_ID", "No.", "Room Name", "Room Type", "Violation Type", "Date & Time", "File Path"), 
                                 show='headings', 
                                 displaycolumns=("No.", "Room Name", "Room Type", "Violation Type", "Date & Time", "File Path"),
                                 yscrollcommand=tree_scroll_y.set, 
                                 xscrollcommand=tree_scroll_x.set)
        
        tree_scroll_y.configure(command=self.tree.yview)
        tree_scroll_x.configure(command=self.tree.xview)
        
        self.tree.heading("No.", text="No.")
        self.tree.column("No.", anchor="center", width=50, minwidth=50, stretch=False)
        
        self.tree.heading("Room Name", text="Room Name")
        self.tree.column("Room Name", anchor="center", width=120, minwidth=120)

        # BAGO: Header para sa Room Type
        self.tree.heading("Room Type", text="Room Type")
        self.tree.column("Room Type", anchor="center", width=150, minwidth=150)
        
        self.tree.heading("Violation Type", text="Violation Type")
        self.tree.column("Violation Type", anchor="center", width=250, minwidth=250)
        
        self.tree.heading("Date & Time", text="Date & Time")
        self.tree.column("Date & Time", anchor="center", width=200, minwidth=200)
        
        self.tree.heading("File Path", text="File Path")
        self.tree.column("File Path", anchor="w", width=450, minwidth=450)
        
        self.tree.bind("<Button-1>", self.on_click_clear)
        self.tree.pack(expand=True, fill="both")

    def on_click_clear(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region not in ("tree", "cell"):
            self.tree.selection_remove(self.tree.selection())

    def load_from_db(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        records = self.db.fetch_all_violations()
        display_index = 1
        
        for rec in records:
            db_id = rec[0]
            abs_path = os.path.abspath(str(rec[5]))
            
            # --- BAGO: AUTO-CLEANUP GHOST RECORDS ---
            # Iche-check ng system kung totoong nasa folder pa yung video.
            # Kung hindi nai-save o nabura sa folder, buburahin na rin niya sa Database!
            if not os.path.exists(abs_path):
                self.db.delete_violation(db_id)
                continue # Laktawan at wag nang ipakita sa table
                
            # Kung nag-e-exist yung video, ilagay sa table
            self.tree.insert("", "end", values=(db_id, display_index, rec[1], rec[2], rec[3], rec[4], rec[5]))
            display_index += 1

    def search_records(self, event=None):
        search_query = self.search_entry.get().lower()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        records = self.db.fetch_all_violations()
        display_index = 1
        
        for rec in records:
            db_id = rec[0]
            abs_path = os.path.abspath(str(rec[5]))
            
            # --- BAGO: AUTO-CLEANUP GHOST RECORDS ---
            if not os.path.exists(abs_path):
                self.db.delete_violation(db_id)
                continue
                
            room_name = str(rec[1]).lower()
            if search_query in room_name:
                self.tree.insert("", "end", values=(db_id, display_index, rec[1], rec[2], rec[3], rec[4], rec[5]))
                display_index += 1
    def add_report_entry(self):
        self.search_entry.delete(0, 'end')
        self.load_from_db()

    def view_snapshot(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Record", "Please select a record to view.")
            return
        
        data = self.tree.item(selected[0])['values']
        abs_path = os.path.abspath(data[6]) # Updated index dahil na-move ang file path sa dulo
        
        if os.path.exists(abs_path):
            os.startfile(abs_path) 
            self.tree.selection_remove(self.tree.selection())
        else:
            messagebox.showerror("Error", f"Video file not found at:\n{abs_path}")

    def delete_record(self):
        selected_items = self.tree.selection()
        
        if not selected_items:
            messagebox.showwarning("Select Record", "Please select at least one record to delete.")
            return
            
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {len(selected_items)} selected violation(s)?"):
            for item in selected_items:
                data = self.tree.item(item)['values']
                rec_id = data[0]
                
                # BAGO: Mas pinatibay na pagbasa ng file path
                file_path = str(data[6]) 
                abs_path = os.path.normpath(file_path)
                
                # 1. Burahin muna sa Database
                self.db.delete_violation(rec_id)
                
                # 2. Burahin sa mismong "violations" folder
                if os.path.exists(abs_path):
                    try: 
                        os.remove(abs_path)
                        print(f"SUCCESS: File Deleted -> {abs_path}")
                    except Exception as e: 
                        print(f"ERROR: {e}")
                else:
                    print(f"WARNING: This file is no longer existed -> {abs_path}")
            
            # I-refresh ang UI table
            self.search_entry.delete(0, 'end') 
            self.load_from_db()