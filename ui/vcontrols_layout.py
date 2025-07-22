
from PyQt5.QtWidgets import QLabel, QSpinBox, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy, QFrame
from PyQt5.QtCore import Qt
from constants import GRID_ROWS, GRID_COLS
def setup_vcontrols_layout(parent):
    top_bar_layout = _setup_info_and_grid(parent)
    button_groups_layout = _setup_button_groups(parent)

    divider_line = QFrame()
    divider_line.setFrameShape(QFrame.HLine)
    divider_line.setFrameShadow(QFrame.Sunken)

    controls_vertical_layout = QVBoxLayout()
    controls_vertical_layout.addLayout(top_bar_layout)
    controls_vertical_layout.addWidget(divider_line)
    controls_vertical_layout.addLayout(button_groups_layout)

    parent.setLayout(controls_vertical_layout)

    return controls_vertical_layout

def _setup_info_and_grid(parent):
    # --- Top Controls (Info Label + Row/Col Spinboxes) ---
    parent.info_label = QLabel("Select cells to create virtual buttons.")
    parent.info_label.setWordWrap(False)
    parent.info_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    parent.info_label.setMaximumHeight(30)

    parent.row_spinbox = QSpinBox()
    parent.row_spinbox.setRange(1, 20)
    parent.row_spinbox.setValue(GRID_ROWS)

    parent.col_spinbox = QSpinBox()
    parent.col_spinbox.setRange(1, 20)
    parent.col_spinbox.setValue(GRID_COLS)

    rowcol_layout = QHBoxLayout()
    rowcol_layout.addWidget(QLabel("Rows:"))
    rowcol_layout.addWidget(parent.row_spinbox)
    rowcol_layout.addSpacing(10)
    rowcol_layout.addWidget(QLabel("Cols:"))
    rowcol_layout.addWidget(parent.col_spinbox)

    top_bar_layout = QHBoxLayout()
    top_bar_layout.addWidget(parent.info_label)
    top_bar_layout.addStretch()
    top_bar_layout.addLayout(rowcol_layout)

    return top_bar_layout

def _setup_button_groups(parent):
    # --- Button Groups ---
    parent.btn_create_button = QPushButton("Create")
    parent.btn_delete = QPushButton("Delete")

    parent.btn_map_key = QPushButton("Map")
    parent.btn_unmap_key = QPushButton("Unmap")

    parent.zoom_in_button = QPushButton("+")
    parent.zoom_out_button = QPushButton("-")

    def create_button_group(label_text, buttons):
        group_layout = QVBoxLayout()
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignCenter)
        group_layout.addWidget(label)
        btn_layout = QHBoxLayout()
        for btn in buttons:
            btn_layout.addWidget(btn)
        group_layout.addLayout(btn_layout)
        return group_layout

    virtual_btn_group = create_button_group("Virtual Button", [parent.btn_create_button, parent.btn_delete])
    physical_key_group = create_button_group("Physical Key", [parent.btn_map_key, parent.btn_unmap_key])
    zoom_group = create_button_group("Zoom", [parent.zoom_in_button, parent.zoom_out_button])

    button_groups_layout = QHBoxLayout()
    button_groups_layout.addLayout(virtual_btn_group)
    button_groups_layout.addLayout(physical_key_group)
    button_groups_layout.addLayout(zoom_group)
    button_groups_layout.addStretch()

    return button_groups_layout