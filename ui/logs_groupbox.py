from PyQt5.QtWidgets import QGroupBox, QTextEdit, QVBoxLayout

def setup_logs_groupbox(parent):
    parent.log_output = QTextEdit()
    parent.log_output.setReadOnly(True)
    parent.log_output.setPlaceholderText("Logs will appear here...")
    parent.log_output.setFixedHeight(250)

    parent.logs_groupbox = QGroupBox("Logs")
    parent.logs_groupbox.setCheckable(True)
    parent.logs_groupbox.setChecked(True)
    logs_layout = QVBoxLayout()
    logs_layout.addWidget(parent.log_output)
    parent.logs_groupbox.setLayout(logs_layout)
    #parent.logs_groupbox.toggled.connect(parent.toggle_logs_visibility)