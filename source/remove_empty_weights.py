import bpy


class T113D_OT_RemoveEmptyWeights(bpy.types.Operator):
    bl_idname = "t113d.remove_empty_groups"
    bl_label = "Remove Empty"
    bl_description = "Removes all groups with no weights"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        active = context.active_object
        return active is not None and len(active.vertex_groups) > 0

    def execute(self, context):
        active = context.active_object
        mesh: bpy.types.Mesh = active.data

        has_weight = [False] * len(active.vertex_groups)
        for v in mesh.vertices:
            for g in v.groups:
                has_weight[g.group] = True

        to_remove = [
            g for g in active.vertex_groups if not has_weight[g.index]]
        for r in to_remove:
            active.vertex_groups.remove(r)

        return {'FINISHED'}
