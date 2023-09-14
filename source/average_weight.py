import bpy


class T113D_OT_AverageWeight(bpy.types.Operator):
    """Average the weights of the selected vertices"""
    bl_idname = "paint_weight.average"
    bl_label = "Average weight"
    bl_description = "Average the weights of the selected vertices"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        active = context.active_object
        return (
            active is not None
            and active.type == "MESH"
            and len(active.vertex_groups) > 0
            and active.data.use_paint_mask
            or active.data.use_paint_mask_vertex
            and active.vertex_groups.active is not None
        )

    def execute(self, context):

        active = context.active_object
        if active.data.use_paint_mask or active.data.use_paint_mask_vertex:
            group = active.vertex_groups.active

            selected_verts = [v for v in active.data.vertices if v.select]

            weight = 0
            indices = []
            for v in selected_verts:
                try:
                    weight += group.weight(v.index)
                except RuntimeError:
                    weight = weight
                indices.append(v.index)

            weight /= len(selected_verts)

            for v in selected_verts:
                group.add(indices, weight, 'REPLACE')

        return {'FINISHED'}
