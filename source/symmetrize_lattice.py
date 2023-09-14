import bpy
import math


class T113D_OT_SymmetryizeLattice(bpy.types.Operator):
    """Symmetrizes a lattice"""
    bl_idname = "t113d.symmetrize_lattice"
    bl_label = "Symmetrize lattice"
    bl_description = "Symmetrizes a lattice"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "OBJECT"
            and context.active_object is not None
            and context.active_object.type == "LATTICE"
        )

    def execute(self, context):
        lattice: bpy.types.Lattice = context.active_object.data

        row_num = lattice.points_v * lattice.points_w
        loop_num = math.ceil(lattice.points_u / 2.0)

        for row_index in range(row_num):
            start_index = row_index * lattice.points_u

            for loop_index in range(loop_num):
                ni = start_index + loop_index
                pi = start_index + lattice.points_u - (1 + loop_index)

                np = lattice.points[ni]
                pp = lattice.points[pi]

                if pi == ni:
                    pp.co_deform.x = 0
                else:
                    np.co_deform = pp.co_deform
                    np.co_deform.x = -pp.co_deform.x

        return {'FINISHED'}
