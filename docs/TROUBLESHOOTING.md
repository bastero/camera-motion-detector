# Fix Camera Detection - Motion Threshold Too High

## Problem
Your camera detection is working but not triggering AI analysis because:
- Current threshold: **50,000 bytes** (default)
- Actual frame differences: **5,000-7,000 bytes**
- Result: Motion never detected, AI never called

## Solution
Add `motion_threshold: 10000` to your apps.yaml configuration file.

---

## Step-by-Step Instructions

### 1. Open File Editor in Home Assistant
- Go to Home Assistant web interface: http://192.168.1.125:8123
- Click **Settings** (gear icon)
- Click **Add-ons**
- Click **File editor**
- Click **OPEN WEB UI**

### 2. Navigate to apps.yaml
In the file browser on the left, navigate to:
```
/config/apps/apps.yaml
```

### 3. Find the camera_detection section
Look for this section:
```yaml
camera_detection:
  module: camera_detection.camera_detection_scheduled
  class: CameraMotionDetection

  snapshot_url: "rtsp://wyzecam1:garby111@192.168.1.206/live"
  check_interval: 30
  anthropic_api_key: "YOUR_ANTHROPIC_API_KEY_HERE"
  mqtt_topic_prefix: "camera_detection"
```

### 4. Add this line AFTER check_interval
```yaml
  motion_threshold: 10000
```

### 5. Final configuration should look like:
```yaml
camera_detection:
  module: camera_detection.camera_detection_scheduled
  class: CameraMotionDetection

  snapshot_url: "rtsp://wyzecam1:garby111@192.168.1.206/live"
  check_interval: 30
  motion_threshold: 10000
  anthropic_api_key: "YOUR_ANTHROPIC_API_KEY_HERE"
  mqtt_topic_prefix: "camera_detection"
```

### 6. Save the file
Click the **SAVE** icon (floppy disk) in the top right

### 7. Restart AppDaemon
- Go back to Home Assistant
- Click **Settings** → **Add-ons** → **AppDaemon**
- Click **RESTART**
- Wait 30 seconds

### 8. Check the logs
- In AppDaemon add-on, click **Log** tab
- You should now see within 30-60 seconds:
```
Motion detected! Frame size difference: 6720 bytes
Analyzing frame (328056 bytes)...
```

---

## What to Expect After Fix

With the lower threshold (10,000 bytes), the system will:

✅ Detect normal scene changes (people moving, lighting changes)
✅ Call AI for analysis
✅ Publish detections to MQTT
✅ Respect 60-second cooldown between analyses
✅ Filter out decorations with keyword matching

The first motion event should trigger within 30-60 seconds if there's any activity in view.

---

## If You Still Don't See AI Analysis

If motion is detected but AI still doesn't respond, it could be:

1. **API Key Issue**: The Anthropic API key might be invalid
   - Check for error messages in the logs mentioning "401" or "authentication"

2. **Network Issue**: AppDaemon can't reach api.anthropic.com
   - Check for error messages mentioning "connection" or "timeout"

3. **Code Issue**: The analyze_frame function has a bug
   - Look for Python exceptions in the logs

Share the logs after the fix and I can diagnose further!
