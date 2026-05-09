import subprocess
import threading
import webbrowser
import time
import os

def run_flask():
    subprocess.run(["python", "analyze.py"])

# Start Flask in background thread
t = threading.Thread(target=run_flask, daemon=True)
t.start()

# Wait for Flask to boot
time.sleep(2)

# Open both
webbrowser.open("file:///" + os.path.abspath("index.html"))

print("✅ System running. Close this window to stop.")
input("Press Enter to stop...")