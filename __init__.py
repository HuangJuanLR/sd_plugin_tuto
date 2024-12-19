import os
import sd

from PySide6 import QtCore, QtWidgets, QtGui, QtUiTools

from sd.api.sdproperty import SDPropertyCategory
from sd.api.sdbasetypes import float2, float4
from sd.api.sdvaluefloat import SDValueFloat
from sd.api.sdvaluefloat4 import SDValueFloat4

context = sd.getContext()
app = context.getSDApplication()

pkg_mgr = app.getPackageMgr()
ui_mgr = app.getQtForPythonUIMgr()

graph = ui_mgr.getCurrentGraph()
main_window = ui_mgr.getMainWindow()

# #creating dialog
dialog = QtWidgets.QDialog(parent=main_window)
# dialog.show()

# creating menu
def test_action():
    # print("Test Action")
    dialog.show()

menu_id = "HuangJuanLr" + "#TestMenuItem"

menu = ui_mgr.findMenuFromObjectName(menu_id)
if menu is not None:
    ui_mgr.deleteMenu(menu_id)

menu_bar = main_window.menuBar()
menu = QtWidgets.QMenu("HuangJuanLr", menu_bar)
menu.setObjectName(menu_id)
menu_bar.addMenu(menu)
action = QtGui.QAction("Test", menu)
action.triggered.connect(test_action)
menu.addAction(action)

def initializeSDPlugin():
    print("On SD Plugin Init")

def uninitializeSDPlugin():
    print("On SD Plugin Uninit")
