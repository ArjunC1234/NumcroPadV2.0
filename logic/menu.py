from constants import SETTINGS_FILE, CONFIG_FILE, GRID_COLS, GRID_ROWS
import json
import os
from components.StartupLayoutDialog import StartupLayoutDialog
from PyQt5.QtWidgets import QFileDialog, QMessageBox  # <-- Add this line

from components.VirtualButton import VirtualButton
from components.MacroManager import MacroManager

import logic.data as data_logic
import logic.table as table_logic
import logic.macros as macro_logic

def on_device_filtering_toggled(parent, checked):
    parent.device_filtering_enabled = checked
    parent.settings["device_filtering"] = checked
    data_logic.save_settings(parent)
    status = "enabled" if checked else "disabled"
    parent.info_label.setText(f"Device filtering {status}.")

def load_layout_from_file(parent, path):
    try:
        with open(path, "r") as f:
            layout_data = json.load(f)
        load_layout(parent, layout_data, path)  # Assuming this method already exists
        parent.info_label.setText(f"Loaded startup layout: {os.path.basename(path)}")
    except Exception as e:
        parent.log_message(f"Failed to load layout: {e}")

def save_layout(parent):
    if parent.current_layout_file is None:
        save_layout_as(parent)
    else:
        _save_to_file(parent, parent.current_layout_file)

def save_layout_as(parent):
    default_dir = str(CONFIG_FILE.parent) if CONFIG_FILE.exists() else ""

    file_path, _ = QFileDialog.getSaveFileName(
        parent, "Save Layout As", default_dir, "JSON Files (*.json)"
    )
    if file_path:
        if not file_path.lower().endswith(".json"):
            file_path += ".json"
        parent.current_layout_file = file_path
        _save_to_file(parent, file_path)

def create_new_layout(parent):
    confirm = QMessageBox.question(
        parent,
        "New Layout",
        "Are you sure you want to create a new layout? All unsaved changes will be lost.",
        QMessageBox.Yes | QMessageBox.No
    )
    if confirm == QMessageBox.Yes:
        parent.virtual_buttons = []  # Clear the layout
        parent.current_layout_file = None  # Reset the file reference
        table_logic.clear_table_cells(parent)   # Clear the visual grid
        table_logic.update_table(parent)        # Refresh the UI
        parent.info_label.setText("New layout created.")

def _save_to_file(parent, file_path):
    data = {
        "rows": parent.table.rowCount(),
        "cols": parent.table.columnCount(),
        "virtual_buttons": [vb.to_dict() for vb in parent.virtual_buttons]
    }
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        parent.statusBar().showMessage(f"Layout saved to {file_path}", 3000)
    except Exception as e:
        QMessageBox.critical(parent, "Error Saving File", str(e))

def load_layout(parent, layout_data, file_path):
    rows = layout_data.get("rows", GRID_ROWS)
    cols = layout_data.get("cols", GRID_COLS)

    parent.row_spinbox.setValue(rows)
    parent.col_spinbox.setValue(cols)

    parent.virtual_buttons = [VirtualButton.from_dict(d) for d in layout_data.get("virtual_buttons", [])]
    table_logic.update_table()
    table_logic.update_grid_size()
    parent.current_layout_file = file_path
    parent.statusBar().showMessage(f"Loaded layout from {file_path}", 3000)

def open_layout(parent):
    default_dir = str(CONFIG_FILE.parent) if CONFIG_FILE.exists() else ""
    file_path, _ = QFileDialog.getOpenFileName(
        parent, "Open Layout", default_dir, "JSON Files (*.json)"
    )
    if file_path:
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            load_layout(parent, data, file_path)

        except Exception as e:
            QMessageBox.critical(parent, "Error Loading File", str(e))
def run_current_layout_in_background(parent):
    save_layout(parent)

    if not parent.tray_mode:
        parent.tray_mode = True
        parent.init_tray_icon()

    parent.hide()  # Hide the window

def choose_startup_layout(parent):
    dlg = StartupLayoutDialog(parent)
    if dlg.exec_():
        update_startup_menu_checkmark(parent)

def get_startup_layout(parent):
    if SETTINGS_FILE.exists():
        try:
            with SETTINGS_FILE.open("r") as f:
                data = json.load(f)
            print(f"[INFO] Loaded startup layout: {data.get('startup_layout')}")
            return data.get("startup_layout", None)
        except Exception as e:
            print(f"[ERROR] Failed to load startup config: {e}")
    else:
        print("[INFO] No startup config found.")
    return None

def update_startup_menu_checkmark(parent):
    startup_layout = get_startup_layout(parent)
    checked = startup_layout is not None and not startup_layout == ""
    parent.choose_startup_action.setChecked(checked)
    parent.choose_startup_action.setCheckable(True)

def open_macro_manager(parent):
    parent.macro_dialog = MacroManager(parent)
    parent.macro_dialog.macros_deleted.connect(lambda: macro_logic.unmap_deleted_macros(parent))
    parent.macro_dialog.exec_()
    parent.macros = parent.macro_dialog.load_macros()
    macro_logic.refresh_macro_dropdown(parent)