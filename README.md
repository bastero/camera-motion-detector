# Camera Motion Detection with AI Analysis

**Production-ready AppDaemon app for Home Assistant**

Detects motion using pixel-based analysis and identifies people, vehicles, and animals using Anthropic Claude AI.

---

## Overview

This system monitors your security camera (RTSP stream), detects motion using advanced pixel comparison, and uses AI to identify what triggered the motion. Perfect for driveway monitoring, front door security, or property surveillance.

### Key Features

✅ **Pixel-based motion detection** - Detects people/vehicles entering frame instantly
✅ **AI-powered identification** - Claude 3.5 Haiku analyzes what's happening
✅ **Cost-effective** - Only calls AI when real motion detected (~$2-3/month)
✅ **MQTT integration** - Publishes to Home Assistant for automations
✅ **Configurable sensitivity** - Tune for your specific environment
✅ **Focus areas** - Monitors driveway/property, ignores street activity

---

## Quick Start

### Prerequisites

- Home Assistant OS with AppDaemon add-on installed
- RTSP camera (Wyze, Reolink, etc.)
- Anthropic API key ([get one here](https://console.anthropic.com))
- MQTT broker (Mosquitto add-on)

### Installation

1. **Install AppDaemon dependencies:**
   ```yaml
   # Settings → Add-ons → AppDaemon → Configuration
   python_packages:
     - anthropic
     - requests
     - Pillow
     - numpy

   system_packages:
     - ffmpeg
   ```

2. **Deploy files:**
   - Copy `camera_detection_pixel.py` to `/addon_configs/a0d7b954_appdaemon/apps/ad-cameradetection/apps/camera_detection/`
   - Create `__init__.py` in the same directory (empty file)
   - Copy `apps.yaml` to `/addon_configs/a0d7b954_appdaemon/apps/`

3. **Configure:**
   Edit `apps.yaml`:
   ```yaml
   camera_detection:
     snapshot_url: "rtsp://YOUR_CAMERA_IP/live"
     anthropic_api_key: "YOUR_API_KEY"
   ```

4. **Restart AppDaemon:**
   Settings → Add-ons → AppDaemon → RESTART

### Verification

Check AppDaemon logs for:
```
INFO camera_detection: ✓ Camera Motion Detection started (pixel-based)
INFO camera_detection: ✓ Motion threshold: 2000 changed pixels
INFO camera_detection: Checking for motion...
```

---

## How It Works

```
┌──────────┐     Every 15s     ┌────────────────┐
│  Camera  ├─────────────────▶│ Capture Frame  │
└──────────┘      (RTSP)       └────────┬───────┘
                                        │
                                        ▼
                                ┌───────────────┐
                                │ Convert to    │
                                │ Grayscale     │
                                │ 320x240 pixels│
                                └───────┬───────┘
                                        │
                                        ▼
                                ┌───────────────┐
                                │ Compare       │
                                │ Pixels with   │
                                │ Previous Frame│
                                └───────┬───────┘
                                        │
                            2000+ pixels changed?
                                        │
                                       Yes
                                        ▼
                                ┌───────────────┐
                                │ Anthropic AI  │
                                │ Analysis      │
                                └───────┬───────┘
                                        │
                                        ▼
                                ┌───────────────┐
                                │ Publish to    │
                                │ MQTT          │
                                └───────────────┘
```

### Motion Detection Algorithm

1. **Capture:** Gets frame from RTSP camera
2. **Resize:** Converts to 320x240 grayscale (fast processing)
3. **Compare:** Checks each pixel against previous frame
4. **Count:** Tallies pixels that changed by 30+ brightness units
5. **Trigger:** If 2000+ pixels changed, analyze with AI

**Why this works better than file size comparison:**
- Person walking into empty frame changes 5,000-15,000 pixels ✅
- JPEG file size might only change 1,000 bytes ❌
- Result: Instant detection vs. missed events

---

## Configuration

### Basic Settings

```yaml
camera_detection:
  # RTSP stream from camera
  snapshot_url: "rtsp://username:password@192.168.1.100/live"

  # How often to check for motion (seconds)
  check_interval: 15

  # Number of pixels that must change to trigger
  motion_pixel_threshold: 2000

  # Brightness change required per pixel (0-255 scale)
  pixel_difference_threshold: 30

  # Anthropic API key
  anthropic_api_key: "sk-ant-api03-..."

  # Wait time between AI analyses (prevents spam)
  cooldown_seconds: 60

  # MQTT topic prefix
  mqtt_topic_prefix: "camera_detection"
```

### Sensitivity Tuning

**Too many false alarms?**
```yaml
motion_pixel_threshold: 3000      # Require more pixels to change
pixel_difference_threshold: 40    # Require bigger brightness change
check_interval: 20                # Check less frequently
```

**Missing events?**
```yaml
motion_pixel_threshold: 1500      # More sensitive
pixel_difference_threshold: 20    # Detect subtle changes
check_interval: 10                # Check more often
```

**Busy street triggers detection?**
- Adjust camera angle to exclude street
- Increase `motion_pixel_threshold` to 4000+
- AI prompt already filters non-property activity

---

## MQTT Topics

### Published Topics

| Topic | Payload | Retained | Description |
|-------|---------|----------|-------------|
| `camera_detection/status` | `online`/`offline` | Yes | System status |
| `camera_detection/motion/binary` | `ON` | No | Motion detected event |
| `camera_detection/last_detection` | JSON | Yes | Most recent detection |
| `camera_detection/{location}/{type}` | JSON | No | Specific detection |

### Detection JSON Format

```json
{
  "type": "person",
  "location": "driveway",
  "description": "walking toward house carrying package",
  "confidence": 0.85,
  "timestamp": "2026-01-01T16:30:45.123456"
}
```

### Location Values

- `driveway` - In driveway area
- `in_front` - In front of property
- `walking_by` - Passing by on sidewalk

### Type Values

- `person` - Human detected
- `vehicle` - Car, truck, bike, etc.
- `animal` - Pet or wildlife

---

## Home Assistant Integration

### Binary Sensor

```yaml
# configuration.yaml
binary_sensor:
  - platform: mqtt
    name: "Driveway Motion"
    state_topic: "camera_detection/motion/binary"
    payload_on: "ON"
    device_class: motion
    off_delay: 30
```

### Sensor for Last Detection

```yaml
sensor:
  - platform: mqtt
    name: "Last Camera Detection"
    state_topic: "camera_detection/last_detection"
    value_template: "{{ value_json.type }} in {{ value_json.location }}"
    json_attributes_topic: "camera_detection/last_detection"
    json_attributes_template: "{{ value_json | tojson }}"
```

### Automation Examples

**Notify when person detected:**
```yaml
automation:
  - alias: "Driveway Person Alert"
    trigger:
      platform: mqtt
      topic: "camera_detection/driveway/person"
    action:
      service: notify.mobile_app_iphone
      data:
        title: "Person in Driveway"
        message: "{{ trigger.payload_json.description }}"
```

**Turn on lights at night:**
```yaml
automation:
  - alias: "Driveway Lights on Motion"
    trigger:
      platform: mqtt
      topic: "camera_detection/motion/binary"
      payload: "ON"
    condition:
      condition: sun
      after: sunset
    action:
      service: light.turn_on
      target:
        entity_id: light.driveway_lights
      data:
        brightness: 255
```

**Announce deliveries:**
```yaml
automation:
  - alias: "Delivery Notification"
    trigger:
      platform: mqtt
      topic: "camera_detection/in_front/person"
    condition:
      condition: template
      value_template: "{{ 'package' in trigger.payload_json.description or 'delivery' in trigger.payload_json.description }}"
    action:
      service: tts.google_say
      data:
        message: "Delivery person at the door"
```

---

## Cost Estimates

### Anthropic API Usage

**Typical residential driveway:**
- 5-10 detections per day (mail, delivery, residents, etc.)
- $0.01 per image analysis (Claude 3.5 Haiku)
- **Daily cost: $0.05-0.10**
- **Monthly cost: $1.50-3.00**

**High traffic area:**
- 20-30 detections per day
- **Monthly cost: $6-9**

**Cost-saving features built-in:**
- 60-second cooldown (prevents repeated analysis of same event)
- Pixel threshold filters false positives
- Only analyzes when real motion detected
- No analysis of clouds, shadows, trees

---

## Troubleshooting

### No motion detected

**Check logs for pixel counts:**
```
Pixels changed: 150 (threshold: 2000)
```

**If consistently below threshold:**
- Lower `motion_pixel_threshold` to 1500
- Lower `pixel_difference_threshold` to 20
- Verify camera is pointed at active area

### Too many false alarms

**Common causes:**
- Trees swaying → increase threshold to 3000
- Sun/shadow changes → increase `pixel_difference_threshold` to 40
- Busy street in frame → adjust camera angle

### AI not detecting objects

**Verify in logs:**
```
Analysis complete: [summary]
Detected [LOCATION]: type - description
```

**If analysis returns empty:**
- Check if object is in focus areas (driveway, in_front)
- AI ignores street/neighbor activity by design
- Review camera angle and framing

### RTSP connection issues

**Symptoms:**
```
Failed to capture frame
```

**Solutions:**
- Verify RTSP URL is correct
- Test with VLC: `vlc rtsp://camera_ip/live`
- Check camera network settings
- Ensure ffmpeg is installed in AppDaemon

---

## File Structure

```
/addon_configs/a0d7b954_appdaemon/
├── appdaemon.yaml
└── apps/
    ├── apps.yaml                                    # Main configuration
    └── ad-cameradetection/
        └── apps/
            └── camera_detection/
                ├── __init__.py                      # Empty file (required)
                └── camera_detection_pixel.py        # Main app
```

---

## Upgrading

### From File Size Detection (old)

If you were using `camera_detection_scheduled.py` with `motion_threshold` in bytes:

1. Install new dependencies (Pillow, numpy)
2. Copy `camera_detection_pixel.py` to deployment location
3. Update `apps.yaml`:
   ```yaml
   module: camera_detection.camera_detection_pixel  # Changed
   motion_pixel_threshold: 2000                      # New parameter
   pixel_difference_threshold: 30                    # New parameter
   # Remove old motion_threshold parameter
   ```
4. Restart AppDaemon

**Benefits:**
- Detects people entering frame instantly
- Much more reliable for outdoor monitoring
- No more "standing in front of camera for 60 seconds" to trigger

---

## Support

### Documentation

- `PRODUCTION_READY.md` - Full production deployment guide
- `PIXEL_MOTION_DETECTION_UPGRADE.md` - Technical details on pixel detection
- `TROUBLESHOOTING.md` - Common issues and solutions

### Logs

Monitor AppDaemon logs for debugging:
Settings → Add-ons → AppDaemon → Log

### Typical Log Output

```
2026-01-01 16:00:00 INFO camera_detection: Checking for motion...
2026-01-01 16:00:03 INFO camera_detection: Pixels changed: 8542 (threshold: 2000), avg change: 67.8
2026-01-01 16:00:03 INFO camera_detection: 🎯 Motion detected! 8542 pixels changed
2026-01-01 16:00:03 INFO camera_detection: Analyzing frame (321273 bytes)...
2026-01-01 16:00:06 INFO camera_detection: Analysis complete: Person detected walking up driveway
2026-01-01 16:00:06 INFO camera_detection: Detected [DRIVEWAY]: person - walking toward house
```

---

## License

MIT License - Free to use and modify

## Credits

Built with:
- [Anthropic Claude AI](https://anthropic.com) - Vision analysis
- [AppDaemon](https://appdaemon.readthedocs.io) - Home Assistant automation
- [Home Assistant](https://home-assistant.io) - Smart home platform
- [FFmpeg](https://ffmpeg.org) - RTSP stream capture

---

## Version

**v2.0** - Pixel-based motion detection (2026-01-01)

Previous versions used file size comparison which was unreliable for detecting people entering frame.
