import sys
from picamera2 import picamera2
from picamera2.preview import QtPreview
from PyQt5.QtWidgets import QApplication

def main():
    # 1. Initialize the QApplication for the GUI preview window
    app = QApplication(sys.argv)
    
    # 2. Create the Picamera2 instance
    picam = Picamera2()
    
    # 3. Configure the camera for a standard 720p live preview
    # (Camera Module 3 NoIR handles low-light naturally, no special config needed)
    picam.configure(picam.create_preview_configuration(main={"size": (1280, 720)}))
    
    # 4. Set up the Qt preview window
    preview = QtPreview()
    picam.start_preview(preview)
    
    print("Camera live view started. Close the window or press Ctrl+C to exit.")
    
    # 5. Start the camera sensor and hand control over to the Qt event loop
    picam.start()
    
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("\nClosing camera...")
    finally:
        # Clean up resources properly on exit
        picam.stop()
        picam.close()

if __name__ == "__main__":
    main()
