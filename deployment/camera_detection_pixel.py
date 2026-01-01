"""
Camera Motion Detection AppDaemon App - Pixel Difference Version
Uses actual image pixel comparison instead of file size
Much more accurate for detecting people walking into frame
"""

import appdaemon.plugins.hass.hassapi as hass
import base64
import json
import subprocess
import os
import time
import numpy as np
from datetime import datetime
from typing import Dict, Optional
from PIL import Image
from io import BytesIO

class CameraMotionDetection(hass.Hass):
    """Pixel-based motion detection with AI analysis"""

    def initialize(self):
        """Initialize the AppDaemon app"""
        self.log("Initializing Camera Motion Detection (Pixel-based)")

        # Get configuration
        self.snapshot_url = self.args.get('snapshot_url')
        self.anthropic_api_key = self.args.get('anthropic_api_key')
        self.mqtt_topic_prefix = self.args.get('mqtt_topic_prefix', 'camera_detection')
        self.check_interval = self.args.get('check_interval', 30)

        # Pixel-based thresholds
        self.motion_pixel_threshold = self.args.get('motion_pixel_threshold', 2000)  # Number of changed pixels
        self.pixel_difference_threshold = self.args.get('pixel_difference_threshold', 30)  # Brightness change per pixel
        self.cooldown_seconds = self.args.get('cooldown_seconds', 30)

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
        self.last_frame_array = None
        self.last_analysis_time = 0

        # Publish online status
        self.publish_status("online")

        # Start periodic checking
        self.log(f"✓ Checking for motion every {self.check_interval} seconds")
        self.log(f"✓ Motion threshold: {self.motion_pixel_threshold} changed pixels")
        self.log(f"✓ Pixel difference: {self.pixel_difference_threshold} brightness change")
        self.log(f"✓ Cooldown: {self.cooldown_seconds} seconds")
        self.run_every(self.check_motion, "now+5", self.check_interval)

        self.log("✓ Camera Motion Detection started (pixel-based)")

    def terminate(self):
        """Clean up when app is terminated"""
        self.log("Shutting down Camera Motion Detection")
        self.publish_status("offline")

    def capture_frame(self) -> Optional[bytes]:
        """Capture frame from RTSP as raw bytes"""
        try:
            tmp_path = f"/config/www/motion_check_{int(time.time())}.jpg"

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
                return None

        except Exception as e:
            self.error(f"Error capturing frame: {e}")
            return None

    def image_to_grayscale_array(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """Convert JPEG bytes to grayscale numpy array for comparison"""
        try:
            img = Image.open(BytesIO(image_bytes))
            # Resize to smaller size for faster processing (320x240 is plenty)
            img = img.resize((320, 240), Image.Resampling.LANCZOS)
            # Convert to grayscale
            img = img.convert('L')
            # Convert to numpy array
            return np.array(img)
        except Exception as e:
            self.error(f"Error converting image: {e}")
            return None

    def detect_motion(self, current_array: np.ndarray, previous_array: np.ndarray) -> tuple:
        """Compare two frames and detect motion using pixel differences"""
        try:
            # Calculate absolute difference between frames
            diff = np.abs(current_array.astype(int) - previous_array.astype(int))

            # Count pixels that changed more than threshold
            changed_pixels = np.sum(diff > self.pixel_difference_threshold)

            # Calculate average difference for changed pixels
            if changed_pixels > 0:
                avg_change = np.mean(diff[diff > self.pixel_difference_threshold])
            else:
                avg_change = 0

            return changed_pixels, avg_change

        except Exception as e:
            self.error(f"Error detecting motion: {e}")
            return 0, 0

    def check_motion(self, kwargs):
        """Capture frame and check for motion"""
        self.log("Checking for motion...")
        try:
            # Get current frame
            current_frame_bytes = self.capture_frame()
            if not current_frame_bytes:
                self.log("Failed to capture frame")
                return

            # Convert to grayscale array
            current_frame_array = self.image_to_grayscale_array(current_frame_bytes)
            if current_frame_array is None:
                self.log("Failed to convert frame to array")
                return

            # If we have a previous frame, compare
            if self.last_frame_array is not None:
                # Detect motion using pixel comparison
                changed_pixels, avg_change = self.detect_motion(current_frame_array, self.last_frame_array)

                self.log(f"Pixels changed: {changed_pixels} (threshold: {self.motion_pixel_threshold}), avg change: {avg_change:.1f}")

                if changed_pixels > self.motion_pixel_threshold:
                    # Check cooldown
                    current_time = time.time()
                    if current_time - self.last_analysis_time >= self.cooldown_seconds:
                        self.log(f"🎯 Motion detected! {changed_pixels} pixels changed (avg: {avg_change:.1f})")
                        self.publish_motion()
                        self.analyze_frame(current_frame_bytes)
                        self.last_analysis_time = current_time
                    else:
                        remaining = int(self.cooldown_seconds - (current_time - self.last_analysis_time))
                        self.log(f"Motion detected but in cooldown ({remaining}s remaining)")
                else:
                    self.log("No significant motion detected")

            else:
                self.log("First frame captured, establishing baseline")

            # Store current frame for next comparison
            self.last_frame_array = current_frame_array

        except Exception as e:
            self.error(f"Error checking motion: {e}")
            import traceback
            self.error(traceback.format_exc())

    def analyze_frame(self, frame_bytes: bytes):
        """Analyze frame with Anthropic AI"""
        self.log(f"Analyzing frame ({len(frame_bytes)} bytes)...")
        try:
            # Convert to base64
            image_base64 = base64.b64encode(frame_bytes).decode('utf-8')

            # Analyze with AI
            result = self.analyze_image(image_base64)

            if result and 'detections' in result:
                self.log(f"Analysis complete: {result.get('summary', 'No summary')}")

                # Process detections
                for detection in result['detections']:
                    obj_type = detection.get('type', 'unknown')
                    location = detection.get('location', 'unknown')
                    description = detection.get('description', '')
                    confidence = detection.get('confidence', 0)

                    self.log(f"Detected [{location.upper()}]: {obj_type} - {description}")

                    # Publish to MQTT
                    self.publish_detection(detection)
            else:
                self.log("No detections in analysis result")

        except Exception as e:
            self.error(f"Error analyzing frame: {e}")
            import traceback
            self.error(traceback.format_exc())

    def analyze_image(self, image_base64: str) -> Dict:
        """Analyze image with Anthropic Claude Vision"""
        try:
            prompt = """
            Analyze this outdoor security camera image for activity.

            FOCUS ON THESE AREAS ONLY:
            1. The driveway area (typically to the right side of frame)
            2. Vehicles parked directly in front of the property
            3. People or animals in front of the property or on the driveway

            DETECT AND REPORT:
            - People walking, standing, or approaching
            - Vehicles (cars, trucks, bikes, delivery trucks)
            - Animals (pets, wildlife)

            IGNORE:
            - Activity on the street/road (not on property)
            - Activity on neighboring properties
            - Background movement (trees, clouds, flags)
            - Static decorations (Christmas lights, deer statues, lawn ornaments)

            For each detected object IN THE FOCUS AREAS, specify:
            - type: "person", "vehicle", or "animal"
            - location: "driveway", "in_front", or "walking_by"
            - description: Brief description of what they're doing/where they are
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

            If nothing is detected in the focus areas, return empty detections array.
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
            text_content = response.content[0].text

            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', text_content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result
            else:
                self.error(f"Could not parse JSON from response: {text_content}")
                return {"detections": [], "summary": text_content}

        except Exception as e:
            self.error(f"Error calling Anthropic API: {e}")
            import traceback
            self.error(traceback.format_exc())
            return {"detections": [], "summary": f"Error: {str(e)}"}

    def publish_motion(self):
        """Publish motion event to MQTT"""
        try:
            topic = f"{self.mqtt_topic_prefix}/motion/binary"
            self.call_service("mqtt/publish",
                topic=topic,
                payload="ON",
                retain=False
            )
        except Exception as e:
            self.error(f"Error publishing motion: {e}")

    def publish_detection(self, detection: Dict):
        """Publish detection to MQTT"""
        try:
            # Publish to specific topic
            location = detection.get('location', 'unknown')
            obj_type = detection.get('type', 'unknown')
            topic = f"{self.mqtt_topic_prefix}/{location}/{obj_type}"

            self.call_service("mqtt/publish",
                topic=topic,
                payload=json.dumps(detection),
                retain=False
            )

            # Also publish to last_detection topic
            topic = f"{self.mqtt_topic_prefix}/last_detection"
            payload = {
                "type": obj_type,
                "location": location,
                "description": detection.get('description', ''),
                "confidence": detection.get('confidence', 0),
                "timestamp": datetime.now().isoformat()
            }

            self.call_service("mqtt/publish",
                topic=topic,
                payload=json.dumps(payload),
                retain=True
            )

        except Exception as e:
            self.error(f"Error publishing detection: {e}")

    def publish_status(self, status: str):
        """Publish online/offline status"""
        try:
            topic = f"{self.mqtt_topic_prefix}/status"
            self.call_service("mqtt/publish",
                topic=topic,
                payload=status,
                retain=True
            )
        except Exception as e:
            self.error(f"Error publishing status: {e}")
