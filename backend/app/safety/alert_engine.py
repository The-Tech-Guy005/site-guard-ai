import os
import json
from typing import List, Dict, Any, Tuple

class SafetyAlertEngine:
    """
    Step 7: Safety Event & Alert Engine.
    Processes spatial risk assessments and worker PPE states to flag incidents.
    Supports debouncing (cooldown) to prevent consecutive frame duplicate alerts.
    """
    def __init__(self, fps: float = 29.97, cooldown_seconds: float = 5.0):
        self.fps = fps
        self.cooldown_frames = int(cooldown_seconds * fps)
        self.events: List[Dict[str, Any]] = []
        self.event_counter = 0
        
        # Debounce registry: maps alert key -> frame index when last triggered
        self.last_triggered: Dict[str, int] = {}
        
        # Zone tracking registry: maps worker_id -> previous zone name (for entry edge detection)
        self.worker_prev_zones: Dict[int, str] = {}

    def check_worker_alerts(
        self, 
        frame_idx: int, 
        worker_id: int, 
        zone_name: str, 
        zone_type: str, 
        ppe_status: Dict[str, bool], 
        risk_score: int, 
        severity: str
    ) -> List[Dict[str, Any]]:
        """
        Evaluates safety alerts for an individual worker.
        """
        new_alerts = []
        
        # 1. Edge-triggered transition checks (UNSAFE_ZONE_ENTRY)
        prev_zone = self.worker_prev_zones.get(worker_id, None)
        if prev_zone is not None and prev_zone != zone_name:
            if zone_type in ["CAUTION", "HIGH_RISK", "CRITICAL"]:
                event_type = "UNSAFE_ZONE_ENTRY"
                desc = f"Worker#{worker_id:02d} entered {zone_name} ({zone_type})"
                alert_sev = "MEDIUM" if zone_type == "CAUTION" else ("HIGH" if zone_type == "HIGH_RISK" else "CRITICAL")
                
                alert = self._create_alert(
                    frame_idx=frame_idx,
                    worker_id=worker_id,
                    event_type=event_type,
                    severity=alert_sev,
                    zone=zone_name,
                    description=desc
                )
                new_alerts.append(alert)
                
        # Save current zone state for next frame evaluation
        self.worker_prev_zones[worker_id] = zone_name
        
        # 2. PPE compliance checks (PPE_VIOLATION)
        missing_items = []
        # CAUTION/WORK_ZONE requires helmet and safety vest
        if zone_type in ["CAUTION", "HIGH_RISK", "CRITICAL", "NONE"]:
            if not ppe_status.get("helmet", False):
                missing_items.append("helmet")
            if not ppe_status.get("safety_vest", False):
                missing_items.append("safety_vest")
            # HIGH_RISK/CRITICAL zones require safety shoes
            if zone_type in ["HIGH_RISK", "CRITICAL"] and not ppe_status.get("safety_shoes", False):
                missing_items.append("safety_shoes")
                
        for item in missing_items:
            # Debounce per worker per missing item
            debounce_key = f"ppe_{worker_id}_{item}"
            if self._is_cooldown_active(debounce_key, frame_idx):
                continue
                
            event_type = "PPE_VIOLATION"
            desc = f"Worker#{worker_id:02d} missing {item} in {zone_name}"
            
            alert = self._create_alert(
                frame_idx=frame_idx,
                worker_id=worker_id,
                event_type=event_type,
                severity=severity,
                zone=zone_name,
                description=desc
            )
            new_alerts.append(alert)
            self._update_cooldown(debounce_key, frame_idx)
            
        # 3. High-risk location presence (HIGH_RISK_ZONE_PRESENCE)
        if zone_type in ["HIGH_RISK", "CRITICAL"]:
            debounce_key = f"presence_{worker_id}_{zone_name}"
            if not self._is_cooldown_active(debounce_key, frame_idx):
                event_type = "HIGH_RISK_ZONE_PRESENCE"
                desc = f"Worker#{worker_id:02d} detected inside dangerous area: {zone_name}"
                alert_sev = "HIGH" if zone_type == "HIGH_RISK" else "CRITICAL"
                
                alert = self._create_alert(
                    frame_idx=frame_idx,
                    worker_id=worker_id,
                    event_type=event_type,
                    severity=alert_sev,
                    zone=zone_name,
                    description=desc
                )
                new_alerts.append(alert)
                self._update_cooldown(debounce_key, frame_idx)
                
        return new_alerts

    def check_zone_crowd_alerts(self, frame_idx: int, zone_occupancy: Dict[str, List[int]], crowd_threshold: int = 3) -> List[Dict[str, Any]]:
        """
        Evaluates crowd density limits for safety zones.
        """
        new_alerts = []
        for zone_name, worker_ids in zone_occupancy.items():
            count = len(worker_ids)
            if count >= crowd_threshold:
                debounce_key = f"crowd_{zone_name}"
                if self._is_cooldown_active(debounce_key, frame_idx):
                    continue
                    
                event_type = "CROWD_ACCUMULATION"
                desc = f"Crowd density warning: {count} workers clustered in {zone_name}"
                
                # Determine severity based on zone name keywords
                alert_sev = "HIGH"
                if "CRITICAL" in zone_name:
                    alert_sev = "CRITICAL"
                elif "REST" in zone_name:
                    alert_sev = "LOW"
                    
                alert = self._create_alert(
                    frame_idx=frame_idx,
                    worker_id=None,
                    event_type=event_type,
                    severity=alert_sev,
                    zone=zone_name,
                    description=desc
                )
                new_alerts.append(alert)
                self._update_cooldown(debounce_key, frame_idx)
                
        return new_alerts

    def _create_alert(self, frame_idx: int, worker_id: Any, event_type: str, severity: str, zone: str, description: str) -> Dict[str, Any]:
        self.event_counter += 1
        timestamp_sec = round(frame_idx / self.fps, 2)
        
        alert = {
            "event_id": f"evt_{self.event_counter:03d}",
            "frame_number": frame_idx,
            "timestamp_seconds": timestamp_sec,
            "worker_id": f"Worker#{worker_id:02d}" if worker_id is not None else None,
            "event_type": event_type,
            "severity": severity,
            "zone": zone,
            "description": description
        }
        self.events.append(alert)
        return alert

    def _is_cooldown_active(self, key: str, frame_idx: int) -> bool:
        if key in self.last_triggered:
            last_frame = self.last_triggered[key]
            if frame_idx - last_frame < self.cooldown_frames:
                return True
        return False

    def _update_cooldown(self, key: str, frame_idx: int):
        self.last_triggered[key] = frame_idx

    def save_report(self, filepath: str):
        """
        Saves all recorded safety events into a JSON file.
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(self.events, f, indent=2)
