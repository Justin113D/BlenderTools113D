import bpy


class T113D_OT_RemoveUnusedWeights(bpy.types.Operator):
    bl_idname = "t113d.remove_unused_weights"
    bl_label = "Remove Unused"
    bl_description = (
        "Removes all groups that are not used in the assigned armature/s"
        " (from the object's armature modifier/s)"
    )
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        active = context.active_object
        if active is None or len(active.vertex_groups) == 0:
            return False

        for m in active.modifiers:
            if m.type == 'ARMATURE' and m.object is not None:
                return True

        return False

    def execute(self, context):

        active = context.active_object

        armatures = list()
        for m in active.modifiers:
            if m.type == 'ARMATURE' and m.object is not None:
                armatures.append(m.object.data)

        used = list()
        for a in armatures:
            for b in a.bones:
                if b.use_deform:
                    used.append(b.name)

        groups = list(active.vertex_groups)
        for g in groups:
            if g.name not in used:
                active.vertex_groups.remove(g)

        return {'FINISHED'}
