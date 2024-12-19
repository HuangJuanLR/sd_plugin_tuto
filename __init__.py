import os
import time
import sd

context = sd.getContext()
app = context.getSDApplication()

pkg_mgr = app.getPackageMgr()
ui_mgr = app.getQtForPythonUIMgr()

# get loaded packages
all_pkgs = pkg_mgr.getPackages()

for pkg in all_pkgs:
    print(pkg.getFilePath())

# load packages
# sbsar_dir = os.path.join("U:/SD/plugins/plugin_tuto/resources", "corrupted_stone_floor.sbsar")
graph = ui_mgr.getCurrentGraph()
cur_pkg = graph.getPackage()
cur_pkg_path = os.path.dirname(cur_pkg.getFilePath())
sbsar_dir = os.path.join(cur_pkg_path, "resources", "corrupted_stone_floor.sbsar")
pkg = pkg_mgr.loadUserPackage(sbsar_dir)

# get resource
res = pkg.findResourceFromUrl("corrupted_stone_floor")
graph.newInstanceNode(res)

# unload package
pkg_mgr.unloadUserPackage(pkg)

# create blur node
blur_node = graph.newNode('sbs::compositing::blur')


def initializeSDPlugin():
    print("On SD Plugin Init")

def uninitializeSDPlugin():
    print("On SD Plugin Uninit")
