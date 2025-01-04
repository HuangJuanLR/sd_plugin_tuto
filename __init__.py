import sd
import os
from pathlib import Path
from glob import glob
from shutil import copy2
from PySide6 import QtCore, QtWidgets, QtGui, QtUiTools
from Tools.scripts.fixnotice import process
from sd.api.sdproperty import SDPropertyCategory
from sd.api.sdbasetypes import float2, float4
from sd.api.sdvaluefloat4 import SDValueFloat4
from sd.api.sdvaluefloat import SDValueFloat
from sd.api.sdresourcefolder import SDResourceFolder
from sd.api.sdtypetexture import SDTypeTexture
from sd.api.sdvaluebool import SDValueBool
from sd.api.sdresourcebitmap import SDResourceBitmap
from sd.api.sdresource import EmbedMethod
from sd.api.sdvaluestring import SDValueString
from sd.tools.export import exportSDGraphOutputs

color_io = (
    "normal",
    "position",
    "worldnormal",
    "mads",
    "n",
    "bc",
    "basecolor",
    "albedo"
)
grayscale_io = (
    "ao",
    "curvature",
    "thickness",
    "metalness",
    "metallic",
    "roughness",
    "smoothness",
    "height",
    "ambientocclusion"
)

ui_file = Path(__file__).resolve().parent / "batch_process_dialog.ui"

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
        self.resource_folder_name = "BakedTexture"

        self.ui_file = QtCore.QFile(ui_file)
        self.ui_file.open(QtCore.QFile.ReadOnly)
        loader = QtUiTools.QUiLoader()
        self.window = loader.load(self.ui_file, parent)
        self.ui_file.close()

        # set temp path for input/output directory
        self.graph = ui_mgr.getCurrentGraph()
        if self.graph is not None:
            cur_pkg = self.graph.getPackage()
            temp_path = str(Path(cur_pkg.getFilePath()).resolve().parent)
            self.input_directory = temp_path
            self.output_directory = temp_path

        self.processNameLineEdit = self.window.findChild(
            QtWidgets.QLineEdit, "processorNameLineEdit")
        self.resourceFolderLineEdit = self.window.findChild(
            QtWidgets.QLineEdit, "resourceFolderLineEdit")
        self.inputDirectoryLineEdit = self.window.findChild(
            QtWidgets.QLineEdit, "inputDir")
        self.outputDirectoryLineEdit = self.window.findChild(
            QtWidgets.QLineEdit, "outputDir")
        self.patternLineEdit = self.window.findChild(
            QtWidgets.QLineEdit, "patternLineEdit")
        self.previewLabel = self.window.findChild(
            QtWidgets.QLabel, "previewLabel")

        self.browseInputButton = self.window.findChild(
            QtWidgets.QPushButton, "browseInputButton")
        self.browseOutputButton = self.window.findChild(
            QtWidgets.QPushButton, "browseOutputButton")
        self.chooseButton = self.window.findChild(
            QtWidgets.QPushButton, "chooseProcessorButton")
        self.processButton = self.window.findChild(
            QtWidgets.QPushButton, "processButton")

        self.resourceFolderLineEdit.setText(self.resource_folder_name)
        self.inputDirectoryLineEdit.setText(self.input_directory)
        self.outputDirectoryLineEdit.setText(self.output_directory)
        self.patternLineEdit.setText(self.pattern)

        self.patternLineEdit.textChanged.connect(self.on_pattern_changed)
        self.resourceFolderLineEdit.editingFinished.connect(self.on_resource_folder_changed)
        self.inputDirectoryLineEdit.editingFinished.connect(self.on_input_directory_manual)
        self.outputDirectoryLineEdit.editingFinished.connect(self.on_output_directory_manual)

        self.browseInputButton.clicked.connect(self.browse_input_directory)
        self.browseOutputButton.clicked.connect(self.browse_output_directory)
        self.chooseButton.clicked.connect(self.choose_processor)
        self.processButton.clicked.connect(self.process_loop)

        self.update_preview()

    def show(self):
        self.window.show()

    def on_input_directory_manual(self):
        self.input_directory = self.inputDirectoryLineEdit.text()

    def browse_input_directory(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(parent=self.window,
                                                   caption="Select Input Directory",
                                                   dir=self.input_directory)
        if path:
            self.on_input_changed(path)

    def on_input_changed(self, path=None):
        if not path:
            self.input_directory = self.inputDirectoryLineEdit.text()
        else:
            self.input_directory = path
            self.inputDirectoryLineEdit.setText(path)

    def on_output_directory_manual(self):
        self.output_directory = self.outputDirectoryLineEdit.text()

    def browse_output_directory(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(parent=self.window,
                                                          caption="Select Output Directory",
                                                          dir=self.output_directory)
        if path:
            self.on_output_changed(path)

    def on_output_changed(self, path=None):
        if not path:
            self.output_directory = self.outputDirectoryLineEdit.text()
        else:
            self.output_directory = path
            self.outputDirectoryLineEdit.setText(path)

    def on_resource_folder_changed(self):
        self.resource_folder_name = self.resourceFolderLineEdit.text()

    def on_pattern_changed(self):
        self.pattern = self.patternLineEdit.text()
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

    def choose_processor(self):
        selected_nodes = self.ui_mgr.getCurrentGraphSelectedNodes()
        if selected_nodes.getSize() <= 0: return

        self.processor_node = selected_nodes.getItem(0)
        if self.processor_node is not None:
            processor_label = self.processor_node.getDefinition().getLabel()
            processor_id = self.processor_node.getIdentifier()
            self.processNameLineEdit.setText(processor_label + "_" + processor_id)

    def fetch_baked_textures(self):
        textures = list(Path(self.input_directory).glob('**/*.exr'))
        return textures

    def process_loop(self):
        textures = self.fetch_baked_textures()
        loop_indices = []
        for tex in textures:
            tex_filename = Path(tex.name).stem
            tex_index = int(str.split(tex_filename, "_")[1])
            if tex_index not in loop_indices:
                loop_indices.append(tex_index)

        loop_indices.sort()
        for index in loop_indices:
            self.process(index)

    def process(self, index):
        if self.graph is None or self.processor_node is None: return

        output_nodes = []

        processor_node_input = self.processor_node.getProperties(SDPropertyCategory.Input)
        processor_node_output = self.processor_node.getProperties(SDPropertyCategory.Output)
        processor_pos = self.processor_node.getPosition()

        pkg = self.graph.getPackage()

        resource_folder = self.get_resource_folder(pkg)

        self.solve_previous_resources(resource_folder)

        self.fetch_input(processor_node_input, processor_pos, index, resource_folder)

        self.generate_output(processor_node_output, processor_pos, index)

    def get_resource_folder(self, pkg):
        # get/create resources folder
        resource_folder = None
        all_resources = pkg.getChildrenResources(True)
        for res in all_resources:
            if isinstance(res, SDResourceFolder) and res.getIdentifier() == self.resource_folder_name:
                resource_folder = res
        if resource_folder is None:
            resource_folder = SDResourceFolder.sNew(pkg)
            resource_folder.setIdentifier(self.resource_folder_name)

        return resource_folder

    def solve_previous_resources(self, resource_folder):
        # delete all prev loaded bitmap and nodes
        all_nodes = self.graph.getNodes()
        loaded_resources = resource_folder.getChildren(False)
        loaded_resources_path = []
        for res in loaded_resources:
            loaded_resources_path.append(res.getUrl())

        for node in all_nodes:
            if node.getDefinition().getId() == "sbs::compositing::bitmap":
                pkg_resource_path = node.getPropertyValueFromId("bitmapresourcepath", SDPropertyCategory.Input).get()
                if pkg_resource_path in loaded_resources_path:
                    self.graph.deleteNode(node)

        for res in loaded_resources:
            res.delete()

    def fetch_input(self, processor_node_input, processor_pos, index, resource_folder):
        # get input count for layout of input bitmap nodes
        input_count = 0
        for prop in processor_node_input:
            if isinstance(prop.getType(), SDTypeTexture):
                input_count = input_count + 1

        prop_index = 0
        for prop in processor_node_input:
            if not isinstance(prop.getType(), SDTypeTexture): continue

            prop_id = prop.getId().lower()

            input_bitmap_node = self.graph.newNode("sbs::compositing::bitmap")
            pos_y = processor_pos.y - ((input_count - 1) * 150) / 2 + prop_index * 150
            input_bitmap_node.setPosition(float2(processor_pos.x - 200, pos_y))
            # setting color mode based on processor's prop id
            color_mode_prop = input_bitmap_node.getPropertyFromId('colorswitch', SDPropertyCategory.Input)
            if prop_id in color_io:
                input_bitmap_node.setPropertyValue(color_mode_prop, SDValueBool.sNew(True))
            elif prop_id in grayscale_io:
                input_bitmap_node.setPropertyValue(color_mode_prop, SDValueBool.sNew(False))

            # load bitmap resources
            textures = self.fetch_baked_textures()
            for tex in textures:
                # get texture's name and id
                tex_filename = Path(tex.name).stem
                tex_name = str.split(tex_filename, "_")[0]
                tex_index = int(str.split(tex_filename, "_")[1])

                if tex_name == prop_id and tex_index == index:
                    tex_resource = SDResourceBitmap.sNewFromFile(resource_folder, str(tex), EmbedMethod.Linked)
                    bitmap_resource_property = input_bitmap_node.getPropertyFromId("bitmapresourcepath",
                                                                                   SDPropertyCategory.Input)
                    pkg_res_path = SDValueString.sNew(tex_resource.getUrl())
                    input_bitmap_node.setPropertyValue(bitmap_resource_property, pkg_res_path)

            bitmap_output_prop = input_bitmap_node.getPropertyFromId("unique_filter_output",
                                                                     SDPropertyCategory.Output)
            input_bitmap_node.newPropertyConnection(bitmap_output_prop, self.processor_node, prop)

            prop_index = prop_index + 1

    def generate_output(self, processor_node_output, processor_pos, index):
        output_count = processor_node_output.getSize()
        output_nodes = []
        output_index = 0
        output_ids = []
        for output in processor_node_output:
            # delete prev output nodes
            all_nodes = self.graph.getNodes()
            for node in all_nodes:
                if (node.getDefinition().getId() == "sbs::compositing::output" and
                        node.getPropertyValueFromId("identifier",
                                                    SDPropertyCategory.Annotation).get() == output.getId()):
                    self.graph.deleteNode(node)

            output_node = self.graph.newNode("sbs::compositing::output")
            output_nodes.append(output_node)

            # set new output node's position
            pos_y = processor_pos.y - ((output_count - 1) * 150) / 2 + output_index * 150
            output_node.setPosition(float2(processor_pos.x + 200, pos_y))
            # set output identifier
            output_identifier = output_node.getPropertyFromId("identifier", SDPropertyCategory.Annotation)
            output_node.setPropertyValue(output_identifier, SDValueString.sNew(output.getId()))
            # connect to processor node
            output_node_input = output_node.getPropertyFromId("inputNodeOutput", SDPropertyCategory.Input)
            self.processor_node.newPropertyConnection(output, output_node, output_node_input)

            output_ids.append(output.getId())
            output_index = output_index + 1

        if len(output_nodes) > 0:
            for node in output_nodes:
                self.graph.setOutputNode(node, True)

            exportSDGraphOutputs(self.graph, self.output_directory, "png")

            # map pattern to name
            mapping = dict()
            mapping['$(graph)'] = self.graph.getIdentifier()

            tex_files = glob(os.path.join(self.output_directory, "*.png"))
            tex_files.sort(key=os.path.getmtime, reverse=True)
            latest_text_files = tex_files[:output_index]
            output_ids.reverse()
            for i, tex in enumerate(latest_text_files):
                mapping["$(identifier)"] = output_ids[i]
                pattern = self.pattern
                for k, v in mapping.items():
                    pattern = pattern.replace(k, v)
                target_file = os.path.join(self.output_directory, f"{pattern}_{index}.png")
                copy2(tex, target_file)
                os.remove(tex)

context = sd.getContext()
app = context.getSDApplication()

pkg_mgr = app.getPackageMgr()
ui_mgr = app.getQtForPythonUIMgr()

# get loaded packages
all_pkgs = pkg_mgr.getPackages()

graph = ui_mgr.getCurrentGraph()

main_window = ui_mgr.getMainWindow()

win = Window(ui_file, main_window, pkg_mgr, ui_mgr)

menu_id = "HuangJuanLr" + "#BatchProcess"

def show_plugin():
    # print("test action")
    win.show()

menu_bar = main_window.menuBar()

menu = ui_mgr.findMenuFromObjectName(menu_id)
if menu is not None:
    ui_mgr.deleteMenu(menu_id)

menu = QtWidgets.QMenu("HuangJuanLr", menu_bar)
menu.setObjectName(menu_id)
menu_bar.addMenu(menu)
action = QtGui.QAction("Batch Process", menu)
action.triggered.connect(show_plugin)
menu.addAction(action)

def initializeSDPlugin():
    pass

def uninitializeSDPlugin():
    pass