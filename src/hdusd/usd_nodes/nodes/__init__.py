import bpy
from nodeitems_utils import (
    NodeCategory,
    NodeItem,
    register_node_categories,
    unregister_node_categories,
)

from hdusd.utils.logging import Log
log = Log(tag="usd.nodes")


# classes to register
from . import (
    read_usd_file, read_blend_data, write_file, merge, print_file, filter, usd_to_blender,
    hydra_render, rpr_render_settings
)


class USDNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'usd.USDTree'

node_categories = [
    USDNodeCategory('USD', 'USD', items=[
        NodeItem('usd.ReadBlendDataNode'),
        NodeItem('usd.FilterNode'),
        NodeItem('usd.HydraRenderNode'),
        NodeItem('usd.MergeNode'),
        NodeItem('usd.PrintFileNode'),
        NodeItem('usd.ReadUsdFileNode'),
        NodeItem('usd.RprRenderSettingsNode'),
        NodeItem('usd.USDToBlenderNode'),
        NodeItem('usd.WriteFileNode')
    ])
]

# nodes to register
register_nodes, unregister_nodes = bpy.utils.register_classes_factory([
    read_blend_data.ReadBlendDataNode,
    read_usd_file.ReadUsdFileNode,
    write_file.WriteFileNode,
    merge.MergeNode,
    print_file.PrintFileNode,
    filter.FilterNode,
    usd_to_blender.USDToBlenderNode,
    hydra_render.HydraRenderNode,
    rpr_render_settings.RprRenderSettingsNode,
])


def register():
    register_nodes()
    register_node_categories("USD_NODES", node_categories)


def unregister():
    unregister_node_categories("USD_NODES")
    unregister_nodes()
