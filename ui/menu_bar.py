# ui/menu_bar.py

from PyQt5.QtWidgets import QMenuBar, QAction

def setup_menu_bar(parent):
    """
    Builds the menu bar on the given QMainWindow (parent),
    attaches all QAction objects to `parent` for later wiring.
    """
    menubar = QMenuBar(parent)
    parent.setMenuBar(menubar)

    # ─── File Menu ──────────────────────────────────────────
    file_menu = menubar.addMenu("File")
    parent.action_save    = QAction("Save", parent)
    parent.action_save_as = QAction("Save As...", parent)
    parent.action_open    = QAction("Open", parent)
    parent.action_new     = QAction("New Layout", parent)

    file_menu.addAction(parent.action_save)
    file_menu.addAction(parent.action_save_as)
    file_menu.addAction(parent.action_open)
    file_menu.addAction(parent.action_new)

    # ─── Macros Menu ───────────────────────────────────────
    macros_menu = menubar.addMenu("Macros")
    parent.action_macro_mgr = QAction("Open Macro Manager", parent)
    macros_menu.addAction(parent.action_macro_mgr)

    # ─── Run Menu ──────────────────────────────────────────
    run_menu = menubar.addMenu("Run")
    parent.action_run_bg = QAction("Run Layout in Background", parent)
    parent.choose_startup_action = QAction("Choose Startup Layout", parent)

    run_menu.addAction(parent.action_run_bg)
    run_menu.addAction(parent.choose_startup_action)

    # ─── Advanced Menu ─────────────────────────────────────
    adv_menu = menubar.addMenu("Advanced")
    parent.device_filtering_action = QAction("Enable Device Filtering", parent)
    parent.device_filtering_action.setCheckable(True)
    adv_menu.addAction(parent.device_filtering_action)
