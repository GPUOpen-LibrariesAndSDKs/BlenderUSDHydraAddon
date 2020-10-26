import bpy
from .base_node import USDNode
from . import log


class HydraRenderNode(USDNode):
    """Render to Hydra"""
    
    bl_idname = 'usd.HydraRenderNode'
    bl_label = "Render USD via Hydra"

    render_type: bpy.props.EnumProperty(
        name='Type',
        items=(('FINAL', 'Final', 'Final Render'),
            ('VIEWPORT', 'Viewport', 'Viewport Render'),
            ('BOTH', 'Both', 'All Renders'),
        ),
        default='BOTH'
    )
    
    def init(self, context):
        self.inputs.new(name="Input", type="NodeSocketShader")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'render_type')

    def draw_buttons_ext(self, context, layout):
        pass
        # self.draw_buttons(context, layout)

    def compute(self, **kwargs):
        stage = self.get_input_link('Input', **kwargs)
        return stage

    def update(self):
        print(self)
        context = bpy.context
        depsgraph = context.evaluated_depsgraph_get()

        stage = self.get_input_link('Input',
            depsgraph=depsgraph)

        scene_collection = context.scene.collection
        usd_collection = scene_collection.children.get('USD')
        if not usd_collection:
            usd_collection = bpy.data.collections.get('USD', bpy.data.collections.new('USD'))
            scene_collection.children.link(usd_collection)

        data_objects = bpy.data.objects

        obj_names = set(obj.name for obj in usd_collection.objects)

        if stage:
            prim_names = set(str(prim.GetPath()) for prim in stage.Traverse())
        else:
            prim_names = set()

        obj_to_remove = obj_names - prim_names
        for name in obj_to_remove:
            data_objects.remove(data_objects[name])

        obj_to_add = prim_names - obj_names
        for name in obj_to_add:
            obj = data_objects.new(name, None)
            usd_collection.objects.link(obj)
