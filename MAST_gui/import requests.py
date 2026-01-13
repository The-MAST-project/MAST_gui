import requests
import json
import time

BASE_URL = "http://mast-wis-control:8000"

def send_notification(path, value):
    """Send a test notification"""
    notification = {
        "initiator": {
            "site": "wis",
            "machine_type": "unit",
            "machine_name": "mastw",
            "project": "mast"
        },
        "type": "status_update",
        "value": value,
        "cache": {"path": path}
    }
    
    resp = requests.post(
        f"{BASE_URL}/api/notifications",
        json=notification,
        timeout=5
    )
    print(f"Sent: {'.'.join(path)} = {value} → {resp.status_code}")
    return resp.ok

def check_cache():
    """Check cache contents"""
    resp = requests.get(f"{BASE_URL}/api/debug/cache")
    if resp.ok:
        data = resp.json()
        print(f"\nCache timestamp: {data.get('last_refresh')}")
        return data
    return None

# Run tests
print("=== Testing Notification System ===\n")

# Test 1: Focuser position
send_notification(["wis", "unit", "mastw", "focuser", "position"], 10000)
time.sleep(0.5)

# Test 2: Mount coordinates
send_notification(["wis", "unit", "mastw", "mount", "ra_j2000_hours"], 15.5)
time.sleep(0.5)

# Test 3: Activities
send_notification(["wis", "unit", "mastw", "focuser", "activities_verbal"], ["Moving"])
time.sleep(0.5)

# Check cache
print("\n=== Checking Cache ===")
cache = check_cache()
if cache:
    print(json.dumps(cache, indent=2))

print("\n=== Tests Complete ===")
