import bpy
from pxr import Usd

from . import log


class USDError(BaseException):
    pass


class USDNode(bpy.types.Node):
    """Base class for parsing USD nodes"""

    bl_compatibility = {'HdUSD'}
    tree_idname = 'hdusd.USDTree'

    @classmethod
    def poll(cls, tree: bpy.types.NodeTree):
        return tree.bl_idname == cls.tree_idname

    def __hash__(self):
        return self.as_pointer()

    # COMPUTE FUNCTION
    def compute(self, **kwargs) -> [Usd.Stage, None]:
        """
        Main compute function which should be overridable in child classes.
        It should return Prim object or None.
        """
        pass

    def final_compute(self, socket_out: bpy.types.NodeSocket, group_nodes=(), **kwargs):
        """
        This is the entry point of NodeParser classes.
        This function does some useful preparation before and after calling compute() function.
        """
        log("compute", self, socket_out, group_nodes)
        return self.compute(socket_out=socket_out, group_nodes=group_nodes, **kwargs)

    def _compute_node(self, node, socket_out, group_node=None, **kwargs):
        """
        Exports node with output socket.
        1. Checks if such node was already computeed and returns it.
        2. Searches corresponded NodeParser class and do compute through it
        3. Store group node reference if new one passed
        """
        # Keep reference for group node if present
        if not isinstance(node, USDNode):
            log.warn("Ignoring unsupported node", node)
            return None

        group_nodes = kwargs.pop('group_nodes', None)
        if group_node:
            if group_nodes:
                group_nodes += (group_node,)
            else:
                group_nodes = (group_node,)

        # getting corresponded NodeParser class
        return node.final_compute(socket_out, group_nodes, **kwargs)

    # HELPER FUNCTIONS
    # Child classes should use them to do their compute

    def get_input_link(self, socket_key: [str, int], **kwargs):
        """Returns linked parsed node or None if nothing is linked or not link is not valid"""

        socket_in = self.inputs[socket_key]
        if not socket_in.links:
            return None

        link = socket_in.links[0]
        if not link.is_valid:
            raise USDError("Invalid link found", link, socket_in, self)

        # removing 'socket_out' from kwargs before transferring to _compute_node
        kwargs.pop('socket_out', None)
        return self._compute_node(link.from_node, link.from_socket, **kwargs)


class RenderTaskNode(USDNode):
    """Base class for all hydra render task nodes"""
    tree_idname = 'hdusd.RenderTaskTree'
