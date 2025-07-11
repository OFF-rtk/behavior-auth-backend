import os
import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Tuple, List
from scipy.stats import zscore, percentileofscore
import json
from datetime import datetime

DATA_DIR = "data"
MODEL_DIR = "models"

FEATURES = [
    "tap_duration", "swipe_speed", "swipe_angle",
    "scroll_distance", "scroll_velocity", 
    "inter_key_delay_avg", "key_press_duration_avg", "typing_error_rate", #done
    "gyro_variance", "accelerometer_noise",
    "screen_transition_count", "avg_dwell_time_per_screen",
    "session_start_hour", "session_duration_sec"
]

class ModelManager:
    def __init__(self, dataset_root="data"):
        self.dataset_root = dataset_root
        self.models = {}
        
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(MODEL_DIR, exist_ok=True)
        
    def _get_model_path(self, user_id: str) -> str:
        return os.path.join(MODEL_DIR, f"{user_id}_model.pkl")
    
    def _get_user_data_path(self, user_id: str) -> str:
        return os.path.join(DATA_DIR, f"{user_id}.csv")
    
    def _get_meta_path(self, user_id: str) -> str:
        return os.path.join(MODEL_DIR, f"{user_id}_meta.json")
    
    def _load_model(self, user_id: str) -> Tuple[IsolationForest, StandardScaler]:
        with open(self._get_model_path(user_id), "rb") as f:
            model, scaler, iso_score = pickle.load(f)
            
        self.models[user_id] = (model, scaler, iso_score)
        return model, scaler, iso_score
    
    def _get_model(self, user_id: str) -> Tuple[IsolationForest, StandardScaler]:
        if user_id in self.models:
            return self.models[user_id]
        
        if os.path.exists(self._get_model_path(user_id)):
            return self._load_model[user_id]
        
        raise ValueError("Model not trained yet")
    
    def store_snapshot(self, user_id: str, snapshot: dict):
        df = pd.DataFrame([snapshot])
        user_data_path = self._get_user_data_path(user_id)
        if os.path.exists(user_data_path):
            existing = pd.read_csv(user_data_path)
            df = pd.concat([existing, df], ignore_index=True)
        df.to_csv(user_data_path, index=False)
        
        if len(df) >= 5:
            self._train_model(user_id, df)
            
    def _train_model(self, user_id: str):
        user_dir = os.path.join(self.dataset_root, user_id)
        session_files = sorted(f for f in os.listdir(user_dir) if f.startswith("session_"))

        all_snapshots = []

        for file in session_files:
            path = os.path.join(user_dir, file)
            df = pd.read_csv(path)
            df = df[FEATURES].dropna()
            if not df.empty:
                all_snapshots.append(df)

        if len(all_snapshots) < 5:
            print(f"[{user_id}] ⚠️ Not enough sessions to train.")
            return

        full_df = pd.concat(all_snapshots, ignore_index=True)

        if len(full_df) < 10:
            print(f"[{user_id}] ⚠️ Not enough total snapshots to train.")
            return

        # Use only the latest 100 snapshots (or all if less)
        train_df = full_df.tail(100)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(train_df[FEATURES])

        model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
        model.fit(X_scaled)

        iso_scores = model.decision_function(X_scaled)

        # Save model to disk
        with open(self._get_model_path(user_id), "wb") as f:
            pickle.dump((model, scaler, iso_scores), f)

        # Store in memory
        self.models[user_id] = (model, scaler, iso_scores)
        
        # Enhanced etadata
        quarantine_dir = os.path.join("quarantine", user_id)
        num_quarantined = len([
            f for f in os.listdir(quarantine_dir)
            if f.startswith("session_") and f.endswith(".csv")
        ]) if os.path.exists(quarantine_dir) else 0

        metadata = {
            "user_id": user_id,
            "model_exists": True,
            "last_trained": datetime.now().isoformat(),
            "snapshot_count": len(train_df),
            "num_sessions": len(session_files),
            "num_quarantined_sessions": num_quarantined,
            "model_type": "IsolationForest",
            "model_version": self._get_next_version(user_id)
        }
        
        with open(self._get_meta_path(user_id), "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"[{user_id}] ✅ Model trained and saved (snapshots: {len(train_df)})")
        print(f"[{user_id}] 🔢 Stored isolation scores: {len(iso_scores)}")

    
    def _get_next_version(self, user_id: str) -> int:
        meta_path = self._get_meta_path(user_id)
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                meta = json.load(f)
            return meta.get("model_version", 0) + 1
        return 1
    
    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def predict_risk(self, user_id: str, snapshot: dict) -> float:
        try:
            model, scaler, iso_scores = self._get_model(user_id)
        except:
            return 0.0
        
        try:
            X = pd.DataFrame([snapshot])[FEATURES]
            missing = [f for f in FEATURES if f not in snapshot or pd.isna(snapshot[f])]
            if missing:
                print(f"[{user_id}] Warning: Missing features in snapshot: {missing}")
                return 0.0

            
            X_scaled = scaler.transform(X)
            iso_score = model.decision_function(X_scaled)[0]

            # Improved normalization of IsolationForest score:
            # Clip to range [-0.5, 0.5] and map to [100, 0] risk
            
            if iso_scores is not None and len(iso_scores) >= 10:
                center = np.mean(iso_scores)
                scale = np.std(iso_scores) if np.std(iso_scores) > 0 else 0.01
                z_score = (iso_score - center) / scale
                norm_score = 1 / (1 + np.exp(-z_score * 1.5))  # sigmoid
            else:
                # fallback sigmoid normalization for early snapshots
                norm_score = 1 / (1 + np.exp(-iso_score * 20))

            # Convert to iso_risk (0 = safest, 70 = riskiest)
            iso_risk = round((1 - norm_score) * 100, 2)



            z_risk = np.mean(np.abs(zscore(X.iloc[0]))) * 10
            final_risk = round(0.6 * iso_risk + 0.4 * z_risk, 2)

            print(f"[{user_id}] 📊 Isolation score: {iso_score}")
            print(f"[{user_id}] 📊 Iso-risk percentile: {iso_risk}")
            print(f"[{user_id}] 📊 Z-score risk: {round(z_risk, 2)}")
            print(f"[{user_id}] 📊 Final risk: {final_risk}")

            return min(final_risk, 100)


        except Exception as e:
            print("Prediction error:", e)
            return 0.0
            