import json

def flatten_snapshot(data: dict) -> dict:
    
    return {
        # tap data
        "tap_duration": data.get("tap_data", {}).get("tap_duration"),

        # typing data
        "inter_key_delay_avg": data.get("typing_data", {}).get("inter_key_delay_avg"),
        "key_press_duration_avg": data.get("typing_data", {}).get("key_press_duration_avg"),
        "typing_error_rate": data.get("typing_data", {}).get("typing_error_rate"),

        # swipe and scroll
        "swipe_speed": data.get("swipe_data", {}).get("swipe_speed"),
        "swipe_angle": data.get("swipe_data", {}).get("swipe_angle"),
        "scroll_distance": data.get("scroll_data", {}).get("scroll_distance"),
        "scroll_velocity": data.get("scroll_data", {}).get("scroll_velocity"),

        # sensors
        "gyro_variance": data.get("sensor_data", {}).get("gyro_variance"),
        "accelerometer_noise": data.get("sensor_data", {}).get("accelerometer_noise"),

        # session meta
        "session_duration_sec": data.get("session_metadata", {}).get("session_duration_sec"),
        "session_start_hour": data.get("session_metadata", {}).get("session_start_hour"),
        "screen_transition_count": data.get("session_metadata", {}).get("screen_transition_count"),
        "avg_dwell_time_per_screen": data.get("session_metadata", {}).get("avg_dwell_time_per_screen")
    }