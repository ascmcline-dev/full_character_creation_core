from __future__ import annotations

import copy
import json
import re
from typing import Any

from .nodes import LENS_PROMPTS_V2
from .nodes_v230 import _clean_phrase, _is_extreme_closeup_v231, _sentences
from .nodes_v241 import _is_direct_back, _is_rear_orientation
from .nodes_v243 import AUTO_ASPECT, WIDE_FULL_BODY, _is_regional
from .nodes_v244 import AUTO_LENS
from .nodes_v245 import (
    ALL_FOURS as LEGACY_ALL_FOURS,
    EXTENDED_PUPPY,
    FACE_SCALE_SHOTS,
    FLOOR_POSES_V245,
)
from .nodes_v246 import (
    CharacterBlueprintCreatorV246,
    CharacterPromptAssemblerV246,
    CharacterShotControlV246,
    QwenDatasetQueueV246,
)

# -----------------------------------------------------------------------------
# V2.4.7 / Studio V2.8.7
# - floor-pose framing is no longer allowed to inherit standing shot language
# - all-fours uses neutral solo tabletop terminology instead of sexual wording
# - extended puppy has a dedicated pose route and cannot collapse into tabletop
# - floor poses receive a single-subject, single-frame composition authority
# - camera orientation is rebuilt for floor geometry rather than standing bodies
# -----------------------------------------------------------------------------

ALL_FOURS = "All Fours — Hands and Knees (Solo)"
FLOOR_POSE_LABELS = {ALL_FOURS, LEGACY_ALL_FOURS, EXTENDED_PUPPY}
FLOOR_POSES_V247 = set(FLOOR_POSES_V245) | FLOOR_POSE_LABELS


def _pose_choices_v247() -> list[str]:
    inherited = list(CharacterShotControlV246.INPUT_TYPES()["required"]["pose"][0])
    out: list[str] = []
    for value in inherited:
        if value in {LEGACY_ALL_FOURS, ALL_FOURS, EXTENDED_PUPPY, "Custom"}:
            continue
        out.append(value)
    out.extend([ALL_FOURS, EXTENDED_PUPPY, "Custom"])
    return out


POSES_V247 = _pose_choices_v247()


def _floor_kind(pose: str) -> str:
    if pose in {ALL_FOURS, LEGACY_ALL_FOURS}:
        return "all_fours"
    if pose == EXTENDED_PUPPY:
        return "extended_puppy"
    return ""


def _floor_pose_prompt_v247(kind: str, shot_type: str) -> str:
    """Pose language that names one body and unambiguous support landmarks."""
    if not kind:
        return ""

    if shot_type in FACE_SCALE_SHOTS:
        if kind == "extended_puppy":
            return _sentences(
                "the primary character is positioned in an extended puppy yoga pose outside the tight portrait crop",
                "only the head, nearby shoulder line, and forward-reaching arm context enter the close frame",
                "the head remains naturally aligned between the extended arms",
            )
        return _sentences(
            "the primary character is positioned on hands and knees outside the tight portrait crop",
            "only the head and nearby shoulder line enter the close frame",
            "the head remains naturally aligned with the spine",
        )

    if kind == "extended_puppy":
        return _sentences(
            "one adult primary character in a solo extended puppy yoga pose on the floor",
            "the knees are planted directly beneath the hips and the shins and tops of the feet rest continuously on the surface",
            "the hips remain high above the knees while both arms reach far forward with the palms flat",
            "the chest and sternum lower toward the surface and the head stays low between the extended arms",
            "the body forms one continuous aligned figure from hands through shoulders, spine, pelvis, knees, and feet",
        )

    return _sentences(
        "one adult primary character in a solo tabletop pose on hands and knees",
        "the palms are planted shoulder-width directly beneath the shoulders and support the upper body",
        "the knees are planted hip-width directly beneath the hips while the shins and tops of the feet rest on the surface",
        "the spine remains neutral, the pelvis stays centered above the knees, and the head aligns naturally with the spine",
        "the body forms one continuous figure from head through shoulders, back, pelvis, knees, lower legs, and feet",
    )


def _floor_framing_v247(shot_type: str, kind: str) -> str:
    """Reinterpret vertical body-shot names as floor-pose coverage, never standing."""
    pose_name = "extended puppy pose" if kind == "extended_puppy" else "hands-and-knees tabletop pose"
    if shot_type == WIDE_FULL_BODY:
        return _sentences(
            f"wide landscape environmental photograph of one complete {pose_name}",
            "the entire head, hair, arms, hands, torso, back, pelvis, knees, shins, and feet remain inside one continuous frame",
            "the floor pose occupies about fifty-five to sixty-five percent of the image width with generous environment on every side",
        )
    if shot_type == "Full Body":
        return _sentences(
            f"landscape full-body floor composition of one complete {pose_name}",
            "the entire head and hair, arms, hands, torso, back, pelvis, knees, lower legs, and feet are fully inside the frame",
            "clear margin remains beyond the hands, head, hips, knees, and feet",
            "the single subject occupies about sixty-five to seventy-five percent of the image width",
        )
    if shot_type == "Three-Quarter Body":
        return _sentences(
            f"medium-wide landscape floor composition showing one complete {pose_name}",
            "the head, shoulders, arms, hands, torso, pelvis, both knees, shins, and feet remain inside the same frame",
            "the crop follows the horizontal floor geometry and includes the complete pose",
            "clear margin remains around the full pose",
        )
    if shot_type == "Waist-Up Midshot":
        return _sentences(
            f"medium floor-level composition of one {pose_name}",
            "the complete head, shoulders, arms, hands, torso, pelvis, and knees are visible together",
            "the lower legs may approach the far edge while the body remains one continuous subject",
        )
    return ""


def _floor_view_prompt_v247(plan: dict[str, Any], kind: str) -> str:
    view = str(plan.get("camera_view", "Front View"))
    pose_name = "extended puppy pose" if kind == "extended_puppy" else "tabletop pose"

    if view == "Back View":
        return _sentences(
            f"strict rear floor-level view from behind the single subject in the {pose_name}",
            "the camera is centered on the spine and pelvis and looks forward along the length of the body",
            "the back of the head, shoulders, back, waist, hips, knees, shins, and feet face the camera in one continuous alignment",
            "the face remains turned away from the lens",
        )
    if view in {"Rear Three-Quarter Left", "Rear Three-Quarter Right"}:
        return _sentences(
            f"{view.lower()} floor-level view of the single subject in the {pose_name}",
            "the back, rear waist, and hips remain dominant while the camera reveals only a mild side plane",
            "the torso and pelvis remain aligned in the same pose",
        )
    if view in {"Left Profile", "Right Profile"}:
        return _sentences(
            f"{view.lower()} floor-level profile of the single subject in the {pose_name}",
            "the shoulders, spine, hips, knees, and lower legs remain visibly connected in one lateral body line",
        )
    if view in {"Three-Quarter Left", "Three-Quarter Right"}:
        return _sentences(
            f"{view.lower()} floor-level view of the single subject in the {pose_name}",
            "the camera supplies a mild oblique angle while the body remains one continuous aligned figure",
        )
    return _sentences(
        f"front floor-level view facing the single subject in the {pose_name}",
        "the head and shoulders are nearest the camera while the torso, pelvis, knees, and feet recede naturally behind",
        "the body remains one continuous figure rather than separate views",
    )


def _floor_height_prompt_v247(plan: dict[str, Any]) -> str:
    height = str(plan.get("camera_height", "Eye Level"))
    if height == "Slightly Above Eye Level":
        return "camera moderately elevated above the floor pose with a controlled downward view centered between the mid-back and pelvis"
    if height == "Slightly Below Eye Level":
        return "camera very low near the floor surface with a mild upward view along the complete pose"
    if height == "Eye Level":
        return "camera level with the middle of the floor pose and parallel to the support surface"
    return _clean_phrase(plan.get("camera_prompt", ""))


def _single_subject_scene_v247(scene_prompt: str) -> str:
    scene_prompt = _clean_phrase(scene_prompt)
    replacement = "one single adult primary character is captured once in one uninterrupted single-camera frame"
    if not scene_prompt:
        return replacement
    scene_prompt = re.sub(
        r"only the primary character is visible in the scene",
        replacement,
        scene_prompt,
        flags=re.I,
    )
    if replacement.lower() not in scene_prompt.lower():
        scene_prompt = _sentences(replacement, scene_prompt)
    return scene_prompt


class CharacterBlueprintCreatorV247(CharacterBlueprintCreatorV246):
    FUNCTION = "build_blueprint_v247"
    DESCRIPTION = "Current Character Creator paired with the v2.4.7 floor-pose geometry hotfix."

    def build_blueprint_v247(self, **kwargs):
        result = list(super().build_blueprint_v246(**kwargs))
        profile = copy.deepcopy(result[8])
        profile["schema"] = "CHARACTER_BLUEPRINT_V247"
        profile["schema_version"] = 18
        result[8] = profile
        result[15] = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        return tuple(result)


class CharacterShotControlV247(CharacterShotControlV246):
    FUNCTION = "build_shot_plan_v247"
    DESCRIPTION = (
        "Current Shot Control with dedicated single-subject floor-pose framing for hands-and-knees and extended puppy poses. "
        "Standing crop language is never reused for these floor poses."
    )

    @classmethod
    def INPUT_TYPES(cls):
        base = copy.deepcopy(super().INPUT_TYPES())
        base["required"]["pose"] = (POSES_V247, {"default": "Neutral Standing"})
        return base

    def build_shot_plan_v247(self, **kwargs):
        call_kwargs = dict(kwargs)
        requested_pose = str(call_kwargs.get("pose", ""))
        # Accept workflows saved with the older label while presenting only the
        # neutral solo label in the current dropdown.
        if requested_pose == LEGACY_ALL_FOURS:
            call_kwargs["pose"] = LEGACY_ALL_FOURS

        result = list(super().build_shot_plan_v246(**call_kwargs))
        plan = copy.deepcopy(result[0])
        kind = _floor_kind(requested_pose)
        if not kind:
            plan["schema"] = "FCC_SHOT_PLAN_V247"
            plan["schema_version"] = 16
            result[0] = plan
            result[8] = json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True)
            return tuple(result)

        shot_type = str(plan.get("shot_type", call_kwargs.get("shot_type", "")))
        effective_lens = str(plan.get("lens_effective", plan.get("lens", "50mm Normal")))
        plan["pose"] = ALL_FOURS if kind == "all_fours" else EXTENDED_PUPPY
        plan["pose_kind"] = kind
        plan["floor_pose_route"] = True
        plan["schema"] = "FCC_SHOT_PLAN_V247"
        plan["schema_version"] = 16

        floor_framing = _floor_framing_v247(shot_type, kind)
        if floor_framing and not _is_regional(plan) and not _is_extreme_closeup_v231(plan):
            plan["framing_prompt"] = floor_framing

        if not _is_regional(plan) and not _is_extreme_closeup_v231(plan):
            plan["pose_prompt"] = _floor_pose_prompt_v247(kind, shot_type)
            plan["camera_prompt"] = _sentences(
                _floor_view_prompt_v247(plan, kind),
                _floor_height_prompt_v247(plan),
                LENS_PROMPTS_V2.get(effective_lens, "rectilinear 50mm normal-lens perspective"),
                "camera distance is established before capture so the complete floor pose remains inside one frame",
            )
            plan["scene_prompt"] = _single_subject_scene_v247(str(plan.get("scene_prompt", "")))
            if _is_direct_back(plan) or _is_rear_orientation(plan):
                plan["expression_prompt"] = ""

        # Floor poses always use landscape Auto-by-Shot dimensions for body
        # coverage. Explicit user aspect choices remain respected.
        requested_aspect = str(kwargs.get("aspect_ratio", AUTO_ASPECT))
        if requested_aspect == AUTO_ASPECT and shot_type in {"Waist-Up Midshot", "Three-Quarter Body", "Full Body", WIDE_FULL_BODY}:
            plan["aspect_ratio"] = "Landscape 3:2 — Automatic for Floor Pose"
            plan["recommended_width"] = 1536
            plan["recommended_height"] = 1024

        plan["resolution_summary"] = (
            f"ACTIVE OUTPUT SIZE: {plan.get('recommended_width')} × {plan.get('recommended_height')} | "
            f"{plan.get('aspect_ratio')} | EFFECTIVE LENS: {effective_lens}"
        )
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
        summary = re.sub(r"\nACTIVE OUTPUT SIZE:.*$", "", summary, flags=re.S).rstrip()
        summary += (
            "\nFloor-pose route: active — vertical standing crop language replaced with one continuous landscape floor composition"
            f"\nPose route: {'Extended Puppy' if kind == 'extended_puppy' else 'Solo All Fours'}"
            "\n" + plan["resolution_summary"]
        )
        plan["active_settings_summary"] = summary

        result[0] = plan
        result[1] = plan["final_shot_prompt"]
        result[2] = plan.get("framing_prompt", "")
        result[3] = plan.get("camera_prompt", "")
        result[4] = plan.get("pose_prompt", "")
        result[5] = plan.get("expression_prompt", "")
        result[7] = plan["active_settings_summary"]
        result[8] = json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True)
        result[9] = int(plan.get("recommended_width", result[9]))
        result[10] = int(plan.get("recommended_height", result[10]))
        return tuple(result)


class CharacterPromptAssemblerV247(CharacterPromptAssemblerV246):
    FUNCTION = "assemble_prompt_v247"
    DESCRIPTION = "Garment-first visibility compiler paired with the v2.4.7 single-subject floor-pose route."

    def assemble_prompt_v247(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        result = list(super().assemble_prompt_v246(
            character_blueprint, shot_plan, generation_purpose, reference_label,
            trigger_word, custom_prefix, custom_suffix,
        ))
        plan = shot_plan if isinstance(shot_plan, dict) else {}
        if plan.get("floor_pose_route"):
            notes = str(result[10] or "")
            notes += (
                "\nFloor-pose compiler V2.4.7: standing framing was replaced by a landscape single-subject floor composition; "
                "all-fours and extended puppy use separate anatomical support landmarks."
            )
            result[10] = notes
            try:
                sections = json.loads(result[18]) if result[18] else {}
            except Exception:
                sections = {}
            sections["routing_mode"] = "single_subject_floor_pose_v247"
            sections["floor_pose_kind"] = plan.get("pose_kind", "")
            result[18] = json.dumps(sections, indent=2, ensure_ascii=False)
        return tuple(result)


class QwenDatasetQueueV247(QwenDatasetQueueV246):
    DESCRIPTION = "Current FCC Qwen dataset queue paired with the v2.4.7 floor-pose route."
