#!/usr/bin/env python3
"""
Updated Raspberry Pi camera preview script using the Picamera2 API.
- Fixes incorrect imports (uses Picamera2 class name)
- Prefers SimplePreview by default (no PyQt/PyQt5 dependency)
- Falls back to a Qt GL preview if available
- Adds clean signal handling for Ctrl+C and termination

This is intended for Raspberry Pi OS on a Raspberry Pi 4B with an HDMI display attached.

Usage:
  python3 20260711_camera_script_v1.py

Press Ctrl+C or close the preview window to exit cleanly.
"""

import sys
import signal
import time
from picamera2 import Picamera2

# Try to import preview classes. SimplePreview is preferred because it
# doesn't require PyQt. QtGlPreview is optional and used if present.
try:
    from picamera2.preview import SimplePreview, QtGlPreview
except Exception:
    try:
        from picamera2.preview import SimplePreview
        QtGlPreview = None
    except Exception:
        SimplePreview = None
        QtGlPreview = None


def main():
    # Create the camera instance
    try:
        picam = Picamera2()
    except Exception as e:
        print(f"Failed to create Picamera2 instance: {e}")
        sys.exit(1)

    # Configure a 720p preview by default
    try:
        config = picam.create_preview_configuration(main={"size": (1280, 720)})
        picam.configure(config)
    except Exception as e:
        print(f"Failed to configure camera: {e}")
        # Continue — some Picamera2 versions allow start without explicit config

    # Choose a preview implementation
    preview = None
    if 'QtGlPreview' in globals() and QtGlPreview is not None:
        try:
            preview = QtGlPreview()
        except Exception:
            preview = None

    if preview is None and 'SimplePreview' in globals() and SimplePreview is not None:
        try:
            preview = SimplePreview()
        except Exception:
            preview = None

    # If no preview implementation is available, run headless (no window)
    try:
        if preview is not None:
            picam.start_preview(preview)

        picam.start()
    except Exception as e:
        print(f"Failed to start camera/preview: {e}")
        try:
            picam.close()
        except Exception:
            pass
        sys.exit(1)

    print("Camera preview started. Close the preview window or press Ctrl+C to exit.")

    def shutdown(signum=None, frame=None):
        print("\nShutting down camera preview...")
        try:
            picam.stop()
        except Exception:
            pass
        try:
            picam.close()
        except Exception:
            pass
        sys.exit(0)

    # Handle signals for a clean shutdown
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Block while the preview runs. Use signal.pause() where available.
    try:
        signal.pause()
    except AttributeError:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            shutdown()


if __name__ == "__main__":
    main()
