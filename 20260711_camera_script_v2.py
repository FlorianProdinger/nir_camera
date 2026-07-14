#!/usr/bin/env python3
"""
Camera preview with robust fallbacks:
 - Prefer QtGlPreview (if available)
 - Fallback to SimplePreview (if available)
 - Otherwise display frames in an OpenCV window (requires python3-opencv)
 - Prints debug info about what's available and why a window might not open
"""
import sys
import signal
import time
from picamera2 import Picamera2

# Discover preview backends
SimplePreview = None
QtGlPreview = None
try:
    from picamera2.preview import SimplePreview, QtGlPreview  # try both
except Exception:
    try:
        from picamera2.preview import SimplePreview
    except Exception:
        SimplePreview = None
    try:
        from picamera2.preview import QtGlPreview
    except Exception:
        QtGlPreview = None

# Try to import OpenCV for fallback display
try:
    import cv2
except Exception:
    cv2 = None

def debug_env():
    print("Debug info:")
    print(f"  SimplePreview available: {SimplePreview is not None}")
    print(f"  QtGlPreview available:   {QtGlPreview is not None}")
    print(f"  OpenCV available:        {cv2 is not None}")
    # DISPLAY env helps indicate whether an X server is present:
    import os
    print(f"  DISPLAY env:             {os.environ.get('DISPLAY')!r}")

def main():
    debug_env()

    try:
        picam = Picamera2()
    except Exception as e:
        print(f"Failed to create Picamera2 instance: {e}")
        sys.exit(1)

    # Try a typical preview configuration (720p)
    try:
        config = picam.create_preview_configuration(main={"size": (1280, 720)})
        picam.configure(config)
    except Exception as e:
        print(f"Warning: failed to configure preview explicitly: {e}")
        # Not fatal — some setups work without explicit config

    preview = None
    if QtGlPreview is not None:
        try:
            preview = QtGlPreview()
            print("Using QtGlPreview")
        except Exception as e:
            print(f"Failed to initialize QtGlPreview: {e}")
            preview = None

    if preview is None and SimplePreview is not None:
        try:
            preview = SimplePreview()
            print("Using SimplePreview")
        except Exception as e:
            print(f"Failed to initialize SimplePreview: {e}")
            preview = None

    running = True

    def shutdown(signum=None, frame=None):
        nonlocal running
        print("\nShutting down camera...")
        running = False
        try:
            picam.stop()
        except Exception:
            pass
        try:
            picam.close()
        except Exception:
            pass
        # if using OpenCV, destroy windows
        if cv2 is not None:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # If we have a preview implementation, use it
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

    # If preview was provided, the preview object should open a window.
    if preview is not None:
        print("Camera preview started via Picamera2 preview backend. Close the window or press Ctrl+C to exit.")
        # Block until signal
        try:
            signal.pause()
        except AttributeError:
            while running:
                time.sleep(1)
        shutdown()

    # Otherwise fallback to OpenCV window, if available
    if cv2 is None:
        print("No preview backend and OpenCV is not installed. Install OpenCV (e.g., sudo apt-get install python3-opencv) or run this on the Pi desktop.")
        shutdown()

    window_name = "Picamera2 (press q to quit)"
    try:
        while running:
            arr = picam.capture_array()
            # Picamera2 uses RGB ordering; OpenCV expects BGR
            try:
                bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
            except Exception:
                # If conversion fails, display raw array
                bgr = arr
            cv2.imshow(window_name, bgr)
            key = cv2.waitKey(1)
            if key != -1:
                # ord('q') to quit
                if (key & 0xFF) == ord('q'):
                    break
            # small sleep to lower CPU
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        shutdown()

if __name__ == "__main__":
    main()
