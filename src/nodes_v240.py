from __future__ import annotations

import copy
import json
import re
from collections import Counter
from typing import Any

from .nodes import FCCDatasetDirector, FCCQueueItemRouter, _dataset_specs, _slug
from .nodes_v230 import (
    CharacterBlueprintCreatorV230,
    CharacterPromptAssemblerV230,
    CharacterShotControlV230,
    QwenDatasetQueueV230,
    _clean_phrase,
    _crop_prompt_v230,
    _extreme_macro_sections_v231,
    _focus_identity_prompt_v231,
    _focus_is_v231,
    _focus_local_camera_v231,
    _focus_value_v231,
    _is_clinical,
    _is_extreme_closeup_v231,
    _sentences,
)

# -----------------------------------------------------------------------------
# V2.4.0 visibility compiler
# Complete character data stays in the blueprint. Generator prompts receive only
# the details that are visible in the selected crop and not covered by clothing.
# -----------------------------------------------------------------------------

TAN_LEVELS_V240 = [
    "None",
    "Light Tan",
    "Medium Tan",
    "Dark Tan",
    "Custom",
]
TAN_LINE_STATES_V240 = [
    "Even Tan — No Defined Lines",
    "Subtle Tan Lines",
    "Defined Tan Lines",
    "Custom",
]
TAN_LINE_PATTERNS_V240 = [
    "Bikini Top and Bottom",
    "One-Piece Swimwear",
    "Bra and Brief",
    "Tank Top",
    "T-Shirt",
    "Shorts",
    "Socks / Footwear",
    "Mixed Clothing Tan Lines",
    "Custom",
]
TAN_LINE_VISIBILITY_V240 = ["Subtle", "Moderate", "Distinct"]

TAN_PATTERN_REGIONS_V240 = {
    "Bikini Top and Bottom": {"chest", "upper_back", "hips", "groin", "buttocks", "upper_thighs"},
    "One-Piece Swimwear": {"shoulders", "chest", "upper_back", "lower_back", "hips", "groin", "buttocks"},
    "Bra and Brief": {"chest", "upper_back", "hips", "groin", "buttocks"},
    "Tank Top": {"shoulders", "upper_chest", "upper_back", "upper_arms"},
    "T-Shirt": {"neck", "upper_arms", "forearms"},
    "Shorts": {"upper_thighs", "thighs", "legs"},
    "Socks / Footwear": {"ankles", "feet"},
    "Mixed Clothing Tan Lines": {"chest", "upper_back", "hips", "groin", "buttocks", "thighs", "legs", "ankles", "feet"},
    "Custom": {"custom"},
}

FACE_TAGS = {
    "face", "hairline", "forehead", "eye", "eyes", "eyebrow", "eyebrows",
    "nose", "nostril", "septum", "bridge", "lip", "lips", "mouth", "chin",
    "jaw", "ear", "ears", "temple", "cheek", "neck",
}
UPPER_TAGS = {"shoulders", "upper_chest", "chest", "breast", "nipple", "areola", "upper_back", "upper_arms", "arms"}
MID_TAGS = {"abdomen", "waist", "navel", "lower_back", "forearms", "hands"}
LOWER_TAGS = {"hips", "groin", "pubic", "genital", "buttocks", "thighs", "upper_thighs", "legs", "knees", "ankles", "feet"}

LOCATION_RULES: list[tuple[tuple[str, ...], str, set[str]]] = [
    (("left eyebrow",), "Left Eyebrow", {"face", "eyebrow", "left_eyebrow", "forehead"}),
    (("right eyebrow",), "Right Eyebrow", {"face", "eyebrow", "right_eyebrow", "forehead"}),
    (("left nostril",), "Left Nostril", {"face", "nose", "nostril", "left_nostril"}),
    (("right nostril",), "Right Nostril", {"face", "nose", "nostril", "right_nostril"}),
    (("septum",), "Septum", {"face", "nose", "septum", "nostril"}),
    (("nose bridge", "bridge"), "Bridge", {"face", "nose", "bridge"}),
    (("left lip",), "Left Lip", {"face", "lip", "mouth", "left_lip"}),
    (("right lip",), "Right Lip", {"face", "lip", "mouth", "right_lip"}),
    (("center lip", "labret"), "Center Lip", {"face", "lip", "mouth", "center_lip", "chin"}),
    (("left ear",), "Left Ear", {"face", "ear", "left_ear"}),
    (("right ear",), "Right Ear", {"face", "ear", "right_ear"}),
    (("left nipple", "left areola"), "Left Nipple", {"chest", "breast", "nipple", "areola", "left_nipple"}),
    (("right nipple", "right areola"), "Right Nipple", {"chest", "breast", "nipple", "areola", "right_nipple"}),
    (("upper left chest", "left upper chest", "left breast"), "Upper Left Chest", {"chest", "upper_chest", "breast", "left_chest"}),
    (("upper right chest", "right upper chest", "right breast"), "Upper Right Chest", {"chest", "upper_chest", "breast", "right_chest"}),
    (("chest", "breast"), "Chest", {"chest", "breast"}),
    (("left forearm",), "Left Forearm", {"arms", "forearms", "left_forearm"}),
    (("right forearm",), "Right Forearm", {"arms", "forearms", "right_forearm"}),
    (("left upper arm",), "Left Upper Arm", {"arms", "upper_arms", "left_upper_arm"}),
    (("right upper arm",), "Right Upper Arm", {"arms", "upper_arms", "right_upper_arm"}),
    (("left arm",), "Left Arm", {"arms", "upper_arms", "forearms", "left_arm"}),
    (("right arm",), "Right Arm", {"arms", "upper_arms", "forearms", "right_arm"}),
    (("left hand",), "Left Hand", {"hands", "left_hand"}),
    (("right hand",), "Right Hand", {"hands", "right_hand"}),
    (("abdomen", "stomach"), "Abdomen", {"abdomen", "waist"}),
    (("navel", "belly button"), "Navel", {"abdomen", "navel", "waist"}),
    (("lower back",), "Lower Back", {"lower_back", "waist"}),
    (("upper back",), "Upper Back", {"upper_back", "shoulders"}),
    (("left hip",), "Left Hip", {"hips", "left_hip"}),
    (("right hip",), "Right Hip", {"hips", "right_hip"}),
    (("hip",), "Hip", {"hips"}),
    (("pubic mons", "mons pubis"), "Pubic Mons", {"groin", "pubic"}),
    (("groin", "pelvis"), "Groin", {"groin", "pubic", "genital"}),
    (("left buttock",), "Left Buttock", {"buttocks", "left_buttock"}),
    (("right buttock",), "Right Buttock", {"buttocks", "right_buttock"}),
    (("buttock", "glute"), "Buttocks", {"buttocks"}),
    (("left thigh",), "Left Thigh", {"thighs", "upper_thighs", "left_thigh"}),
    (("right thigh",), "Right Thigh", {"thighs", "upper_thighs", "right_thigh"}),
    (("thigh",), "Thigh", {"thighs", "upper_thighs"}),
    (("left foot",), "Left Foot", {"feet", "left_foot", "ankles"}),
    (("right foot",), "Right Foot", {"feet", "right_foot", "ankles"}),
    (("foot", "feet"), "Foot", {"feet", "ankles"}),
]

MATERIALS = ["black titanium", "silver titanium", "rose gold", "gold", "steel", "titanium", "silver"]
JEWELRY_TYPES = ["curved barbell", "straight barbell", "circular barbell", "decorative ring", "seam ring", "horseshoe", "clicker", "barbell", "hoop", "stud", "ring"]


def _insert_after(mapping: dict, after_key: str, additions: list[tuple[str, Any]]) -> dict:
    out: dict = {}
    for key, value in mapping.items():
        out[key] = value
        if key == after_key:
            for name, spec in additions:
                out[name] = spec
    return out


def _location_from_text(text: str) -> tuple[str, set[str]]:
    value = str(text or "").lower()
    for tokens, label, tags in LOCATION_RULES:
        if any(token in value for token in tokens):
            return label, set(tags)
    return "Unspecified", {"unknown"}


def _parse_tattoo_record(entry: str) -> dict[str, Any]:
    raw = _clean_phrase(entry)
    location, tags = _location_from_text(raw)
    return {
        "kind": "tattoo",
        "raw": raw,
        "location": location,
        "region_tags": sorted(tags),
        "quantity": 1,
    }


def _parse_piercing_record(entry: str) -> dict[str, Any]:
    raw = _clean_phrase(entry)
    low = raw.lower()
    location, tags = _location_from_text(raw)
    material = next((m.title() for m in MATERIALS if m in low), "")
    jewelry = next((j.title() for j in JEWELRY_TYPES if j in low), "")
    custom = raw
    for token in sorted([location.lower(), material.lower(), jewelry.lower()], key=len, reverse=True):
        if token and token != "unspecified":
            custom = re.sub(re.escape(token), "", custom, flags=re.IGNORECASE)
    custom = re.sub(r"\s+", " ", custom).strip(" ,.;-")
    return {
        "kind": "piercing",
        "raw": raw,
        "location": location,
        "region_tags": sorted(tags),
        "material": material,
        "jewelry_type": jewelry,
        "custom_detail": custom,
        "quantity": 1,
    }


def _group_piercing_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for record in records:
        key = (
            record.get("location", "Unspecified"),
            record.get("material", ""),
            record.get("jewelry_type", ""),
            record.get("custom_detail", ""),
        )
        if key not in groups:
            groups[key] = copy.deepcopy(record)
        else:
            groups[key]["quantity"] = int(groups[key].get("quantity", 1)) + 1
    return list(groups.values())


def _article(text: str) -> str:
    return "an" if str(text or "").strip().lower()[:1] in "aeiou" else "a"


def _piercing_phrase(record: dict[str, Any]) -> str:
    quantity = int(record.get("quantity", 1))
    location = str(record.get("location", "Unspecified"))
    material = str(record.get("material", "")).lower()
    jewelry = str(record.get("jewelry_type", "")).lower()
    custom = str(record.get("custom_detail", "")).strip()
    item = " ".join(x for x in (material, jewelry) if x).strip() or custom or "piercing jewelry"
    anatomical = f"the primary character's anatomical {location.lower()}"
    if location == "Septum":
        if quantity == 1:
            phrase = f"{_article(item)} {item} through the central nasal septum directly beneath the nose"
        elif quantity == 2:
            phrase = f"two closely arranged {item}s through the central nasal septum directly beneath the nose"
        else:
            phrase = f"{quantity} closely arranged {item}s through the central nasal septum directly beneath the nose"
    elif quantity == 1:
        phrase = f"{_article(item)} {item} on {anatomical}"
    elif quantity == 2:
        phrase = f"two small closely spaced {item}s on {anatomical}"
    else:
        phrase = f"{quantity} closely grouped {item}s on {anatomical}"
    if custom and custom.lower() not in phrase.lower():
        phrase += f", {custom}"
    return phrase


def _tattoo_phrase(record: dict[str, Any]) -> str:
    raw = str(record.get("raw", "")).strip()
    return raw[:1].lower() + raw[1:] if raw else ""


def _tan_base_prompt(profile: dict) -> str:
    level = profile.get("tan_level", "None")
    if level == "None":
        return ""
    if level == "Custom":
        return _clean_phrase(profile.get("custom_tan_description", ""))
    return f"{level.lower()} with natural variation across the visible skin"


def _focus_tags(focus: str) -> set[str]:
    f = str(focus or "").lower()
    location, tags = _location_from_text(f)
    if "complete face" in f or "facial profile" in f:
        return set(FACE_TAGS)
    if "both eyes" in f:
        return {"face", "eye", "eyes", "eyebrow", "eyebrows", "nose", "bridge", "forehead"}
    if "left eye" in f:
        return {"face", "eye", "eyebrow", "left_eyebrow", "forehead", "temple", "cheek", "nose"}
    if "right eye" in f:
        return {"face", "eye", "eyebrow", "right_eyebrow", "forehead", "temple", "cheek", "nose"}
    if "nose and septum" in f or "nose and mouth" in f:
        return {"face", "nose", "nostril", "septum", "bridge", "mouth", "lip"}
    if "mouth" in f:
        return {"face", "mouth", "lip", "chin", "nose"}
    if "forehead" in f or "hairline" in f:
        return {"face", "forehead", "hairline", "eyebrow", "temple"}
    if "nipple" in f or "areola" in f:
        return {"chest", "breast", "nipple", "areola"} | tags
    if "pubic" in f or "genital" in f:
        return {"groin", "pubic", "genital"}
    if tags != {"unknown"}:
        return tags
    return {"unknown"}


def _visible_tags(plan: dict) -> set[str]:
    if _is_extreme_closeup_v231(plan):
        return _focus_tags(_focus_value_v231(plan))
    shot = str(plan.get("shot_type", "")).lower()
    focus = str(plan.get("focus_region", "")).lower()
    if "regional" in shot:
        tags = _focus_tags(focus)
        if tags != {"unknown"}:
            return tags
        if "face" in focus or "head" in focus:
            return set(FACE_TAGS)
        if "chest" in focus or "ribcage" in focus:
            return set(UPPER_TAGS) | {"neck"}
        if "abdomen" in focus or "waist" in focus:
            return set(MID_TAGS) | {"chest"}
        if any(x in focus for x in ("groin", "pelvis", "hip", "butt", "thigh", "feet", "foot")):
            return set(LOWER_TAGS) | set(MID_TAGS)
        if "arm" in focus:
            return {"arms", "upper_arms", "forearms", "hands"}
    if "face close" in shot:
        return set(FACE_TAGS) | {"shoulders"}
    if "head and shoulders" in shot:
        return set(FACE_TAGS) | {"shoulders", "upper_chest"}
    if "chest-up" in shot or "chest up" in shot:
        return set(FACE_TAGS) | set(UPPER_TAGS) | {"neck"}
    if "waist-up" in shot or "midshot" in shot:
        return set(FACE_TAGS) | set(UPPER_TAGS) | set(MID_TAGS) | {"neck"}
    if "three-quarter" in shot:
        return set(FACE_TAGS) | set(UPPER_TAGS) | set(MID_TAGS) | {"hips", "thighs", "knees", "neck"}
    if "full body" in shot:
        return set(FACE_TAGS) | set(UPPER_TAGS) | set(MID_TAGS) | set(LOWER_TAGS) | {"neck"}
    return set(FACE_TAGS) | set(UPPER_TAGS) | set(MID_TAGS) | set(LOWER_TAGS)


def _coverage_tags(profile: dict) -> set[str]:
    if profile.get("presentation_mode") != "Clothed Character":
        return set()
    components = profile.get("outfit_components") if isinstance(profile.get("outfit_components"), dict) else {}
    top = " ".join(str(components.get(k, "")) for k in ("top", "one_piece", "outerwear", "raw")).lower()
    bottom = " ".join(str(components.get(k, "")) for k in ("bottom", "one_piece", "swimwear_bottom", "raw")).lower()
    footwear = str(components.get("footwear", "")).lower()
    covered = {"nipple", "areola", "breast", "groin", "pubic", "genital", "buttocks"}
    if top:
        covered |= {"chest", "abdomen", "upper_back", "lower_back"}
        if any(x in top for x in ("long sleeve", "long-sleeve", "jacket", "hoodie", "sweater", "coat")):
            covered |= {"upper_arms", "forearms", "arms"}
        elif any(x in top for x in ("t-shirt", "tee", "short sleeve", "short-sleeve")):
            covered |= {"upper_arms"}
    if bottom:
        covered |= {"hips", "groin", "pubic", "genital", "buttocks", "upper_thighs"}
        if any(x in bottom for x in ("jeans", "pants", "trousers", "leggings")):
            covered |= {"thighs", "legs", "knees"}
        elif "short" in bottom:
            covered |= {"upper_thighs"}
    if footwear:
        covered |= {"feet"}
    return covered


def _record_visible(record: dict[str, Any], visible: set[str], covered: set[str]) -> bool:
    tags = set(record.get("region_tags", []))
    if "unknown" in tags:
        return "full_body" in visible or len(visible & LOWER_TAGS) > 4
    if not tags.intersection(visible):
        return False
    if tags.intersection(covered):
        # A mark may have both broad and exposed tags. Require at least one specific
        # visible tag that is not covered.
        exposed = tags.intersection(visible) - covered
        return bool(exposed)
    return True


def _record_matches_extreme_focus(record: dict[str, Any], focus: str) -> bool:
    location = str(record.get("location", "Unspecified"))
    f = str(focus or "").lower()
    if "complete face" in f or "facial profile" in f:
        return bool(set(record.get("region_tags", [])).intersection(FACE_TAGS))
    if "left eye" in f:
        return location in {"Left Eyebrow"} or "left eye" in str(record.get("raw", "")).lower()
    if "right eye" in f:
        return location in {"Right Eyebrow"} or "right eye" in str(record.get("raw", "")).lower()
    if "both eyes" in f:
        return location in {"Left Eyebrow", "Right Eyebrow", "Bridge"}
    if "nose and septum" in f or "nose and mouth" in f:
        return location in {"Left Nostril", "Right Nostril", "Septum", "Bridge", "Left Lip", "Right Lip", "Center Lip"}
    if "mouth" in f:
        return location in {"Left Lip", "Right Lip", "Center Lip"}
    if "forehead" in f or "hairline" in f:
        return location in {"Left Eyebrow", "Right Eyebrow"} or "forehead" in str(record.get("raw", "")).lower()
    tags = set(record.get("region_tags", []))
    return bool(tags.intersection(_focus_tags(focus)))


def _visible_marks(profile: dict, plan: dict) -> tuple[str, list[dict], list[dict]]:
    visible = _visible_tags(plan)
    covered = _coverage_tags(profile)
    extreme = _is_extreme_closeup_v231(plan)
    focus = _focus_value_v231(plan) if extreme else ""
    tattoos = [r for r in profile.get("tattoo_records", []) if _record_visible(r, visible, covered) and (not extreme or _record_matches_extreme_focus(r, focus))]
    piercings = [r for r in profile.get("piercing_records", []) if _record_visible(r, visible, covered) and (not extreme or _record_matches_extreme_focus(r, focus))]
    tattoo_phrases = [_tattoo_phrase(r) for r in tattoos if _tattoo_phrase(r)]
    piercing_phrases = [_piercing_phrase(r) for r in piercings if _piercing_phrase(r)]
    parts: list[str] = []
    if tattoo_phrases:
        parts.append("visible permanent skin marking: " + "; ".join(tattoo_phrases))
    if piercing_phrases:
        parts.append("visible permanent jewelry: " + "; ".join(piercing_phrases))
    return _sentences(*parts), tattoos, piercings


def _tan_prompt_for_plan(profile: dict, plan: dict) -> str:
    base = _tan_base_prompt(profile)
    if not base:
        return ""
    state = profile.get("tan_line_state", "Even Tan — No Defined Lines")
    if state == "Even Tan — No Defined Lines":
        return base
    visible = _visible_tags(plan)
    pattern = profile.get("tan_line_pattern", "Bikini Top and Bottom")
    regions = set(profile.get("tan_line_regions", [])) or TAN_PATTERN_REGIONS_V240.get(pattern, set())
    if "custom" not in regions and not visible.intersection(regions):
        return base
    if state == "Custom":
        custom = _clean_phrase(profile.get("custom_tan_description", ""))
        return _sentences(base, custom)
    strength = str(profile.get("tan_line_visibility", "Moderate")).lower()
    pattern_text = pattern.lower().replace("top and bottom", "top-and-bottom")
    return _sentences(base, f"{strength} natural lighter {pattern_text} tan-line boundaries across the visible skin in this crop")


def _pubic_prompt_with_color(old_prompt: str, hair_color: str) -> str:
    old = _clean_phrase(old_prompt)
    color = _clean_phrase(hair_color)
    if not old or not color or color.lower() in {"unspecified", "custom / unspecified"}:
        return old
    if re.search(r"\b(?:black|brown|blonde|blond|red|auburn|gray|grey|white|purple|blue|pink|green)\b", old, re.I):
        return old
    return _sentences(old, f"the pubic hair color matches the character's {color.lower()} hair color")


def _upper_body_shape(profile: dict) -> str:
    body = str(profile.get("body_type", "Average"))
    prompts = {
        "Very Slim": "a distinctly slim shoulder, arm, and upper-torso silhouette",
        "Slim": "a lean shoulder, arm, and upper-torso silhouette",
        "Average": "an average balanced shoulder and upper-torso silhouette",
        "Athletic": "an athletic upper-body silhouette with trained shoulders and arms and a firm torso",
        "Curvy": "a naturally curvy upper-torso silhouette with a defined waist",
        "Full-Figured": "a full upper-torso silhouette with substantial natural body volume",
        "Muscular": "a muscular upper-body silhouette with broad shoulders and developed arms",
        "Heavyset": "a broad heavyset upper-body silhouette with substantial torso volume",
    }
    return prompts.get(body, "")


def _clothed_bust_size_only(profile: dict) -> str:
    if profile.get("resolved_chest_anatomy") != "Bust Anatomy — Use Bust Controls":
        return ""
    size = str(profile.get("bust_size", "Unspecified"))
    if size == "Unspecified":
        return ""
    return f"the selected {size.lower()} bust size subtly shapes the fitted upper garment while the garment keeps normal coverage"


def _visible_body_and_presentation(profile: dict, plan: dict) -> tuple[str, str, str]:
    visible = _visible_tags(plan)
    presentation_mode = profile.get("presentation_mode", "Clothed Character")
    is_clinical = presentation_mode == "Clinical Anatomy"
    body_parts: list[str] = []

    face_only = visible.issubset(FACE_TAGS | {"shoulders", "upper_chest", "neck"})
    upper_visible = bool(visible.intersection(UPPER_TAGS | MID_TAGS))
    lower_visible = bool(visible.intersection(LOWER_TAGS))
    groin_visible = bool(visible.intersection({"groin", "pubic", "genital"}))

    if not face_only:
        if is_clinical:
            if upper_visible:
                body_parts.append(_clean_phrase(profile.get("anatomy_upper_body", "")))
            if lower_visible:
                lower = _clean_phrase(profile.get("anatomy_lower_body", ""))
                pubic = _clean_phrase(profile.get("pubic_hair_prompt", "")) if groin_visible else ""
                groin = _clean_phrase(profile.get("groin_anatomy_prompt", "")) if groin_visible else ""
                if groin and groin in lower:
                    lower = lower.replace(groin, "").strip(" ,.;")
                if pubic and pubic in lower:
                    lower = lower.replace(pubic, "").strip(" ,.;")
                body_parts.extend([lower, groin, pubic])
        else:
            if upper_visible:
                body_parts.append(_upper_body_shape(profile))
                # Clothing hides detailed bust shape, placement, firmness, augmentation.
                body_parts.append(_clothed_bust_size_only(profile))
            if lower_visible:
                body_parts.append(_clean_phrase(profile.get("clothed_lower_body", "")))

    if presentation_mode == "Clothed Character":
        components = profile.get("outfit_components") if isinstance(profile.get("outfit_components"), dict) else {}
        top = _clean_phrase(components.get("top") or components.get("one_piece") or components.get("raw") or "")
        bottom = _clean_phrase(components.get("bottom") or components.get("one_piece") or components.get("raw") or "")
        footwear = _clean_phrase(components.get("footwear", ""))
        if visible.issubset(FACE_TAGS | {"shoulders", "upper_chest", "neck"}):
            presentation = f"the visible upper-garment edge is {top}" if top else ""
        elif upper_visible and not lower_visible:
            presentation = f"wearing {top} with normal fit and coverage" if top else _clean_phrase(profile.get("active_presentation_prompt", ""))
        else:
            presentation = _sentences(
                f"wearing {top}" if top else "",
                f"with {bottom}" if bottom else "",
                f"and {footwear}" if footwear and "feet" in visible else "",
                "the selected outfit keeps normal construction, fit, and coverage",
            )
    elif presentation_mode == "Clinical Anatomy":
        presentation = "unclothed neutral non-aroused clinical anatomy documentation"
    else:
        presentation = _clean_phrase(profile.get("active_presentation_prompt", ""))

    return _sentences(*body_parts), presentation, "clinical" if is_clinical else "clothed"


class CharacterBlueprintCreatorV240(CharacterBlueprintCreatorV230):
    FUNCTION = "build_blueprint_v240"
    DESCRIPTION = (
        "Current Character Creator with structured tan controls, crop-safe mark records, automatic single-piercing source resolution, "
        "and pubic-hair color matched to the selected hair color."
    )

    @classmethod
    def INPUT_TYPES(cls):
        base = copy.deepcopy(super().INPUT_TYPES())
        required = base["required"]
        required = _insert_after(required, "complexion", [
            ("tan_level", (TAN_LEVELS_V240, {"default": "None"})),
            ("tan_line_state", (TAN_LINE_STATES_V240, {"default": "Even Tan — No Defined Lines"})),
            ("tan_line_pattern", (TAN_LINE_PATTERNS_V240, {"default": "Bikini Top and Bottom"})),
            ("tan_line_visibility", (TAN_LINE_VISIBILITY_V240, {"default": "Moderate"})),
            ("custom_tan_description", ("STRING", {"default": "", "multiline": True})),
        ])
        base["required"] = required
        return base

    def build_blueprint_v240(self, **kwargs):
        tan_level = kwargs.pop("tan_level")
        tan_line_state = kwargs.pop("tan_line_state")
        tan_line_pattern = kwargs.pop("tan_line_pattern")
        tan_line_visibility = kwargs.pop("tan_line_visibility")
        custom_tan_description = kwargs.pop("custom_tan_description")

        # Automatically choose the populated single-piercing source.
        auto_warning = ""
        if kwargs.get("piercing_status") == "One":
            descriptor_filled = bool(str(kwargs.get("piercing_descriptors", "")).strip())
            structured_filled = bool(str(kwargs.get("piercing_location", "")).strip() or str(kwargs.get("structured_piercing_custom", "")).strip())
            if kwargs.get("piercing_input_mode") == "Descriptor List" and not descriptor_filled and structured_filled:
                kwargs["piercing_input_mode"] = "Structured Single Piercing"
                auto_warning = "Single piercing source automatically switched to Structured Single Piercing because the descriptor box was blank."
            elif kwargs.get("piercing_input_mode") == "Structured Single Piercing" and not structured_filled and descriptor_filled:
                kwargs["piercing_input_mode"] = "Descriptor List"
                auto_warning = "Single piercing source automatically switched to Descriptor List because the structured location was blank."

        result = list(super().build_blueprint_v230(**kwargs))
        profile = copy.deepcopy(result[8])

        hair_color = str(profile.get("hair_color", ""))
        old_pubic = str(profile.get("pubic_hair_prompt", ""))
        new_pubic = _pubic_prompt_with_color(old_pubic, hair_color)
        profile["pubic_hair_prompt"] = new_pubic
        if old_pubic and new_pubic != old_pubic:
            for key in ("anatomy_lower_body", "lower_body_identity", "clinical_character_prompt"):
                profile[key] = str(profile.get(key, "")).replace(old_pubic, new_pubic)
            result[2] = str(result[2]).replace(old_pubic, new_pubic)
            result[13] = str(result[13]).replace(old_pubic, new_pubic)

        tattoo_records = [_parse_tattoo_record(x) for x in profile.get("tattoo_entries", [])]
        if kwargs.get("piercing_status") == "One" and kwargs.get("piercing_input_mode") == "Structured Single Piercing":
            location = kwargs.get("piercing_location", "") or "Unspecified"
            _, tags = _location_from_text(location)
            if location == "Other" and kwargs.get("structured_piercing_custom", "").strip():
                parsed_location, parsed_tags = _location_from_text(kwargs.get("structured_piercing_custom", ""))
                if parsed_location != "Unspecified":
                    location, tags = parsed_location, parsed_tags
            piercing_records = [{
                "kind": "piercing",
                "raw": _clean_phrase(" ".join(x for x in (location, kwargs.get("piercing_material", ""), kwargs.get("piercing_type", ""), kwargs.get("structured_piercing_custom", "")) if x)),
                "location": location,
                "region_tags": sorted(tags),
                "material": kwargs.get("piercing_material", ""),
                "jewelry_type": kwargs.get("piercing_type", ""),
                "custom_detail": _clean_phrase(kwargs.get("structured_piercing_custom", "")),
                "quantity": 1,
            }]
        else:
            piercing_records = _group_piercing_records([_parse_piercing_record(x) for x in profile.get("piercing_entries", [])])

        concise_tattoos = [_tattoo_phrase(r) for r in tattoo_records if _tattoo_phrase(r)]
        concise_piercings = [_piercing_phrase(r) for r in piercing_records if _piercing_phrase(r)]
        concise_marks = _sentences(
            "permanent skin marking: " + "; ".join(concise_tattoos) if concise_tattoos else "",
            "permanent jewelry: " + "; ".join(concise_piercings) if concise_piercings else "",
        )

        tan_regions = sorted(TAN_PATTERN_REGIONS_V240.get(tan_line_pattern, set()))
        profile.update({
            "schema": "CHARACTER_BLUEPRINT_V240",
            "schema_version": 12,
            "tan_level": tan_level,
            "tan_line_state": tan_line_state,
            "tan_line_pattern": tan_line_pattern,
            "tan_line_visibility": tan_line_visibility,
            "custom_tan_description": custom_tan_description,
            "tan_line_regions": tan_regions,
            "tan_base_prompt": _tan_base_prompt({
                "tan_level": tan_level,
                "custom_tan_description": custom_tan_description,
            }),
            "tattoo_records": tattoo_records,
            "piercing_records": piercing_records,
            "marks_prompt": concise_marks,
            "piercing_input_mode": kwargs.get("piercing_input_mode", profile.get("piercing_input_mode")),
        })

        # Keep the complete blueprint readable, but remove aggressive global locks
        # from any full-profile text that could be connected accidentally.
        active_character = _sentences(
            profile.get("gender_authority_prompt", ""),
            profile.get("identity_detail_prompt", ""),
            profile.get("active_body_prompt", ""),
            profile.get("active_presentation_prompt", ""),
            concise_marks,
        )
        profile["active_character_prompt"] = active_character
        profile["full_profile_prompt"] = active_character
        profile["clothed_character_prompt"] = _sentences(
            profile.get("gender_authority_prompt", ""), profile.get("identity_detail_prompt", ""),
            profile.get("clothed_upper_body", ""), profile.get("clothed_lower_body", ""),
            profile.get("default_clothing_prompt", ""), concise_marks,
        )
        profile["clinical_character_prompt"] = _sentences(
            profile.get("gender_authority_prompt", ""), profile.get("identity_detail_prompt", ""),
            profile.get("anatomy_upper_body", ""), profile.get("anatomy_lower_body", ""),
            "unclothed neutral non-aroused clinical anatomy documentation", concise_marks,
        )
        if auto_warning:
            profile["warnings"] = _sentences(profile.get("warnings", ""), auto_warning)

        tan_summary = "None" if tan_level == "None" else f"{tan_level}; {tan_line_state}; {tan_line_pattern if tan_line_state != 'Even Tan — No Defined Lines' else 'no defined pattern'}"
        profile["presentation_summary"] = str(profile.get("presentation_summary", "")).replace(
            "Warnings:", f"Tan / skin variation: {tan_summary}\nWarnings:"
        )
        profile["anatomy_configuration_summary"] = str(profile.get("anatomy_configuration_summary", "")).replace(
            "Pubic hair:", f"Pubic hair color: matches {hair_color or '[unspecified]'} head hair\nPubic hair:"
        )

        result[4] = concise_marks
        result[6] = active_character
        result[8] = profile
        result[9] = profile.get("warnings", "")
        result[15] = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        result[18] = active_character
        result[19] = profile["clothed_character_prompt"]
        result[20] = profile["clinical_character_prompt"]
        result[21] = profile["presentation_summary"]
        result[28] = profile["anatomy_configuration_summary"]
        return tuple(result)


class CharacterShotControlV240(CharacterShotControlV230):
    FUNCTION = "build_shot_plan_v240"
    DESCRIPTION = "Current Shot Control. Camera, crop, pose, expression, scene cast, and environment only."

    def build_shot_plan_v240(self, **kwargs):
        result = list(super().build_shot_plan_v230(**kwargs))
        plan = copy.deepcopy(result[0])
        plan["schema"] = "FCC_SHOT_PLAN_V240"
        plan["schema_version"] = 7
        result[0] = plan
        result[8] = json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True)
        return tuple(result)


class CharacterPromptAssemblerV240(CharacterPromptAssemblerV230):
    FUNCTION = "assemble_prompt_v240"
    DESCRIPTION = (
        "Visibility-compiled prompt assembler. It includes only body traits, clothing, tattoos, piercings, tan lines, and anatomy that are visible in the selected crop."
    )

    def assemble_prompt_v240(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan = shot_plan if isinstance(shot_plan, dict) else {}
        krea = generation_purpose.startswith("Krea")
        qwen = generation_purpose.startswith("Qwen")
        extreme = _is_extreme_closeup_v231(plan)

        if generation_purpose == "Krea — First Identity Image":
            purpose = "A realistic camera photograph"
            reference = "None — text-to-image"
        elif generation_purpose == "Krea — LoRA Expansion":
            purpose = "A realistic camera photograph using the loaded identity LoRA"
            reference = "Identity LoRA"
        elif generation_purpose == "Qwen — Anatomy Documentation":
            purpose = f"Edit {reference_label} into neutral clinical anatomy documentation of the same primary character"
            reference = reference_label
        elif qwen:
            purpose = f"Edit {reference_label} into a new realistic photograph while preserving the exact identity of the primary character"
            reference = reference_label
        else:
            purpose = "A realistic camera photograph"
            reference = reference_label

        primary_gender = _clean_phrase(profile.get("gender_authority_prompt", ""))
        identity = _clean_phrase(profile.get("identity_detail_prompt", ""))
        tan = _tan_prompt_for_plan(profile, plan)
        marks, visible_tattoos, visible_piercings = _visible_marks(profile, plan)

        if extreme:
            macro = _extreme_macro_sections_v231(profile, plan)
            focus = _focus_value_v231(plan)
            shot_section = _sentences(macro["crop"], macro["camera"], macro["eye_state"], macro["environment"], macro["exclusion"])
            character_section = _sentences(_focus_identity_prompt_v231(profile, focus), tan)
            body_section = ""
            appearance_section = marks
            presentation = ""
            scene = ""
            crop = macro["crop"]
            if qwen:
                instruction = _sentences(
                    purpose,
                    f"replace the original image with one tightly cropped macro view of {focus.lower()} only",
                    "preserve only identity characteristics and permanent marks physically belonging inside this crop",
                )
                final_prompt = _sentences(custom_prefix, instruction, shot_section, character_section, appearance_section, custom_suffix)
            else:
                final_prompt = _sentences(trigger_word, custom_prefix, purpose, shot_section, character_section, appearance_section, custom_suffix)
            routing_mode = "extreme_closeup_visibility_compiled"
        else:
            crop = _crop_prompt_v230(plan)
            custom_direction = _clean_phrase(plan.get("framing_prompt", "")) if plan.get("planner_mode") == "Custom Shot Direction — Keep Character Settings" else ""
            visible_scope = _visible_tags(plan)
            face_or_headshot = visible_scope.issubset(FACE_TAGS | {"shoulders", "upper_chest", "neck"})
            shot_section = _sentences(
                custom_direction or crop,
                "" if custom_direction else _clean_phrase(plan.get("camera_prompt", "")),
                "" if custom_direction or face_or_headshot else _clean_phrase(plan.get("pose_prompt", "")),
                _clean_phrase(plan.get("expression_prompt", "")),
                _clean_phrase(plan.get("scene_prompt", "")),
                _clean_phrase(plan.get("environment_prompt", "")),
            )
            character_section = _sentences(primary_gender, identity, tan)
            body_section, presentation, presentation_kind = _visible_body_and_presentation(profile, plan)
            appearance_section = marks
            scene = _clean_phrase(plan.get("scene_prompt", ""))
            if qwen:
                instruction = _sentences(
                    purpose,
                    "replace the original framing, camera, pose, and scene with the active Shot Control result",
                    "apply only the visible Character Creator traits appropriate to this crop and clothing coverage",
                    "secondary people are not copies of the primary character unless Scene Direction explicitly requests that",
                )
                final_prompt = _sentences(custom_prefix, instruction, shot_section, character_section, body_section, presentation, appearance_section, custom_suffix)
            else:
                final_prompt = _sentences(trigger_word, custom_prefix, purpose, shot_section, character_section, body_section, presentation, appearance_section, custom_suffix)
            routing_mode = "standard_visibility_compiled"

        width = int(plan.get("recommended_width", 1024))
        height = int(plan.get("recommended_height", 1280))
        character_id = profile.get("character_id", "character")
        focus = plan.get("focus_region", "")
        shot_id = _slug(_sentences(character_id, generation_purpose, plan.get("shot_type", ""), focus, plan.get("pose", "")))
        presentation_mode = profile.get("presentation_mode", "Unspecified")
        resolution_debug = f"{width} × {height} from {plan.get('aspect_ratio', 'selected aspect ratio')}"
        advisory = (
            f"Visibility compiler included {len(visible_tattoos)} tattoo record(s) and {len(visible_piercings)} piercing record(s). "
            "Off-frame and clothing-covered anatomy and marks were omitted."
        )
        notes = "\n".join([
            f"Purpose: {generation_purpose}",
            f"Reference: {reference}",
            "Visibility Compiler: ACTIVE",
            "Character Creator stores the complete blueprint; this prompt contains only physically visible and uncovered details.",
            advisory,
        ])
        active_summary = "\n\n".join([
            profile.get("presentation_summary", "Character settings unavailable"),
            plan.get("active_settings_summary", "Shot settings unavailable"),
            f"FINAL PRIMARY CHARACTER\n{character_section}",
            f"FINAL SCENE / SHOT\n{shot_section}",
            f"FINAL VISIBLE BODY\n{body_section or '[none needed for this crop]'}",
            f"FINAL VISIBLE PRESENTATION\n{presentation or '[not visible / omitted]'}",
            f"FINAL VISIBLE MARKS\n{appearance_section or '[none visible in this crop]'}",
            notes,
        ])
        sections = {
            "purpose": purpose,
            "shot_scene": shot_section,
            "primary_character": character_section,
            "visible_body": body_section,
            "visible_presentation": presentation,
            "visible_marks": appearance_section,
            "visible_tattoo_records": visible_tattoos,
            "visible_piercing_records": visible_piercings,
            "routing_mode": routing_mode,
            "final_prompt": final_prompt,
        }
        return (
            final_prompt if krea else "",
            final_prompt if qwen else "",
            shot_section,
            presentation,
            appearance_section,
            reference,
            shot_id,
            width,
            height,
            character_id,
            notes,
            presentation_mode,
            active_summary,
            final_prompt,
            advisory,
            crop,
            presentation or "[not visible / omitted]",
            resolution_debug,
            json.dumps(sections, indent=2, ensure_ascii=False),
            character_section,
            scene,
        )


class QwenDatasetQueueV240(QwenDatasetQueueV230):
    FUNCTION = "build_queue"
    DESCRIPTION = "Qwen dataset queue using the V2.4 visibility compiler and crop-local marks."

    def build_queue(self, character_blueprint, dataset_plan, starting_seed, variations_per_shot, images_per_group, output_root, reference_label, prompt_suffix="", complete_outfit_override=""):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        character_id = profile.get("character_id", "character")
        specs = _dataset_specs(dataset_plan, images_per_group)
        prompts=[]; seeds=[]; ids=[]; cats=[]; prefixes=[]; widths=[]; heights=[]; progress=[]; manifest=[]
        idx=0
        for spec in specs:
            for variation in range(variations_per_shot):
                cat = spec["category"]
                desc = spec["description"]
                if cat == "extreme_closeup":
                    focus_map = {
                        "extreme_face_front": "Complete Face",
                        "extreme_left_eye": "Left Eye and Eyebrow",
                        "extreme_right_eye": "Right Eye and Eyebrow",
                        "extreme_both_eyes": "Both Eyes and Nose Bridge",
                        "extreme_nose_septum": "Nose and Septum",
                        "extreme_mouth": "Mouth and Lips",
                        "extreme_forehead_hairline": "Forehead and Hairline",
                        "extreme_left_profile": "Left Facial Profile",
                        "extreme_right_profile": "Right Facial Profile",
                        "extreme_nose_mouth": "Nose and Mouth",
                    }
                    focus = focus_map.get(spec["shot_id"], desc)
                    plan = {
                        "focus_mode": "Extreme Close-Up",
                        "focus_region": focus,
                        "selected_extreme_closeup_focus": focus,
                        "shot_type": "Extreme Close-Up — Single Detail",
                        "lens": "105mm Macro",
                        "environment_prompt": "plain clinical documentation background with flat even lighting",
                        "recommended_width": 1024,
                        "recommended_height": 1024,
                        "aspect_ratio": "Square 1:1",
                    }
                else:
                    shot_type = "Face Close-Up" if cat == "closeup" else "Waist-Up Midshot" if cat == "midshot" else "Full Body"
                    if cat in {"anatomy", "anatomy_focus"}:
                        shot_type = "Close-Up — Regional Documentation" if cat == "anatomy_focus" else "Full Body"
                    plan = {
                        "shot_type": shot_type,
                        "focus_mode": "Regional Close-Up" if cat == "anatomy_focus" else "Inactive",
                        "focus_region": desc,
                        "camera_prompt": "standard rectilinear camera perspective",
                        "pose_prompt": "",
                        "expression_prompt": "neutral expression",
                        "scene_prompt": "only the primary character is visible",
                        "environment_prompt": "plain neutral background with even realistic lighting",
                        "recommended_width": 1024,
                        "recommended_height": 1280 if cat in {"closeup", "midshot", "anatomy_focus"} else 1536,
                        "aspect_ratio": "Portrait 4:5" if cat in {"closeup", "midshot", "anatomy_focus"} else "Portrait 2:3",
                    }
                    plan["framing_prompt"] = desc
                assembler = CharacterPromptAssemblerV240()
                purpose = "Qwen — Anatomy Documentation" if cat in {"anatomy", "anatomy_focus"} else "Qwen — Identity Documentation"
                assembled = assembler.assemble_prompt_v240(profile, plan, purpose, reference_label, custom_suffix=prompt_suffix)
                prompt = assembled[1]
                seed=int(starting_seed)+idx
                sid=f"{spec['shot_id']}_v{variation+1:02d}"
                prefix=f"{output_root}/{cat}/{idx+1:04d}_{sid}"
                w = int(plan.get("recommended_width", 1024)); h = int(plan.get("recommended_height", 1280))
                item={"index":idx+1,"shot_id":sid,"category":cat,"seed":seed,"filename_prefix":prefix,"width":w,"height":h,"prompt":prompt}
                prompts.append(prompt);seeds.append(seed);ids.append(sid);cats.append(cat);prefixes.append(prefix);widths.append(w);heights.append(h);manifest.append(item)
                idx+=1
        total=len(manifest)
        progress=[f"{x['index']} of {total} | {x['category']} | {x['shot_id']}" for x in manifest]
        plan_json=json.dumps({"schema":"FCC_QWEN_DATASET_PLAN_V240","schema_version":5,"character_id":character_id,"plan":dataset_plan,"images_per_group":images_per_group,"variations_per_shot":variations_per_shot,"total_images":total,"items":manifest},indent=2,ensure_ascii=False)
        return prompts,seeds,ids,cats,prefixes,widths,heights,[plan_json for _ in prompts],progress


__all__ = [
    "QwenDatasetQueueV240",
    "FCCDatasetDirector",
    "FCCQueueItemRouter",
    "CharacterBlueprintCreatorV240",
    "CharacterShotControlV240",
    "CharacterPromptAssemblerV240",
]
