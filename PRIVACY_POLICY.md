# 🔒 Privacy Policy — Behavior-Based Authentication API

**Effective Date:** July 2025

---

## 1. Introduction

This Privacy Policy explains how we collect, use, and protect behavioral and contextual data through this authentication system. By using this system, you agree to the terms outlined below.

---

## 2. What Data We Collect

We collect behavioral and contextual signals that help us detect anomalies and verify legitimate users:

- Tap, swipe, and typing behavior  
- Sensor noise data (accelerometer, gyroscope)  
- Device details (OS, OS version, device model)  
- Network info (IP address, network type, ISP)  
- Geolocation (latitude, longitude, timestamp)  
- Session metadata (session duration, active hours, screen transitions)

---

## 3. Purpose of Collection

The data is strictly used to:

- Train per-user machine learning models  
- Score risk in real-time during sessions  
- Detect context and device mismatches  
- Quarantine potentially fraudulent behavior

> ✅ We do **not** use this data for profiling, advertising, or selling.

---

## 4. Data Storage & Retention

- Session and model data is stored locally on secure servers.
- Context history is cached temporarily for scoring and overwritten.
- Quarantined sessions and risk logs are stored only for audit and retraining.

You may request deletion of your user data at any time via the `/reset-user-data/{user_id}` API.

---

## 5. Data Sharing

> ❌ We do **not** sell, rent, or share any user data with third parties.

Only the development team has access to stored data, and it is used solely for model evaluation and testing.

---

## 6. Your Rights

You have the right to:

- 📥 Access your data
- 🗑️ Request deletion of your data
- 🔁 Withdraw your consent for data usage at any time

To initiate any of these, please reach out via the contact below.

---

## 7. Contact

**Ritik Joshi**  
Developer – Behavior Auth API  
📧 `mail.officialritik@gmail.com`

---

## 8. Updates to This Policy

This policy may be updated as development evolves. You will be notified of any significant changes via the project dashboard or repository.

---

**By continuing to use this system, you acknowledge and accept this policy.**

