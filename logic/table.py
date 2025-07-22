from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QGraphicsProxyWidget
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QColor, QBrush
from constants import CELL_SIZE

import logic.macros as macro_logic

def clear_table_cells(parent):
    for r in range(parent.table.rowCount()):
        for c in range(parent.table.columnCount()):
            parent.table.setSpan(r, c, 1, 1)
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignCenter)
            parent.table.setItem(r, c, item)

def update_grid_size(parent):
    rows = parent.row_spinbox.value()
    cols = parent.col_spinbox.value()

    parent.table.setRowCount(rows)
    parent.table.setColumnCount(cols)
    clear_table_cells(parent)

    size = CELL_SIZE
    for r in range(rows):
        parent.table.setRowHeight(r, size)
    for c in range(cols):
        parent.table.setColumnWidth(c, size)

    parent.virtual_buttons = [
        vb for vb in parent.virtual_buttons
        if vb.start_row + vb.row_span <= rows and vb.start_col + vb.col_span <= cols
    ]

    update_table(parent)
    update_table_size(parent)
    resize_table_to_contents(parent)
    parent.proxy.updateGeometry()
    parent.view.setSceneRect(parent.scene.itemsBoundingRect())

def highlight_selected_virtual_button(parent, selected_vb):
    for vb in parent.virtual_buttons:
        item = parent.table.item(vb.start_row, vb.start_col)
        if item:
            if vb == selected_vb:
                item.setBackground(QColor("#add8e6"))  # light blue = selected
            elif vb.mapped_key:
                item.setBackground(QColor("#fffacd"))  # light yellow = mapped
            else:
                item.setBackground(QColor("white"))  # unselected and unmapped

    parent.table.viewport().update()

def update_table_size(parent):
    parent.table.setFixedSize(
        parent.table.columnCount() * parent.base_cell_size,
        parent.table.rowCount() * parent.base_cell_size
    )
    parent.view.setSceneRect(parent.scene.itemsBoundingRect())

def handle_cell_click(parent, row, col):
    found = False
    for vb in parent.virtual_buttons:
        if vb.contains(row, col):
            parent.selected_vb = vb
            highlight_selected_virtual_button(parent, vb)
            macro_logic.update_macro_info(parent, vb)

            # Safely read turbo settings from the VirtualButton instance
            turbo_enabled = getattr(vb, 'turbo_enabled', False)
            turbo_delay = getattr(vb, 'turbo_delay_ms', 100)

            parent.turbo_checkbox.blockSignals(True)
            parent.turbo_checkbox.setChecked(turbo_enabled)
            parent.turbo_checkbox.blockSignals(False)

            parent.turbo_delay_spinbox.blockSignals(True)
            parent.turbo_delay_spinbox.setValue(turbo_delay)
            parent.turbo_delay_spinbox.blockSignals(False)

            found = True
            break

    if not found:
        parent.selected_vb = None
        parent.key_name_label.setText("Key: None")
        parent.macro_combo.setCurrentIndex(0)

        parent.turbo_checkbox.blockSignals(True)
        parent.turbo_checkbox.setChecked(False)
        parent.turbo_checkbox.blockSignals(False)

        parent.turbo_delay_spinbox.blockSignals(True)
        parent.turbo_delay_spinbox.setValue(100)
        parent.turbo_delay_spinbox.blockSignals(False)

        highlight_selected_virtual_button(parent, None)

def resize_table_to_contents(parent):
    width = sum(parent.table.columnWidth(c) for c in range(parent.table.columnCount()))
    height = sum(parent.table.rowHeight(r) for r in range(parent.table.rowCount()))
    parent.table.setFixedSize(width, height)

@pyqtSlot(object, bool)
def set_button_highlight(parent, vb, highlight_on):
    item = parent.table.item(vb.start_row, vb.start_col)
    if not item:
        return
    if highlight_on:
        item.setBackground(QBrush(QColor("#ffff00")))  # bright yellow
    else:
        if vb.mapped_key:
            item.setBackground(QBrush(QColor("#fffacd")))  # light yellow
        else:
            item.setBackground(QBrush(Qt.white))
    parent.table.viewport().update()

def unmap_deleted_macros(parent, deleted_ids):
    for vb in parent.virtual_buttons:
        if vb.assigned_macro_id in deleted_ids:
            vb.assigned_macro_id = None
            vb.assigned_macro_name = None
    update_table(parent)

def update_table(parent):
    clear_table_cells(parent)
    for vb in parent.virtual_buttons:
        parent.table.setSpan(vb.start_row, vb.start_col, vb.row_span, vb.col_span)
        item = QTableWidgetItem(vb.name)
        item.setTextAlignment(Qt.AlignCenter)
        tip = f"Mapped: {vb.mapped_key or 'None'}\nMacro: {vb.assigned_macro_name or 'None'}"
        item.setToolTip(tip)

        if vb.mapped_key:
            item.setBackground(QColor("#fffacd"))
        else:
            item.setBackground(QColor("white"))
        parent.table.setItem(vb.start_row, vb.start_col, item)