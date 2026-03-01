import customtkinter as ctk
from PIL import Image, ImageDraw, ImageOps
from main_dashboard import SEMSDashboard 

class SEMSCompactSplash(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        width, height = 450, 250
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        
        bg_hex = "#121212"
        self.config(bg=bg_hex)
        self.attributes("-transparentcolor", bg_hex)

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w // 2) - (width // 2)
        y = (screen_h // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.after_id = None

        # --- Image Processing ---
        img_path = r"C:\Users\My PC\Logos\logo.png"
        radius = 35 

        try:
            img = Image.open(img_path).convert("RGBA")
            img = ImageOps.fit(img, (width, height), Image.Resampling.LANCZOS)
            mask = Image.new('L', (width, height), 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=255)
            img.putalpha(mask)

            self.logo_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(width, height))
            self.bg_label = ctk.CTkLabel(self, image=self.logo_ctk, text="", bg_color=bg_hex)
            self.bg_label.pack()
        except:
            self.label = ctk.CTkLabel(self, text="SEMS", font=("Orbitron", 30), text_color="white")
            self.label.pack(expand=True)

        # --- Progress Bar ---
        self.progress = ctk.CTkProgressBar(
            self, width=width-120, height=6, corner_radius=10,
            progress_color="#FF3131", fg_color="#1a1a1a", border_width=0
        )
        self.progress.place(relx=0.5, rely=0.88, anchor="center")
        self.progress.set(0)

        self.loading_step(0)

    def loading_step(self, val):
        if val <= 1.0:
            self.progress.set(val)
            # 30ms * 100 iterations = 3 seconds
            self.after_id = self.after(30, lambda: self.loading_step(val + 0.01))
        else:
            self.after(100, self.open_dashboard)

    def open_dashboard(self):
        if self.after_id:
            self.after_cancel(self.after_id)
        self.withdraw()
        main_app = SEMSDashboard()
        self.destroy()
        main_app.mainloop()

if __name__ == "__main__":
    app = SEMSCompactSplash()
    app.mainloop()