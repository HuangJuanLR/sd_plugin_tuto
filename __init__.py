import os
import sd

from sd.api.sdproperty import SDPropertyCategory
from sd.api.sdbasetypes import float2, float4
from sd.api.sdvaluefloat import SDValueFloat
from sd.api.sdvaluefloat4 import SDValueFloat4

context = sd.getContext()
app = context.getSDApplication()

pkg_mgr = app.getPackageMgr()
ui_mgr = app.getQtForPythonUIMgr()

graph = ui_mgr.getCurrentGraph()

# get all nodes
all_nodes = graph.getNodes()
# get selected nodes
selected_nodes = ui_mgr.getCurrentGraphSelectedNodes()

# for n in selected_nodes:
#     print(n.getDefinition())
#     print(n.getIdentifier())
#     print(n.getDefinition().getId())

selected_props = selected_nodes[0].getProperties(SDPropertyCategory.Output)

for prop in selected_props:
    print(prop.getId())
    print(prop.getType())

uniform_color_node = graph.newNode("sbs::compositing::uniform")
uniform_color_node.newPropertyConnectionFromId("unique_filter_output", selected_nodes[0], "basecolor")
processor_pos = selected_nodes[0].getPosition()
uniform_color_node.setPosition(float2(processor_pos.x - 200, processor_pos.y))


output_color = uniform_color_node.getPropertyFromId("outputcolor", SDPropertyCategory.Input)

uniform_color_node.setPropertyValue(output_color, SDValueFloat4.sNew(float4(0.5, 0.8, 0.2, 1)))

hue = selected_nodes[0].getPropertyFromId("hue", SDPropertyCategory.Input)
sat = selected_nodes[0].getPropertyFromId("saturation", SDPropertyCategory.Input)
light = selected_nodes[0].getPropertyFromId("luminosity", SDPropertyCategory.Input)

selected_nodes[0].setPropertyValue(hue, SDValueFloat.sNew(0.55))
selected_nodes[0].setPropertyValue(sat, SDValueFloat.sNew(0.525))
selected_nodes[0].setPropertyValue(light, SDValueFloat.sNew(0.6))

def initializeSDPlugin():
    print("On SD Plugin Init")

def uninitializeSDPlugin():
    print("On SD Plugin Uninit")
