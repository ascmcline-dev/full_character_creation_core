from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .nodes import (
    AGE_RANGES,
    ASPECT_RATIOS_V2,
    BACKGROUNDS_V2,
    BACKGROUND_PROMPTS_V2,
    BODY_TYPES,
    BUST_AUGMENTATION,
    BUST_AUGMENTATION_PROMPTS,
    BUST_FIRMNESS,
    BUST_FIRMNESS_PROMPTS,
    BUST_POSITIONS,
    BUST_POSITION_PROMPTS,
    BUST_SHAPES,
    BUST_SHAPE_PROMPTS,
    BUST_SIZES,
    BUST_SIZE_PROMPTS,
    BUTTOCKS,
    CAMERA_HEIGHTS_V2,
    CAMERA_HEIGHT_PROMPTS_V2,
    CAMERA_PROMPTS,
    CAMERA_VIEWS,
    CHIN_SHAPES,
    COMPLEXIONS,
    DEFAULT_CLOTHING,
    DISTORTION_GUARDS_V2,
    EYE_COLORS,
    EYE_SHAPES,
    EYEBROWS,
    EXPRESSIONS_V2,
    EXPRESSION_PROMPTS_V2,
    EXTREME_CLOSEUP_FOCUS_V2,
    FACIAL_HAIR,
    FACIAL_HAIR_PROMPTS,
    HAIR_COLORS,
    HEIGHTS,
    HERITAGES,
    JEWELRY_LEVELS,
    JAW_SHAPES,
    LENSES_V2,
    LENS_PROMPTS_V2,
    LIGHTING_V2,
    LIGHTING_PROMPTS_V2,
    LINGERIE_STYLES_V2,
    LIPS,
    MALE_CHEST,
    MALE_GENITAL_SIZES,
    MARK_STATUSES,
    NOSES,
    PHOTO_STYLES,
    PIERCING_INPUT_MODES_V22,
    POSES_V2,
    POSE_PROMPTS_V2,
    PUBIC_HAIR_STYLES_V224,
    QwenDatasetQueue,
    FCCDatasetDirector,
    FCCQueueItemRouter,
    SHOT_TYPES_V2,
    SHOT_PROMPTS_V2,
    SKIN_TONES,
    CLOSEUP_REGIONS_V2,
    CharacterBlueprintCreatorV224,
    CharacterShotControlV22,
    CharacterPromptAssemblerV224,
    _aspect_dimensions_v2,
    _dataset_specs,
    _build_authoritative_outfit_v2,
    _clean_mark_negations_v224,
    _extreme_focus_prompt_v22,
    _focus_specific_integrity_lock_v22,
    _join,
    _mark_anatomy_integrity_lock_v22,
    _mark_prompt_v22,
    _pubic_hair_prompt_v224,
    _regional_focus_prompt_v22,
    _slug,
    _structured_single_piercing_prompt_v22,
)


# -----------------------------------------------------------------------------
# V2.3.1 production architecture
# - Character Creator defines one primary character, not the number of people.
# - Shot Control defines scene cast, framing, camera, pose, and interactions.
# - Custom pose and scene direction are adjacent to the controls that activate them.
# - Chest anatomy and groin anatomy are independent of gender identity.
# - Krea prompts use compact natural language rather than long "authority" labels.
# -----------------------------------------------------------------------------

PRIMARY_GENDERS_V230 = ["Adult Woman", "Adult Man", "Adult Nonbinary"]
GENDER_CANONICAL_V230 = {
    "Adult Woman": "Adult Female",
    "Adult Man": "Adult Male",
    "Adult Nonbinary": "Adult Nonbinary",
}

HAIR_LENGTHS_V230 = [
    "Unspecified",
    "Shaved Head / Bald",
    "Buzz Cut",
    "Very Short",
    "Chin-Length",
    "Shoulder-Length",
    "Mid-Back",
    "Waist-Length",
    "Custom",
]
HAIR_TEXTURES_V230 = [
    "Unspecified",
    "Pin-Straight",
    "Straight",
    "Slightly Wavy",
    "Wavy",
    "Curly",
    "Coily",
    "Custom",
]
HAIR_STYLES_V230 = [
    "Unspecified",
    "Loose Natural",
    "Center Part",
    "Side Part",
    "Braids",
    "Ponytail",
    "Bun",
    "Pixie",
    "Locs",
    "Afro",
    "Custom",
]

CHEST_ANATOMY_V230 = [
    "Auto — Match Gender Identity",
    "Bust Anatomy — Use Bust Controls",
    "Masculine Chest — Use Male Chest Control",
    "Flat / Neutral Chest",
    "Custom Chest Description",
]
GROIN_ANATOMY_V230 = [
    "Auto — Match Gender Identity",
    "Female External Anatomy",
    "Male External Anatomy",
    "Unspecified — Do Not Describe",
    "Custom Groin Anatomy",
]
FORESKIN_STATUS_V230 = [
    "Unspecified",
    "Circumcised",
    "Uncircumcised / Intact Foreskin",
]

PRESENTATION_MODES_V230 = [
    "Clothed — Use Outfit Controls",
    "Clinical Anatomy — No Clothing",
    "Custom Presentation — Use Text Below",
]
PRESENTATION_CANONICAL_V230 = {
    "Clothed — Use Outfit Controls": "Clothed Character",
    "Clinical Anatomy — No Clothing": "Clinical Anatomy",
    "Custom Presentation — Use Text Below": "Custom Presentation",
}
CUSTOM_BODY_DETAIL_V230 = [
    "Body Shape Only — No Explicit Anatomy",
    "Clinical Anatomy — Include Selected Chest / Groin",
    "Identity Only — No Body Description",
]
OUTFIT_INPUT_METHODS_V230 = [
    "Preset — Ready-Made Complete Outfit",
    "Exact Text — Describe Entire Outfit",
    "Build Outfit — Separate Garment Fields",
]
OUTFIT_SOURCE_CANONICAL_V230 = {
    "Preset — Ready-Made Complete Outfit": "Preset Outfit",
    "Exact Text — Describe Entire Outfit": "Exact Outfit Text",
    "Build Outfit — Separate Garment Fields": "Structured Components",
}
STRUCTURED_OUTFIT_TYPES_V230 = [
    "Top + Bottom Outfit",
    "One-Piece Outfit",
    "Two-Piece Swimwear",
    "Lingerie",
]
STRUCTURED_TYPE_CANONICAL_V230 = {
    "Top + Bottom Outfit": "Complete Outfit",
    "One-Piece Outfit": "One-Piece Garment",
    "Two-Piece Swimwear": "Swimwear Set",
    "Lingerie": "Lingerie Set",
}

PLANNER_MODES_V230 = [
    "Freestyle — Use Shot Controls",
    "Custom Shot Direction — Keep Character Settings",
]
SCENE_CAST_V230 = [
    "Solo — Primary Character Only",
    "Primary Character + One Other Adult",
    "Primary Character + Small Group",
    "Custom — Describe People in Scene Direction",
]

CREATOR_CONTROL_LEGEND_V230 = """FCC CHARACTER CREATOR — QUICK GUIDE
1. Primary Character Gender controls identity and overall presentation, not scene headcount.
2. Chest Anatomy and Groin Anatomy are independent. Auto follows gender; choose explicit anatomy for nonbinary or mixed configurations.
3. Presentation Mode chooses the visible state: clothed, clinical anatomy, or custom presentation text.
4. Outfit Input Method is used only in Clothed mode. Only the selected outfit path contributes.
5. Custom Presentation Body Detail is used only in Custom Presentation mode.
6. Tattoo and Piercing Status are the master switches. Hidden stored fields are ignored.
7. Hair Length Shaved/Buzz suppresses unrelated texture and hairstyle fields.
8. Scene actions, poses, extra people, camera, and background belong in FCC Universal Shot Control."""

SHOT_CONTROL_LEGEND_V230 = """FCC UNIVERSAL SHOT CONTROL — QUICK GUIDE
1. Freestyle uses every visible dropdown plus Scene Direction.
2. Pose = Custom uses Custom Pose. It never reads Custom Shot Direction.
3. Custom Shot Direction replaces framing, camera, and pose only; Character Creator identity, anatomy, clothing, marks, expression, background, and lighting still apply.
4. Scene Cast controls how many people appear. Character Creator always describes only the primary character.
5. Scene Direction is always active and is the place for interactions, another person, props, and complex action.
6. Extreme Close-Up and Regional Close-Up reveal their own focus controls. Other shot types ignore them."""


BODY_SHAPE_PROMPTS_V230 = {
    "Very Slim": "a distinctly very slim adult build with narrow shoulders, a slender torso, slim arms, a narrow waist, and slender legs",
    "Slim": "a lean adult build with slim shoulders and arms, a lean torso, a defined waist, and slim legs",
    "Average": "an average adult build with balanced shoulders, torso, waist, hips, arms, and legs",
    "Athletic": "an athletic adult build with trained shoulders and arms, a firm torso, a defined waist, athletic hips and thighs, and moderate muscle definition",
    "Curvy": "a curvy adult build with a clearly defined waist, fuller hips and thighs, and balanced natural body volume",
    "Full-Figured": "a full-figured adult build with substantial natural torso, hip, thigh, and limb volume",
    "Muscular": "a muscular adult build with broad trained shoulders, developed arms, a muscular torso, strong hips, and developed legs",
    "Heavyset": "a heavyset adult build with broad shoulders, substantial torso mass, a fuller waist, hips, limbs, and legs",
    "Custom / Unspecified": "",
}

MALE_CHEST_PROMPTS_V230 = {
    "Average Male Chest": "an average masculine chest with natural pectoral volume",
    "Slim Male Chest": "a slim masculine chest with minimal pectoral bulk",
    "Athletic Defined Chest": "an athletic masculine chest with clearly defined natural pectorals",
    "Broad Muscular Chest": "a broad muscular masculine chest with developed pectorals",
    "Heavyset Male Chest": "a broad heavyset masculine chest with substantial natural chest mass",
}

MALE_SIZE_PROMPTS_V230 = {
    "Very Small": "very small proportional size",
    "Small": "small proportional size",
    "Average": "average proportional size",
    "Above Average": "above-average proportional size",
    "Very Large": "very large proportional size",
}


# ------------------------------- utilities ----------------------------------

def _sentences(*parts: str) -> str:
    cleaned: list[str] = []
    for part in parts:
        value = re.sub(r"\s+", " ", str(part or "")).strip(" ,.;")
        if value:
            cleaned.append(value)
    return ". ".join(cleaned) + ("." if cleaned else "")


def _clean_phrase(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip(" ,.;")


def _primary_gender_prompt_v230(label: str) -> str:
    if label == "Adult Man":
        return "the primary character is an adult man with a clearly masculine facial presentation and overall male appearance"
    if label == "Adult Woman":
        return "the primary character is an adult woman with a clearly feminine facial presentation and overall female appearance"
    return "the primary character is an adult nonbinary person with an intentionally androgynous or user-selected presentation"


def _resolve_chest_mode_v230(gender_label: str, selection: str) -> str:
    if selection != "Auto — Match Gender Identity":
        return selection
    if gender_label == "Adult Woman":
        return "Bust Anatomy — Use Bust Controls"
    if gender_label == "Adult Man":
        return "Masculine Chest — Use Male Chest Control"
    return "Flat / Neutral Chest"


def _resolve_groin_mode_v230(gender_label: str, selection: str) -> str:
    if selection != "Auto — Match Gender Identity":
        return selection
    if gender_label == "Adult Woman":
        return "Female External Anatomy"
    if gender_label == "Adult Man":
        return "Male External Anatomy"
    return "Unspecified — Do Not Describe"


def _hair_prompt_v230(
    hair_color: str,
    custom_hair_color: str,
    hair_length: str,
    custom_hair_length: str,
    hair_texture: str,
    custom_hair_texture: str,
    hair_style: str,
    custom_hair_style: str,
) -> tuple[str, list[str]]:
    warnings: list[str] = []
    color = custom_hair_color.strip() if hair_color == "Custom" else hair_color.lower()
    if hair_color == "Custom" and not custom_hair_color.strip():
        color = ""
        warnings.append("Hair Color is Custom but Custom Hair Color is blank.")

    if hair_length == "Shaved Head / Bald":
        return "a clean-shaven head with a smooth visible scalp and no visible hairstyle", warnings

    if hair_length == "Buzz Cut":
        return _clean_phrase(f"{color} close buzz cut with short even hair"), warnings

    if hair_length == "Custom":
        length = custom_hair_length.strip()
        if not length:
            warnings.append("Hair Length is Custom but Custom Hair Length is blank.")
    elif hair_length == "Unspecified":
        length = ""
    else:
        length = hair_length.lower()

    if hair_texture == "Custom":
        texture = custom_hair_texture.strip()
        if not texture:
            warnings.append("Hair Texture is Custom but Custom Hair Texture is blank.")
    elif hair_texture == "Unspecified":
        texture = ""
    else:
        texture = hair_texture.lower()

    if hair_style == "Custom":
        style = custom_hair_style.strip()
        if not style:
            warnings.append("Hair Style is Custom but Custom Hair Style is blank; no hairstyle wording is added.")
    elif hair_style == "Unspecified":
        style = ""
    else:
        style = hair_style.lower()

    pieces = [p for p in (color, length, texture, style) if p]
    if not pieces:
        return "", warnings
    return _clean_phrase(" ".join(pieces) + " hair"), warnings


def _facial_hair_prompt_v230(selection: str, custom: str) -> tuple[str, str]:
    if selection == "None":
        return "", ""
    if selection == "Custom":
        text = custom.strip()
        return text, "Facial Hair is Custom but Custom Facial Hair is blank." if not text else ""
    return FACIAL_HAIR_PROMPTS.get(selection, selection.lower()), ""


def _chest_prompts_v230(
    resolved_mode: str,
    male_chest: str,
    custom_chest_description: str,
    bust_size: str,
    bust_shape: str,
    bust_position: str,
    bust_firmness: str,
    bust_augmentation: str,
) -> tuple[str, str, str, list[str]]:
    warnings: list[str] = []
    if resolved_mode == "Masculine Chest — Use Male Chest Control":
        if male_chest == "Custom":
            anatomy = custom_chest_description.strip()
            if not anatomy:
                warnings.append("Male Chest is Custom but Custom Chest Description is blank.")
        else:
            anatomy = MALE_CHEST_PROMPTS_V230.get(male_chest, male_chest.lower())
        clothed = _sentences(anatomy, "the garment follows this masculine chest contour without changing it")
        return clothed, anatomy, anatomy, warnings

    if resolved_mode == "Flat / Neutral Chest":
        anatomy = "a flat neutral adult chest with minimal projection and balanced natural anatomy"
        clothed = "a flat neutral chest silhouette with minimal garment projection"
        return clothed, anatomy, anatomy, warnings

    if resolved_mode == "Custom Chest Description":
        anatomy = custom_chest_description.strip()
        if not anatomy:
            warnings.append("Custom Chest Description is selected but the description is blank.")
        clothed = _sentences(anatomy, "the garment follows the selected chest contour") if anatomy else ""
        return clothed, anatomy, anatomy, warnings

    # Bust anatomy branch.
    selected = [bust_size, bust_shape, bust_position, bust_firmness, bust_augmentation]
    if all(value == "Unspecified" for value in selected):
        warnings.append("Bust Anatomy is selected but every bust control is Unspecified.")
    anatomy = _join(
        BUST_SIZE_PROMPTS.get(bust_size, ""),
        BUST_SHAPE_PROMPTS.get(bust_shape, ""),
        BUST_POSITION_PROMPTS.get(bust_position, ""),
        BUST_FIRMNESS_PROMPTS.get(bust_firmness, ""),
        BUST_AUGMENTATION_PROMPTS.get(bust_augmentation, ""),
    )
    clothed_parts = []
    if bust_size != "Unspecified":
        clothed_parts.append(BUST_SIZE_PROMPTS.get(bust_size, "").replace("bust", "bust silhouette"))
    if bust_shape != "Unspecified":
        clothed_parts.append(BUST_SHAPE_PROMPTS.get(bust_shape, ""))
    if bust_position != "Unspecified":
        clothed_parts.append(BUST_POSITION_PROMPTS.get(bust_position, ""))
    clothed = _sentences(
        _join(*clothed_parts),
        "the garment follows the selected bust contour with normal fit and coverage" if anatomy else "",
    )
    return clothed, anatomy, anatomy, warnings


def _groin_prompt_v230(
    resolved_mode: str,
    male_genital_size: str,
    foreskin_status: str,
    custom_groin_anatomy: str,
) -> tuple[str, list[str]]:
    warnings: list[str] = []
    if resolved_mode == "Unspecified — Do Not Describe":
        return "", warnings
    if resolved_mode == "Female External Anatomy":
        return "adult female external genital anatomy in a neutral non-aroused clinical state", warnings
    if resolved_mode == "Custom Groin Anatomy":
        text = custom_groin_anatomy.strip()
        if not text:
            warnings.append("Custom Groin Anatomy is selected but the description is blank.")
        return text, warnings

    parts = ["adult male external genital anatomy in a neutral non-aroused clinical state"]
    size = MALE_SIZE_PROMPTS_V230.get(male_genital_size, "")
    if size:
        parts.append(size)
    if foreskin_status == "Circumcised":
        parts.append("circumcised anatomy")
    elif foreskin_status == "Uncircumcised / Intact Foreskin":
        parts.append("uncircumcised anatomy with intact natural foreskin")
    return _join(*parts), warnings


def _identity_lower_silhouette_v230(gender_label: str) -> str:
    if gender_label == "Adult Man":
        return "a masculine waist, hip, pelvis, and leg silhouette"
    if gender_label == "Adult Woman":
        return "a feminine waist, hip, pelvis, and leg silhouette"
    return "a balanced androgynous waist, hip, pelvis, and leg silhouette"


def _scene_cast_prompt_v230(selection: str) -> str:
    return {
        "Solo — Primary Character Only": "only the primary character is visible in the scene",
        "Primary Character + One Other Adult": "the primary character is accompanied by one secondary adult person",
        "Primary Character + Small Group": "the primary character is accompanied by a small group of secondary adults",
        "Custom — Describe People in Scene Direction": "",
    }.get(selection, "")


def _is_clinical(profile: dict) -> bool:
    return profile.get("presentation_mode") == "Clinical Anatomy"


def _focus_scope_v230(plan: dict) -> str:
    focus = str(plan.get("focus_region", "") or "").lower()
    shot = str(plan.get("shot_type", "") or "")
    if shot == "Face Close-Up" or any(t in focus for t in ("face", "eye", "nose", "mouth", "forehead", "hairline", "jaw", "ear")):
        return "face"
    if shot in {"Head and Shoulders", "Chest-Up"} or any(t in focus for t in ("chest", "breast", "nipple", "areola", "ribcage", "shoulder", "arm", "upper back")):
        return "upper"
    if shot == "Waist-Up Midshot" or any(t in focus for t in ("abdomen", "waist", "navel", "lower back")):
        return "waist"
    if any(t in focus for t in ("groin", "pelvis", "pubic", "genital", "hip", "butt", "glute", "thigh", "leg", "foot", "feet")):
        return "lower"
    if "hand" in focus:
        return "hand"
    return "full" if shot in {"Three-Quarter Body", "Full Body", "Custom Framing"} else "regional"


def _crop_prompt_v230(plan: dict) -> str:
    shot = str(plan.get("shot_type", "") or "")
    focus = str(plan.get("focus_region", "") or "")
    if shot == "Extreme Close-Up — Single Detail":
        return f"true macro extreme close-up of {focus or 'the selected detail'}, filling roughly eighty-five percent of the frame with only minimal surrounding context"
    if shot == "Close-Up — Regional Documentation":
        return f"regional close-up of {focus or 'the selected body region'}, showing the complete region with nearby anatomical landmarks"
    return {
        "Face Close-Up": "face close-up from the complete hairline through the upper shoulders, with the face filling most of the frame",
        "Head and Shoulders": "head-and-shoulders framing with the complete head, neck, shoulders, and upper chest visible",
        "Chest-Up": "chest-up framing from above the complete head to just below the chest, ending before the waist",
        "Waist-Up Midshot": "waist-up framing from above the complete head through the natural waist and lower abdomen",
        "Three-Quarter Body": "three-quarter-body framing from above the complete head to below the knees, with the feet outside the frame",
        "Full Body": "full-body framing with the entire primary character visible from head to feet and balanced space around the body",
        "Custom Framing": _clean_phrase(plan.get("framing_prompt", "")),
    }.get(shot, _clean_phrase(plan.get("framing_prompt", "")))


def _visible_presentation_v230(profile: dict, plan: dict) -> str:
    mode = profile.get("presentation_mode")
    active = _clean_phrase(profile.get("active_presentation_prompt", ""))
    if mode != "Clothed Character":
        return active

    shot = str(plan.get("shot_type", "") or "")
    scope = _focus_scope_v230(plan)
    components = profile.get("outfit_components", {}) if isinstance(profile.get("outfit_components"), dict) else {}
    raw = _clean_phrase(components.get("raw", ""))
    top = _clean_phrase(components.get("top", ""))
    bottom = _clean_phrase(components.get("bottom", ""))
    footwear = _clean_phrase(components.get("footwear", ""))
    outerwear = _clean_phrase(components.get("outerwear", ""))
    one_piece = _clean_phrase(components.get("one_piece", ""))
    swim_top = _clean_phrase(components.get("swimwear_top", ""))
    swim_bottom = _clean_phrase(components.get("swimwear_bottom", ""))
    jewelry = _clean_phrase(profile.get("jewelry_prompt", ""))

    if raw and not any((top, bottom, footwear, one_piece, swim_top, swim_bottom)):
        normalized = re.sub(r"\s*,?\s+and\s+", ", ", raw, flags=re.IGNORECASE)
        parts = [p.strip(" ,") for p in normalized.split(",") if p.strip(" ,")]
        top = parts[0] if parts else raw
        bottom = parts[1] if len(parts) > 1 else ""
        footwear = parts[2] if len(parts) > 2 else ""

    upper = _join(outerwear, one_piece or swim_top or top)
    lower = _join(one_piece or swim_bottom or bottom)
    stable = "the selected outfit keeps the same colors, materials, construction, normal fit, and normal coverage"

    if shot in {"Full Body", "Three-Quarter Body", "Custom Framing"} or scope == "full":
        return _sentences(active, stable)
    if scope == "lower":
        return _sentences(
            f"the selected lower garment is {lower}" if lower else "the selected lower garment remains unchanged",
            f"footwear is {footwear}" if footwear and any(x in str(plan.get('focus_region','')).lower() for x in ('foot','feet')) else "",
            stable,
        )
    if scope == "hand":
        return _sentences("the selected outfit remains unchanged outside the hand-focused crop", jewelry, stable)
    if shot == "Waist-Up Midshot" or scope == "waist":
        return _sentences(
            f"the visible upper garment is {upper}" if upper else "the selected upper garment is visible",
            f"the upper edge of {lower} may appear at the bottom of the frame" if lower else "",
            jewelry,
            stable,
        )
    return _sentences(
        f"the visible upper garment is {upper}" if upper else "the selected upper garment remains visible",
        jewelry,
        stable,
    )


def _visible_body_v230(profile: dict, plan: dict) -> tuple[str, str, str, str]:
    scope = _focus_scope_v230(plan)
    mode = profile.get("presentation_mode")
    body_shape = _clean_phrase(profile.get("body_type_authority_prompt", ""))
    chest = _clean_phrase(
        profile.get("chest_anatomy_prompt", "") if mode == "Clinical Anatomy" else profile.get("chest_clothed_prompt", "")
    )
    upper = _clean_phrase(
        profile.get("anatomy_upper_body", "") if mode == "Clinical Anatomy" else profile.get("clothed_upper_body", "")
    )
    lower = _clean_phrase(
        profile.get("anatomy_lower_body", "") if mode == "Clinical Anatomy" else profile.get("clothed_lower_body", "")
    )
    groin = _clean_phrase(profile.get("groin_anatomy_prompt", "")) if mode == "Clinical Anatomy" else ""

    if scope == "face":
        return "", "", "", ""
    if scope == "upper":
        return body_shape, chest or upper, "", ""
    if scope == "waist":
        return body_shape, chest or upper, "", ""
    if scope == "lower":
        return "", "", lower, groin
    return body_shape, chest or upper, lower, groin


def _crop_shows_groin_v230(plan: dict) -> bool:
    scope = _focus_scope_v230(plan)
    shot = str(plan.get("shot_type", "") or "")
    focus = str(plan.get("focus_region", "") or "").lower()
    return scope == "lower" or shot in {"Three-Quarter Body", "Full Body", "Custom Framing"} or any(
        token in focus for token in ("groin", "pelvis", "pubic", "genital")
    )


# -------------------- V2.3.1 extreme-detail routing -------------------------

def _looks_like_extreme_closeup_v231(text: str) -> bool:
    value = re.sub(r"[-_]+", " ", str(text or "").lower())
    return bool(re.search(r"\b(?:true\s+)?(?:macro\s+)?extreme\s+close\s*up\b", value))


def _is_extreme_closeup_v231(plan: dict) -> bool:
    if str(plan.get("focus_mode", "")) == "Extreme Close-Up":
        return True
    if str(plan.get("shot_type", "")) == "Extreme Close-Up — Single Detail":
        return True
    if str(plan.get("selected_shot_type", "")) == "Extreme Close-Up — Single Detail":
        return True
    return _looks_like_extreme_closeup_v231(plan.get("framing_prompt", ""))


def _focus_value_v231(plan: dict) -> str:
    focus = _clean_phrase(plan.get("focus_region", ""))
    if focus:
        return focus
    selected = _clean_phrase(plan.get("selected_extreme_closeup_focus", ""))
    custom = _clean_phrase(plan.get("custom_extreme_focus", ""))
    if selected == "Custom" and custom:
        return custom
    return selected or "selected detail"


def _profile_value_v231(profile: dict, key: str, suffix: str = "") -> str:
    value = _clean_phrase(profile.get(key, ""))
    if not value or value in {"Unspecified", "Custom / Unspecified", "Not applicable"}:
        return ""
    return f"{value.lower()}{suffix}"


def _focus_is_v231(focus: str, *tokens: str) -> bool:
    value = focus.lower()
    return any(token in value for token in tokens)


def _focus_crop_prompt_v231(focus: str) -> str:
    f = focus.lower()
    if "left eye" in f:
        return _sentences(
            "single-image clinical macro documentation of the primary character's anatomical left eye and left eyebrow only",
            "the subject's anatomical left eye appears on the viewer's right side",
            "one eye only; the opposite eye is completely outside the frame",
            "the left eye, eyelids, eyelashes, eyebrow, and immediately surrounding skin occupy approximately eighty-five to ninety percent of the image",
            "crop tightly from the eyebrow and lower forehead to the upper cheek and from the inner nose bridge to the outer temple",
        )
    if "right eye" in f:
        return _sentences(
            "single-image clinical macro documentation of the primary character's anatomical right eye and right eyebrow only",
            "the subject's anatomical right eye appears on the viewer's left side",
            "one eye only; the opposite eye is completely outside the frame",
            "the right eye, eyelids, eyelashes, eyebrow, and immediately surrounding skin occupy approximately eighty-five to ninety percent of the image",
            "crop tightly from the eyebrow and lower forehead to the upper cheek and from the inner nose bridge to the outer temple",
        )
    if "both eyes" in f:
        return _sentences(
            "single-image clinical macro documentation of both eyes, both eyebrows, and the nose bridge only",
            "the eye band occupies approximately eighty-five to ninety percent of the image",
            "crop away the mouth, chin, ears, neck, shoulders, and torso",
        )
    if "complete face" in f:
        return _sentences(
            "single-image extreme close-up identity documentation of the complete face from hairline to chin",
            "the face occupies approximately eighty-five percent of the image",
            "crop away the shoulders, torso, and most of the neck",
            "this is not a head-and-shoulders portrait",
        )
    if "nose and mouth" in f:
        return _sentences(
            "single-image clinical macro documentation of the complete nose and complete mouth only",
            "the nose-and-mouth region occupies approximately eighty-five to ninety percent of the image",
            "crop from the lower nose bridge through the chin edge and exclude both eyes, ears, neck, shoulders, and torso",
        )
    if "nose" in f or "septum" in f:
        return _sentences(
            "single-image clinical macro documentation of the nose, nostrils, columella, and septum only",
            "the nose region occupies approximately eighty-five to ninety percent of the image",
            "exclude both eyes, the complete mouth, ears, neck, shoulders, and torso",
        )
    if "mouth" in f or "lips" in f:
        return _sentences(
            "single-image clinical macro documentation of the mouth, lips, philtrum, lower nose edge, and immediately surrounding skin only",
            "the mouth region occupies approximately eighty-five to ninety percent of the image",
            "exclude both eyes, the complete face, ears, neck, shoulders, and torso",
        )
    if "forehead" in f or "hairline" in f:
        return _sentences(
            "single-image clinical macro documentation of the forehead, hairline, temples, and eyebrows only",
            "the upper-face region occupies approximately eighty-five to ninety percent of the image",
            "crop away the mouth, chin, neck, shoulders, and torso",
        )
    if "left facial profile" in f:
        return _sentences(
            "single-image extreme close-up of the true anatomical left facial profile",
            "show the left forehead, nose profile, lips, chin, jawline, and left ear edge",
            "the profile occupies approximately eighty-five percent of the image",
            "exclude shoulders and torso",
        )
    if "right facial profile" in f:
        return _sentences(
            "single-image extreme close-up of the true anatomical right facial profile",
            "show the right forehead, nose profile, lips, chin, jawline, and right ear edge",
            "the profile occupies approximately eighty-five percent of the image",
            "exclude shoulders and torso",
        )
    if any(x in f for x in ("chin", "jawline", "beard")):
        return _sentences(
            "single-image clinical macro documentation of the lower face, lips, chin, jawline, moustache boundary, and beard density only",
            "the lower-face region occupies approximately eighty-five to ninety percent of the image",
            "exclude both eyes, forehead, neck, shoulders, and torso",
        )
    if "left ear" in f:
        return _sentences(
            "single-image clinical macro documentation of the complete anatomical left ear only",
            "the left ear and immediately surrounding hairline and skin occupy approximately eighty-five to ninety percent of the image",
            "exclude the complete face, neck, shoulders, and torso",
        )
    if "right ear" in f:
        return _sentences(
            "single-image clinical macro documentation of the complete anatomical right ear only",
            "the right ear and immediately surrounding hairline and skin occupy approximately eighty-five to ninety percent of the image",
            "exclude the complete face, neck, shoulders, and torso",
        )
    if "left nipple" in f:
        return _sentences(
            "single-image neutral clinical macro documentation of exactly one anatomical left nipple and its complete left areola only",
            "the left nipple-and-areola complex occupies approximately seventy-five to eighty-five percent of the image",
            "show only minimal surrounding breast skin and exclude the full breast, chest, torso, face, and all other body regions",
        )
    if "right nipple" in f:
        return _sentences(
            "single-image neutral clinical macro documentation of exactly one anatomical right nipple and its complete right areola only",
            "the right nipple-and-areola complex occupies approximately seventy-five to eighty-five percent of the image",
            "show only minimal surrounding breast skin and exclude the full breast, chest, torso, face, and all other body regions",
        )
    if "both nipples" in f:
        return _sentences(
            "single-image neutral clinical close documentation of both anatomical nipples, both areolae, and the center chest only",
            "the selected chest center occupies approximately eighty-five percent of the image",
            "exclude the face, abdomen, pelvis, and outer torso context",
        )
    if "navel" in f:
        return _sentences(
            "single-image neutral clinical macro documentation of the navel and immediately surrounding abdominal skin only",
            "the navel region occupies approximately eighty-five percent of the image",
            "exclude the complete abdomen, chest, pelvis, face, and limbs",
        )
    if "pubic mons" in f:
        return _sentences(
            "single-image neutral clinical macro documentation of the pubic mons and immediately surrounding lower-abdominal skin only",
            "the selected region occupies approximately seventy-five to eighty-five percent of the image",
            "exclude the full pelvis, torso, face, and limbs",
        )
    if "external genital" in f or "genital anatomy" in f:
        return _sentences(
            "single-image neutral non-aroused clinical macro documentation of the selected adult external genital anatomy only",
            "the selected anatomy occupies approximately seventy-five to eighty-five percent of the image",
            "exclude the broad pelvis, torso, face, and limbs",
        )
    if "left hand" in f:
        return "single-image macro documentation of the complete anatomical left hand from wrist through fingertips, occupying approximately eighty-five percent of the image"
    if "right hand" in f:
        return "single-image macro documentation of the complete anatomical right hand from wrist through fingertips, occupying approximately eighty-five percent of the image"
    if "left foot" in f:
        return "single-image macro documentation of the complete anatomical left foot from ankle through toes, occupying approximately eighty-five percent of the image"
    if "right foot" in f:
        return "single-image macro documentation of the complete anatomical right foot from ankle through toes, occupying approximately eighty-five percent of the image"
    return _sentences(
        f"single-image macro documentation of {focus.lower()} only",
        "the selected single detail occupies approximately eighty-five percent of the image with minimal surrounding context",
        "exclude all unrelated body regions",
    )


def _focus_eye_state_v231(focus: str) -> str:
    f = focus.lower()
    if "left eye" in f:
        return "the left eyelids remain naturally fully open throughout the exposure, the complete iris and pupil are visible, and the gaze is neutral and attentive toward the lens"
    if "right eye" in f:
        return "the right eyelids remain naturally fully open throughout the exposure, the complete iris and pupil are visible, and the gaze is neutral and attentive toward the lens"
    if "both eyes" in f:
        return "both eyelids remain naturally fully open throughout the exposure, both irises and pupils are completely visible, and the gaze is neutral and attentive toward the lens"
    return ""


def _focus_local_camera_v231(plan: dict, focus: str) -> str:
    f = focus.lower()
    lens = str(plan.get("lens", "") or "")
    lens_prompt = LENS_PROMPTS_V2.get(lens, "")
    if not lens_prompt or "macro" not in lens_prompt.lower():
        lens_prompt = "rectilinear 105mm macro-lens perspective with precise close-focus detail"
    if "left eye" in f:
        target = "camera centered specifically on the anatomical left eye, not on the complete face"
    elif "right eye" in f:
        target = "camera centered specifically on the anatomical right eye, not on the complete face"
    elif "both eyes" in f:
        target = "camera centered specifically on the eye band and nose bridge, not on the complete face"
    else:
        target = f"camera centered specifically on {focus.lower()}, not on the complete face or body"
    return _sentences(target, lens_prompt, "natural local proportions with no fisheye distortion or perspective enlargement")


def _focus_identity_prompt_v231(profile: dict, focus: str) -> str:
    f = focus.lower()
    base = _sentences(
        _clean_phrase(profile.get("gender_authority_prompt", "")),
        f"age range {profile.get('age_range')}" if profile.get("age_range") else "",
        _profile_value_v231(profile, "skin_tone", " skin tone"),
        _profile_value_v231(profile, "complexion"),
    )
    eye = _sentences(
        _profile_value_v231(profile, "eye_color", " iris color"),
        _profile_value_v231(profile, "eye_shape", " eye shape"),
        _profile_value_v231(profile, "eyebrow_shape", " eyebrow shape"),
    )
    if "left eye" in f or "right eye" in f or "both eyes" in f:
        return _sentences(base, eye, "preserve the exact local eyelid folds, eyelashes, pores, and surrounding identity characteristics")
    if "nose and mouth" in f:
        return _sentences(base, _profile_value_v231(profile, "nose_shape", " nose"), _profile_value_v231(profile, "lip_shape", " lips"), "preserve the exact local philtrum, skin texture, and facial identity characteristics")
    if "nose" in f or "septum" in f:
        return _sentences(base, _profile_value_v231(profile, "nose_shape", " nose"), "preserve the exact nostril shape, columella, septum, pores, and local facial identity characteristics")
    if "mouth" in f or "lips" in f:
        return _sentences(base, _profile_value_v231(profile, "lip_shape", " lips"), "lips rest naturally closed without a smile, preserving exact lip texture, philtrum, and local identity characteristics")
    if "forehead" in f or "hairline" in f:
        return _sentences(base, _profile_value_v231(profile, "hair_color", " hair"), "preserve the exact hairline shape, temple hair, forehead texture, and local identity characteristics")
    if "profile" in f or "complete face" in f:
        return _sentences(_clean_phrase(profile.get("gender_authority_prompt", "")), _clean_phrase(profile.get("identity_detail_prompt", "")))
    if any(x in f for x in ("chin", "jawline", "beard")):
        return _sentences(base, _profile_value_v231(profile, "jaw_shape", " jaw"), _profile_value_v231(profile, "chin_shape", " chin"), _profile_value_v231(profile, "lip_shape", " lips"), _clean_phrase(profile.get("facial_hair_prompt", "")))
    if "ear" in f:
        return _sentences(base, _profile_value_v231(profile, "hair_color", " hair"), "preserve the exact local ear shape, folds, skin texture, and nearby hairline")
    if any(x in f for x in ("nipple", "areola", "chest center")):
        return _sentences(base, _clean_phrase(profile.get("chest_anatomy_prompt", "")), "preserve the exact local skin texture and anatomical placement")
    if "pubic mons" in f:
        return _sentences(base, _clean_phrase(profile.get("pubic_hair_prompt", "")), "preserve the exact local grooming pattern, skin texture, and anatomical placement")
    if "genital" in f:
        return _sentences(base, _clean_phrase(profile.get("groin_anatomy_prompt", "")), _clean_phrase(profile.get("pubic_hair_prompt", "")))
    return _sentences(base, "preserve the exact local skin texture and anatomical identity characteristics")


_FOCUS_MARK_TOKENS_V231 = {
    "left eye": ("left eye", "left eyelid", "left eyebrow", "left brow", "left temple"),
    "right eye": ("right eye", "right eyelid", "right eyebrow", "right brow", "right temple"),
    "both eyes": ("eye", "eyebrow", "brow", "bridge", "forehead", "temple"),
    "nose": ("nose", "nostril", "septum", "bridge", "columella"),
    "mouth": ("mouth", "lip", "philtrum", "lower nose", "chin"),
    "forehead": ("forehead", "hairline", "temple", "eyebrow", "brow"),
    "left profile": ("left face", "left facial", "left eyebrow", "left eye", "left temple", "left cheek", "left ear", "left jaw", "left lip", "left nostril"),
    "right profile": ("right face", "right facial", "right eyebrow", "right eye", "right temple", "right cheek", "right ear", "right jaw", "right lip", "right nostril"),
    "left ear": ("left ear",),
    "right ear": ("right ear",),
    "left nipple": ("left nipple", "left areola", "left breast", "upper left chest"),
    "right nipple": ("right nipple", "right areola", "right breast", "upper right chest"),
    "both nipples": ("nipple", "areola", "breast", "chest"),
    "navel": ("navel", "belly button", "umbilical", "abdomen"),
    "pubic mons": ("pubic", "mons", "lower abdomen", "groin"),
    "genital": ("genital", "groin", "pubic", "penis", "vulva", "labia", "scrot", "foreskin"),
    "left hand": ("left hand", "left wrist", "left finger", "left palm"),
    "right hand": ("right hand", "right wrist", "right finger", "right palm"),
    "left foot": ("left foot", "left ankle", "left toe"),
    "right foot": ("right foot", "right ankle", "right toe"),
}


def _focus_mark_tokens_v231(focus: str) -> tuple[str, ...]:
    f = focus.lower()
    if "left eye" in f:
        return _FOCUS_MARK_TOKENS_V231["left eye"]
    if "right eye" in f:
        return _FOCUS_MARK_TOKENS_V231["right eye"]
    if "both eyes" in f:
        return _FOCUS_MARK_TOKENS_V231["both eyes"]
    if "nose" in f or "septum" in f:
        return _FOCUS_MARK_TOKENS_V231["nose"]
    if "mouth" in f or "lip" in f:
        return _FOCUS_MARK_TOKENS_V231["mouth"]
    if "forehead" in f or "hairline" in f:
        return _FOCUS_MARK_TOKENS_V231["forehead"]
    if "left facial profile" in f:
        return _FOCUS_MARK_TOKENS_V231["left profile"]
    if "right facial profile" in f:
        return _FOCUS_MARK_TOKENS_V231["right profile"]
    for key in ("left ear", "right ear", "left nipple", "right nipple", "both nipples", "navel", "pubic mons", "left hand", "right hand", "left foot", "right foot"):
        if key in f:
            return _FOCUS_MARK_TOKENS_V231[key]
    if "genital" in f:
        return _FOCUS_MARK_TOKENS_V231["genital"]
    if "complete face" in f:
        return tuple(sorted(set(sum((_FOCUS_MARK_TOKENS_V231[k] for k in ("both eyes", "nose", "mouth", "forehead", "left ear", "right ear")), ()))))
    return tuple(token for token in re.split(r"[^a-z0-9]+", f) if len(token) > 3)


def _entry_matches_focus_v231(entry: str, focus: str) -> bool:
    value = entry.lower()
    f = focus.lower()
    if "left" in f and "right" in value and "left" not in value and "both" not in value:
        return False
    if "right" in f and "left" in value and "right" not in value and "both" not in value:
        return False
    return any(token in value for token in _focus_mark_tokens_v231(focus))


def _local_marks_prompt_v231(profile: dict, focus: str) -> tuple[str, str]:
    tattoos = [str(x) for x in profile.get("tattoo_entries", []) if _entry_matches_focus_v231(str(x), focus)]
    piercings = [str(x) for x in profile.get("piercing_entries", []) if _entry_matches_focus_v231(str(x), focus)]
    parts: list[str] = []
    if tattoos:
        parts.append("preserve each local permanent skin marking in this crop exactly once at its documented location, scale, orientation, color, and wording: " + "; ".join(tattoos))
    if piercings:
        parts.append("preserve each local attached jewelry item in this crop exactly once at its documented location, orientation, material, and jewelry type: " + "; ".join(piercings))
    if not tattoos:
        parts.append("the visible local skin has continuous natural texture without added decorative pigment or lettering")
    if not piercings:
        parts.append("the selected local region has no added attached jewelry")
    parts.append("do not add, duplicate, mirror, relocate, merge, or invent any local mark or jewelry")
    summary = f"Local tattoos: {len(tattoos)}; local piercings: {len(piercings)}"
    return _sentences(*parts), summary


def _extreme_macro_sections_v231(profile: dict, plan: dict) -> dict[str, str]:
    focus = _focus_value_v231(plan)
    crop = _focus_crop_prompt_v231(focus)
    camera = _focus_local_camera_v231(plan, focus)
    eye_state = _focus_eye_state_v231(focus)
    identity = _focus_identity_prompt_v231(profile, focus)
    local_marks, local_marks_summary = _local_marks_prompt_v231(profile, focus)
    environment = _clean_phrase(plan.get("environment_prompt", ""))
    integrity = _focus_specific_integrity_lock_v22(focus)
    exclusion = _sentences(
        "one uninterrupted image and one crop only",
        "do not create a split-screen, collage, inset, comparison panel, secondary view, portrait companion, or full-body companion image",
        "do not show unrelated body regions or repeat the selected detail elsewhere in the image",
    )
    return {
        "focus": focus,
        "crop": crop,
        "camera": camera,
        "eye_state": eye_state,
        "identity": identity,
        "local_marks": local_marks,
        "local_marks_summary": local_marks_summary,
        "environment": environment,
        "integrity": integrity,
        "exclusion": exclusion,
    }


# --------------------------- Character Creator -------------------------------

class CharacterBlueprintCreatorV230:
    CATEGORY = "character creation/v2"
    FUNCTION = "build_blueprint_v230"
    DESCRIPTION = (
        "Current Character Creator. Defines one primary character. Gender identity, chest anatomy, groin anatomy, "
        "presentation, outfit source, hair, tattoos, and piercings are independently source-gated and clearly labeled."
    )

    RETURN_TYPES = CharacterBlueprintCreatorV224.RETURN_TYPES + ("STRING", "STRING", "STRING")
    RETURN_NAMES = CharacterBlueprintCreatorV224.RETURN_NAMES + (
        "control_legend", "anatomy_configuration_summary", "active_hair_prompt",
    )

    @classmethod
    def INPUT_TYPES(cls):
        preset_outfits = [x for x in DEFAULT_CLOTHING if x not in {"Clinical Unclothed Documentation", "Custom"}]
        return {"required": {
            "primary_character_gender": (PRIMARY_GENDERS_V230, {"default": "Adult Woman"}),
            "age_range": (AGE_RANGES, {"default": "25–34"}),
            "heritage": (HERITAGES, {"default": "Unspecified"}),
            "custom_heritage": ("STRING", {"default": "", "multiline": False}),
            "skin_tone": (SKIN_TONES, {"default": "Medium"}),
            "complexion": (COMPLEXIONS, {"default": "Natural Skin Texture"}),
            "face_shape": (["Oval", "Round", "Heart-Shaped", "Soft Angular", "Square", "Long", "Diamond", "Unspecified"], {"default": "Oval"}),
            "jaw_shape": (JAW_SHAPES, {"default": "Defined"}),
            "chin_shape": (CHIN_SHAPES, {"default": "Rounded"}),
            "eye_color": (EYE_COLORS, {"default": "Brown"}),
            "eye_shape": (EYE_SHAPES, {"default": "Almond"}),
            "eyebrow_shape": (EYEBROWS, {"default": "Soft Arch"}),
            "nose_shape": (NOSES, {"default": "Straight"}),
            "lip_shape": (LIPS, {"default": "Balanced Medium"}),

            "hair_color": (HAIR_COLORS, {"default": "Dark Brown"}),
            "custom_hair_color": ("STRING", {"default": "", "multiline": False}),
            "hair_length": (HAIR_LENGTHS_V230, {"default": "Shoulder-Length"}),
            "custom_hair_length": ("STRING", {"default": "", "multiline": False}),
            "hair_texture": (HAIR_TEXTURES_V230, {"default": "Slightly Wavy"}),
            "custom_hair_texture": ("STRING", {"default": "", "multiline": False}),
            "hair_style": (HAIR_STYLES_V230, {"default": "Loose Natural"}),
            "custom_hair_style": ("STRING", {"default": "", "multiline": False}),
            "facial_hair": (FACIAL_HAIR, {"default": "None"}),
            "custom_facial_hair": ("STRING", {"default": "", "multiline": True}),

            "height": (HEIGHTS, {"default": "Average"}),
            "body_type": (BODY_TYPES, {"default": "Average"}),
            "buttocks": (BUTTOCKS, {"default": "Average"}),

            "chest_anatomy": (CHEST_ANATOMY_V230, {"default": "Auto — Match Gender Identity"}),
            "male_chest": (MALE_CHEST, {"default": "Average Male Chest"}),
            "custom_chest_description": ("STRING", {"default": "", "multiline": True}),
            "bust_size": (BUST_SIZES, {"default": "Unspecified"}),
            "bust_shape": (BUST_SHAPES, {"default": "Unspecified"}),
            "bust_position": (BUST_POSITIONS, {"default": "Unspecified"}),
            "bust_firmness": (BUST_FIRMNESS, {"default": "Unspecified"}),
            "bust_augmentation": (BUST_AUGMENTATION, {"default": "Unspecified"}),

            "groin_anatomy": (GROIN_ANATOMY_V230, {"default": "Auto — Match Gender Identity"}),
            "male_genital_size": (MALE_GENITAL_SIZES, {"default": "Unspecified"}),
            "male_foreskin_status": (FORESKIN_STATUS_V230, {"default": "Unspecified"}),
            "custom_groin_anatomy": ("STRING", {"default": "", "multiline": True}),
            "pubic_hair_style": (PUBIC_HAIR_STYLES_V224, {"default": "Unspecified"}),
            "custom_pubic_hair_style": ("STRING", {"default": "", "multiline": False}),
            "use_advanced_lower_body_notes": (["Off", "On"], {"default": "Off"}),
            "advanced_lower_body_notes": ("STRING", {"default": "", "multiline": True}),

            "visible_presentation_mode": (PRESENTATION_MODES_V230, {"default": "Clothed — Use Outfit Controls"}),
            "custom_mode_body_detail": (CUSTOM_BODY_DETAIL_V230, {"default": "Body Shape Only — No Explicit Anatomy"}),
            "custom_presentation_text": ("STRING", {"default": "", "multiline": True}),

            "outfit_input_method": (OUTFIT_INPUT_METHODS_V230, {"default": "Preset — Ready-Made Complete Outfit"}),
            "preset_outfit_if_selected": (preset_outfits, {"default": "Casual Jeans and T-Shirt"}),
            "exact_outfit_text": ("STRING", {"default": "", "multiline": True, "placeholder": "Used only with Exact Text — describe the complete outfit here"}),
            "structured_outfit_layout": (STRUCTURED_OUTFIT_TYPES_V230, {"default": "Top + Bottom Outfit"}),
            "structured_top": ("STRING", {"default": "", "multiline": False}),
            "structured_bottom": ("STRING", {"default": "", "multiline": False}),
            "structured_footwear": ("STRING", {"default": "", "multiline": False}),
            "structured_outerwear": ("STRING", {"default": "", "multiline": False}),
            "structured_one_piece": ("STRING", {"default": "", "multiline": False}),
            "structured_swimwear_top": ("STRING", {"default": "", "multiline": False}),
            "structured_swimwear_bottom": ("STRING", {"default": "", "multiline": False}),
            "lingerie_style_if_selected": (LINGERIE_STYLES_V2, {"default": "Matching Bra and Brief Set"}),
            "custom_lingerie_description": ("STRING", {"default": "", "multiline": True}),
            "outfit_notes": ("STRING", {"default": "", "multiline": True}),

            "removable_jewelry": (JEWELRY_LEVELS, {"default": "Minimal"}),
            "removable_jewelry_description": ("STRING", {"default": "", "multiline": True}),

            "tattoo_status": (MARK_STATUSES, {"default": "None"}),
            "tattoo_descriptors": ("STRING", {"default": "", "multiline": True, "placeholder": "One tattoo per line, including exact location"}),
            "piercing_status": (MARK_STATUSES, {"default": "None"}),
            "piercing_input_mode": (PIERCING_INPUT_MODES_V22, {"default": "Descriptor List"}),
            "piercing_descriptors": ("STRING", {"default": "", "multiline": True, "placeholder": "One piercing per line, including exact location and jewelry"}),
            "piercing_location": (["", "Left Eyebrow", "Right Eyebrow", "Left Nostril", "Right Nostril", "Septum", "Bridge", "Left Lip", "Right Lip", "Center Lip", "Left Nipple", "Right Nipple", "Other"], {"default": ""}),
            "piercing_type": (["", "Stud", "Hoop", "Curved Barbell", "Straight Barbell", "Circular Barbell", "Horseshoe", "Clicker", "Seam Ring", "Decorative Ring", "Custom"], {"default": ""}),
            "piercing_material": (["", "Black Titanium", "Silver Titanium", "Gold", "Rose Gold", "Steel", "Custom"], {"default": ""}),
            "piercing_visibility": (["", "Subtle", "Normal", "Prominent", "Documentation"], {"default": "Normal"}),
            "structured_piercing_custom": ("STRING", {"default": "", "multiline": False}),

            "custom_identity_notes": ("STRING", {"default": "", "multiline": True}),
        }}

    def build_blueprint_v230(self, **kwargs):
        gender_label = kwargs["primary_character_gender"]
        canonical_gender = GENDER_CANONICAL_V230[gender_label]
        warnings: list[str] = []

        heritage = kwargs["heritage"]
        heritage_prompt = kwargs["custom_heritage"].strip() if heritage == "Custom" else ("" if heritage == "Unspecified" else heritage.lower())
        if heritage == "Custom" and not kwargs["custom_heritage"].strip():
            warnings.append("Heritage is Custom but Custom Heritage is blank.")

        hair_prompt, hair_warnings = _hair_prompt_v230(
            kwargs["hair_color"], kwargs["custom_hair_color"], kwargs["hair_length"],
            kwargs["custom_hair_length"], kwargs["hair_texture"], kwargs["custom_hair_texture"],
            kwargs["hair_style"], kwargs["custom_hair_style"],
        )
        warnings.extend(hair_warnings)
        facial_hair_prompt, facial_warning = _facial_hair_prompt_v230(kwargs["facial_hair"], kwargs["custom_facial_hair"])
        if facial_warning:
            warnings.append(facial_warning)

        cleaned_identity_notes, removed_mark_clauses = _clean_mark_negations_v224(
            kwargs["custom_identity_notes"], kwargs["tattoo_status"], kwargs["piercing_status"]
        )
        if removed_mark_clauses:
            warnings.append("Status selectors ignored redundant custom mark-negation text: " + "; ".join(removed_mark_clauses))

        primary_gender_prompt = _primary_gender_prompt_v230(gender_label)
        identity_details = _join(
            f"age range {kwargs['age_range']}",
            f"{heritage_prompt} heritage" if heritage_prompt else "",
            f"{kwargs['skin_tone'].lower()} skin tone" if kwargs["skin_tone"] != "Custom / Unspecified" else "",
            kwargs["complexion"].lower() if kwargs["complexion"] != "Unspecified" else "",
            f"{kwargs['face_shape'].lower()} face" if kwargs["face_shape"] != "Unspecified" else "",
            f"{kwargs['jaw_shape'].lower()} jaw" if kwargs["jaw_shape"] != "Unspecified" else "",
            f"{kwargs['chin_shape'].lower()} chin" if kwargs["chin_shape"] != "Unspecified" else "",
            f"{kwargs['eye_color'].lower()} eyes" if kwargs["eye_color"] != "Custom / Unspecified" else "",
            f"{kwargs['eye_shape'].lower()} eye shape" if kwargs["eye_shape"] != "Unspecified" else "",
            f"{kwargs['eyebrow_shape'].lower()} eyebrows" if kwargs["eyebrow_shape"] != "Unspecified" else "",
            f"{kwargs['nose_shape'].lower()} nose" if kwargs["nose_shape"] != "Unspecified" else "",
            f"{kwargs['lip_shape'].lower()} lips" if kwargs["lip_shape"] != "Unspecified" else "",
            hair_prompt,
            facial_hair_prompt,
            cleaned_identity_notes,
        )
        face_identity = _join(primary_gender_prompt, identity_details)

        body_shape = BODY_SHAPE_PROMPTS_V230.get(kwargs["body_type"], "")
        height_prompt = "" if kwargs["height"] == "Unspecified" else f"{kwargs['height'].lower()} height"
        body_shape = _join(height_prompt, body_shape)

        resolved_chest = _resolve_chest_mode_v230(gender_label, kwargs["chest_anatomy"])
        chest_clothed, chest_anatomy, bust_prompt, chest_warnings = _chest_prompts_v230(
            resolved_chest, kwargs["male_chest"], kwargs["custom_chest_description"],
            kwargs["bust_size"], kwargs["bust_shape"], kwargs["bust_position"],
            kwargs["bust_firmness"], kwargs["bust_augmentation"],
        )
        warnings.extend(chest_warnings)

        resolved_groin = _resolve_groin_mode_v230(gender_label, kwargs["groin_anatomy"])
        groin_prompt, groin_warnings = _groin_prompt_v230(
            resolved_groin, kwargs["male_genital_size"], kwargs["male_foreskin_status"],
            kwargs["custom_groin_anatomy"],
        )
        warnings.extend(groin_warnings)

        pubic_prompt = _pubic_hair_prompt_v224(canonical_gender, kwargs["pubic_hair_style"], kwargs["custom_pubic_hair_style"])
        if kwargs["pubic_hair_style"] == "Custom" and not kwargs["custom_pubic_hair_style"].strip():
            warnings.append("Pubic Hair Style is Custom but Custom Pubic Hair Style is blank.")
        advanced_lower = kwargs["advanced_lower_body_notes"].strip() if kwargs["use_advanced_lower_body_notes"] == "On" else ""

        lower_silhouette = _identity_lower_silhouette_v230(gender_label)
        buttocks = "" if kwargs["buttocks"] == "Unspecified" else f"{kwargs['buttocks'].lower()} gluteal build"
        clothed_upper = _join(body_shape, chest_clothed)
        anatomy_upper = _join(body_shape, chest_anatomy)
        clothed_lower = _join(buttocks, lower_silhouette)
        anatomy_lower = _join(buttocks, lower_silhouette, groin_prompt, pubic_prompt, advanced_lower)

        tattoo_prompt, tattoo_entries, tattoo_warning, tattoo_lock = _mark_prompt_v22(
            "Tattoo", kwargs["tattoo_status"], kwargs["tattoo_descriptors"]
        )
        if tattoo_warning:
            warnings.append(tattoo_warning)
        if kwargs["tattoo_status"] == "None":
            tattoo_lock = ""

        piercing_warnings: list[str] = []
        piercing_status = kwargs["piercing_status"]
        if piercing_status == "None":
            piercing_prompt, piercing_entries, piercing_lock = "", [], ""
        elif piercing_status == "Multiple":
            piercing_prompt, piercing_entries, piercing_warning, piercing_lock = _mark_prompt_v22(
                "Piercing", "Multiple", kwargs["piercing_descriptors"]
            )
            if piercing_warning:
                piercing_warnings.append(piercing_warning)
        elif kwargs["piercing_input_mode"] == "Structured Single Piercing":
            piercing_prompt, piercing_entries, piercing_warning, piercing_lock = _structured_single_piercing_prompt_v22(
                kwargs["piercing_location"], kwargs["piercing_type"], kwargs["piercing_material"],
                kwargs["piercing_visibility"], kwargs["structured_piercing_custom"],
            )
            if piercing_warning:
                piercing_warnings.append(piercing_warning)
        else:
            piercing_prompt, piercing_entries, piercing_warning, piercing_lock = _mark_prompt_v22(
                "Piercing", "One", kwargs["piercing_descriptors"]
            )
            if piercing_warning:
                piercing_warnings.append(piercing_warning)
        warnings.extend(piercing_warnings)

        marks_prompt = _join(tattoo_prompt, piercing_prompt)
        anatomy_integrity_lock = _mark_anatomy_integrity_lock_v22(
            canonical_gender, tattoo_entries, piercing_entries
        )

        presentation_label = kwargs["visible_presentation_mode"]
        presentation_mode = PRESENTATION_CANONICAL_V230[presentation_label]
        outfit_method_label = kwargs["outfit_input_method"]
        outfit_source = OUTFIT_SOURCE_CANONICAL_V230[outfit_method_label]
        structured_type_label = kwargs["structured_outfit_layout"]
        structured_type = STRUCTURED_TYPE_CANONICAL_V230[structured_type_label]

        # Only the active outfit input path is passed to the builder. Hidden stored
        # values never create warnings or leak into the prompt.
        if presentation_mode != "Clothed Character":
            outfit_prompt, outfit_components, outfit_warnings = "", {}, []
        else:
            exact_active = kwargs["exact_outfit_text"] if outfit_source == "Exact Outfit Text" else ""
            structured_active = outfit_source == "Structured Components"
            outfit_prompt, outfit_components, outfit_warnings = _build_authoritative_outfit_v2(
                outfit_source,
                kwargs["preset_outfit_if_selected"],
                exact_active,
                structured_type,
                kwargs["lingerie_style_if_selected"],
                kwargs["structured_top"] if structured_active else "",
                kwargs["structured_bottom"] if structured_active else "",
                kwargs["structured_footwear"] if structured_active else "",
                kwargs["structured_outerwear"] if structured_active else "",
                kwargs["structured_one_piece"] if structured_active else "",
                kwargs["structured_swimwear_top"] if structured_active else "",
                kwargs["structured_swimwear_bottom"] if structured_active else "",
                kwargs["custom_lingerie_description"] if structured_active else "",
                kwargs["outfit_notes"],
            )
            # The older helper appends a long negative "wardrobe authority" clause.
            # V2.3 replaces it with one short positive-state sentence below.
            outfit_prompt = re.sub(
                r"\s*,?\s*wardrobe authority:.*$",
                "",
                str(outfit_prompt or ""),
                flags=re.IGNORECASE,
            ).strip(" ,.;")
        warnings.extend(outfit_warnings)

        jewelry = "" if kwargs["removable_jewelry"] == "None" else _join(
            f"{kwargs['removable_jewelry'].lower()} removable jewelry",
            kwargs["removable_jewelry_description"],
        )
        clothed_presentation = _join(outfit_prompt, jewelry, "the outfit is worn normally with stable fit and coverage")
        clinical_presentation = "unclothed neutral non-aroused clinical anatomy documentation"
        if piercing_entries:
            clinical_presentation = _join(clinical_presentation, "only the defined permanent piercings remain")

        custom_body_detail = kwargs["custom_mode_body_detail"]
        custom_presentation = kwargs["custom_presentation_text"].strip()
        if presentation_mode == "Clothed Character":
            active_presentation = clothed_presentation
            active_body = _join(clothed_upper, clothed_lower)
        elif presentation_mode == "Clinical Anatomy":
            active_presentation = clinical_presentation
            active_body = _join(anatomy_upper, anatomy_lower)
        else:
            active_presentation = custom_presentation
            if not custom_presentation:
                warnings.append("Custom Presentation is selected but Custom Presentation Text is blank.")
            if custom_body_detail == "Clinical Anatomy — Include Selected Chest / Groin":
                active_body = _join(anatomy_upper, anatomy_lower)
            elif custom_body_detail == "Identity Only — No Body Description":
                active_body = ""
            else:
                active_body = _join(clothed_upper, clothed_lower)

        active_character = _join(primary_gender_prompt, identity_details, active_body, active_presentation, marks_prompt, tattoo_lock, piercing_lock, anatomy_integrity_lock)
        clothed_character = _join(primary_gender_prompt, identity_details, clothed_upper, clothed_lower, clothed_presentation, marks_prompt, tattoo_lock, piercing_lock, anatomy_integrity_lock)
        clinical_character = _join(primary_gender_prompt, identity_details, anatomy_upper, anatomy_lower, clinical_presentation, marks_prompt, tattoo_lock, piercing_lock, anatomy_integrity_lock)

        stable_base = _join(gender_label, kwargs["age_range"], kwargs["heritage"], kwargs["face_shape"], hair_prompt, kwargs["body_type"], resolved_chest, resolved_groin)
        character_id = _slug(stable_base) + "_" + hashlib.sha1(active_character.encode("utf-8")).hexdigest()[:8]

        anatomy_summary = "\n".join([
            f"Gender identity: {gender_label}",
            f"Resolved chest anatomy: {resolved_chest}",
            f"Resolved groin anatomy: {resolved_groin}",
            f"Male genital size: {kwargs['male_genital_size'] if resolved_groin == 'Male External Anatomy' else '[inactive]'}",
            f"Foreskin status: {kwargs['male_foreskin_status'] if resolved_groin == 'Male External Anatomy' else '[inactive]'}",
            f"Pubic hair: {kwargs['pubic_hair_style']} (included only in clinical crops that show the groin)",
        ])
        summary = "\n".join([
            "FCC CHARACTER CREATOR — ACTIVE PATH",
            f"Primary character: {gender_label}",
            f"Hair: {hair_prompt or '[unspecified]'}",
            f"Body: {body_shape or '[unspecified]'}",
            f"Chest: {resolved_chest} → {chest_anatomy or '[blank]'}",
            f"Groin: {resolved_groin} → {groin_prompt or '[not described]'}",
            f"Presentation: {presentation_label}",
            f"Outfit path: {outfit_method_label if presentation_mode == 'Clothed Character' else '[inactive]'}",
            f"Tattoo path: {kwargs['tattoo_status']} → {len(tattoo_entries)} active",
            f"Piercing path: {piercing_status} → {len(piercing_entries)} active",
            f"Warnings: {' '.join(warnings) if warnings else 'None'}",
        ])

        profile = {
            "schema": "CHARACTER_BLUEPRINT_V230",
            "schema_version": 11,
            "character_id": character_id,
            "primary_character_gender": gender_label,
            "age_range": kwargs["age_range"],
            "heritage": kwargs["heritage"],
            "heritage_prompt": heritage_prompt,
            "skin_tone": kwargs["skin_tone"],
            "complexion": kwargs["complexion"],
            "face_shape": kwargs["face_shape"],
            "jaw_shape": kwargs["jaw_shape"],
            "chin_shape": kwargs["chin_shape"],
            "eye_color": kwargs["eye_color"],
            "eye_shape": kwargs["eye_shape"],
            "eyebrow_shape": kwargs["eyebrow_shape"],
            "nose_shape": kwargs["nose_shape"],
            "lip_shape": kwargs["lip_shape"],
            "hair_color": kwargs["custom_hair_color"].strip() if kwargs["hair_color"] == "Custom" else kwargs["hair_color"],
            "hair_length": kwargs["hair_length"],
            "hair_texture": kwargs["hair_texture"],
            "hair_style": kwargs["hair_style"],
            "gender": canonical_gender,
            "gender_authority_prompt": primary_gender_prompt,
            "identity_detail_prompt": identity_details,
            "face_identity": face_identity,
            "hair_prompt": hair_prompt,
            "facial_hair_prompt": facial_hair_prompt,
            "height": kwargs["height"],
            "body_type": kwargs["body_type"],
            "body_type_authority_prompt": body_shape,
            "buttocks": kwargs["buttocks"],
            "chest_anatomy_selection": kwargs["chest_anatomy"],
            "resolved_chest_anatomy": resolved_chest,
            "chest_clothed_prompt": chest_clothed,
            "chest_anatomy_prompt": chest_anatomy,
            "bust_clothed_authority_prompt": chest_clothed if resolved_chest == "Bust Anatomy — Use Bust Controls" else "",
            "bust_anatomy_authority_prompt": chest_anatomy if resolved_chest == "Bust Anatomy — Use Bust Controls" else "",
            "bust_size": kwargs["bust_size"],
            "bust_shape": kwargs["bust_shape"],
            "bust_position": kwargs["bust_position"],
            "bust_firmness": kwargs["bust_firmness"],
            "bust_augmentation": kwargs["bust_augmentation"],
            "groin_anatomy_selection": kwargs["groin_anatomy"],
            "resolved_groin_anatomy": resolved_groin,
            "groin_anatomy_prompt": groin_prompt,
            "male_genital_size": kwargs["male_genital_size"] if resolved_groin == "Male External Anatomy" else "Not applicable",
            "male_foreskin_status": kwargs["male_foreskin_status"] if resolved_groin == "Male External Anatomy" else "Not applicable",
            "pubic_hair_style": kwargs["pubic_hair_style"],
            "pubic_hair_prompt": pubic_prompt,
            "anatomy_upper_body": anatomy_upper,
            "clothed_upper_body": clothed_upper,
            "upper_body_identity": anatomy_upper,
            "anatomy_lower_body": anatomy_lower,
            "clothed_lower_body": clothed_lower,
            "lower_body_identity": anatomy_lower,
            "presentation_mode": presentation_mode,
            "presentation_mode_label": presentation_label,
            "custom_presentation_body_detail": custom_body_detail,
            "custom_mode_body_detail_label": custom_body_detail,
            "outfit_source": outfit_source,
            "outfit_source_label": outfit_method_label,
            "outfit_preset": kwargs["preset_outfit_if_selected"],
            "preset_outfit_if_selected": kwargs["preset_outfit_if_selected"],
            "structured_outfit_type": structured_type,
            "structured_outfit_type_label": structured_type_label,
            "outfit_components": outfit_components,
            "structured_outfit_prompt": outfit_prompt,
            "jewelry_prompt": jewelry,
            "default_clothing_prompt": clothed_presentation,
            "active_presentation_prompt": active_presentation,
            "active_body_prompt": active_body,
            "active_character_prompt": active_character,
            "clothed_character_prompt": clothed_character,
            "clinical_character_prompt": clinical_character,
            "full_profile_prompt": active_character,
            "marks_prompt": marks_prompt,
            "tattoo_status": kwargs["tattoo_status"],
            "tattoo_entries": tattoo_entries,
            "tattoo_count_lock": tattoo_lock,
            "piercing_status": piercing_status,
            "piercing_input_mode": kwargs["piercing_input_mode"],
            "piercing_entries": piercing_entries,
            "piercing_count_lock": piercing_lock,
            "anatomy_integrity_lock": anatomy_integrity_lock,
            "warnings": " ".join(warnings),
            "presentation_summary": summary,
            "control_legend": CREATOR_CONTROL_LEGEND_V230,
            "anatomy_configuration_summary": anatomy_summary,
        }
        blueprint_json = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        active_chest = chest_anatomy if presentation_mode == "Clinical Anatomy" else chest_clothed

        return (
            face_identity, anatomy_upper, anatomy_lower, active_chest, marks_prompt,
            clothed_presentation, active_character, character_id, profile, " ".join(warnings),
            clothed_upper, anatomy_upper, clothed_lower, anatomy_lower,
            outfit_prompt, blueprint_json, active_presentation, active_body,
            active_character, clothed_character, clinical_character, summary,
            tattoo_lock, piercing_lock, anatomy_integrity_lock,
            body_shape, active_chest,
            CREATOR_CONTROL_LEGEND_V230, anatomy_summary, hair_prompt,
        )


# ------------------------------ Shot Control ---------------------------------

class CharacterShotControlV230:
    CATEGORY = "character creation/v2"
    FUNCTION = "build_shot_plan_v230"
    DESCRIPTION = (
        "Current Shot Control. Freestyle uses every visible shot setting and always includes Scene Direction. "
        "Custom Shot Direction replaces only framing/camera/pose while preserving the Character Creator."
    )

    RETURN_TYPES = CharacterShotControlV22.RETURN_TYPES + ("STRING", "STRING")
    RETURN_NAMES = CharacterShotControlV22.RETURN_NAMES + ("control_legend", "scene_prompt")

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "character_blueprint": ("CHARACTER_BLUEPRINT",),
            "planner_mode": (PLANNER_MODES_V230, {"default": "Freestyle — Use Shot Controls"}),
            "custom_shot_direction": ("STRING", {"default": "", "multiline": True, "placeholder": "Used only in Custom Shot Direction mode. Replaces framing, camera, and pose; character settings still apply."}),
            "scene_cast": (SCENE_CAST_V230, {"default": "Solo — Primary Character Only"}),
            "scene_direction": ("STRING", {"default": "", "multiline": True, "placeholder": "Always active: interactions, extra people, props, action, and scene-specific direction."}),
            "shot_type": (SHOT_TYPES_V2, {"default": "Head and Shoulders"}),
            "custom_framing": ("STRING", {"default": "", "multiline": True}),
            "camera_view": (CAMERA_VIEWS, {"default": "Front View"}),
            "camera_height": (CAMERA_HEIGHTS_V2, {"default": "Eye Level"}),
            "lens": (LENSES_V2, {"default": "85mm Portrait — Recommended"}),
            "custom_camera": ("STRING", {"default": "", "multiline": True}),
            "pose": (POSES_V2, {"default": "Neutral Standing"}),
            "custom_pose": ("STRING", {"default": "", "multiline": True, "placeholder": "Used only when Pose = Custom"}),
            "expression": (EXPRESSIONS_V2, {"default": "Neutral"}),
            "custom_expression": ("STRING", {"default": "", "multiline": False}),
            "extreme_closeup_focus": (EXTREME_CLOSEUP_FOCUS_V2, {"default": "Complete Face"}),
            "custom_extreme_focus": ("STRING", {"default": "", "multiline": True}),
            "closeup_region": (CLOSEUP_REGIONS_V2, {"default": "Face Portrait"}),
            "custom_closeup_region": ("STRING", {"default": "", "multiline": True}),
            "background": (BACKGROUNDS_V2, {"default": "Studio Solid Gray"}),
            "custom_background": ("STRING", {"default": "", "multiline": True}),
            "lighting": (LIGHTING_V2, {"default": "Soft Natural Daylight"}),
            "custom_lighting": ("STRING", {"default": "", "multiline": True}),
            "photo_style": (PHOTO_STYLES, {"default": "Identity Documentation"}),
            "aspect_ratio": (ASPECT_RATIOS_V2, {"default": "Portrait 4:5"}),
            "distortion_guard": (DISTORTION_GUARDS_V2, {"default": "On — Natural Rectilinear"}),
            "shot_suffix": ("STRING", {"default": "", "multiline": True}),
        }}

    def build_shot_plan_v230(self, **kwargs):
        profile = kwargs["character_blueprint"] if isinstance(kwargs["character_blueprint"], dict) else {}
        mode = kwargs["planner_mode"]
        warnings: list[str] = []
        ignored: list[str] = []
        focus_mode = "Inactive"
        focus_region = ""

        custom_direction_mode = mode == "Custom Shot Direction — Keep Character Settings"
        scene_direction = kwargs["scene_direction"].strip()
        cast_prompt = _scene_cast_prompt_v230(kwargs["scene_cast"])
        if kwargs["scene_cast"] == "Custom — Describe People in Scene Direction" and not scene_direction:
            warnings.append("Custom scene cast is selected but Scene Direction is blank.")

        if custom_direction_mode:
            framing_prompt = kwargs["custom_shot_direction"].strip()
            if not framing_prompt:
                warnings.append("Custom Shot Direction mode is selected but Custom Shot Direction is blank.")
                framing_prompt = "natural camera framing and pose"
            camera_prompt = ""
            pose_prompt = ""
            shot_type_for_plan = "Custom Framing"
            if _looks_like_extreme_closeup_v231(framing_prompt):
                focus_mode = "Extreme Close-Up"
                focus_region = kwargs["custom_extreme_focus"].strip() if kwargs["extreme_closeup_focus"] == "Custom" else kwargs["extreme_closeup_focus"]
                ignored.extend(["shot type", "camera view", "camera height", "pose", "regional close-up focus"])
            else:
                ignored.extend(["shot type", "camera view", "camera height", "lens", "pose", "focus controls"])
        else:
            shot_type_for_plan = kwargs["shot_type"]
            if kwargs["shot_type"] == "Extreme Close-Up — Single Detail":
                focus_mode = "Extreme Close-Up"
                focus_region = kwargs["custom_extreme_focus"].strip() if kwargs["extreme_closeup_focus"] == "Custom" else kwargs["extreme_closeup_focus"]
                framing_prompt = _extreme_focus_prompt_v22(kwargs["extreme_closeup_focus"], kwargs["custom_extreme_focus"])
                ignored.extend(["regional close-up focus", "pose"])
                pose_prompt = ""
            elif kwargs["shot_type"] == "Close-Up — Regional Documentation":
                focus_mode = "Regional Close-Up"
                focus_region = kwargs["custom_closeup_region"].strip() if kwargs["closeup_region"] == "Custom" else kwargs["closeup_region"]
                framing_prompt = _regional_focus_prompt_v22(kwargs["closeup_region"], kwargs["custom_closeup_region"])
                ignored.append("extreme close-up focus")
                pose_prompt = None
            elif kwargs["shot_type"] == "Custom Framing":
                framing_prompt = kwargs["custom_framing"].strip()
                if not framing_prompt:
                    warnings.append("Custom Framing is selected but Custom Framing is blank.")
                    framing_prompt = "natural custom framing"
                if _looks_like_extreme_closeup_v231(framing_prompt):
                    focus_mode = "Extreme Close-Up"
                    focus_region = kwargs["custom_extreme_focus"].strip() if kwargs["extreme_closeup_focus"] == "Custom" else kwargs["extreme_closeup_focus"]
                    pose_prompt = ""
                    ignored.extend(["regional close-up focus", "pose"])
                else:
                    pose_prompt = None
                    ignored.extend(["extreme close-up focus", "regional close-up focus"])
            else:
                framing_prompt = SHOT_PROMPTS_V2.get(kwargs["shot_type"], kwargs["shot_type"].lower())
                pose_prompt = None
                ignored.extend(["extreme close-up focus", "regional close-up focus"])

            view_prompt = CAMERA_PROMPTS.get(kwargs["camera_view"], kwargs["camera_view"].lower())
            if kwargs["camera_height"] == "Custom" or kwargs["lens"] == "Custom":
                custom_camera = kwargs["custom_camera"].strip()
                if not custom_camera:
                    warnings.append("Custom camera setting is selected but Custom Camera is blank.")
                height_prompt = custom_camera
                lens_prompt = ""
            else:
                height_prompt = CAMERA_HEIGHT_PROMPTS_V2.get(kwargs["camera_height"], "")
                lens_prompt = LENS_PROMPTS_V2.get(kwargs["lens"], "")
            if focus_mode == "Extreme Close-Up":
                lens_prompt = _join(lens_prompt, "macro close-focus detail with natural perspective")
            camera_prompt = _join(view_prompt, height_prompt, lens_prompt)

            if pose_prompt is None:
                if kwargs["pose"] == "Custom":
                    pose_prompt = kwargs["custom_pose"].strip()
                    if not pose_prompt:
                        warnings.append("Pose is Custom but Custom Pose is blank; no pose wording is added.")
                else:
                    pose_prompt = POSE_PROMPTS_V2.get(kwargs["pose"], kwargs["pose"].lower())

        if kwargs["expression"] == "Custom":
            expression_prompt = kwargs["custom_expression"].strip()
            if not expression_prompt:
                warnings.append("Expression is Custom but Custom Expression is blank; no expression wording is added.")
        else:
            expression_prompt = EXPRESSION_PROMPTS_V2.get(kwargs["expression"], kwargs["expression"].lower() + " expression")

        if kwargs["background"] == "Custom":
            background_prompt = kwargs["custom_background"].strip()
            if not background_prompt:
                warnings.append("Background is Custom but Custom Background is blank.")
        else:
            background_prompt = BACKGROUND_PROMPTS_V2.get(kwargs["background"], kwargs["background"].lower() + " background")
        if kwargs["lighting"] == "Custom":
            lighting_prompt = kwargs["custom_lighting"].strip()
            if not lighting_prompt:
                warnings.append("Lighting is Custom but Custom Lighting is blank.")
        else:
            lighting_prompt = LIGHTING_PROMPTS_V2.get(kwargs["lighting"], kwargs["lighting"].lower())
        environment_prompt = _join(background_prompt, lighting_prompt, kwargs["photo_style"].lower())

        if focus_mode == "Extreme Close-Up" and focus_region:
            facial_tokens = ("face", "eye", "eyebrow", "nose", "septum", "mouth", "lip", "forehead", "hairline", "chin", "jaw", "beard", "ear")
            if not any(token in focus_region.lower() for token in facial_tokens):
                expression_prompt = ""
                ignored.append("expression")

        distortion_prompt = ""
        if kwargs["distortion_guard"] == "On — Natural Rectilinear":
            distortion_prompt = "natural rectilinear perspective, normal proportions, and comfortable camera distance"

        scene_prompt = _join(cast_prompt, scene_direction)
        final_shot_prompt = _join(
            framing_prompt,
            camera_prompt,
            distortion_prompt,
            pose_prompt,
            expression_prompt,
            scene_prompt,
            environment_prompt,
            kwargs["shot_suffix"],
        )
        width, height = _aspect_dimensions_v2(kwargs["aspect_ratio"])
        warning_text = " ".join(warnings)
        character_id = profile.get("character_id", "unlinked-character")

        summary = "\n".join([
            "FCC UNIVERSAL SHOT CONTROL — ACTIVE PATH",
            f"Mode: {mode}",
            f"Scene cast: {kwargs['scene_cast']}",
            f"Scene direction: {scene_direction or '[blank]'}",
            f"Shot type: {shot_type_for_plan}",
            f"Framing: {framing_prompt}",
            f"Camera: {camera_prompt or '[defined by custom shot direction]'}",
            f"Pose: {pose_prompt or '[defined by custom shot direction / inactive]'}",
            f"Expression: {expression_prompt or '[inactive]'}",
            f"Focus: {focus_region or '[inactive]'}",
            f"Environment: {environment_prompt}",
            f"Aspect: {kwargs['aspect_ratio']} ({width} × {height})",
            f"Ignored controls: {', '.join(ignored) if ignored else 'None'}",
            f"Warnings: {warning_text or 'None'}",
        ])

        plan = {
            "schema": "FCC_SHOT_PLAN_V230",
            "schema_version": 6,
            "character_id": character_id,
            "planner_mode": mode,
            "scene_cast": kwargs["scene_cast"],
            "scene_cast_prompt": cast_prompt,
            "scene_direction": scene_direction,
            "scene_prompt": scene_prompt,
            "shot_type": shot_type_for_plan,
            "selected_shot_type": kwargs["shot_type"],
            "camera_view": kwargs["camera_view"],
            "camera_height": kwargs["camera_height"],
            "lens": kwargs["lens"],
            "pose": kwargs["pose"],
            "expression": kwargs["expression"],
            "focus_mode": focus_mode,
            "focus_region": focus_region,
            "selected_extreme_closeup_focus": kwargs["extreme_closeup_focus"],
            "custom_extreme_focus": kwargs["custom_extreme_focus"],
            "background": kwargs["background"],
            "lighting": kwargs["lighting"],
            "photo_style": kwargs["photo_style"],
            "aspect_ratio": kwargs["aspect_ratio"],
            "distortion_guard": kwargs["distortion_guard"],
            "framing_prompt": framing_prompt,
            "camera_prompt": camera_prompt,
            "pose_prompt": pose_prompt,
            "expression_prompt": expression_prompt,
            "environment_prompt": environment_prompt,
            "final_shot_prompt": final_shot_prompt,
            "recommended_width": width,
            "recommended_height": height,
            "ignored_controls": ignored,
            "warnings": warning_text,
            "active_settings_summary": summary,
            "control_legend": SHOT_CONTROL_LEGEND_V230,
        }
        return (
            plan, final_shot_prompt, framing_prompt, camera_prompt, pose_prompt,
            expression_prompt, environment_prompt, summary,
            json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True),
            width, height, warning_text,
            SHOT_CONTROL_LEGEND_V230, scene_prompt,
        )


# ------------------------------ Prompt Assembler -----------------------------

class CharacterPromptAssemblerV230:
    CATEGORY = "character creation/v2"
    FUNCTION = "assemble_prompt_v230"
    DESCRIPTION = (
        "Current compact assembler with minimal region-filtered extreme close-up routing. Uses natural Krea phrasing, directive Qwen phrasing, explicit primary-character identity, "
        "scene cast, custom scene direction, and independent chest/groin anatomy."
    )

    RETURN_TYPES = CharacterPromptAssemblerV224.RETURN_TYPES + ("STRING", "STRING", "STRING")
    RETURN_NAMES = CharacterPromptAssemblerV224.RETURN_NAMES + (
        "prompt_sections_json", "primary_character_prompt", "scene_direction_prompt",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "character_blueprint": ("CHARACTER_BLUEPRINT",),
            "shot_plan": ("FCC_SHOT_PLAN",),
            "generation_purpose": ([
                "Krea — First Identity Image",
                "Qwen — Edit from Image 1",
                "Qwen — Identity Documentation",
                "Qwen — Anatomy Documentation",
                "Qwen — Clothed Action / Lifestyle",
                "Krea — LoRA Expansion",
            ], {"default": "Krea — First Identity Image"}),
            "reference_label": ("STRING", {"default": "Image 1", "multiline": False}),
        }, "optional": {
            "trigger_word": ("STRING", {"default": "", "multiline": False}),
            "custom_prefix": ("STRING", {"default": "", "multiline": True}),
            "custom_suffix": ("STRING", {"default": "", "multiline": True}),
        }}

    def assemble_prompt_v230(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan = shot_plan if isinstance(shot_plan, dict) else {}
        krea = generation_purpose.startswith("Krea")
        qwen = generation_purpose.startswith("Qwen")

        primary_gender = _clean_phrase(profile.get("gender_authority_prompt", ""))
        identity = _clean_phrase(profile.get("identity_detail_prompt", ""))
        extreme_macro = _is_extreme_closeup_v231(plan)

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

        if extreme_macro:
            macro = _extreme_macro_sections_v231(profile, plan)
            crop = macro["crop"]
            camera = macro["camera"]
            scene = ""
            presentation = ""
            marks = macro["local_marks"]
            character_section = macro["identity"]
            body_section = ""
            appearance_section = _sentences(macro["local_marks"], macro["integrity"])
            shot_section = _sentences(
                macro["crop"],
                macro["camera"],
                macro["eye_state"],
                macro["environment"],
                macro["exclusion"],
            )
            if krea:
                final_prompt = _sentences(
                    trigger_word,
                    custom_prefix,
                    purpose,
                    shot_section,
                    character_section,
                    appearance_section,
                    "preserve the exact local identity characteristics of the selected detail",
                    custom_suffix,
                )
            else:
                qwen_instruction = _sentences(
                    purpose,
                    f"replace the original image with one tightly cropped macro view of {macro['focus'].lower()} only",
                    "preserve only identity characteristics and permanent marks physically belonging inside this selected crop",
                    "do not preserve or reproduce unrelated body regions from the reference image",
                )
                final_prompt = _sentences(
                    custom_prefix,
                    qwen_instruction,
                    shot_section,
                    character_section,
                    appearance_section,
                    custom_suffix,
                )
        else:
            crop = _crop_prompt_v230(plan)
            body_shape, chest, lower, groin = _visible_body_v230(profile, plan)
            presentation = _visible_presentation_v230(profile, plan)
            scene = _clean_phrase(plan.get("scene_prompt", ""))
            camera = _clean_phrase(plan.get("camera_prompt", ""))
            pose = _clean_phrase(plan.get("pose_prompt", ""))
            expression = _clean_phrase(plan.get("expression_prompt", ""))
            environment = _clean_phrase(plan.get("environment_prompt", ""))
            custom_direction = _clean_phrase(plan.get("framing_prompt", "")) if plan.get("planner_mode") == "Custom Shot Direction — Keep Character Settings" else ""
            marks = _clean_phrase(profile.get("marks_prompt", ""))
            tattoo_lock = _clean_phrase(profile.get("tattoo_count_lock", "")) if profile.get("tattoo_status") != "None" else ""
            piercing_lock = _clean_phrase(profile.get("piercing_count_lock", "")) if profile.get("piercing_status") != "None" else ""
            anatomy_lock = _clean_phrase(profile.get("anatomy_integrity_lock", ""))
            pubic = _clean_phrase(profile.get("pubic_hair_prompt", "")) if (
                _is_clinical(profile) and _crop_shows_groin_v230(plan)
            ) else ""
            if groin and groin in lower:
                lower = lower.replace(groin, "").strip(" ,.;")
            if pubic and pubic in lower:
                lower = lower.replace(pubic, "").strip(" ,.;")
            if pubic.lower().startswith("pubic-hair grooming authority:"):
                pubic = pubic.split(":", 1)[1].strip()

            if profile.get("tattoo_status") == "None":
                skin_surface = (
                    "keep all visible skin naturally unmarked and remove unlisted decorative pigment or lettering"
                    if qwen else
                    "all visible skin is naturally unmarked with continuous natural skin texture"
                )
            else:
                skin_surface = ""

            if profile.get("piercing_status") == "None":
                if qwen and _is_clinical(profile):
                    body_jewelry = "remove all attached and removable jewelry from the clinical documentation image"
                elif qwen:
                    body_jewelry = "remove unlisted attached body jewelry while preserving any selected removable outfit jewelry"
                elif _is_clinical(profile):
                    body_jewelry = "eyebrows, nose, lips, ears, chest, and navel have smooth uninterrupted skin with no attached jewelry"
                else:
                    body_jewelry = "eyebrows, nose, lips, ears, chest, and navel have smooth uninterrupted skin; selected removable outfit jewelry may remain"
            else:
                body_jewelry = ""

            shot_section = _sentences(
                custom_direction or crop,
                "" if custom_direction else camera,
                "" if custom_direction else pose,
                expression,
                scene,
                environment,
            )
            character_section = _sentences(primary_gender, identity)
            body_section = _sentences(body_shape, chest, lower, groin, pubic)
            appearance_section = _sentences(presentation, skin_surface, body_jewelry, marks, tattoo_lock, piercing_lock, anatomy_lock)

            if krea:
                final_prompt = _sentences(
                    trigger_word,
                    custom_prefix,
                    purpose,
                    shot_section,
                    character_section,
                    body_section,
                    appearance_section,
                    "keep the primary character consistent across identity, anatomy configuration, body proportions, hair, clothing, and permanent marks",
                    custom_suffix,
                )
            else:
                qwen_instruction = _sentences(
                    purpose,
                    "replace the original framing, camera, pose, and scene with the active Shot Control result",
                    "apply the active Character Creator identity, anatomy configuration, presentation, clothing, and permanent marks to the primary character",
                    "secondary people are not copies of the primary character unless Scene Direction explicitly requests that",
                )
                final_prompt = _sentences(
                    custom_prefix,
                    qwen_instruction,
                    shot_section,
                    character_section,
                    body_section,
                    appearance_section,
                    custom_suffix,
                )

        width = int(plan.get("recommended_width", 1024))
        height = int(plan.get("recommended_height", 1280))
        character_id = profile.get("character_id", "character")
        focus = plan.get("focus_region", "")
        shot_id = _slug(_join(character_id, generation_purpose, plan.get("planner_mode", ""), plan.get("shot_type", ""), focus, plan.get("pose", ""), plan.get("scene_direction", "")))
        presentation_mode = profile.get("presentation_mode", "Unspecified")
        marks_output = marks
        crop_authority = crop
        visible_outfit = "[omitted for extreme close-up]" if extreme_macro else presentation
        resolution_debug = f"{width} × {height} from {plan.get('aspect_ratio', 'selected aspect ratio')}"

        custom_direction = _clean_phrase(plan.get("framing_prompt", "")) if plan.get("planner_mode") == "Custom Shot Direction — Keep Character Settings" else ""
        advisory_parts = []
        if extreme_macro:
            advisory_parts.append("Extreme Close-Up minimal regional routing is active; pose, expression, scene interactions, full-body anatomy, clothing, and unrelated marks are omitted.")
        if plan.get("pose") == "Custom" and not plan.get("pose_prompt"):
            advisory_parts.append("Custom Pose is blank.")
        if plan.get("planner_mode") == "Custom Shot Direction — Keep Character Settings" and not custom_direction:
            advisory_parts.append("Custom Shot Direction is blank.")
        if profile.get("resolved_groin_anatomy") == "Male External Anatomy" and profile.get("presentation_mode") != "Clinical Anatomy":
            advisory_parts.append("Male genital size and foreskin status are stored but omitted from clothed prompts.")
        advisory = " ".join(advisory_parts)

        notes = "\n".join([
            f"Purpose: {generation_purpose}",
            f"Reference: {reference}",
            "Character Creator owns the primary character only.",
            "Shot Control owns scene cast, camera, pose, interaction, and environment.",
            "Custom Pose reads only Custom Pose. Custom Shot Direction reads only in its dedicated planner mode.",
            f"Extreme detail routing: {'Minimal local profile active' if extreme_macro else 'Inactive'}",
            f"Advisory: {advisory or 'None'}",
        ])
        active_summary = "\n\n".join([
            profile.get("presentation_summary", "Character settings unavailable"),
            plan.get("active_settings_summary", "Shot settings unavailable"),
            f"FINAL PRIMARY CHARACTER\n{character_section}",
            f"FINAL SCENE / SHOT\n{shot_section}",
            f"FINAL BODY / PRESENTATION\n{body_section or '[omitted by regional routing]'}\n{appearance_section}",
            notes,
        ])
        sections = {
            "purpose": purpose,
            "shot_scene": shot_section,
            "primary_character": character_section,
            "body": body_section,
            "appearance_marks": appearance_section,
            "routing_mode": "extreme_closeup_minimal_local" if extreme_macro else "standard_full_profile",
            "final_prompt": final_prompt,
        }

        return (
            final_prompt if krea else "",
            final_prompt if qwen else "",
            shot_section,
            presentation,
            marks_output,
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
            crop_authority,
            visible_outfit,
            resolution_debug,
            json.dumps(sections, indent=2, ensure_ascii=False),
            character_section,
            scene,
        )


class QwenDatasetQueueV230(QwenDatasetQueue):
    CATEGORY = "character creation/dataset"
    FUNCTION = "build_queue"
    DESCRIPTION = (
        "Current Qwen dataset queue. Uses the V2.3 primary-character blueprint, independent anatomy configuration, "
        "and mark-safe prompts without naming absent tattoos or piercings."
    )

    def build_queue(self, character_blueprint, dataset_plan, starting_seed, variations_per_shot, images_per_group, output_root, reference_label, prompt_suffix="", complete_outfit_override=""):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        face = profile.get("face_identity", "the primary character")
        marks = profile.get("marks_prompt", "")
        tattoo_lock = profile.get("tattoo_count_lock", "") if profile.get("tattoo_status") != "None" else ""
        piercing_lock = profile.get("piercing_count_lock", "") if profile.get("piercing_status") != "None" else ""
        anatomy_lock = profile.get("anatomy_integrity_lock", "")
        upper = profile.get("clothed_upper_body", profile.get("upper_body_identity", ""))
        lower = profile.get("clothed_lower_body", profile.get("lower_body_identity", ""))
        anatomy_upper = profile.get("anatomy_upper_body", profile.get("upper_body_identity", ""))
        anatomy_lower = profile.get("anatomy_lower_body", profile.get("lower_body_identity", ""))
        outfit = complete_outfit_override.strip() or profile.get("default_clothing_prompt", "complete simple fitted clothing")
        character_id = profile.get("character_id", "character")
        specs = _dataset_specs(dataset_plan, images_per_group)

        if marks:
            mark_instruction = "preserve every defined permanent mark at its exact location, scale, orientation, color, and jewelry type"
        else:
            mark_instruction = "keep naturally unmarked skin and remove any unlisted attached body jewelry"

        prompts=[]; seeds=[]; ids=[]; cats=[]; prefixes=[]; widths=[]; heights=[]; progress=[]; manifest=[]
        idx=0
        for spec in specs:
            for variation in range(variations_per_shot):
                cat=spec["category"]
                clinical = cat in {"anatomy", "anatomy_focus"}
                if clinical:
                    wardrobe = "unclothed neutral non-aroused clinical anatomy documentation"
                    body = _join(anatomy_upper, anatomy_lower)
                    style = "even clinical lighting, plain background, realistic skin texture"
                else:
                    if cat in {"extreme_closeup", "closeup"}:
                        wardrobe = f"preserve only the same visible upper-garment edge from {reference_label}"
                    else:
                        wardrobe = outfit
                    include_lower = cat in {"full_body", "action", "body_confirmation", "clothed_action"}
                    body = _join(upper if cat not in {"extreme_closeup", "closeup"} else "", lower if include_lower else "")
                    style = "ordinary realistic consumer-camera photography, natural skin texture, believable eyes and hair, rectilinear perspective"

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
                    focus = focus_map.get(spec["shot_id"], spec["description"])
                    macro_plan = {
                        "focus_mode": "Extreme Close-Up",
                        "focus_region": focus,
                        "shot_type": "Extreme Close-Up — Single Detail",
                        "lens": "105mm Macro",
                        "environment_prompt": "plain clinical documentation background with flat even lighting and minimal shadow obstruction",
                    }
                    macro = _extreme_macro_sections_v231(profile, macro_plan)
                    prompt = _sentences(
                        f"Edit {reference_label} into one tightly cropped macro documentation image of the same primary character",
                        f"replace the original image with one view of {focus.lower()} only",
                        macro["crop"],
                        macro["camera"],
                        macro["eye_state"],
                        macro["identity"],
                        macro["local_marks"],
                        macro["integrity"],
                        macro["environment"],
                        macro["exclusion"],
                        "do not preserve or reproduce unrelated body regions from the reference image",
                        prompt_suffix,
                    )
                else:
                    prompt = _sentences(
                        f"Edit {reference_label} into a new realistic photograph of the same primary character",
                        f"preserve the exact recognizable identity and hairline from {reference_label}",
                        spec["description"],
                        wardrobe,
                        face,
                        body,
                        marks,
                        tattoo_lock,
                        piercing_lock,
                        anatomy_lock,
                        mark_instruction,
                        style,
                        prompt_suffix,
                    )
                seed=int(starting_seed)+idx
                sid=f"{spec['shot_id']}_v{variation+1:02d}"
                prefix=f"{output_root}/{cat}/{idx+1:04d}_{sid}"
                if cat=="extreme_closeup": w,h=(1024,1024)
                elif cat in {"closeup","midshot","anatomy_focus"}: w,h=(1024,1280)
                else: w,h=(1024,1536)
                item={"index":idx+1,"shot_id":sid,"category":cat,"seed":seed,"filename_prefix":prefix,"width":w,"height":h,"prompt":prompt}
                prompts.append(prompt);seeds.append(seed);ids.append(sid);cats.append(cat);prefixes.append(prefix);widths.append(w);heights.append(h);manifest.append(item)
                idx+=1
        total=len(manifest)
        progress=[f"{x['index']} of {total} | {x['category']} | {x['shot_id']}" for x in manifest]
        plan_json=json.dumps({"schema":"FCC_QWEN_DATASET_PLAN_V231","schema_version":4,"character_id":character_id,"plan":dataset_plan,"images_per_group":images_per_group,"variations_per_shot":variations_per_shot,"total_images":total,"items":manifest},indent=2,ensure_ascii=False)
        return prompts,seeds,ids,cats,prefixes,widths,heights,[plan_json for _ in prompts],progress


__all__ = [
    "QwenDatasetQueueV230",
    "FCCDatasetDirector",
    "FCCQueueItemRouter",
    "CharacterBlueprintCreatorV230",
    "CharacterShotControlV230",
    "CharacterPromptAssemblerV230",
]
