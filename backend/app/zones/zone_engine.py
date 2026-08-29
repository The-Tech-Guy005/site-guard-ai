import cv2
import numpy as np
from typing import List, Dict, Any, Tuple

class SafetyZone:
    """
    Represents a single configurable safety zone polygon.
    """
    def __init__(self, zone_id: str, name: str, zone_type: str, coordinates: list, severity: str = "LOW"):
        self.zone_id = zone_id
        self.name = name
        self.zone_type = zone_type
        # Coordinates reshaped to shape (N, 1, 2) which is strictly expected by OpenCV polylines/fillPoly
        self.coordinates = np.array(coordinates, dtype=np.int32).reshape((-1, 1, 2))
        self.severity = severity
        self.color = self._get_color()

    def _get_color(self) -> Tuple[int, int, int]:
        """
        Returns the BGR color mapping based on zone type or severity.
        """
        colors = {
            "SAFE": (0, 255, 0),                       # Green
            "REST": (255, 255, 0),                     # Cyan/Yellow-Green
            "CAUTION": (0, 255, 255),                  # Yellow
            "WORK_ZONE": (0, 165, 255),                 # Orange
            "VEHICLE_ZONE": (0, 0, 255),                # Red
            "CRANE_ZONE": (0, 0, 180),                  # Crimson
            "EXCAVATION_ZONE": (0, 50, 255),            # Orange-Red
            "FALL_RISK_ZONE": (0, 0, 220),              # Deep Red
            "HIGH_RISK": (0, 0, 255),                   # Red
            "CRITICAL": (0, 0, 255),                    # Red
            "PUBLIC_SAFETY_PERIMETER": (255, 0, 255)    # Purple/Magenta
        }
        return colors.get(self.zone_type, (255, 255, 255)) # White fallback

    def contains_point(self, point: Tuple[float, float]) -> bool:
        """
        Checks if a point is inside the zone polygon boundary.
        """
        # cv2.pointPolygonTest expects a float point. Returns >= 0 if inside or on edge.
        dist = cv2.pointPolygonTest(self.coordinates, (float(point[0]), float(point[1])), False)
        return dist >= 0


class SafetyZoneEngine:
    """
    Manages multiple SafetyZone polygons, coordinates checks, and overlays.
    """
    def __init__(self, zones_config: List[Dict[str, Any]] = None):
        self.zones: List[SafetyZone] = []
        if zones_config:
            self.load_zones(zones_config)

    def load_zones(self, zones_config: List[Dict[str, Any]]):
        """
        Initializes zones from a configuration list.
        """
        self.zones = []
        for cfg in zones_config:
            zone = SafetyZone(
                zone_id=cfg["zone_id"],
                name=cfg["name"],
                zone_type=cfg["zone_type"],
                coordinates=cfg["coordinates"],
                severity=cfg.get("severity", "LOW")
            )
            self.zones.append(zone)

    def get_zone_for_point(self, point: Tuple[float, float]) -> SafetyZone:
        """
        Finds the zone containing the given point. If a point falls into multiple zones,
        resolves it based on severity order (CRITICAL > HIGH_RISK > CAUTION > LOW).
        """
        severity_order = {
            "CRITICAL": 5,
            "HIGH_RISK": 4,
            "CAUTION": 3,
            "LOW": 1
        }
        
        matched_zones = []
        for zone in self.zones:
            if zone.contains_point(point):
                matched_zones.append(zone)
                
        if not matched_zones:
            return None
            
        # Prioritize matching zone with highest severity
        matched_zones.sort(key=lambda z: severity_order.get(z.severity, 0), reverse=True)
        return matched_zones[0]

    def draw_zones(self, frame: np.ndarray) -> np.ndarray:
        """
        Draws all zone boundaries as semi-transparent polygons with labels positioned near boundaries.
        """
        overlay = frame.copy()
        
        # 1. Draw filled transparent polygons first on the overlay
        for zone in self.zones:
            cv2.fillPoly(overlay, [zone.coordinates], zone.color)
            
        # 2. Blend the filled polygon overlay with the frame using a subtle 15% opacity (alpha=0.15)
        # This keeps the original video clearly visible without heavy tinting
        alpha = 0.15
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        
        # 3. Draw outline borders and labels on top of the blended frame
        for zone in self.zones:
            # Draw thin clearly visible outline (thickness=2)
            cv2.polylines(frame, [zone.coordinates], isClosed=True, color=zone.color, thickness=2)
            
            # Position the zone label near the top-left boundary of the polygon
            # We sort coordinate points by Y, then X to find a good top-left boundary point
            coords_flat = zone.coordinates.reshape(-1, 2)
            top_left_pt = coords_flat[np.argmin(coords_flat[:, 1])]  # point with minimum Y coord
            
            cx = int(top_left_pt[0]) + 10
            cy = int(top_left_pt[1]) + 20
            
            label = f"{zone.name} ({zone.zone_type})"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.45  # Small unobtrusive text size
            thickness = 1
            
            (w, h), _ = cv2.getTextSize(label, font, font_scale, thickness)
            
            # Draw solid black backing banner for text
            cv2.rectangle(frame, (cx - 4, cy - h - 4), (cx + w + 4, cy + 4), (0, 0, 0), -1)
            # Draw zone label text
            cv2.putText(frame, label, (cx, cy), font, font_scale, zone.color, thickness, cv2.LINE_AA)
            
        return frame
