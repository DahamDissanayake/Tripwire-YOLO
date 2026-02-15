import cv2
import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk
from ultralytics import YOLO
import threading
import time
import os
import datetime
import numpy as np

class TripwireApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Virtual Tripwire Security System")
        self.root.geometry("1200x800")
        
        # Initialize variables
        self.is_running = False
        self.tripwire_points = []
        self.setting_tripwire = False
        self.counter = 0
        self.model = YOLO('yolov8n.pt')  # Load YOLOv8n model
        self.track_history = {} # Store previous side for each track ID
        self.cap = None
        self.latest_frame = None
        self.lock = threading.Lock()
        
        # Create alerts directory
        if not os.path.exists('alerts'):
            os.makedirs('alerts')

        # GUI Layout
        self.setup_ui()

    def setup_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self.root, width=250, bg="#2c3e50")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        # Title in Sidebar
        tk.Label(self.sidebar, text="Control Panel", font=("Helvetica", 16, "bold"), bg="#2c3e50", fg="white").pack(pady=20)

        # Buttons
        self.btn_style = {"font": ("Helvetica", 12), "bg": "#34495e", "fg": "white", "width": 20, "pady": 5}
        
        self.btn_start = tk.Button(self.sidebar, text="Start Camera", command=self.start_camera_thread, **self.btn_style)
        self.btn_start.pack(pady=10)

        self.btn_stop = tk.Button(self.sidebar, text="Stop Camera", command=self.stop_camera, state=tk.DISABLED, **self.btn_style)
        self.btn_stop.pack(pady=10)

        self.btn_set_tripwire = tk.Button(self.sidebar, text="Set Tripwire", command=self.enable_tripwire_setting, **self.btn_style)
        self.btn_set_tripwire.pack(pady=10)
        
        self.btn_reset = tk.Button(self.sidebar, text="Reset Counter", command=self.reset_counter, **self.btn_style)
        self.btn_reset.pack(pady=10)

        # Counter Display
        self.lbl_counter = tk.Label(self.sidebar, text=f"Crossings: {self.counter}", font=("Helvetica", 20, "bold"), bg="#2c3e50", fg="#e74c3c")
        self.lbl_counter.pack(pady=30)

        # History Log
        tk.Label(self.sidebar, text="Event History:", font=("Helvetica", 12), bg="#2c3e50", fg="white").pack(anchor="w", padx=10)
        self.log_area = scrolledtext.ScrolledText(self.sidebar, height=15, width=28, font=("Consolas", 9))
        self.log_area.pack(pady=5, padx=10)
        
        # Main Video Area
        self.video_frame_container = tk.Frame(self.root, bg="black")
        self.video_frame_container.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        
        self.lbl_video = tk.Label(self.video_frame_container, bg="black")
        self.lbl_video.pack(expand=True)
        
        # Bind mouse events to the video label for tripwire setting
        self.lbl_video.bind("<Button-1>", self.on_video_click)

    def log_message(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)

    def start_camera_thread(self):
        if not self.is_running:
            self.is_running = True
            self.btn_start.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.NORMAL)
            self.thread = threading.Thread(target=self.video_loop, daemon=True)
            self.thread.start()
            self.log_message("Camera started.")

    def stop_camera(self):
        self.is_running = False
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.log_message("Camera stopped.")

    def reset_counter(self):
        self.counter = 0
        self.lbl_counter.config(text=f"Crossings: {self.counter}")
        self.log_message("Counter reset.")

    def enable_tripwire_setting(self):
        self.setting_tripwire = True
        self.tripwire_points = []
        self.log_message("Click 2 points to set tripwire.")

    def on_video_click(self, event):
        if self.setting_tripwire:
            # We need to map the click coordinates on the label to the actual image coordinates
            # This implementation assumes the displayed image fits the label or we handle scaling.
            # For simplicity in this version, we will assume 1:1 or use relative if scaled.
            # Better approach: store raw coordinates and scale during drawing.
            # Here: just taking the event x,y. NOTE: This might need adjustment if image is resized.
            
            x, y = event.x, event.y
            self.tripwire_points.append((x, y))
            self.log_message(f"Point set: {x}, {y}")
            
            if len(self.tripwire_points) == 2:
                self.setting_tripwire = False
                self.log_message("Tripwire set.")

    def video_loop(self):
        # Open webcam
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.log_message("Error: Could not open camera.")
            self.is_running = False
            return

        while self.is_running:
            success, frame = self.cap.read()
            if not success:
                break

            # Resize frame for better performance/fit (optional)
            # frame = cv2.resize(frame, (1280, 720)) # Example
            
            # Use threading lock if updating shared resources strictly, 
            # but for simple reading/displaying, we can manage.
            
            # YOLO Tracking
            # Detect only person class (class 0)
            results = self.model.track(frame, classes=0, persist=True, verbose=False)
            
            # Process detections
            annotated_frame = results[0].plot() # Default plot
            
            # Check tripwire
            if len(self.tripwire_points) == 2:
                self.check_line_crossing(results, frame)
                # Draw tripwire manually on top of annotated frame
                pt1, pt2 = self.tripwire_points
                cv2.line(annotated_frame, pt1, pt2, (0, 0, 255), 2)

            # Convert to Tkinter format
            # OpenCV is BGR, Pillow uses RGB
            rgb_image = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(rgb_image)
            
            # Resize image to fit the label if necessary? 
            # For now let's keep it native to webcam resolution or resized earlier.
            
            # Thread-Safety:
            # We must create ImageTk.PhotoImage on the main thread to avoid issues.
            # We store the PIL image and schedule an update.
            self.current_pil_image = image
            self.root.after(0, self.update_ui_from_thread)
            
            # Maintain simpler loop control
            time.sleep(0.01) # Small delay to yield CPU if needed within high FPS

        self.cap.release()
        # Clear video display
        self.lbl_video.config(image='')

    def check_line_crossing(self, results, frame):
        # Line definition
        A = np.array(self.tripwire_points[0])
        B = np.array(self.tripwire_points[1])
        
        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xywh.cpu() # x_center, y_center, width, height
            track_ids = results[0].boxes.id.int().cpu().tolist()
            
            for box, track_id in zip(boxes, track_ids):
                x, y, w, h = box
                centroid = np.array([float(x), float(y)])
                
                # Cross product to determine side
                # (Bx - Ax) * (Py - Ay) - (By - Ay) * (Px - Ax)
                cross_product = (B[0] - A[0]) * (centroid[1] - A[1]) - (B[1] - A[1]) * (centroid[0] - A[0])
                current_side = 1 if cross_product > 0 else -1
                
                if track_id in self.track_history:
                    previous_side = self.track_history[track_id]
                    if previous_side != current_side:
                        # Crossing detected!
                        self.trigger_alert(frame)
                        self.track_history[track_id] = current_side # Update side
                else:
                    self.track_history[track_id] = current_side

    def trigger_alert(self, frame):
        self.counter += 1
        timestamp = datetime.datetime.now().strftime("%H%M%S")
        
        # update counter on UI (thread-safe wrapper needed ideally)
        self.root.after(0, lambda: self.lbl_counter.config(text=f"Crossings: {self.counter}"))
        
        # Log
        self.root.after(0, lambda: self.log_message(f"ALERT! Crossing detected."))
        
        # Flash UI (change bg color briefly)
        self.root.after(0, lambda: self.flash_ui())
        
        # Save snapshot
        filename = f"alerts/alert_{timestamp}.jpg"
        cv2.imwrite(filename, frame)
        self.root.after(0, lambda: self.log_message(f"Snapshot saved: {filename}"))

    def flash_ui(self):
        original_bg = self.sidebar.cget("bg")
        self.sidebar.config(bg="red")
        self.lbl_counter.config(bg="red", fg="white")
        self.root.after(200, lambda: self.restore_ui(original_bg))

    def restore_ui(self, original_bg):
        self.sidebar.config(bg=original_bg)
        self.lbl_counter.config(bg=original_bg, fg="#e74c3c")

    def update_ui_from_thread(self):
        if hasattr(self, 'current_pil_image'):
            # Create ImageTk on main thread
            imgtk = ImageTk.PhotoImage(image=self.current_pil_image)
            self.lbl_video.config(image=imgtk)
            self.current_image_ref = imgtk # Keep reference 

if __name__ == "__main__":
    root = tk.Tk()
    app = TripwireApp(root)
    
    # Handle window close
    def on_closing():
        app.stop_camera()
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
