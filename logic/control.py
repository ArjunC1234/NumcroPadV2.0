import threading
from PyQt5.QtWidgets import QMessageBox, QInputDialog
from components.VirtualButton import VirtualButton  # Adjust the import path if needed
import logic.table as table_logic
import logic.live as live_logic

def adjust_zoom(parent, factor):
    parent.zoom_factor *= factor
    parent.view.scale(factor, factor)

def unmap_physical_key(parent):
    if parent.selected_vb:
        parent.selected_vb.mapped_key = None
        parent.key_name_label.setText("Key: None")
        table_logic.update_table(parent)

def toggle_logs_visibility(parent, checked):
    parent.log_output.setVisible(checked)
    parent.logs_groupbox.setFlat(not checked)  # optional: make it visually minimal when hidden
    if checked:
        parent.logs_groupbox.setMaximumHeight(16777215)  # Default max
    else:
        parent.logs_groupbox.setMaximumHeight(30)  # Only show title bar
    parent.logs_groupbox.updateGeometry()

def create_virtual_button(parent):
    selected = parent.table.selectedItems()
    if not selected:
        return

    rows = sorted(set(i.row() for i in selected))
    cols = sorted(set(i.column() for i in selected))
    expected = (rows[-1] - rows[0] + 1) * (cols[-1] - cols[0] + 1)
    
    if len(selected) != expected:
        QMessageBox.warning(parent, "Error", "Select a solid rectangle.")
        return

    # Check for overlap with any existing virtual button
    for vb in parent.virtual_buttons:
        for r in range(rows[0], rows[-1] + 1):
            for c in range(cols[0], cols[-1] + 1):
                if vb.contains(r, c):
                    QMessageBox.warning(parent, "Error", "Selection overlaps an existing virtual button.")
                    return

    name, ok = QInputDialog.getText(parent, "Button Name", "Enter button name:")
    if not ok or not name.strip():
        return

    btn = VirtualButton(name.strip(), rows[0], cols[0], len(rows), len(cols))
    parent.virtual_buttons.append(btn)
    table_logic.update_table(parent)

def map_physical_key(parent):
    sel = parent.table.selectedRanges()
    if not sel:
        return

    row = sel[0].topRow()
    col = sel[0].leftColumn()

    for vb in parent.virtual_buttons:
        if vb.start_row == row and vb.start_col == col:
            parent.mapping_key_process = True
            parent.mapping_target = vb  # So on_raw_input knows what to map
            parent.info_label.setText("Press any key to map it to this virtual button...")
            return

def delete_virtual_button(parent):
    sel = parent.table.selectedRanges()
    if not sel:
        return
    row = sel[0].topRow()
    col = sel[0].leftColumn()
    for vb in parent.virtual_buttons:
        if row == vb.start_row and col == vb.start_col:
            parent.virtual_buttons.remove(vb)
            table_logic.update_table(parent)
            break