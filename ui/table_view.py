from PyQt5.QtWidgets import QTableWidget, QGraphicsProxyWidget, QGraphicsScene, QGraphicsView, QVBoxLayout
from PyQt5.QtGui import QPainter
from constants import GRID_ROWS, GRID_COLS
from components.PannableGraphicsView import PannableGraphicsView
from PyQt5.QtCore import Qt
import logic.table as table_logic

def setup_table_view(parent):
    parent.table = QTableWidget(GRID_ROWS, GRID_COLS)
    parent.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
    parent.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
    parent.table.horizontalHeader().setVisible(False)
    parent.table.verticalHeader().setVisible(False)
    parent.table.setEditTriggers(QTableWidget.NoEditTriggers)
    parent.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    parent.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    table_logic.clear_table_cells(parent)

    # Wrap table in pannable view
    parent.proxy = QGraphicsProxyWidget()
    parent.proxy.setWidget(parent.table)
    parent.scene = QGraphicsScene()
    parent.scene.addItem(parent.proxy)
    parent.view = PannableGraphicsView(parent.scene)
    parent.view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
    parent.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
    parent.view.setResizeAnchor(QGraphicsView.AnchorViewCenter)
    parent.view.centerOn(parent.proxy)