import pandas as pd
import os
import json

from datetime import datetime
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, APIRouter
from typing import List

from app.model_manager import ModelManager
from app.analyze_context import analyze_context

app = FastAPI()
model_manager = ModelManager()

DEVICE_PROFILE_DIR = "device_profiles"
os.makedirs(DEVICE_PROFILE_DIR, exist_ok=True)

class DeviceInfo(BaseModel):
    os: str
    os_version: str
    device_model: str

def flatten_snapshot(data: dict) -> dict:
    print("\n📥 Raw snapshot received:")
    print(json.dumps(data, indent=2))
    
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


@app.get("/")
def root():
    return {"message": "Behavior Auth API is running"}

@app.post("/store-device-profile/{user_id}")
def store_device_profile(user_id: str, device_info: DeviceInfo):
    profile_path = os.path.join(DEVICE_PROFILE_DIR, f"{user_id}.json")
    
    try:
        with open(profile_path, "w") as f:
            json.dump(device_info.dict(), f, indent=4)
        return {"message": f"Device profile stored for user {user_id}."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving profile: {str(e)}")


@app.get("/device-profile/{user_id}")
def get_device_profile(user_id: str):
    profile_path = os.path.join("device_profiles", f"{user_id}.json")
    
    if os.path.exists(profile_path):
        with open(profile_path, "r") as f:
            profile = json.load(f)
        return {
            "user_id": user_id,
            "device_profile": profile
        }
    else:
        return {
            "user_id": user_id,
            "message": "⚠️ Device profile not found. User may not be authenticated yet."
        }

@app.post("/predict")
def predict(data: dict):
    user_id = data["user_id"]
    
    context = data.get("context", {})
    context_score = analyze_context(user_id, context)
    
    snapshot = flatten_snapshot(data)
    risk = model_manager.predict_risk(user_id, snapshot)
    
    os.makedirs("risks", exist_ok=True)
    risk_log_path = os.path.join("risks", f"{user_id}.json")
    log_entry = {"timestamp": datetime.now().isoformat(), "risk": risk, **context_score}
    if os.path.exists(risk_log_path):
        with open(risk_log_path, "r") as f:
            log = json.load(f)
    else:
        log=[]
    log.append(log_entry)
    with open(risk_log_path, "w") as f:
        json.dump(log[-20:], f, indent=2)
    
    return {"user_id": user_id, "risk_score": risk, **context_score}

@app.post("/end-session")
def end_session(data: dict):
    user_id = data["user_id"]
    snapshots: List[dict] = data["snapshots"]
    
    #Flatten all snapshots
    flattened_snapshots = []
    context_scores_list = []

    for snapshot in snapshots:
        # Flatten core features
        flat = flatten_snapshot(snapshot)
        flattened_snapshots.append(flat)

        # Analyze context
        context_data = snapshot.get("context", {})
        context_scores = analyze_context(user_id, context_data)
        context_scores_list.append(context_scores)
        
    session_df = pd.DataFrame(flattened_snapshots)
    
    # Calculate risk on averaged snapshot
    averaged_snapshot = session_df.mean().to_dict()
    risk = model_manager.predict_risk(user_id, averaged_snapshot)

    # Determine where to save based on risk
    if risk >= 55:
        quarantine_dir = os.path.join("quarantine", user_id)
        os.makedirs(quarantine_dir, exist_ok=True)
        existing_quarantine = [
            f for f in os.listdir(quarantine_dir)
            if f.startswith("session_") and f.endswith(".csv")
        ]
        next_quarantine_number = len(existing_quarantine) + 1
        quarantine_path = os.path.join(quarantine_dir, f"session_{next_quarantine_number}.csv")
        session_df.to_csv(quarantine_path, index=False)

        return {"message": f"⚠️ High-risk session quarantined. Risk = {risk:.2f}", "context_scores": context_scores_list}
    
    user_dir = os.path.join("data", user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    existing = [f for f in os.listdir(user_dir) if f.startswith("session_") and f.endswith(".csv")]
    next_session_number = len(existing) + 1
    session_path = os.path.join(user_dir, f"session_{next_session_number}.csv")
    session_df.to_csv(session_path, index=False)
    
    if next_session_number >= 5:
        print(f"\n📚 Retraining on {min(len(existing) + 1, 15)} most recent sessions")
        model_manager._train_model(user_id)
    else:
        print(f"\nNot enough sessions to retrain (have {len(existing) + 1})")

    return {
        "message": f"✅ Session {next_session_number} stored for {user_id}",
        "risk_score": risk,
        "context_scores": context_scores_list
    }

@app.get("/model-meta/{user_id}")
def get_model_metadata(user_id: str):
    meta_path = os.path.join("models", f"{user_id}_meta.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            metadata = json.load(f)
        return metadata
    else:
        return {"message": "Metadata not available. Model may not be trained yet"}
    

@app.get("/all-users-meta")
def get_all_users_metadata():
    user_metas = []
    model_dir = "models"
    risk_dir = "risks"
    
    for filename in os.listdir(model_dir):
        if filename.endswith("_meta.json"):
            user_id = filename.replace("_meta.json", "")
            meta_path = os.path.join(model_dir, filename)
            model_path = os.path.join(model_dir, f"{user_id}_model.pkl")
            risk_path = os.path.join(risk_dir, f"{user_id}.json")
            
            with open(meta_path, "r") as f:
                metadata = json.load(f)
                
            trained = os.path.exists(model_path)
            latest_risk = None
            if os.path.exists(risk_path):
                with open(risk_path, "r") as rf:
                    risk_log = json.load(rf)
                    if risk_log:
                        latest_risk = risk_log[-1]["risk"]
            user_metas.append({
                "user_id": user_id,
                "trained": trained,
                "latest_risk": latest_risk,
                **metadata,
            })
    return user_metas

@app.get("/session-data/{user_id}")
def get_session_data(user_id: str):
    
    user_dir = os.path.join("data", user_id)
    session_data = []
    
    if not os.path.exists(user_dir):
        return {"message": "User has no session data yet."}
    
    # load upto 10 sessions
    session_files = sorted([
        f for f in os.listdir(user_dir) if f.startswith("session_") and f.endswith(".csv")
    ])[-10:]
    
    
    # load full risk logs
    risk_path = os.path.join("risks", f"{user_id}.json")
    risk_log = []
    if os.path.exists(risk_path):
        with open(risk_path, "r") as rf:
            risk_log = json.load(rf)
            
    all_snapshots = []
    for filename in session_files:
        path = os.path.join(user_dir, filename)
        df = pd.read_csv(path)
        snapshots = df.to_dict(orient="records")
        all_snapshots.append((filename, snapshots))

    # Reverse to keep most recent 10 entries (if >10 snapshots)
    risk_log = risk_log[-sum(len(s) for _, s in all_snapshots):]

    flat_index = 0
    session_data = []

    for filename, snapshots in all_snapshots:
        for i in range(len(snapshots)):
            if flat_index < len(risk_log):
                context_entry = risk_log[flat_index]
                snapshots[i]["risk"] = context_entry.get("risk", None)
                snapshots[i]["geo_shift_score"] = context_entry.get("geo_shift_score", None)
                snapshots[i]["network_shift_score"] = context_entry.get("network_shift_score", None)
                snapshots[i]["device_mismatch_score"] = context_entry.get("device_mismatch_score", None)
                flat_index += 1

        session_data.append({
            "filename": filename,
            "snapshots": snapshots
        })

    return {
        "user_id": user_id,
        "risk_log": risk_log[-10:],  # most recent 10 risk+context entries
        "sessions": session_data
    }

@app.delete("/reset-user-data/{user_id}")
def reset_user_data(user_id: str):
    deleted = []
    user_session_dir = os.path.join("data", user_id)
    if os.path.exists(user_session_dir):
        for file in os.listdir(user_session_dir):
            file_path = os.path.join(user_session_dir, file)
            os.remove(file_path)
            deleted.append(file_path)
        os.rmdir(user_session_dir)
        
    quarantine_dir = os.path.join("quarantine", user_id)
    if os.path.exists(quarantine_dir):
        for file in os.listdir(quarantine_dir):
            file_path = os.path.join(quarantine_dir, file)
            os.remove(file_path)
            deleted.append(file_path)
        os.rmdir(quarantine_dir)

    # Delete models and risk
    for folder, suffix in [("models", "_model.pkl"), ("models", "_meta.json"), ("risks", ".json")]:
        path = os.path.join(folder, f"{user_id}{suffix}")
        if os.path.exists(path):
            os.remove(path)
            deleted.append(path)
            
    # Delete device profile
    device_profile_path = os.path.join("device_profiles", f"{user_id}.json")
    if os.path.exists(device_profile_path):
        os.remove(device_profile_path)

    # Delete context cache
    context_cache_path = os.path.join("context_cache", f"{user_id}.json")
    if os.path.exists(context_cache_path):
        os.remove(context_cache_path)


    return {"message": f"Reset completed for {user_id}", "deleted_files": deleted}
