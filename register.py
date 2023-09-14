import bpy

from .source import (
    average_weight,
    remove_empty_weights,
    remove_unused_weights,
    symmetrize_action,
    symmetrize_lattice,
    bake_cyclic_action,
    menus
)

classes = [
    average_weight.T113D_OT_AverageWeight,
    remove_empty_weights.T113D_OT_RemoveEmptyWeights,
    remove_unused_weights.T113D_OT_RemoveUnusedWeights,
    symmetrize_lattice.T113D_OT_SymmetryizeLattice,
    bake_cyclic_action.T113D_OT_BakeCyclicAction,
    symmetrize_action.T113D_OT_SymmetrizeAction
]


def register_classes():
    """Loading API classes into blender"""

    for cls in classes:
        bpy.utils.register_class(cls)

    menus.attach_menus()


def unregister_classes():
    """Unloading classes loaded in register(), as well as various cleanup"""

    menus.detach_menus()

    for cls in classes:
        bpy.utils.unregister_class(cls)
