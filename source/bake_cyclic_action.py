import bpy
from bpy.types import Context
from mathutils import Vector
import math


class T113D_OT_BakeCyclicAction(bpy.types.Operator):
    bl_idname = "t113d.bake_cyclic_action"
    bl_label = "Bake cyclic action"
    bl_description = (
        "bakes the cyclic action so that keyframes"
        " are only in the actions frame range"
    )
    bl_options = {'UNDO'}

    _error_message: str

    @classmethod
    def poll(cls, context):
        return (
            context.mode in ["OBJECT", "POSE"]
            and context.active_object is not None
            and context.active_object.animation_data is not None
            and context.active_object.animation_data.action is not None
        )

    @staticmethod
    def _verify_modifiers(fcurve: bpy.types.FCurve):
        if len(fcurve.modifiers) > 1:
            return False

        if len(fcurve.modifiers) == 0:
            return True

        modifier: bpy.types.FModifierCycles = fcurve.modifiers[0]
        if modifier.type != 'CYCLES':
            return False

        return (
            not modifier.use_restricted_range
            and (not modifier.use_influence or modifier.influence == 1.0)
            and modifier.mode_before == 'REPEAT'
            and modifier.cycles_before == 0
            and modifier.mode_after == 'REPEAT'
            and modifier.cycles_after == 0
        )

    @staticmethod
    def _get_keyframe_before(fcurve: bpy.types.FCurve, frame: float):

        previous_keyframe = None
        for keyframe in fcurve.keyframe_points:
            if keyframe.co.x > frame:
                break

            previous_keyframe = keyframe

        if previous_keyframe is None:
            raise LookupError(
                f"No keyframe before frame {frame}"
                f" on fcurve {fcurve.data_path}")

        return previous_keyframe

    @staticmethod
    def _bake_non_cyclic(
            fcurve: bpy.types.FCurve,
            start_frame: float,
            end_frame: float):

        try:
            T113D_OT_BakeCyclicAction._get_keyframe_before(fcurve, start_frame)
        except LookupError:
            fcurve.keyframe_points.insert(
                start_frame,
                fcurve.keyframe_points[0].co.y
            ).interpolation = 'CONSTANT'

        try:
            T113D_OT_BakeCyclicAction._get_keyframe_before(fcurve, end_frame)
        except LookupError:
            last_keyframe_index = len(fcurve.keyframe_points) - 1
            fcurve.keyframe_points.insert(
                start_frame,
                fcurve.keyframe_points[last_keyframe_index].co.y
            ).interpolation = 'CONSTANT'

        return True

    def _get_repeats(
            self,
            fcurve: bpy.types.FCurve,
            target_frame: float,
            source_frame: float,
            source_range: float):

        if target_frame == source_frame:
            return 0

        result = math.ceil(
            (source_frame - target_frame) / source_range)

        real_target_frame = target_frame + source_range * result
        keyframe = T113D_OT_BakeCyclicAction._get_keyframe_before(
            fcurve, real_target_frame)

        if (keyframe.co.x != real_target_frame
                and keyframe.interpolation
                not in ['CONSTANT', 'LINEAR', 'BEZIER']):
            self._error_message = (
                f"{fcurve.data_path}[{fcurve.array_index}] Does not repeat on"
                " a dividable interpolation type!"
                f" See frame {real_target_frame}"
            )
            return None

        return max(result, 0)

    @staticmethod
    def _add_repeats(
            fcurve: bpy.types.FCurve,
            points: list[bpy.types.Keyframe],
            repeats: float,
            offset: float):

        if repeats == 0:
            return

        add_num = repeats * len(points)
        fcurve.keyframe_points.add(add_num)
        new_points = iter(fcurve.keyframe_points[-add_num:])

        for p in points:
            for i in range(repeats):
                kf = next(new_points)

                kf.co = Vector((
                    p.co.x + (i + 1) * offset,
                    p.co.y
                ))

                kf.amplitude = p.amplitude
                kf.back = p.back
                kf.easing = p.easing
                kf.handle_left = kf.co + (p.handle_left - p.co)
                kf.handle_left_type = p.handle_left_type
                kf.handle_right = kf.co + (p.handle_right - p.co)
                kf.handle_right_type = p.handle_right_type
                kf.interpolation = p.interpolation
                kf.period = p.period
                kf.type = p.type

    def _bake_cyclic(
            self,
            fcurve: bpy.types.FCurve,
            start_frame: float,
            end_frame: float):

        first_keyframe = fcurve.keyframe_points[0]
        first_frame = first_keyframe.co.x

        last_keyframe_index = len(fcurve.keyframe_points) - 1
        last_keyframe = fcurve.keyframe_points[last_keyframe_index]
        last_frame = last_keyframe.co.x

        frame_range = last_frame - first_frame

        ###################################################################
        # check repeating frames

        if abs(first_keyframe.co.y - last_keyframe.co.y) > 0.001:
            self._error_message = (
                f"{fcurve.data_path}[{fcurve.array_index}] First and last"
                " keyframes do not carry the same value!"
            )
            return False

        ###################################################################
        # determine repeats

        repeats_to_start = self._get_repeats(
            fcurve, start_frame, first_frame, frame_range)
        if repeats_to_start is None:
            return False

        repeats_to_end = self._get_repeats(
            fcurve, end_frame, last_frame, -frame_range)
        if repeats_to_end is None:
            return False

        ###################################################################
        # copying over the handles

        border_value = (first_keyframe.co.y + last_keyframe.co.y) * 0.5
        first_keyframe.co_ui.y = border_value
        last_keyframe.co_ui.y = border_value

        first_keyframe.handle_left_type = 'FREE'
        first_keyframe.handle_right_type = 'FREE'
        first_keyframe.handle_left = (
            first_keyframe.co
            + (last_keyframe.handle_left - last_keyframe.co))

        last_keyframe.handle_left_type = 'FREE'
        last_keyframe.handle_right_type = 'FREE'
        last_keyframe.handle_right = (
            last_keyframe.co
            + (first_keyframe.handle_right - first_keyframe.co))

        ###################################################################
        # adding the repeats

        points = list(fcurve.keyframe_points)

        self._add_repeats(fcurve, points[1:], repeats_to_end, frame_range)
        self._add_repeats(fcurve, points[:-1], repeats_to_start, -frame_range)

        fcurve.update()

        return True

    @staticmethod
    def _get_create_keyframe(fcurve: bpy.types.FCurve, frame: float):
        result = T113D_OT_BakeCyclicAction._get_keyframe_before(
            fcurve, frame)

        if result.co.x != frame:
            value = fcurve.evaluate(frame)
            result = fcurve.keyframe_points.insert(frame, value)

        for i, kf in enumerate(fcurve.keyframe_points):
            if kf.co.x == frame:
                return i

        raise IndexError("Index not found")

    def _process(self, action: bpy.types.Action):
        start_frame = action.frame_range[0]
        end_frame = action.frame_range[1]

        for fcurve in action.fcurves:
            if len(fcurve.keyframe_points) == 0:
                continue
            elif len(fcurve.keyframe_points) == 1:
                value = fcurve.keyframe_points[0].co.y
                fcurve.keyframe_points.add(1)
                fcurve.keyframe_points[0].co_ui = Vector((start_frame, value))
                fcurve.keyframe_points[0].interpolation = 'CONSTANT'
                fcurve.keyframe_points[1].co_ui = Vector((end_frame, value))
                fcurve.keyframe_points[1].interpolation = 'CONSTANT'
                continue
            else:
                first_keyframe = fcurve.keyframe_points[0]
                last_keyframe_index = len(fcurve.keyframe_points) - 1
                last_keyframe = fcurve.keyframe_points[last_keyframe_index]

                if (first_keyframe.co.x == start_frame
                        and last_keyframe.co.x == end_frame):
                    continue

            if not self._verify_modifiers(fcurve):
                self._error_message = (
                    f"Modifiers on curve {fcurve.data_path} are invalid"
                )
                return

            success = False
            if len(fcurve.modifiers) == 0:
                success = self._bake_non_cyclic(fcurve, start_frame, end_frame)
            else:
                success = self._bake_cyclic(fcurve, start_frame, end_frame)

            if not success:
                return

            fcurve.keyframe_points.sort()

            to_delete_start = self._get_create_keyframe(fcurve, start_frame)
            to_delete_end_index = self._get_create_keyframe(
                fcurve, end_frame) + 1
            to_delete_end = len(fcurve.keyframe_points) - to_delete_end_index

            for _ in range(to_delete_end):
                fcurve.keyframe_points.remove(
                    fcurve.keyframe_points[to_delete_end_index],
                    fast=True)

            for _ in range(to_delete_start):
                fcurve.keyframe_points.remove(
                    fcurve.keyframe_points[0],
                    fast=True)

    def execute(self, context: Context):
        base_action = context.active_object.animation_data.action
        self._error_message = None

        if not base_action.use_cyclic:
            self._error_message = (
                f"The action {base_action.name} is not cyclic"
            )

        else:

            action: bpy.types.Action = base_action.copy()
            action.name = base_action.name + "_baked"

            self._process(action)

            if self._error_message is not None:
                bpy.data.actions.remove(action)

        if self._error_message is not None:
            self.report({'ERROR'}, self._error_message)
            return {'CANCELLED'}
        else:
            context.active_object.animation_data.action = action
            return {'FINISHED'}
