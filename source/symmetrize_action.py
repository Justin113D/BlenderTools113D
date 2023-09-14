import typing
import bpy
from bpy.props import BoolProperty, FloatProperty
from bpy.types import Context, Event

MODIFIER_IGNORE_ATTRIBS = {
    '__doc__', '__module__', '__slots__', 'active',
    'bl_rna', 'is_valid', 'rna_type', 'type'}


class ActionSymmetrizer:
    _prev_mode: str
    _armature: bpy.types.Armature
    _pose: bpy.types.Pose
    _action: bpy.types.Action

    _selected_bones: set[bpy.types.PoseBone]
    _hidden_bones: set[bpy.types.PoseBone]
    _hidden_layers: set[int]

    _selected_curves: set[bpy.types.FCurve]
    _hidden_curves: set[bpy.types.FCurve]

    _selected_keyframes: set[bpy.types.Keyframe]
    _selected_left_handles: set[bpy.types.Keyframe]
    _selected_right_handles: set[bpy.types.Keyframe]

    _bone_curves: dict[str, set[bpy.types.FCurve]]
    _sym_name_pairs: dict[str, str]
    _sym_curve_pairs: dict[bpy.types.FCurve, bpy.types.FCurve]

    def __init__(self):
        self._prev_mode = 'OBJECT'
        self._armature = None
        self._pose = None
        self._action = None

        self._selected_bones = set()
        self._hidden_bones = set()
        self._hidden_layers = set()

        self._selected_curves = set()
        self._hidden_curves = set()

        self._selected_keyframes = set()
        self._selected_left_handles = set()
        self._selected_right_handles = set()

        self._bone_curves = {}
        self._sym_name_pairs = {}
        self._sym_curve_pairs = {}

    @staticmethod
    def _get_symmetrized_name(name: str):
        lowercase = name.lower()
        result = name

        if lowercase.endswith('left'):
            base_name = name[:-4]
            if name[-4] == 'l':
                result = base_name + 'right'
            elif name[-3] == 'e':
                result = base_name + 'Right'
            else:
                result = base_name + 'RIGHT'

        elif lowercase.startswith('left'):
            base_name = name[4:]
            if name[0] == 'l':
                result = 'right' + base_name
            elif name[1] == 'e':
                result = 'Right' + base_name
            else:
                result = 'RIGHT' + base_name

        elif lowercase[-1] == 'l' and lowercase[-2] in ['.', '_', '-', ' ']:
            result = result[:-1] + ('R' if name[-1] == 'L' else 'r')

        elif lowercase[0] == 'l' and lowercase[1] in ['.', '_', '-', ' ']:
            result = ('R' if name[0] == 'L' else 'r') + result[1:]

        else:
            return None

        return result

    def _collect_states(self, context: Context):
        self._prev_mode = context.mode
        self._armature = context.active_object.data
        self._pose = context.active_object.pose
        self._action = context.active_object.animation_data.action

        self._selected_bones = set(
            [b for b in self._pose.bones if b.bone.select])
        self._hidden_bones = set([b for b in self._pose.bones if b.bone.hide])
        self._hidden_layers = set(
            [i for i, l in enumerate(self._armature.layers) if not l])

        self._selected_curves = set(
            [f for f in self._action.fcurves if f.select])
        self._hidden_curves = set([f for f in self._action.fcurves if f.hide])

        for fcurve in self._action.fcurves:
            for kf in fcurve.keyframe_points:
                if kf.select_control_point:
                    self._selected_keyframes.add(kf)
                if kf.select_left_handle:
                    self._selected_left_handles.add(kf)
                if kf.select_right_handle:
                    self._selected_right_handles.add(kf)

    def _collect_curves(self):
        for bone in self._pose.bones:
            sym_name = ActionSymmetrizer._get_symmetrized_name(bone.name)
            if sym_name is not None:
                self._sym_name_pairs[bone.name] = sym_name
                self._bone_curves[bone.name] = set()
                self._bone_curves[sym_name] = set()

        for left_curve in self._action.fcurves:
            if not left_curve.data_path.startswith("pose.bones[\""):
                continue

            end = left_curve.data_path.index("\"]")
            bone_name = left_curve.data_path[12:end]

            if bone_name in self._bone_curves:
                self._bone_curves[bone_name].add(left_curve)

        for left_name, right_name in self._sym_name_pairs.items():
            # deleting previously existing curves
            right_curves = self._bone_curves[right_name]
            for left_curve in right_curves:
                self._action.fcurves.remove(left_curve)

            right_curves.clear()

            for left_curve in self._bone_curves[left_name]:
                # creating right sided copy
                right_data_path = left_curve.data_path.replace(
                    left_name, right_name)

                right_curve = self._action.fcurves.new(
                    right_data_path,
                    index=left_curve.array_index,
                    action_group=right_name)

                right_curve.extrapolation = left_curve.extrapolation

                right_curve.keyframe_points.insert(
                    left_curve.keyframe_points[0].co.x, 0, options={'FAST'})

                for left_modifier in left_curve.modifiers:
                    right_modifier = right_curve.modifiers.new(
                        left_modifier.type)

                    for p in dir(left_modifier):
                        if p in MODIFIER_IGNORE_ATTRIBS:
                            continue
                        value = getattr(left_modifier, p)
                        setattr(right_modifier, p, value)

                right_curves.add(right_curve)
                self._sym_curve_pairs[left_curve] = right_curve

    def _prepare(self):
        bpy.ops.object.mode_set(mode='POSE')

        for i in range(len(self._armature.layers)):
            self._armature.layers[i] = True

        for bone in self._pose.bones:
            bone.bone.hide = False
            bone.bone.select = bone.name in self._sym_name_pairs

        for fcurve in self._action.fcurves:
            fcurve.hide = False
            fcurve.select = fcurve in self._sym_curve_pairs

            for kf in fcurve.keyframe_points:
                kf.select_control_point = fcurve.select
                kf.select_left_handle = False
                kf.select_right_handle = False

        bpy.ops.graph.copy()

    def _insert(self, offset: float):
        for left_name, right_name in self._sym_name_pairs.items():
            self._pose.bones[left_name].bone.select = False
            self._pose.bones[right_name].bone.select = True

        for left_curve, right_curve in self._sym_curve_pairs.items():
            left_curve.select = False
            right_curve.select = True

        bpy.ops.graph.paste(
            offset='NONE',
            value_offset='NONE',
            flipped=True
        )

        for fcurve in self._sym_curve_pairs.values():
            for kf in fcurve.keyframe_points:
                kf.co_ui.x += offset

    def _cleanup(self):

        for layer in self._hidden_layers:
            self._armature.layers[layer] = False

        for bone in self._pose.bones:
            bone.bone.hide = bone in self._hidden_bones
            bone.bone.select = bone in self._selected_bones

        for fcurve in self._action.fcurves:
            fcurve.select = fcurve in self._selected_curves
            fcurve.hide = fcurve in self._hidden_curves

            for kf in fcurve.keyframe_points:
                kf.select_control_point = kf in self._selected_keyframes
                kf.select_left_handle = kf in self._selected_left_handles
                kf.select_right_handle = kf in self._selected_right_handles

        bpy.ops.object.mode_set(mode=self._prev_mode)

    def execute(self, context: Context, offset: float):
        self._collect_states(context)
        self._collect_curves()
        self._prepare()
        self._insert(offset)
        self._cleanup()


class T113D_OT_SymmetrizeAction(bpy.types.Operator):
    bl_idname = "t113d.symmetrize_action"
    bl_label = "Symmetrize Action"
    bl_description = "Symmetrizes the active action"
    bl_options = {'REGISTER', 'PRESET', 'UNDO'}

    use_custom_offset: BoolProperty(
        name="Use Custom Offset",
        default=False
    )

    custom_offset: FloatProperty(
        name="Custom Offset",
        default=0
    )

    @classmethod
    def poll(cls, context: Context):
        return (
            context.area.type in ['GRAPH_EDITOR', 'DOPESHEET_EDITOR']
            and context.mode in ["OBJECT", "POSE"]
            and context.active_object is not None
            and context.active_object.type == 'ARMATURE'
            and context.active_object.animation_data is not None
            and context.active_object.animation_data.action is not None
        )

    def check(self, context: Context):

        if not self.use_custom_offset:
            action = context.active_object.animation_data.action
            new_offset = (
                action.frame_range[1] - action.frame_range[0]) * 0.5

            changed = new_offset != self.custom_offset

            if changed:
                self.custom_offset = new_offset

            return changed

        return False

    def invoke(self, context: Context, event: Event):
        self.check(context)
        return self.execute(context)

    def draw(self, context: Context):
        self.layout.prop(self, "use_custom_offset")
        row = self.layout.row()
        row.active = self.use_custom_offset
        row.prop(self, "custom_offset")

    def execute(self, context: Context):
        ActionSymmetrizer().execute(context, self.custom_offset)
        return {'FINISHED'}
