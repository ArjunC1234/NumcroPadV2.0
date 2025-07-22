import subprocess
import threading
import json
import os

class RawInputReceiver:
    def __init__(self, exe_path):
        self.exe_path = exe_path
        self.process = None
        self.listener_thread = None
        self._running = False

        self.on_input = None  # Callback to handle full JSON object from C# (device + key info)
    def linkOnInput(self, func):
        self.on_input = func
    def start(self):
        if self._running:
            return

        if not os.path.exists(self.exe_path):
            raise FileNotFoundError(f"Raw input handler not found: {self.exe_path}")

        self.process = subprocess.Popen(
            [self.exe_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1
        )

        self._running = True
        self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listener_thread.start()

    def stop(self):
        if not self._running:
            return

        self._running = False
        if self.process:
            try:
                self.process.kill()
                self.process.wait()
            except Exception:
                pass
        self.process = None

    def _listen_loop(self):
        while self._running and self.process and self.process.stdout:
            line = self.process.stdout.readline()
            if not line:
                break

            try:
                event = json.loads(line.strip())
                if self.on_input:
                    self.on_input(event)
            except json.JSONDecodeError:
                continue

        self._running = False

    def is_running(self):
        return self._running
