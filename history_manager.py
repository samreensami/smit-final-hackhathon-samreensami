import json
import os

HISTORY_FILE = "receipt_history.json"

def save_to_history(data):
    """Nayi receipt ka data purani history mein add karein."""
    history = load_history()
    history.append(data)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

def load_history():
    """Sari purani receipts load karein."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def clear_history():
    """History ko delete karne ke liye."""
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)