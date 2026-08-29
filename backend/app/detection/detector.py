import cv2
import numpy as np
from ultralytics import YOLO
from app.config import settings

class YOLODetector:
    """
    Modular object detector wrapper around Ultralytics YOLO.
    Designed to detect safety-related objects (person, vehicles) in images or video frames.
    """
    def __init__(self, model_path: str = None):
        import os
        # Fallback to config setting if model_path is not specified
        self.model_path = model_path or settings.YOLO_MODEL
        
        # Check if the model weights exist locally to prevent internet download hang
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"\n[!] Error: Pretrained weights file '{self.model_path}' not found locally.\n"
                f"Due to sandbox network restrictions, automatic downloads will fail.\n"
                f"Please download '{self.model_path}' manually from:\n"
                f"  https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt\n"
                f"And place the downloaded file in the root of your 'backend' folder."
            )
            
        print("Loading YOLO model...")
        self.model = YOLO(self.model_path)
        print("Model loaded.")
        
        # Predefined COCO classes of interest (0-indexed)
        # Note: Pretrained COCO model does not natively support "excavator" or custom machinery;
        # however, it detects "truck", "bus", "car", "motorcycle", "person".
        self.target_classes = {
            0: "person",
            2: "car",
            3: "motorcycle",
            5: "bus",
            7: "truck"
        }
        
        # BGR colors for drawing detection overlays
        self.colors = {
            "person": (0, 255, 0),       # Green
            "car": (255, 0, 0),          # Blue
            "motorcycle": (0, 255, 255),  # Yellow
            "bus": (255, 0, 255),        # Magenta
            "truck": (0, 165, 255)       # Orange
        }
        self.default_color = (255, 255, 255)  # White

    def detect(self, frame: np.ndarray, confidence_threshold: float = 0.25):
        """
        Performs object detection on an input image/frame.
        
        Args:
            frame: np.ndarray (OpenCV BGR image frame)
            confidence_threshold: float, threshold to filter low-confidence detections
            
        Returns:
            detections: list of dicts. Format:
                [
                    {
                        "class_name": str,
                        "confidence": float,
                        "bbox": [xmin, ymin, xmax, ymax]
                    }, ...
                ]
            annotated_frame: np.ndarray, the frame with bounding boxes and labels drawn
        """
        # Run YOLO inference in silent mode
        results = self.model(frame, verbose=False)
        
        detections = []
        annotated_frame = frame.copy()
        
        if not results:
            return detections, annotated_frame
            
        result = results[0]
        boxes = result.boxes
        
        for box in boxes:
            class_id = int(box.cls[0].item())
            
            # Filter detections based on target class list
            if class_id in self.target_classes:
                confidence = float(box.conf[0].item())
                if confidence < confidence_threshold:
                    continue
                
                class_name = self.target_classes[class_id]
                
                # Get bounding box coordinates as [xmin, ymin, xmax, ymax]
                xyxy = box.xyxy[0].tolist()
                xmin, ymin, xmax, ymax = map(int, xyxy)
                
                detections.append({
                    "class_name": class_name,
                    "confidence": confidence,
                    "bbox": [xmin, ymin, xmax, ymax]
                })
                
                # Draw bounding box and label onto the annotated frame
                self._draw_detection(annotated_frame, class_name, confidence, xmin, ymin, xmax, ymax)
                
        return detections, annotated_frame

    def _draw_detection(self, frame: np.ndarray, class_name: str, confidence: float, xmin: int, ymin: int, xmax: int, ymax: int):
        """
        Helper method to draw bounding boxes and confidence labels.
        """
        color = self.colors.get(class_name, self.default_color)
        
        # Draw bounding box rectangle
        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 2)
        
        # Prepare text label
        label = f"{class_name} {confidence:.2f}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        
        # Get dimensions of label background
        (w, h), _ = cv2.getTextSize(label, font, font_scale, thickness)
        
        # Keep label text within frame boundaries
        text_ymin = max(ymin, h + 5)
        
        # Draw label background rectangle
        cv2.rectangle(frame, (xmin, text_ymin - h - 5), (xmin + w, text_ymin), color, -1)
        
        # Choose text color (black for light background, white otherwise)
        text_color = (0, 0, 0)
        
        # Draw text label
        cv2.putText(
            frame,
            label,
            (xmin, text_ymin - 3),
            font,
            font_scale,
            text_color,
            thickness,
            cv2.LINE_AA
        )
