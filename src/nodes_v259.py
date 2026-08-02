from __future__ import annotations

import copy
import json
import re
from typing import Any

from .nodes import BUST_AUGMENTATION_PROMPTS, BUST_FIRMNESS_PROMPTS
from .nodes_v230 import _clean_phrase, _sentences
from .nodes_v243 import BUST_SHAPE_PROMPTS_V243, _record_visible_v243, _visible_tags_v243
from .nodes_v256 import _merge_unique
from .nodes_v257 import (
    SCAR_MARK_FIELD,
    _canonical_character_prompts,
    _canonicalize_chest,
    _prune_summary,
)
from .nodes_v258 import (
    BACKGROUND_FOCUS_OPTIONS,
    CharacterBlueprintCreatorV258,
    CharacterPromptAssemblerV258,
    CharacterShotControlV258,
    QwenDatasetQueueV258,
    _canonical_presentation,
    _coverage_v258,
    _crop_scoped_body,
    _crop_scoped_presentation,
    _daisy_active,
    _focus_prompt,
    _front_view_lock,
    _is_clothed,
    _is_clinical,
    _presentation_mode,
    _replace_summary_line,
    _remove_raw_focus_falloff,
    _selected_chest_text,
    _upper_build_prompt,
    _visible_piercings_v258,
    _visible_scars_v258,
    _visible_tattoos_v258,
)

# -----------------------------------------------------------------------------
# V2.4.19 / Studio V2.8.19 — controlled-checklist stabilization
# - stronger but independent bust size / position calibration
# - clean-skin authority when tattoo status is None; configured marks remain exclusive
# - camera-surface visibility for anterior pelvic tattoos
# - full-leg/buttock coverage prompts protect knees, posterior surfaces, and continuity
# - simplified center-lip and navel jewelry geometry
# - Face Close, Waist-Up, and Front View final authorities are shot-specific
# - Extended Puppy respects the selected camera height instead of forcing eye-level
# - background focus receives a final post-character authority
# - selected clothing receives a final visibility lock without reactivating stale outfits
# -----------------------------------------------------------------------------

CORE_VERSION = "2.4.19"
STUDIO_VERSION = "2.8.19"


BUST_SIZE_CALIBRATION_V259 = {
    "Very Small": (
        "a very small but still visibly present adult bust with a slight natural breast mound and minimal projection, "
        "clearly distinct from a completely flat chest"
    ),
    "Small": (
        "a clearly small adult bust with modest but unmistakable breast volume and gentle projection, visibly fuller than Very Small "
        "and clearly distinct from a flat chest"
    ),
    "Small-Medium": (
        "a small-to-medium adult bust with moderate visible volume and projection, clearly fuller than Small while remaining below Medium"
    ),
    "Medium": (
        "a clearly medium adult bust with moderate balanced volume and forward projection, occupying a visibly larger portion of the chest "
        "than Small and remaining distinctly below Full"
    ),
    "Medium-Full": (
        "a medium-full adult bust with clearly noticeable volume and projection, visibly fuller than Medium and below Full"
    ),
    "Full": (
        "a full adult bust with pronounced natural volume, broad visible chest occupancy, and strong forward projection"
    ),
    "Large": (
        "a clearly large adult bust with substantial volume, broad chest occupancy, and strong forward projection, visibly larger than Full"
    ),
    "Very Large": (
        "a very large adult bust with heavy visible volume, broad chest occupancy, strong projection, and substantial natural weight"
    ),
    "Overly Large": (
        "an unmistakably extremely large adult bust with exaggerated volume, broad chest occupancy, very strong projection, and substantial natural weight"
    ),
}

BUST_POSITION_CALIBRATION_V259 = {
    "Natural Average-Set": (
        "preserve the selected bust size and shape unchanged; place the breast roots at a conventional centered adult chest height, "
        "with a normal-height lower fold and neither unusually high nor unusually low placement"
    ),
    "High-Set / Perky": (
        "preserve the selected bust size and shape unchanged; place the breast roots clearly higher on the torso with a higher lower fold, "
        "a shorter vertical footprint, lifted forward orientation, and limited lower drop"
    ),
    "High and Tight": (
        "preserve the selected bust size and shape unchanged; place the breast roots at the highest configured position close to the upper chest, "
        "with a high tight lower fold, a compact vertical footprint, and minimal lower hang; do not reduce volume or narrow the selected base"
    ),
    "Low-Set": (
        "preserve the selected bust size and shape unchanged; place the breast roots clearly lower on the torso with a lower fold, "
        "a longer upper-chest-to-bust distance, and natural lower settling"
    ),
    "Downward-Sloping": (
        "preserve the selected bust size and base shape unchanged; orient the bust with a descending upper slope and lower-pole-dominant weight"
    ),
    "Pendulous Natural": (
        "preserve the selected bust size and base shape unchanged; use pronounced natural lower hang, realistic gravitational weight, "
        "and a lower fullest point"
    ),
}


def _bust_shape_text(profile: dict[str, Any]) -> str:
    return _clean_phrase(BUST_SHAPE_PROMPTS_V243.get(str(profile.get("bust_shape", "")), ""))


def _calibrate_chest_v259(profile: dict[str, Any]) -> None:
    resolved = str(profile.get("resolved_chest_anatomy", ""))
    if resolved == "Flat / Neutral Chest":
        anatomy = _sentences(
            "a truly flat neutral adult chest with a smooth chest plane, minimal soft-tissue projection, and balanced natural anatomy",
            "no breast mound, cleavage, rounded breast volume, or residual bust-control geometry is present",
        )
        clothed = _sentences(
            "a truly flat neutral chest silhouette with minimal garment projection",
            "the garment follows a smooth chest plane without creating breast mounds or cleavage",
        )
        integrity = _sentences(
            "chest-region anatomy lock: the selected chest remains truly flat and neutral",
            "the smooth chest plane and minimal projection remain unchanged in every visible view",
            "do not replace it with small breasts, bust anatomy, cleavage, or rounded breast volume",
        )
    elif resolved == "Bust Anatomy — Use Bust Controls":
        size = str(profile.get("bust_size", "Unspecified"))
        shape = _bust_shape_text(profile)
        position = _clean_phrase(BUST_POSITION_CALIBRATION_V259.get(str(profile.get("bust_position", "")), ""))
        firmness = _clean_phrase(BUST_FIRMNESS_PROMPTS.get(str(profile.get("bust_firmness", "")), ""))
        augmentation = _clean_phrase(BUST_AUGMENTATION_PROMPTS.get(str(profile.get("bust_augmentation", "")), ""))
        size_text = _clean_phrase(BUST_SIZE_CALIBRATION_V259.get(size, ""))
        anatomy = _sentences(
            size_text,
            shape,
            position,
            firmness,
            augmentation,
            "bust size, base shape, vertical placement, firmness, and augmentation are independent controls; changing one does not silently reduce or replace the others",
        )
        clothed = _sentences(
            anatomy,
            "the selected garment follows the complete configured bust volume and contour without shrinking it, except when an explicit compression garment is selected",
        )
        integrity = _sentences(
            "chest-region anatomy lock: the selected chest has one adult bust anatomy system only",
            "the left and right breasts, nipples, areolae, sternum relationship, selected volume, selected base shape, and selected root height remain physically consistent",
            "do not average the selected size toward a smaller category and do not let vertical placement alter the selected volume or base shape",
        )
    else:
        return

    profile["chest_anatomy_prompt"] = anatomy
    profile["chest_clothed_prompt"] = clothed
    profile["active_chest_anatomy_prompt"] = anatomy
    profile["active_chest_clothed_prompt"] = clothed
    profile["chest_region_integrity_prompt"] = integrity
    profile["active_chest_integrity_prompt"] = integrity
    profile["resolved_chest_authority"] = {
        "category": resolved,
        "anatomy_prompt": anatomy,
        "clothed_prompt": clothed,
        "integrity_prompt": integrity,
        "bust_controls_active": resolved == "Bust Anatomy — Use Bust Controls",
        "calibration_version": CORE_VERSION,
    }
    body = _clean_phrase(profile.get("body_type_authority_prompt", ""))
    profile["anatomy_upper_body"] = _merge_unique(body, anatomy)
    profile["upper_body_identity"] = profile["anatomy_upper_body"]
    profile["clothed_upper_body"] = _merge_unique(body, clothed)


def _refine_mark_records_v259(profile: dict[str, Any]) -> None:
    records = profile.get("scar_mole_beauty_mark_records", [])
    if not isinstance(records, list):
        return
    for record in records:
        if not isinstance(record, dict):
            continue
        raw = str(record.get("raw", "")).lower()
        if re.search(r"(?:upper\s+right|right\s+upper)\s+thigh", raw):
            record["location"] = "Right Upper Thigh"
            record["region_tags"] = ["thighs", "upper_thighs", "right_thigh"]
        elif re.search(r"(?:upper\s+left|left\s+upper)\s+thigh", raw):
            record["location"] = "Left Upper Thigh"
            record["region_tags"] = ["thighs", "upper_thighs", "left_thigh"]
        elif "above upper lip" in raw or "upper lip" in raw:
            tags = {"face", "mouth", "lip", "lips"}
            if "left" in raw:
                tags.add("left_lip")
                record["location"] = "Left Upper Lip"
            elif "right" in raw:
                tags.add("right_lip")
                record["location"] = "Right Upper Lip"
            else:
                record["location"] = "Upper Lip"
            record["region_tags"] = sorted(tags)


def _camera_surface_allows_tattoo(location: str, view: str) -> bool:
    if "Front Pelvic" not in location:
        return True
    if view in {"Back View", "Rear Three-Quarter Left", "Rear Three-Quarter Right"}:
        return False
    if view == "Left Profile" and location.startswith("Right"):
        return False
    if view == "Right Profile" and location.startswith("Left"):
        return False
    return True


def _visible_tattoos_v259(profile: dict[str, Any], plan: dict[str, Any]) -> list[dict[str, Any]]:
    view = str(plan.get("camera_view", ""))
    return [
        record for record in _visible_tattoos_v258(profile, plan)
        if _camera_surface_allows_tattoo(str(record.get("location", "")), view)
    ]


def _tattoo_prompt_v259(record: dict[str, Any], plan: dict[str, Any]) -> str:
    from .nodes_v258 import _tattoo_record_prompt_v258

    base = _tattoo_record_prompt_v258(record, plan)
    location = str(record.get("location", ""))
    view = str(plan.get("camera_view", ""))
    if location in {"Full Left Leg + Left Buttock", "Full Right Leg + Right Buttock"}:
        side = "left" if "Left" in location else "right"
        if view == "Front View":
            surface = (
                f"from the front, the anatomical {side} buttock itself is behind the body; prove continuity by carrying the artwork visibly to the highest exposed outer and inner upper thigh and around the {side} hip edge"
            )
        elif view == "Back View":
            surface = (
                f"from the rear, the artwork visibly covers the anatomical {side} buttock, gluteal fold, posterior thigh, back of the knee, calf, and ankle as one connected design"
            )
        elif view in {"Left Profile", "Right Profile"}:
            surface = (
                f"from profile, the artwork visibly wraps continuously across the anatomical {side} buttock, outer hip, lateral thigh, knee, calf, and ankle"
            )
        else:
            surface = "the artwork remains continuous across every configured visible surface"
        return _sentences(
            base,
            surface,
            "configured knee surfaces are filled by the continuous design; no blank knee band, detached lower-leg patch, or large uncovered interruption appears",
            "only small intentional negative spaces inside the artwork are allowed; large clean-skin gaps across configured surfaces are not allowed",
        )
    if location == "Both Full Legs + Both Buttocks":
        return _sentences(
            base,
            "both configured knee surfaces, posterior thighs, shins, calves, and ankles remain visibly integrated into the coordinated design",
            "do not leave blank bands around either knee or large unconfigured clean-skin panels within the selected full-coverage surfaces",
        )
    if "Front Pelvic Bone" in location:
        return _sentences(
            base,
            "this is an anterior pelvic-bone mark; it is omitted completely from direct rear and rear-three-quarter views rather than relocated to the back, flank, wrist, or arm",
        )
    return base


def _piercing_prompt_v259(record: dict[str, Any], plan: dict[str, Any]) -> str:
    location = str(record.get("location", "")).strip().lower()
    jewelry = str(record.get("jewelry_type", "piercing jewelry")).strip().lower()
    material = str(record.get("material", "")).strip().lower() or "metal"
    visibility = str(record.get("visibility", "Normal") or "Normal").lower()
    if "center lip" in location and ("ring" in jewelry or "hoop" in jewelry):
        return _sentences(
            f"exactly one small {material} hoop is centered at the midpoint of the lower lip",
            "one ring only; no second ring, no paired side rings, and no jewelry at either mouth corner",
            "the single hoop crosses the lower-lip edge at one centered healed piercing site and hangs directly beneath the middle of the mouth",
            "the nose, septum, and both nostrils remain completely bare",
            f"visibility is {visibility}",
            "the hoop remains a clean circular ring rather than bent wire laid across the lip surface",
        )
    if "navel" in location or "belly button" in location:
        if "barbell" in jewelry:
            return _sentences(
                f"exactly one small {material} curved barbell is attached through the upper rim of the existing navel",
                "one top bead sits immediately above the pierced upper navel rim and one lower bead sits just inside or immediately below the navel opening",
                "the short curved shaft is mostly hidden beneath the pierced tissue; only the two attached beads and a minimal clean shaft segment are visible",
                "two beads only; no loose hook, melted metal, detached end, duplicate opening, or second navel",
                f"visibility is {visibility}",
            )
    from .nodes_v258 import _piercing_prompt_v258
    return _piercing_prompt_v258(record, plan)


def _scar_prompt_v259(record: dict[str, Any]) -> str:
    raw = _clean_phrase(record.get("raw", ""))
    location = _clean_phrase(record.get("location", ""))
    if not raw:
        return ""
    low = raw.lower()
    if "mole" in low or "beauty mark" in low:
        kind = "exactly one small permanent natural mole or beauty mark"
    elif any(token in low for token in ("scar", "shrapnel", "gunshot", "stab")):
        kind = "exactly one clearly visible permanent healed scar"
    else:
        kind = "exactly one clearly visible permanent natural skin mark"
    return _sentences(
        f"{kind} appears only at the configured {location.lower() if location else 'anatomical location'}: {raw}",
        "the configured mark remains visible at ordinary documentation scale and follows the local skin surface",
        "no duplicate, mirrored, relocated, enlarged, or second matching mark appears elsewhere",
        "do not convert the mark into decorative tattoo artwork",
    )


def _clean_skin_authority_v259(
    profile: dict[str, Any],
    visible_tattoos: list[dict[str, Any]],
    visible_scars: list[dict[str, Any]],
    visible_piercings: list[dict[str, Any]],
) -> str:
    tattoo_records = profile.get("tattoo_records", []) if isinstance(profile.get("tattoo_records"), list) else []
    scar_records = profile.get("scar_mole_beauty_mark_records", []) if isinstance(profile.get("scar_mole_beauty_mark_records"), list) else []
    piercing_records = profile.get("piercing_records", []) if isinstance(profile.get("piercing_records"), list) else []
    parts: list[str] = []
    if not tattoo_records:
        parts.append("all visible skin remains free of tattoos, body art, decorative ink, symbols, lettering, and ornamental markings")
    elif visible_tattoos:
        parts.append("only the configured visible tattoo artwork is present; every other visible skin region remains tattoo-free")
    else:
        parts.append("the configured tattoo is outside this crop or hidden by the selected view; do not relocate it onto another visible body region")

    if scar_records:
        parts.append(
            f"exactly {len(scar_records)} configured permanent scar, mole, or beauty-mark record(s) exist on the character; no additional prominent permanent marks are invented"
        )
    if piercing_records:
        parts.append(
            f"exactly {len(piercing_records)} configured permanent piercing record(s) exist on the character; no additional piercing jewelry is invented"
        )
    else:
        parts.append("no piercing jewelry is present anywhere")
    return _sentences(*parts)


def _front_view_lock_v259(plan: dict[str, Any]) -> str:
    if str(plan.get("camera_view", "")) != "Front View":
        return ""
    shot = str(plan.get("shot_type", ""))
    if shot == "Waist-Up Midshot":
        return _sentences(
            "final waist-up front-view authority: the facial midline, sternum, and visible torso centerline face directly toward the lens",
            "both shoulders remain equally distant from the camera and neither shoulder rotates backward",
            "the pelvis, hip points, groin, and knees are outside the crop and are not named or used as alignment landmarks",
            "the stance does not rotate the visible shoulders, ribcage, or waist",
        )
    if shot in {"Three-Quarter Body", "Full Body", "Wide Full Body / Environmental"}:
        return _sentences(
            "final strict front-view authority: the sternum, navel, and pelvic centerline face directly toward the lens",
            "both shoulders and both front hip points remain equally distant from the camera",
            "the feet remain forward and the pose uses no torso yaw, pelvic yaw, contrapposto twist, or three-quarter rotation",
        )
    return ""


def _final_frame_authority_v259(profile: dict[str, Any], plan: dict[str, Any]) -> str:
    shot = str(plan.get("shot_type", plan.get("selected_shot_type", "")))
    if shot == "Face Close-Up":
        return _sentences(
            "FINAL FACE-CLOSE FRAME AUTHORITY",
            "the face fills approximately eighty-two to ninety percent of the square image height",
            "clear margin remains above the complete crown and all hair",
            "the bottom image edge cuts through the middle-to-lower neck before either clavicle begins",
            "both shoulder joints, upper arms, armpits, chest, bust, garment straps, neckline, and torso remain completely outside the frame",
            "both arms hang below the frame and are not raised beside or above the head",
            "do not widen or lower the composition",
        )
    if shot == "Waist-Up Midshot":
        boundary = "the visible waistband at the natural waist" if _is_clothed(profile) else "the natural waist above the iliac crest"
        return _sentences(
            "FINAL WAIST-UP FRAME AUTHORITY",
            "the complete crown and hair remain visible with clear margin above them",
            f"the lower image edge cuts exactly across {boundary}",
            "the pelvis, pubic region, groin, crotch, buttocks, thighs, knees, lower legs, and feet remain completely outside the image",
            "the camera crops the body at the waist rather than moving farther back to show lower anatomy",
            "chest size, clothing, tattoos, piercings, and marks do not change the selected waist-up crop",
        )
    if shot in {"Full Body", "Wide Full Body / Environmental"}:
        return _sentences(
            "FINAL FULL-BODY FRAME AUTHORITY",
            "this remains one complete standing full-body photograph",
            "the complete crown and hair, face, neck, torso, both arms, both hands, pelvis, both complete legs, both ankles, and both feet remain fully inside the image",
            "clear visible background margin remains above the hair and beneath both feet",
            "the camera moves farther away rather than cropping the body",
            "clothing, chest proportions, tattoos, piercings, scars, moles, and other details do not convert the image into a portrait, waist-up image, or three-quarter crop",
        )
    return ""


def _final_presentation_authority_v259(profile: dict[str, Any], presentation: str) -> str:
    if not _is_clothed(profile):
        return ""
    layout = str(profile.get("structured_outfit_type_label", profile.get("structured_outfit_type", "")))
    if layout in {"Top Only — Lower Body Unclothed", "Top Only"}:
        return _sentences(
            "FINAL GARMENT AUTHORITY: the selected top remains visibly worn as the only garment",
            "no bottom garment or footwear is added, and the top is not omitted",
        )
    if layout in {"Bottom Only — Upper Body Unclothed", "Bottom Only"}:
        return _sentences(
            "FINAL GARMENT AUTHORITY: the selected lower garment remains visibly worn as the only garment",
            "the upper torso remains uncovered and the bottom garment is not omitted",
        )
    return _sentences(
        "FINAL GARMENT AUTHORITY: the primary character remains fully dressed in the complete selected outfit",
        "every selected garment remains visibly present and is not replaced by nudity, missing fabric, or an unrelated outfit",
        _clean_phrase(presentation),
    )


def _final_focus_authority_v259(plan: dict[str, Any]) -> str:
    value = str(plan.get("background_focus", BACKGROUND_FOCUS_OPTIONS[0]))
    if value == "Natural Snapshot Focus — No Artificial Bokeh":
        return _sentences(
            "FINAL BACKGROUND-FOCUS AUTHORITY: use a deep-focus ordinary consumer snapshot",
            "the subject, midground people, shelves, bottles, signs, and room edges retain ordinary readable edge detail",
            "no shallow depth of field, portrait-mode blur, creamy bokeh, synthetic subject cutout, or strongly defocused background",
        )
    if value == "Mostly In Focus":
        return _sentences(
            "FINAL BACKGROUND-FOCUS AUTHORITY: foreground, subject, midground, and background remain broadly sharp in one ordinary snapshot",
            "background objects retain visible edges and are not converted into soft bokeh",
        )
    if value == "Mild Natural Separation":
        return _sentences(
            "FINAL BACKGROUND-FOCUS AUTHORITY: only mild natural optical softness is allowed behind the subject",
            "the environment remains recognizable with retained object edges and no synthetic creamy blur",
        )
    return ""


def _extended_puppy_camera_v259(plan: dict[str, Any]) -> str:
    view = str(plan.get("camera_view", ""))
    height = str(plan.get("camera_height", "Eye Level"))
    if view != "Back View":
        return ""
    base = _sentences(
        "strict direct rear camera at the six-o'clock position behind the sacrum",
        "the lens remains centered on the spinal midline and both rear hips remain equally visible",
        "the forward arms recede toward twelve o'clock on the same axis as the spine",
        "this is not a side, profile, or rear-three-quarter view",
        "rectilinear 50mm normal-lens perspective",
    )
    height_text = {
        "Eye Level": _sentences(
            "camera lens centered at rear-pelvis height",
            "optical axis horizontal and parallel to the floor with zero downward tilt",
        ),
        "Slightly Above Eye Level": _sentences(
            "camera slightly above rear-pelvis height with a gentle downward angle of approximately ten to fifteen degrees",
            "the view remains behind the subject and is not overhead",
        ),
        "Slightly Below Eye Level": _sentences(
            "camera slightly below rear-pelvis height with a gentle upward angle",
            "the view remains directly behind the subject",
        ),
        "High Angle": _sentences(
            "camera clearly elevated behind the pelvis with a distinct downward angle of approximately thirty-five to forty-five degrees",
            "this is a rear high-angle view, not eye-level and not a true top-down overhead view",
        ),
        "Low Angle": _sentences(
            "camera low behind the knees and pelvis with a distinct upward angle",
            "the rear pelvis remains centered and the camera is not overhead",
        ),
        "Overhead": _sentences(
            "true overhead top-down camera aligned along the spine from hands to pelvis to knees",
            "the full floor pose remains one connected figure",
        ),
    }.get(height, "")
    return _sentences(base, height_text)


def _extended_puppy_pose_v259() -> str:
    return _sentences(
        "one adult subject performs one extended puppy yoga pose directly on the floor",
        "exactly two knees remain planted directly beneath the hip sockets; the shins and tops of both feet remain on the floor",
        "the hips remain elevated above the knees while the chest and sternum lower toward the floor in front of the knees",
        "both arms extend straight forward from the shoulders toward twelve o'clock, shoulder-width apart, with palms flat beyond the crown",
        "the head remains low between the forward arms",
        "the torso is not fully prone and the legs do not extend straight backward",
        "the arms do not spread sideways, form a T shape, or rest beside the torso",
        "the complete body remains one connected figure from hands through shoulders, spine, pelvis, knees, shins, and feet",
    )


def _replace_active_output_size(summary: str, width: int, height: int, aspect: str) -> str:
    line = f"ACTIVE OUTPUT SIZE: {width} × {height} | {aspect}"
    if re.search(r"^ACTIVE OUTPUT SIZE:.*$", summary, flags=re.M):
        return re.sub(r"^ACTIVE OUTPUT SIZE:.*$", line, summary, flags=re.M)
    return summary.rstrip() + "\n" + line


class CharacterBlueprintCreatorV259(CharacterBlueprintCreatorV258):
    FUNCTION = "build_blueprint_v259"
    DESCRIPTION = (
        "Controlled-checklist Character Creator with calibrated chest authority, refined permanent-mark regions, clean-skin state, and exact presentation exclusivity."
    )

    def build_blueprint_v259(self, **kwargs):
        result = list(super().build_blueprint_v258(**kwargs))
        profile = copy.deepcopy(result[8])
        _refine_mark_records_v259(profile)
        _calibrate_chest_v259(profile)
        _canonicalize_chest(profile)
        _canonical_character_prompts(profile)

        profile["clean_skin_authority"] = _clean_skin_authority_v259(profile, [], [], [])
        profile["schema"] = "CHARACTER_BLUEPRINT_V259"
        profile["schema_version"] = 29
        profile["fcc_core_version"] = CORE_VERSION
        profile["fcc_studio_version"] = STUDIO_VERSION
        resolved = str(profile.get("resolved_chest_anatomy", ""))
        summary = _prune_summary(profile.get("presentation_summary", ""), resolved).replace("V2.4.18", CORE_VERSION)
        summary += (
            "\nChest V2.4.19: structured size, shape, position, firmness, and augmentation are independent; Small/Medium/Large use stronger visual separation."
            "\nSkin V2.4.19: Tattoo None emits tattoo-free visible skin; configured marks and piercings receive exact-count exclusivity."
            "\nMarks V2.4.19: upper-thigh and upper-lip descriptors receive explicit regional tags before visibility filtering."
        )
        profile["presentation_summary"] = summary

        presentation_mode = str(profile.get("presentation_mode", ""))
        result[1] = profile.get("anatomy_upper_body", "")
        result[2] = profile.get("anatomy_lower_body", "")
        result[3] = profile.get("chest_anatomy_prompt", "") if presentation_mode == "Clinical Anatomy" else profile.get("chest_clothed_prompt", "")
        result[4] = profile.get("marks_prompt", "")
        result[6] = profile.get("active_character_prompt", "")
        result[8] = profile
        result[10] = profile.get("clothed_upper_body", "")
        result[11] = profile.get("anatomy_upper_body", "")
        result[12] = profile.get("clothed_lower_body", "")
        result[13] = profile.get("anatomy_lower_body", "")
        result[15] = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        result[17] = profile.get("active_body_prompt", "")
        result[18] = profile.get("active_character_prompt", "")
        result[19] = profile.get("clothed_character_prompt", "")
        result[20] = profile.get("clinical_character_prompt", "")
        result[21] = summary
        return tuple(result)


class CharacterShotControlV259(CharacterShotControlV258):
    FUNCTION = "build_shot_plan_v259"
    DESCRIPTION = (
        "Controlled-checklist Shot Control with tighter Face Close/Waist-Up framing, shot-specific front locks, camera-height-aware Extended Puppy, and deep-focus snapshot authority."
    )

    def build_shot_plan_v259(self, **kwargs):
        result = list(super().build_shot_plan_v258(**kwargs))
        plan = copy.deepcopy(result[0])
        shot = str(plan.get("shot_type", kwargs.get("shot_type", "")))
        view = str(plan.get("camera_view", kwargs.get("camera_view", "")))
        pose = str(plan.get("pose", kwargs.get("pose", ""))).lower()

        plan["photo_style_prompt"] = _remove_raw_focus_falloff(plan.get("photo_style_prompt", ""))
        plan["environment_prompt"] = _remove_raw_focus_falloff(plan.get("environment_prompt", ""))
        plan["environment_prompt"] = _sentences(
            re.sub(r"ordinary consumer-camera depth of field.*$", "", str(plan.get("environment_prompt", "")), flags=re.I),
            _focus_prompt(str(plan.get("background_focus", BACKGROUND_FOCUS_OPTIONS[0])), str(plan.get("custom_background_focus", ""))),
        )

        if shot == "Face Close-Up":
            plan["framing_prompt"] = _sentences(
                "tight square facial documentation close-up with a small clear margin above the complete crown",
                "the complete crown, hairline, both sides of the head, visible ear edges, complete face, and chin remain inside the frame",
                "the face occupies approximately eighty-two to ninety percent of the image height",
                "the lower edge cuts through the middle-to-lower neck before either clavicle begins",
                "shoulder joints, upper arms, armpits, chest, bust, garment straps, neckline, and torso remain outside the frame",
            )
            plan["crop_authority_prompt"] = "both arms hang below the frame; do not raise arms beside the face and do not widen or lower the face-close composition"
            plan["pose_prompt"] = _sentences(
                "head upright with a natural neck position",
                "facial plane follows the selected camera view",
                "both arms remain lowered below the crop and entirely outside the image",
            )
            plan["recommended_width"] = 1024
            plan["recommended_height"] = 1024
            plan["aspect_ratio"] = "Square 1:1 — Face Close"
            plan["resolution_summary"] = "1024 × 1024 | Square 1:1 — Face Close"
        elif shot == "Waist-Up Midshot":
            plan["framing_prompt"] = _sentences(
                "complete-head waist-up composition with clear margin above the complete crown",
                "the complete head, hair, neck, shoulders, torso, arms, and natural waist remain inside the frame",
                "the lower edge cuts across the natural waist above the iliac crest or across a visible waistband positioned at that same waist line",
                "the pelvis, pubic region, groin, crotch, buttocks, thighs, knees, lower legs, and feet remain outside the image",
            )
            plan["crop_authority_prompt"] = "crop the body at the waist; do not move the camera farther back or widen downward into a three-quarter-body composition"
            plan["recommended_width"] = 1024
            plan["recommended_height"] = 1024
            plan["aspect_ratio"] = "Square 1:1 — Waist-Up"
            plan["resolution_summary"] = "1024 × 1024 | Square 1:1 — Waist-Up"

        if "extended puppy" in pose:
            plan["pose_prompt"] = _extended_puppy_pose_v259()
            if view == "Back View":
                plan["camera_prompt"] = _extended_puppy_camera_v259(plan)
                plan["rear_puppy_lock_v259"] = True

        # Remove the inherited V2.4.18 generic front lock before adding the
        # shot-specific V2.4.19 lock. The inherited text names pelvis/hip
        # landmarks even for Waist-Up and weakens the crop boundary.
        pose_text = str(plan.get("pose_prompt", ""))
        pose_text = re.sub(
            r"final front-view authority:.*?does not rotate the shoulders, ribcage, waist, or pelvis\.?",
            "", pose_text, flags=re.I | re.S,
        ).strip(" .")
        plan["pose_prompt"] = pose_text
        front_lock = _front_view_lock_v259(plan)
        if front_lock:
            plan["pose_prompt"] = _sentences(plan.get("pose_prompt", ""), front_lock)

        plan["schema"] = "FCC_SHOT_PLAN_V259"
        plan["schema_version"] = 29
        plan["fcc_core_version"] = CORE_VERSION
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

        summary = str(plan.get("active_settings_summary", "")).replace("V2.4.18", CORE_VERSION)
        summary = _replace_summary_line(summary, "Framing", plan.get("framing_prompt", ""))
        summary = _replace_summary_line(summary, "Camera", plan.get("camera_prompt", ""))
        summary = _replace_summary_line(summary, "Pose", plan.get("pose_prompt", ""))
        summary = _replace_summary_line(summary, "Environment", plan.get("environment_prompt", ""))
        if shot == "Face Close-Up":
            summary = _replace_summary_line(summary, "Aspect", "Square 1:1 — Face Close (1024 × 1024)")
        elif shot == "Waist-Up Midshot":
            summary = _replace_summary_line(summary, "Aspect", "Square 1:1 — Waist-Up (1024 × 1024)")
        summary = _replace_active_output_size(summary, int(plan.get("recommended_width", 1024)), int(plan.get("recommended_height", 1024)), str(plan.get("aspect_ratio", "Auto")))
        if "extended puppy" in pose:
            summary += f"\nV2.4.19 Extended Puppy: selected camera height '{plan.get('camera_height')}' now controls rear elevation independently."
        summary += "\nV2.4.19 crop locks: Face Close excludes raised arms/armpits; Waist-Up uses a square waist boundary without pelvis landmarks."
        plan["active_settings_summary"] = summary

        result[0] = plan
        result[1] = plan["final_shot_prompt"]
        result[2] = plan.get("framing_prompt", "")
        result[3] = plan.get("camera_prompt", "")
        result[4] = plan.get("pose_prompt", "")
        result[6] = plan.get("environment_prompt", "")
        result[7] = summary
        result[8] = json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True)
        result[9] = int(plan.get("recommended_width", result[9]))
        result[10] = int(plan.get("recommended_height", result[10]))
        return tuple(result)


class CharacterPromptAssemblerV259(CharacterPromptAssemblerV258):
    FUNCTION = "assemble_prompt_v259"
    DESCRIPTION = (
        "Controlled-checklist prompt compiler with clean-skin authority, camera-surface mark filtering, simplified jewelry geometry, final clothing/focus locks, and corrected crop/pose authorities."
    )

    def assemble_prompt_v259(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        result = list(super().assemble_prompt_v258(
            character_blueprint, shot_plan, generation_purpose, reference_label,
            trigger_word, custom_prefix, custom_suffix,
        ))
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan = shot_plan if isinstance(shot_plan, dict) else {}
        try:
            sections = json.loads(result[18]) if result[18] else {}
        except Exception:
            sections = {}

        presentation = _crop_scoped_presentation(profile, plan, str(sections.get("visible_presentation", result[3] or "")))
        body = _crop_scoped_body(profile, plan, str(sections.get("visible_body", "")))
        if str(plan.get("shot_type", "")) == "Waist-Up Midshot":
            body = _merge_unique(_upper_build_prompt(profile), _selected_chest_text(profile), profile.get("active_chest_integrity_prompt", ""))

        tattoos = _visible_tattoos_v259(profile, plan)
        tattoo_text = _sentences(*(_tattoo_prompt_v259(record, plan) for record in tattoos))
        piercings = _visible_piercings_v258(profile, plan)
        piercing_text = _sentences(*(_piercing_prompt_v259(record, plan) for record in piercings if isinstance(record, dict)))
        scars = _visible_scars_v258(profile, plan)
        scar_text = _sentences(*(_scar_prompt_v259(record) for record in scars))
        clean_skin = _clean_skin_authority_v259(profile, tattoos, scars, piercings)
        marks = _merge_unique(tattoo_text, piercing_text, scar_text, clean_skin)

        shot = _clean_phrase(plan.get("final_shot_prompt", sections.get("shot_scene", result[2] or "")))
        purpose = str(sections.get("purpose", "A realistic camera photograph"))
        character = str(sections.get("primary_character", result[19] or ""))
        tan = str(sections.get("visible_tan_skin_variation", ""))
        final_authority = _merge_unique(
            _front_view_lock_v259(plan),
            _final_presentation_authority_v259(profile, presentation),
            _final_focus_authority_v259(plan),
            _final_frame_authority_v259(profile, plan),
        )

        final_prompt = _sentences(
            trigger_word if str(generation_purpose).startswith("Krea") else "",
            custom_prefix,
            purpose,
            shot,
            character,
            presentation,
            body,
            tan,
            marks,
            custom_suffix,
            final_authority,
        )
        sections.update({
            "visible_presentation": presentation,
            "visible_body": body,
            "visible_tattoo_records": tattoos,
            "visible_piercing_records": piercings,
            "visible_scar_mole_beauty_mark_records": scars,
            "visible_marks": marks,
            "clean_skin_authority": clean_skin,
            "shot_scene": shot,
            "final_frame_authority": final_authority,
            "final_prompt": final_prompt,
            "routing_mode": str(sections.get("routing_mode", "")) + "+v259_checklist_stabilization",
            "resolved_presentation_mode": _presentation_mode(profile),
        })

        result[2] = shot
        result[3] = presentation
        result[4] = marks
        result[13] = final_prompt
        result[16] = presentation
        result[7] = int(plan.get("recommended_width", result[7]))
        result[8] = int(plan.get("recommended_height", result[8]))
        if str(generation_purpose).startswith("Krea"):
            result[0] = final_prompt
        else:
            result[1] = final_prompt

        notes = str(result[10] or "").replace("V2.4.18", CORE_VERSION)
        notes += (
            "\nStage 0 V2.4.19: final clean-skin, selected-garment, background-focus, front-view, and crop authorities are emitted after body and mark text."
            "\nMarks V2.4.19: front-pelvic tattoos are hidden from rear views; full-leg systems protect knees/posterior surfaces; lip/navel jewelry uses simplified one-object geometry."
        )
        result[10] = notes
        result[18] = json.dumps(sections, indent=2, ensure_ascii=False)
        from .nodes_v246 import _rebuild_active_summary_v246
        result[12] = _rebuild_active_summary_v246(profile, plan, sections, notes)
        return tuple(result)


class QwenDatasetQueueV259(QwenDatasetQueueV258):
    DESCRIPTION = (
        "Compatibility queue registered to V2.4.19. Stage 3 remains manual-review only while Stage 2 regional and reference-required extreme lanes are validated."
    )
