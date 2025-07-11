import os
import json
from datetime import datetime
from geopy.distance import geodesic

CONTEXT_CACHE_DIR = "context_cache"
DEVICE_PROFILES_DIR = "device_profiles"

# Ensure folders exist
os.makedirs(CONTEXT_CACHE_DIR, exist_ok=True)
os.makedirs(DEVICE_PROFILES_DIR, exist_ok=True)


def load_cached_context(user_id):
    cache_path = os.path.join(CONTEXT_CACHE_DIR, f"{user_id}.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            return json.load(f)
    return None


def save_cached_context(user_id, context):
    cache_path = os.path.join(CONTEXT_CACHE_DIR, f"{user_id}.json")
    with open(cache_path, "w") as f:
        json.dump(context, f)


def load_device_profile(user_id):
    profile_path = os.path.join(DEVICE_PROFILES_DIR, f"{user_id}.json")
    if os.path.exists(profile_path):
        with open(profile_path, "r") as f:
            return json.load(f)
    return None

def is_different_subnet(ip1, ip2, level=2):
    try:
        return ip1.split(".")[:level] != ip2.split(".")[:level]
    except Exception:
        return True  # Treat malformed IPs as different


def compute_network_shift_score(last_net: dict, current_net: dict) -> float:
    
    score = 0.0

    # Weights for each signal
    weights = {
        "network_type_change": 0.5,   # High signal (e.g., WiFi → Mobile)
        "ip_subnet_change": 0.3,      # Medium signal
        "isp_change": 0.2             # Low-medium signal
    }

    # Check 1: Network type change (WiFi <-> Mobile)
    if last_net.get("network_type") != current_net.get("network_type"):
        score += weights["network_type_change"]

    # Check 2: Subnet change in IP
    if is_different_subnet(
        last_net.get("ip_address", ""), current_net.get("ip_address", ""), level=2
    ):
        score += weights["ip_subnet_change"]

    # Check 3: ISP change
    if (
        last_net.get("isp")
        and current_net.get("isp")
        and last_net["isp"] != current_net["isp"]
    ):
        score += weights["isp_change"]

    # Final score out of 100
    return round(score * 100, 2)


def analyze_context(user_id, context):
    geo_shift_score = 0.0
    network_shift_score = 0.0
    device_mismatch_score = 0.0

    current_loc = context.get("location", {})
    current_net = context.get("network_info", {})
    current_dev = context.get("device_info", {})

    # -------------------------------
    # Device profile mismatch score
    # -------------------------------
    base_profile = load_device_profile(user_id)
    if base_profile:
        mismatches = sum(
            1 for key in ["os", "os_version", "device_model"]
            if current_dev.get(key) != base_profile.get(key)
        )
        device_mismatch_score = (mismatches / 3) * 100

    # -------------------------------
    # Geolocation and Network shift
    # -------------------------------
    last_context = load_cached_context(user_id)

    if last_context:
        # Geolocation shift
        last_loc = last_context.get("location", {})
        if "latitude" in last_loc and "longitude" in last_loc:
            coords1 = (last_loc["latitude"], last_loc["longitude"])
            coords2 = (current_loc["latitude"], current_loc["longitude"])
            distance_km = geodesic(coords1, coords2).kilometers

            # Define scoring: beyond 1000km in short time = 100 score
            # Parse timestamps
            last_time_str = last_loc.get("timestamp")
            current_time_str = current_loc.get("timestamp")

            last_time = datetime.fromisoformat(last_time_str)
            current_time = datetime.fromisoformat(current_time_str)

            # Compute time difference in hours
            if current_time <= last_time:
                geo_shift_score = 0
            else:
                time_diff_hours = abs((current_time - last_time).total_seconds()) / 3600
                expected_max_distance = time_diff_hours * 80
                geo_shift_score = min((distance_km / expected_max_distance) * 100, 100)


        # Network shift
        last_net = last_context.get("network_info", {})

        network_shift_score = compute_network_shift_score(last_net, current_net)


    # Update the context cache
    save_cached_context(user_id, context)

    return {
        "geo_shift_score": round(geo_shift_score, 2),
        "network_shift_score": round(network_shift_score, 2),
        "device_mismatch_score": round(device_mismatch_score, 2)
    }


