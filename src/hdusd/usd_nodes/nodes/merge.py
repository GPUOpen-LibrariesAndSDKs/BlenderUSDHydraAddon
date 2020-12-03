import bpy

from .base_node import USDNode
from ... import utils
from . import log


class MergeNode(USDNode):
    """Merges two USD streams"""
    bl_idname = 'usd.MergeNode'
    bl_label = "Merge USD"

    input_names = ()

    def update_inputs_number(self, context):
        if len(self.inputs) < self.inputs_number:
            for i in range(len(self.inputs), self.inputs_number):
                self.safe_op(self.inputs.new, name=f"Input {i + 1}", type="NodeSocketShader")

        elif len(self.inputs) > self.inputs_number:
            for i in range(len(self.inputs), self.inputs_number, -1):
                self.safe_op(self.inputs.remove, self.inputs[i - 1])

    inputs_number: bpy.props.IntProperty(
        name="Inputs",
        min=2, max=10, default=2,
        update=update_inputs_number
    )

    def init(self, context):
        self.update_inputs_number(context)
        super().init(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'inputs_number')

    def compute(self, **kwargs):
        from pxr import Usd, UsdGeom

        ref_stages = []
        for i in range(self.inputs_number):
            stage = self.get_input_link(i, **kwargs)
            if stage:
                ref_stages.append(stage)

        if not ref_stages:
            return None

        if len(ref_stages) == 1:
            return ref_stages[0]

        stage = self.cached_stage.create()
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        merge_prim = stage.DefinePrim(f"/merge")
        stage.SetDefaultPrim(merge_prim)

        for i, ref_stage in enumerate(ref_stages, 1):
            ref = stage.DefinePrim(f"/merge/ref{i}", 'Xform')
            default_prim = ref_stage.GetDefaultPrim()
            override_prim = stage.OverridePrim(str(ref.GetPath()) + '/' + default_prim.GetName())
            override_prim.GetReferences().AddReference(ref_stage.GetRootLayer().realPath)

        return stage
