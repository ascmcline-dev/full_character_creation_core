from __future__ import annotations

import copy
import json
from typing import Any

from .nodes import LENS_PROMPTS_V2
from .nodes_v230 import _clean_phrase, _sentences
from .nodes_v247 import _floor_kind, _single_subject_scene_v247
from .nodes_v252 import _update_summary_line
from .nodes_v246 import _rebuild_active_summary_v246
from .nodes_v254 import (
    CharacterBlueprintCreatorV254,
    CharacterPromptAssemblerV254,
    CharacterShotControlV254,
    QwenDatasetQueueV254,
)

# -----------------------------------------------------------------------------
# V2.4.15 / Studio V2.8.15
#
# Live-output corrections:
# - strict direct-back All Fours view instead of drifting to rear three-quarter
# - floor-pose camera-height blocks that make Eye Level, Low Angle, High Angle,
#   and Overhead materially different
# - Extended Puppy arms remain straight forward beyond the head and never open
#   into a lateral T/airplane position
# - staged architecture metadata includes the optional extreme-clinical body
#   validation lane while keeping it out of the default LoRA dataset
# -----------------------------------------------------------------------------

REAR_FAMILY = {"Back View", "Rear Three-Quarter Left", "Rear Three-Quarter Right"}

ALL_FOURS_POSE_V255 = _sentences(
    "one anatomically normal adult subject holds one stable quadruped hands-and-knees pose directly on the room floor",
    "both palms are flat on the same floor directly beneath the shoulders and both knees are on that floor directly beneath the hip sockets",
    "both elbows remain naturally extended, both upper arms descend from the shoulders, and both forearms remain aligned beneath the upper body",
    "the torso stays elevated with a neutral spine and one continuous connected body from the back of the head through shoulders, spine, pelvis, thighs, knees, shins, ankles, and feet",
    "the pelvis remains centered above the knees rather than twisting toward either side",
    "both shins and the tops of both feet rest naturally on the same floor behind the knees",
    "there is no table, countertop, desk, bench, bed, platform, furniture, raised slab, or elevated support beneath the subject",
)

EXTENDED_PUPPY_POSE_V255 = _sentences(
    "one anatomically normal adult subject performs one extended puppy yoga pose directly on the room floor",
    "the subject kneels face-down with exactly two knees on the floor directly below the hip sockets and the pelvis elevated above the knees",
    "the abdomen and chest face the floor while the shoulders and upper chest lower in front of the knees",
    "both arms reach straight forward from the shoulders along the same longitudinal direction as the spine",
    "the two arms remain shoulder-width apart, parallel to one another, and parallel to the body's head-to-pelvis axis",
    "both elbows are fully extended and both forearms continue forward beyond the crown of the head to two palms flat on the floor",
    "both wrists and hands are farther forward than the head; the hands are the farthest body landmarks from the knees",
    "the arms do not spread sideways, do not form a T shape, do not form airplane wings, and are never perpendicular to the spine",
    "the face points directly toward the floor and remains hidden",
    "the spine, waist, rear pelvis, backs of the thighs, calves, and tops of the feet form one continuous posterior body",
    "this is not supine, not face-up, not reclining, not a bridge pose, not a duplicated body, and not a front-back anatomical hybrid",
)


def _floor_height_v255(height: str) -> str:
    """Produce camera-height language with deliberately non-overlapping geometry."""
    mapping = {
        "Eye Level": _sentences(
            "pose-level rear camera approximately sixty to eighty centimeters above the floor",
            "the lens optical axis is horizontal and parallel to the floor with zero downward tilt",
            "the camera is not above the subject and the top surfaces of the back are not the dominant view",
            "a level floor horizon remains visible beyond the subject; this is not elevated, high-angle, top-down, or overhead",
        ),
        "Slightly Above Eye Level": _sentences(
            "rear camera approximately ninety to one hundred ten centimeters above the floor",
            "the lens tilts downward only about ten degrees while remaining behind the pelvis",
            "this is a mild elevation and not a high-angle or overhead composition",
        ),
        "Slightly Below Eye Level": _sentences(
            "rear camera approximately thirty to forty centimeters above the floor and below the rear hip line",
            "the lens tilts upward only slightly toward the pelvis",
            "the floor horizon remains low in the frame and no downward-looking view is used",
        ),
        "Low Angle": _sentences(
            "very low rear camera approximately ten to twenty centimeters above the floor and clearly below the rear hip line",
            "the lens angles upward toward the elevated pelvis by a noticeable ten to fifteen degrees",
            "the rear and underside silhouette is emphasized; this is not level, downward-looking, high-angle, or overhead",
        ),
        "High Angle": _sentences(
            "clearly elevated rear camera approximately one hundred thirty to one hundred sixty centimeters above the floor",
            "the lens angles downward about thirty to forty degrees while staying behind the pelvis",
            "this is distinctly higher than Eye Level but is not a vertical overhead view",
        ),
        "Overhead": _sentences(
            "camera positioned directly above the complete floor pose",
            "the lens points nearly straight downward in a deliberate vertical top-down composition",
            "this is the only camera-height option that uses a true overhead view",
        ),
        "Custom": "",
    }
    return mapping.get(str(height), mapping["Eye Level"])


def _rear_floor_view_v255(plan: dict[str, Any], kind: str, effective_lens: str) -> str:
    view = str(plan.get("camera_view", "Back View"))
    pose_name = "extended puppy pose" if kind == "extended_puppy" else "quadruped hands-and-knees pose"

    if view == "Back View":
        orientation = _sentences(
            f"strict direct back view of the single subject in the {pose_name}",
            "the camera is placed at the six-o'clock position directly behind the sacrum and centered exactly on the spinal midline",
            "the subject's head and forward hands point toward twelve o'clock directly away from the camera",
            "both rear hips, both buttock contours, both thighs, both knees, and both lower legs appear with balanced left-right symmetry",
            "the spine recedes straight away from the lens through the shoulders toward the crown, forward arms, and hands",
            "no left or right side plane dominates; this is not rear three-quarter, side, profile, front, or face-visible",
            "only posterior body surfaces and the back or crown of the head are visible",
        )
    else:
        side = "anatomical left" if view == "Rear Three-Quarter Left" else "anatomical right"
        orientation = _sentences(
            f"rear-dominant three-quarter view of the single subject in the {pose_name}",
            f"the camera remains behind the sacrum and is offset only twenty-five degrees toward the subject's {side} side",
            "the rear pelvis, lower back, spine, shoulder blades, and backs of the limbs remain dominant",
            "only one narrow side contour is revealed and the camera never moves around toward the face or front torso",
            "the spine still recedes away from the lens toward the forward arms and hands",
        )

    custom = _clean_phrase(plan.get("custom_camera", "")) if str(plan.get("camera_height")) == "Custom" else ""
    height = custom or _floor_height_v255(str(plan.get("camera_height", "Eye Level")))
    return _sentences(
        orientation,
        height,
        LENS_PROMPTS_V2.get(effective_lens, "rectilinear 50mm normal-lens perspective"),
        "camera distance is established before capture so the complete head, complete torso, pelvis, both arms, both hands, both knees, both shins, and both feet remain inside one uninterrupted landscape frame",
    )


def _rebuild_floor_result(result: list[Any], plan: dict[str, Any], kwargs: dict[str, Any]) -> tuple[Any, ...]:
    plan["final_shot_prompt"] = _sentences(
        plan.get("framing_prompt", ""),
        plan.get("crop_authority_prompt", ""),
        plan.get("pose_prompt", ""),
        plan.get("camera_prompt", ""),
        plan.get("expression_prompt", ""),
        plan.get("scene_prompt", ""),
        plan.get("environment_prompt", ""),
        _clean_phrase(kwargs.get("shot_suffix", "")),
    )
    summary = str(plan.get("active_settings_summary", ""))
    summary = _update_summary_line(summary, "Framing", str(plan.get("framing_prompt", "")))
    summary = _update_summary_line(summary, "Camera", str(plan.get("camera_prompt", "")))
    summary = _update_summary_line(summary, "Pose", str(plan.get("pose_prompt", "")))
    summary += "\nV2.4.15 rear floor-pose lock: direct Back View is centered at six o'clock behind the sacrum; camera heights use distinct physical elevations"
    if plan.get("rear_puppy_lock"):
        summary += "\nV2.4.15 Extended Puppy arm lock: both straight arms remain forward beyond the head, parallel to the spine, never spread sideways"
    plan["active_settings_summary"] = summary

    result[0] = plan
    result[1] = plan["final_shot_prompt"]
    result[2] = plan.get("framing_prompt", "")
    result[3] = plan.get("camera_prompt", "")
    result[4] = plan.get("pose_prompt", "")
    result[5] = plan.get("expression_prompt", "")
    result[7] = summary
    result[8] = json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True)
    result[9] = int(plan.get("recommended_width", result[9]))
    result[10] = int(plan.get("recommended_height", result[10]))
    return tuple(result)


class CharacterBlueprintCreatorV255(CharacterBlueprintCreatorV254):
    FUNCTION = "build_blueprint_v255"
    DESCRIPTION = (
        "Current Character Creator preserving all V2.4.14 controls and documenting the optional Stage 2 extreme-clinical body-validation lane, Stage 3 Qwen angle completion, and Stage 4 identity-LoRA dataset build."
    )

    def build_blueprint_v255(self, **kwargs):
        result = list(super().build_blueprint_v254(**kwargs))
        profile = copy.deepcopy(result[8])
        profile["schema"] = "CHARACTER_BLUEPRINT_V255"
        profile["schema_version"] = 25
        profile["fcc_core_version"] = "2.4.15"
        profile["fcc_studio_version"] = "2.8.15"
        architecture = copy.deepcopy(profile.get("dataset_architecture") or {})
        architecture["stage_2_optional_extreme_clinical"] = (
            "opt-in body-only extreme clinical anatomy validation; excluded from default identity-LoRA selection"
        )
        profile["dataset_architecture"] = architecture
        result[8] = profile
        result[15] = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        return tuple(result)


class CharacterShotControlV255(CharacterShotControlV254):
    FUNCTION = "build_shot_plan_v255"
    DESCRIPTION = (
        "Current Shot Control preserving all passed V2.4.14 behavior and adding strict direct-back All Fours geometry, distinct floor-pose camera elevations, and forward-only Extended Puppy arms."
    )

    def build_shot_plan_v255(self, **kwargs):
        requested_pose = str(kwargs.get("pose", ""))
        result = list(super().build_shot_plan_v254(**kwargs))
        plan = copy.deepcopy(result[0])
        plan["schema"] = "FCC_SHOT_PLAN_V255"
        plan["schema_version"] = 25
        plan["fcc_core_version"] = "2.4.15"

        kind = _floor_kind(requested_pose)
        view = str(plan.get("camera_view", kwargs.get("camera_view", "")))
        shot_type = str(plan.get("shot_type", kwargs.get("shot_type", "")))
        body_scale = shot_type not in {"Face Close-Up", "Close-Up Portrait"}

        if kind == "all_fours" and body_scale:
            plan["all_fours_floor_lock"] = True
            plan["pose_prompt"] = ALL_FOURS_POSE_V255
            if view in REAR_FAMILY:
                plan["rear_all_fours_lock"] = True
                plan["rear_floor_camera_height_lock"] = True
                effective_lens = str(plan.get("lens_effective", plan.get("lens", "50mm Normal")))
                plan["camera_prompt"] = _rear_floor_view_v255(plan, kind, effective_lens)
                plan["expression_prompt"] = ""
            plan["scene_prompt"] = _sentences(
                _single_subject_scene_v247(str(plan.get("scene_prompt", ""))),
                "both hands and both knees contact one ordinary room floor; no furniture or raised support is present",
            )

        if kind == "extended_puppy" and body_scale:
            plan["pose_prompt"] = EXTENDED_PUPPY_POSE_V255
            if view in REAR_FAMILY:
                plan["rear_puppy_lock"] = True
                plan["rear_puppy_camera_height_lock"] = True
                plan["rear_floor_camera_height_lock"] = True
                effective_lens = str(plan.get("lens_effective", plan.get("lens", "50mm Normal")))
                plan["camera_prompt"] = _rear_floor_view_v255(plan, kind, effective_lens)
                plan["expression_prompt"] = ""
            plan["scene_prompt"] = _sentences(
                _single_subject_scene_v247(str(plan.get("scene_prompt", ""))),
                "the pose occurs directly on one ordinary room floor with both straight arms reaching forward beyond the head",
            )

        if kind and body_scale:
            return _rebuild_floor_result(result, plan, kwargs)

        result[0] = plan
        result[8] = json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True)
        return tuple(result)


class CharacterPromptAssemblerV255(CharacterPromptAssemblerV254):
    FUNCTION = "assemble_prompt_v255"
    DESCRIPTION = (
        "Current prompt compiler preserving V2.4.14 garment, anatomy, marks, and crop behavior while carrying strict rear-floor view and Extended Puppy forward-arm authority into the exact Krea prompt."
    )

    def assemble_prompt_v255(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        result = list(super().assemble_prompt_v254(
            character_blueprint, shot_plan, generation_purpose, reference_label,
            trigger_word, custom_prefix, custom_suffix,
        ))
        plan = shot_plan if isinstance(shot_plan, dict) else {}
        notes = str(result[10] or "").replace("V2.4.14", "V2.4.15")
        if plan.get("rear_all_fours_lock"):
            notes += "\nAll Fours V2.4.15: Back View is a strict direct rear six-o'clock camera centered on the sacrum with symmetric rear landmarks and no side-plane drift."
        if plan.get("rear_puppy_lock"):
            notes += "\nExtended Puppy V2.4.15: both arms remain straight forward beyond the crown, parallel to the spine; Eye Level and Low Angle use separate physical camera heights."
        result[10] = notes
        try:
            sections = json.loads(result[18]) if result[18] else {}
        except Exception:
            sections = {}
        sections["routing_mode"] = str(sections.get("routing_mode", "")) + "+v255_rear_floor_camera_and_forward_arms"
        result[18] = json.dumps(sections, indent=2, ensure_ascii=False)
        result[12] = _rebuild_active_summary_v246(
            character_blueprint if isinstance(character_blueprint, dict) else {},
            plan,
            sections,
            notes,
        )
        return tuple(result)


class QwenDatasetQueueV255(QwenDatasetQueueV254):
    DESCRIPTION = (
        "Compatibility queue registered to V2.4.15. Stage 3 supports manually approved face, midshot, full-body, and body-regional references; every generated result remains manually reviewed."
    )
