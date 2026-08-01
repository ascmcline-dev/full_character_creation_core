from __future__ import annotations

import copy
import json
import re
from typing import Any

from .nodes import LENS_PROMPTS_V2
from .nodes_v230 import _clean_phrase, _is_extreme_closeup_v231, _sentences
from .nodes_v241 import _is_direct_back, _is_rear_orientation
from .nodes_v243 import _is_regional
from .nodes_v247 import (
    ALL_FOURS,
    EXTENDED_PUPPY,
    CharacterBlueprintCreatorV247,
    CharacterPromptAssemblerV247,
    CharacterShotControlV247,
    QwenDatasetQueueV247,
    _floor_kind,
    _floor_pose_prompt_v247,
    _single_subject_scene_v247,
)

# -----------------------------------------------------------------------------
# V2.4.8 / Studio V2.8.8
# Section B targeted correction:
# - direct Back View for All Fours is anchored behind the pelvis, not near the head
# - rear tabletop geometry keeps shoulders above wrists and hips above knees
# - torso remains elevated/horizontal and the head looks forward away from camera
# - front-view All Fours behavior is inherited unchanged from V2.4.7
# Small requested pose-list maintenance:
# - add body-only Forward Lean pose
# - remove Finger Heart and Licking a Popsicle from the current dropdown
# -----------------------------------------------------------------------------

FORWARD_LEAN = "Forward Lean — Playful Social Pose"
REMOVED_CURRENT_POSES = {"Finger Heart Near Face", "Licking a Popsicle"}


def _pose_choices_v248() -> list[str]:
    inherited = list(CharacterShotControlV247.INPUT_TYPES()["required"]["pose"][0])
    out: list[str] = []
    for value in inherited:
        if value in REMOVED_CURRENT_POSES or value in {FORWARD_LEAN, "Custom"}:
            continue
        out.append(value)
    out.extend([FORWARD_LEAN, "Custom"])
    return out


POSES_V248 = _pose_choices_v248()


def _forward_lean_prompt_v248() -> str:
    """Body-only standing lean with no furniture or prop dependency."""
    return _sentences(
        "standing in a playful forward lean from the hips",
        "the torso angles gently toward the camera while the spine stays naturally elongated and the shoulders remain relaxed",
        "the hips shift slightly backward for balance, the knees remain softly bent, and the waist forms a natural subtle curve",
        "both arms rest naturally behind the torso, alongside the hips, or relaxed near the thighs",
        "the head remains comfortably aligned with the upper body in a casual confident social-media pose",
    )


def _rear_all_fours_pose_v248(shot_type: str) -> str:
    """A true elevated tabletop rather than a bow, fold, crouch, or puppy pose."""
    return _sentences(
        _floor_pose_prompt_v247("all_fours", shot_type),
        "the torso is elevated and held approximately parallel to the floor, with open space beneath the chest and abdomen",
        "the shoulders are vertically above the wrists, both elbows are extended, and both arms form straight supporting columns",
        "the hip sockets are vertically above the knees, both thighs are near vertical, and the pelvis remains clearly separated above the heels",
        "the shoulders and hips remain at approximately the same working height in a stable neutral tabletop",
        "the head is lifted in neutral spinal alignment and the gaze is directed forward away from the camera",
    )


def _rear_all_fours_camera_v248(plan: dict[str, Any], effective_lens: str) -> str:
    """Fix camera location to the rear side of the pelvis and establish depth order."""
    height = str(plan.get("camera_height", "Eye Level"))
    if height == "Slightly Above Eye Level":
        height_text = "camera is slightly elevated above rear hip height with a mild controlled downward angle"
    elif height == "Slightly Below Eye Level":
        height_text = "camera is low behind the subject near knee-to-hip height with a mild upward angle"
    else:
        height_text = "camera is behind the subject at rear hip height with a level horizon"

    return _sentences(
        "strict direct rear view of one subject holding an elevated hands-and-knees tabletop pose",
        "the camera is physically positioned on the rear side of the pelvis and aims forward toward the shoulders and back of the head",
        "the rear hips and lower back occupy the central foreground, and the spine leads away from the lens toward the shoulders and back of the head",
        "the back of the head is the only visible side of the head, with the face located on the far side and the gaze directed forward",
        height_text,
        LENS_PROMPTS_V2.get(effective_lens, "rectilinear 50mm normal-lens perspective"),
        "camera distance is established before capture so both hands, both knees, both shins, both feet, the complete torso, and the complete head remain in one frame",
    )


class CharacterBlueprintCreatorV248(CharacterBlueprintCreatorV247):
    FUNCTION = "build_blueprint_v248"
    DESCRIPTION = "Current Character Creator paired with the v2.4.8 rear-tabletop camera and support-geometry lock."

    def build_blueprint_v248(self, **kwargs):
        result = list(super().build_blueprint_v247(**kwargs))
        profile = copy.deepcopy(result[8])
        profile["schema"] = "CHARACTER_BLUEPRINT_V248"
        profile["schema_version"] = 19
        result[8] = profile
        result[15] = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        return tuple(result)


class CharacterShotControlV248(CharacterShotControlV247):
    FUNCTION = "build_shot_plan_v248"
    DESCRIPTION = (
        "Current Shot Control with a direct-rear All Fours camera locked behind the pelvis, elevated tabletop support geometry, "
        "and the body-only Forward Lean social pose."
    )

    @classmethod
    def INPUT_TYPES(cls):
        base = copy.deepcopy(super().INPUT_TYPES())
        base["required"]["pose"] = (POSES_V248, {"default": "Neutral Standing"})
        return base

    def build_shot_plan_v248(self, **kwargs):
        requested_pose = str(kwargs.get("pose", ""))
        result = list(super().build_shot_plan_v247(**kwargs))
        plan = copy.deepcopy(result[0])
        plan["schema"] = "FCC_SHOT_PLAN_V248"
        plan["schema_version"] = 17

        # Requested body-only pose. This intentionally changes no camera,
        # framing, expression, clothing, mark, or environment routing.
        if requested_pose == FORWARD_LEAN and not _is_regional(plan) and not _is_extreme_closeup_v231(plan):
            plan["pose"] = FORWARD_LEAN
            plan["pose_prompt"] = _forward_lean_prompt_v248()

        # Section B fix is deliberately limited to All Fours + direct Back View.
        # Front View, profiles, and three-quarter variants retain V2.4.7 behavior.
        kind = _floor_kind(requested_pose)
        if kind == "all_fours" and str(plan.get("camera_view", "")) == "Back View":
            effective_lens = str(plan.get("lens_effective", plan.get("lens", "50mm Normal")))
            shot_type = str(plan.get("shot_type", kwargs.get("shot_type", "Three-Quarter Body")))
            plan["rear_tabletop_lock"] = True
            plan["pose_prompt"] = _rear_all_fours_pose_v248(shot_type)
            plan["camera_prompt"] = _rear_all_fours_camera_v248(plan, effective_lens)
            plan["scene_prompt"] = _single_subject_scene_v247(str(plan.get("scene_prompt", "")))
            plan["expression_prompt"] = ""

        plan["final_shot_prompt"] = _sentences(
            plan.get("framing_prompt", ""),
            plan.get("camera_prompt", ""),
            plan.get("pose_prompt", ""),
            plan.get("expression_prompt", ""),
            plan.get("scene_prompt", ""),
            plan.get("environment_prompt", ""),
            _clean_phrase(kwargs.get("shot_suffix", "")),
        )

        summary = str(plan.get("active_settings_summary", ""))
        summary = re.sub(r"\nRear-tabletop lock:.*$", "", summary, flags=re.S).rstrip()
        if plan.get("rear_tabletop_lock"):
            summary += (
                "\nRear-tabletop lock: camera anchored behind pelvis; torso elevated; "
                "shoulders over wrists; hips over knees; back of head only"
            )
        plan["active_settings_summary"] = summary

        result[0] = plan
        result[1] = plan["final_shot_prompt"]
        result[3] = plan.get("camera_prompt", "")
        result[4] = plan.get("pose_prompt", "")
        result[5] = plan.get("expression_prompt", "")
        result[7] = plan["active_settings_summary"]
        result[8] = json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True)
        return tuple(result)


class CharacterPromptAssemblerV248(CharacterPromptAssemblerV247):
    FUNCTION = "assemble_prompt_v248"
    DESCRIPTION = "Current visibility compiler paired with the v2.4.8 direct-rear tabletop geometry lock."

    def assemble_prompt_v248(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        result = list(super().assemble_prompt_v247(
            character_blueprint, shot_plan, generation_purpose, reference_label,
            trigger_word, custom_prefix, custom_suffix,
        ))
        plan = shot_plan if isinstance(shot_plan, dict) else {}
        if plan.get("rear_tabletop_lock"):
            notes = str(result[10] or "")
            notes += (
                "\nRear tabletop compiler V2.4.8: direct Back View is physically anchored behind the pelvis; "
                "the torso stays elevated, shoulders remain above wrists, hips remain above knees, and only the back of the head is visible."
            )
            result[10] = notes
            try:
                sections = json.loads(result[18]) if result[18] else {}
            except Exception:
                sections = {}
            sections["routing_mode"] = "rear_tabletop_lock_v248"
            sections["rear_tabletop_lock"] = True
            result[18] = json.dumps(sections, indent=2, ensure_ascii=False)
        return tuple(result)


class QwenDatasetQueueV248(QwenDatasetQueueV247):
    DESCRIPTION = "Current FCC Qwen dataset queue paired with the v2.4.8 rear-tabletop geometry lock."
