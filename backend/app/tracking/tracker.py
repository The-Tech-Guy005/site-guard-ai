import cv2
import numpy as np
from app.detection.detector import YOLODetector

class ByteTracker:
    """
    Multi-object tracker wrapping ByteTrack via Ultralytics YOLO.
    Tracks target classes (person, car, truck, motorcycle, bus) across frames
    and maps them to persistent worker and vehicle IDs.
    """
    def __init__(self, detector: YOLODetector = None):
        # Initialize or reuse the existing detector
        self.detector = detector or YOLODetector()
        
        # Track historical set of unique track IDs
        self.unique_worker_ids = set()
        self.unique_all_ids = set()

    def track(self, frame: np.ndarray, confidence_threshold: float = 0.25, persist: bool = True, imgsz: int = 1280, classes: list = None):
        """
        Processes a single frame for tracking.
        
        Args:
            frame: np.ndarray (OpenCV BGR image frame)
            confidence_threshold: float, threshold to filter detections
            persist: bool, whether to persist tracking status across frames
            imgsz: int, inference size for YOLO model
            classes: list, class indices to filter detections (e.g. [0] for person)
            
        Returns:
            tracks: list of dicts. Format:
                [
                    {
                        "class_name": str,
                        "confidence": float,
                        "bbox": [xmin, ymin, xmax, ymax],
                        "track_id": int
                    }, ...
                ]
            annotated_frame: np.ndarray, the frame annotated with boxes and IDs
        """
        # Run tracking using ByteTrack
        results = self.detector.model.track(
            source=frame,
            persist=persist,
            tracker="bytetrack.yaml",
            conf=confidence_threshold,
            imgsz=imgsz,
            classes=classes,
            verbose=False
        )
        
        tracks = []
        annotated_frame = frame.copy()
        
        if not results or results[0].boxes is None:
            return tracks, annotated_frame
            
        result = results[0]
        boxes = result.boxes
        
        # If no tracking IDs are active in this frame, return empty tracks
        if boxes.id is None:
            return tracks, annotated_frame
            
        for box in boxes:
            class_id = int(box.cls[0].item())
            
            # Keep only the target classes configured in YOLODetector
            if class_id in self.detector.target_classes:
                confidence = float(box.conf[0].item())
                class_name = self.detector.target_classes[class_id]
                
                # Retrieve the track ID
                track_id = int(box.id[0].item())
                self.unique_all_ids.add(track_id)
                if class_name == "person":
                    self.unique_worker_ids.add(track_id)
                
                # Bounding box coordinates
                xyxy = box.xyxy[0].tolist()
                xmin, ymin, xmax, ymax = map(int, xyxy)
                
                tracks.append({
                    "class_name": class_name,
                    "confidence": confidence,
                    "bbox": [xmin, ymin, xmax, ymax],
                    "track_id": track_id
                })
                
                # Draw annotated overlay
                self._draw_track(annotated_frame, class_name, track_id, xmin, ymin, xmax, ymax)
                
        return tracks, annotated_frame

    def _draw_track(self, frame: np.ndarray, class_name: str, track_id: int, xmin: int, ymin: int, xmax: int, ymax: int):
        """
        Draws bounding box and custom worker/vehicle IDs on the frame.
        """
        color = self.detector.colors.get(class_name, self.detector.default_color)
        
        # Draw bounding box
        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 2)
        
        # Label formatting: "Worker#01" for people, "Car#01" for cars, etc.
        if class_name == "person":
            label = f"Worker#{track_id:02d}"
        else:
            label = f"{class_name.capitalize()}#{track_id:02d}"
            
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        
        # Calculate label sizing
        (w, h), _ = cv2.getTextSize(label, font, font_scale, thickness)
        
        # Keep the label inside the frame boundary
        text_ymin = max(ymin, h + 5)
        
        # Draw background banner
        cv2.rectangle(frame, (xmin, text_ymin - h - 5), (xmin + w + 4, text_ymin + 2), color, -1)
        
        # Draw ID text on banner
        cv2.putText(
            frame,
            label,
            (xmin + 2, text_ymin - 2),
            font,
            font_scale,
            (0, 0, 0),
            thickness,
            cv2.LINE_AA
        )

    def get_unique_workers_count(self) -> int:
        """
        Returns the number of unique worker IDs tracked so far.
        """
        return len(self.unique_worker_ids)

    def get_unique_all_count(self) -> int:
        """
        Returns the number of all unique entities tracked so far.
        """
        return len(self.unique_all_ids)
