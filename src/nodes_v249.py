from __future__ import annotations

import copy
import json
import re
from typing import Any

from .nodes import BUST_AUGMENTATION_PROMPTS, BUST_FIRMNESS_PROMPTS, LENS_PROMPTS_V2
from .nodes_v230 import _clean_phrase, _is_extreme_closeup_v231, _sentences
from .nodes_v241 import _is_direct_back, _is_rear_orientation
from .nodes_v243 import _is_regional
from .nodes_v246 import _rebuild_active_summary_v246, _shot_scope_v246
from .nodes_v247 import (
    EXTENDED_PUPPY,
    _floor_kind,
    _single_subject_scene_v247,
)
from .nodes_v248 import (
    ALL_FOURS,
    FORWARD_LEAN,
    CharacterBlueprintCreatorV248,
    CharacterPromptAssemblerV248,
    CharacterShotControlV248,
    QwenDatasetQueueV248,
)

# -----------------------------------------------------------------------------
# V2.4.9 / Studio V2.8.9
# Targeted open-section correction:
# - Extended Puppy rear views are anchored behind the pelvis rather than near
#   the hands or face.
# - Rear Three-Quarter Left/Right preserve rear dominance and only reveal a
#   narrow side plane.
# - Rear Extended Puppy avoids the word "forward" because several Krea-family
#   checkpoints interpreted it as a front-facing camera request.
# - Simple Dress is compiled as one complete opaque dress with a full rear
#   bodice and attached skirt, never as an "upper-body garment".
# - Standard opaque garments preserve the selected covered bust volume, shape,
#   position, firmness, and augmentation instead of normalizing the chest.
# - The support frontend is served from the extension root so the animated panel
#   and friendly labels load in current ComfyUI frontends.
# - Section A registration, Section B All-Fours lock, Section D floor framing,
#   tattoo routing, rear facial-piercing filtering, and Raw Instagram style are
#   inherited unchanged.
# -----------------------------------------------------------------------------


def _rear_puppy_pose_v249(shot_type: str) -> str:
    """Extended puppy geometry written for a camera behind the pelvis."""
    return _sentences(
        "one adult primary character in a solo extended puppy yoga pose on the floor",
        "both knees are planted directly beneath the hip sockets while both shins and the tops of both feet rest continuously on the surface",
        "the pelvis remains elevated directly above the knees and clearly separated from the heels",
        "the torso slopes downward from the elevated pelvis toward the lowered shoulders and chest",
        "both arms extend straight away from the knees along the floor, with both palms flat and the hands positioned farthest from the rear camera",
        "the chest and sternum lower toward the surface while the crown and back of the head remain low between the extended arms",
        "the facial plane is directed toward the floor and away from the rear camera",
        "the body remains one continuous aligned figure from hands through arms, shoulders, spine, pelvis, knees, shins, and feet",
    )


def _rear_puppy_camera_v249(plan: dict[str, Any], effective_lens: str) -> str:
    """Dedicated rear and rear-three-quarter camera geometry for puppy pose."""
    view = str(plan.get("camera_view", "Back View"))
    height = str(plan.get("camera_height", "Eye Level"))

    if height == "Slightly Above Eye Level":
        height_text = "the camera origin is slightly elevated above rear hip height with a mild controlled downward angle"
    elif height == "Slightly Below Eye Level":
        height_text = "the camera origin is low behind the pelvis near knee-to-hip height with a mild upward angle"
    else:
        height_text = "the camera origin is fixed behind the pelvis at rear hip height with a level horizon"

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


def _component_text_v249(profile: dict[str, Any]) -> str:
    components = profile.get("outfit_components") if isinstance(profile.get("outfit_components"), dict) else {}
    return " ".join(
        _clean_phrase(components.get(key, ""))
        for key in ("top", "bottom", "one_piece", "swimwear_top", "swimwear_bottom", "raw", "notes")
        if _clean_phrase(components.get(key, ""))
    ).lower()


def _dress_presentation_v249(profile: dict[str, Any], plan: dict[str, Any], fallback: str) -> str:
    """Compile a dress as a complete one-piece garment with explicit rear continuity."""
    components = profile.get("outfit_components") if isinstance(profile.get("outfit_components"), dict) else {}
    if str(components.get("kind", "")) != "one_piece":
        return fallback
    garment = _clean_phrase(components.get("one_piece") or components.get("raw") or "")
    low = garment.lower()
    if "dress" not in low:
        return fallback

    # Preserve custom descriptors while supplying the missing physical garment
    # topology that Krea needs to maintain the rear bodice.
    base = _sentences(
        f"wearing {garment} constructed as one complete opaque one-piece dress",
        "the fitted bodice has a visible neckline, continuous front and full rear fabric panels, two shoulder seams, short fitted sleeves, side seams, and natural waist shaping",
        "the opaque rear bodice continuously covers both shoulders, the upper back, mid-back, and waist",
        "the attached straight skirt begins at the natural waist and continues with uninterrupted fabric to a knee-length hem",
    )
    if _is_rear_orientation(plan):
        return _sentences(
            base,
            "from behind, the complete rear bodice, both sleeves, shoulder seams, side seams, waist connection, attached skirt, and knee-length rear hem are visibly connected as one continuous dress",
        )
    return _sentences(
        base,
        "the bodice and attached skirt remain visibly connected around the complete waist as one continuous garment",
    )


def _covered_bust_effect_v249(profile: dict[str, Any], plan: dict[str, Any]) -> str:
    """Describe only the externally visible covered silhouette under clothing."""
    if profile.get("presentation_mode") != "Clothed Character":
        return ""
    if str(profile.get("resolved_chest_anatomy", profile.get("chest_anatomy_selection", ""))) != "Bust Anatomy — Use Bust Controls":
        return ""
    if _is_rear_orientation(plan):
        return ""
    scope = _shot_scope_v246(plan)
    if scope not in {"chest_up", "waist_up", "three_quarter", "full", "other"}:
        return ""

    components_text = _component_text_v249(profile)
    # No garment reaching the chest means there is no covered silhouette route.
    components = profile.get("outfit_components") if isinstance(profile.get("outfit_components"), dict) else {}
    upper_present = bool(_clean_phrase(
        components.get("top") or components.get("one_piece") or components.get("swimwear_top") or components.get("raw") or ""
    ))
    if not upper_present:
        return ""

    base = _clean_phrase(profile.get("bust_clothed_authority_prompt", ""))
    if not base:
        size = str(profile.get("bust_size", "Unspecified"))
        base = f"the covered chest silhouette preserves the selected {size.lower()} bust volume" if size != "Unspecified" else ""
    # Remove the old weak garment tail and convert explicit anatomy labels into
    # covered-contour language suitable for clothed images.
    base = re.sub(r"[.;]?\s*the garment follows.*$", "", base, flags=re.I).strip(" ,.;")
    base = base.replace("breast shape", "covered bust contour")
    base = base.replace("breast placement", "covered bust placement")
    base = base.replace("breast roots", "covered bust roots")
    base = base.replace("chest tissue", "covered contour")

    firmness = str(profile.get("bust_firmness", "Unspecified"))
    augmentation = str(profile.get("bust_augmentation", "Unspecified"))
    firmness_text = _clean_phrase(BUST_FIRMNESS_PROMPTS.get(firmness, "")) if firmness != "Unspecified" else ""
    augmentation_text = _clean_phrase(BUST_AUGMENTATION_PROMPTS.get(augmentation, "")) if augmentation != "Unspecified" else ""
    replacements = {
        "chest tissue": "covered silhouette",
        "implants": "augmented contour",
        "implant footprint": "augmented base",
        "chest structure": "covered contour",
        "round high-profile augmentation": "round high-profile augmented contour",
        "breast roots": "covered bust roots",
    }
    for old, new in replacements.items():
        firmness_text = firmness_text.replace(old, new)
        augmentation_text = augmentation_text.replace(old, new)

    if any(token in components_text for token in ("sports bra", "compression", "compressive")):
        garment_behavior = (
            "the selected athletic compression garment supports the chest and may moderately reduce visible projection as an intentional garment effect"
        )
    elif any(token in components_text for token in ("bra", "bikini", "swimwear", "lingerie")):
        garment_behavior = (
            "the supportive fitted garment follows and supports the complete selected covered volume without reducing the selected bust size"
        )
    else:
        garment_behavior = (
            "the opaque garment is normally fitted and non-compressive across the chest; its fabric follows and preserves the complete selected covered volume rather than flattening or minimizing it"
        )

    return _sentences(
        base,
        firmness_text,
        augmentation_text,
        garment_behavior,
        "the visible result is a fully covered external garment silhouette; nipple and areola details are not described through the clothing",
    )


def _replace_weak_bust_v249(body: str, replacement: str) -> str:
    if not replacement:
        return body
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", str(body or "")) if s.strip()]
    kept = []
    for sentence in sentences:
        low = sentence.lower()
        if "bust size subtly shapes" in low or "bust size subtly shapes the covered" in low:
            continue
        kept.append(sentence)
    return _sentences(*kept, replacement)


def _replace_prompt_section_v249(prompt: str, old: str, new: str) -> str:
    text = str(prompt or "")
    old = str(old or "")
    if old and old in text:
        return text.replace(old, new, 1)
    return _sentences(text, new) if new else text


class CharacterBlueprintCreatorV249(CharacterBlueprintCreatorV248):
    FUNCTION = "build_blueprint_v249"
    DESCRIPTION = (
        "Current Character Creator paired with the v2.4.9 rear Extended Puppy lock, complete-dress continuity, "
        "covered-bust silhouette fidelity, and visible support panel."
    )

    def build_blueprint_v249(self, **kwargs):
        result = list(super().build_blueprint_v248(**kwargs))
        profile = copy.deepcopy(result[8])
        profile["schema"] = "CHARACTER_BLUEPRINT_V249"
        profile["schema_version"] = 20
        profile["presentation_summary"] = str(profile.get("presentation_summary", "")) + (
            "\nClothed bust fidelity: standard opaque garments preserve selected covered bust volume, contour, placement, firmness, and augmentation; only intentional sports-compression garments may reduce projection."
            "\nOne-piece dress continuity: dresses use a complete rear bodice connected to the attached skirt."
        )
        result[8] = profile
        result[15] = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        result[21] = profile["presentation_summary"]
        return tuple(result)


class CharacterShotControlV249(CharacterShotControlV248):
    FUNCTION = "build_shot_plan_v249"
    DESCRIPTION = (
        "Current Shot Control with Section A registration locked, Section B rear All-Fours inherited, "
        "Section C rear Extended Puppy views anchored behind the pelvis, and Section D framing preserved."
    )

    def build_shot_plan_v249(self, **kwargs):
        requested_pose = str(kwargs.get("pose", ""))
        result = list(super().build_shot_plan_v248(**kwargs))
        plan = copy.deepcopy(result[0])
        plan["schema"] = "FCC_SHOT_PLAN_V249"
        plan["schema_version"] = 18

        kind = _floor_kind(requested_pose)
        view = str(plan.get("camera_view", ""))
        rear_puppy = kind == "extended_puppy" and view in {
            "Back View",
            "Rear Three-Quarter Left",
            "Rear Three-Quarter Right",
        }

        if rear_puppy and not _is_regional(plan) and not _is_extreme_closeup_v231(plan):
            effective_lens = str(plan.get("lens_effective", plan.get("lens", "50mm Normal")))
            shot_type = str(plan.get("shot_type", kwargs.get("shot_type", "Three-Quarter Body")))
            plan["rear_puppy_lock"] = True
            plan["pose_prompt"] = _rear_puppy_pose_v249(shot_type)
            plan["camera_prompt"] = _rear_puppy_camera_v249(plan, effective_lens)
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
        summary = re.sub(r"\nRear-puppy lock:.*$", "", summary, flags=re.S).rstrip()
        if plan.get("rear_puppy_lock"):
            summary += (
                "\nRear-puppy lock: camera anchored behind pelvis; rear surfaces dominant; "
                "hips nearest; hands farthest; face directed toward floor"
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


class CharacterPromptAssemblerV249(CharacterPromptAssemblerV248):
    FUNCTION = "assemble_prompt_v249"
    DESCRIPTION = (
        "Current visibility compiler with rear Extended Puppy orientation lock, complete one-piece dress topology, "
        "and non-compressive covered-bust silhouette fidelity."
    )

    def assemble_prompt_v249(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan = shot_plan if isinstance(shot_plan, dict) else {}
        result = list(super().assemble_prompt_v248(
            character_blueprint, shot_plan, generation_purpose, reference_label,
            trigger_word, custom_prefix, custom_suffix,
        ))

        try:
            sections = json.loads(result[18]) if result[18] else {}
        except Exception:
            sections = {}

        notes = str(result[10] or "")
        changed = False

        if plan.get("rear_puppy_lock"):
            notes += (
                "\nRear Extended Puppy compiler V2.4.9: camera is anchored behind the pelvis; "
                "rear body surfaces stay dominant, the hips are nearest, the hands are farthest, "
                "and the facial plane remains directed toward the floor."
            )
            sections["routing_mode"] = "rear_puppy_lock_v249"
            sections["rear_puppy_lock"] = True

        standard_clothed = (
            profile.get("presentation_mode") == "Clothed Character"
            and not _is_extreme_closeup_v231(plan)
            and not _is_regional(plan)
        )
        if standard_clothed:
            old_presentation = str(sections.get("visible_presentation", result[3] or ""))
            new_presentation = _dress_presentation_v249(profile, plan, old_presentation)
            if new_presentation != old_presentation:
                sections["visible_presentation"] = new_presentation
                result[3] = new_presentation
                result[16] = new_presentation
                changed = True
                notes += (
                    "\nOne-piece dress compiler V2.4.9: full front and rear bodice panels, shoulder seams, sleeves, side seams, waist connection, attached skirt, and knee-length hem remain one continuous dress."
                )

            old_body = str(sections.get("visible_body", ""))
            bust_effect = _covered_bust_effect_v249(profile, plan)
            new_body = _replace_weak_bust_v249(old_body, bust_effect)
            if new_body != old_body:
                sections["visible_body"] = new_body
                changed = True
                notes += (
                    "\nCovered-bust compiler V2.4.9: standard opaque garments preserve selected covered volume, contour, vertical placement, firmness, and augmentation without exposing nipple or areola detail."
                )

            if changed:
                purpose = str(sections.get("purpose", "A realistic camera photograph"))
                shot = str(sections.get("shot_scene", result[2] or ""))
                character = str(sections.get("primary_character", result[19] or ""))
                presentation = str(sections.get("visible_presentation", result[3] or ""))
                body = str(sections.get("visible_body", ""))
                tan = str(sections.get("visible_tan_skin_variation", ""))
                marks = str(sections.get("visible_marks", result[4] or ""))
                old_final = str(sections.get("final_prompt", result[13] or ""))

                if generation_purpose.startswith("Krea"):
                    final_prompt = _sentences(
                        trigger_word, custom_prefix, purpose, shot, character,
                        presentation, body, tan, marks, custom_suffix,
                    )
                    result[0] = final_prompt
                else:
                    final_prompt = old_final
                    old_presentation = str(result[3] or "") if not sections.get("visible_presentation") else ""
                    final_prompt = _replace_prompt_section_v249(final_prompt, old_presentation, presentation)
                    final_prompt = _replace_prompt_section_v249(final_prompt, old_body, body)
                    result[1] = final_prompt

                sections["final_prompt"] = final_prompt
                sections["routing_mode"] = "standard_garment_and_bust_fidelity_v249"
                result[13] = final_prompt

        result[10] = notes
        result[18] = json.dumps(sections, indent=2, ensure_ascii=False)
        if changed:
            result[12] = _rebuild_active_summary_v246(profile, plan, sections, notes)
        return tuple(result)


class QwenDatasetQueueV249(QwenDatasetQueueV248):
    DESCRIPTION = "Current FCC Qwen dataset queue paired with the v2.4.9 rear-pose, dress-continuity, and clothed-bust fidelity compiler."
