from __future__ import annotations

import copy
import json

from .nodes_v230 import LENS_PROMPTS_V2, _clean_phrase, _is_extreme_closeup_v231, _sentences
from .nodes_v241 import (
    FCCDatasetDirector,
    FCCQueueItemRouter,
    POSES_V241,
    POSE_PROMPTS_V241,
    QwenDatasetQueueV241,
    CharacterBlueprintCreatorV241,
    CharacterPromptAssemblerV241,
    CharacterShotControlV241,
    _camera_view,
    _is_direct_back,
    _rebuild_shot_summary,
    _regional_pose_should_be_suppressed,
)

# -----------------------------------------------------------------------------
# V2.4.2 / Studio V2.8.2
# - adds explicit left-side-down and right-side-down lateral recumbent poses
# - replaces standing/front/back camera language with side-lying camera language
# - keeps shoulders, torso, pelvis, and legs stacked without body twisting
# - provides body-level, elevated, and low-surface camera placement for side poses
# -----------------------------------------------------------------------------

SIDE_LYING_LEFT = "Lying on Side — Left Side Down"
SIDE_LYING_RIGHT = "Lying on Side — Right Side Down"
SIDE_LYING_POSES = {SIDE_LYING_LEFT, SIDE_LYING_RIGHT}

POSES_V242 = list(POSES_V241)[:-1] + [
    SIDE_LYING_LEFT,
    SIDE_LYING_RIGHT,
    "Custom",
]

POSE_PROMPTS_V242 = dict(POSE_PROMPTS_V241)
POSE_PROMPTS_V242.update({
    SIDE_LYING_LEFT: (
        "clear lateral recumbent pose lying on the anatomical left side, with the left shoulder, left ribcage, "
        "and left hip supported by the surface, the right side uppermost, shoulders and pelvis vertically stacked, "
        "the spine naturally aligned, the legs together with a gentle relaxed bend, and the head supported in line with the spine"
    ),
    SIDE_LYING_RIGHT: (
        "clear lateral recumbent pose lying on the anatomical right side, with the right shoulder, right ribcage, "
        "and right hip supported by the surface, the left side uppermost, shoulders and pelvis vertically stacked, "
        "the spine naturally aligned, the legs together with a gentle relaxed bend, and the head supported in line with the spine"
    ),
})


def _side_down_label(pose: str) -> tuple[str, str]:
    if pose == SIDE_LYING_LEFT:
        return "left", "right"
    return "right", "left"


def _side_lying_view_prompt(plan: dict) -> str:
    pose = str(plan.get("pose", ""))
    down_side, upper_side = _side_down_label(pose)
    view = _camera_view(plan)

    if view == "Back View":
        return _sentences(
            "rear lateral view from behind of the primary character in a side-lying position",
            f"the anatomical {down_side} side rests on the surface and the {upper_side} side remains uppermost",
            "the back of the head, rear shoulder, back, waist, rear hip, and backs of the legs face the camera",
            "the shoulders and pelvis remain stacked and the spine remains aligned without torso rotation toward the lens",
        )
    if view == "Front View":
        return _sentences(
            "front lateral view of the primary character in a side-lying position",
            f"the anatomical {down_side} side rests on the surface and the {upper_side} side remains uppermost",
            "the face, front shoulder, front torso, waist, and front hip are oriented toward the camera",
            "the shoulders and pelvis remain stacked in a clear lateral recumbent body position",
        )
    if view == "Three-Quarter Left":
        return _sentences(
            "front three-quarter-left view of the side-lying primary character",
            f"the anatomical {down_side} side rests on the surface and the {upper_side} side remains uppermost",
            "the body remains laterally stacked with only a mild camera-side perspective",
        )
    if view == "Three-Quarter Right":
        return _sentences(
            "front three-quarter-right view of the side-lying primary character",
            f"the anatomical {down_side} side rests on the surface and the {upper_side} side remains uppermost",
            "the body remains laterally stacked with only a mild camera-side perspective",
        )
    if view == "Rear Three-Quarter Left":
        return _sentences(
            "rear three-quarter-left view of the side-lying primary character",
            f"the anatomical {down_side} side rests on the surface and the {upper_side} side remains uppermost",
            "the back remains dominant in frame and the torso does not twist toward the camera",
        )
    if view == "Rear Three-Quarter Right":
        return _sentences(
            "rear three-quarter-right view of the side-lying primary character",
            f"the anatomical {down_side} side rests on the surface and the {upper_side} side remains uppermost",
            "the back remains dominant in frame and the torso does not twist toward the camera",
        )
    if view == "Left Profile":
        return _sentences(
            "left-side profile view of the primary character lying laterally",
            f"the anatomical {down_side} side rests on the surface and the {upper_side} side remains uppermost",
            "the camera is slightly elevated when needed so the side-lying body remains fully visible",
        )
    if view == "Right Profile":
        return _sentences(
            "right-side profile view of the primary character lying laterally",
            f"the anatomical {down_side} side rests on the surface and the {upper_side} side remains uppermost",
            "the camera is slightly elevated when needed so the side-lying body remains fully visible",
        )
    return _sentences(
        "clear side-lying lateral view of the primary character",
        f"the anatomical {down_side} side rests on the surface and the {upper_side} side remains uppermost",
        "the shoulders and pelvis remain stacked and the spine remains aligned",
    )


def _side_lying_height_prompt(plan: dict) -> str:
    height = str(plan.get("camera_height", ""))
    if height == "Slightly Above Eye Level":
        return "camera moderately elevated above the side-lying body with a controlled downward angle centered on the torso"
    if height == "Slightly Below Eye Level":
        return "camera placed low near the support surface with a mild upward angle centered on the side-lying torso"
    if height == "Eye Level":
        return "camera level with the side-lying body's midline and centered on the torso, with sufficient distance for the selected crop"
    return "camera centered on the side-lying body with sufficient distance for the selected crop"


class CharacterBlueprintCreatorV242(CharacterBlueprintCreatorV241):
    FUNCTION = "build_blueprint_v242"
    DESCRIPTION = (
        "Current Character Creator with visibility-aware anatomy, tan, swimwear, tattoo, piercing, and hair-color routing."
    )

    def build_blueprint_v242(self, **kwargs):
        return super().build_blueprint_v241(**kwargs)


class CharacterShotControlV242(CharacterShotControlV241):
    FUNCTION = "build_shot_plan_v242"
    DESCRIPTION = (
        "Current Shot Control with strict camera direction, prone and left/right side-lying poses, social gestures, "
        "body-scale camera targeting, and regional-documentation pose suppression."
    )

    @classmethod
    def INPUT_TYPES(cls):
        base = copy.deepcopy(super().INPUT_TYPES())
        base["required"]["pose"] = (POSES_V242, {"default": "Neutral Standing"})
        return base

    def build_shot_plan_v242(self, **kwargs):
        result = list(super().build_shot_plan_v241(**kwargs))
        plan = copy.deepcopy(result[0])
        plan["schema"] = "FCC_SHOT_PLAN_V242"
        plan["schema_version"] = 9

        pose = str(kwargs.get("pose", ""))
        plan["pose"] = pose
        custom_direction = plan.get("planner_mode") == "Custom Shot Direction — Keep Character Settings"

        if pose in SIDE_LYING_POSES:
            plan["pose_prompt"] = POSE_PROMPTS_V242[pose]

            if not custom_direction and not _is_extreme_closeup_v231(plan) and not _regional_pose_should_be_suppressed(plan):
                view_prompt = _side_lying_view_prompt(plan)
                height_prompt = _side_lying_height_prompt(plan)
                lens = str(plan.get("lens", ""))
                lens_prompt = LENS_PROMPTS_V2.get(lens, "")
                if plan.get("camera_height") == "Custom" or lens == "Custom":
                    custom_camera = _clean_phrase(kwargs.get("custom_camera", ""))
                    if custom_camera:
                        height_prompt = custom_camera
                        lens_prompt = ""
                plan["camera_prompt"] = _sentences(view_prompt, height_prompt, lens_prompt)

            # A direct rear side-lying view cannot show a usable facial expression.
            ignored_extra: list[str] = []
            if _is_direct_back(plan):
                plan["expression_prompt"] = ""
                ignored_extra.append("facial expression in rear side-lying view")

            if _regional_pose_should_be_suppressed(plan):
                plan["pose_prompt"] = ""
                ignored_extra.append("side-lying pose for regional documentation")

            plan["final_shot_prompt"] = _sentences(
                plan.get("framing_prompt", ""),
                plan.get("camera_prompt", ""),
                plan.get("pose_prompt", ""),
                plan.get("expression_prompt", ""),
                plan.get("scene_prompt", ""),
                plan.get("environment_prompt", ""),
                _clean_phrase(kwargs.get("shot_suffix", "")),
            )
            plan["active_settings_summary"] = _rebuild_shot_summary(plan, ignored_extra)

        result[0] = plan
        result[1] = plan.get("final_shot_prompt", "")
        result[3] = plan.get("camera_prompt", "")
        result[4] = plan.get("pose_prompt", "")
        result[5] = plan.get("expression_prompt", "")
        result[7] = plan.get("active_settings_summary", "")
        result[8] = json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True)
        return tuple(result)


class CharacterPromptAssemblerV242(CharacterPromptAssemblerV241):
    FUNCTION = "assemble_prompt_v242"
    DESCRIPTION = (
        "Visibility compiler with camera-orientation awareness, explicit swimwear, pattern-specific tan lines, strict rear views, "
        "side-lying pose support, and positive-boundary regional macro routing."
    )

    def assemble_prompt_v242(self, **kwargs):
        return super().assemble_prompt_v241(**kwargs)


class QwenDatasetQueueV242(QwenDatasetQueueV241):
    DESCRIPTION = "Current FCC Qwen dataset queue using the v2.4.2 character blueprint and visibility rules."
