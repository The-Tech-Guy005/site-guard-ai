import os
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
from ultralytics import YOLO
from app.ppe.config import PPE_MODEL_PATH, PPE_CONF_THRESHOLD, PPE_CLASSES_MAP

class PPEDetector:
    """
    Architecturally separate Personal Protective Equipment (PPE) detector layer.
    Loads the YOLO PPE model and supports crop-based detection.
    """
    def __init__(self, model_path: str = None, confidence_threshold: float = None):
        self.model_path = model_path or PPE_MODEL_PATH
        self.confidence_threshold = confidence_threshold or PPE_CONF_THRESHOLD
        
        # Verify weight file exists locally to prevent sandboxed environment downloads from hanging
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"\n[!] Error: Pretrained PPE weights file '{self.model_path}' not found locally.\n"
                f"Due to sandbox network restrictions, automatic downloads will fail.\n"
                f"Please download the weights file manually and place it in the backend directory:\n"
                f"  {os.path.abspath(self.model_path)}\n"
            )
            
        print("Loading PPE model...")
        self.model = YOLO(self.model_path)
        print("PPE Model loaded.")
        
        # BGR colors for drawing distinct PPE bounding boxes
        self.colors = {
            "helmet": (0, 255, 255),       # Cyan/Yellow
            "safety_vest": (0, 165, 255),  # Orange
            "safety_shoes": (255, 0, 255), # Purple
            "gloves": (0, 255, 0)          # Green
        }
        self.default_color = (255, 255, 255) # White

    def detect_crop(self, crop: np.ndarray) -> List[Dict[str, Any]]:
        """
        Runs PPE object detection on a cropped image (e.g. worker bounding box).
        
        Args:
            crop: np.ndarray, the cropped worker image
            
        Returns:
            detections: List of dicts. Format:
                [
                    {
                        "class_name": str,
                        "confidence": float,
                        "bbox": [xmin, ymin, xmax, ymax] (local coordinates)
                    }, ...
                ]
        """
        if crop.size == 0:
            return []
            
        results = self.model(crop, conf=self.confidence_threshold, verbose=False)
        detections = []
        
        if not results or results[0].boxes is None:
            return detections
            
        result = results[0]
        boxes = result.boxes
        
        for box in boxes:
            class_id = int(box.cls[0].item())
            
            # Map detected class IDs based on configuration mapping
            if class_id in PPE_CLASSES_MAP:
                confidence = float(box.conf[0].item())
                class_name = PPE_CLASSES_MAP[class_id]
                
                # Bounding box coordinates
                xyxy = box.xyxy[0].tolist()
                xmin, ymin, xmax, ymax = map(int, xyxy)
                
                detections.append({
                    "class_name": class_name,
                    "confidence": confidence,
                    "bbox": [xmin, ymin, xmax, ymax]
                })
                
        return detections

    def draw_ppe_box(self, frame: np.ndarray, class_name: str, confidence: float, local_bbox: List[int], offset: Tuple[int, int]):
        """
        Maps local crop coordinates back to global frame coordinates and draws the thin border box.
        
        Args:
            frame: np.ndarray, the global frame to draw on
            class_name: str, name of the PPE class
            confidence: float, confidence score of detection
            local_bbox: List[int], [xmin, ymin, xmax, ymax] relative to crop
            offset: Tuple[int, int], (xmin_crop_offset, ymin_crop_offset) relative to global frame
        """
        ox, oy = offset
        lx_min, ly_min, lx_max, ly_max = local_bbox
        
        g_xmin = lx_min + ox
        g_ymin = ly_min + oy
        g_xmax = lx_max + ox
        g_ymax = ly_max + oy
        
        # Clip coordinates within the frame boundary
        h, w = frame.shape[:2]
        g_xmin = max(0, min(g_xmin, w - 1))
        g_ymin = max(0, min(g_ymin, h - 1))
        g_xmax = max(0, min(g_xmax, w - 1))
        g_ymax = max(0, min(g_ymax, h - 1))
        
        color = self.colors.get(class_name, self.default_color)
        
        # Draw small bounding box (thickness=1)
        cv2.rectangle(frame, (g_xmin, g_ymin), (g_xmax, g_ymax), color, 1)
        
        # Draw text label
        label = f"{class_name} {confidence:.2f}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.35
        thickness = 1
        (lw, lh), _ = cv2.getTextSize(label, font, font_scale, thickness)
        
        text_ymin = max(g_ymin, lh + 3)
        cv2.rectangle(frame, (g_xmin, text_ymin - lh - 3), (g_xmin + lw + 4, text_ymin + 1), color, -1)
        cv2.putText(
            frame,
            label,
            (g_xmin + 2, text_ymin - 2),
            font,
            font_scale,
            (0, 0, 0),
            thickness,
            cv2.LINE_AA
        )
