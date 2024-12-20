import os
import sd
from PySide6 import QtCore, QtWidgets, QtGui, QtUiTools
from sd.api.sdproperty import SDPropertyCategory
from sd.api.sdbasetypes import float2, float4
from sd.api.sdvaluefloat import SDValueFloat
from sd.api.sdvaluefloat4 import SDValueFloat4

from lib import Window

context = sd.getContext()
app = context.getSDApplication()

pkg_mgr = app.getPackageMgr()
ui_mgr = app.getQtForPythonUIMgr()

graph = ui_mgr.getCurrentGraph()
main_window = ui_mgr.getMainWindow()

win = Window.Window(main_window, pkg_mgr, ui_mgr)

def show_plugin():
    win.show()

menu_id = "HuangJuanLr" + "#BatchProcess"

menu = ui_mgr.findMenuFromObjectName(menu_id)
if menu is not None:
    ui_mgr.deleteMenu(menu_id)

menu_bar = main_window.menuBar()
menu = QtWidgets.QMenu("HuangJuanLr", menu_bar)
menu.setObjectName(menu_id)
menu_bar.addMenu(menu)
action = QtGui.QAction("Batch Process", menu)
action.triggered.connect(show_plugin)
menu.addAction(action)

def initializeSDPlugin():
    print("On SD Plugin Init")

def uninitializeSDPlugin():
    print("On SD Plugin Uninit")
