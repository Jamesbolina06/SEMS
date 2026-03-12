import customtkinter as ctk
from PIL import Image, ImageDraw, ImageOps
from main_dashboard1 import SEMSDashboard 

# Notice we changed ctk.CTk to ctk.CTkToplevel
class SEMSCompactSplash(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)

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
        img_path = r"C:\Users\420\OneDrive\Documents\SEMS Capstone\SEMS\images\logo.png"
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
            # 20ms * 100 iterations = 2 seconds
            self.after_id = self.after(20, lambda: self.loading_step(val + 0.01))
        else:
            self.after(100, self.open_dashboard)

    def open_dashboard(self):
        if self.after_id:
            self.after_cancel(self.after_id)
            
        # Destroy the splash screen popup
        self.destroy()
        
        # Un-hide the main dashboard!
        self.master.deiconify()

if __name__ == "__main__":
    # 1. Create the Main Dashboard FIRST (This makes it the official root window)
    main_app = SEMSDashboard()
    
    # 2. Hide the dashboard immediately so the user doesn't see it yet
    main_app.withdraw()
    
    # 3. Create the Splash Screen and pass the dashboard as its master
    splash = SEMSCompactSplash(main_app)
    
    # 4. Start the application loop
    main_app.mainloop()