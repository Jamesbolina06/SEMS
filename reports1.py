import customtkinter as ctk
from tkinter import ttk

class ReportsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(20, 10))
        ctk.CTkLabel(header, text="Reports", font=("Segoe UI", 32, "bold"), text_color="white").pack(side="right")
        
        self.setup_table()

    def setup_table(self):
        # I-set up ang style para mag-match sa dark theme
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0, rowheight=35)
        style.configure("Treeview.Heading", background="#3a3a3b", foreground="white", relief="flat")
        style.map("Treeview", background=[('selected', '#1f538d')])

        self.tree = ttk.Treeview(self, columns=("No.", "Room Name", "Date", "Snapshots"), show='headings')
        for col in ("No.", "Room Name", "Date", "Snapshots"):
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=150)
        
        # Sample Data para hindi blanko
        sample_rows = [
            ("1", "Room 01", "2025-11-20", "snap_001.jpg"),
            ("2", "Room 02", "2025-11-20", "snap_002.jpg")
        ]
        for row in sample_rows:
            self.tree.insert("", "end", values=row)

        self.tree.pack(expand=True, fill="both", padx=30, pady=20)