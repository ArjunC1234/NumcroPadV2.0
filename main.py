from ui.main_window import MainWindow
import sys
import os
import json

from PyQt5.QtWidgets import QApplication
from PyQt5.QtNetwork import QLocalSocket, QLocalServer
from PyQt5.QtCore import QDataStream
from constants import SETTINGS_FILE, UNIQUE_APP_ID


def is_another_instance_running():
    socket = QLocalSocket()
    socket.connectToServer(UNIQUE_APP_ID)

    if socket.waitForConnected(500):
        try:
            stream = QDataStream(socket)
            stream.writeQString("ACTIVATE")
            socket.flush()
            socket.waitForBytesWritten(1000)
            print("📤 Sent ACTIVATE message to running instance.")
        except Exception as e:
            print("Pipe send failed:", e)
        finally:
            socket.disconnectFromServer()
        return True

    # Could not connect — maybe the server was killed and socket is stale
    QLocalServer.removeServer(UNIQUE_APP_ID)
    return False



if __name__ == "__main__":
    if is_another_instance_running():
        print("Another instance of Numcro Pad is already running.")
        sys.exit(0)

    app = QApplication(sys.argv)
    tray_mode = "--tray" in sys.argv
    main_window = MainWindow(tray_mode=tray_mode)

    # 🧠 IMPORTANT: Start server early
    main_window.start_instance_listener()

    # ✅ Load startup layout if exists
    layout_path = None
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
            layout_path = data.get("startup_layout")
        except Exception as e:
            print(f"[Startup Load] Failed to parse settings.json: {e}")

    if layout_path and os.path.exists(layout_path):
        try:
            main_window.load_layout_from_file(layout_path)

            if tray_mode:
                main_window.run_current_layout_in_background()
            else:
                main_window.show()
        except Exception as e:
            print(f"[Startup Layout] Failed to load layout: {e}")
            main_window.show()
    else:
        main_window.show()

    sys.exit(app.exec_())
