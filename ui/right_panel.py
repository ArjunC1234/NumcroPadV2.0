from PyQt5.QtWidgets import QGroupBox, QCheckBox, QSpinBox, QHBoxLayout, QVBoxLayout, QLabel, QComboBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


def _setup_turbo_box(parent):
    # Turbo Settings GroupBox
    turbo_groupbox = QGroupBox("Turbo Settings")
    turbo_groupbox.setStyleSheet("""
        QGroupBox {
            background-color: #dcdcdc;
            border: 1px solid #aaa;
            border-radius: 8px;
            padding: 10px;
            margin-top: 5px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 3px;
        }
    """)

    parent.turbo_checkbox = QCheckBox("Enable Turbo")
    parent.turbo_checkbox.setToolTip("Continuously trigger selected macro when enabled")
    #parent.turbo_checkbox.stateChanged.connect(parent.on_turbo_toggled)

    parent.turbo_delay_spinbox = QSpinBox()
    parent.turbo_delay_spinbox.setRange(10, 1000)
    parent.turbo_delay_spinbox.setValue(100)
    parent.turbo_delay_spinbox.setSuffix(" ms")
    parent.turbo_delay_spinbox.setToolTip("Delay between repeated macro triggers")
    #parent.turbo_delay_spinbox.valueChanged.connect(parent.on_turbo_delay_changed)

    turbo_layout = QHBoxLayout()
    turbo_layout.addWidget(parent.turbo_checkbox)
    turbo_layout.addWidget(QLabel("Delay:"))
    turbo_layout.addWidget(parent.turbo_delay_spinbox)
    turbo_layout.addStretch()

    turbo_container_layout = QVBoxLayout()
    turbo_container_layout.addLayout(turbo_layout)
    turbo_groupbox.setLayout(turbo_container_layout)

    return turbo_groupbox

def _setup_macro_box(parent):
    # Macro Assignment GroupBox
    macro_groupbox = QGroupBox("Macro Assignment")
    macro_groupbox.setStyleSheet("""
        QGroupBox {
            background-color: #dcdcdc;
            border: 1px solid #aaa;
            border-radius: 8px;
            padding: 10px;
            margin-top: 5px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 3px;
        }
    """)

    parent.macro_info_label = QLabel("Assign a macro to the selected key")
    parent.key_name_label = QLabel("Key: None")
    parent.device_label = QLabel("Device: None")  # <-- Added device label

    parent.macro_combo = QComboBox()
    parent.macro_combo.addItem("None", None)
    for macro_id, macro_data in parent.macros.items():
        parent.macro_combo.addItem(macro_data['name'], macro_id)
    #parent.macro_combo.currentIndexChanged.connect(parent.assign_macro_to_selected)

    macro_layout = QVBoxLayout()
    macro_layout.addWidget(parent.macro_info_label)
    macro_layout.addWidget(parent.key_name_label)
    macro_layout.addWidget(parent.device_label)  # <-- Inserted into layout
    macro_layout.addWidget(QLabel("Assigned Macro:"))
    macro_layout.addWidget(parent.macro_combo)
    macro_groupbox.setLayout(macro_layout)

    return macro_groupbox

def _setup_logo_box(parent):
    # --- Right side panel ---
    logo_label = QLabel()
    pixmap = QPixmap("./assets/BigLogo.png")
    pixmap = pixmap.scaledToWidth(120, Qt.SmoothTransformation)
    logo_label.setPixmap(pixmap)
    logo_label.setAlignment(Qt.AlignCenter)
    logo_label.setFixedSize(pixmap.size())

    return logo_label

def setup_right_panel(parent):
    right_panel = QVBoxLayout()
    logo_container = QHBoxLayout()
    logo_container.addStretch()
    logo_container.addWidget(_setup_logo_box(parent))
    logo_container.addStretch()
    right_panel.addLayout(logo_container)
    right_panel.addSpacing(10)
    right_panel.addWidget(_setup_macro_box(parent))
    right_panel.addWidget(_setup_turbo_box(parent))
    right_panel.addStretch()

    return right_panel