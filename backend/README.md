# SiteGuard AI Backend

This is the backend foundation for **SiteGuard AI**, a context-aware predictive safety intelligence system for construction sites.

## Installation

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (Python 3.11+ is required):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate  # On Windows
   ```

3. Install the dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Download the pretrained weights file:
   - Download **[yolo11n.pt](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt)** (approx 5.3 MB).
   - Place the file directly in the `backend/` directory.

---

## Running the FastAPI Server

Start the FastAPI application using Uvicorn:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Testing the Endpoints
- **Root**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/) → `{"status": "SiteGuard AI backend running"}`
- **Health**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) → `{"status": "healthy"}`
- **Interactive API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Testing Object Detection (Step 2)

Run YOLO object detection on a sample image to test the detection module:

1. **Place a sample image** (e.g. `construction site image.jpg`) inside the `data/videos/` directory.
2. **Run the test script** from the `backend/` directory:
   ```bash
   python scripts/test_detection.py
   ```

By default, the script looks for `../data/videos/construction site image.jpg` and saves the annotated copy to `../data/outputs/annotated.jpg`.

---

## Testing Multi-Object Tracking (Step 3)

Run ByteTrack multi-object tracking on the construction video:

1. **Ensure a video file exists** inside the `data/videos/` directory (e.g. `14495427_3840_2160_30fps.mp4`).
2. **Run the test script** from the `backend/` directory:
   ```bash
   python scripts/test_tracking.py
   ```

### Expected Outputs
- Progress logging output to the terminal showing processed frames and current count of unique/active workers.
- The annotated output video saved as `data/outputs/tracked_output.mp4` with persistent worker IDs (`Worker#01`, `Worker#02`, etc.) drawn above tracked people.

---

## Testing Safety Zone Engine (Step 4)

Run safety zones overlay and occupancy analysis on the construction video:

1. **Ensure a video file exists** inside the `data/videos/` directory (e.g. `14495427_3840_2160_30fps.mp4`).
2. **Run the test script** from the `backend/` directory:
   ```bash
   python scripts/test_zones.py
   ```

### Expected Outputs
- Polygons corresponding to configured Safety Zones drawn as semi-transparent color overlays directly on the video.
- Zone name and type displays rendered inside each zone.
- Worker labels extended to show both their Worker ID and current zone name (e.g. `Worker#01` and `Zone: Excavation Area`) drawn beneath their boxes.
- Output video saved as `data/outputs/zones_output.mp4` at original resolution.
- Occupancy stats summary (unique visitors, peak occupancy, average occupancy) output to the terminal upon completion.

---

## Testing PPE Detection (Step 5)

Run worker tracking combined with the separate PPE detection layer on the construction video:

1. **Download the PPE weights**: Download a pretrained construction safety YOLO model (such as `ppe_yolo11n.pt`) and place it in the `backend/` directory.
2. **Ensure a video file exists** inside the `data/videos/` directory (e.g. `14495427_3840_2160_30fps.mp4`).
3. **Run the test script** from the `backend/` directory:
   ```bash
   python scripts/test_ppe.py
   ```

### Expected Outputs
- Parallel rendering of worker tracking tags and thin labeled boxes identifying detected PPE gear (`helmet`, `safety_vest`, `safety_shoes`).
- Output video saved as `data/outputs/ppe_output.mp4` at original resolution and FPS, using QuickTime-compatible H.264 format.
- Cumulative PPE detections by class printed at execution completion.

---

## Testing Safety Risk & Violation Engine (Step 6)

Run the integrated pipeline combining Tracking, Safety Zones, PPE compliance, and Risk Evaluation:

1. **Ensure a video file exists** inside the `data/videos/` directory (e.g. `14495427_3840_2160_30fps.mp4`).
2. **Ensure pretrained model weights are present** (`yolo11n.pt` and `ppe_yolo11n.pt`) inside the `backend/` directory.
3. **Run the test script** from the `backend/` directory:
   ```bash
   python scripts/test_safety.py
   ```

### Expected Outputs
- Real-time overlay of configured safety zones.
- Compact worker banner containing the safety profile and risk score: `Worker#XX | Risk: YY% (SEVERITY) | H:✓ V:✓ S:✗` color-coded by risk level (green to red).
- A transparent HUD Safety Dashboard in the top-left corner displaying active workers, active PPE violations, peak risk score, and real-time critical alert logs.
- Output video saved as `data/outputs/safety_output.mp4` encoded in H.264 format compatible with QuickTime Player.
- Final summary of site statistics printed at execution completion.

---

## Testing Safety Event & Alert Engine (Step 7)

Run the safety events and alert engine analysis combining Tracking, Safety Zones, PPE, and Risk Scoring, while logging events to a JSON report:

1. **Ensure a video file exists** inside the `data/videos/` directory (e.g. `14495427_3840_2160_30fps.mp4`).
2. **Ensure pretrained model weights are present** (`yolo11n.pt` and `ppe_yolo11n.pt`) inside the `backend/` directory.
3. **Run the test script** from the `backend/` directory:
   ```bash
   python scripts/test_alerts.py
   ```

### Expected Outputs
- Real-time overlay of Safety Zones, HUD Safety Dashboard, and compact worker safety statuses.
- A machine-readable event log file generated at `data/outputs/safety_events.json` documenting every unique spatial hazard, PPE violation, and zone entry with frame timestamps.
- Video output with the overlay dashboard saved to `data/outputs/safety_output.mp4` (QuickTime-compatible H.264).
- A detailed events summary (alert types, severity breakdown, JSON output logs) output to the terminal upon completion.




