# Pixel-Based Motion Detection Upgrade

## What Changed and Why

### The Problem with File Size Comparison:
- **Old method**: Compared JPEG file sizes between frames
- **Issue**: JPEG compression makes file size unreliable for motion detection
- **Result**: Someone walking into frame might only change file size by 1,000 bytes (below threshold)
- **You experienced**: Had to stand still for a long time to trigger detection

### The New Pixel-Based Solution:
- **New method**: Converts images to grayscale and compares actual pixel values
- **Advantage**: Detects real visual changes, not file size changes
- **Result**: Instantly detects when someone walks into frame
- **Perfect for**: Your use case of detecting people entering the driveway

## How It Works:

1. **Captures frame** from RTSP camera
2. **Resizes to 320x240** (76,800 pixels) for fast processing
3. **Converts to grayscale** (0-255 brightness values)
4. **Compares each pixel** to previous frame
5. **Counts changed pixels** that differ by more than 30 brightness units
6. **Triggers if 2,000+ pixels changed** (~2.6% of image)

## Configuration Parameters:

```yaml
check_interval: 10  # Check every 10 seconds (faster than before)

motion_pixel_threshold: 2000  # Number of pixels that must change
# - 2000 = ~2.6% of image
# - Lower = more sensitive (500 = very sensitive)
# - Higher = less sensitive (5000 = only large movements)

pixel_difference_threshold: 30  # How bright/dark a pixel must change
# - 30 = moderate sensitivity (good default)
# - Lower = detects subtle changes like shadows (10-20)
# - Higher = only detects major changes (50-100)

cooldown_seconds: 30  # Wait 30s between AI analyses
```

## Installation Steps:

### Step 1: Add Python Dependencies

Go to Home Assistant → Settings → Add-ons → AppDaemon → Configuration tab

Add these packages to the `python_packages` list:

```yaml
python_packages:
  - anthropic
  - requests
  - Pillow
  - numpy
```

Click **SAVE**

### Step 2: Restart AppDaemon

Settings → Add-ons → AppDaemon → **RESTART**

### Step 3: Verify in Logs

You should see:

```
INFO camera_detection: Initializing Camera Motion Detection (Pixel-based)
INFO camera_detection: ✓ Anthropic client initialized
INFO camera_detection: ✓ Checking for motion every 10 seconds
INFO camera_detection: ✓ Motion threshold: 2000 changed pixels
INFO camera_detection: ✓ Pixel difference: 30 brightness change
INFO camera_detection: ✓ Cooldown: 30 seconds
INFO camera_detection: ✓ Camera Motion Detection started (pixel-based)
```

Then every 10 seconds:

```
INFO camera_detection: Checking for motion...
INFO camera_detection: Pixels changed: 450 (threshold: 2000), avg change: 12.3
INFO camera_detection: No significant motion detected
```

When someone walks into frame:

```
INFO camera_detection: Checking for motion...
INFO camera_detection: Pixels changed: 8542 (threshold: 2000), avg change: 67.8
INFO camera_detection: 🎯 Motion detected! 8542 pixels changed (avg: 67.8)
INFO camera_detection: Analyzing frame (321273 bytes)...
INFO camera_detection: Analysis complete: Person detected walking in driveway
INFO camera_detection: Detected [DRIVEWAY]: person - walking toward house
```

## Testing:

1. **Static scene**: Should show 0-500 pixels changed
2. **Small movement** (hand wave): 500-2000 pixels changed
3. **Person enters frame**: 5000-20000 pixels changed ✅ TRIGGERS
4. **Car drives by**: 10000-30000 pixels changed ✅ TRIGGERS

## Tuning Sensitivity:

**Too many false alarms?**
- Increase `motion_pixel_threshold` to 5000
- Increase `pixel_difference_threshold` to 50

**Missing events?**
- Decrease `motion_pixel_threshold` to 1000
- Decrease `pixel_difference_threshold` to 20

**Check too slow?**
- Decrease `check_interval` to 5 (but uses more CPU)

## Files Changed:

1. **Created**: `/addon_configs/a0d7b954_appdaemon/apps/ad-cameradetection/apps/camera_detection/camera_detection_pixel.py`
2. **Updated**: `/addon_configs/a0d7b954_appdaemon/apps/apps.yaml`
   - Changed module from `camera_detection_scheduled` to `camera_detection_pixel`
   - Updated configuration parameters

## Reverting to Old Version:

If you want to go back to file size comparison:

1. Edit `apps.yaml`
2. Change `module: camera_detection.camera_detection_pixel` to `module: camera_detection.camera_detection_scheduled`
3. Restart AppDaemon

---

## Summary:

This upgrade fundamentally changes **how** motion is detected:

- **Old**: "Did the JPEG file size change by 5000+ bytes?"
- **New**: "Did 2000+ pixels change by 30+ brightness units?"

The pixel-based approach is **much better** for detecting people walking into frame, which is exactly your use case for monitoring the driveway!
