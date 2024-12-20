from PySide6 import QtCore, QtWidgets, QtGui, QtUiTools

class Window(QtWidgets.QDialog):
    def __init__(self, parent, pkg_mgr, ui_mgr):
        super(Window, self).__init__(parent)

        self.ui_mgr = ui_mgr
        self.pkg_mgr = pkg_mgr

        self.window = QtWidgets.QDialog(parent=parent)

    def show(self):
        self.window.show()
