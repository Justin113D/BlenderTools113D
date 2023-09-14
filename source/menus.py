import bpy

from . import (
    average_weight,
    remove_empty_weights,
    remove_unused_weights,
    symmetrize_lattice
)

def drawfunc_weight_paint(self, context):
    self.layout.operator(average_weight.T113D_OT_AverageWeight.bl_idname)

def drawfunc_vertex_groups(self, context):
    self.layout.separator()
    self.layout.operator(remove_empty_weights.T113D_OT_RemoveEmptyWeights.bl_idname)
    self.layout.operator(remove_unused_weights.T113D_OT_RemoveUnusedWeights.bl_idname)

def drawfunc_lattice_context(self, context):
    active = context.active_object
    if bpy.context.object.mode == "OBJECT" and active is not None and active.type == "LATTICE":
        self.layout.operator(symmetrize_lattice.T113D_OT_SymmetryizeLattice.bl_idname)

def attach_menus():
    bpy.types.VIEW3D_MT_object.append(drawfunc_lattice_context)
    bpy.types.VIEW3D_MT_object_context_menu.append(drawfunc_lattice_context)
    bpy.types.VIEW3D_MT_paint_weight.append(drawfunc_weight_paint)
    bpy.types.MESH_MT_vertex_group_context_menu.append(drawfunc_vertex_groups)

def detach_menus():
    bpy.types.VIEW3D_MT_object.remove(drawfunc_lattice_context)
    bpy.types.VIEW3D_MT_object_context_menu.remove(drawfunc_lattice_context)
    bpy.types.VIEW3D_MT_paint_weight.remove(drawfunc_weight_paint)
    bpy.types.MESH_MT_vertex_group_context_menu.remove(drawfunc_vertex_groups)