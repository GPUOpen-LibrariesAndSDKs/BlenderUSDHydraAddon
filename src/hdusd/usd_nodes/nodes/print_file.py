from .base_node import USDNode


class PrintFileNode(USDNode):
    """Writes stream out to console output"""
    bl_idname = 'usd.PrintFileNode'
    bl_label = "Print USD to stdout"

    def init(self, context):
        self.inputs.new(name="Input", type="NodeSocketShader")
        self.outputs.new(name="output", type="NodeSocketShader")

    def compute(self, **kwargs):
        stage = self.get_input_link('Input', **kwargs)
        if stage:
            print(stage.ExportToString())

        return stage
