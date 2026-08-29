import os
from dotenv import load_dotenv

load_dotenv()

# Configurable path to the pretrained PPE model weights
# Defaults to ppe_yolo11n.pt in the backend root
PPE_MODEL_PATH = os.getenv("PPE_MODEL_PATH", "ppe_yolo11n.pt")

# Configurable confidence threshold for PPE detection
PPE_CONF_THRESHOLD = float(os.getenv("PPE_CONF_THRESHOLD", "0.25"))

# Dict mapping the model's raw class IDs to user-friendly PPE category labels.
# Matching our verified ppe_yolo11n.pt classes:
# 0: Gloves, 1: Vest, 2: goggles, 3: helmet, 4: mask, 5: safety_shoe
PPE_CLASSES_MAP = {
    0: "gloves",
    1: "safety_vest",
    2: "goggles",
    3: "helmet",
    4: "mask",
    5: "safety_shoes"
}
