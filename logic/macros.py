from constants import MACRO_FILE
import json
from PyQt5.QtCore import Qt

import logic.table as table_logic

def load_macros(parent):
    if MACRO_FILE.exists():
        return json.load(open(MACRO_FILE))
    return {}


def on_turbo_toggled(parent, state):
    if not parent.selected_vb:
        return

    enabled = state == Qt.Checked
    parent.selected_vb.turbo_enabled = enabled

    # Enable or disable the delay spinbox accordingly
    parent.turbo_delay_spinbox.setEnabled(enabled)

    # Optionally update UI/log
    parent.log_message(f"Turbo {'enabled' if enabled else 'disabled'} for '{parent.selected_vb.name}'")

def on_turbo_delay_changed(parent, value):
    if not parent.selected_vb:
        return

    parent.selected_vb.turbo_delay_ms = value
    parent.log_message(f"Turbo delay set to {value} ms for '{parent.selected_vb.name}'")

def refresh_macro_dropdown(parent):
    parent.macro_combo.blockSignals(True)
    parent.macro_combo.clear()
    parent.macro_combo.addItem("None", None)
    for macro_id, macro_data in parent.macros.items():
        parent.macro_combo.addItem(macro_data['name'], macro_id)
    parent.macro_combo.blockSignals(False)

    for vb in parent.virtual_buttons:
        if vb.assigned_macro_id in parent.macros:
            vb.assigned_macro_name = parent.macros[vb.assigned_macro_id]["name"]
        else:
            vb.assigned_macro_id = None
            vb.assigned_macro_name = None
    table_logic.update_table(parent)

def assign_macro_to_selected(parent, index):
    if parent.selected_vb:
        macro_id = parent.macro_combo.itemData(index)
        macro_name = parent.macro_combo.currentText() if macro_id is not None else None

        if macro_id is None:
            parent.selected_vb.assigned_macro_id = None
            parent.selected_vb.assigned_macro_name = None
        else:
            parent.selected_vb.assigned_macro_id = macro_id
            parent.selected_vb.assigned_macro_name = macro_name

        item = parent.table.item(parent.selected_vb.start_row, parent.selected_vb.start_col)
        if item:
            tip = f"Mapped: {parent.selected_vb.mapped_key or 'None'}\nMacro: {parent.selected_vb.assigned_macro_name or 'None'}"
            item.setToolTip(tip)

def update_macro_info(parent, vb):
    parent.selected_vb = vb
    parent.key_name_label.setText(f"Key: {vb.mapped_key if vb.mapped_key else 'None'}")

    if vb.assigned_macro_id:
        idx = parent.macro_combo.findData(vb.assigned_macro_id)
        if idx != -1:
            parent.macro_combo.setCurrentIndex(idx)
        else:
            parent.macro_combo.setCurrentIndex(0)
    else:
        parent.macro_combo.setCurrentIndex(0)