# Camera Detection System - File Index

Quick reference to find what you need.

---

## Start Here

📖 **[README.md](README.md)** - Main documentation, features, how it works, configuration

🚀 **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Step-by-step deployment instructions

---

## Production Files

### Deploy These to Home Assistant

📁 **deployment/**
- `camera_detection_pixel.py` - Main application (v2.0, pixel-based) ⭐ CURRENT
- `camera_detection_scheduled.py` - Legacy version (v1.x, file size) [reference only]
- `apps.yaml` - Configuration template

---

## Documentation

### Essential Reading

📘 **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Complete project overview, metrics, status

📋 **[CHANGELOG.md](CHANGELOG.md)** - Version history, migration guides

### Detailed Guides

📁 **docs/**
- `PRODUCTION_READY.md` - Full production guide with automation examples
- `PIXEL_MOTION_DETECTION_UPGRADE.md` - Technical details on pixel detection
- `TROUBLESHOOTING.md` - Common issues and solutions

---

## Quick Links

### I want to...

**Deploy the system:**
→ [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

**Understand how it works:**
→ [README.md](README.md) → "How It Works" section

**Tune sensitivity:**
→ [README.md](README.md) → "Configuration" → "Sensitivity Tuning"

**Fix an issue:**
→ [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

**Create automations:**
→ [README.md](README.md) → "Home Assistant Integration"

**Understand the algorithm:**
→ [docs/PIXEL_MOTION_DETECTION_UPGRADE.md](docs/PIXEL_MOTION_DETECTION_UPGRADE.md)

**See what changed:**
→ [CHANGELOG.md](CHANGELOG.md)

**Get project stats:**
→ [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

---

## File Purposes

| File | Purpose | Audience |
|------|---------|----------|
| README.md | Main documentation | All users |
| DEPLOYMENT_GUIDE.md | Step-by-step deployment | First-time users |
| PROJECT_SUMMARY.md | Project overview & metrics | Developers, managers |
| CHANGELOG.md | Version history | Users upgrading |
| deployment/camera_detection_pixel.py | Production app code | Deployed to HA |
| deployment/apps.yaml | Configuration | Deployed to HA |
| docs/PRODUCTION_READY.md | Detailed guide | Advanced users |
| docs/PIXEL_MOTION_DETECTION_UPGRADE.md | Technical details | Developers |
| docs/TROUBLESHOOTING.md | Problem solving | Users with issues |

---

## Document Reading Order

### For New Users

1. README.md (overview)
2. DEPLOYMENT_GUIDE.md (install)
3. docs/TROUBLESHOOTING.md (if issues)

### For Advanced Users

1. PROJECT_SUMMARY.md (full context)
2. README.md (features & config)
3. docs/PRODUCTION_READY.md (advanced setup)

### For Developers

1. PROJECT_SUMMARY.md (architecture)
2. docs/PIXEL_MOTION_DETECTION_UPGRADE.md (algorithm)
3. CHANGELOG.md (evolution)
4. deployment/camera_detection_pixel.py (code)

---

## Version Information

**Current Version:** 2.0
**Release Date:** 2026-01-01
**Status:** Production Ready ✅

**Production File:** `deployment/camera_detection_pixel.py`
**Algorithm:** Pixel-based motion detection
**Dependencies:** Pillow, numpy, anthropic, requests, ffmpeg

---

## Archive

**Old directory:** `../camera-motion-detector-ARCHIVE-2026-01-01/`

Contains development history, test files, and deprecated versions.
Not needed for production deployment.

---

## Updates

This index was last updated: 2026-01-01

**Maintained by:** Juan C Thomas
