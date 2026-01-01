# Changelog

All notable changes to the Camera Detection system.

---

## [2.0.0] - 2026-01-01

### Changed - Major Algorithm Upgrade

**BREAKING CHANGE:** Switched from file size comparison to pixel-based motion detection

**Why the change:**
- Old method compared JPEG file sizes between frames
- Person walking into frame only changed file size by ~1,000 bytes
- Required standing still for 60+ seconds to accumulate enough change
- Fundamentally flawed for detecting people entering frame

**New pixel-based detection:**
- Converts frames to 320x240 grayscale
- Compares each pixel's brightness (0-255 scale)
- Counts pixels that changed by 30+ units
- Triggers when 2,000+ pixels changed (~2.6% of image)
- Detects person entering frame instantly

### Added

- `motion_pixel_threshold` parameter (replaces `motion_threshold`)
- `pixel_difference_threshold` parameter
- Configurable `cooldown_seconds` from config file
- Numpy and Pillow dependencies for image processing
- Debug logging showing pixel counts and thresholds

### Removed

- `motion_threshold` parameter (bytes) - replaced by pixel count
- File size comparison algorithm

### Migration Guide

1. **Add dependencies to AppDaemon:**
   ```yaml
   python_packages:
     - Pillow
     - numpy
   ```

2. **Update apps.yaml:**
   ```yaml
   # Old (v1.x):
   motion_threshold: 50000

   # New (v2.0):
   motion_pixel_threshold: 2000
   pixel_difference_threshold: 30
   ```

3. **Change module reference:**
   ```yaml
   # Old:
   module: camera_detection.camera_detection_scheduled

   # New:
   module: camera_detection.camera_detection_pixel
   ```

4. Restart AppDaemon

### Performance Impact

- **CPU usage:** Slightly higher (image processing vs file size check)
- **Memory usage:** +5-10MB (image arrays in memory)
- **Detection accuracy:** Dramatically improved
- **Response time:** Instant (was 30-60 seconds)

---

## [1.2.0] - 2025-12-31

### Added

- Configurable check_interval parameter
- Configurable motion_threshold parameter
- Outdoor-focused AI prompt

### Fixed

- AI prompt now ignores indoor activity when pointed outdoors
- Filters out Christmas decorations and static objects

---

## [1.1.0] - 2025-12-30

### Changed

- Switched from Frigate integration to scheduled polling
- Direct RTSP capture with ffmpeg
- Removed Frigate dependency

### Fixed

- Frigate MQTT authentication issues (bypassed entirely)
- Frigate CPU detector not producing events (no longer used)

---

## [1.0.0] - 2025-12-29

### Added

- Initial AppDaemon integration
- Frigate-based motion detection
- Anthropic Claude AI analysis
- MQTT publishing to Home Assistant
- Focus on driveway monitoring
- Filter out decorations

### Known Issues (Fixed in later versions)

- File size comparison unreliable
- Required prolonged presence to trigger
- Missed quick events (person walking by)

---

## Development History

### Abandoned Approaches

1. **Standalone Python script** - Required separate server
2. **Frigate NVR integration** - MQTT auth never worked, CPU detector too slow
3. **File size comparison** - Fundamentally flawed for entrance detection

### Why Pixel-Based Detection Won

After testing in production:
- Indoor testing: Standing still showed 500-1,900 pixel changes (below threshold)
- Motion event: Walking showed 2,400+ pixel changes (instant trigger)
- Outdoor monitoring: Person entering driveway shows 5,000-15,000 pixel changes
- False positives: Clouds/shadows show 50-500 pixel changes (correctly ignored)

**Result:** Perfect for detecting people/vehicles entering property

---

## Future Enhancements (Potential)

- [ ] Zone-based detection (multiple areas with different thresholds)
- [ ] Time-based sensitivity (lower threshold at night)
- [ ] Video clip recording on detection
- [ ] Face recognition for known vs unknown people
- [ ] License plate reading for vehicles
- [ ] Motion heatmap visualization
- [ ] Integration with NVR systems
- [ ] Mobile app for live view

**Note:** Current system is production-ready and stable. Future enhancements only if needed.
