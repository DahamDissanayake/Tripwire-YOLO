import cv2
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
from ultralytics import YOLO
import threading
import time
import os
import datetime
import numpy as np
import webbrowser

# Set CustomTkinter appearance
ctk.set_appearance_mode("System")  # "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

class TripwireApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tripwire-YOLO Security System")
        self.root.geometry("1280x800")
        
        # Initialize variables
        self.is_running = False
        self.tripwire_points = []
        self.setting_tripwire = False
        self.counter = 0
        self.model = YOLO('yolov8n.pt') 
        self.track_history = {} 
        self.cap = None
        self.latest_frame = None
        self.lock = threading.Lock()
        
        if not os.path.exists('alerts'):
            os.makedirs('alerts')

        # Configure Grid Layout
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.setup_ui()

    def setup_ui(self):
        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self.root, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1) # Log area expands

        # Title
        self.logo_label = ctk.CTkLabel(self.sidebar, text="Tripwire AI", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0,padx=20, pady=(20, 10))

        # Camera Controls
        self.btn_start = ctk.CTkButton(self.sidebar, text="Start Camera", command=self.start_camera_thread, fg_color="#2ecc71", hover_color="#27ae60")
        self.btn_start.grid(row=1, column=0, padx=20, pady=10)

        self.btn_stop = ctk.CTkButton(self.sidebar, text="Stop Camera", command=self.stop_camera, state="disabled", fg_color="#e74c3c", hover_color="#c0392b")
        self.btn_stop.grid(row=2, column=0, padx=20, pady=10)

        # Tripwire Controls
        self.btn_set_tripwire = ctk.CTkButton(self.sidebar, text="Set Tripwire", command=self.enable_tripwire_setting)
        self.btn_set_tripwire.grid(row=3, column=0, padx=20, pady=10)
        
        self.btn_reset = ctk.CTkButton(self.sidebar, text="Reset Counter", command=self.reset_counter, fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"))
        self.btn_reset.grid(row=4, column=0, padx=20, pady=10)

        # Counter Display
        self.lbl_counter = ctk.CTkLabel(self.sidebar, text=f"Crossings: {self.counter}", font=ctk.CTkFont(size=20, weight="bold"), text_color="#e74c3c")
        self.lbl_counter.grid(row=5, column=0, padx=20, pady=(20, 10))

        # Log Area (Using Textbox)
        self.log_label = ctk.CTkLabel(self.sidebar, text="Event Log:", anchor="w")
        self.log_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        
        self.log_area = ctk.CTkTextbox(self.sidebar, width=200, height=200, corner_radius=5)
        self.log_area.grid(row=7, column=0, padx=20, pady=(0, 20), sticky="nsew")

        # Credits Section (Bottom of Sidebar)
        self.credits_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.credits_frame.grid(row=9, column=0, padx=20, pady=20, sticky="ew")

        ctk.CTkLabel(self.credits_frame, text="Developed by", font=ctk.CTkFont(size=12)).pack()
        
        self.link_label = ctk.CTkLabel(self.credits_frame, text="DAMA", font=ctk.CTkFont(size=14, weight="bold", underline=True), text_color=("#3B8ED0", "#1F6AA5"), cursor="hand2")
        self.link_label.pack()
        self.link_label.bind("<Button-1>", lambda e: self.open_link("https://github.com/DahamDissanayake/Tripwire-YOLO"))

        # --- Main Video Area ---
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color="black") # Use black background for video feel
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Video Display Label (Using Standard Tkinter Label inside CTkFrame for better image compatibility)
        self.lbl_video = tk.Label(self.main_frame, bg="black")
        self.lbl_video.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Bind events
        self.lbl_video.bind("<Button-1>", self.on_video_click)

    def open_link(self, url):
        webbrowser.open_new(url)

    def log_message(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)

    def start_camera_thread(self):
        if not self.is_running:
            self.is_running = True
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
            self.thread = threading.Thread(target=self.video_loop, daemon=True)
            self.thread.start()
            self.log_message("Camera started.")

    def stop_camera(self):
        self.is_running = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.log_message("Camera stopped.")

    def reset_counter(self):
        self.counter = 0
        self.lbl_counter.configure(text=f"Crossings: {self.counter}")
        self.log_message("Counter reset.")

    def enable_tripwire_setting(self):
        self.setting_tripwire = True
        self.tripwire_points = []
        self.log_message("Click 2 points to set tripwire.")

    def on_video_click(self, event):
        if self.setting_tripwire:
            x, y = event.x, event.y
            self.tripwire_points.append((x, y))
            self.log_message(f"Point set: {x}, {y}")
            
            if len(self.tripwire_points) == 2:
                self.setting_tripwire = False
                self.log_message("Tripwire set.")

    def video_loop(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.log_message("Error: Could not open camera.")
            self.is_running = False
            return

        while self.is_running:
            success, frame = self.cap.read()
            if not success:
                break

            results = self.model.track(frame, classes=0, persist=True, verbose=False)
            annotated_frame = results[0].plot()
            
            if len(self.tripwire_points) == 2:
                self.check_line_crossing(results, frame)
                pt1, pt2 = self.tripwire_points
                cv2.line(annotated_frame, pt1, pt2, (0, 0, 255), 2)

            rgb_image = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(rgb_image)
            
            self.current_pil_image = image
            self.root.after(0, self.update_ui_from_thread)
            
            time.sleep(0.01)

        self.cap.release()
        self.lbl_video.configure(image='')
        self.lbl_video.image = None

    def update_ui_from_thread(self):
        if hasattr(self, 'current_pil_image'):
            imgtk = ImageTk.PhotoImage(image=self.current_pil_image)
            self.lbl_video.configure(image=imgtk)
            self.lbl_video.image = imgtk

    def check_line_crossing(self, results, frame):
        A = np.array(self.tripwire_points[0])
        B = np.array(self.tripwire_points[1])
        
        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xywh.cpu()
            track_ids = results[0].boxes.id.int().cpu().tolist()
            
            for box, track_id in zip(boxes, track_ids):
                x, y, w, h = box
                centroid = np.array([float(x), float(y)])
                
                cross_product = (B[0] - A[0]) * (centroid[1] - A[1]) - (B[1] - A[1]) * (centroid[0] - A[0])
                current_side = 1 if cross_product > 0 else -1
                
                if track_id in self.track_history:
                    previous_side = self.track_history[track_id]
                    if previous_side != current_side:
                        self.trigger_alert(frame)
                        self.track_history[track_id] = current_side
                else:
                    self.track_history[track_id] = current_side

    def trigger_alert(self, frame):
        self.counter += 1
        timestamp = datetime.datetime.now().strftime("%H%M%S")
        
        self.root.after(0, lambda: self.lbl_counter.configure(text=f"Crossings: {self.counter}"))
        self.root.after(0, lambda: self.log_message(f"ALERT! Crossing detected."))
        self.root.after(0, lambda: self.flash_ui())
        
        filename = f"alerts/alert_{timestamp}.jpg"
        cv2.imwrite(filename, frame)
        self.root.after(0, lambda: self.log_message(f"Snapshot saved."))

    def flash_ui(self):
        self.sidebar.configure(fg_color="#e74c3c") # Red alert
        self.root.after(200, lambda: self.sidebar.configure(fg_color=["gray90", "gray13"])) # Reset to default (approx)

if __name__ == "__main__":
    root = ctk.CTk()
    app = TripwireApp(root)
    
    def on_closing():
        app.stop_camera()
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
