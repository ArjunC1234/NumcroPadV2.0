import json
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QHBoxLayout,
    QPushButton, QInputDialog, QMessageBox
)
from constants import MACRO_FILE
import uuid
import queue
import threading
import time
from PyQt5.QtCore import pyqtSignal, Qt, pyqtSlot
from PyQt5.QtWidgets import QLabel, QTextEdit, QListWidgetItem
import keyboard



class MacroManager(QDialog):
    macro_recorded = pyqtSignal(str, dict)  # macro_id, macro_data
    macros_deleted = pyqtSignal(set)  # Emit set of deleted macro IDs
    recording_stopped = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.recording_stopped.connect(self.reset_ui)
        self.macro_recorded.connect(self.on_macro_recorded)
        self.recording = False
        self.record_thread = None

        self.setWindowTitle("Macro Manager")
        self.setMinimumSize(400, 300)
        self.macros = self.load_macros()

        layout = QVBoxLayout()

        self.macro_list = QListWidget()
        self.macro_list.itemClicked.connect(self.load_macro)

        btns = QHBoxLayout()
        self.record_btn = QPushButton("Start Recording")
        self.record_btn.clicked.connect(self.toggle_recording)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_macro)
        btns.addWidget(self.record_btn)
        btns.addWidget(self.delete_btn)

        self.recording_label = QLabel("Recording: OFF")
        self.recording_label.setStyleSheet("color: red; font-weight: bold;")

        self.editor = QTextEdit()
        self.original_text = ""  # Keep track of original JSON
        self.editor.textChanged.connect(self.check_if_text_modified)


        self.save_btn = QPushButton("Save Changes")
        self.save_btn.clicked.connect(self.save_macro_changes)

        layout.addWidget(self.macro_list)
        layout.addLayout(btns)
        layout.addWidget(self.recording_label)
        layout.addWidget(self.editor)
        layout.addWidget(self.save_btn)
        self.setLayout(layout)

        self.refresh_macro_list()

    def check_if_text_modified(self):
        current_text = self.editor.toPlainText().strip()
        self.save_btn.setEnabled(current_text != self.original_text.strip())

    def toggle_recording(self):
        if not self.recording:
            # Start recording
            name, ok = QInputDialog.getText(self, "Macro Name", "Enter a name for this macro:")
            if not ok or not name.strip():
                return
            self.macro_name = name.strip()
            self.macro_id = str(uuid.uuid4())
            self.recording = True
            self.record_btn.setText("Stop Recording")
            self.recording_label.setText("Recording: ON")
            self.recording_label.setStyleSheet("color: green; font-weight: bold;")

            # Setup event queue and hook keyboard
            self.event_queue = queue.Queue()
            self.hook = keyboard.hook(self._on_key_event)

            self.record_thread = threading.Thread(target=self.record_loop, daemon=True)
            self.record_thread.start()
        else:
            # Stop recording
            self.recording = False
            keyboard.unhook(self.hook)
            self.record_btn.setEnabled(False)  # Disable until thread stops

    def _on_key_event(self, e):
        self.event_queue.put(e)

    def record_loop(self):
        macro = []
        last_time = time.time()
        key_down_times = {}

        first_event = True  # Track whether this is the first recorded key

        while self.recording or not self.event_queue.empty():
            try:
                e = self.event_queue.get(timeout=0.05)
            except queue.Empty:
                continue

            now = time.time()

            if e.event_type == keyboard.KEY_DOWN:
                delay = 0 if first_event else round(now - last_time, 3)
                last_time = now
                key_down_times[e.name] = now

                if e.name == "esc":
                    self.recording = False
                    break

                macro.append({"key": e.name, "delay": delay, "duration": None})
                first_event = False

            elif e.event_type == keyboard.KEY_UP:
                if e.name in key_down_times:
                    duration = now - key_down_times[e.name]
                    key_down_times.pop(e.name)

                    for event in reversed(macro):
                        if event["key"] == e.name and event["duration"] is None:
                            event["duration"] = round(duration, 3)
                            break

        self.macro_recorded.emit(self.macro_id, {"name": self.macro_name, "steps": macro})
        self.recording_stopped.emit()

    def reset_ui(self):
        self.recording = False
        self.record_btn.setText("Start Recording")
        self.record_btn.setEnabled(True)
        self.recording_label.setText("Recording: OFF")
        self.recording_label.setStyleSheet("color: red; font-weight: bold;")



    @pyqtSlot(str, dict)
    def on_macro_recorded(self, macro_id, data):
        self.macros[macro_id] = data
        self.save_macros()
        self.refresh_macro_list()
        QMessageBox.information(self, "Done", f"Macro '{data['name']}' recorded.")

    def load_macros(self):
        try:
            with open(MACRO_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def refresh_macro_list(self):
        self.macro_list.clear()
        for macro_id, data in self.macros.items():
            item = QListWidgetItem(data['name'])
            item.setData(Qt.UserRole, macro_id)
            self.macro_list.addItem(item)

    def load_macro(self, item):
        macro_id = item.data(Qt.UserRole)
        if macro_id in self.macros:
            pretty_json = json.dumps(self.macros[macro_id], indent=2)
            self.original_text = pretty_json
            self.editor.setPlainText(pretty_json)
            self.save_btn.setEnabled(False)  # Start disabled
            self.macro_list.setCurrentItem(item)

    def delete_macro(self):
        item = self.macro_list.currentItem()
        if not item:
            return
        macro_id = item.data(Qt.UserRole)
        if macro_id in self.macros:
            del self.macros[macro_id]
            self.save_macros()
            self.refresh_macro_list()
            self.macros_deleted.emit({macro_id})  # <- Notify MainWindow
            self.editor.clear()

    def save_macro_changes(self):
        try:
            new_data = json.loads(self.editor.toPlainText())
            selected_items = self.macro_list.selectedItems()
            if not selected_items:
                return
            macro_id = selected_items[0].data(Qt.UserRole)
            if macro_id:
                self.macros[macro_id] = new_data
                self.save_macros()
                self.refresh_macro_list()

                # Update the saved state
                self.original_text = self.editor.toPlainText()
                self.save_btn.setEnabled(False)

        except Exception as e:
            QMessageBox.warning(self, "Invalid JSON", str(e))

    def save_macros(self):
        with open(MACRO_FILE, "w") as f:
            json.dump(self.macros, f, indent=2)