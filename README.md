# Virtual Tripwire Security System

A high-performance desktop application for real-time security monitoring using a webcam, **CustomTkinter**, and **YOLOv8** from Ultralytics.

![Tripwire AI](https://repository-images.githubusercontent.com/placeholder)
_(Add a screenshot here if you have one)_

## Features

- **Modern UI**: Sleek, professional interface built with `CustomTkinter`.
- **Real-time Person Detection**: Uses YOLOv8n to detect people with high accuracy.
- **Virtual Tripwire**: Draw a line on the video feed; alarms trigger when a person crosses it.
- **Live Alerts**: Visual flashing UI and crossing counter.
- **Snapshots**: Automatically saves an image of the event to the `alerts/` folder.
- **Event Log**: Logs timestamped events in the sidebar.
- **Threaded Architecture**: Ensures the GUI remains responsive while processing video frames.

## Installation

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/DahamDissanayake/Tripwire-YOLO.git
    cd Tripwire-YOLO
    ```

2.  **Create and Activate Virtual Environment** (Recommended):
    - **Windows**:
      ```bash
      python -m venv venv
      venv\Scripts\activate
      ```
    - **Mac/Linux**:
      ```bash
      python3 -m venv venv
      source venv/bin/activate
      ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the application**:

    ```bash
    python main.py
    ```

2.  **Start Monitoring**:
    - Click **Start Camera** to enable the webcam feed.
    - Click **Set Tripwire**, then click **two points** on the video feed to draw the virtual line.
    - The system will now track people (`Class 0`) and trigger an alert if they cross the line.
    - View the **Live Counter** and **Event Log** for updates.

3.  **Reset**:
    - Click **Reset Counter** to clear the count.
    - Click **Stop Camera** to pause the feed.

## Folder Structure

- `main.py`: The main application script.
- `requirements.txt`: Python package dependencies.
- `alerts/`: Generated directory where alert snapshots are saved.

## Requirements

- Python 3.8+
- Webcam (Default ID 0)
- **Libraries**:
  - `opencv-python`
  - `ultralytics`
  - `customtkinter`
  - `pillow`
  - `lapx` (for tracking on Windows)

## Credits

**Developed by DAMA**

[https://github.com/DahamDissanayake/Tripwire-YOLO](https://github.com/DahamDissanayake/Tripwire-YOLO)
