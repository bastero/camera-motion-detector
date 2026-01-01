# Deployment Guide

Quick reference for deploying the camera detection system to Home Assistant.

---

## Pre-Deployment Checklist

- [ ] Home Assistant OS installed
- [ ] AppDaemon add-on installed
- [ ] Mosquitto MQTT broker add-on installed
- [ ] Camera accessible via RTSP
- [ ] Anthropic API key obtained

---

## Step-by-Step Deployment

### 1. Install AppDaemon Dependencies

**Settings → Add-ons → AppDaemon → Configuration tab**

Add to the configuration:

```yaml
python_packages:
  - anthropic
  - requests
  - Pillow
  - numpy

system_packages:
  - ffmpeg
```

Click **SAVE**

### 2. Create Directory Structure

Using File Editor add-on, create these directories:

```
/addon_configs/a0d7b954_appdaemon/apps/
├── apps.yaml
└── ad-cameradetection/
    └── apps/
        └── camera_detection/
            ├── __init__.py
            └── camera_detection_pixel.py
```

**Note:** The `a0d7b954_appdaemon` ID might be different on your system. Check existing apps to find the correct path.

### 3. Deploy Files

**Copy from `deployment/` folder:**

1. **camera_detection_pixel.py** → `/addon_configs/a0d7b954_appdaemon/apps/ad-cameradetection/apps/camera_detection/`

2. **Create __init__.py** in the same directory (empty file or with a comment)

3. **apps.yaml** → `/addon_configs/a0d7b954_appdaemon/apps/`

### 4. Configure

Edit `/addon_configs/a0d7b954_appdaemon/apps/apps.yaml`:

```yaml
camera_detection:
  module: camera_detection.camera_detection_pixel
  class: CameraMotionDetection

  # YOUR CAMERA RTSP URL
  snapshot_url: "rtsp://username:password@192.168.1.xxx/live"

  # Check interval (seconds)
  check_interval: 15

  # Motion thresholds
  motion_pixel_threshold: 2000
  pixel_difference_threshold: 30

  # YOUR ANTHROPIC API KEY
  anthropic_api_key: "sk-ant-api03-YOUR_KEY_HERE"

  # MQTT settings
  mqtt_topic_prefix: "camera_detection"
  cooldown_seconds: 60
```

**Replace:**
- Camera RTSP URL
- Anthropic API key

### 5. Restart AppDaemon

**Settings → Add-ons → AppDaemon → RESTART**

Wait for startup (may take 1-2 minutes on first run as it installs packages).

### 6. Verify Installation

**Check logs:** Settings → Add-ons → AppDaemon → Log

Look for:

```
✅ SUCCESS - Should see:
INFO camera_detection: Initializing Camera Motion Detection (Pixel-based)
INFO camera_detection: ✓ Anthropic client initialized
INFO camera_detection: ✓ Checking for motion every 15 seconds
INFO camera_detection: ✓ Motion threshold: 2000 changed pixels
INFO camera_detection: ✓ Pixel difference: 30 brightness change
INFO camera_detection: ✓ Cooldown: 60 seconds
INFO camera_detection: ✓ Camera Motion Detection started (pixel-based)
INFO camera_detection: Checking for motion...
INFO camera_detection: Pixels changed: 150 (threshold: 2000), avg change: 22.3
INFO camera_detection: No significant motion detected
```

```
❌ ERROR - If you see:
ERROR: ModuleNotFoundError: No module named 'numpy'
  → Go back to step 1, add dependencies, restart

ERROR: Failed to capture frame
  → Check RTSP URL in step 4

ERROR: Failed to initialize Anthropic client
  → Check API key in step 4
```

### 7. Test Detection

**Walk in front of the camera.** Within 15 seconds you should see:

```
INFO camera_detection: Pixels changed: 8542 (threshold: 2000), avg change: 67.8
INFO camera_detection: 🎯 Motion detected! 8542 pixels changed
INFO camera_detection: Analyzing frame (321273 bytes)...
INFO camera_detection: Analysis complete: Person detected...
INFO camera_detection: Detected [DRIVEWAY]: person - walking toward house
```

### 8. Verify MQTT

**Developer Tools → MQTT → Listen to topic:** `camera_detection/#`

Click **START LISTENING**

Trigger motion again. You should see messages appear:

```json
Topic: camera_detection/motion/binary
Payload: ON

Topic: camera_detection/last_detection
Payload:
{
  "type": "person",
  "location": "driveway",
  "description": "walking toward house",
  "confidence": 0.85,
  "timestamp": "2026-01-01T16:30:45.123456"
}
```

---

## Post-Deployment Configuration

### Adjust Sensitivity

Monitor for a day and tune thresholds:

**Too many false alarms (trees, shadows):**
```yaml
motion_pixel_threshold: 3000
pixel_difference_threshold: 40
```

**Missing events (far away, small movements):**
```yaml
motion_pixel_threshold: 1500
pixel_difference_threshold: 20
check_interval: 10
```

### Create Automations

See **README.md** for automation examples.

---

## Troubleshooting Deployment

### AppDaemon won't start

**Check configuration syntax:**
```bash
# In Terminal add-on or SSH:
appdaemon -c /config -D DEBUG
```

### App not loading

**Check apps.yaml path:**
```
ERROR: Failed to import 'camera_detection.camera_detection_pixel'
```

Verify file is at:
`/addon_configs/a0d7b954_appdaemon/apps/ad-cameradetection/apps/camera_detection/camera_detection_pixel.py`

And `__init__.py` exists in the same directory.

### RTSP connection fails

**Test RTSP URL:**
```bash
# On your computer with VLC installed:
vlc rtsp://username:password@192.168.1.xxx/live
```

If VLC can't connect, the URL is wrong or camera is unreachable.

### No MQTT messages

**Check Mosquitto broker:**

Settings → Add-ons → Mosquitto broker → Log

Should see connection from AppDaemon.

**Verify MQTT integration:**

Settings → Devices & Services → MQTT

Should show as "configured".

---

## Upgrade from v1.x

If you're upgrading from the file size detection version:

1. **Backup current configuration**
2. **Add new dependencies** (Pillow, numpy)
3. **Copy new `camera_detection_pixel.py`**
4. **Update apps.yaml:**
   - Change `module` to `camera_detection_pixel`
   - Replace `motion_threshold` with `motion_pixel_threshold`
   - Add `pixel_difference_threshold`
5. **Restart AppDaemon**
6. **Monitor logs** for new pixel-based output

See **CHANGELOG.md** for full details.

---

## Directory Structure After Deployment

```
/addon_configs/a0d7b954_appdaemon/
├── appdaemon.yaml
└── apps/
    ├── apps.yaml
    └── ad-cameradetection/
        └── apps/
            └── camera_detection/
                ├── __init__.py
                └── camera_detection_pixel.py
```

**Optional old files (can be removed):**
- `camera_detection_scheduled.py` (v1.x file size version)
- `camera_detection_frigate_http.py` (abandoned Frigate version)
- `camera_detection_simple.py` (early test version)

---

## Production Monitoring

### Daily

- Check AppDaemon logs for errors
- Verify detections are accurate
- Monitor false positive rate

### Weekly

- Review Anthropic API usage/costs
- Tune sensitivity if needed
- Check MQTT message retention

### Monthly

- Review automation effectiveness
- Consider adding new automations
- Update documentation with learnings

---

## Support Files

- **README.md** - Main documentation
- **PRODUCTION_READY.md** - Detailed production guide with examples
- **PIXEL_MOTION_DETECTION_UPGRADE.md** - Technical details on algorithm
- **TROUBLESHOOTING.md** - Common issues
- **CHANGELOG.md** - Version history

---

## Success Criteria

✅ **Deployment successful when:**

1. AppDaemon starts without errors
2. Logs show motion checks every 15 seconds
3. Walking in front of camera triggers detection within 15 seconds
4. AI analysis describes what was detected
5. MQTT messages appear in Home Assistant
6. Automations respond to detections

---

## Rollback Plan

If something goes wrong:

1. **Stop AppDaemon:** Settings → Add-ons → AppDaemon → STOP
2. **Revert apps.yaml** to backup
3. **Remove camera_detection_pixel.py**
4. **Restore old version** (if upgrading)
5. **Restart AppDaemon**

Always keep backups of working configurations!
