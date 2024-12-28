import os
import sd
from pathlib import Path
from glob import glob
from shutil import copy2
from PySide6 import QtCore, QtWidgets, QtGui, QtUiTools
from sd.api.sdproperty import SDPropertyCategory
from sd.api.sdbasetypes import float2, float4
from sd.api.sdvaluefloat import SDValueFloat
from sd.api.sdvaluefloat4 import SDValueFloat4
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
        self.chooseButton.clicked.connect(self.choose_processor)
        self.processButton.clicked.connect(self.process_loop)

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

    def choose_processor(self):
        selected_nodes = self.ui_mgr.getCurrentGraphSelectedNodes()
        if selected_nodes.getSize() <= 0: return

        self.processor_node = selected_nodes.getItem(0)
        if self.processor_node is not None:
            processor_label = self.processor_node.getDefinition().getLabel()
            processor_id = self.processor_node.getIdentifier()
            self.processorNameLineEdit.setText(processor_label + "_" + processor_id)

    def fetch_baked_textures(self):
        textures = list(Path(self.input_directory).glob('**/*.exr'))
        return textures

    def process_loop(self):
        self.process(1)


    def process(self, index):
        if self.graph is None or self.processor_node is None: return

        output_nodes = []

        processor_node_properties = self.processor_node.getProperties(SDPropertyCategory.Input)
        processor_node_output = self.processor_node.getProperties(SDPropertyCategory.Output)
        processor_pos = self.processor_node.getPosition()

        # get/create resources folder
        resource_folder = None
        pkg = self.ui_mgr.getCurrentGraph().getPackage()
        all_resource = self.ui_mgr.getCurrentGraph().getPackage().getChildrenResources(True)
        for res in all_resource:
            if isinstance(res, SDResourceFolder) and res.getIdentifier() == self.resource_folder_name:
                resource_folder = res
        if resource_folder is None:

            resource_folder = SDResourceFolder.sNew(pkg)
            resource_folder.setIdentifier(self.resource_folder_name)

        # delete all previous loaded bitmap resources if any
        # delete any bitmap node link to these resources
        # pass False as not recursive to get only direct children
        all_nodes = self.graph.getNodes()
        loaded_resources = resource_folder.getChildren(False)
        loaded_resources_path = []
        for res in loaded_resources:
            loaded_resources_path.append(res.getUrl())

        for node in all_nodes:
            if node.getDefinition().getId() == "sbs::compositing::bitmap":
                pkg_resource_path = node.getPropertyValueFromId("bitmapresourcepath",
                                                                SDPropertyCategory.Input).get()
                if pkg_resource_path in loaded_resources_path:
                    self.graph.deleteNode(node)

        # loop again maybe not the right approach
        # just for avoiding logging resource lost warning
        for res in loaded_resources:
            print(f"Deleting: {res.getIdentifier()}")
            res.delete()

        # loop and count, prop_count is for layout of input bitmap nodes
        prop_count = 0
        for prop in processor_node_properties:
            prop_id = prop.getId()
            if not prop_id.startswith("$") and isinstance(prop.getType(), SDTypeTexture):
                prop_count = prop_count + 1

        # loop through processor node's input port
        prop_index = 0
        for prop in processor_node_properties:
            prop_id = prop.getId().lower()
            # if prop.isConnectable():
            if isinstance(prop.getType(), SDTypeTexture):
                # create new bitmap nodes and store
                input_bitmap_node = self.graph.newNode("sbs::compositing::bitmap")
                # setting bitmap node position
                pos_y = processor_pos.y - ((prop_count - 1) * 150) / 2 + prop_index * 150
                input_bitmap_node.setPosition(float2(processor_pos.x - 200, pos_y))
                # setting color mode based on processor's prop id
                color_mode_prop = input_bitmap_node.getPropertyFromId('colorswitch', SDPropertyCategory.Input)
                if prop_id in color_io:
                    input_bitmap_node.setPropertyValue(color_mode_prop, SDValueBool.sNew(True))
                elif prop_id in grayscale_io:
                    input_bitmap_node.setPropertyValue(color_mode_prop, SDValueBool.sNew(False))

                # load bitmap resources from selected directory
                textures = self.fetch_baked_textures()
                for tex in textures:
                    # get texture's name and index
                    tex_filename = Path(tex.name).stem
                    tex_name = str.split(tex_filename, "_")[0]
                    tex_index = int(str.split(tex_filename, "_")[1])
                    # load texture as resource

                    if tex_name == prop_id and tex_index == index:
                        # tex_resource = pkg.findResourceFromUrl(str(tex))
                        tex_resource = SDResourceBitmap.sNewFromFile(resource_folder, str(tex),
                                                                     EmbedMethod.Linked)
                        # set bitmap node PKG Resource Path
                        bitmap_resource_property = input_bitmap_node.getPropertyFromId("bitmapresourcepath",
                                                                                       SDPropertyCategory.Input)
                        pkg_res_path = SDValueString.sNew(tex_resource.getUrl())
                        input_bitmap_node.setPropertyValue(bitmap_resource_property, pkg_res_path)

                # connect bitmap node to processor node
                bitmap_output_prop = input_bitmap_node.getPropertyFromId("unique_filter_output",
                                                                         SDPropertyCategory.Output)
                input_bitmap_node.newPropertyConnection(bitmap_output_prop, self.processor_node, prop)

                prop_index = prop_index + 1

        output_count = processor_node_output.getSize()

        output_index = 0
        output_ids = []
        for output in processor_node_output:
            # delete previous output nodes with the same identifier
            all_nodes = self.graph.getNodes()
            for node in all_nodes:
                if (node.getDefinition().getId() == "sbs::compositing::output" and
                        node.getPropertyValueFromId("identifier",
                                                    SDPropertyCategory.Annotation).get() == output.getId()):
                    self.graph.deleteNode(node)

            # create and store output node
            output_node = self.graph.newNode("sbs::compositing::output")
            output_nodes.append(output_node)
            # set new output node's position
            pos_y = processor_pos.y - ((output_count - 1) * 150) / 2 + output_index * 150
            output_node.setPosition(float2(processor_pos.x + 200, pos_y))
            # set output identifier
            output_identifier = output_node.getPropertyFromId("identifier", SDPropertyCategory.Annotation)
            output_node.setPropertyValue(output_identifier, SDValueString.sNew(output.getId()))
            # connect processor node to output node
            output_node_input = output_node.getPropertyFromId("inputNodeOutput", SDPropertyCategory.Input)
            self.processor_node.newPropertyConnection(output, output_node, output_node_input)
            # store output identifiers for later renaming files
            output_ids.append(output.getId())

            output_index = output_index + 1

        if len(output_nodes) > 0:
            for node in output_nodes:
                self.graph.setOutputNode(node, True)

            exportSDGraphOutputs(self.graph, self.output_directory, "png")

            # map pattern to name
            mapping = dict()
            mapping['$(graph)'] = self.graph.getIdentifier()

            # batch copy to new file and rename
            # get latest output textures according to output number
            tex_files = glob((os.path.join(self.output_directory, "*.png")))
            tex_files.sort(key=os.path.getmtime, reverse=True)
            latest_tex_files = tex_files[:output_index]
            # rename latest created textures and save it as a copy
            output_ids.reverse()
            for i, tex in enumerate(latest_tex_files):
                mapping['$(identifier)'] = output_ids[i]
                pattern = self.pattern
                for k, v in mapping.items():
                    pattern = pattern.replace(k, v)
                target_file = os.path.join(self.output_directory, f"{pattern}_{index}.png")
                copy2(tex, target_file)
                # then delete origin file
                os.remove(tex)


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
