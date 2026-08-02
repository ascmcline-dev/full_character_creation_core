from __future__ import annotations

import copy
import json
import re
from typing import Any

from .nodes_v230 import _clean_phrase, _sentences
from .nodes_v241 import _location_from_text_v241
from .nodes_v243 import _record_visible_v243, _visible_tags_v243
from .nodes_v245 import _coverage_tags_v245
from .nodes_v246 import _rebuild_active_summary_v246
from .nodes_v253 import _piercing_geometry, _tattoo_record_prompt_v253
from .nodes_v256 import (
    CharacterBlueprintCreatorV256,
    CharacterPromptAssemblerV256,
    CharacterShotControlV256,
    QwenDatasetQueueV256,
    _merge_unique,
    _plan_shows_chest,
    _plan_shows_groin,
)

# -----------------------------------------------------------------------------
# V2.4.17 / Studio V2.8.17
# - one canonical, mutually-exclusive chest authority path
# - inactive bust controls retained as saved UI values but removed from all
#   active prompts, summaries, locks, and Stage 2 anatomy fields
# - direct-rear floor-pose camera authority is applied after clothing
# - Extended Puppy uses a shorter landmark-first skeleton
# - Daisy Duke preset remains a complete crop-top + rigid denim cutoff outfit
# - full-leg sleeves remain visible on exposed leg skin below short hems
# - center-lip rings are explicitly lower-lip jewelry and never septum jewelry
# - navel / belly-button structured piercing location
# - optional scar / mole / beauty-mark descriptor box and region-aware records
# -----------------------------------------------------------------------------

SCAR_MARK_FIELD = "scar_mole_beauty_mark_descriptors"

# Positive-only garment construction. Negative category names such as
# "leggings" or "yoga pants" are deliberately absent because Krea can treat
# those words as outfit concepts even when they appear inside exclusions.
DAISY_DUKE_BOTTOM_V257 = (
    "extra-low-rise rigid distressed blue denim cutoff micro-shorts in classic Daisy Duke style; "
    "the denim waistband sits very low across the upper hips at or slightly below the pelvic-bone line; "
    "a metal button, zipper fly, belt loops, front pockets, rear patch pockets, side seams, and two clearly separate very short leg openings are part of the garment; "
    "the irregular raw-cut hems rise high over the upper thighs with visible frayed denim threads; "
    "rear and rear-three-quarter views preserve both rear patch pockets and the very short frayed hem line; "
    "the garment remains rigid woven denim with stable cutoff-short construction in every view"
)


def _insert_after(mapping: dict[str, Any], key: str, additions: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, spec in mapping.items():
        out[name] = spec
        if name == key:
            for add_name, add_spec in additions:
                out[add_name] = add_spec
    return out


def _mark_tags(text: str) -> tuple[str, set[str]]:
    cleaned = _clean_phrase(text)
    location, tags = _location_from_text_v241(cleaned)
    low = cleaned.lower()
    extra: set[str] = set(tags)
    rules = [
        (("above upper lip", "upper lip", "lower lip", "lip"), "Lip / Mouth", {"face", "mouth", "lip", "lips"}),
        (("cheek",), "Cheek", {"face", "cheek"}),
        (("forehead",), "Forehead", {"face", "forehead"}),
        (("chin", "jaw"), "Chin / Jaw", {"face", "chin", "jaw"}),
        (("nose", "nostril"), "Nose", {"face", "nose", "nostril"}),
        (("eye", "eyebrow", "brow"), "Eye / Brow", {"face", "eye", "eyes", "eyebrow"}),
        (("ear",), "Ear", {"face", "ear", "ears"}),
        (("upper full back", "full upper back", "upper back"), "Upper Back", {"upper_back", "shoulders", "back"}),
        (("full back", "entire back"), "Full Back", {"upper_back", "lower_back", "back"}),
        (("lower back",), "Lower Back", {"lower_back", "back", "waist"}),
        (("navel", "belly button"), "Navel", {"abdomen", "navel", "waist"}),
        (("abdomen", "stomach"), "Abdomen", {"abdomen", "waist"}),
        (("left forearm",), "Left Forearm", {"arms", "forearms", "left_forearm"}),
        (("right forearm",), "Right Forearm", {"arms", "forearms", "right_forearm"}),
        (("left leg", "left thigh", "left calf"), "Left Leg", {"legs", "thighs", "calves", "left_leg", "left_thigh", "left_calf"}),
        (("right leg", "right thigh", "right calf"), "Right Leg", {"legs", "thighs", "calves", "right_leg", "right_thigh", "right_calf"}),
    ]
    for tokens, label, mapped in rules:
        if any(token in low for token in tokens):
            if location == "Unspecified":
                location = label
            extra |= mapped
    if len(extra) > 1 and "unknown" in extra:
        extra.discard("unknown")
    if not extra:
        extra.add("unknown")
    return location, extra


def _scar_records(text: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in re.split(r"[\r\n;]+", str(text or "")):
        raw = _clean_phrase(line)
        if not raw:
            continue
        location, tags = _mark_tags(raw)
        records.append({
            "kind": "scar_mole_beauty_mark",
            "raw": raw,
            "description": raw,
            "location": location,
            "region_tags": sorted(tags),
            "quantity": 1,
        })
    return records


def _scar_record_prompt(record: dict[str, Any]) -> str:
    raw = _clean_phrase(record.get("raw", ""))
    location = _clean_phrase(record.get("location", ""))
    if not raw:
        return ""
    low = raw.lower()
    if "mole" in low or "beauty mark" in low:
        kind = "one permanent natural mole or beauty mark"
    elif "scar" in low or "shrapnel" in low or "gunshot" in low or "stab" in low:
        kind = "one permanent healed scar"
    else:
        kind = "one permanent natural skin mark"
    return _sentences(
        f"{kind} remains exactly as described: {raw}",
        f"its location remains fixed at {location.lower()}" if location and location != "Unspecified" else "its documented anatomical location remains fixed",
        "the mark follows the natural skin surface and is not duplicated, mirrored, relocated, converted into a tattoo, or removed",
    )


def _prune_summary(summary: str, resolved_chest: str) -> str:
    lines = str(summary or "").splitlines()
    kept: list[str] = []
    bust_active = resolved_chest == "Bust Anatomy — Use Bust Controls"
    for line in lines:
        low = line.lower().strip()
        if not bust_active and (
            low.startswith("bust vertical placement effect:")
            or low.startswith("clothed bust fidelity:")
            or "augmentation modifies projection" in low
        ):
            continue
        kept.append(line)
    if not bust_active:
        replacement = {
            "Flat / Neutral Chest": "Clothed chest fidelity: the selected flat neutral chest remains minimally projected under normal garments; stored bust controls are inactive.",
            "Masculine Chest — Use Male Chest Control": "Clothed chest fidelity: the selected masculine pectoral structure remains authoritative; stored bust controls are inactive.",
            "Custom Chest Description": "Clothed chest fidelity: only the explicit custom chest description is authoritative; stored bust controls are inactive.",
        }.get(resolved_chest, "Stored bust controls are inactive for the resolved chest selection.")
        # Keep this next to the general garment notes rather than at the very end.
        insert_at = next((i + 1 for i, line in enumerate(kept) if line.startswith("Garment stability:")), len(kept))
        kept.insert(insert_at, replacement)
    return "\n".join(kept)


def _replace_nested(value: Any, old: str, new: str) -> Any:
    if not old or old == new:
        return value
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, list):
        return [_replace_nested(item, old, new) for item in value]
    if isinstance(value, tuple):
        return tuple(_replace_nested(item, old, new) for item in value)
    if isinstance(value, dict):
        return {key: _replace_nested(item, old, new) for key, item in value.items()}
    return value


def _replace_profile_and_outputs(profile: dict[str, Any], result: list[Any], old: str, new: str) -> None:
    if not old or old == new:
        return
    replaced = _replace_nested(profile, old, new)
    profile.clear()
    profile.update(replaced)
    for index, value in enumerate(result):
        result[index] = _replace_nested(value, old, new)


def _canonicalize_chest(profile: dict[str, Any]) -> None:
    resolved = str(profile.get("resolved_chest_anatomy", ""))
    bust_active = resolved == "Bust Anatomy — Use Bust Controls"
    stored = {
        "size": profile.get("bust_size", "Unspecified"),
        "shape": profile.get("bust_shape", "Unspecified"),
        "position": profile.get("bust_position", "Unspecified"),
        "firmness": profile.get("bust_firmness", "Unspecified"),
        "augmentation": profile.get("bust_augmentation", "Unspecified"),
    }
    profile["stored_bust_controls"] = stored
    profile["bust_controls_active"] = bust_active
    if not bust_active:
        profile["bust_anatomy_authority_prompt"] = ""
        profile["bust_clothed_authority_prompt"] = ""
        profile["bust_position_augmentation_summary"] = ""

    chest_anatomy = _clean_phrase(profile.get("chest_anatomy_prompt", ""))
    chest_clothed = _clean_phrase(profile.get("chest_clothed_prompt", ""))
    chest_lock = _clean_phrase(profile.get("chest_region_integrity_prompt", ""))
    profile["active_chest_anatomy_prompt"] = chest_anatomy
    profile["active_chest_clothed_prompt"] = chest_clothed
    profile["active_chest_integrity_prompt"] = chest_lock
    profile["resolved_chest_authority"] = {
        "category": resolved,
        "anatomy_prompt": chest_anatomy,
        "clothed_prompt": chest_clothed,
        "integrity_prompt": chest_lock,
        "bust_controls_active": bust_active,
    }

    body = _clean_phrase(profile.get("body_type_authority_prompt", ""))
    profile["anatomy_upper_body"] = _merge_unique(body, chest_anatomy)
    profile["upper_body_identity"] = profile["anatomy_upper_body"]
    profile["clothed_upper_body"] = _merge_unique(body, chest_clothed)


def _canonical_character_prompts(profile: dict[str, Any]) -> None:
    presentation_mode = str(profile.get("presentation_mode", ""))
    anatomy_upper = _clean_phrase(profile.get("anatomy_upper_body", ""))
    clothed_upper = _clean_phrase(profile.get("clothed_upper_body", ""))
    anatomy_lower = _clean_phrase(profile.get("anatomy_lower_body", ""))
    clothed_lower = _clean_phrase(profile.get("clothed_lower_body", ""))
    if presentation_mode == "Clinical Anatomy":
        active_body = _merge_unique(anatomy_upper, anatomy_lower)
    elif presentation_mode == "Custom Presentation" and str(profile.get("custom_presentation_body_detail", "")) == "Clinical Anatomy — Include Selected Chest / Groin":
        active_body = _merge_unique(anatomy_upper, anatomy_lower)
    else:
        active_body = _merge_unique(clothed_upper, clothed_lower)
    profile["active_body_prompt"] = active_body

    identity = _merge_unique(profile.get("gender_authority_prompt", ""), profile.get("identity_detail_prompt", ""))
    marks = _clean_phrase(profile.get("marks_prompt", ""))
    tattoo_lock = _clean_phrase(profile.get("tattoo_count_lock", ""))
    piercing_lock = _clean_phrase(profile.get("piercing_count_lock", ""))
    active_presentation = _clean_phrase(profile.get("active_presentation_prompt", ""))
    clothed_presentation = _clean_phrase(profile.get("default_clothing_prompt", ""))
    clinical_presentation = "unclothed adult subject in neutral clinical anatomy documentation"
    if profile.get("piercing_entries"):
        clinical_presentation = _merge_unique(clinical_presentation, "only the defined permanent piercings remain")

    profile["active_character_prompt"] = _merge_unique(identity, active_body, active_presentation, marks, tattoo_lock, piercing_lock)
    profile["full_profile_prompt"] = profile["active_character_prompt"]
    profile["clothed_character_prompt"] = _merge_unique(identity, clothed_upper, clothed_lower, clothed_presentation, marks, tattoo_lock, piercing_lock)
    profile["clinical_character_prompt"] = _merge_unique(identity, anatomy_upper, anatomy_lower, clinical_presentation, marks, tattoo_lock, piercing_lock)


def _daisy_presentation(profile: dict[str, Any]) -> str:
    if str(profile.get("outfit_preset", "")) != "High-Hem Crop Top and Daisy Dukes":
        return ""
    components = profile.get("outfit_components") if isinstance(profile.get("outfit_components"), dict) else {}
    top = _clean_phrase(components.get("top", ""))
    bottom = _clean_phrase(components.get("bottom", ""))
    footwear = _clean_phrase(components.get("footwear", ""))
    return _sentences(
        f"wearing {top}" if top else "",
        "the cropped tank remains an ordinary opaque matte cotton-spandex fashion top with natural fabric tension and no special shaping function",
        f"wearing {bottom}" if bottom else "",
        f"wearing {footwear}" if footwear else "",
        "the complete selected crop-top and rigid woven denim cutoff outfit remains visible wherever the full-body frame includes it and retains the same fashion-garment construction throughout",
    )


def _daisy_coverage(profile: dict[str, Any], covered: set[str]) -> set[str]:
    if str(profile.get("outfit_preset", "")) != "High-Hem Crop Top and Daisy Dukes":
        return covered
    # The old parser found the words "leggings" and "full-length pants" inside
    # exclusion text and therefore marked the entire leg as covered. Daisy Dukes
    # cover the pelvis and only the very top of the thighs.
    fixed = set(covered)
    fixed -= {"thighs", "legs", "knees", "shins", "calves", "ankles", "abdomen", "navel", "waist"}
    fixed |= {"hips", "groin", "pubic", "genital", "buttocks", "upper_thighs"}
    return fixed


def _visible_tattoos(profile: dict[str, Any], plan: dict[str, Any]) -> list[dict[str, Any]]:
    visible = _visible_tags_v243(plan)
    covered = _daisy_coverage(profile, _coverage_tags_v245(profile))
    out: list[dict[str, Any]] = []
    for record in profile.get("tattoo_records", []) if isinstance(profile.get("tattoo_records"), list) else []:
        if not isinstance(record, dict):
            continue
        location = str(record.get("location", ""))
        sleeve = location in {"Full Left Leg Sleeve", "Full Right Leg Sleeve"}
        if sleeve and visible & {"legs", "thighs", "knees", "calves", "ankles", "feet"}:
            if not ({"legs", "thighs", "knees", "calves", "ankles"} <= covered):
                out.append(record)
                continue
        if _record_visible_v243(record, visible, covered, plan):
            out.append(record)
    return out


def _visible_scars(profile: dict[str, Any], plan: dict[str, Any]) -> list[dict[str, Any]]:
    visible = _visible_tags_v243(plan)
    covered = _daisy_coverage(profile, _coverage_tags_v245(profile))
    out: list[dict[str, Any]] = []
    for record in profile.get("scar_mole_beauty_mark_records", []) if isinstance(profile.get("scar_mole_beauty_mark_records"), list) else []:
        if isinstance(record, dict) and _record_visible_v243(record, visible, covered, plan):
            out.append(record)
    return out


def _visible_piercings(profile: dict[str, Any], plan: dict[str, Any]) -> list[dict[str, Any]]:
    # Re-evaluate from the canonical current records. Older assemblers do not
    # know the V2.4.17 navel location and can incorrectly drop it.
    visible = _visible_tags_v243(plan)
    covered = _daisy_coverage(profile, _coverage_tags_v245(profile))
    out: list[dict[str, Any]] = []
    for record in profile.get("piercing_records", []) if isinstance(profile.get("piercing_records"), list) else []:
        if isinstance(record, dict) and _record_visible_v243(record, visible, covered, plan):
            out.append(record)
    return out


def _center_lip_location(location: str) -> str:
    low = str(location or "").lower()
    if "center lip" in low:
        return _sentences(
            "through the exact center of the lower-lip vermilion edge, visibly crossing living lower-lip tissue directly below the mouth opening",
            "the complete jewelry remains attached to the lower lip only; the nasal region remains unpierced and contains no jewelry",
        )
    if "navel" in low or "belly button" in low:
        return _sentences(
            "through the defined upper rim of the existing navel at the exact configured belly-button location",
            "the complete jewelry is visibly anchored through living navel-rim tissue and follows the natural centerline of the abdomen",
            "the surrounding abdominal skin contains one natural navel and no duplicate opening",
        )
    # Keep the tested location wording from V2.4.13 for all other sites.
    from .nodes_v253 import _piercing_location
    return _piercing_location(location)


def _piercing_prompt(record: dict[str, Any], plan: dict[str, Any]) -> str:
    location = str(record.get("location", "")).strip()
    material = str(record.get("material", "")).strip().lower()
    jewelry = str(record.get("jewelry_type", "piercing jewelry")).strip().lower()
    quantity = int(record.get("quantity", 1) or 1)
    visibility = str(record.get("visibility", "Normal") or "Normal")
    geometry = _piercing_geometry(jewelry)
    if "center lip" in location.lower() and ("hoop" in jewelry or "ring" in jewelry):
        geometry = _sentences(
            "one small continuous circular lip hoop passes through the center lower-lip edge",
            "the upper arc enters and exits the lower-lip tissue while the lower arc remains clearly visible immediately below the lower lip",
            "the smooth continuous hoop has no bead and remains centered on the lower-lip tissue",
        )
    if "navel" in location.lower() or "belly button" in location.lower():
        geometry = _sentences(
            geometry,
            "the jewelry hangs or curves naturally from the pierced navel rim and remains visibly anchored through that tissue",
        )
    distance_lock = ""
    if location.lower() in {"center lip", "left lip", "right lip"} and str(plan.get("shot_type", "")) in {"Full Body", "Three-Quarter Body", "Wide / Environmental Full Body"}:
        distance_lock = "the lip jewelry remains clearly recognizable at the selected full-body camera distance while staying anatomically plausible in size"
    return _sentences(
        f"exactly {quantity} healed permanent {material} {jewelry} piercing is present at the exact configured {location.lower()}",
        _center_lip_location(location),
        geometry,
        distance_lock,
        f"the selected visibility level is {visibility.lower()} and the jewelry remains visually distinct from nearby facial or body features",
        "the jewelry is physically inserted through living tissue at a healed opening and is not floating, glued on, clipped on, painted on, or resting on the skin",
        "do not add a second opening, detached end, duplicate item, opposite-side item, or relocate the jewelry",
    )


def _final_rear_camera_lock(plan: dict[str, Any]) -> str:
    pose = str(plan.get("pose", "")).lower()
    view = str(plan.get("camera_view", ""))
    if view != "Back View" or not any(token in pose for token in ("all fours", "doggy", "extended puppy", "hands and knees")):
        return ""
    return _sentences(
        "final camera authority after clothing and anatomy: strict direct six-o'clock rear view",
        "the lens center remains aligned with the rear pelvis and sacrum on the spinal midline",
        "both rear hips are equally visible and neither side torso plane dominates",
        "the optical axis is horizontal and parallel to the floor with zero downward tilt",
        "clothing does not alter the camera position",
        "this is not elevated, overhead, diagonal, side, profile, or rear three-quarter",
    )


class CharacterBlueprintCreatorV257(CharacterBlueprintCreatorV256):
    FUNCTION = "build_blueprint_v257"
    DESCRIPTION = (
        "Current Character Creator with one exclusive resolved chest path, independent nonbinary chest/groin locks, navel piercing support, corrected center-lip ring geometry, full-leg tattoo visibility, and an optional scar/mole/beauty-mark descriptor box."
    )

    @classmethod
    def INPUT_TYPES(cls):
        inherited = copy.deepcopy(super().INPUT_TYPES())
        required = inherited.get("required", {})
        loc_spec = required.get("piercing_location")
        if isinstance(loc_spec, tuple) and isinstance(loc_spec[0], list):
            options = list(loc_spec[0])
            if "Navel / Belly Button" not in options:
                insert = options.index("Other") if "Other" in options else len(options)
                options.insert(insert, "Navel / Belly Button")
            required["piercing_location"] = (options, copy.deepcopy(loc_spec[1]) if len(loc_spec) > 1 else {"default": ""})
        required = _insert_after(required, "structured_piercing_custom", [
            (SCAR_MARK_FIELD, ("STRING", {
                "default": "",
                "multiline": True,
                "placeholder": "Optional, one per line: (body area) descriptor — e.g. above upper lip on left side, a small beauty mole",
            })),
        ])
        inherited["required"] = required
        return inherited

    def build_blueprint_v257(self, **kwargs):
        scar_text = str(kwargs.pop(SCAR_MARK_FIELD, ""))
        result = list(super().build_blueprint_v256(**kwargs))
        profile = copy.deepcopy(result[8])

        # Replace the inherited Daisy Duke bottom everywhere with a positive-only
        # construction before any active prompts or coverage are rebuilt.
        if str(kwargs.get("preset_outfit_if_selected", "")) == "High-Hem Crop Top and Daisy Dukes":
            components = copy.deepcopy(profile.get("outfit_components") or {})
            old_bottom = _clean_phrase(components.get("bottom", ""))
            components["bottom"] = DAISY_DUKE_BOTTOM_V257
            profile["outfit_components"] = components
            _replace_profile_and_outputs(profile, result, old_bottom, DAISY_DUKE_BOTTOM_V257)

        _canonicalize_chest(profile)

        scars = _scar_records(scar_text)
        profile[SCAR_MARK_FIELD] = scar_text
        profile["scar_mole_beauty_mark_records"] = scars
        profile["scar_mole_beauty_mark_entries"] = [r["raw"] for r in scars]
        scar_prompt = _sentences(*(_scar_record_prompt(r) for r in scars))
        profile["scar_mole_beauty_mark_prompt"] = scar_prompt
        profile["marks_prompt"] = _merge_unique(profile.get("marks_prompt", ""), scar_prompt)

        # Preserve structured piercing visibility in the record used by the
        # Stage 0 and Stage 2 visibility compilers.
        if str(kwargs.get("piercing_status", "")) == "One" and str(kwargs.get("piercing_input_mode", "")) == "Structured Single Piercing":
            for record in profile.get("piercing_records", []) if isinstance(profile.get("piercing_records"), list) else []:
                if isinstance(record, dict):
                    record["visibility"] = str(kwargs.get("piercing_visibility", "Normal") or "Normal")

        _canonical_character_prompts(profile)
        resolved = str(profile.get("resolved_chest_anatomy", ""))
        profile["presentation_summary"] = _prune_summary(profile.get("presentation_summary", ""), resolved)
        profile["presentation_summary"] += (
            f"\nScar / mole / beauty-mark descriptors: {len(scars)} active"
            "\nPiercing V2.4.17: Center Lip is fixed to living lower-lip tissue; the nasal region remains unpierced. Navel / Belly Button is available as a structured location."
            "\nTattoo V2.4.17: short garments expose the uncovered portions of full-leg sleeves instead of hiding the complete tattoo."
        )
        profile["schema"] = "CHARACTER_BLUEPRINT_V257"
        profile["schema_version"] = 27
        profile["fcc_core_version"] = "2.4.17"
        profile["fcc_studio_version"] = "2.8.17"

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
        result[21] = profile.get("presentation_summary", "")
        return tuple(result)


class CharacterShotControlV257(CharacterShotControlV256):
    FUNCTION = "build_shot_plan_v257"
    DESCRIPTION = (
        "Current Shot Control with landmark-first Extended Puppy geometry and anatomy-relative direct-rear floor-pose camera locks."
    )

    def build_shot_plan_v257(self, **kwargs):
        result = list(super().build_shot_plan_v256(**kwargs))
        plan = copy.deepcopy(result[0])
        pose = str(plan.get("pose", kwargs.get("pose", ""))).lower()
        view = str(plan.get("camera_view", kwargs.get("camera_view", "")))
        if "extended puppy" in pose:
            plan["pose_prompt"] = _sentences(
                "one adult subject performs one extended puppy yoga pose directly on the floor",
                "exactly two knees remain beneath the hip sockets and the pelvis stays elevated above the knees",
                "the chest lowers toward the floor directly in front of the knees",
                "both shoulder joints point toward twelve o'clock in the same direction as the spine",
                "both upper arms, elbows, wrists, and hands extend toward twelve o'clock beyond the crown",
                "the hands are the farthest body landmarks from the knees",
                "the arms remain shoulder-width and never extend toward three o'clock or nine o'clock",
                "the arms never form a T shape, airplane wings, or a line perpendicular to the spine",
                "the complete body remains one connected face-down figure from hands through shoulders, spine, pelvis, knees, shins, and feet",
            )
            if view == "Back View":
                plan["camera_prompt"] = _sentences(
                    "strict direct back view from the six-o'clock position behind the sacrum",
                    "the lens center is aligned with the rear pelvis and sacrum at the subject's pose level",
                    "the optical axis is horizontal and parallel to the floor with zero downward tilt",
                    "both rear hips, knees, and lower legs remain balanced left and right",
                    "the spine and forward arms recede straight toward twelve o'clock away from the lens",
                    "this is not overhead, elevated, diagonal, side, profile, or rear three-quarter",
                    "rectilinear 50mm normal-lens perspective",
                )
                plan["rear_puppy_lock"] = True
        if view == "Back View" and any(token in pose for token in ("all fours", "doggy", "hands and knees")):
            plan["camera_prompt"] = _sentences(
                plan.get("camera_prompt", ""),
                "camera lens centered at the rear pelvis and sacrum height rather than above the body",
                "zero downward tilt; optical axis horizontal and parallel to the floor",
            )
            plan["all_fours_direct_rear_v257"] = True

        plan["schema"] = "FCC_SHOT_PLAN_V257"
        plan["schema_version"] = 27
        plan["fcc_core_version"] = "2.4.17"
        plan["final_shot_prompt"] = _sentences(
            plan.get("framing_prompt", ""), plan.get("crop_authority_prompt", ""),
            plan.get("pose_prompt", ""), plan.get("camera_prompt", ""),
            plan.get("expression_prompt", ""), plan.get("scene_prompt", ""),
            plan.get("environment_prompt", ""), _clean_phrase(kwargs.get("shot_suffix", "")),
        )
        summary = str(plan.get("active_settings_summary", "")).replace("V2.4.16", "V2.4.17")
        if "extended puppy" in pose:
            summary += "\nV2.4.17 Extended Puppy: shoulders, arms, wrists, and hands remain on the twelve-o'clock spine axis; lateral/T-shaped arms are forbidden."
        if view == "Back View" and any(token in pose for token in ("all fours", "doggy", "extended puppy", "hands and knees")):
            summary += "\nV2.4.17 rear camera: lens is centered at sacrum height with a horizontal optical axis; clothing cannot convert the shot into overhead or rear three-quarter."
        plan["active_settings_summary"] = summary
        result[0] = plan
        result[1] = plan["final_shot_prompt"]
        result[3] = plan.get("camera_prompt", "")
        result[4] = plan.get("pose_prompt", "")
        result[7] = summary
        result[8] = json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True)
        return tuple(result)


class CharacterPromptAssemblerV257(CharacterPromptAssemblerV256):
    FUNCTION = "assemble_prompt_v257"
    DESCRIPTION = (
        "Current prompt compiler with exclusive chest authority, complete Daisy Duke routing, exposed full-leg sleeve visibility, corrected center-lip/navel piercings, region-aware scars and beauty marks, and final post-clothing rear-camera locks."
    )

    def assemble_prompt_v257(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        result = list(super().assemble_prompt_v256(
            character_blueprint, shot_plan, generation_purpose, reference_label,
            trigger_word, custom_prefix, custom_suffix,
        ))
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan = shot_plan if isinstance(shot_plan, dict) else {}
        try:
            sections = json.loads(result[18]) if result[18] else {}
        except Exception:
            sections = {}

        # One exclusive visible chest path. The lock remains separate and is
        # emitted once by the V2.4.16 visibility gate.
        visible_body = str(sections.get("visible_body", "") or "")
        if str(profile.get("resolved_chest_anatomy", "")) != "Bust Anatomy — Use Bust Controls":
            visible_body = re.sub(r"the selected athletic compression garment supports the chest.*?clothing\.", "", visible_body, flags=re.I | re.S)
        elif str(profile.get("outfit_preset", "")) == "High-Hem Crop Top and Daisy Dukes":
            visible_body = re.sub(
                r"the selected athletic compression garment supports the chest and may moderately reduce visible projection as an intentional garment effect",
                "the selected opaque fashion crop top follows the configured covered bust contour with ordinary fabric fit and natural tension",
                visible_body,
                flags=re.I,
            )
        sections["visible_body"] = _clean_phrase(visible_body)

        daisy = _daisy_presentation(profile)
        if daisy:
            sections["visible_presentation"] = daisy
            result[3] = daisy
            result[16] = daisy

        tattoos = _visible_tattoos(profile, plan)
        tattoo_text = _sentences(*(_tattoo_record_prompt_v253(record, plan) for record in tattoos))
        piercings = _visible_piercings(profile, plan)
        piercing_text = _sentences(*(_piercing_prompt(record, plan) for record in piercings if isinstance(record, dict)))
        sections["visible_piercing_records"] = piercings
        scars = _visible_scars(profile, plan)
        scar_text = _sentences(*(_scar_record_prompt(record) for record in scars))
        marks = _merge_unique(tattoo_text, piercing_text, scar_text)
        sections["visible_tattoo_records"] = tattoos
        sections["visible_scar_mole_beauty_mark_records"] = scars
        sections["visible_marks"] = marks
        result[4] = marks

        rear_lock = _final_rear_camera_lock(plan)
        shot = _merge_unique(sections.get("shot_scene", result[2] or ""), rear_lock)
        sections["shot_scene"] = shot
        result[2] = shot

        purpose = str(sections.get("purpose", "A realistic camera photograph"))
        character = str(sections.get("primary_character", result[19] or ""))
        presentation = str(sections.get("visible_presentation", result[3] or ""))
        body = str(sections.get("visible_body", ""))
        tan = str(sections.get("visible_tan_skin_variation", ""))
        final_prompt = _sentences(
            trigger_word if str(generation_purpose).startswith("Krea") else "",
            custom_prefix, purpose, shot, character, presentation, body, tan, marks, custom_suffix,
        )
        sections["final_prompt"] = final_prompt
        sections["routing_mode"] = str(sections.get("routing_mode", "")) + "+v257_stage0_alignment"
        result[13] = final_prompt
        if str(generation_purpose).startswith("Krea"):
            result[0] = final_prompt
        else:
            result[1] = final_prompt

        notes = str(result[10] or "").replace("V2.4.16", "V2.4.17")
        notes += (
            "\nStage 0 V2.4.17: inactive bust controls are absent from non-bust routes; Daisy Dukes remain rigid denim cutoffs; exposed full-leg sleeves remain visible; center-lip/navel jewelry and permanent scars/moles use location-specific geometry."
        )
        result[10] = notes
        result[18] = json.dumps(sections, indent=2, ensure_ascii=False)
        result[12] = _rebuild_active_summary_v246(profile, plan, sections, notes)
        return tuple(result)


class QwenDatasetQueueV257(QwenDatasetQueueV256):
    DESCRIPTION = (
        "Compatibility queue registered to V2.4.17. Stage 3 remains deferred until Stage 0 and Stage 2 live validation is complete."
    )
