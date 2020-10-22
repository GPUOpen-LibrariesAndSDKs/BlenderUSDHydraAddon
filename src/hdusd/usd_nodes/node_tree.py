import bpy
from .nodes.hydra_render import HydraRenderNode

class USDTree(bpy.types.ShaderNodeTree):
    """
    Holds hierarchy of data and composition of USD for rendering
    The basic (default) graph should be simply
    
    Read Blender Data (scene) ---> Hydra Render 

    When nodes or tree is updated, the node computation is re-run
    """
    bl_label = "USD"
    bl_icon = "NODETREE"
    bl_idname = "usd.USDTree"

    def get_output_node(self, render_type='BOTH'):
        return next((node for node in self.nodes if isinstance(node, HydraRenderNode) and \
                     node.render_type == render_type), None)


class RenderTaskTree(bpy.types.ShaderNodeTree):
    """
    Hydra Tasks needed for rendering.  
    The outputs of this will be AOV's passed to blender.
    The default tree is simply Hydra Render -> outputs, but other options
    could be denoising, bloom filters, tone mapping, etc
    """
    bl_label = "Hydra Render"
    bl_icon = "NODETREE"
    bl_idname = "usd.RenderTaskTree"


def get_usd_nodetree():
    ''' return first USD nodetree found '''
    return next((ng for ng in bpy.data.node_groups if isinstance(ng, USDTree)), None)


def register():
    bpy.utils.register_class(USDTree)
    # bpy.utils.register_class(RenderTaskTree)


def unregister():
    bpy.utils.unregister_class(USDTree)
    # bpy.utils.unregister_class(RenderTaskTree)
