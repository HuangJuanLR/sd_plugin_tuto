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

        # set temp path for input/output directory
        self.graph = ui_mgr.getCurrentGraph()
        if self.graph is not None:
            cur_pkg = self.graph.getPackage()
            temp_path = str(Path(cur_pkg.getFilePath()).resolve().parent)
            self.input_directory = temp_path
            self.output_directory = temp_path

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

        self.resourceFolderLineEdit.setText(self.resource_folder_name)
        self.inputDirectoryLineEdit.setText(self.input_directory)
        self.outputDirectoryLineEdit.setText(self.output_directory)
        self.patternLineEdit.setText(self.pattern)

        self.resourceFolderLineEdit.editingFinished.connect(self.on_resource_folder_changed)
        self.patternLineEdit.textChanged.connect(self.on_pattern_changed)

        self.browseInputButton.clicked.connect(self.browse_input_directory)
        self.browseOutputButton.clicked.connect(self.browse_output_directory)

        self.update_preview()

    def show(self):
        self.window.show()

    def browse_input_directory(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(parent = self.window,
                                                          caption="Select Input Directory",
                                                          dir=self.input_directory)
        if path:
            self.on_input_changed(path)

    def browse_output_directory(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(parent=self.window,
                                                          caption="Select Output Directory",
                                                          dir=self.output_directory)
        if path:
            self.on_output_changed(path)


    def on_input_changed(self, path=None):
        if not path:
            self.input_directory = self.inputDirectoryLineEdit.text()
        else:
            self.input_directory = path
            self.inputDirectoryLineEdit.setText(path)

    def on_output_changed(self, path=None):
        if not path:
            self.output_directory = self.outputDirectoryLineEdit.text()
        else:
            self.output_directory = path
            self.outputDirectoryLineEdit.setText(path)

    def on_resource_folder_changed(self):
        self.resource_folder_name = self.resourceFolderLineEdit.text()

    def on_pattern_changed(self):
        self.pattern =  self.patternLineEdit.text()
        self.update_preview()

    def update_preview(self):
        pattern = self.pattern
        mapping = dict()
        mapping['$(graph)'] = self.graph.getIdentifier()
        mapping['$(identifier)'] = "basecolor"
        for k, v in mapping.items():
            pattern = pattern.replace(k, v)
        preview_text = f"Preview: {pattern}_0"
        self.previewLabel.setText(preview_text)

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
