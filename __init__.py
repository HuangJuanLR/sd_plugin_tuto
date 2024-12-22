import os
import sd
from pathlib import Path
from PySide6 import QtCore, QtWidgets, QtGui, QtUiTools
from sd.api.sdproperty import SDPropertyCategory
from sd.api.sdbasetypes import float2, float4
from sd.api.sdvaluefloat import SDValueFloat
from sd.api.sdvaluefloat4 import SDValueFloat4

# from lib import Window

class Window(QtWidgets.QDialog):
    def __init__(self, ui_file, parent, pkg_mgr, ui_mgr):
        super(Window, self).__init__(parent)

        self.ui_mgr = ui_mgr
        self.pkg_mgr = pkg_mgr

        self.processor_node = None
        self.processor_name = None
        self.input_directory = None
        self.output_directory = None
        self.pattern = "$(graph)_$(identifier)"
        self.resource_folder_name = "BakedTextures"

        self.ui_file = QtCore.QFile(ui_file)
        self.ui_file.open(QtCore.QFile.ReadOnly)
        loader = QtUiTools.QUiLoader()
        self.window = loader.load(ui_file, parent)
        self.ui_file.close()

        # link variables to QtWidgets
        self.processorNameLineEdit = self.window.findChild(QtWidgets.QLineEdit, "processorNameLineEdit")
        self.resourceFolderLineEdit = self.window.findChild(QtWidgets.QLineEdit, "resourceFolderLineEdit")
        self.inputDirectoryLineEdit = self.window.findChild(QtWidgets.QLineEdit, "inputDir")
        self.outputDirectoryLineEdit = self.window.findChild(QtWidgets.QLineEdit, "outputDir")
        self.patternLineEdit = self.window.findChild(QtWidgets.QLineEdit, "patternLineEdit")
        self.previewLabel = self.window.findChild(QtWidgets.QLabel, "previewLabel")

        self.browseProcessorUrlButton = self.window.findChild(QtWidgets.QPushButton, "browseProcessorUrlButton")
        self.browseInputButton = self.window.findChild(QtWidgets.QPushButton, "browseInputButton")
        self.browseOutputButton = self.window.findChild(QtWidgets.QPushButton, "browseOutputButton")
        self.chooseButton = self.window.findChild(QtWidgets.QPushButton, "chooseProcessorButton")
        self.processButton = self.window.findChild(QtWidgets.QPushButton, "processButton")

    def show(self):
        self.window.show()

ui_file = Path(__file__).resolve().parent / "batch_process_dialog.ui"

context = sd.getContext()
app = context.getSDApplication()

pkg_mgr = app.getPackageMgr()
ui_mgr = app.getQtForPythonUIMgr()

graph = ui_mgr.getCurrentGraph()
main_window = ui_mgr.getMainWindow()

win = Window(ui_file, main_window, pkg_mgr, ui_mgr)

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
