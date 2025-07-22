from PyQt5.QtWidgets import (
    QMainWindow, QHBoxLayout, QWidget, QVBoxLayout, QSystemTrayIcon,
    QMenu, QAction, QApplication, QMessageBox
)
from PyQt5.QtNetwork import QLocalServer
from PyQt5.QtCore import pyqtSignal, Qt, QTimer, QEvent,  QDataStream, QDateTime
from PyQt5.QtGui import QIcon
from constants import CELL_SIZE, UNIQUE_APP_ID

from ui.menu_bar import setup_menu_bar
from ui.vcontrols_layout import setup_vcontrols_layout
from ui.table_view import setup_table_view
from ui.logs_groupbox import setup_logs_groupbox
from ui.right_panel import setup_right_panel

import logic.macros as macro_logic
import logic.table as table_logic
import logic.control as control_logic
import logic.live as live_logic
import logic.menu as menu_logic
import logic.data as data_logic


class MainWindow(QMainWindow):
    highlight_signal = pyqtSignal(object, bool)  # vb, highlight_on_or_off
    key_mapped_signal = pyqtSignal()

    def __init__(self, tray_mode=False):
        super().__init__()
        self.current_layout_file = None
        self.zoom_factor = 1.0
        self.base_cell_size = CELL_SIZE
        self.setWindowTitle("Numpad Layout Designer & Mapper")
        self.resize(1000, 1000)
        self.setMinimumSize(1000, 1000)
        self.setMaximumSize(1500, 1500)
        self.virtual_buttons = []
        self.macros = macro_logic.load_macros(self)
        self.selected_vb = None
        self.tray_mode = tray_mode
        self.tray_icon = None
        self.settings = data_logic.load_settings(self)

        self._init_ui()
        self._init_logic()

    def _init_ui(self):

        # menu bar setup
        setup_menu_bar(self)

        # table view setup
        setup_table_view(self)

        # logs box setup
        setup_logs_groupbox(self)

        # Layout Assembly
        main_layout = QHBoxLayout()

        # Table view layout (controls + table)
        table_layout = QVBoxLayout()
        table_layout.addLayout(setup_vcontrols_layout(self)) # adding vertical controls layout
        table_layout.addWidget(self.view) # adding table view (pannable graphics)
        table_layout.setAlignment(Qt.AlignTop)

        left_panel = QVBoxLayout()
        left_panel.addLayout(table_layout)
        left_panel.addWidget(self.logs_groupbox) # adding logs groupbox
        left_panel.setStretch(0, 7)
        left_panel.setStretch(1, 3)

        right_panel = setup_right_panel(self)

        main_layout.addLayout(left_panel, stretch=5)
        main_layout.addLayout(right_panel, stretch=2)

        container = QWidget()
        container.setLayout(main_layout)
        container.setContentsMargins(10, 10, 10, 10)
        self.setCentralWidget(container)

        
        

    def _init_logic(self):
        
        self.row_spinbox.valueChanged.connect(lambda: table_logic.update_grid_size(self))
        self.col_spinbox.valueChanged.connect(lambda: table_logic.update_grid_size(self))

        self.btn_create_button.clicked.connect(lambda: control_logic.create_virtual_button(self))
        self.btn_delete.clicked.connect(lambda: control_logic.delete_virtual_button(self))
        self.btn_map_key.clicked.connect(lambda: control_logic.map_physical_key(self))
        self.btn_unmap_key.clicked.connect(lambda: control_logic.unmap_physical_key(self))
        self.zoom_in_button.clicked.connect(lambda: control_logic.adjust_zoom(self, 1.1))
        self.zoom_out_button.clicked.connect(lambda: control_logic.adjust_zoom(self, 0.9))

        self.logs_groupbox.toggled.connect(lambda checked: control_logic.toggle_logs_visibility(self, checked))

        self.action_save.triggered.connect(lambda: menu_logic.save_layout(self))
        self.action_save_as.triggered.connect(lambda: menu_logic.save_layout_as(self))
        self.action_open.triggered.connect(lambda: menu_logic.open_layout(self))
        self.action_new.triggered.connect(lambda: menu_logic.create_new_layout(self))

        self.action_macro_mgr.triggered.connect(lambda: menu_logic.open_macro_manager(self))

        self.action_run_bg.triggered.connect(lambda: menu_logic.run_current_layout_in_background(self))
        self.choose_startup_action.triggered.connect(lambda: menu_logic.choose_startup_layout(self))

        self.device_filtering_action.triggered.connect(lambda checked: menu_logic.on_device_filtering_toggled(self, checked))

        if self.tray_mode:
            self.init_tray_icon()

        QTimer.singleShot(0, lambda: self.view.centerOn(self.proxy))
        menu_logic.update_startup_menu_checkmark(self)
        table_logic.update_grid_size(self)




    def log_message(self, message):
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.log_output.append(f"[{timestamp}] {message}")



    def init_tray_icon(self):
        if self.tray_icon:  # Prevent multiple icons
            return

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("./assets/BigLogo.png"))

        tray_menu = QMenu()

        restore_action = QAction("Restore", self)
        restore_action.triggered.connect(self.show_normal_window)
        tray_menu.addAction(restore_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    def start_instance_listener(self):
        self.local_server = QLocalServer(self)
        print("🟢 Starting instance listener... local server started")
        if not self.local_server.listen(UNIQUE_APP_ID):
            print(f"⚠️ Server error: {self.local_server.errorString()}")
            QLocalServer.removeServer(UNIQUE_APP_ID)
            if not self.local_server.listen(UNIQUE_APP_ID):
                print("❌ Failed to listen again after removing server.")
                return

        print("🟢 Instance listener running...")
        self.local_server.newConnection.connect(self.handle_new_instance_connection)

    def handle_new_instance_connection(self):
        socket = self.local_server.nextPendingConnection()
        if socket and socket.waitForReadyRead(1000):
            stream = QDataStream(socket)
            message = stream.readQString()
            print(f"📥 Received message: {message}")
            if message == "ACTIVATE":
                self.show_normal_window()

    def show_normal_window(self):
        if self.isMinimized():
            self.setWindowState(self.windowState() & ~Qt.WindowMinimized)  # Restore window if minimized
        self.show()
        self.raise_()
        
        # Only activate window if it doesn't have focus already
        if not self.isActiveWindow():
            self.activateWindow()


    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isHidden() or self.isMinimized():
                self.show_normal_window()

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                QTimer.singleShot(0, self.hide_to_tray)

    def hide_to_tray(self):
        if not self.tray_icon:
            self.init_tray_icon()
        self.hide()

    def closeEvent(self, event):
        msg = QMessageBox(self)
        msg.setWindowTitle("Exit Numcro Pad?")
        msg.setText("Do you want to close the app completely or minimize it to the system tray?")
        msg.setIcon(QMessageBox.Question)

        minimize_button = msg.addButton("Minimize to tray", QMessageBox.AcceptRole)
        close_button = msg.addButton("Close completely", QMessageBox.RejectRole)

        msg.exec_()

        if msg.clickedButton() == minimize_button:
            if not self.tray_icon:
                self.init_tray_icon()

            self.hide()
            self.tray_icon.showMessage(
                "Numcro Pad",
                "Application minimized to tray.",
                QSystemTrayIcon.Information,
                3000
            )
            event.ignore()

        elif msg.clickedButton() == close_button:
            if self.tray_icon:
                self.tray_icon.hide()
            event.accept()
        else:
            event.ignore()