# 🧠 Behavior-Based Authentication API

A production-ready, context-aware backend API that authenticates users based on behavioral and contextual anomalies — including typing patterns, sensor noise, swipe behavior, device info, network, and geolocation.

Deployed Live: [https://behavior-auth-api.onrender.com](https://behavior-auth-api.onrender.com)

---

## 🚀 Features

- 🔐 **Behavior-Based Authentication** using tap, swipe, typing, scroll, and sensor data
- 🧠 **Isolation Forest ML model** per user for anomaly detection
- 🌍 **Contextual Awareness**:
  - IP & Network Type changes
  - Device info mismatch
  - Geolocation/time anomalies
- 🗃️ **Auto-Retraining** of models after multiple sessions
- 🚨 **Risk-Based Quarantine** of high-risk sessions
- 📈 **Session and Risk Logging** for dashboard integration

---

## 📦 Tech Stack

- **FastAPI** (Python 3.11)
- **Gunicorn** with Uvicorn workers
- **Scikit-learn** for Isolation Forest model
- **Render** for deployment
- **pandas, numpy, geopy** for data processing
- **Postman** for testing API endpoints

---

## 🗂️ Project Structure

```bash
.
├── app/
│   ├── main.py                # FastAPI endpoints
│   ├── model_manager.py       # ML model logic
│   ├── analyze_context.py     # Context shift analysis
│   └── flatten_snapshot.py    # Snapshot transformer
├── data/                      # Stored session CSVs (per user)
├── models/                    # Saved models and metadata
├── quarantine/                # Quarantined high-risk sessions
├── context_cache/             # Context history (per user)
├── device_profiles/           # Stored device baselines
├── risks/                     # Risk logs (JSON)
├── requirements.txt           # Python dependencies
├── startup.sh                 # Entry script for gunicorn
└── render.yaml                # Blueprint for Render deployment
```

---

## 📡 API Endpoints

### `GET /`
Check if the API is live.

### `POST /predict`
Predict risk score for a snapshot.

```json
{
  "user_id": "s001",
  "tap_data": {
    "tap_duration": 0.34
  },
  "typing_data": {
    "inter_key_delay_avg": 0.12,
    "key_press_duration_avg": 0.08,
    "typing_error_rate": 0.01
  },
  "sensor_data": {
    "gyro_variance": 0.02,
    "accelerometer_noise": 0.03
  },
  "swipe_data": {
    "swipe_speed": 1.2,
    "swipe_angle": 45.0
  },
  "scroll_data": {
    "scroll_distance": 500,
    "scroll_velocity": 0.9
  },
  "session_metadata": {
    "session_duration_sec": 120,
    "session_start_hour": 14,
    "screen_transition_count": 10,
    "avg_dwell_time_per_screen": 12
  },
  "context": {
    "location": {
      "latitude": 28.6139,
      "longitude": 77.2090,
      "timestamp": "2025-07-11T12:34:56"
    },
    "network_info": {
      "ip_address": "192.168.0.1",
      "network_type": "wifi",
      "isp": "Jio"
    },
    "device_info": {
      "os": "Android",
      "os_version": "13",
      "device_model": "Pixel 6"
    }
  }
}

```

### `POST /end-session`
Submit full session for storage, retraining, and quarantine check.

### `POST /store-device-profile/{user_id}`
Store device baseline (OS, model, etc.) for future context comparison.

### `GET /device-profile/{user_id}`
Fetch stored device profile.

### `GET /model-meta/{user_id}`
Check ML model status and metadata.

### `GET /session-data/{user_id}`
Returns last 10 sessions and full snapshot + risk log for dashboard use.

### `GET /all-users-meta`
Returns metadata + latest risk score for all users (for admin dashboard).

### `DELETE /reset-user-data/{user_id}`
Fully resets a user — deletes all sessions, models, risks, and quarantine data.

---

## ⚙️ Deployment (via Render)

This app is deployed using Render’s free tier via `render.yaml`. Key setup:

- Python 3.11.9 (`PYTHON_VERSION` env var)
- `startup.sh` runs gunicorn with Uvicorn workers
- Auto-redeploys on GitHub push

**Live URL**: [https://behavior-auth-api.onrender.com](https://behavior-auth-api.onrender.com)

---

## 🧪 Testing

Use Postman or curl to POST sample sessions and snapshots.

```bash
curl -X POST https://behavior-auth-api.onrender.com/predict \
  -H "Content-Type: application/json" \
  -d @sample_snapshot.json
```

---

## 📈 Future Improvements

- Add Auth layer (JWT or API key)
- Enable dashboard integration via WebSocket
- Push risk alerts to Slack or email
- Add Dockerfile for portability
- Expand model types (e.g., LSTM, autoencoders)

---

## 👨‍💻 Author

**Ritik Joshi**  
B.Tech Computer Science, BTKIT Dwarahat  
[GitHub – OFF-rtk](https://github.com/OFF-rtk)

---

## 📄 License

MIT License — free to use with attribution

---

## 📄 API Documentation

See [API_Documentation.pdf](./API_Documentation.pdf) for exact input schema, risk scoring method, and context analysis units.
