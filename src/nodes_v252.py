from __future__ import annotations

import copy
import json
import re
from typing import Any

from .nodes_v230 import _clean_phrase, _sentences
from .nodes_v241 import _is_rear_orientation
from .nodes_v246 import _rebuild_active_summary_v246, _shot_scope_v246
from .nodes_v247 import EXTENDED_PUPPY, _floor_kind, _single_subject_scene_v247
from .nodes_v249 import _rear_puppy_pose_v249
from .nodes_v250 import (
    CharacterBlueprintCreatorV250,
    CharacterPromptAssemblerV250,
    CharacterShotControlV250,
    QwenDatasetQueueV250,
)
from .nodes import LENS_PROMPTS_V2

# -----------------------------------------------------------------------------
# V2.4.12 / Studio V2.8.12
# Targeted live-test correction build:
# - Face Close-Up uses a hard neck/trapezius lower boundary and suppresses
#   full-body pose wording and complete-garment construction leakage.
# - Rear Extended Puppy keeps the locked behind-pelvis geometry while every
#   Camera Height selection receives distinct elevation authority.
# - Opaque fitted tank/crop presets use dense matte optical-opacity wording,
#   explicit hem placement, and close-fitted torso behavior.
# - Covered bust volume is communicated through garment silhouette rather than
#   transparency or extreme fabric stretching.
# - A single visible tattoo receives a concise visible-only count/location lock
#   so a combined design is not split, mirrored, or relocated.
# - All prior locked garment presence, dress continuity, rear piercing routing,
#   crop-aware visibility, Raw Instagram, and skin-tone stability are inherited.
# -----------------------------------------------------------------------------

FACE_CLOSE_FRAMING_V252 = _sentences(
    "tight facial close-up composition with the complete head, complete hairline, and visible ear edges inside the frame",
    "the face occupies approximately seventy to eighty percent of the image height",
    "the lower frame ends at the base of the neck and upper trapezius line",
    "only narrow upper-shoulder edges may appear at the extreme lower corners",
    "the chest, bust, cleavage, collarbone field, upper torso, upper arms, and armpits remain outside the frame",
    "show only the portion of long hair naturally visible inside this close crop and do not widen the framing to display the full hair length",
)

FACE_CLOSE_CROP_AUTHORITY_V252 = _sentences(
    "mandatory face-close crop authority",
    "the face fills most of the image and the frame stops at the base of the neck and upper trapezius line",
    "do not include the chest, bust, cleavage, upper torso, upper arms, armpits, waist, hips, or full garment body",
    "do not zoom out to demonstrate the standing pose, arm position, outfit length, or complete hair length",
)

FACE_CLOSE_COMPACT_POSE_V252 = _sentences(
    "head upright with a natural neck position and relaxed upper trapezius line",
    "the arms and torso remain outside the face-close frame",
)

DENSE_OPAQUE_MATERIAL_V252 = (
    "dense midweight double-layer matte cotton-spandex jersey with uniform optical opacity under direct light, backlight, and normal fabric tension"
)

OPAQUE_FITTED_TANK_V252 = (
    "solid fitted tank top with a normal neckline, two secure shoulder straps, complete chest coverage, and continuous front and rear fabric panels; "
    f"constructed from {DENSE_OPAQUE_MATERIAL_V252}; "
    "close fitted from the neckline through the covered bust, ribs, waist, and finished lower hem at the natural waist; "
    "the torso panel remains smooth with only minimal natural tension folds and does not hang loosely, billow, become translucent, or turn sheer"
)

OPAQUE_FITTED_CROP_V252 = (
    "solid fitted cropped tank top with a round neckline, two secure wide shoulder straps, complete chest coverage, and continuous front and rear fabric panels; "
    f"constructed from {DENSE_OPAQUE_MATERIAL_V252}; "
    "close fitted from the neckline through the covered bust and ribs to a level finished hem at the lower ribcage clearly above the navel; "
    "a narrow strip of midriff remains visible below the hem; the torso panel remains smooth with only minimal natural tension folds and does not hang loosely, billow, become translucent, or turn sheer"
)


def _update_summary_line(summary: str, label: str, value: str) -> str:
    lines = str(summary or "").splitlines()
    prefix = f"{label}:"
    replaced = False
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            lines[index] = f"{prefix} {value}"
            replaced = True
            break
    if not replaced:
        lines.append(f"{prefix} {value}")
    return "\n".join(lines)


def _rear_puppy_camera_v252(plan: dict[str, Any], effective_lens: str) -> str:
    """Rear puppy geometry with independent camera-height authority."""
    view = str(plan.get("camera_view", "Back View"))
    height = str(plan.get("camera_height", "Eye Level"))

    height_text = {
        "Eye Level": _sentences(
            "the camera origin is behind the pelvis at rear hip height",
            "the lens axis remains level with a level horizon and no elevated, downward-looking, high-angle, or overhead perspective",
        ),
        "Slightly Above Eye Level": _sentences(
            "the camera origin is slightly above rear hip height behind the pelvis",
            "the lens angles only mildly downward and does not become a high-angle or top-down view",
        ),
        "Slightly Below Eye Level": _sentences(
            "the camera origin is low behind the pelvis near knee-to-hip height",
            "the lens angles only mildly upward and the floor remains close to the camera",
        ),
        "High Angle": _sentences(
            "the camera origin is clearly elevated behind the pelvis above rear hip height",
            "the lens angles distinctly downward while remaining behind the pelvis rather than moving over the hands or face",
        ),
        "Low Angle": _sentences(
            "the camera origin is just above the floor behind the pelvis and clearly below the rear hip line",
            "the lens angles upward toward the elevated pelvis with no downward-looking or overhead perspective",
        ),
        "Overhead": _sentences(
            "the camera origin is high above and behind the rear pelvis",
            "the lens points strongly downward in a deliberate top-down rear composition while the pelvis remains the rear anchor",
        ),
        "Custom": _clean_phrase(plan.get("custom_camera", "")) or _sentences(
            "the camera origin remains behind the pelvis",
            "apply the custom camera-height direction without moving toward the hands or front of the face",
        ),
    }.get(height, _sentences(
        "the camera origin is behind the pelvis at rear hip height",
        "the lens axis remains level with no overhead perspective",
    ))

    if view == "Back View":
        orientation = _sentences(
            "strict direct rear view photographed from behind the pelvis",
            "the rear hips, sacrum, and lower back form the nearest central foreground",
            "the camera centerline follows the spine away from the lens toward the shoulders, crown of the head, extended arms, and hands",
            "the hands are the farthest body landmarks from the camera",
            "only posterior body surfaces and the crown and back of the head are visible",
            "the face, eyes, nose, mouth, front chest, and front torso remain hidden by the body orientation",
        )
    else:
        side = "anatomical left" if view == "Rear Three-Quarter Left" else "anatomical right"
        orientation = _sentences(
            f"rear three-quarter view photographed from behind the pelvis with the camera offset only twenty to thirty degrees toward the subject's {side} side",
            "the rear hips, sacrum, lower back, and back remain the dominant visible surfaces",
            "only a narrow side contour of the torso and limbs is revealed while the rear view remains primary",
            "the camera line continues from the rear pelvis along the spine toward the shoulders, crown of the head, extended arms, and hands",
            "the hands remain the farthest body landmarks from the camera",
            "the facial plane remains directed toward the floor and away from the lens",
            "the camera does not move around toward the hands or the front of the face",
        )

    return _sentences(
        orientation,
        height_text,
        LENS_PROMPTS_V2.get(effective_lens, "rectilinear 50mm normal-lens perspective"),
        "camera distance is established before capture so both hands, both arms, the complete torso, pelvis, both knees, both shins, both feet, and the complete head remain inside one uninterrupted frame",
    )


def _tank_variant_v252(profile: dict[str, Any]) -> str:
    components = profile.get("outfit_components") if isinstance(profile.get("outfit_components"), dict) else {}
    top = _clean_phrase(components.get("top") or components.get("raw") or "").lower()
    preset = str(profile.get("outfit_preset", profile.get("preset_outfit_if_selected", ""))).lower()
    if "crop" in top or "high-hem" in top or "crop" in preset:
        return "crop"
    if "tank top" in top or "tank" in preset:
        return "tank"
    return ""


def _tank_presentation_v252(profile: dict[str, Any], plan: dict[str, Any], fallback: str) -> str:
    variant = _tank_variant_v252(profile)
    if not variant or profile.get("presentation_mode") != "Clothed Character":
        return fallback
    scope = _shot_scope_v246(plan)
    if scope == "face":
        return _sentences(
            "only a tiny opaque neckline or shoulder-strap edge may appear at the extreme lower corners of the face-close frame",
            "the garment body, chest, bust, collarbone field, upper torso, and upper arms remain outside the frame",
            "do not widen the composition to show the top's length or hem",
        )
    garment = OPAQUE_FITTED_CROP_V252 if variant == "crop" else OPAQUE_FITTED_TANK_V252
    if scope == "head_shoulders":
        return _sentences(
            f"the neckline, shoulder straps, and only the uppermost opaque fabric panel of {garment} are visible",
            "the dense matte fabric remains uniformly opaque and close fitted",
        )
    return _sentences(
        f"wearing {garment}",
        "the complete visible garment remains solid, matte, uniformly opaque, and close fitted across every visible covered region",
    )


def _refine_tank_bust_body_v252(body: str, profile: dict[str, Any]) -> str:
    if not _tank_variant_v252(profile):
        return body
    old = (
        "the opaque garment is normally fitted and non-compressive across the chest; its fabric follows and preserves the complete selected covered volume rather than flattening or minimizing it"
    )
    new = (
        "the garment's cut and outward covered silhouette preserve the complete selected bust volume, contour, placement, and projection rather than flattening or minimizing it; "
        "this volume is communicated through the dense opaque garment shape rather than transparency, extreme stretching, or visible anatomical surface detail"
    )
    return str(body or "").replace(old, new)


def _anatomical_location_v252(location: str) -> str:
    text = str(location or "").strip()
    low = text.lower()
    if low.startswith("right "):
        return "the subject's anatomical right " + text[6:].lower()
    if low.startswith("left "):
        return "the subject's anatomical left " + text[5:].lower()
    return text.lower()


def _single_visible_tattoo_v252(sections: dict[str, Any]) -> str:
    records = sections.get("visible_tattoo_records")
    if not isinstance(records, list) or len(records) != 1:
        return str(sections.get("visible_marks", "") or "")
    record = records[0] if isinstance(records[0], dict) else {}
    if int(record.get("quantity", 1) or 1) != 1:
        return str(sections.get("visible_marks", "") or "")
    location = _anatomical_location_v252(str(record.get("location", "")))
    description = _clean_phrase(record.get("description") or record.get("raw") or "tattoo")
    description = re.sub(r"\bwith a orchid\b", "with an orchid", description, flags=re.I)
    opposite = ""
    low = str(record.get("location", "")).lower()
    if low.startswith("right "):
        opposite = "the subject's anatomical left arm and all other visible skin remain tattoo-free"
    elif low.startswith("left "):
        opposite = "the subject's anatomical right arm and all other visible skin remain tattoo-free"
    else:
        opposite = "all other visible skin remains tattoo-free"
    return _sentences(
        f"exactly one visible permanent tattoo appears in the entire image: one single combined tattoo design located only on {location}, depicting {description}",
        opposite,
        "the tattoo is not split into separate designs, mirrored, duplicated, or relocated",
    )


class CharacterBlueprintCreatorV252(CharacterBlueprintCreatorV250):
    FUNCTION = "build_blueprint_v252"
    DESCRIPTION = (
        "Current Character Creator with all v2.4.10 identity, garment, mark, and complexion behavior, "
        "plus dense opaque tank/crop preset construction for the v2.4.12 test release."
    )

    def build_blueprint_v252(self, **kwargs):
        result = list(super().build_blueprint_v250(**kwargs))
        profile = copy.deepcopy(result[8])

        # Apply the revised preset text only to the current V252 result. Do not
        # mutate the shared PRESET_OUTFITS table because older locked-version
        # regression tests and legacy classes must remain byte-for-byte in behavior.
        components = copy.deepcopy(profile.get("outfit_components") or {})
        old_top = _clean_phrase(components.get("top", ""))
        selected_preset = str(kwargs.get("preset_outfit_if_selected", ""))
        new_top = ""
        if selected_preset == "Opaque Fitted Tank Top":
            new_top = OPAQUE_FITTED_TANK_V252
        elif selected_preset == "High-Hem Crop Top and Daisy Dukes":
            new_top = OPAQUE_FITTED_CROP_V252
        if new_top and old_top:
            components["top"] = new_top
            profile["outfit_components"] = components
            for key, value in list(profile.items()):
                if isinstance(value, str) and old_top in value:
                    profile[key] = value.replace(old_top, new_top)
            for index, value in enumerate(result):
                if isinstance(value, str) and old_top in value:
                    result[index] = value.replace(old_top, new_top)

        profile["schema"] = "CHARACTER_BLUEPRINT_V252"
        profile["schema_version"] = 22
        profile["presentation_summary"] = str(profile.get("presentation_summary", "")) + (
            "\nV2.4.12 garment test route: opaque tank and crop presets use dense matte optical-opacity, explicit hem placement, and close-fitted torso construction."
        )
        result[8] = profile
        result[15] = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        result[21] = profile["presentation_summary"]
        return tuple(result)


class CharacterShotControlV252(CharacterShotControlV250):
    FUNCTION = "build_shot_plan_v252"
    DESCRIPTION = (
        "Current Shot Control with a strict Face Close crop and full Camera Height authority for locked rear Extended Puppy views."
    )

    def build_shot_plan_v252(self, **kwargs):
        requested_pose = str(kwargs.get("pose", ""))
        result = list(super().build_shot_plan_v250(**kwargs))
        plan = copy.deepcopy(result[0])
        plan["schema"] = "FCC_SHOT_PLAN_V252"
        plan["schema_version"] = 22

        if str(plan.get("shot_type", "")) == "Face Close-Up":
            plan["face_close_lock"] = True
            plan["framing_prompt"] = FACE_CLOSE_FRAMING_V252
            body_pose_tokens = (
                "standing", "seated", "leaning", "walking", "arms relaxed", "arms loosely crossed",
                "hand at waist", "crossed-leg", "weight shift", "both arms resting",
            )
            inherited_pose = str(plan.get("pose_prompt", "") or "")
            if any(token in inherited_pose.lower() for token in body_pose_tokens):
                plan["pose_prompt"] = FACE_CLOSE_COMPACT_POSE_V252
            else:
                plan["pose_prompt"] = _sentences(
                    inherited_pose,
                    "the chest and torso remain outside the tight face-close frame",
                )
            plan["crop_authority_prompt"] = FACE_CLOSE_CROP_AUTHORITY_V252

        rear_puppy = (
            _floor_kind(requested_pose) == "extended_puppy"
            and str(plan.get("camera_view", "")) in {"Back View", "Rear Three-Quarter Left", "Rear Three-Quarter Right"}
            and plan.get("rear_puppy_lock")
        )
        if rear_puppy:
            effective_lens = str(plan.get("lens_effective", plan.get("lens", "50mm Normal")))
            plan["pose_prompt"] = _rear_puppy_pose_v249(str(plan.get("shot_type", "Three-Quarter Body")))
            plan["camera_prompt"] = _rear_puppy_camera_v252(plan, effective_lens)
            plan["scene_prompt"] = _single_subject_scene_v247(str(plan.get("scene_prompt", "")))
            plan["expression_prompt"] = ""
            plan["rear_puppy_camera_height_lock"] = True

        plan["final_shot_prompt"] = _sentences(
            plan.get("framing_prompt", ""),
            plan.get("crop_authority_prompt", ""),
            plan.get("camera_prompt", ""),
            plan.get("pose_prompt", ""),
            plan.get("expression_prompt", ""),
            plan.get("scene_prompt", ""),
            plan.get("environment_prompt", ""),
            _clean_phrase(kwargs.get("shot_suffix", "")),
        )

        summary = str(plan.get("active_settings_summary", ""))
        summary = _update_summary_line(summary, "Framing", str(plan.get("framing_prompt", "")))
        summary = _update_summary_line(summary, "Camera", str(plan.get("camera_prompt", "")))
        summary = _update_summary_line(summary, "Pose", str(plan.get("pose_prompt", "")))
        if plan.get("face_close_lock"):
            summary += "\nFace-close lock: frame stops at base of neck / upper trapezius; chest, bust, torso, upper arms, full garment body, and complete hair length stay outside the crop"
        if plan.get("rear_puppy_camera_height_lock"):
            summary += f"\nRear-puppy camera-height lock: selected height '{plan.get('camera_height')}' is applied independently while the camera remains behind the pelvis"
        plan["active_settings_summary"] = summary

        result[0] = plan
        result[1] = plan["final_shot_prompt"]
        result[2] = plan.get("framing_prompt", "")
        result[3] = plan.get("camera_prompt", "")
        result[4] = plan.get("pose_prompt", "")
        result[5] = plan.get("expression_prompt", "")
        result[7] = summary
        result[8] = json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True)
        return tuple(result)


class CharacterPromptAssemblerV252(CharacterPromptAssemblerV250):
    FUNCTION = "assemble_prompt_v252"
    DESCRIPTION = (
        "Current compiler with Face Close crop isolation, rear-puppy camera-height authority, dense opaque tank/crop material behavior, "
        "covered-silhouette bust fidelity, and concise visible-only single-tattoo exactness."
    )

    def assemble_prompt_v252(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan = shot_plan if isinstance(shot_plan, dict) else {}
        result = list(super().assemble_prompt_v250(
            character_blueprint, shot_plan, generation_purpose, reference_label,
            trigger_word, custom_prefix, custom_suffix,
        ))
        try:
            sections = json.loads(result[18]) if result[18] else {}
        except Exception:
            sections = {}

        notes = str(result[10] or "").replace("V2.4.10", "V2.4.12")
        changed = False

        if plan.get("face_close_lock"):
            sections["shot_scene"] = str(plan.get("final_shot_prompt", result[2] or ""))
            sections["face_close_lock"] = True
            result[2] = sections["shot_scene"]
            result[15] = FACE_CLOSE_CROP_AUTHORITY_V252
            notes += "\nFace Close compiler V2.4.12: lower frame stops at the base of the neck / upper trapezius and suppresses standing-arm, complete-garment, chest, bust, torso, and full-hair-length framing leakage."
            changed = True

        old_presentation = str(sections.get("visible_presentation", result[3] or ""))
        new_presentation = _tank_presentation_v252(profile, plan, old_presentation)
        if new_presentation != old_presentation:
            sections["visible_presentation"] = new_presentation
            result[3] = new_presentation
            result[16] = new_presentation
            notes += "\nOpaque tank/crop compiler V2.4.12: dense matte double-layer material, uniform optical opacity, close-fitted torso construction, and explicit standard/crop hem placement are active."
            changed = True

        old_body = str(sections.get("visible_body", "") or "")
        new_body = _refine_tank_bust_body_v252(old_body, profile)
        if new_body != old_body:
            sections["visible_body"] = new_body
            notes += "\nCovered tank/crop silhouette V2.4.12: selected bust volume is expressed through the outward opaque garment silhouette rather than transparency or extreme fabric stretching."
            changed = True

        old_marks = str(sections.get("visible_marks", result[4] or "") or "")
        new_marks = _single_visible_tattoo_v252(sections)
        if new_marks != old_marks:
            sections["visible_marks"] = new_marks
            result[4] = new_marks
            notes += "\nSingle visible tattoo exactness V2.4.12: one combined visible design is kept on its anatomical side and is not split, mirrored, duplicated, or relocated."
            changed = True

        if plan.get("rear_puppy_camera_height_lock"):
            sections["rear_puppy_camera_height"] = str(plan.get("camera_height", ""))
            notes += "\nRear Extended Puppy camera-height compiler V2.4.12: selected camera elevation is applied independently while the locked behind-pelvis orientation remains intact."

        if changed:
            purpose = str(sections.get("purpose", "A realistic camera photograph"))
            shot = str(sections.get("shot_scene", result[2] or ""))
            character = str(sections.get("primary_character", result[19] or ""))
            presentation = str(sections.get("visible_presentation", result[3] or ""))
            body = str(sections.get("visible_body", ""))
            tan = str(sections.get("visible_tan_skin_variation", ""))
            marks = str(sections.get("visible_marks", result[4] or ""))

            if generation_purpose.startswith("Krea"):
                final_prompt = _sentences(
                    trigger_word, custom_prefix, purpose, shot, character,
                    presentation, body, tan, marks, custom_suffix,
                )
                result[0] = final_prompt
            else:
                final_prompt = str(result[13] or result[1] or "")
                for old, new in ((old_presentation, new_presentation), (old_body, new_body), (old_marks, new_marks)):
                    if old and old in final_prompt and old != new:
                        final_prompt = final_prompt.replace(old, new, 1)
                result[1] = final_prompt

            sections["final_prompt"] = final_prompt
            sections["routing_mode"] = str(sections.get("routing_mode", "")) + "+v252_test_fixes"
            result[13] = final_prompt

        result[10] = notes
        result[18] = json.dumps(sections, indent=2, ensure_ascii=False)
        result[12] = _rebuild_active_summary_v246(profile, plan, sections, notes)
        return tuple(result)


class QwenDatasetQueueV252(QwenDatasetQueueV250):
    DESCRIPTION = (
        "Current FCC Qwen dataset queue paired with the v2.4.12 Face Close, rear-puppy camera-height, opaque tank/crop, and visible tattoo exactness test compiler."
    )
