import os
from typing import List, Dict, Any, Tuple
from app.zones.zone_engine import SafetyZone

class SafetyRiskEngine:
    """
    Step 6: SiteGuard AI Safety Risk & Violation Engine.
    Integrates geographic safety zones and individual worker PPE compliance states
    to calculate safety risk scores and identify OSHA compliance violations.
    """
    def __init__(self):
        pass

    def evaluate_safety(self, track_id: int, zone: SafetyZone, ppe_status: Dict[str, bool]) -> Tuple[int, List[str], str]:
        """
        Evaluates safety compliance and returns a risk score, violations list, and risk severity level.
        
        Risk level ranges:
          - SAFE (0 - 20): All required PPE present in low-severity zone
          - LOW (21 - 45): Slight PPE deficiency or warning in safe area
          - MEDIUM (46 - 70): Standard work zone with missing basic PPE
          - HIGH (71 - 90): High-risk vehicle zones with missing PPE
          - CRITICAL (91 - 100): Critical danger zones with missing gear
          
        Args:
            track_id: int, worker tracking ID
            zone: SafetyZone, the zone the worker is standing in (None if outside)
            ppe_status: Dict[str, bool], maps 'helmet', 'safety_vest', 'safety_shoes' to their presence
            
        Returns:
            risk_score: int (0 to 100)
            violations: List[str] describing compliance issues
            severity: str ('SAFE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
        """
        has_helmet = ppe_status.get("helmet", False)
        has_vest = ppe_status.get("safety_vest", False)
        has_shoes = ppe_status.get("safety_shoes", False)
        
        violations = []
        zone_type = zone.zone_type if zone else "NONE"
        
        # 1. Base risk assessment based on spatial severity level
        if zone_type == "SAFE": # REST_ZONE
            base_risk = 10
            # Warning only, not strict violation
            if not has_helmet:
                violations.append("No Helmet in Rest Zone (Warning)")
            if not has_vest:
                violations.append("No Vest in Rest Zone (Warning)")
                
        elif zone_type == "CAUTION": # WORK_ZONE
            base_risk = 30
            # Helmet and Vest required
            if not has_helmet:
                violations.append("Missing Helmet in WORK_ZONE")
            if not has_vest:
                violations.append("Missing Safety Vest in WORK_ZONE")
                
        elif zone_type == "HIGH_RISK": # VEHICLE_ZONE
            base_risk = 60
            # Helmet, Vest, and Safety Shoes required
            if not has_helmet:
                violations.append("Missing Helmet in VEHICLE_ZONE")
            if not has_vest:
                violations.append("Missing Safety Vest in VEHICLE_ZONE")
            if not has_shoes:
                violations.append("Missing Safety Shoes in VEHICLE_ZONE")
                
        elif zone_type == "CRITICAL": # CRITICAL_ZONE
            base_risk = 80
            # All PPE strictly required
            if not has_helmet:
                violations.append("CRITICAL: No Helmet in Crane Area")
            if not has_vest:
                violations.append("CRITICAL: No Vest in Crane Area")
            if not has_shoes:
                violations.append("CRITICAL: No Safety Shoes in Crane Area")
                
        else: # Outside configured zones
            base_risk = 20
            # Helmet and Vest required by default on site
            if not has_helmet:
                violations.append("Missing Helmet")
            if not has_vest:
                violations.append("Missing Safety Vest")

        # 2. Compute risk penalty based on active violations
        penalty = len(violations) * 20
        # Extra penalty for CRITICAL violations in danger zones
        if any("CRITICAL" in v for v in violations):
            penalty += 25
            
        risk_score = min(100, base_risk + penalty)
        
        # Safety bonus if fully compliant
        if not violations:
            risk_score = max(0, base_risk - 10)
            
        # 3. Classify overall severity rank
        if risk_score <= 20:
            severity = "SAFE"
        elif risk_score <= 45:
            severity = "LOW"
        elif risk_score <= 70:
            severity = "MEDIUM"
        elif risk_score <= 90:
            severity = "HIGH"
        else:
            severity = "CRITICAL"
            
        return risk_score, violations, severity
