from __future__ import annotations

import copy
import json
import re
from typing import Any

from .nodes_v230 import _clean_phrase, _sentences
from .nodes_v241 import _is_rear_orientation
from .nodes_v246 import _rebuild_active_summary_v246, _shot_scope_v246
from .nodes_v247 import _floor_kind, _single_subject_scene_v247
from .nodes_v252 import (
    CharacterBlueprintCreatorV252,
    CharacterPromptAssemblerV252,
    CharacterShotControlV252,
    QwenDatasetQueueV252,
    DENSE_OPAQUE_MATERIAL_V252,
    OPAQUE_FITTED_CROP_V252,
    OPAQUE_FITTED_TANK_V252,
    _refine_tank_bust_body_v252,
    _tank_presentation_v252,
    _tank_variant_v252,
    _update_summary_line,
)
from .nodes import LENS_PROMPTS_V2

# -----------------------------------------------------------------------------
# V2.4.13 / Studio V2.8.13
# Quality-first correction and dataset architecture build.
#
# Locked v2.4.12 successes are inherited. This file changes only confirmed
# live-test failures:
# - higher Face Close framing with a clear crown margin and no garment/chest
# - simplified Extended Puppy pose anatomy before view/elevation instructions
# - dedicated extra-low-rise Daisy Duke cutoff construction
# - view-aware anatomical tattoo-side wording and full-back coverage authority
# - piercing construction that passes through tissue instead of lying on skin
# - complete-head authority for Waist-Up and Three-Quarter Body crops
# -----------------------------------------------------------------------------

FACE_CLOSE_FRAMING_V253 = _sentences(
    "tight facial close-up with a small clear margin above the complete crown of the head",
    "the complete crown, complete forehead hairline, both sides of the head, and visible ear edges remain inside the frame",
    "the face occupies approximately seventy to eighty percent of the image height",
    "the camera framing is centered higher on the face rather than lower on the shoulders",
    "the lower center edge ends exactly at the base of the neck",
    "only an extremely narrow trace of upper trapezius may appear in the two bottom corners",
    "the clavicle field, shoulders as broad forms, chest, bust, cleavage, upper torso, upper arms, armpits, garment neckline, garment straps, and garment body remain outside the frame",
    "show only the portion of long hair naturally present inside the close crop and never widen the composition to display its full length",
)

FACE_CLOSE_CROP_AUTHORITY_V253 = _sentences(
    "mandatory face-close boundary",
    "preserve clear image margin above the complete crown and do not crop the top of the hair",
    "the lower center edge contains neck only and stops before the clavicles",
    "do not spend lower-frame space on shoulders, upper chest, garment straps, neckline, garment body, arms, torso, waist, or hips",
    "do not zoom out to demonstrate pose, outfit construction, or complete hair length",
)

FACE_CLOSE_POSE_V253 = _sentences(
    "head upright with a natural neck position",
    "facial plane follows the selected camera view",
    "the body and arms remain outside the frame",
)

WAIST_UP_FRAMING_V253 = _sentences(
    "complete-head waist-up midshot with clear margin above the complete crown",
    "the complete head, hair, neck, both shoulders, torso, arms, natural waist, and waistband are inside the frame",
    "camera distance is increased as necessary to preserve both the complete head and the lower waist boundary",
    "never crop the crown, forehead, or chin in order to include the waist",
)

THREE_QUARTER_FRAMING_V253 = _sentences(
    "complete-head three-quarter-body composition from clear margin above the crown through both knees and upper calves",
    "the complete head, hair, torso, both arms, pelvis, both knees, and upper calves remain inside the frame",
    "camera distance is established before capture and widened as necessary",
    "never crop the crown or convert the requested composition into a torso-only portrait",
)

DAISY_DUKE_BOTTOM_V253 = (
    "extra-low-rise rigid distressed blue denim cutoff micro-shorts in classic Daisy Duke style; "
    "the denim waistband rides very low across the upper hips at or slightly below the pelvic-bone line; "
    "a metal button, zipper fly, belt loops, front pockets, rear patch pockets, side seams, and two clearly separate short leg openings remain visible when their view is in frame; "
    "the raw-cut leg openings rise extremely high over the upper thighs with heavy irregular frayed denim threads; "
    "from rear and rear-three-quarter views the extremely short cutoff hem reveals the lower buttock curves below the frayed edges; "
    "the shorts remain rigid woven denim and never become leggings, yoga pants, compression bottoms, knit shorts, bicycle shorts, high-waisted shorts, or full-length pants"
)

EXTENDED_PUPPY_POSE_V253 = _sentences(
    "one anatomically normal adult subject performs one extended puppy yoga pose on the floor",
    "the subject is kneeling face-down with exactly two knees on the floor directly below the hip sockets",
    "both shins and the tops of both feet rest on the floor behind the knees",
    "the pelvis remains elevated above the knees and clearly separated from the heels",
    "the abdomen faces the floor and the torso slopes downward from the elevated pelvis toward the lowered chest and shoulders",
    "both arms extend straight along the floor beyond the head with both palms flat",
    "the hands are farther from the knees than the head and shoulders",
    "the face points directly toward the floor and remains hidden",
    "the back, shoulder blades, spine, waist, rear pelvis, backs of the thighs, calves, and tops of the feet form one continuous posterior body",
    "this is not supine, not lying on the back, not face-up, not reclining, not a bridge pose, not a duplicated body, and not a front-back anatomical hybrid",
)

EXTENDED_PUPPY_FRAMING_V253 = _sentences(
    "landscape full-body floor composition containing one complete extended puppy pose",
    "the complete head and hair, both arms, both hands, complete torso, pelvis, both knees, both shins, and both feet remain inside one uninterrupted frame",
    "clear margin remains beyond the hands, head, hips, knees, and feet",
    "the single subject occupies approximately sixty-five to seventy-five percent of the image width",
)

ALL_FOURS_FLOOR_POSE_V253 = _sentences(
    "one anatomically normal adult subject holds one stable quadruped hands-and-knees pose directly on the room floor",
    "both palms contact the same floor directly beneath the shoulders and both knees contact that floor directly beneath the hips",
    "the torso remains elevated above the floor with a neutral spine, shoulders supported above the wrists, and hips supported above the knees",
    "both shins and the tops of both feet extend naturally behind the knees on the same floor surface",
    "the head remains naturally aligned with the spine and the complete body is one continuous connected figure",
    "there is no table, countertop, desk, bench, bed, platform, furniture, raised slab, or elevated support surface beneath the subject",
    "the subject is not kneeling on furniture and is not posed on top of any object",
)


def _remove_literal_tabletop_terms(text: str) -> str:
    value = str(text or "")
    value = re.sub(r"hands-and-knees tabletop pose", "quadruped hands-and-knees floor pose", value, flags=re.I)
    value = re.sub(r"solo tabletop pose", "solo hands-and-knees floor pose", value, flags=re.I)
    value = re.sub(r"rear tabletop", "rear hands-and-knees floor", value, flags=re.I)
    value = re.sub(r"tabletop support geometry", "hands-and-knees support geometry", value, flags=re.I)
    value = re.sub(r"tabletop pose", "hands-and-knees floor pose", value, flags=re.I)
    value = re.sub(r"tabletop", "hands-and-knees alignment", value, flags=re.I)
    return _clean_phrase(value)


def _all_fours_hair_highlight_lock_v253(profile: dict[str, Any], plan: dict[str, Any]) -> str:
    highlights = _clean_phrase(profile.get("hair_highlights", ""))
    if not highlights:
        return ""
    view = str(plan.get("camera_view", ""))
    if view in {"Front View", "Three-Quarter Left", "Three-Quarter Right"}:
        return _sentences(
            f"the configured {highlights} remain clearly visible in the front hairline, temple strands, face-framing sections, and forward-falling side lengths during this floor pose",
            "the highlighted strands remain distinct from the natural base hair color and do not disappear, revert to one solid color, or become hidden behind the head",
        )
    return _sentences(
        f"the configured {highlights} remain visible wherever the selected camera angle exposes those strands",
        "the highlighted strands remain distinct from the natural base hair color",
    )


def _rear_puppy_camera_v253(plan: dict[str, Any], effective_lens: str) -> str:
    """Short view block followed by one independent elevation block."""
    view = str(plan.get("camera_view", "Back View"))
    height = str(plan.get("camera_height", "Eye Level"))

    if view == "Back View":
        view_text = _sentences(
            "direct rear camera position behind the pelvis",
            "the rear pelvis and hips are the nearest central landmarks",
            "the spine leads away from the lens toward the shoulders, crown, extended arms, and hands",
            "the hands are the farthest landmarks",
            "only posterior body surfaces and the crown and back of the head are visible",
        )
    else:
        side = "anatomical left" if view == "Rear Three-Quarter Left" else "anatomical right"
        view_text = _sentences(
            f"rear-dominant three-quarter camera position behind the pelvis, offset only twenty to thirty degrees toward the subject's {side} side",
            "the rear pelvis, lower back, spine, shoulder blades, and backs of the limbs remain the dominant visible surfaces",
            "only a narrow side contour is revealed",
            "the camera never moves around toward the hands, face, or front torso",
            "the rear pelvis remains nearest and the hands remain farthest",
        )

    height_text = {
        "Eye Level": _sentences(
            "camera center at rear hip height behind the pelvis",
            "level lens axis and level horizon with no downward, overhead, or top-down view",
        ),
        "Slightly Above Eye Level": _sentences(
            "camera center only slightly above rear hip height",
            "a mild downward angle only, never a high-angle or overhead view",
        ),
        "Slightly Below Eye Level": _sentences(
            "camera center below rear hip height near knee-to-hip level",
            "a mild upward angle toward the pelvis",
        ),
        "High Angle": _sentences(
            "camera clearly elevated behind the pelvis",
            "distinct downward view while remaining behind the pelvis rather than above the head or hands",
        ),
        "Low Angle": _sentences(
            "camera just above the floor behind the pelvis and below the rear hip line",
            "clear upward view toward the elevated pelvis",
        ),
        "Overhead": _sentences(
            "camera high above and behind the pelvis",
            "deliberate top-down rear composition whose visual anchor remains the rear pelvis",
        ),
        "Custom": _clean_phrase(plan.get("custom_camera", "")) or "custom elevation applied while the camera stays behind the pelvis",
    }.get(height, "camera center at rear hip height with a level lens axis")

    return _sentences(
        view_text,
        height_text,
        LENS_PROMPTS_V2.get(effective_lens, "rectilinear 50mm normal-lens perspective"),
        "camera distance is established before capture so the complete pose and all stated margins remain visible",
    )


def _replace_in_profile_and_outputs(profile: dict[str, Any], result: list[Any], old: str, new: str) -> None:
    if not old or old == new:
        return
    for key, value in list(profile.items()):
        if isinstance(value, str) and old in value:
            profile[key] = value.replace(old, new)
    for index, value in enumerate(result):
        if isinstance(value, str) and old in value:
            result[index] = value.replace(old, new)


def _image_plane_side(view: str, anatomical_side: str) -> str:
    view = str(view or "")
    side = str(anatomical_side or "").lower()
    if side not in {"left", "right"}:
        return ""
    front_family = {"Front View", "Three-Quarter Left", "Three-Quarter Right", "Left Profile", "Right Profile"}
    rear_family = {"Back View", "Rear Three-Quarter Left", "Rear Three-Quarter Right"}
    if view in front_family:
        return "right side of the image" if side == "left" else "left side of the image"
    if view in rear_family:
        return "left side of the image" if side == "left" else "right side of the image"
    return ""


def _tattoo_record_prompt_v253(record: dict[str, Any], plan: dict[str, Any] | None = None) -> str:
    location_raw = str(record.get("location", "")).strip()
    location_low = location_raw.lower()
    description = _clean_phrase(record.get("description") or record.get("raw") or "tattoo")
    description = re.sub(r"\bwith a orchid\b", "with an orchid", description, flags=re.I)
    quantity = int(record.get("quantity", 1) or 1)
    view = str((plan or {}).get("camera_view", ""))

    if "full back" in location_low:
        return _sentences(
            "exactly one visible permanent full-back tattoo appears across the subject's exposed back",
            "it is one large continuous integrated artwork rather than a small localized emblem",
            "the composition is centered on the spine, spans broadly across both anatomical sides of the back, begins across the upper shoulder-blade region, and continues toward the lower back and waistline",
            "the design wraps naturally over both shoulder blades, ribs, spine, and lumbar contours and occupies approximately seventy to eighty-five percent of the visible exposed back",
            f"the unified artwork clearly depicts {description}",
            "it must not shrink into a small shoulder tattoo, side-back tattoo, isolated symbol, lower-back emblem, or single localized patch",
            "all other visible skin remains tattoo-free and the artwork is not split, mirrored, duplicated, ghosted, or relocated",
        )

    sleeve_match = re.match(r"^full\s+(left|right)\s+(arm|leg)\s+sleeve$", location_low)
    if sleeve_match:
        anatomical_side, limb = sleeve_match.groups()
        opposite = "left" if anatomical_side == "right" else "right"
        plane = _image_plane_side(view, anatomical_side)
        opposite_plane = _image_plane_side(view, opposite)
        plane_text = f", appearing primarily on the {plane}" if plane else ""
        opposite_text = f" on the {opposite_plane}" if opposite_plane else ""
        if limb == "arm":
            coverage = _sentences(
                f"exactly one permanent full anatomical {anatomical_side} arm sleeve tattoo forms one continuous integrated artwork{plane_text}",
                "the sleeve begins at the shoulder cap and upper arm, crosses the elbow without breaking, wraps around the inner and outer forearm, and ends cleanly at the wrist",
                "it covers approximately eighty to ninety-five percent of the visible arm skin and reads as a true near-complete 360-degree sleeve rather than one forearm patch or several disconnected tattoos",
                "the hand remains tattoo-free unless a separate hand tattoo was explicitly configured",
            )
        else:
            coverage = _sentences(
                f"exactly one permanent full anatomical {anatomical_side} leg sleeve tattoo forms one continuous integrated artwork{plane_text}",
                "the sleeve begins high on the upper thigh, crosses the knee without breaking, wraps around the shin and calf, and ends cleanly at the ankle",
                "it covers approximately eighty to ninety-five percent of the visible leg skin and reads as a true near-complete 360-degree leg sleeve rather than one thigh patch, calf patch, or several disconnected tattoos",
                "the foot remains tattoo-free unless a separate foot tattoo was explicitly configured",
            )
        return _sentences(
            coverage,
            f"the unified sleeve artwork clearly depicts {description}",
            f"the anatomical {opposite} {limb}{opposite_text} and all other unconfigured visible skin remain tattoo-free",
            "do not mirror, swap sides, split, shrink, interrupt, duplicate, ghost, invent, or relocate the sleeve",
        )

    match = re.match(r"^(right|left)\s+(.+)$", location_low)
    if match:
        anatomical_side, region = match.groups()
        plane = _image_plane_side(view, anatomical_side)
        opposite = "left" if anatomical_side == "right" else "right"
        opposite_plane = _image_plane_side(view, opposite)
        plane_text = f", which appears on the {plane}" if plane else ""
        opposite_text = f" on the {opposite_plane}" if opposite_plane else ""
        return _sentences(
            f"exactly {quantity} visible permanent tattoo appears in the entire image: one combined design on the subject's anatomical {anatomical_side} {region}{plane_text}, depicting {description}",
            f"the subject's anatomical {opposite} corresponding region{opposite_text} and all other visible skin remain completely tattoo-free",
            "do not horizontally mirror, swap sides, ghost, duplicate, split, invent, or relocate the tattoo",
        )

    return _sentences(
        f"exactly {quantity} visible permanent tattoo appears in the entire image: one combined design located only on {location_low}, depicting {description}",
        "all other visible skin remains tattoo-free",
        "the tattoo is not split, mirrored, duplicated, ghosted, or relocated",
    )


def _tattoo_prompt_v253(sections: dict[str, Any], plan: dict[str, Any]) -> str:
    records = sections.get("visible_tattoo_records")
    if not isinstance(records, list) or len(records) != 1:
        return str(sections.get("visible_marks", "") or "")
    record = records[0] if isinstance(records[0], dict) else {}
    if int(record.get("quantity", 1) or 1) != 1:
        return str(sections.get("visible_marks", "") or "")
    return _tattoo_record_prompt_v253(record, plan)


def _piercing_geometry(jewelry_type: str) -> str:
    low = str(jewelry_type or "").lower()
    if "curved" in low and "barbell" in low:
        return _sentences(
            "one short continuous curved shaft passes beneath the skin between two healed piercing openings",
            "only exactly two attached end beads and a minimal portion of shaft are visible outside the tissue",
        )
    if "straight" in low and "barbell" in low:
        return _sentences(
            "one straight shaft passes through the tissue with exactly one attached end on each side",
            "the central post is partly hidden within the pierced tissue",
        )
    if "captive" in low and "ring" in low:
        return "one continuous circular ring passes through the tissue with exactly one bead captured in the ring opening"
    if "horseshoe" in low:
        return "one open circular horseshoe bar passes through the tissue with exactly two attached end beads"
    if "hoop" in low or "ring" in low:
        return "one continuous circular ring passes through the piercing opening and does not float beside the skin"
    if "stud" in low:
        return "one visible decorative stud head is anchored by a short post passing through the tissue; there is no second surface ornament"
    return "the selected single piece of jewelry passes through a healed piercing opening and is physically anchored within the tissue"


def _piercing_location(location: str) -> str:
    low = str(location or "").lower()
    if "eyebrow" in low:
        return "through the eyebrow ridge at the selected inner, center, or outer-third position, never through the eyelid or skin below the eye"
    if "nostril" in low:
        return "through the selected anatomical nostril wing or alar rim, not through the septum and not floating beside the nose"
    if "septum" in low:
        return "centered through the nasal septum between both nostrils, not attached to either nostril wing"
    if "bridge" in low:
        return "horizontally through the upper nasal bridge between the eyes, not through either eyebrow"
    if "lip" in low:
        return "through the selected upper- or lower-lip edge at the specified anatomical side, not relocated to the cheek or mouth corner"
    if "nipple" in low:
        return "through the already-existing selected anatomical nipple tissue without creating another nipple or areola"
    if "navel" in low:
        return "through the selected rim of the existing navel without creating a second opening"
    if "ear" in low:
        return "through the selected ear tissue at the specified location"
    return "through the selected anatomical tissue at the exact configured location"


def _piercing_prompt_v253(sections: dict[str, Any], plan: dict[str, Any]) -> str:
    records = sections.get("visible_piercing_records")
    if not isinstance(records, list) or not records:
        return ""
    phrases: list[str] = []
    view = str(plan.get("camera_view", ""))
    for record in records:
        if not isinstance(record, dict):
            continue
        location = str(record.get("location", "")).strip()
        material = str(record.get("material", "")).strip().lower()
        jewelry = str(record.get("jewelry_type", "piercing jewelry")).strip().lower()
        quantity = int(record.get("quantity", 1) or 1)
        side_match = re.match(r"^(left|right)\b", location.lower())
        side = side_match.group(1) if side_match else ""
        plane = _image_plane_side(view, side)
        plane_text = f" and appears on the {plane}" if plane else ""
        phrases.append(_sentences(
            f"exactly {quantity} healed permanent {material} {jewelry} piercing is present at the subject's anatomical {location.lower()}{plane_text}" if side else f"exactly {quantity} healed permanent {material} {jewelry} piercing is present at the exact {location.lower()}",
            _piercing_location(location),
            _piercing_geometry(jewelry),
            "the jewelry is inserted through living tissue with a visible healed entry point and an exit point when that jewelry type requires one",
            "it is not resting on top of the skin, glued on, clipped on, painted on, floating, or attached as a decorative surface ornament",
            "do not add detached beads, extra holes, a third end, duplicate jewelry, or jewelry on the opposite side",
        ))
    return _sentences(*phrases)


def _preserve_floor_outfit_v253(profile: dict[str, Any]) -> str:
    if profile.get("presentation_mode") != "Clothed Character":
        return ""
    components = profile.get("outfit_components") if isinstance(profile.get("outfit_components"), dict) else {}
    top = _clean_phrase(components.get("top") or components.get("one_piece") or "upper garment")
    bottom = _clean_phrase(components.get("bottom") or components.get("swimwear_bottom") or "lower garment")
    if components.get("kind") == "one_piece":
        return _sentences(
            f"the complete {top} remains worn normally as one connected garment during the floor pose",
            "its rear bodice, waist connection, and attached lower section do not disappear, lift away, or transform into skin",
        )
    return _sentences(
        f"the complete {top} remains worn normally across the torso and both arms during the floor pose",
        f"the complete {bottom} remains secured around the waist, pelvis, buttocks, and both legs wherever those regions are covered by the selected garment",
        "neither garment disappears, changes category, becomes skin, or is displaced by the pose",
    )


class CharacterBlueprintCreatorV253(CharacterBlueprintCreatorV252):
    FUNCTION = "build_blueprint_v253"
    DESCRIPTION = (
        "Current Character Creator retaining the passed v2.4.12 tank/crop behavior and adding dedicated Daisy Duke construction plus blueprint metadata for the Krea pre-LoRA documentation run."
    )

    def build_blueprint_v253(self, **kwargs):
        result = list(super().build_blueprint_v252(**kwargs))
        profile = copy.deepcopy(result[8])

        if str(kwargs.get("preset_outfit_if_selected", "")) == "High-Hem Crop Top and Daisy Dukes":
            components = copy.deepcopy(profile.get("outfit_components") or {})
            old_bottom = _clean_phrase(components.get("bottom", ""))
            components["bottom"] = DAISY_DUKE_BOTTOM_V253
            profile["outfit_components"] = components
            _replace_in_profile_and_outputs(profile, result, old_bottom, DAISY_DUKE_BOTTOM_V253)

        profile["schema"] = "CHARACTER_BLUEPRINT_V253"
        profile["schema_version"] = 23
        profile["krea_blueprint_documentation_ready"] = True
        profile["presentation_summary"] = str(profile.get("presentation_summary", "")) + (
            "\nV2.4.13 dataset route: the blueprint can drive a Krea pre-LoRA anatomical/body documentation queue; Qwen is reserved for approved-face camera angles."
            "\nDaisy Duke route: extra-low-rise rigid frayed cutoff micro-shorts are distinct from leggings or high-waisted bottoms."
        )
        result[8] = profile
        result[15] = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        result[21] = profile["presentation_summary"]
        return tuple(result)


class CharacterShotControlV253(CharacterShotControlV252):
    FUNCTION = "build_shot_plan_v253"
    DESCRIPTION = (
        "Quality-first Shot Control: complete-crown Face Close framing, complete-head Waist/Three-Quarter framing, and simplified rear Extended Puppy anatomy with separate view/elevation controls."
    )

    def build_shot_plan_v253(self, **kwargs):
        requested_pose = str(kwargs.get("pose", ""))
        result = list(super().build_shot_plan_v252(**kwargs))
        plan = copy.deepcopy(result[0])
        plan["schema"] = "FCC_SHOT_PLAN_V253"
        plan["schema_version"] = 23

        shot_type = str(plan.get("shot_type", kwargs.get("shot_type", "")))
        if shot_type == "Face Close-Up":
            plan["face_close_lock"] = True
            plan["framing_prompt"] = FACE_CLOSE_FRAMING_V253
            plan["crop_authority_prompt"] = FACE_CLOSE_CROP_AUTHORITY_V253
            plan["pose_prompt"] = FACE_CLOSE_POSE_V253
        elif shot_type == "Waist-Up Midshot":
            plan["framing_prompt"] = WAIST_UP_FRAMING_V253
            plan["complete_head_distance_lock"] = True
        elif shot_type == "Three-Quarter Body":
            plan["framing_prompt"] = THREE_QUARTER_FRAMING_V253
            plan["complete_head_distance_lock"] = True

        all_fours_floor = _floor_kind(requested_pose) == "all_fours"
        if all_fours_floor:
            plan["all_fours_floor_lock"] = True
            plan["framing_prompt"] = _remove_literal_tabletop_terms(str(plan.get("framing_prompt", "")))
            plan["camera_prompt"] = _remove_literal_tabletop_terms(str(plan.get("camera_prompt", "")))
            if shot_type not in {"Face Close-Up", "Close-Up Portrait"}:
                plan["pose_prompt"] = ALL_FOURS_FLOOR_POSE_V253
            else:
                plan["pose_prompt"] = _sentences(
                    _remove_literal_tabletop_terms(str(plan.get("pose_prompt", ""))),
                    "the selected quadruped hands-and-knees position occurs on the room floor outside this portrait crop, never on furniture or a raised surface",
                )
            plan["scene_prompt"] = _sentences(
                _single_subject_scene_v247(str(plan.get("scene_prompt", ""))),
                "both hands and both knees contact an ordinary room floor or ground surface; no table, countertop, bench, bed, platform, furniture, or elevated support appears beneath the subject",
            )

        rear_puppy = (
            _floor_kind(requested_pose) == "extended_puppy"
            and str(plan.get("camera_view", "")) in {"Back View", "Rear Three-Quarter Left", "Rear Three-Quarter Right"}
        )
        if rear_puppy:
            effective_lens = str(plan.get("lens_effective", plan.get("lens", "50mm Normal")))
            plan["rear_puppy_lock"] = True
            plan["rear_puppy_camera_height_lock"] = True
            plan["framing_prompt"] = EXTENDED_PUPPY_FRAMING_V253
            plan["pose_prompt"] = EXTENDED_PUPPY_POSE_V253
            plan["camera_prompt"] = _rear_puppy_camera_v253(plan, effective_lens)
            plan["scene_prompt"] = _single_subject_scene_v247(str(plan.get("scene_prompt", "")))
            plan["expression_prompt"] = ""

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
        if plan.get("face_close_lock"):
            summary += "\nV2.4.13 Face Close: clear crown margin; lower center ends at base of neck; no clavicle, chest, shoulders, or garment body"
        if plan.get("complete_head_distance_lock"):
            summary += "\nV2.4.13 distance lock: complete crown and requested lower crop boundary must both remain in frame"
        if all_fours_floor:
            summary += "\nV2.4.13 All Fours: quadruped hands-and-knees pose occurs directly on the room floor; literal tables and raised furniture are forbidden"
        if rear_puppy:
            summary += "\nV2.4.13 Extended Puppy: base face-down anatomy is resolved before rear view and camera elevation"
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


class CharacterPromptAssemblerV253(CharacterPromptAssemblerV252):
    FUNCTION = "assemble_prompt_v253"
    DESCRIPTION = (
        "Current prompt compiler with quality-first Face Close and Extended Puppy ordering, complete-head crop authority, Daisy Duke construction, view-aware tattoo sides, full-back coverage, and physical piercing insertion geometry."
    )

    def assemble_prompt_v253(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan = shot_plan if isinstance(shot_plan, dict) else {}
        result = list(super().assemble_prompt_v252(
            character_blueprint, shot_plan, generation_purpose, reference_label,
            trigger_word, custom_prefix, custom_suffix,
        ))
        try:
            sections = json.loads(result[18]) if result[18] else {}
        except Exception:
            sections = {}

        notes = str(result[10] or "").replace("V2.4.12", "V2.4.13")
        changed = False

        if plan.get("face_close_lock") or plan.get("complete_head_distance_lock") or plan.get("rear_puppy_lock") or plan.get("all_fours_floor_lock"):
            sections["shot_scene"] = str(plan.get("final_shot_prompt", result[2] or ""))
            result[2] = sections["shot_scene"]
            changed = True

        if plan.get("face_close_lock"):
            sections["visible_presentation"] = ""
            result[3] = ""
            result[15] = FACE_CLOSE_CROP_AUTHORITY_V253
            result[16] = ""
            notes += "\nFace Close V2.4.13: complete crown and clear top margin are mandatory; lower center ends at the neck before clavicles; garment and chest are fully suppressed."
            changed = True

        # Retain the passed v2.4.12 tank/crop refinement outside Face Close.
        if not plan.get("face_close_lock"):
            old_presentation = str(sections.get("visible_presentation", result[3] or ""))
            new_presentation = _tank_presentation_v252(profile, plan, old_presentation)
            if new_presentation != old_presentation:
                sections["visible_presentation"] = new_presentation
                result[3] = new_presentation
                result[16] = new_presentation
                changed = True
            old_body = str(sections.get("visible_body", "") or "")
            new_body = _refine_tank_bust_body_v252(old_body, profile)
            if new_body != old_body:
                sections["visible_body"] = new_body
                changed = True

        if plan.get("all_fours_floor_lock"):
            outfit_lock = _preserve_floor_outfit_v253(profile)
            if outfit_lock:
                sections["visible_presentation"] = _sentences(
                    sections.get("visible_presentation", result[3] or ""),
                    outfit_lock,
                )
                result[3] = sections["visible_presentation"]
                result[16] = sections["visible_presentation"]
            hair_lock = _all_fours_hair_highlight_lock_v253(profile, plan)
            if hair_lock:
                sections["primary_character"] = _sentences(
                    sections.get("primary_character", result[19] or ""),
                    hair_lock,
                )
                result[19] = sections["primary_character"]
            notes += "\nAll Fours V2.4.13: the pose is directly on the room floor rather than a literal table; front and three-quarter views preserve configured hair highlights; selected garments remain present."
            changed = True

        if plan.get("rear_puppy_lock"):
            outfit_lock = _preserve_floor_outfit_v253(profile)
            if outfit_lock:
                sections["visible_presentation"] = _sentences(
                    sections.get("visible_presentation", result[3] or ""),
                    outfit_lock,
                )
                result[3] = sections["visible_presentation"]
                result[16] = sections["visible_presentation"]
            notes += "\nExtended Puppy V2.4.13: concise face-down pose anatomy precedes rear-view and elevation text; selected garments are explicitly retained during the floor pose."
            changed = True

        old_marks = str(sections.get("visible_marks", result[4] or "") or "")
        tattoo_text = _tattoo_prompt_v253(sections, plan)
        piercing_text = _piercing_prompt_v253(sections, plan)
        new_marks = _sentences(tattoo_text, piercing_text)
        if new_marks and new_marks != old_marks:
            sections["visible_marks"] = new_marks
            result[4] = new_marks
            notes += "\nMarks V2.4.13: tattoo side is resolved against the camera view; Full Back, full arm sleeves, and full leg sleeves use dedicated coverage authority; piercing jewelry passes through tissue with entry/exit geometry."
            changed = True

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
                if old_marks and old_marks in final_prompt and new_marks:
                    final_prompt = final_prompt.replace(old_marks, new_marks, 1)
                result[1] = final_prompt
            sections["final_prompt"] = final_prompt
            sections["routing_mode"] = str(sections.get("routing_mode", "")) + "+v253_quality_fixes"
            result[13] = final_prompt

        result[10] = notes
        result[18] = json.dumps(sections, indent=2, ensure_ascii=False)
        result[12] = _rebuild_active_summary_v246(profile, plan, sections, notes)
        return tuple(result)


class QwenDatasetQueueV253(QwenDatasetQueueV252):
    DESCRIPTION = (
        "Compatibility queue registered to the v2.4.13 suite. The active Master Dataset Director now limits Qwen to approved-face camera angles; Krea handles blueprint body/anatomy documentation."
    )
