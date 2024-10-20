import os
import subprocess
import uvicorn


# Set up headless display for Pygame
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["DISPLAY"] = ":99"

# Check if Xvfb :99 is already running
lock_file = "/tmp/.X99-lock"
if not os.path.exists(lock_file):
    # Start the Xvfb display
    try:
        xvfb = subprocess.Popen(['Xvfb', os.environ["DISPLAY"]])
        print("Xvfb started successfully.")
    except Exception as e:
        print(f"Failed to start Xvfb: {e}")
        exit(1)


# should be imported after the Xvfb setup; pygame.init may be called by dependencies
from dweam.server import app


# Run the FastAPI app with Uvicorn
try:
    uvicorn.run(app, host="0.0.0.0", port=8080)
finally:
    # Terminate Xvfb when done
    xvfb.terminate()
