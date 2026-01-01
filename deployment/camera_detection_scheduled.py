"""
Camera Motion Detection AppDaemon App - Scheduled Version
Captures frames periodically, detects motion by comparing frames, analyzes with AI
No dependency on Frigate or other motion detection systems
"""

import appdaemon.plugins.hass.hassapi as hass
import base64
import json
import subprocess
import os
import time
from datetime import datetime
from typing import Dict, Optional

class CameraMotionDetection(hass.Hass):
    """Scheduled AppDaemon app - periodic capture with motion detection"""

    def initialize(self):
        """Initialize the AppDaemon app"""
        self.log("Initializing Camera Motion Detection (Scheduled)")

        # Get configuration
        self.snapshot_url = self.args.get('snapshot_url')
        self.anthropic_api_key = self.args.get('anthropic_api_key')
        self.mqtt_topic_prefix = self.args.get('mqtt_topic_prefix', 'camera_detection')
        self.check_interval = self.args.get('check_interval', 30)  # Check every 30 seconds
        self.motion_threshold = self.args.get('motion_threshold', 50000)  # Bytes difference to trigger

        # Validate configuration
        if not self.anthropic_api_key:
            self.error("anthropic_api_key is required in configuration")
            return

        if not self.snapshot_url:
            self.error("snapshot_url is required")
            return

        # Initialize Anthropic client
        try:
            import anthropic
            self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            self.log("✓ Anthropic client initialized")
        except Exception as e:
            self.error(f"Failed to initialize Anthropic client: {e}")
            return

        # Store last frame for motion detection
        self.last_frame = None
        self.last_analysis_time = 0
        self.cooldown_seconds = 60  # Don't analyze more than once per minute

        # Publish online status
        self.publish_status("online")

        # Start periodic checking
        self.log(f"✓ Checking for motion every {self.check_interval} seconds")
        self.log(f"✓ Motion threshold: {self.motion_threshold} bytes")
        self.log(f"✓ Cooldown: {self.cooldown_seconds} seconds")
        self.run_every(self.check_motion, "now+5", self.check_interval)

        self.log("✓ Camera Motion Detection started")

    def terminate(self):
        """Clean up when app is terminated"""
        self.log("Shutting down Camera Motion Detection")
        self.publish_status("offline")

    def check_motion(self, kwargs):
        """Capture frame and check for motion"""
        self.log("Checking for motion...")
        try:
            # Get current frame
            current_frame = self.capture_frame()
            if not current_frame:
                self.log("Failed to capture frame")
                return

            # If we have a previous frame, compare
            if self.last_frame:
                # Simple motion detection: compare frame sizes (rough but fast)
                size_diff = abs(len(current_frame) - len(self.last_frame))
                self.log(f"Frame difference: {size_diff} bytes (threshold: {self.motion_threshold})")

                if size_diff > self.motion_threshold:
                    # Check cooldown
                    current_time = time.time()
                    if current_time - self.last_analysis_time >= self.cooldown_seconds:
                        self.log(f"Motion detected! Frame size difference: {size_diff} bytes")
                        self.publish_motion()
                        self.analyze_frame(current_frame)
                        self.last_analysis_time = current_time
                    else:
                        remaining = int(self.cooldown_seconds - (current_time - self.last_analysis_time))
                        self.log(f"Motion detected but in cooldown ({remaining}s remaining)")

            # Store current frame for next comparison
            self.last_frame = current_frame
            self.log(f"Frame captured ({len(current_frame)} bytes). {'First frame' if not self.last_frame else 'Waiting for next frame to compare'}")

        except Exception as e:
            self.error(f"Error checking motion: {e}")

    def capture_frame(self) -> Optional[bytes]:
        """Capture frame from RTSP as raw bytes"""
        try:
            tmp_path = f"/config/www/motion_check_{time.time()}.jpg"

            cmd = [
                'ffmpeg',
                '-loglevel', 'error',
                '-rtsp_transport', 'tcp',
                '-i', self.snapshot_url,
                '-frames:v', '1',
                '-q:v', '2',
                '-y',
                tmp_path
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=10)

            if result.returncode == 0 and os.path.exists(tmp_path):
                with open(tmp_path, 'rb') as f:
                    frame_data = f.read()
                os.remove(tmp_path)
                return frame_data
            else:
                self.log("Failed to capture frame")
                return None

        except subprocess.TimeoutExpired:
            self.log("Frame capture timeout")
            return None
        except Exception as e:
            self.log(f"Frame capture error: {e}")
            return None

    def analyze_frame(self, frame_data: bytes):
        """Analyze frame with Claude AI"""
        try:
            # Convert to base64
            image_base64 = base64.b64encode(frame_data).decode('utf-8')

            self.log(f"Analyzing frame ({len(frame_data)} bytes)...")
            result = self.analyze_image(image_base64)

            if result and 'detections' in result:
                for detection in result['detections']:
                    self.handle_detection(detection)
            else:
                self.log("No detections in frame")

        except Exception as e:
            self.error(f"Analysis error: {e}")

    def analyze_image(self, image_base64: str) -> Dict:
        """Analyze image with Anthropic Claude Vision"""
        try:
            prompt = """
            Analyze this camera image for activity.

            FOCUS AREAS ONLY:
            1. The driveway area (to the right side of the image)
            2. Vehicles parked directly in front of the property
            3. People or animals walking directly in front of the property

            IGNORE:
            - Activity on the street/road
            - Activity on neighboring properties
            - Background movement (trees, clouds, etc.)
            - Static decorations (Christmas lights, deer, etc.)

            For each detected object in the focus areas, specify:
            - type: "person", "vehicle", or "animal"
            - location: "driveway", "in_front", or "walking_by"
            - description: Brief description
            - confidence: 0.0-1.0

            Return ONLY a JSON object:
            {
                "detections": [
                    {
                        "type": "person|vehicle|animal",
                        "location": "driveway|in_front|walking_by",
                        "description": "brief description",
                        "confidence": 0.0-1.0
                    }
                ],
                "summary": "brief summary"
            }
            """

            # Call Anthropic API
            response = self.anthropic_client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }]
            )

            # Parse response
            response_text = response.content[0].text
            result = self.extract_json(response_text)

            if result:
                self.log(f"Analysis complete: {result.get('summary', 'No summary')}")

            return result

        except Exception as e:
            self.error(f"Analysis error: {e}")
            return {}

    def extract_json(self, text: str) -> Dict:
        """Extract JSON from LLM response"""
        try:
            return json.loads(text)
        except:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except:
                    pass
        return {}

    def handle_detection(self, detection: Dict):
        """Handle a detection and publish to MQTT"""
        detection_type = detection.get('type', 'unknown')
        location = detection.get('location', 'unknown')
        description = detection.get('description', '').lower()
        confidence = detection.get('confidence', 0.0)

        # Filter out static decorations
        ignore_keywords = ['decoration', 'deer', 'stag', 'reindeer', 'illuminated', 'christmas', 'holiday', 'light']
        if any(keyword in description for keyword in ignore_keywords):
            self.log(f"Ignoring static decoration: {description}")
            return

        self.log(f"Detected [{location.upper()}]: {detection_type} - {description}")

        # Publish detection
        self.publish_detection(detection_type, location, description, confidence)

        # Fire Home Assistant event
        self.fire_event("camera_detection",
            type=detection_type,
            location=location,
            description=description,
            confidence=confidence
        )

    def publish_detection(self, detection_type: str, location: str, description: str, confidence: float):
        """Publish detection to MQTT"""
        payload = {
            "type": detection_type,
            "location": location,
            "description": description,
            "confidence": round(confidence, 2),
            "timestamp": datetime.now().isoformat()
        }

        # Publish to specific topic
        topic = f"{self.mqtt_topic_prefix}/{location}/{detection_type}"
        self.call_service("mqtt/publish", topic=topic, payload=json.dumps(payload), qos=1, retain=False)

        # Publish to last_detection
        self.call_service("mqtt/publish",
                         topic=f"{self.mqtt_topic_prefix}/last_detection",
                         payload=json.dumps(payload),
                         qos=1,
                         retain=True)

    def publish_motion(self):
        """Publish motion event to MQTT"""
        self.call_service("mqtt/publish",
                         topic=f"{self.mqtt_topic_prefix}/motion/binary",
                         payload="ON",
                         qos=1,
                         retain=False)

    def publish_status(self, status: str):
        """Publish online/offline status"""
        self.call_service("mqtt/publish",
                         topic=f"{self.mqtt_topic_prefix}/status",
                         payload=status,
                         qos=1,
                         retain=True)
