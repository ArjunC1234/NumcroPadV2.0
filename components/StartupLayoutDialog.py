import os
import json
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
    QPushButton, QLabel
)
from constants import SETTINGS_FILE
from pathlib import Path

import winshell
from win32com.client import Dispatch
import sys


class StartupLayoutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Startup Layout")
        self.resize(400, 300)

        self.layouts_folder = os.path.abspath("data/layouts")
        self.startup_config_path = SETTINGS_FILE

        self._init_ui()
        self._populate_layouts()
        self._load_selected_layout()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self.info_label = QLabel("Select a layout to run on startup or choose None:")
        layout.addWidget(self.info_label)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("Select")
        self.btn_cancel = QPushButton("Cancel")
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def _populate_layouts(self):
        self.list_widget.clear()
        self.list_widget.addItem("None")

        if os.path.exists(self.layouts_folder):
            for fname in sorted(os.listdir(self.layouts_folder)):
                if fname.lower().endswith(".json"):
                    self.list_widget.addItem(fname)

    def _load_selected_layout(self):
        selected_name = None
        if os.path.exists(self.startup_config_path):
            try:
                with open(self.startup_config_path, "r") as f:
                    data = json.load(f)
                layout_path = data.get("startup_layout", None)
                if layout_path:
                    selected_name = os.path.basename(layout_path)
            except Exception:
                pass

        # Set selection
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).text() == (selected_name or "None"):
                self.list_widget.setCurrentRow(i)
                return
        self.list_widget.setCurrentRow(0)

    def get_selected_layout(self):
        selected_item = self.list_widget.currentItem()
        if selected_item:
            text = selected_item.text()
            if text == "None":
                return None
            return os.path.join(self.layouts_folder, text)
        return None

    def accept(self):

        def create_startup_shortcut(script_path):
            startup_dir = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
            shortcut_path = os.path.join(startup_dir, "Numcro Pad.lnk")

            # Use pythonw.exe to prevent console window
            pythonw = os.path.join(sys.exec_prefix, "pythonw.exe")

            shell = Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.TargetPath = pythonw

            # Add full path to script and arguments here
            full_script_path = os.path.abspath(script_path)
            shortcut.Arguments = f'"{full_script_path}" --tray'

            shortcut.WorkingDirectory = os.path.dirname(full_script_path)
            shortcut.IconLocation = os.path.abspath("./assets/BigLogo.ico")  # optional
            shortcut.save()

            print("✅ Shortcut created with --tray argument")

        def remove_startup_shortcut(shortcut_name):
            startup_folder = winshell.startup()
            shortcut_path = os.path.join(startup_folder, f"{shortcut_name}.lnk")
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)


        selected_layout = self.get_selected_layout()

        # Save the layout selection
        with open(self.startup_config_path, "w") as f:
            json.dump({"startup_layout": selected_layout}, f)

        # Create/remove startup shortcut
        main_script = os.path.abspath("main.py")  # or m    ain.exe if frozen
        shortcut_name = "Numcro Pad"
        if selected_layout:
            create_startup_shortcut(main_script)
        else:
            remove_startup_shortcut(shortcut_name)

        super().accept()  
