from __future__ import annotations

import hashlib
import json
import re
from typing import Any


def _join(*parts: str) -> str:
    return ", ".join(str(p).strip(" ,") for p in parts if p and str(p).strip(" ,"))


def _slug(text: str) -> str:
    value = str(text).lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


GENDERS = ["Adult Female", "Adult Male", "Adult Nonbinary"]
FACIAL_HAIR = ["None", "Clean-Shaven", "Light Stubble", "Short Beard", "Full Beard", "Mustache", "Goatee", "Custom"]
FACIAL_HAIR_PROMPTS = {
    "Clean-Shaven": "clean-shaven face",
    "Light Stubble": "light even facial stubble across the moustache area, cheeks, jawline, and chin",
    "Short Beard": "short connected beard covering the sideburns, cheeks, jawline, chin, and moustache area",
    "Full Beard": "thick dense full beard with high broad continuous coverage across both cheeks, fully connected sideburns, moustache, jawline, chin, and beneath the lower lip, substantial natural cheek volume and beard depth, thick connected moustache and beard, not a narrow chin strap or jaw strap",
    "Mustache": "full moustache clearly covering the upper-lip area",
    "Goatee": "connected goatee covering the chin and moustache area",
}
MALE_CHEST = ["Average Male Chest", "Slim Male Chest", "Athletic Defined Chest", "Broad Muscular Chest", "Heavyset Male Chest", "Custom"]
MALE_GENITAL_SIZES = ["Unspecified", "Very Small", "Small", "Average", "Above Average", "Very Large"]
MALE_GENITAL_SIZE_PROMPTS = {
    "Very Small": "neutral non-aroused adult male external genital anatomy with very small proportional size",
    "Small": "neutral non-aroused adult male external genital anatomy with small proportional size",
    "Average": "neutral non-aroused adult male external genital anatomy with average proportional size",
    "Above Average": "neutral non-aroused adult male external genital anatomy with above-average proportional size",
    "Very Large": "neutral non-aroused adult male external genital anatomy with very large proportional size",
}
AGE_RANGES = ["18–24", "25–34", "35–44", "45–54", "55–64", "65+"]
HERITAGES = [
    "Unspecified",
    "Latin American / Hispanic",
    "Afro-Latino",
    "Caribbean",
    "White / European (Caucasian)",
    "Mediterranean / Southern European",
    "Black / African Descent",
    "Mixed Black / Multiracial",
    "East Asian",
    "Japanese",
    "Chinese",
    "Korean",
    "South Asian",
    "Southeast Asian",
    "Middle Eastern / North African",
    "Indigenous / Native American",
    "Pacific Islander",
    "Mixed Heritage",
    "Custom",
]
SKIN_TONES = [
    "Very Light", "Light", "Light-Medium", "Medium", "Olive", "Deep Tan",
    "Brown", "Deep Brown", "Very Deep", "Custom / Unspecified",
]
COMPLEXIONS = [
    "Natural Skin Texture", "Clear and Even", "Freckled", "Lightly Freckled",
    "Visible Pores", "Sun-Kissed", "Mature Natural Skin", "Unspecified",
]
FACE_SHAPES = ["Oval", "Round", "Heart-Shaped", "Soft Angular", "Square", "Long", "Diamond", "Unspecified"]
JAW_SHAPES = ["Delicate", "Soft", "Defined", "Strong", "Wide", "Tapered", "Unspecified"]
CHIN_SHAPES = ["Rounded", "Pointed", "Square", "Soft", "Prominent", "Unspecified"]
EYE_COLORS = ["Brown", "Dark Brown", "Hazel", "Green", "Blue", "Gray", "Amber", "Custom / Unspecified"]
EYE_SHAPES = ["Almond", "Round", "Prominent", "Deep-Set", "Hooded", "Upturned", "Downturned", "Unspecified"]
EYEBROWS = ["Soft Arch", "High Arch", "Straight", "Thick Natural", "Thin Natural", "Angular", "Unspecified"]
NOSES = ["Straight", "Narrow", "Button", "Wide", "Aquiline", "Rounded", "Upturned", "Unspecified"]
LIPS = ["Thin", "Balanced Medium", "Full", "Soft Cupid's Bow", "Wide", "Narrow", "Unspecified"]
HAIR_COLORS = ["Black", "Dark Brown", "Medium Brown", "Light Brown", "Strawberry Blonde", "Blonde", "Platinum", "Red", "Gray", "Silver", "Custom"]
HAIR_LENGTHS = ["Buzzed", "Very Short", "Chin-Length", "Shoulder-Length", "Mid-Back", "Waist-Length", "Custom"]
HAIR_TEXTURES = ["Pin-Straight", "Straight", "Slightly Wavy", "Wavy", "Curly", "Coily", "Custom"]
HAIR_STYLES = ["Loose Natural", "Center Part", "Side Part", "Braids", "Ponytail", "Bun", "Pixie", "Locs", "Afro", "Custom"]
HEIGHTS = ["Short", "Below Average", "Average", "Above Average", "Tall", "Very Tall", "Unspecified"]
BODY_TYPES = ["Very Slim", "Slim", "Average", "Athletic", "Curvy", "Full-Figured", "Muscular", "Heavyset", "Custom / Unspecified"]
BUST_SIZES = [
    "Unspecified", "Very Small", "Small", "Small-Medium", "Medium",
    "Medium-Full", "Full", "Large", "Very Large", "Overly Large",
]
BUST_SIZE_PROMPTS = {
    "Very Small": "very small bust with minimal projection and subtle chest volume",
    "Small": "small bust with gentle natural projection",
    "Small-Medium": "small-to-medium bust with modest natural projection",
    "Medium": "medium bust with balanced natural projection",
    "Medium-Full": "medium-full bust with noticeable but balanced projection",
    "Full": "full bust with pronounced natural volume and projection",
    "Large": "large bust with substantial natural volume and projection",
    "Very Large": "very large bust with heavy natural volume and strong projection",
    "Overly Large": "extremely large bust with exaggerated volume, very strong projection, and substantial natural weight",
}
BUST_SHAPES = ["Unspecified", "Bell Shape", "Teardrop", "Round", "Asymmetrical Natural", "East-West", "Side-Set", "Slender"]
BUST_SHAPE_PROMPTS = {
    "Bell Shape": "bell-shaped bust with a narrower upper pole and fuller rounded lower pole",
    "Teardrop": "teardrop-shaped bust with a gentle upper slope and natural lower fullness",
    "Round": "round bust with balanced upper-pole and lower-pole fullness",
    "Asymmetrical Natural": "naturally asymmetrical bust with subtle realistic left-right variation",
    "East-West": "east-west bust orientation with projection angled slightly outward",
    "Side-Set": "side-set bust with a wider natural center gap and fuller outer chest",
    "Slender": "slender elongated bust shape with a narrow base and gentle vertical contour",
}
BUST_POSITIONS = ["Unspecified", "Natural Average-Set", "High-Set / Perky", "High and Tight", "Low-Set", "Downward-Sloping", "Pendulous Natural"]
BUST_POSITION_PROMPTS = {
    "Natural Average-Set": "natural average-set chest position",
    "High-Set / Perky": "high-set perky chest position with a natural upward presentation",
    "High and Tight": "high and tight chest position with compact attachment and minimal lower drop",
    "Low-Set": "low-set chest position with realistic gravitational weight",
    "Downward-Sloping": "natural downward-sloping chest position with visible lower-pole weight",
    "Pendulous Natural": "naturally pendulous chest position with lower-set fullness and realistic gravitational drop",
}
BUST_FIRMNESS = ["Unspecified", "Firm", "Naturally Firm", "Balanced Natural", "Soft", "Very Soft / Natural Movement"]
BUST_FIRMNESS_PROMPTS = {
    "Firm": "firm chest tissue with limited natural movement",
    "Naturally Firm": "naturally firm chest tissue with stable shape and slight realistic movement",
    "Balanced Natural": "balanced natural chest tissue with moderate softness and realistic weight",
    "Soft": "soft natural chest tissue with gentle shape variation and realistic gravity",
    "Very Soft / Natural Movement": "very soft natural chest tissue with pronounced settling, weight, and realistic movement",
}
BUST_AUGMENTATION = ["Unspecified", "Natural / Unaugmented", "Subtle Natural-Looking Augmentation", "Round High-Profile Implants", "Teardrop / Anatomical Implants", "Very Firm Augmented Projection"]
BUST_AUGMENTATION_PROMPTS = {
    "Natural / Unaugmented": "natural unaugmented chest structure",
    "Subtle Natural-Looking Augmentation": "subtle natural-looking augmentation with moderate projection and preserved natural slope",
    "Round High-Profile Implants": "round high-profile implants with increased upper-pole fullness and forward projection",
    "Teardrop / Anatomical Implants": "anatomical teardrop implants with a sloped upper pole and fuller lower pole",
    "Very Firm Augmented Projection": "very firm augmented projection with high upper-pole fullness and minimal natural drop",
}
BUTTOCKS = ["Unspecified", "Small", "Average", "Rounded", "Full", "Wide", "Athletic", "Prominent"]
DEFAULT_CLOTHING = [
    "Simple Fitted T-Shirt", "Opaque Fitted Tank Top", "Casual Jeans and T-Shirt",
    "Fitted Athletic Outfit", "Simple Dress", "Business Casual", "Swimwear",
    "Clinical Unclothed Documentation", "Custom",
]
JEWELRY_LEVELS = ["None", "Minimal", "Everyday", "Statement", "Custom"]
MARK_STATUSES = ["None", "One", "Multiple"]

SHOT_TYPES = ["Face Close-Up", "Head and Shoulders", "Chest-Up", "Waist-Up Midshot", "Three-Quarter Body", "Full Body", "Body Close-Up"]
SHOT_PROMPTS = {
    "Face Close-Up": "close-up face portrait framed from slightly above the complete head to the upper shoulders, face occupying most of the image",
    "Head and Shoulders": "head-and-shoulders portrait with full head, hair, neck, shoulders, and upper chest visible",
    "Chest-Up": "true chest-up portrait with the camera pulled back, frame beginning slightly above the complete head and ending below the bust line, full neck, both shoulders, complete upper chest, both upper arms, and the full visible bust area inside the image",
    "Waist-Up Midshot": "true waist-up midshot framed from slightly above the complete head to the navel or lower mid-abdomen, full head, both shoulders, arms, torso, natural waist, and mid-abdomen visible",
    "Three-Quarter Body": "three-quarter-body photograph framed from slightly above the complete head to below the knees, arms and legs clearly visible",
    "Full Body": "full-body photograph with the entire subject visible from head to feet and balanced space around the body",
    "Body Close-Up": "focused body-documentation close-up of the selected region with that region fully visible and centered",
}
CAMERA_VIEWS = ["Front View", "Three-Quarter Left", "Three-Quarter Right", "Left Profile", "Right Profile", "Rear Three-Quarter Left", "Rear Three-Quarter Right", "Back View"]
CAMERA_PROMPTS = {
    "Front View": "front-facing camera view, camera centered",
    "Three-Quarter Left": "three-quarter-left camera view, body and face turned approximately 45 degrees left",
    "Three-Quarter Right": "three-quarter-right camera view, body and face turned approximately 45 degrees right",
    "Left Profile": "true left-profile camera view",
    "Right Profile": "true right-profile camera view",
    "Rear Three-Quarter Left": "rear three-quarter-left camera view",
    "Rear Three-Quarter Right": "rear three-quarter-right camera view",
    "Back View": "direct back-facing camera view",
}
POSES = ["Neutral Standing", "Relaxed Standing", "Seated", "Leaning", "Walking", "Arms Relaxed", "Arms Loosely Crossed", "One Hand at Waist", "Custom"]
EXPRESSIONS = [
    "Neutral", "Natural Closed-Mouth Smile", "Genuine Smile", "Big Smile", "Laughing",
    "Serious", "Focused", "Thoughtful", "Concerned", "Surprised", "Shy", "Nervous",
    "Confident", "Determined", "Angry", "Fearful", "Disgusted", "Pain / Strain",
    "Playful", "Cheeky", "Pout", "Wink", "Tongue Slightly Out", "Ahegao (Stylized Adult)",
    "Custom",
]
EXPRESSION_PROMPTS = {
    "Ahegao (Stylized Adult)": "exaggerated stylized adult ahegao expression with crossed or upward-rolled eyes, open mouth, and tongue visible; intentionally non-natural facial acting",
    "Pain / Strain": "controlled visible strain or pain expression while preserving recognizable facial structure",
    "Tongue Slightly Out": "playful expression with the tongue only slightly visible",
}
BODY_REGIONS = ["Upper Torso", "Chest and Ribcage", "Abdomen and Waist", "Upper Back and Shoulders", "Lower Back and Waist", "Hips Front", "Hips Rear", "Left Side Torso", "Right Side Torso", "Custom"]
STAGES = ["Krea Identity Anchor", "Qwen Face Documentation", "Qwen Upper-Body Anchor", "Qwen Anatomy Documentation", "Qwen Clothing Edit", "Qwen Body Close-Up", "Krea Mini-LoRA Expansion"]
CLOTHING_MODES = ["Profile Default", "Exact Outfit Override", "Clinical Unclothed", "Preserve Reference Clothing"]
BODY_DETAIL_MODES = ["Auto by Stage", "Clothed Silhouette", "Clinical Anatomy"]
OUTFIT_COVERAGE = ["Auto by Shot", "Complete Outfit", "Upper-Body Garment", "Lower-Body Garment", "One-Piece Garment", "Swimwear Set"]
CLOTHING_PRIORITIES = ["Standard", "Strong", "Maximum"]
BACKGROUNDS = ["Plain Neutral", "Simple Indoor", "Simple Outdoor", "Clinical Neutral", "Natural Home", "Gym", "Custom"]
LIGHTING = ["Soft Natural Daylight", "Even Window Light", "Clinical Even Light", "Warm Indoor Light", "Overcast Outdoor Light", "Custom"]
PHOTO_STYLES = ["Authentic Consumer Camera", "Personal Cellphone Photo", "Identity Documentation", "Clinical Documentation", "Standard Camera Photo"]


PRESET_OUTFITS: dict[str, dict[str, str]] = {
    "Simple Fitted T-Shirt": {
        "kind": "complete",
        "top": "simple fitted T-shirt",
        "bottom": "high-waisted fitted jeans",
        "footwear": "casual low-profile shoes",
    },
    "Opaque Fitted Tank Top": {
        "kind": "complete",
        "top": "opaque fitted tank top",
        "bottom": "high-waisted fitted jeans",
        "footwear": "casual low-profile shoes",
    },
    "Casual Jeans and T-Shirt": {
        "kind": "complete",
        "top": "casual fitted T-shirt",
        "bottom": "well-fitted jeans",
        "footwear": "casual sneakers",
    },
    "Fitted Athletic Outfit": {
        "kind": "complete",
        "top": "fitted opaque athletic top",
        "bottom": "high-waisted athletic leggings",
        "footwear": "training shoes",
    },
    "Simple Dress": {
        "kind": "one_piece",
        "one_piece": "simple fitted knee-length dress",
        "footwear": "simple low-profile shoes",
    },
    "Business Casual": {
        "kind": "complete",
        "top": "fitted business-casual blouse",
        "bottom": "tailored trousers",
        "footwear": "simple flats",
    },
    "Swimwear": {
        "kind": "swimwear",
        "swimwear_top": "matching fitted swimwear top",
        "swimwear_bottom": "matching fitted swimwear bottoms",
    },
    "Clinical Unclothed Documentation": {"kind": "clinical"},
    "Custom": {"kind": "custom"},
}


def _heritage_prompt(heritage: str, custom: str) -> str:
    if heritage == "Unspecified":
        return ""
    if heritage == "Custom":
        return custom.strip()
    label = heritage.lower()
    return label if label.endswith("heritage") else f"{label} heritage"


def _hair_value(value: str, custom: str, label: str) -> str:
    if value == "Custom":
        custom_value = custom.strip()
        return f"{custom_value} {label}" if custom_value else ""
    return f"{value.lower()} {label}" if value else ""


def _facial_hair_prompt(gender: str, facial_hair: str, custom: str) -> str:
    if gender != "Adult Male" or facial_hair == "None":
        return ""
    if facial_hair == "Custom":
        return custom.strip()
    return FACIAL_HAIR_PROMPTS.get(facial_hair, facial_hair.lower())


def _bust_prompt(gender: str, size: str, shape: str, position: str, firmness: str, augmentation: str) -> str:
    if gender != "Adult Female":
        return ""
    return _join(
        BUST_SIZE_PROMPTS.get(size, ""),
        BUST_SHAPE_PROMPTS.get(shape, ""),
        BUST_POSITION_PROMPTS.get(position, ""),
        BUST_FIRMNESS_PROMPTS.get(firmness, ""),
        BUST_AUGMENTATION_PROMPTS.get(augmentation, ""),
    )


def _clothed_bust_prompt(gender: str, size: str, shape: str, position: str) -> str:
    if gender != "Adult Female":
        return ""
    size_text = BUST_SIZE_PROMPTS.get(size, "")
    shape_text = BUST_SHAPE_PROMPTS.get(shape, "")
    position_text = BUST_POSITION_PROMPTS.get(position, "")
    if size_text:
        size_text = size_text.replace("bust with", "bust shaping the garment with")
    return _join(size_text, shape_text, position_text)


def _split_lines(text: str) -> list[str]:
    values = []
    for block in re.split(r"[\r\n;]+", text or ""):
        cleaned = re.sub(r"^\s*(?:[-*•]+|\d+[.)])\s*", "", block).strip(" ,.;")
        if cleaned:
            values.append(cleaned)
    return values


def _marks_prompt(kind: str, status: str, description: str) -> tuple[str, list[str], str]:
    if status == "None":
        return "", [], ""
    entries = _split_lines(description)
    warnings = []
    if not entries:
        warnings.append(f"{kind} status is enabled but no descriptor was provided.")
    if status == "One" and len(entries) > 1:
        warnings.append(f"One {kind.lower()} is selected but multiple lines were supplied.")
    if status == "Multiple" and len(entries) < 2:
        warnings.append(f"Multiple {kind.lower()}s are selected but fewer than two lines were supplied.")
    if not entries:
        return "", [], " ".join(warnings)
    if len(entries) == 1:
        prompt = f"one permanent identity {kind.lower()} with exact placement: {entries[0]}"
    else:
        numbered = "; ".join(f"{kind.lower()} {i}: {entry}" for i, entry in enumerate(entries, 1))
        prompt = f"{len(entries)} separate permanent identity {kind.lower()}s with exact placements: {numbered}"
    return prompt, entries, " ".join(warnings)


def _structured_piercing_prompt(location: str, piercing_type: str, material: str, visibility: str, custom: str) -> str:
    location = (location or "").strip()
    piercing_type = (piercing_type or "").strip()
    material = (material or "").strip()
    visibility = (visibility or "").strip()
    custom = (custom or "").strip()
    if not any((location, piercing_type, material, custom)):
        return ""
    if location.lower() in {"septum", "nasal septum", "center septum"}:
        placement = "centered through the nasal septum in the middle area directly below the nose, not through either nostril and not on the upper lip"
    else:
        placement = f"at the exact {location}" if location else "at the specified facial location"
    item = custom or " ".join(x for x in (material, piercing_type) if x) or "piercing jewelry"
    visibility_text = f"{visibility.lower()} visibility" if visibility else "clearly visible"
    return f"one permanent identity piercing: {item}, positioned {placement}, {visibility_text}"


def _infer_outfit_kind(text: str) -> str:
    lowered = (text or "").lower()
    if any(token in lowered for token in ("bikini", "swimwear", "swimsuit", "two-piece", "two piece")):
        return "swimwear"
    if any(token in lowered for token in ("dress", "bodysuit", "romper", "jumpsuit", "one-piece", "one piece")):
        return "one_piece"
    return "complete"


def _build_profile_outfit(
    default_clothing: str,
    exact_default_clothing: str,
    default_top: str,
    default_bottom: str,
    default_footwear: str,
    default_outerwear: str,
    default_one_piece: str,
    default_swimwear_top: str,
    default_swimwear_bottom: str,
    outfit_notes: str,
) -> tuple[str, dict[str, str]]:
    preset = dict(PRESET_OUTFITS.get(default_clothing, {"kind": "custom"}))

    components = {
        "kind": preset.get("kind", "custom"),
        "top": default_top.strip() or preset.get("top", ""),
        "bottom": default_bottom.strip() or preset.get("bottom", ""),
        "footwear": default_footwear.strip() or preset.get("footwear", ""),
        "outerwear": default_outerwear.strip() or preset.get("outerwear", ""),
        "one_piece": default_one_piece.strip() or preset.get("one_piece", ""),
        "swimwear_top": default_swimwear_top.strip() or preset.get("swimwear_top", ""),
        "swimwear_bottom": default_swimwear_bottom.strip() or preset.get("swimwear_bottom", ""),
        "raw": exact_default_clothing.strip(),
        "notes": outfit_notes.strip(),
    }

    if components["raw"]:
        components["kind"] = _infer_outfit_kind(components["raw"])

    kind = components["kind"]
    if kind == "clinical":
        return "unclothed adult subject in neutral clinical anatomy documentation", components

    if components["raw"]:
        if kind == "swimwear":
            prompt = _join(
                f"fully wearing a matching two-piece swimwear set described as {components['raw']}",
                "a fitted swimwear top and matching swimwear bottoms are both present",
                "realistic fabric edges, straps, seams, and tension",
                components["notes"],
            )
        elif kind == "one_piece":
            prompt = _join(
                f"fully wearing the one-piece garment described as {components['raw']}",
                components["footwear"] and f"with {components['footwear']}",
                components["notes"],
            )
        else:
            prompt = _join(
                f"fully dressed in the complete outfit described as {components['raw']}",
                components["notes"],
            )
        return prompt, components

    if kind == "swimwear":
        prompt = _join(
            "fully wearing a matching two-piece swimwear set",
            components["swimwear_top"],
            components["swimwear_bottom"],
            "realistic fabric edges, straps, seams, and tension",
            components["notes"],
        )
    elif kind == "one_piece":
        prompt = _join(
            "fully wearing a complete one-piece outfit",
            components["one_piece"],
            components["outerwear"],
            components["footwear"],
            components["notes"],
        )
    elif kind == "complete":
        prompt = _join(
            "fully dressed in a complete outfit consisting of",
            components["top"],
            components["bottom"],
            components["outerwear"],
            components["footwear"],
            components["notes"],
        )
    else:
        prompt = components["notes"]
    return prompt, components


def _override_components(
    exact_outfit: str,
    exact_top: str,
    exact_bottom: str,
    exact_footwear: str,
    exact_outerwear: str,
    outfit_coverage: str,
) -> dict[str, str]:
    raw = exact_outfit.strip()
    inferred_kind = _infer_outfit_kind(raw)
    if outfit_coverage == "Swimwear Set":
        kind = "swimwear"
    elif outfit_coverage == "One-Piece Garment":
        kind = "one_piece"
    elif outfit_coverage in {"Upper-Body Garment", "Lower-Body Garment", "Complete Outfit"}:
        kind = "complete"
    else:
        kind = inferred_kind

    return {
        "kind": kind,
        "top": exact_top.strip(),
        "bottom": exact_bottom.strip(),
        "footwear": exact_footwear.strip(),
        "outerwear": exact_outerwear.strip(),
        "one_piece": raw if kind == "one_piece" else "",
        "swimwear_top": exact_top.strip(),
        "swimwear_bottom": exact_bottom.strip(),
        "raw": raw,
        "notes": "",
    }


def _component_phrase(components: dict[str, str]) -> str:
    kind = components.get("kind", "complete")
    raw = components.get("raw", "")
    if raw:
        if kind == "swimwear":
            return _join(
                f"fully wearing a matching two-piece swimwear set described as {raw}",
                components.get("top") or "a fitted swimwear top",
                components.get("bottom") or "matching swimwear bottoms",
                "realistic fabric edges, straps, seams, and tension",
            )
        if kind == "one_piece":
            return _join(f"fully wearing the one-piece garment described as {raw}", components.get("footwear"))
        return _join(f"fully dressed in the complete outfit described as {raw}", components.get("top"), components.get("bottom"), components.get("outerwear"), components.get("footwear"))

    if kind == "swimwear":
        return _join(
            "fully wearing a matching two-piece swimwear set",
            components.get("swimwear_top") or components.get("top") or "fitted swimwear top",
            components.get("swimwear_bottom") or components.get("bottom") or "matching swimwear bottoms",
            "realistic fabric edges, straps, seams, and tension",
        )
    if kind == "one_piece":
        return _join("fully wearing a complete one-piece outfit", components.get("one_piece"), components.get("outerwear"), components.get("footwear"))
    return _join(
        "fully dressed in a complete outfit consisting of",
        components.get("top"), components.get("bottom"), components.get("outerwear"), components.get("footwear"),
    )


def _crop_outfit_prompt(
    base_prompt: str,
    components: dict[str, str],
    shot_type: str,
    body_region: str,
    priority: str,
) -> tuple[str, str]:
    if not base_prompt:
        return "", ""

    kind = components.get("kind", "complete")
    top = components.get("top") or components.get("swimwear_top") or (components.get("raw") if kind != "one_piece" else "")
    bottom = components.get("bottom") or components.get("swimwear_bottom")
    footwear = components.get("footwear")
    one_piece = components.get("one_piece") or (components.get("raw") if kind == "one_piece" else "")

    if shot_type == "Face Close-Up":
        if kind == "swimwear":
            crop = "the swimwear-top straps and neckline are clearly visible at the lower edge of the portrait"
        elif kind == "one_piece":
            crop = f"the neckline and shoulder area of {one_piece or 'the one-piece garment'} are clearly visible at the lower edge of the portrait"
        else:
            crop = f"the neckline and upper shoulder area of {top or 'the selected upper-body garment'} are clearly visible at the lower edge of the portrait"
    elif shot_type == "Head and Shoulders":
        if kind == "swimwear":
            crop = "the swimwear top neckline and both straps are clearly visible across the shoulders and upper chest"
        elif kind == "one_piece":
            crop = f"the upper portion, neckline, and shoulders of {one_piece or 'the one-piece garment'} are clearly visible"
        else:
            crop = f"the upper portion, neckline, shoulders, and sleeves or straps of {top or 'the selected upper-body garment'} are clearly visible"
    elif shot_type == "Chest-Up":
        if kind == "swimwear":
            crop = "the complete swimwear top is clearly visible across the chest with both sides, straps, neckline, and fabric edges present"
        elif kind == "one_piece":
            crop = f"the complete upper portion of {one_piece or 'the one-piece garment'} is clearly visible across the chest and upper torso"
        else:
            crop = f"the complete {top or 'upper-body garment'} is clearly visible across the chest and upper torso with neckline, seams, sleeves or straps, and fabric edges present"
    elif shot_type == "Waist-Up Midshot":
        if kind == "swimwear":
            crop = "the complete swimwear top and the upper edge of the matching swimwear bottoms are clearly visible"
        elif kind == "one_piece":
            crop = f"the upper and waist portions of {one_piece or 'the one-piece garment'} are clearly visible"
        else:
            crop = _join(
                f"the complete {top or 'upper-body garment'} is visible",
                f"the waistband or upper edge of {bottom or 'the matching lower-body garment'} is visible at the waist",
            )
    elif shot_type == "Three-Quarter Body":
        if kind == "swimwear":
            crop = "the complete matching swimwear top and swimwear bottoms are both clearly visible in the frame"
        elif kind == "one_piece":
            crop = f"the complete {one_piece or 'one-piece garment'} is clearly visible from shoulders through below the knees"
        else:
            crop = _join(
                f"the complete {top or 'upper-body garment'} and {bottom or 'lower-body garment'} are clearly visible",
                "the outfit remains continuous through the waist, hips, and legs",
            )
    elif shot_type == "Full Body":
        if kind == "swimwear":
            crop = "the complete matching swimwear top and swimwear bottoms are both clearly visible from head to feet"
        elif kind == "one_piece":
            crop = _join(
                f"the complete {one_piece or 'one-piece garment'} is clearly visible from head to feet",
                footwear and f"the {footwear} are visible",
            )
        else:
            crop = _join(
                f"the complete {top or 'upper-body garment'} and {bottom or 'lower-body garment'} are clearly visible",
                footwear and f"the {footwear} are visible",
                "the full outfit remains continuous from shoulders through the feet",
            )
    else:
        region = body_region.lower()
        if any(token in region for token in ("upper", "chest", "ribcage", "shoulder")):
            crop = f"the selected upper-body garment is clearly visible across the documented {region} region"
        elif any(token in region for token in ("abdomen", "waist", "hip", "lower")):
            crop = f"the waistband and lower-body garment are clearly visible across the documented {region} region"
        else:
            crop = "the requested garment remains clearly visible across the selected body-documentation region"

    final_lock = ""
    if priority in {"Strong", "Maximum"}:
        final_lock = "garment visibility confirmation: the requested outfit remains clearly visible in the selected crop"
    if priority == "Maximum":
        final_lock = _join(final_lock, "the selected clothing is the dominant wardrobe state in this image")
    return _join(base_prompt, crop), final_lock


def _resolve_body_mode(stage: str, clothing_mode: str, body_detail_mode: str) -> str:
    if clothing_mode == "Clinical Unclothed":
        return "Clinical Anatomy"
    if clothing_mode in {"Exact Outfit Override", "Preserve Reference Clothing"}:
        return "Clothed Silhouette"
    if body_detail_mode != "Auto by Stage":
        return body_detail_mode
    if stage in {"Qwen Anatomy Documentation", "Qwen Body Close-Up"}:
        return "Clinical Anatomy"
    return "Clothed Silhouette"


class CharacterBlueprintCreator:
    CATEGORY = "character creation/core"
    FUNCTION = "build_blueprint"
    DESCRIPTION = "Creates a reusable adult character blueprint with separate clothed-silhouette, clinical-anatomy, markings, and structured outfit prompts."

    RETURN_TYPES = (
        "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING",
        "CHARACTER_BLUEPRINT", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING",
    )
    RETURN_NAMES = (
        "face_identity", "upper_body_identity", "lower_body_identity", "bust_prompt", "marks_prompt",
        "default_clothing_prompt", "full_profile_prompt", "character_id", "character_blueprint", "warnings",
        "clothed_upper_body", "anatomy_upper_body", "clothed_lower_body", "anatomy_lower_body",
        "structured_outfit_prompt", "character_blueprint_json",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "gender": (GENDERS, {"default": "Adult Female"}),
                "age_range": (AGE_RANGES, {"default": "25–34"}),
                "heritage": (HERITAGES, {"default": "Unspecified"}),
                "skin_tone": (SKIN_TONES, {"default": "Light"}),
                "complexion": (COMPLEXIONS, {"default": "Natural Skin Texture"}),
                "face_shape": (FACE_SHAPES, {"default": "Oval"}),
                "jaw_shape": (JAW_SHAPES, {"default": "Defined"}),
                "chin_shape": (CHIN_SHAPES, {"default": "Rounded"}),
                "eye_color": (EYE_COLORS, {"default": "Hazel"}),
                "eye_shape": (EYE_SHAPES, {"default": "Almond"}),
                "eyebrow_shape": (EYEBROWS, {"default": "Soft Arch"}),
                "nose_shape": (NOSES, {"default": "Straight"}),
                "lip_shape": (LIPS, {"default": "Balanced Medium"}),
                "hair_color": (HAIR_COLORS, {"default": "Medium Brown"}),
                "hair_length": (HAIR_LENGTHS, {"default": "Shoulder-Length"}),
                "hair_texture": (HAIR_TEXTURES, {"default": "Slightly Wavy"}),
                "hair_style": (HAIR_STYLES, {"default": "Loose Natural"}),
                "height": (HEIGHTS, {"default": "Average"}),
                "body_type": (BODY_TYPES, {"default": "Average"}),
                "bust_size": (BUST_SIZES, {"default": "Medium"}),
                "bust_shape": (BUST_SHAPES, {"default": "Teardrop"}),
                "bust_position": (BUST_POSITIONS, {"default": "Natural Average-Set"}),
                "bust_firmness": (BUST_FIRMNESS, {"default": "Balanced Natural"}),
                "bust_augmentation": (BUST_AUGMENTATION, {"default": "Natural / Unaugmented"}),
                "buttocks": (BUTTOCKS, {"default": "Average"}),
                "default_clothing": (DEFAULT_CLOTHING, {"default": "Simple Fitted T-Shirt"}),
                "jewelry_level": (JEWELRY_LEVELS, {"default": "Minimal"}),
                "tattoo_status": (MARK_STATUSES, {"default": "None"}),
                "piercing_status": (MARK_STATUSES, {"default": "None"}),
            },
            "optional": {
                "custom_heritage": ("STRING", {"default": "", "multiline": False}),
                "custom_hair_color": ("STRING", {"default": "", "multiline": False}),
                "custom_hair_length": ("STRING", {"default": "", "multiline": False}),
                "custom_hair_texture": ("STRING", {"default": "", "multiline": False}),
                "custom_hair_style": ("STRING", {"default": "", "multiline": False}),
                "exact_default_clothing": ("STRING", {"default": "", "multiline": True}),
                "jewelry_description": ("STRING", {"default": "", "multiline": True}),
                "tattoo_descriptors": ("STRING", {"default": "", "multiline": True, "placeholder": "One tattoo per line, including exact location"}),
                "piercing_descriptors": ("STRING", {"default": "", "multiline": True, "placeholder": "One piercing per line, including exact location and jewelry"}),
                "lower_body_notes": ("STRING", {"default": "", "multiline": True}),
                "custom_identity_notes": ("STRING", {"default": "", "multiline": True}),
                "default_top": ("STRING", {"default": "", "multiline": False, "placeholder": "Optional structured top override"}),
                "default_bottom": ("STRING", {"default": "", "multiline": False, "placeholder": "Optional structured bottom override"}),
                "default_footwear": ("STRING", {"default": "", "multiline": False, "placeholder": "Optional footwear override"}),
                "default_outerwear": ("STRING", {"default": "", "multiline": False, "placeholder": "Optional outerwear"}),
                "default_one_piece": ("STRING", {"default": "", "multiline": False, "placeholder": "Optional dress, bodysuit, romper, or jumpsuit"}),
                "default_swimwear_top": ("STRING", {"default": "", "multiline": False}),
                "default_swimwear_bottom": ("STRING", {"default": "", "multiline": False}),
                "outfit_notes": ("STRING", {"default": "", "multiline": True}),
                "piercing_location": (["", "Left Eyebrow", "Right Eyebrow", "Left Nostril", "Right Nostril", "Septum", "Bridge", "Left Lip", "Right Lip", "Center Lip", "Other"], {"default": ""}),
                "piercing_type": (["", "Stud", "Hoop", "Curved Barbell", "Circular Barbell", "Horseshoe", "Clicker", "Seam Ring", "Decorative Ring", "Custom"], {"default": ""}),
                "piercing_material": (["", "Black Titanium", "Silver Titanium", "Gold", "Rose Gold", "Steel", "Custom"], {"default": ""}),
                "piercing_visibility": (["", "Subtle", "Normal", "Prominent", "Documentation"], {"default": "Normal"}),
                "structured_piercing_custom": ("STRING", {"default": "", "multiline": False}),
                "facial_hair": (FACIAL_HAIR, {"default": "None"}),
                "custom_facial_hair": ("STRING", {"default": "", "multiline": False}),
                "male_chest": (MALE_CHEST, {"default": "Average Male Chest"}),
                "custom_male_chest": ("STRING", {"default": "", "multiline": False}),
                "male_genital_size": (MALE_GENITAL_SIZES, {"default": "Unspecified"}),
            },
        }

    def build_blueprint(
        self, gender, age_range, heritage, skin_tone, complexion, face_shape, jaw_shape, chin_shape,
        eye_color, eye_shape, eyebrow_shape, nose_shape, lip_shape, hair_color, hair_length, hair_texture,
        hair_style, height, body_type, bust_size, bust_shape, bust_position, bust_firmness,
        bust_augmentation, buttocks, default_clothing, jewelry_level, tattoo_status, piercing_status,
        custom_heritage="", custom_hair_color="", custom_hair_length="", custom_hair_texture="",
        custom_hair_style="", exact_default_clothing="", jewelry_description="", tattoo_descriptors="",
        piercing_descriptors="", lower_body_notes="", custom_identity_notes="", default_top="",
        default_bottom="", default_footwear="", default_outerwear="", default_one_piece="",
        default_swimwear_top="", default_swimwear_bottom="", outfit_notes="",
        piercing_location="", piercing_type="", piercing_material="", piercing_visibility="Normal",
        structured_piercing_custom="", facial_hair="None", custom_facial_hair="",
        male_chest="Average Male Chest", custom_male_chest="", male_genital_size="Unspecified",
    ):
        heritage_prompt = _heritage_prompt(heritage, custom_heritage)
        face_identity = _join(
            "adult subject", gender.lower(), f"age range {age_range}", heritage_prompt,
            f"{skin_tone.lower()} skin tone" if skin_tone != "Custom / Unspecified" else "",
            complexion.lower() if complexion != "Unspecified" else "",
            f"{face_shape.lower()} face", f"{jaw_shape.lower()} jaw", f"{chin_shape.lower()} chin",
            f"{eye_color.lower()} eyes" if eye_color != "Custom / Unspecified" else "",
            f"{eye_shape.lower()} eye shape", f"{eyebrow_shape.lower()} eyebrows",
            f"{nose_shape.lower()} nose", f"{lip_shape.lower()} lips",
            _hair_value(hair_color, custom_hair_color, "hair"),
            _hair_value(hair_length, custom_hair_length, "hair length"),
            _hair_value(hair_texture, custom_hair_texture, "hair texture"),
            _hair_value(hair_style, custom_hair_style, "hairstyle"),
            _facial_hair_prompt(gender, facial_hair, custom_facial_hair),
            custom_identity_notes,
        )

        bust_prompt = _bust_prompt(gender, bust_size, bust_shape, bust_position, bust_firmness, bust_augmentation)
        clothed_bust = _clothed_bust_prompt(gender, bust_size, bust_shape, bust_position)

        base_body = _join(
            f"{height.lower()} height" if height != "Unspecified" else "",
            f"{body_type.lower()} body type" if body_type != "Custom / Unspecified" else "",
        )
        if gender == "Adult Male":
            male_chest_prompt = custom_male_chest.strip() if male_chest == "Custom" else male_chest.lower()
            anatomy_upper_body = _join(base_body, male_chest_prompt, "adult male torso and masculine chest anatomy")
            clothed_upper_body = _join(base_body, male_chest_prompt, "masculine shoulder, chest, and torso silhouette shaping the garment")
            male_genital_prompt = MALE_GENITAL_SIZE_PROMPTS.get(male_genital_size, "")
            anatomy_lower_body = _join(
                f"{buttocks.lower()} gluteal build" if buttocks != "Unspecified" else "",
                "adult male pelvis, waist, and leg anatomy",
                male_genital_prompt,
                lower_body_notes,
            )
            clothed_lower_body = _join(
                f"{buttocks.lower()} lower-body and gluteal silhouette" if buttocks != "Unspecified" else "",
                "masculine waist, hip, and leg proportions",
            )
        elif gender == "Adult Nonbinary":
            anatomy_upper_body = _join(base_body, "androgynous adult torso anatomy")
            clothed_upper_body = _join(base_body, "androgynous torso and shoulder silhouette shaping the garment")
            anatomy_lower_body = _join(f"{buttocks.lower()} gluteal build" if buttocks != "Unspecified" else "", "androgynous waist, hip, and leg anatomy", lower_body_notes)
            clothed_lower_body = _join(f"{buttocks.lower()} lower-body silhouette" if buttocks != "Unspecified" else "", "balanced androgynous waist, hip, and leg proportions")
        else:
            anatomy_upper_body = _join(base_body, bust_prompt)
            clothed_upper_body = _join(base_body, clothed_bust)
            anatomy_lower_body = _join(
                f"{buttocks.lower()} buttocks" if buttocks != "Unspecified" else "",
                lower_body_notes,
            )
            clothed_lower_body = _join(
                f"{buttocks.lower()} lower-body and gluteal silhouette" if buttocks != "Unspecified" else "",
                "balanced hip, waist, and leg proportions",
            )

        tattoo_prompt, tattoo_entries, tattoo_warning = _marks_prompt("Tattoo", tattoo_status, tattoo_descriptors)
        piercing_prompt, piercing_entries, piercing_warning = _marks_prompt("Piercing", piercing_status, piercing_descriptors)
        structured_piercing = _structured_piercing_prompt(
            piercing_location, piercing_type, piercing_material, piercing_visibility, structured_piercing_custom
        )
        if structured_piercing:
            piercing_prompt = structured_piercing
            piercing_entries = [structured_piercing]
            piercing_warning = ""
        marks_prompt = _join(tattoo_prompt, piercing_prompt)

        structured_outfit_prompt, outfit_components = _build_profile_outfit(
            default_clothing, exact_default_clothing, default_top, default_bottom,
            default_footwear, default_outerwear, default_one_piece,
            default_swimwear_top, default_swimwear_bottom, outfit_notes,
        )
        jewelry_prompt = "" if jewelry_level == "None" else _join(f"{jewelry_level.lower()} jewelry", jewelry_description)
        default_clothing_prompt = _join(structured_outfit_prompt, jewelry_prompt)

        upper_body_identity = anatomy_upper_body
        lower_body_identity = anatomy_lower_body
        full_profile_prompt = _join(face_identity, marks_prompt, anatomy_upper_body, anatomy_lower_body, default_clothing_prompt)
        base_id = _join(gender, age_range, heritage, face_shape, hair_color, body_type, bust_size)
        character_id = _slug(base_id) + "_" + hashlib.sha1(full_profile_prompt.encode("utf-8")).hexdigest()[:8]

        warnings = " ".join(x for x in [tattoo_warning, piercing_warning] if x)
        if gender == "Adult Male" and bust_prompt:
            warnings = _join(warnings, "Internal validation error: female bust prompt leaked into Adult Male branch.")
        if bust_position == "High and Tight" and bust_firmness in {"Soft", "Very Soft / Natural Movement"}:
            warnings = _join(warnings, "High and Tight conflicts with the selected soft-tissue setting.")
        if outfit_components.get("kind") == "complete" and not outfit_components.get("raw"):
            if not outfit_components.get("top") or not outfit_components.get("bottom"):
                warnings = _join(warnings, "Complete outfit is missing a top or bottom component.")

        blueprint = {
            "schema": "CHARACTER_BLUEPRINT",
            "schema_version": 3,
            "character_id": character_id,
            "gender": gender,
            "age_range": age_range,
            "heritage": heritage,
            "heritage_prompt": heritage_prompt,
            "facial_hair": facial_hair if gender == "Adult Male" else "Not applicable",
            "male_chest": male_chest if gender == "Adult Male" else "Not applicable",
            "male_genital_size": male_genital_size if gender == "Adult Male" else "Not applicable",
            "face_identity": face_identity,
            "upper_body_identity": anatomy_upper_body,
            "lower_body_identity": anatomy_lower_body,
            "anatomy_upper_body": anatomy_upper_body,
            "clothed_upper_body": clothed_upper_body,
            "anatomy_lower_body": anatomy_lower_body,
            "clothed_lower_body": clothed_lower_body,
            "bust_prompt": bust_prompt,
            "marks_prompt": marks_prompt,
            "tattoo_entries": tattoo_entries,
            "piercing_entries": piercing_entries,
            "structured_piercing_prompt": structured_piercing,
            "default_clothing_prompt": default_clothing_prompt,
            "structured_outfit_prompt": structured_outfit_prompt,
            "outfit_components": outfit_components,
            "jewelry_prompt": jewelry_prompt,
            "full_profile_prompt": full_profile_prompt,
            "warnings": warnings,
        }

        return (
            face_identity, anatomy_upper_body, anatomy_lower_body, bust_prompt, marks_prompt,
            default_clothing_prompt, full_profile_prompt, character_id, blueprint, warnings,
            clothed_upper_body, anatomy_upper_body, clothed_lower_body, anatomy_lower_body,
            structured_outfit_prompt, json.dumps(blueprint, indent=2, ensure_ascii=False, sort_keys=True),
        )


class CharacterShotPlanner:
    CATEGORY = "character creation/core"
    FUNCTION = "plan_shot"
    DESCRIPTION = "Builds stage-specific Krea and Qwen prompts with authoritative crop-aware clothing or clinical anatomy routing."

    RETURN_TYPES = (
        "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING",
        "INT", "INT", "STRING", "STRING", "STRING", "STRING", "STRING",
    )
    RETURN_NAMES = (
        "krea_prompt", "qwen_prompt", "shot_prompt", "clothing_prompt", "marks_prompt",
        "reference_required", "shot_id", "recommended_width", "recommended_height",
        "profile_character_id", "planner_notes", "effective_body_detail_mode",
        "outfit_visibility_lock", "outfit_components_prompt",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "stage": (STAGES, {"default": "Krea Identity Anchor"}),
                "shot_type": (SHOT_TYPES, {"default": "Face Close-Up"}),
                "camera_view": (CAMERA_VIEWS, {"default": "Front View"}),
                "pose": (POSES, {"default": "Neutral Standing"}),
                "expression": (EXPRESSIONS, {"default": "Neutral"}),
                "clothing_mode": (CLOTHING_MODES, {"default": "Profile Default"}),
                "body_region": (BODY_REGIONS, {"default": "Upper Torso"}),
                "background": (BACKGROUNDS, {"default": "Plain Neutral"}),
                "lighting": (LIGHTING, {"default": "Soft Natural Daylight"}),
                "photo_style": (PHOTO_STYLES, {"default": "Authentic Consumer Camera"}),
            },
            "optional": {
                "character_blueprint": ("CHARACTER_BLUEPRINT",),
                "exact_outfit": ("STRING", {"default": "", "multiline": True}),
                "custom_pose": ("STRING", {"default": "", "multiline": True}),
                "custom_expression": ("STRING", {"default": "", "multiline": False}),
                "custom_body_region": ("STRING", {"default": "", "multiline": True}),
                "custom_background": ("STRING", {"default": "", "multiline": True}),
                "custom_lighting": ("STRING", {"default": "", "multiline": True}),
                "trigger_word": ("STRING", {"default": "", "multiline": False}),
                "custom_suffix": ("STRING", {"default": "", "multiline": True}),
                "body_detail_mode": (BODY_DETAIL_MODES, {"default": "Auto by Stage"}),
                "outfit_coverage": (OUTFIT_COVERAGE, {"default": "Auto by Shot"}),
                "clothing_priority": (CLOTHING_PRIORITIES, {"default": "Strong"}),
                "exact_top": ("STRING", {"default": "", "multiline": False}),
                "exact_bottom": ("STRING", {"default": "", "multiline": False}),
                "exact_footwear": ("STRING", {"default": "", "multiline": False}),
                "exact_outerwear": ("STRING", {"default": "", "multiline": False}),
            },
        }

    def plan_shot(
        self, stage, shot_type, camera_view, pose, expression, clothing_mode, body_region,
        background, lighting, photo_style, character_blueprint=None, exact_outfit="",
        custom_pose="", custom_expression="", custom_body_region="", custom_background="",
        custom_lighting="", trigger_word="", custom_suffix="", body_detail_mode="Auto by Stage",
        outfit_coverage="Auto by Shot", clothing_priority="Strong", exact_top="",
        exact_bottom="", exact_footwear="", exact_outerwear="",
    ):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        face = profile.get("face_identity", "adult subject")
        marks = profile.get("marks_prompt", "")
        anatomy_upper = profile.get("anatomy_upper_body", profile.get("upper_body_identity", ""))
        clothed_upper = profile.get("clothed_upper_body", profile.get("upper_body_identity", ""))
        anatomy_lower = profile.get("anatomy_lower_body", profile.get("lower_body_identity", ""))
        clothed_lower = profile.get("clothed_lower_body", "")
        default_clothing = profile.get("default_clothing_prompt", "")
        default_components = profile.get("outfit_components", {}) if isinstance(profile.get("outfit_components"), dict) else {}
        character_id = profile.get("character_id", "character")

        effective_shot_type = shot_type
        shot_prompt = _join(SHOT_PROMPTS[effective_shot_type], CAMERA_PROMPTS[camera_view])
        region = custom_body_region.strip() if body_region == "Custom" and custom_body_region.strip() else body_region
        if shot_type == "Body Close-Up":
            shot_prompt = _join(shot_prompt, f"focused on {region.lower()}")

        anchor_lens_prompt = ""
        if stage == "Krea Identity Anchor":
            anchor_crop = "Face Close-Up" if shot_type == "Face Close-Up" else "Head and Shoulders"
            effective_shot_type = anchor_crop
            shot_prompt = _join(
                SHOT_PROMPTS[effective_shot_type],
                CAMERA_PROMPTS["Front View"],
                "straight-on symmetrical identity portrait",
                "eye-level camera positioned at face height",
                "standard rectilinear 85mm portrait-lens perspective",
                "camera placed far enough from the subject for natural undistorted facial proportions",
                "comfortable space around the complete head and both shoulders",
            )
            anchor_lens_prompt = "natural undistorted perspective with level shoulders, centered face, neutral chin position, and ordinary portrait distance"
            pose_prompt = "upright relaxed posture, shoulders level, head centered, chin neutral"
        else:
            pose_prompt = custom_pose.strip() if pose == "Custom" and custom_pose.strip() else pose.lower()
        expression_prompt = (
            custom_expression.strip() if expression == "Custom" and custom_expression.strip()
            else EXPRESSION_PROMPTS.get(expression, expression.lower() + " expression")
        )
        background_prompt = custom_background.strip() if background == "Custom" and custom_background.strip() else background.lower() + " background"
        lighting_prompt = custom_lighting.strip() if lighting == "Custom" and custom_lighting.strip() else lighting.lower()
        style_prompt = photo_style.lower()

        effective_body_mode = _resolve_body_mode(stage, clothing_mode, body_detail_mode)

        if clothing_mode == "Clinical Unclothed":
            clothing_base = "unclothed adult subject in neutral clinical anatomy documentation"
            components = {"kind": "clinical"}
            clothing_prompt = clothing_base
            outfit_lock = ""
        elif clothing_mode == "Preserve Reference Clothing":
            clothing_base = "preserve the complete clothing already visible in Image 1"
            components = {"kind": "preserve"}
            clothing_prompt = clothing_base
            outfit_lock = "the same complete reference outfit remains visible in the selected crop"
        elif clothing_mode == "Exact Outfit Override":
            components = _override_components(
                exact_outfit, exact_top, exact_bottom, exact_footwear, exact_outerwear,
                outfit_coverage,
            )
            clothing_base = _component_phrase(components)
            clothing_prompt, outfit_lock = _crop_outfit_prompt(
                clothing_base, components, effective_shot_type, region, clothing_priority,
            )
        else:
            components = default_components or {"kind": "complete", "raw": default_clothing}
            clothing_base = default_clothing or _component_phrase(components)
            clothing_prompt, outfit_lock = _crop_outfit_prompt(
                clothing_base, components, effective_shot_type, region, clothing_priority,
            )

        face_only = effective_shot_type in {"Face Close-Up", "Head and Shoulders"}
        upper_visible = effective_shot_type in {"Chest-Up", "Waist-Up Midshot", "Three-Quarter Body", "Full Body", "Body Close-Up"}
        lower_visible = effective_shot_type in {"Three-Quarter Body", "Full Body", "Body Close-Up"}

        upper = anatomy_upper if effective_body_mode == "Clinical Anatomy" else clothed_upper
        lower = anatomy_lower if effective_body_mode == "Clinical Anatomy" else clothed_lower

        visible_upper = "" if face_only else upper
        visible_lower = lower if lower_visible else ""

        # Clothing is deliberately placed immediately after framing so it is not buried after anatomy.
        krea_prompt = _join(
            trigger_word,
            shot_prompt,
            clothing_prompt,
            pose_prompt,
            expression_prompt,
            face,
            marks,
            visible_upper,
            visible_lower,
            background_prompt,
            lighting_prompt,
            style_prompt,
            anchor_lens_prompt,
            outfit_lock,
            custom_suffix,
        )

        if stage == "Krea Identity Anchor":
            reference = "None — text-to-image"
            qwen_prompt = ""
            planner_notes = _join(
                "Krea identity anchor is locked to a straight-on face or head-and-shoulders portrait",
                "eye-level 85mm rectilinear portrait perspective prevents fisheye and overhead compression",
                f"body detail mode: {effective_body_mode}",
                "clothing is placed immediately after framing and is crop-aware",
            )
        elif stage == "Qwen Face Documentation":
            reference = "Portrait Anchor"
            qwen_prompt = _join(
                "Edit Image 1 into a realistic photograph of the same adult person",
                "preserve the exact recognizable face, hair, skin characteristics, and permanent facial markings from Image 1",
                shot_prompt,
                clothing_prompt,
                pose_prompt,
                expression_prompt,
                face,
                marks,
                background_prompt,
                lighting_prompt,
                style_prompt,
                outfit_lock,
                "keep natural skin texture, realistic moist eyes, ordinary camera sharpness, and believable hair strands",
                custom_suffix,
            )
            planner_notes = "Uses only face, hair, expression, camera, visible clothing, and permanent markings."
        elif stage == "Qwen Upper-Body Anchor":
            reference = "Portrait Anchor"
            qwen_prompt = _join(
                "Edit Image 1 into a realistic upper-body photograph of the same adult person",
                "preserve the exact recognizable face and hair from Image 1",
                shot_prompt,
                clothing_prompt,
                pose_prompt,
                expression_prompt,
                face,
                marks,
                upper,
                background_prompt,
                lighting_prompt,
                style_prompt,
                outfit_lock,
                "establish consistent shoulders, chest, torso, arms, and natural waist while preserving identity",
                custom_suffix,
            )
            planner_notes = _join("Introduces upper-body traits", f"body detail mode: {effective_body_mode}")
        elif stage == "Qwen Anatomy Documentation":
            reference = "Portrait or Anatomy Anchor"
            clinical_clothing = "unclothed adult subject in neutral clinical anatomy documentation"
            qwen_prompt = _join(
                "Edit Image 1 into neutral adult clinical anatomy documentation of the same person",
                "preserve exact face, hair, body proportions, tattoos, and piercings",
                shot_prompt,
                clinical_clothing,
                pose_prompt,
                face,
                marks,
                anatomy_upper,
                anatomy_lower if lower_visible else "",
                background_prompt,
                lighting_prompt,
                "clinical documentation photography",
                custom_suffix,
            )
            effective_body_mode = "Clinical Anatomy"
            planner_notes = "Clinical anatomy mode uses the full anatomy description and excludes clothing."
        elif stage == "Qwen Clothing Edit":
            reference = "Anatomy or Clothed Anchor"
            qwen_prompt = _join(
                "Edit Image 1 into a realistic wardrobe photograph of the same adult person",
                "preserve the exact face, hair, body shape, chest proportions, waist, tattoos, and piercings from Image 1",
                shot_prompt,
                clothing_prompt,
                pose_prompt,
                expression_prompt,
                face,
                marks,
                clothed_upper,
                clothed_lower if lower_visible else "",
                background_prompt,
                lighting_prompt,
                style_prompt,
                outfit_lock,
                "render realistic fabric, seams, folds, edges, straps, waistbands, and garment tension",
                custom_suffix,
            )
            effective_body_mode = "Clothed Silhouette"
            planner_notes = "Wardrobe edit uses clothed silhouette only; anatomy-only lower-body notes are excluded."
        elif stage == "Qwen Body Close-Up":
            reference = "Anatomy Anchor"
            qwen_prompt = _join(
                "Edit Image 1 into focused adult body-documentation photography of the same person",
                "preserve exact body proportions, skin characteristics, tattoos, and piercings",
                shot_prompt,
                clothing_prompt,
                pose_prompt,
                anatomy_upper if upper_visible else "",
                anatomy_lower if lower_visible else "",
                marks,
                background_prompt,
                lighting_prompt,
                "clinical documentation photography",
                custom_suffix,
            )
            planner_notes = "Body close-up uses anatomy details and the selected body region."
        else:
            reference = "Mini LoRA loaded in Krea model lane"
            qwen_prompt = ""
            planner_notes = _join(
                "Krea mini-LoRA expansion uses the targeted face and body profile",
                f"body detail mode: {effective_body_mode}",
                "clothing is authoritative and crop-aware",
            )

        if effective_shot_type == "Face Close-Up":
            width, height = 1024, 1024
        elif effective_shot_type in {"Head and Shoulders", "Chest-Up", "Waist-Up Midshot", "Body Close-Up"}:
            width, height = 1024, 1280
        else:
            width, height = 1024, 1536

        shot_id = _slug(_join(character_id, stage, effective_shot_type, camera_view, pose, clothing_mode))
        return (
            krea_prompt, qwen_prompt, shot_prompt, clothing_prompt, marks, reference, shot_id,
            width, height, character_id, planner_notes, effective_body_mode, outfit_lock,
            _component_phrase(components) if components.get("kind") not in {"clinical", "preserve"} else clothing_base,
        )


BOOTSTRAP_PLANS = [
    "Identity Extreme Close-Ups",
    "Identity Face Close-Ups",
    "Identity Midshots",
    "Identity Actions",
    "Identity Full Body & Positions",
    "Identity Balanced by Group",
    "Clinical Anatomy Focus — 12",
    "Post-LoRA Anatomy — 40",
    "Post-LoRA Clothed Actions — 60",
    "Post-LoRA Complete Pack — 120",
]


def _identity_groups() -> dict[str, list[tuple[str, str, str]]]:
    extreme = [
        ("extreme_face_front", "extreme_closeup", "true extreme close-up of the complete face from hairline to chin, straight-on front view, face occupying approximately 85 percent of the frame, shoulders and torso cropped away, not a head-and-shoulders context portrait"),
        ("extreme_left_eye", "extreme_closeup", "true macro extreme close-up of only the left eye and left eyebrow, including eyelids, lashes, and immediately surrounding skin, selected eye region occupying approximately 80 to 90 percent of the frame, no full face"),
        ("extreme_right_eye", "extreme_closeup", "true macro extreme close-up of only the right eye and right eyebrow, including eyelids, lashes, and immediately surrounding skin, selected eye region occupying approximately 80 to 90 percent of the frame, no full face"),
        ("extreme_both_eyes", "extreme_closeup", "true macro extreme close-up containing only both eyes, both eyebrows, and the nose bridge, eye band occupying approximately 80 to 90 percent of the frame, crop away mouth and chin"),
        ("extreme_nose_septum", "extreme_closeup", "true macro extreme close-up of only the nose, nostrils, columella, nasal septum, and immediately surrounding skin, nose region occupying approximately 80 to 90 percent of the frame, preserve exact septum and nostril piercing placement, no full face"),
        ("extreme_mouth", "extreme_closeup", "true macro extreme close-up of only the mouth, lips, philtrum, lower-nose edge, and immediately surrounding skin, mouth region occupying approximately 80 to 90 percent of the frame, neutral closed mouth, no complete face"),
        ("extreme_forehead_hairline", "extreme_closeup", "true macro extreme close-up of only the forehead, hairline, both temples, and eyebrows, upper-face region occupying approximately 80 to 90 percent of the frame, crop away mouth and chin"),
        ("extreme_left_profile", "extreme_closeup", "true extreme close-up of the true left facial profile from forehead and nose through lips, chin, jawline, and left ear edge, profile occupying approximately 85 percent of the frame, no shoulders or torso"),
        ("extreme_right_profile", "extreme_closeup", "true extreme close-up of the true right facial profile from forehead and nose through lips, chin, jawline, and right ear edge, profile occupying approximately 85 percent of the frame, no shoulders or torso"),
        ("extreme_nose_mouth", "extreme_closeup", "true macro extreme close-up containing only the complete nose and complete mouth from lower nose bridge through chin edge, nose-and-mouth region occupying approximately 80 to 90 percent of the frame, crop away eyes and most cheeks, preserve moustache and beard boundaries, beard density, and all nearby permanent marks or jewelry"),
    ]
    closeups = [
        ("close_front", "closeup", "head-and-shoulders identity portrait, straight-on front view, neutral expression"),
        ("close_three_quarter_left", "closeup", "head-and-shoulders identity portrait, three-quarter left view, neutral expression"),
        ("close_three_quarter_right", "closeup", "head-and-shoulders identity portrait, three-quarter right view, neutral expression"),
        ("close_left_profile", "closeup", "head-and-shoulders identity portrait, true left profile, neutral expression"),
        ("close_right_profile", "closeup", "head-and-shoulders identity portrait, true right profile, neutral expression"),
        ("close_slight_up", "closeup", "head-and-shoulders identity portrait, chin slightly raised, camera level with the nose"),
        ("close_slight_down", "closeup", "head-and-shoulders identity portrait, chin slightly lowered, camera only slightly above eye level"),
        ("close_soft_smile", "closeup", "head-and-shoulders identity portrait, front view, natural closed-mouth smile"),
        ("close_rear_turn_left", "closeup", "rear three-quarter left head-and-shoulders view with head turned toward camera"),
        ("close_rear_turn_right", "closeup", "rear three-quarter right head-and-shoulders view with head turned toward camera"),
    ]
    midshots = [
        ("mid_chest_front", "midshot", "chest-up identity portrait, front view, shoulders relaxed"),
        ("mid_chest_left", "midshot", "chest-up identity portrait, three-quarter left view"),
        ("mid_chest_right", "midshot", "chest-up identity portrait, three-quarter right view"),
        ("mid_waist_front", "midshot", "waist-up identity midshot, front view, arms relaxed"),
        ("mid_waist_left", "midshot", "waist-up identity midshot, three-quarter left view"),
        ("mid_waist_right", "midshot", "waist-up identity midshot, three-quarter right view"),
        ("mid_left_profile", "midshot", "waist-up identity midshot, true left profile"),
        ("mid_right_profile", "midshot", "waist-up identity midshot, true right profile"),
        ("mid_seated", "midshot", "waist-up seated identity portrait, front view, relaxed posture"),
        ("mid_arms_crossed", "midshot", "waist-up identity midshot, arms loosely crossed"),
    ]
    actions = [
        ("action_walk", "action", "natural walking action photograph, waist-up framing"),
        ("action_couch", "action", "seated naturally on a couch, waist-up candid photograph"),
        ("action_counter", "action", "leaning naturally on a kitchen counter, waist-up candid photograph"),
        ("action_food", "action", "preparing healthy food in a kitchen, natural waist-up action photograph"),
        ("action_coffee", "action", "holding and drinking from a coffee mug, natural waist-up photograph"),
        ("action_desk", "action", "working naturally at a desk, waist-up candid photograph"),
        ("action_warmup", "action", "performing a simple gym warm-up, natural action photograph"),
        ("action_dumbbells", "action", "performing a controlled dumbbell exercise, natural action photograph"),
        ("action_stretch", "action", "performing a natural standing stretch, action photograph"),
        ("action_postworkout", "action", "relaxed post-workout stance, natural candid photograph"),
    ]
    full = [
        ("full_front", "full_body", "full-body identity photograph, straight-on front view, neutral standing"),
        ("full_three_quarter_left", "full_body", "full-body identity photograph, three-quarter left view"),
        ("full_three_quarter_right", "full_body", "full-body identity photograph, three-quarter right view"),
        ("full_left_profile", "full_body", "full-body identity photograph, true left profile"),
        ("full_right_profile", "full_body", "full-body identity photograph, true right profile"),
        ("full_back", "full_body", "full-body identity photograph, direct back view"),
        ("full_walking", "full_body", "full-body identity photograph during a natural walking step"),
        ("full_seated", "full_body", "full-body seated identity pose, relaxed posture"),
        ("full_leaning", "full_body", "full-body identity pose, lightly leaning against a wall"),
        ("full_rear_turn", "full_body", "full-body rear three-quarter view with head turned toward camera"),
    ]
    return {
        "extreme_closeup": extreme,
        "closeup": closeups,
        "midshot": midshots,
        "action": actions,
        "full_body": full,
    }


def _clinical_focus_specs() -> list[tuple[str, str, str]]:
    return [
        ("clinical_chest_front", "anatomy_focus", "focused clinical close-up of chest and ribcage, straight-on front view"),
        ("clinical_chest_left", "anatomy_focus", "focused clinical close-up of chest and ribcage, true left profile"),
        ("clinical_chest_right", "anatomy_focus", "focused clinical close-up of chest and ribcage, true right profile"),
        ("clinical_abdomen_front", "anatomy_focus", "focused clinical close-up of abdomen and waist, straight-on front view"),
        ("clinical_abdomen_left", "anatomy_focus", "focused clinical close-up of abdomen and waist, true left profile"),
        ("clinical_abdomen_right", "anatomy_focus", "focused clinical close-up of abdomen and waist, true right profile"),
        ("clinical_pelvis_front", "anatomy_focus", "focused clinical close-up of pelvis and groin anatomy, straight-on front view, neutral non-aroused anatomy"),
        ("clinical_pelvis_left", "anatomy_focus", "focused clinical close-up of pelvis and groin anatomy, true left profile, neutral non-aroused anatomy"),
        ("clinical_pelvis_right", "anatomy_focus", "focused clinical close-up of pelvis and groin anatomy, true right profile, neutral non-aroused anatomy"),
        ("clinical_gluteal_rear", "anatomy_focus", "focused clinical close-up of hips and gluteal anatomy, direct rear view"),
        ("clinical_gluteal_left", "anatomy_focus", "focused clinical close-up of hips and gluteal anatomy, true left profile"),
        ("clinical_gluteal_right", "anatomy_focus", "focused clinical close-up of hips and gluteal anatomy, true right profile"),
    ]


def _dataset_specs(plan: str, images_per_group: int = 5) -> list[dict[str, str]]:
    group_size = max(5, min(10, int(images_per_group)))
    groups = _identity_groups()
    if plan == "Identity Extreme Close-Ups":
        raw = groups["extreme_closeup"][:group_size]
    elif plan == "Identity Face Close-Ups":
        raw = groups["closeup"][:group_size]
    elif plan == "Identity Midshots":
        raw = groups["midshot"][:group_size]
    elif plan == "Identity Actions":
        raw = groups["action"][:group_size]
    elif plan == "Identity Full Body & Positions":
        raw = groups["full_body"][:group_size]
    elif plan == "Identity Balanced by Group":
        raw = []
        for key in ("extreme_closeup", "closeup", "midshot", "action", "full_body"):
            raw.extend(groups[key][:group_size])
    elif plan == "Clinical Anatomy Focus — 12":
        raw = _clinical_focus_specs()
    else:
        anatomy = [(f"anatomy_{i:02d}", "anatomy", desc) for i, desc in enumerate([
            "clinical upper-body documentation, front view", "clinical upper-body documentation, three-quarter left view", "clinical upper-body documentation, three-quarter right view", "clinical upper-body documentation, left profile", "clinical upper-body documentation, right profile", "clinical upper-body documentation, back view", "clinical torso documentation focused on chest and ribcage", "clinical torso documentation focused on abdomen and waist", "clinical torso documentation focused on upper back and shoulders", "clinical torso documentation focused on lower back and waist", "clinical body documentation focused on hips front", "clinical body documentation focused on hips rear", "clinical full-body documentation, front view", "clinical full-body documentation, left profile", "clinical full-body documentation, right profile", "clinical full-body documentation, back view", "clinical three-quarter-body documentation, front view", "clinical three-quarter-body documentation, rear three-quarter view", "clinical side torso documentation, left side", "clinical side torso documentation, right side",
        ], 1)]
        actions = [(f"action_{i:02d}", "clothed_action", desc) for i, desc in enumerate([
            "waist-up casual standing photo", "waist-up natural walking photo", "waist-up seated on a couch", "waist-up leaning on a kitchen counter", "waist-up preparing healthy food", "waist-up holding a coffee mug", "waist-up working at a desk", "waist-up outdoor walking photo", "waist-up gym warm-up photo", "waist-up holding dumbbells", "waist-up stretching", "waist-up post-workout photo", "full-body casual standing", "full-body walking outdoors", "full-body seated on a chair", "full-body leaning against a wall", "full-body kitchen activity", "full-body office activity", "full-body gym stance", "full-body bodyweight squat setup",
        ], 1)]
        if plan == "Post-LoRA Anatomy — 40":
            raw = anatomy * 2
        elif plan == "Post-LoRA Clothed Actions — 60":
            raw = actions * 3
        else:
            raw = anatomy * 2 + actions * 4
    return [{"shot_id": a, "category": b, "description": c} for a, b, c in raw]


class QwenDatasetQueue:
    CATEGORY = "character creation/dataset"
    FUNCTION = "build_queue"
    DESCRIPTION = "Creates a one-click list of Qwen Image Edit prompts from one approved headshot. Connect list outputs to one reusable Qwen edit lane."
    RETURN_TYPES = ("STRING", "INT", "STRING", "STRING", "STRING", "INT", "INT", "STRING", "STRING")
    RETURN_NAMES = ("qwen_prompts", "seeds", "shot_ids", "categories", "filename_prefixes", "widths", "heights", "dataset_plan_json", "progress_labels")
    OUTPUT_IS_LIST = (True, True, True, True, True, True, True, True, True)

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "character_blueprint": ("CHARACTER_BLUEPRINT",),
            "dataset_plan": (BOOTSTRAP_PLANS, {"default": "Identity Extreme Close-Ups"}),
            "starting_seed": ("INT", {"default": 1000, "min": 0, "max": 0xffffffffffffffff}),
            "variations_per_shot": ("INT", {"default": 1, "min": 1, "max": 4}),
            "images_per_group": ("INT", {"default": 5, "min": 5, "max": 10}),
            "output_root": ("STRING", {"default": "FCC_Dataset", "multiline": False}),
            "reference_label": ("STRING", {"default": "Image 1", "multiline": False}),
        }, "optional": {
            "prompt_suffix": ("STRING", {"default": "", "multiline": True}),
            "complete_outfit_override": ("STRING", {"default": "", "multiline": True}),
        }}

    def build_queue(self, character_blueprint, dataset_plan, starting_seed, variations_per_shot, images_per_group, output_root, reference_label, prompt_suffix="", complete_outfit_override=""):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        face = profile.get("face_identity", "adult subject")
        marks = profile.get("marks_prompt", "")
        tattoo_count_lock = profile.get("tattoo_count_lock", "")
        piercing_count_lock = profile.get("piercing_count_lock", "")
        anatomy_integrity_lock = profile.get("anatomy_integrity_lock", "")
        upper = profile.get("clothed_upper_body", profile.get("upper_body_identity", ""))
        lower = profile.get("clothed_lower_body", profile.get("lower_body_identity", ""))
        anatomy_upper = profile.get("anatomy_upper_body", profile.get("upper_body_identity", ""))
        anatomy_lower = profile.get("anatomy_lower_body", profile.get("lower_body_identity", ""))
        outfit = complete_outfit_override.strip() or profile.get("default_clothing_prompt", "complete simple fitted clothing")
        character_id = profile.get("character_id", "character")
        specs = _dataset_specs(dataset_plan, images_per_group)
        prompts=[]; seeds=[]; ids=[]; cats=[]; prefixes=[]; widths=[]; heights=[]; progress_labels=[]; manifest=[]
        idx=0
        for spec in specs:
            for variation in range(variations_per_shot):
                cat=spec["category"]
                clinical = cat in {"anatomy", "anatomy_focus"}
                if clinical:
                    wardrobe = "unclothed adult subject in neutral clinical anatomy documentation"
                    body = _join(anatomy_upper, anatomy_lower)
                    style = "neutral clinical documentation photography, even lighting, plain background"
                else:
                    if cat in {"extreme_closeup", "closeup"}:
                        wardrobe = f"preserve only the same upper garment visible at the lower edge of {reference_label}"
                    else:
                        wardrobe = outfit
                    include_lower = cat in {"full_body", "action", "body_confirmation", "clothed_action"}
                    body = _join(upper if cat not in {"extreme_closeup", "closeup"} else "", lower if include_lower else "")
                    style = "ordinary realistic consumer-camera photograph, natural skin texture, believable eyes and hair, standard rectilinear lens perspective"
                prompt = _join(
                    f"Edit {reference_label} into a realistic photograph of the same adult person",
                    f"preserve the exact recognizable facial identity, hairline, skin characteristics, tattoos, and piercings from {reference_label}",
                    spec["description"], wardrobe, face, marks, body,
                    tattoo_count_lock, piercing_count_lock, anatomy_integrity_lock,
                    style,
                    "keep identity consistent; do not invent, remove, duplicate, mirror, or relocate permanent markings",
                    prompt_suffix,
                )
                seed = int(starting_seed) + idx
                sid = f"{spec['shot_id']}_v{variation+1:02d}"
                prefix = f"{output_root}/{cat}/{idx+1:04d}_{sid}"
                if cat == "extreme_closeup":
                    w,h=(1024,1024)
                elif cat in {"closeup", "midshot", "anatomy_focus"}:
                    w,h=(1024,1280)
                else:
                    w,h=(1024,1536)
                prompts.append(prompt); seeds.append(seed); ids.append(sid); cats.append(cat); prefixes.append(prefix); widths.append(w); heights.append(h)
                manifest.append({"index": idx+1, "shot_id": sid, "category": cat, "seed": seed, "filename_prefix": prefix, "width": w, "height": h, "prompt": prompt})
                idx += 1
        total = len(manifest)
        for item in manifest:
            progress_labels.append(f"{item['index']} of {total} | {item['category']} | {item['shot_id']}")
        plan_json = json.dumps({"schema":"FCC_QWEN_DATASET_PLAN", "schema_version":2, "character_id":character_id, "plan":dataset_plan, "images_per_group":images_per_group, "variations_per_shot":variations_per_shot, "total_images":len(manifest), "items":manifest}, indent=2, ensure_ascii=False)
        return prompts, seeds, ids, cats, prefixes, widths, heights, [plan_json for _ in prompts], progress_labels


DIRECTOR_TARGETS = [
    "Identity Extreme Close-Ups",
    "Identity Face Close-Ups",
    "Identity Midshots",
    "Identity Actions",
    "Identity Full Body & Positions",
    "Identity Balanced by Group",
    "Clinical Anatomy Focus — 12",
    "Post-LoRA Medical Anatomy — 40",
    "Post-LoRA Clothed Actions — 60",
    "Post-LoRA Complete Expansion — 120",
]

class FCCDatasetDirector:
    CATEGORY = "character creation/studio"
    FUNCTION = "direct"
    DESCRIPTION = "Master one-click dataset director. Builds the Qwen queue from the approved headshot and exposes a readable dashboard and manifest."
    RETURN_TYPES = ("STRING","INT","STRING","STRING","STRING","INT","INT","STRING","STRING","STRING","STRING")
    RETURN_NAMES = ("qwen_prompts","seeds","shot_ids","categories","filename_prefixes","widths","heights","dataset_plan_json","queue_preview","dashboard","progress_labels")
    OUTPUT_IS_LIST = (True,True,True,True,True,True,True,False,False,False,True)

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "character_blueprint": ("CHARACTER_BLUEPRINT",),
            "target": (DIRECTOR_TARGETS, {"default":"Identity Extreme Close-Ups"}),
            "approved_headshot_label": ("STRING", {"default":"Image 1"}),
            "project_name": ("STRING", {"default":"FCC_Character"}),
            "starting_seed": ("INT", {"default":1000,"min":0,"max":0xffffffffffffffff}),
            "variations_per_shot": ("INT", {"default":1,"min":1,"max":4}),
            "images_per_group": ("INT", {"default":5,"min":5,"max":10}),
            "lora_available": ("BOOLEAN", {"default":False}),
        }, "optional": {
            "prompt_suffix": ("STRING", {"default":"", "multiline":True}),
            "complete_outfit_override": ("STRING", {"default":"", "multiline":True}),
        }}

    def direct(self, character_blueprint, target, approved_headshot_label, project_name, starting_seed, variations_per_shot, images_per_group, lora_available, prompt_suffix="", complete_outfit_override=""):
        mapping = {
            "Identity Extreme Close-Ups":"Identity Extreme Close-Ups",
            "Identity Face Close-Ups":"Identity Face Close-Ups",
            "Identity Midshots":"Identity Midshots",
            "Identity Actions":"Identity Actions",
            "Identity Full Body & Positions":"Identity Full Body & Positions",
            "Identity Balanced by Group":"Identity Balanced by Group",
            "Clinical Anatomy Focus — 12":"Clinical Anatomy Focus — 12",
            "Post-LoRA Medical Anatomy — 40":"Post-LoRA Anatomy — 40",
            "Post-LoRA Clothed Actions — 60":"Post-LoRA Clothed Actions — 60",
            "Post-LoRA Complete Expansion — 120":"Post-LoRA Complete Pack — 120",
        }
        post = target.startswith("Post-LoRA")
        if post and not lora_available:
            dashboard = "BLOCKED: Post-LoRA target selected but LoRA Available is OFF. Enable the LoRA and switch this control ON before running."
            return [],[],[],[],[],[],[],json.dumps({"blocked":True,"reason":dashboard}, indent=2),"",dashboard,[]
        q=QwenDatasetQueue()
        prompts,seeds,ids,cats,prefixes,widths,heights,plan_json_list,progress_labels=q.build_queue(
            character_blueprint,mapping[target],starting_seed,variations_per_shot,images_per_group,project_name,approved_headshot_label,prompt_suffix,complete_outfit_override
        )
        plan_json = plan_json_list[0] if plan_json_list else "{}"
        preview_lines=[]
        for i,(sid,cat,seed,prefix) in enumerate(zip(ids,cats,seeds,prefixes),1):
            preview_lines.append(f"{i:03d} | {cat} | {sid} | seed {seed} | {prefix}")
        profile=character_blueprint if isinstance(character_blueprint,dict) else {}
        dashboard="\n".join([
            "FULL CHARACTER STUDIO",
            f"Character: {profile.get('character_id','character')}",
            f"Gender branch: {profile.get('gender','unknown')}",
            f"Target: {target}",
            f"Approved reference: {approved_headshot_label}",
            f"LoRA available: {'YES' if lora_available else 'NO'}",
            f"Images per identity group: {images_per_group}",
            f"Total queued images: {len(prompts)}",
            "Status: READY — queue the workflow once to map the list through the Qwen lane.",
        ])
        return prompts,seeds,ids,cats,prefixes,widths,heights,plan_json,"\n".join(preview_lines),dashboard,progress_labels


class FCCQueueItemRouter:
    CATEGORY = "character creation/studio"
    FUNCTION = "route"
    DESCRIPTION = "Maps one Dataset Director list item at a time and exposes a live progress label before the generator runs."
    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT", "STRING", "STRING", "INT", "INT")
    RETURN_NAMES = ("qwen_prompt", "filename_prefix", "progress_label", "seed", "shot_id", "category", "width", "height")

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "qwen_prompt": ("STRING", {"forceInput": True}),
            "filename_prefix": ("STRING", {"forceInput": True}),
            "progress_label": ("STRING", {"forceInput": True}),
            "seed": ("INT", {"forceInput": True}),
            "shot_id": ("STRING", {"forceInput": True}),
            "category": ("STRING", {"forceInput": True}),
            "width": ("INT", {"forceInput": True}),
            "height": ("INT", {"forceInput": True}),
        }}

    def route(self, qwen_prompt, filename_prefix, progress_label, seed, shot_id, category, width, height):
        return qwen_prompt, filename_prefix, progress_label, seed, shot_id, category, width, height

# -----------------------------------------------------------------------------
# V2.1 architecture: Character Creator owns identity/body/clothing/presentation.
# Universal Shot Control owns framing/camera/pose/expression/environment/focus.
# Prompt Assembler combines both without silently overriding either side.
# -----------------------------------------------------------------------------

PRESENTATION_MODES_V2 = [
    "Clothed Character",
    "Clinical Anatomy",
    "Custom Presentation",
]
OUTFIT_SOURCES_V2 = [
    "Preset Outfit",
    "Exact Outfit Text",
    "Structured Components",
]
STRUCTURED_OUTFIT_TYPES_V2 = [
    "Complete Outfit",
    "One-Piece Garment",
    "Swimwear Set",
    "Lingerie Set",
]
LINGERIE_STYLES_V2 = [
    "Matching Bra and Brief Set",
    "Balconette Bra and Brief Set",
    "Bralette and Brief Set",
    "Longline Bra and High-Waisted Briefs",
    "Bra and Thong Set",
    "Lace Bodysuit",
    "Teddy",
    "Babydoll with Matching Briefs",
    "Corset and Brief Set",
    "Chemise",
    "Custom",
]
LINGERIE_STYLE_PROMPTS_V2 = {
    "Matching Bra and Brief Set": "a coordinated bra and matching brief lingerie set",
    "Balconette Bra and Brief Set": "a coordinated balconette bra and matching brief lingerie set",
    "Bralette and Brief Set": "a coordinated soft bralette and matching brief lingerie set",
    "Longline Bra and High-Waisted Briefs": "a coordinated longline bra and matching high-waisted brief lingerie set",
    "Bra and Thong Set": "a coordinated bra and matching thong lingerie set",
    "Lace Bodysuit": "a complete fitted lace bodysuit",
    "Teddy": "a complete fitted one-piece teddy lingerie garment",
    "Babydoll with Matching Briefs": "a complete babydoll lingerie garment with matching briefs",
    "Corset and Brief Set": "a coordinated fitted corset and matching brief lingerie set",
    "Chemise": "a complete fitted chemise lingerie garment",
}
CUSTOM_BODY_BASES_V2 = [
    "Clothed Silhouette",
    "Clinical Anatomy",
    "Identity Only",
]

PLANNER_MODES_V2 = [
    "Freestyle Controls — Use All Selections",
    "Guided Controls",
    "Full Custom Shot Text",
]
SHOT_TYPES_V2 = [
    "Extreme Close-Up — Single Detail",
    "Close-Up — Regional Documentation",
    "Face Close-Up",
    "Head and Shoulders",
    "Chest-Up",
    "Waist-Up Midshot",
    "Three-Quarter Body",
    "Full Body",
    "Custom Framing",
]
SHOT_PROMPTS_V2 = {
    "Face Close-Up": "close-up face portrait with the complete head, hairline, ears or ear edges, neck, and upper shoulders visible",
    "Head and Shoulders": "head-and-shoulders portrait with the complete head, hair, neck, both shoulders, and upper chest visible",
    "Chest-Up": "chest-up portrait framed from above the complete head to below the chest, both shoulders and upper arms visible",
    "Waist-Up Midshot": "waist-up midshot framed from above the complete head through the natural waist and lower abdomen, both arms visible",
    "Three-Quarter Body": "three-quarter-body photograph framed from above the complete head to below the knees",
    "Full Body": "full-body photograph with the entire subject visible from head to feet and balanced space around the body",
    "Custom Framing": "custom framing",
}
EXTREME_CLOSEUP_FOCUS_V2 = [
    "Complete Face",
    "Left Eye and Eyebrow",
    "Right Eye and Eyebrow",
    "Both Eyes and Nose Bridge",
    "Nose and Septum",
    "Mouth and Lips",
    "Nose and Mouth",
    "Forehead and Hairline",
    "Left Facial Profile",
    "Right Facial Profile",
    "Chin Jawline and Beard",
    "Left Ear",
    "Right Ear",
    "Left Nipple and Areola",
    "Right Nipple and Areola",
    "Both Nipples and Chest Center",
    "Navel",
    "Pubic Mons",
    "External Genital Anatomy",
    "Left Hand",
    "Right Hand",
    "Left Foot",
    "Right Foot",
    "Custom",
]
CLOSEUP_REGIONS_V2 = [
    "Face Portrait",
    "Head and Neck",
    "Upper Chest",
    "Chest and Ribcage",
    "Left Chest Profile",
    "Right Chest Profile",
    "Abdomen and Waist",
    "Groin and Pelvis",
    "Left Groin Profile",
    "Right Groin Profile",
    "Hips Front",
    "Left Hip Profile",
    "Right Hip Profile",
    "Buttocks Rear",
    "Left Buttock Profile",
    "Right Buttock Profile",
    "Upper Back and Shoulders",
    "Lower Back and Waist",
    "Left Arm",
    "Right Arm",
    "Both Arms",
    "Left Hand",
    "Right Hand",
    "Both Hands",
    "Left Thigh",
    "Right Thigh",
    "Both Thighs",
    "Left Foot",
    "Right Foot",
    "Both Feet",
    "Custom",
]
CAMERA_HEIGHTS_V2 = [
    "Eye Level",
    "Slightly Above Eye Level",
    "Slightly Below Eye Level",
    "High Angle",
    "Low Angle",
    "Overhead",
    "Custom",
]
CAMERA_HEIGHT_PROMPTS_V2 = {
    "Eye Level": "eye-level camera positioned directly at the subject's face or selected body region",
    "Slightly Above Eye Level": "camera positioned only slightly above eye level with minimal downward angle",
    "Slightly Below Eye Level": "camera positioned only slightly below eye level with minimal upward angle",
    "High Angle": "clearly elevated high-angle camera looking downward",
    "Low Angle": "clearly low-angle camera looking upward",
    "Overhead": "overhead top-down camera angle",
}
LENSES_V2 = [
    "85mm Portrait — Recommended",
    "70mm Portrait",
    "50mm Normal",
    "105mm Macro",
    "35mm Environmental",
    "Custom",
]
LENS_PROMPTS_V2 = {
    "85mm Portrait — Recommended": "rectilinear 85mm portrait-lens perspective with natural facial proportions",
    "70mm Portrait": "rectilinear 70mm portrait-lens perspective with gentle portrait compression",
    "50mm Normal": "rectilinear 50mm normal-lens perspective",
    "105mm Macro": "rectilinear 105mm macro-lens perspective with precise close detail",
    "35mm Environmental": "rectilinear 35mm environmental portrait perspective with moderate scene context",
}
POSES_V2 = [
    "Neutral Standing",
    "Relaxed Standing",
    "Seated",
    "Leaning",
    "Walking",
    "Arms Relaxed",
    "Arms Loosely Crossed",
    "One Hand at Waist",
    "Peace Sign Near Face",
    "Heart Shape with Both Hands",
    "One Hand in Hair",
    "Over-the-Shoulder Blogger Pose",
    "Casual Crossed-Leg Standing",
    "Custom",
]
POSE_PROMPTS_V2 = {
    "Neutral Standing": "standing upright with shoulders level and both arms resting naturally at the sides",
    "Relaxed Standing": "relaxed natural standing pose with a slight weight shift and loose shoulders",
    "Seated": "seated naturally with balanced posture and hands resting comfortably",
    "Leaning": "lightly leaning against a nearby surface with a natural relaxed posture",
    "Walking": "captured during a natural walking step with believable arm and leg movement",
    "Arms Relaxed": "both arms relaxed and fully visible in a natural position",
    "Arms Loosely Crossed": "both arms loosely crossed across the torso without hiding the face",
    "One Hand at Waist": "one hand resting naturally at the waist while the other arm remains relaxed",
    "Peace Sign Near Face": "one hand raised beside the face making a clear two-finger peace sign, all fingers anatomically correct, the other hand relaxed",
    "Heart Shape with Both Hands": "both hands raised and fully visible, thumbs and index fingers meeting to form one clear heart shape, anatomically correct fingers",
    "One Hand in Hair": "casual social-media pose with one hand lightly touching the hair and the other arm relaxed",
    "Over-the-Shoulder Blogger Pose": "casual blogger-style over-the-shoulder pose with the torso angled away and the face turned naturally back toward the camera",
    "Casual Crossed-Leg Standing": "casual social-media standing pose with one leg crossed lightly in front of the other and relaxed posture",
}
EXPRESSIONS_V2 = [
    "Neutral",
    "Soft Closed-Mouth Smile",
    "Natural Closed-Mouth Smile",
    "Genuine Smile",
    "Big Smile",
    "Laughing",
    "Serious",
    "Focused",
    "Thoughtful",
    "Surprised",
    "Shy",
    "Confident",
    "Angry",
    "Fearful",
    "Playful",
    "Pout",
    "Wink",
    "Tongue Slightly Out",
    "Ahegao (Stylized Adult)",
    "Custom",
]
EXPRESSION_PROMPTS_V2 = {
    "Soft Closed-Mouth Smile": "soft relaxed closed-mouth smile",
    "Natural Closed-Mouth Smile": "natural closed-mouth smile",
    "Genuine Smile": "genuine natural smile",
    "Big Smile": "big open expressive smile",
    "Laughing": "natural laughing expression",
    "Serious": "serious calm expression",
    "Focused": "focused attentive expression",
    "Thoughtful": "thoughtful reflective expression",
    "Surprised": "natural surprised expression",
    "Shy": "subtle shy expression",
    "Confident": "confident composed expression",
    "Angry": "controlled angry expression",
    "Fearful": "controlled fearful expression",
    "Playful": "playful natural expression",
    "Pout": "subtle pout",
    "Wink": "one natural eye wink while preserving facial identity",
    "Tongue Slightly Out": "playful expression with the tongue only slightly visible",
    "Ahegao (Stylized Adult)": "exaggerated stylized adult ahegao expression with crossed or upward-rolled eyes, open mouth, and tongue visible; intentionally non-natural facial acting",
}
BACKGROUNDS_V2 = [
    "Plain Neutral",
    "Studio Solid Gray",
    "Studio Solid White",
    "Studio Solid Black",
    "Simple Indoor",
    "Simple Outdoor",
    "Luxury High-Rise Apartment",
    "Luxury Hotel Room",
    "Luxury Hotel Suite",
    "Modern Home Bedroom",
    "Intimate-Style Bedroom",
    "Modern Living Room",
    "Indoor Pool",
    "Outdoor Pool",
    "Natural Home",
    "Gym",
    "Clinical Neutral",
    "Custom",
]
BACKGROUND_PROMPTS_V2 = {
    "Plain Neutral": "plain uncluttered neutral background",
    "Studio Solid Gray": "seamless solid gray studio background",
    "Studio Solid White": "seamless solid white studio background",
    "Studio Solid Black": "seamless solid black studio background",
    "Simple Indoor": "simple ordinary indoor environment",
    "Simple Outdoor": "simple ordinary outdoor environment",
    "Luxury High-Rise Apartment": "luxury high-rise apartment interior with refined modern furnishings and city views",
    "Luxury Hotel Room": "upscale luxury hotel room interior",
    "Luxury Hotel Suite": "spacious luxury hotel suite interior with refined furnishings",
    "Modern Home Bedroom": "modern comfortable home bedroom",
    "Intimate-Style Bedroom": "warm intimate-style bedroom with soft furnishings and a private relaxed atmosphere",
    "Modern Living Room": "modern comfortable living-room interior",
    "Indoor Pool": "upscale indoor pool environment",
    "Outdoor Pool": "outdoor swimming-pool environment with believable daylight and surrounding deck area",
    "Natural Home": "ordinary lived-in home environment",
    "Gym": "realistic modern gym environment",
    "Clinical Neutral": "clean neutral clinical documentation background",
}
LIGHTING_V2 = [
    "Soft Natural Daylight",
    "Even Window Light",
    "Clinical Even Light",
    "Warm Indoor Light",
    "Overcast Outdoor Light",
    "Golden Hour",
    "Retro Warm Film Lighting",
    "Retro Colored Practical Lights",
    "Neon Pink and Blue Cast",
    "Neon Purple and Cyan Cast",
    "Single Neon Sign Cast",
    "Moody Neon Ambient",
    "Custom",
]
LIGHTING_PROMPTS_V2 = {
    "Soft Natural Daylight": "soft natural daylight with believable shadows",
    "Even Window Light": "even natural window light",
    "Clinical Even Light": "flat even clinical documentation lighting with minimal shadow obstruction",
    "Warm Indoor Light": "warm realistic indoor lighting",
    "Overcast Outdoor Light": "soft overcast outdoor light",
    "Golden Hour": "warm low-angle golden-hour sunlight",
    "Retro Warm Film Lighting": "retro warm film-inspired lighting with gentle amber practical light and natural falloff",
    "Retro Colored Practical Lights": "retro colored practical lights casting subtle red, amber, and teal accents",
    "Neon Pink and Blue Cast": "pink and blue neon light casting clearly across the subject and nearby surfaces",
    "Neon Purple and Cyan Cast": "purple and cyan neon light casting clearly across the subject and nearby surfaces",
    "Single Neon Sign Cast": "one visible off-camera neon sign casting a believable colored glow across the subject",
    "Moody Neon Ambient": "moody low-key ambient neon lighting with realistic colored reflections and shadow depth",
}
ASPECT_RATIOS_V2 = [
    "Square 1:1",
    "Portrait 4:5",
    "Portrait 2:3",
    "Landscape 3:2",
]
DISTORTION_GUARDS_V2 = [
    "On — Natural Rectilinear",
    "Off — Allow Selected Perspective",
]
GENERATION_PURPOSES_V2 = [
    "Krea — First Identity Image",
    "Qwen — Edit from Image 1",
    "Qwen — Identity Documentation",
    "Qwen — Anatomy Documentation",
    "Qwen — Clothed Action / Lifestyle",
    "Krea — LoRA Expansion",
]


def _gender_authority_prompt_v2(gender: str) -> str:
    if gender == "Adult Male":
        return (
            "gender authority: one adult man, unmistakably male, with adult male facial structure, "
            "masculine chest, torso, pelvis, and body proportions throughout the image"
        )
    if gender == "Adult Female":
        return (
            "gender authority: one adult woman, unmistakably female, with adult female facial structure "
            "and adult female body proportions throughout the image"
        )
    return (
        "gender authority: one adult nonbinary person; preserve the explicitly specified androgynous "
        "facial structure, torso, pelvis, and body proportions throughout the image"
    )


def _wardrobe_stability_prompt() -> str:
    return (
        "wardrobe authority: the selected clothing remains in its normal intended position and coverage; "
        "do not pull, lift, lower, roll, open, unzip, remove, or displace any garment unless the Character Creator explicitly requests it"
    )


def _lingerie_components_v2(style: str, custom_description: str, footwear: str, outerwear: str, outfit_notes: str) -> tuple[dict[str, str], list[str]]:
    warnings: list[str] = []
    custom_description = (custom_description or "").strip()
    if style == "Custom":
        description = custom_description
        if not description:
            warnings.append("Lingerie Style is Custom but Custom Lingerie Description is blank.")
    else:
        description = LINGERIE_STYLE_PROMPTS_V2.get(style, style.lower())
    one_piece = style in {"Lace Bodysuit", "Teddy", "Chemise"}
    components = {
        "kind": "lingerie",
        "raw": description,
        "top": "",
        "bottom": "",
        "footwear": (footwear or "").strip(),
        "outerwear": (outerwear or "").strip(),
        "one_piece": description if one_piece else "",
        "swimwear_top": "",
        "swimwear_bottom": "",
        "notes": (outfit_notes or "").strip(),
        "lingerie_style": style,
    }
    return components, warnings


def _component_phrase_v2(components: dict[str, str]) -> str:
    kind = components.get("kind", "complete")
    raw = components.get("raw", "")
    if kind == "lingerie":
        return _join(
            f"fully wearing {raw or 'a complete coordinated lingerie set'}",
            components.get("outerwear"),
            components.get("footwear"),
            "all lingerie pieces remain fully present, correctly positioned, and clearly readable as the selected style",
        )
    return _component_phrase(components)


def _build_authoritative_outfit_v2(
    outfit_source: str,
    outfit_preset: str,
    exact_outfit_text: str,
    structured_outfit_type: str,
    lingerie_style: str,
    top: str,
    bottom: str,
    footwear: str,
    outerwear: str,
    one_piece: str,
    swimwear_top: str,
    swimwear_bottom: str,
    custom_lingerie_description: str,
    outfit_notes: str,
) -> tuple[str, dict[str, str], list[str]]:
    warnings: list[str] = []
    exact_outfit_text = (exact_outfit_text or "").strip()
    top = (top or "").strip()
    bottom = (bottom or "").strip()
    footwear = (footwear or "").strip()
    outerwear = (outerwear or "").strip()
    one_piece = (one_piece or "").strip()
    swimwear_top = (swimwear_top or "").strip()
    swimwear_bottom = (swimwear_bottom or "").strip()
    custom_lingerie_description = (custom_lingerie_description or "").strip()
    outfit_notes = (outfit_notes or "").strip()

    if outfit_source == "Preset Outfit":
        prompt, components = _build_profile_outfit(
            outfit_preset, "", "", "", "", "", "", "", "", outfit_notes
        )
        if exact_outfit_text or any((top, bottom, footwear, outerwear, one_piece, swimwear_top, swimwear_bottom, custom_lingerie_description)):
            warnings.append("Outfit Source is Preset Outfit; exact and structured clothing fields are ignored.")
    elif outfit_source == "Exact Outfit Text":
        kind = _infer_outfit_kind(exact_outfit_text)
        components = {
            "kind": kind,
            "raw": exact_outfit_text,
            "top": "",
            "bottom": "",
            "footwear": "",
            "outerwear": "",
            "one_piece": exact_outfit_text if kind == "one_piece" else "",
            "swimwear_top": "",
            "swimwear_bottom": "",
            "notes": outfit_notes,
        }
        prompt = _component_phrase_v2(components) if exact_outfit_text else ""
        prompt = _join(prompt, outfit_notes)
        if not exact_outfit_text:
            warnings.append("Outfit Source is Exact Outfit Text but Exact Outfit Text is blank.")
        if any((top, bottom, footwear, outerwear, one_piece, swimwear_top, swimwear_bottom, custom_lingerie_description)):
            warnings.append("Outfit Source is Exact Outfit Text; structured clothing component fields are ignored.")
    else:
        if structured_outfit_type == "One-Piece Garment":
            components = {
                "kind": "one_piece", "raw": "", "top": "", "bottom": "",
                "footwear": footwear, "outerwear": outerwear, "one_piece": one_piece,
                "swimwear_top": "", "swimwear_bottom": "", "notes": outfit_notes,
            }
            if not one_piece:
                warnings.append("Structured One-Piece Garment is selected but the one-piece field is blank.")
        elif structured_outfit_type == "Swimwear Set":
            components = {
                "kind": "swimwear", "raw": "", "top": "", "bottom": "",
                "footwear": footwear, "outerwear": outerwear, "one_piece": "",
                "swimwear_top": swimwear_top, "swimwear_bottom": swimwear_bottom,
                "notes": outfit_notes,
            }
            if not swimwear_top or not swimwear_bottom:
                warnings.append("Structured Swimwear Set should include both a swimwear top and matching bottoms.")
        elif structured_outfit_type == "Lingerie Set":
            components, lingerie_warnings = _lingerie_components_v2(
                lingerie_style, custom_lingerie_description, footwear, outerwear, outfit_notes
            )
            warnings.extend(lingerie_warnings)
        else:
            components = {
                "kind": "complete", "raw": "", "top": top, "bottom": bottom,
                "footwear": footwear, "outerwear": outerwear, "one_piece": "",
                "swimwear_top": "", "swimwear_bottom": "", "notes": outfit_notes,
            }
            if not top or not bottom:
                warnings.append("Structured Complete Outfit should include both a top and a bottom.")
        prompt = _join(_component_phrase_v2(components), outfit_notes)
        if exact_outfit_text:
            warnings.append("Outfit Source is Structured Components; Exact Outfit Text is ignored.")

    if prompt:
        prompt = _join(prompt, _wardrobe_stability_prompt())
    return prompt, components, warnings


class CharacterBlueprintCreatorV2:
    CATEGORY = "character creation/v2"
    FUNCTION = "build_blueprint_v2"
    DESCRIPTION = (
        "V2.1 Character Creator. Owns identity, gender authority, hair, marks, anatomy, clothing, lingerie, and active presentation. "
        "Shot controls cannot rewrite these character settings."
    )

    RETURN_TYPES = (
        "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING",
        "CHARACTER_BLUEPRINT", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING",
        "STRING", "STRING", "STRING", "STRING", "STRING", "STRING",
    )
    RETURN_NAMES = (
        "face_identity", "upper_body_identity", "lower_body_identity", "bust_prompt", "marks_prompt",
        "default_clothing_prompt", "full_profile_prompt", "character_id", "character_blueprint", "warnings",
        "clothed_upper_body", "anatomy_upper_body", "clothed_lower_body", "anatomy_lower_body",
        "structured_outfit_prompt", "character_blueprint_json", "active_presentation_prompt",
        "active_body_prompt", "active_character_prompt", "clothed_character_prompt",
        "clinical_character_prompt", "presentation_summary",
    )

    @classmethod
    def INPUT_TYPES(cls):
        preset_outfits = [x for x in DEFAULT_CLOTHING if x not in {"Clinical Unclothed Documentation", "Custom"}]
        return {
            "required": {
                "gender": (GENDERS, {"default": "Adult Female"}),
                "age_range": (AGE_RANGES, {"default": "25–34"}),
                "heritage": (HERITAGES, {"default": "Unspecified"}),
                "skin_tone": (SKIN_TONES, {"default": "Medium"}),
                "complexion": (COMPLEXIONS, {"default": "Natural Skin Texture"}),
                "face_shape": (FACE_SHAPES, {"default": "Oval"}),
                "jaw_shape": (JAW_SHAPES, {"default": "Defined"}),
                "chin_shape": (CHIN_SHAPES, {"default": "Rounded"}),
                "eye_color": (EYE_COLORS, {"default": "Brown"}),
                "eye_shape": (EYE_SHAPES, {"default": "Almond"}),
                "eyebrow_shape": (EYEBROWS, {"default": "Soft Arch"}),
                "nose_shape": (NOSES, {"default": "Straight"}),
                "lip_shape": (LIPS, {"default": "Balanced Medium"}),
                "hair_color": (HAIR_COLORS, {"default": "Dark Brown"}),
                "hair_length": (HAIR_LENGTHS, {"default": "Shoulder-Length"}),
                "hair_texture": (HAIR_TEXTURES, {"default": "Slightly Wavy"}),
                "hair_style": (HAIR_STYLES, {"default": "Loose Natural"}),
                "facial_hair": (FACIAL_HAIR, {"default": "None"}),
                "male_chest": (MALE_CHEST, {"default": "Average Male Chest"}),
                "male_genital_size": (MALE_GENITAL_SIZES, {"default": "Unspecified"}),
                "height": (HEIGHTS, {"default": "Average"}),
                "body_type": (BODY_TYPES, {"default": "Average"}),
                "bust_size": (BUST_SIZES, {"default": "Unspecified"}),
                "bust_shape": (BUST_SHAPES, {"default": "Unspecified"}),
                "bust_position": (BUST_POSITIONS, {"default": "Unspecified"}),
                "bust_firmness": (BUST_FIRMNESS, {"default": "Unspecified"}),
                "bust_augmentation": (BUST_AUGMENTATION, {"default": "Unspecified"}),
                "buttocks": (BUTTOCKS, {"default": "Average"}),
                "presentation_mode": (PRESENTATION_MODES_V2, {"default": "Clothed Character"}),
                "outfit_source": (OUTFIT_SOURCES_V2, {"default": "Exact Outfit Text"}),
                "outfit_preset": (preset_outfits, {"default": "Casual Jeans and T-Shirt"}),
                "structured_outfit_type": (STRUCTURED_OUTFIT_TYPES_V2, {"default": "Complete Outfit"}),
                "lingerie_style": (LINGERIE_STYLES_V2, {"default": "Matching Bra and Brief Set"}),
                "custom_presentation_body_basis": (CUSTOM_BODY_BASES_V2, {"default": "Clothed Silhouette"}),
                "jewelry_level": (JEWELRY_LEVELS, {"default": "Minimal"}),
                "tattoo_status": (MARK_STATUSES, {"default": "None"}),
                "piercing_status": (MARK_STATUSES, {"default": "None"}),
            },
            "optional": {
                "custom_heritage": ("STRING", {"default": "", "multiline": False}),
                "custom_hair_color": ("STRING", {"default": "", "multiline": False}),
                "custom_hair_length": ("STRING", {"default": "", "multiline": False}),
                "custom_hair_texture": ("STRING", {"default": "", "multiline": False}),
                "custom_hair_style": ("STRING", {"default": "", "multiline": False}),
                "custom_facial_hair": ("STRING", {"default": "", "multiline": True}),
                "custom_male_chest": ("STRING", {"default": "", "multiline": False}),
                "custom_identity_notes": ("STRING", {"default": "", "multiline": True}),
                "lower_body_notes": ("STRING", {"default": "", "multiline": True}),
                "exact_outfit_text": ("STRING", {"default": "casual fitted T-shirt, well-fitted jeans, and casual sneakers", "multiline": True}),
                "structured_top": ("STRING", {"default": "", "multiline": False}),
                "structured_bottom": ("STRING", {"default": "", "multiline": False}),
                "structured_footwear": ("STRING", {"default": "", "multiline": False}),
                "structured_outerwear": ("STRING", {"default": "", "multiline": False}),
                "structured_one_piece": ("STRING", {"default": "", "multiline": False}),
                "structured_swimwear_top": ("STRING", {"default": "", "multiline": False}),
                "structured_swimwear_bottom": ("STRING", {"default": "", "multiline": False}),
                "custom_lingerie_description": ("STRING", {"default": "", "multiline": True}),
                "outfit_notes": ("STRING", {"default": "", "multiline": True}),
                "custom_presentation_prompt": ("STRING", {"default": "", "multiline": True}),
                "jewelry_description": ("STRING", {"default": "", "multiline": True}),
                "tattoo_descriptors": ("STRING", {"default": "", "multiline": True, "placeholder": "One tattoo per line, including exact location"}),
                "piercing_descriptors": ("STRING", {"default": "", "multiline": True, "placeholder": "One piercing per line, including exact location and jewelry"}),
                "piercing_location": (["", "Left Eyebrow", "Right Eyebrow", "Left Nostril", "Right Nostril", "Septum", "Bridge", "Left Lip", "Right Lip", "Center Lip", "Other"], {"default": ""}),
                "piercing_type": (["", "Stud", "Hoop", "Curved Barbell", "Circular Barbell", "Horseshoe", "Clicker", "Seam Ring", "Decorative Ring", "Custom"], {"default": ""}),
                "piercing_material": (["", "Black Titanium", "Silver Titanium", "Gold", "Rose Gold", "Steel", "Custom"], {"default": ""}),
                "piercing_visibility": (["", "Subtle", "Normal", "Prominent", "Documentation"], {"default": "Normal"}),
                "structured_piercing_custom": ("STRING", {"default": "", "multiline": False}),
            },
        }

    def build_blueprint_v2(
        self, gender, age_range, heritage, skin_tone, complexion, face_shape, jaw_shape, chin_shape,
        eye_color, eye_shape, eyebrow_shape, nose_shape, lip_shape, hair_color, hair_length, hair_texture,
        hair_style, facial_hair, male_chest, male_genital_size, height, body_type, bust_size, bust_shape,
        bust_position, bust_firmness, bust_augmentation, buttocks, presentation_mode, outfit_source,
        outfit_preset, structured_outfit_type, lingerie_style, custom_presentation_body_basis,
        jewelry_level, tattoo_status, piercing_status, custom_heritage="", custom_hair_color="",
        custom_hair_length="", custom_hair_texture="", custom_hair_style="", custom_facial_hair="",
        custom_male_chest="", custom_identity_notes="", lower_body_notes="", exact_outfit_text="",
        structured_top="", structured_bottom="", structured_footwear="", structured_outerwear="",
        structured_one_piece="", structured_swimwear_top="", structured_swimwear_bottom="",
        custom_lingerie_description="", outfit_notes="", custom_presentation_prompt="",
        jewelry_description="", tattoo_descriptors="", piercing_descriptors="", piercing_location="",
        piercing_type="", piercing_material="", piercing_visibility="Normal",
        structured_piercing_custom="",
    ):
        base = CharacterBlueprintCreator().build_blueprint(
            gender=gender, age_range=age_range, heritage=heritage, skin_tone=skin_tone,
            complexion=complexion, face_shape=face_shape, jaw_shape=jaw_shape, chin_shape=chin_shape,
            eye_color=eye_color, eye_shape=eye_shape, eyebrow_shape=eyebrow_shape,
            nose_shape=nose_shape, lip_shape=lip_shape, hair_color=hair_color,
            hair_length=hair_length, hair_texture=hair_texture, hair_style=hair_style,
            height=height, body_type=body_type, bust_size=bust_size, bust_shape=bust_shape,
            bust_position=bust_position, bust_firmness=bust_firmness,
            bust_augmentation=bust_augmentation, buttocks=buttocks,
            default_clothing=outfit_preset, jewelry_level=jewelry_level,
            tattoo_status=tattoo_status, piercing_status=piercing_status,
            custom_heritage=custom_heritage, custom_hair_color=custom_hair_color,
            custom_hair_length=custom_hair_length, custom_hair_texture=custom_hair_texture,
            custom_hair_style=custom_hair_style, jewelry_description=jewelry_description,
            tattoo_descriptors=tattoo_descriptors, piercing_descriptors=piercing_descriptors,
            lower_body_notes=lower_body_notes, custom_identity_notes=custom_identity_notes,
            piercing_location=piercing_location, piercing_type=piercing_type,
            piercing_material=piercing_material, piercing_visibility=piercing_visibility,
            structured_piercing_custom=structured_piercing_custom, facial_hair=facial_hair,
            custom_facial_hair=custom_facial_hair, male_chest=male_chest,
            custom_male_chest=custom_male_chest, male_genital_size=male_genital_size,
        )
        profile = dict(base[8])
        gender_authority = _gender_authority_prompt_v2(gender)
        face_identity = _join(gender_authority, base[0])
        anatomy_upper = base[11]
        anatomy_lower = base[13]
        clothed_upper = base[10]
        clothed_lower = base[12]
        bust_prompt = base[3]
        marks_prompt = base[4]
        jewelry_prompt = profile.get("jewelry_prompt", "")

        outfit_prompt, outfit_components, outfit_warnings = _build_authoritative_outfit_v2(
            outfit_source, outfit_preset, exact_outfit_text, structured_outfit_type,
            lingerie_style, structured_top, structured_bottom, structured_footwear,
            structured_outerwear, structured_one_piece, structured_swimwear_top,
            structured_swimwear_bottom, custom_lingerie_description, outfit_notes,
        )
        clothed_presentation = _join(outfit_prompt, jewelry_prompt)
        clinical_presentation = (
            "unclothed adult subject in neutral non-aroused clinical anatomy documentation; "
            "only permanent identity piercings remain and removable accessories are absent"
        )

        warnings_list = [base[9]] if base[9] else []
        warnings_list.extend(outfit_warnings)
        if gender == "Adult Male" and any(x != "Unspecified" for x in (bust_size, bust_shape, bust_position, bust_firmness, bust_augmentation)):
            warnings_list.append("Adult Male is selected; all female bust controls are ignored and excluded from every generated prompt.")
        if gender != "Adult Male" and facial_hair not in {"None", "Clean-Shaven"}:
            warnings_list.append("Facial Hair is only authoritative for Adult Male in this version.")

        custom_presentation_prompt = (custom_presentation_prompt or "").strip()
        if presentation_mode == "Clinical Anatomy":
            active_presentation = clinical_presentation
            active_body = _join(anatomy_upper, anatomy_lower)
        elif presentation_mode == "Custom Presentation":
            active_presentation = custom_presentation_prompt
            if not active_presentation:
                warnings_list.append("Presentation Mode is Custom Presentation but Custom Presentation Prompt is blank.")
            if custom_presentation_body_basis == "Clinical Anatomy":
                active_body = _join(anatomy_upper, anatomy_lower)
            elif custom_presentation_body_basis == "Identity Only":
                active_body = ""
            else:
                active_body = _join(clothed_upper, clothed_lower)
        else:
            active_presentation = clothed_presentation
            active_body = _join(clothed_upper, clothed_lower)
            if not outfit_prompt:
                warnings_list.append("Clothed Character is selected but no authoritative outfit prompt was produced.")

        # Gender is always first. Wardrobe follows before detailed facial/body traits.
        active_character = _join(gender_authority, active_presentation, face_identity, marks_prompt, active_body)
        clothed_character = _join(gender_authority, clothed_presentation, face_identity, marks_prompt, clothed_upper, clothed_lower)
        clinical_character = _join(gender_authority, clinical_presentation, face_identity, marks_prompt, anatomy_upper, anatomy_lower)

        identity_hash_source = _join(gender_authority, face_identity, marks_prompt, anatomy_upper, anatomy_lower)
        stable_base = _join(gender, age_range, heritage, face_shape, hair_color, body_type)
        character_id = _slug(stable_base) + "_" + hashlib.sha1(identity_hash_source.encode("utf-8")).hexdigest()[:8]
        warnings = " ".join(x.strip() for x in warnings_list if x and x.strip())

        presentation_summary = "\n".join([
            "CHARACTER CREATOR V2.1 — ACTIVE CHARACTER AUTHORITY",
            f"Gender lock: {gender_authority}",
            f"Mode: {presentation_mode}",
            f"Outfit source: {outfit_source}",
            f"Structured outfit type: {structured_outfit_type}",
            f"Lingerie style: {lingerie_style if structured_outfit_type == 'Lingerie Set' else '[inactive]'}",
            f"Custom body basis: {custom_presentation_body_basis}",
            f"Active presentation: {active_presentation or '[blank]'}",
            f"Active body basis: {active_body or '[identity only]'}",
            f"Warnings: {warnings or 'None'}",
        ])

        profile.update({
            "schema": "CHARACTER_BLUEPRINT_V2",
            "schema_version": 5,
            "character_id": character_id,
            "gender": gender,
            "gender_authority_prompt": gender_authority,
            "face_identity": face_identity,
            "presentation_mode": presentation_mode,
            "outfit_source": outfit_source,
            "outfit_preset": outfit_preset,
            "structured_outfit_type": structured_outfit_type,
            "lingerie_style": lingerie_style,
            "custom_presentation_body_basis": custom_presentation_body_basis,
            "outfit_components": outfit_components,
            "structured_outfit_prompt": outfit_prompt,
            "default_clothing_prompt": clothed_presentation,
            "active_presentation_prompt": active_presentation,
            "active_body_prompt": active_body,
            "active_character_prompt": active_character,
            "clothed_character_prompt": clothed_character,
            "clinical_character_prompt": clinical_character,
            "full_profile_prompt": active_character,
            "warnings": warnings,
            "presentation_summary": presentation_summary,
        })
        blueprint_json = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        return (
            face_identity, anatomy_upper, anatomy_lower, bust_prompt, marks_prompt,
            clothed_presentation, active_character, character_id, profile, warnings,
            clothed_upper, anatomy_upper, clothed_lower, anatomy_lower,
            outfit_prompt, blueprint_json, active_presentation, active_body,
            active_character, clothed_character, clinical_character, presentation_summary,
        )


def _aspect_dimensions_v2(aspect: str) -> tuple[int, int]:
    return {
        "Square 1:1": (1024, 1024),
        "Portrait 4:5": (1024, 1280),
        "Portrait 2:3": (1024, 1536),
        "Landscape 3:2": (1536, 1024),
    }.get(aspect, (1024, 1280))


def _focus_preservation_lock_v2() -> str:
    return (
        "preserve every documented tattoo, piercing, scar, freckle pattern, and permanent mark visible within this crop "
        "at its exact location, scale, orientation, color, and jewelry type; do not omit, relocate, mirror, duplicate, or invent markings"
    )


def _extreme_focus_prompt_v2(focus: str, custom: str) -> str:
    focus_value = (custom or "").strip() if focus == "Custom" else focus
    if not focus_value:
        focus_value = "the selected single anatomical or identity detail"
    return _join(
        f"extreme close-up identity and anatomy documentation focused only on {focus_value.lower()}",
        f"{focus_value.lower()} fills most of the frame with precise local surface detail",
        "include enough immediately surrounding anatomy to confirm exact placement and orientation",
        _focus_preservation_lock_v2(),
    )


def _regional_focus_prompt_v2(region: str, custom: str) -> str:
    region_value = (custom or "").strip() if region == "Custom" else region
    if not region_value:
        region_value = "the selected anatomical region"
    return _join(
        f"close-up regional identity and anatomy documentation of {region_value.lower()}",
        f"the complete {region_value.lower()} area is visible with surrounding anatomical landmarks for context",
        "neutral documentation framing with no important edge cropped off",
        _focus_preservation_lock_v2(),
    )


class CharacterShotControlV2:
    CATEGORY = "character creation/v2"
    FUNCTION = "build_shot_plan"
    DESCRIPTION = (
        "Universal V2.1 shot control. Freestyle Controls uses every selected dropdown without requiring a full custom prompt. "
        "Body-focus controls activate only for Extreme Close-Up or Close-Up documentation shots."
    )
    RETURN_TYPES = (
        "FCC_SHOT_PLAN", "STRING", "STRING", "STRING", "STRING", "STRING",
        "STRING", "STRING", "STRING", "INT", "INT", "STRING",
    )
    RETURN_NAMES = (
        "shot_plan", "final_shot_prompt", "framing_prompt", "camera_prompt", "pose_prompt",
        "expression_prompt", "environment_prompt", "active_settings_summary", "shot_plan_json",
        "recommended_width", "recommended_height", "planner_warnings",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character_blueprint": ("CHARACTER_BLUEPRINT",),
                "planner_mode": (PLANNER_MODES_V2, {"default": "Freestyle Controls — Use All Selections"}),
                "shot_type": (SHOT_TYPES_V2, {"default": "Head and Shoulders"}),
                "camera_view": (CAMERA_VIEWS, {"default": "Front View"}),
                "camera_height": (CAMERA_HEIGHTS_V2, {"default": "Eye Level"}),
                "lens": (LENSES_V2, {"default": "85mm Portrait — Recommended"}),
                "pose": (POSES_V2, {"default": "Neutral Standing"}),
                "expression": (EXPRESSIONS_V2, {"default": "Neutral"}),
                "extreme_closeup_focus": (EXTREME_CLOSEUP_FOCUS_V2, {"default": "Complete Face"}),
                "closeup_region": (CLOSEUP_REGIONS_V2, {"default": "Face Portrait"}),
                "background": (BACKGROUNDS_V2, {"default": "Studio Solid Gray"}),
                "lighting": (LIGHTING_V2, {"default": "Soft Natural Daylight"}),
                "photo_style": (PHOTO_STYLES, {"default": "Identity Documentation"}),
                "aspect_ratio": (ASPECT_RATIOS_V2, {"default": "Portrait 4:5"}),
                "distortion_guard": (DISTORTION_GUARDS_V2, {"default": "On — Natural Rectilinear"}),
            },
            "optional": {
                "full_custom_shot_prompt": ("STRING", {"default": "", "multiline": True, "placeholder": "Only used when Planner Mode is Full Custom Shot Text"}),
                "custom_framing": ("STRING", {"default": "", "multiline": True}),
                "custom_camera": ("STRING", {"default": "", "multiline": True}),
                "custom_pose": ("STRING", {"default": "", "multiline": True}),
                "custom_expression": ("STRING", {"default": "", "multiline": False}),
                "custom_extreme_focus": ("STRING", {"default": "", "multiline": True}),
                "custom_closeup_region": ("STRING", {"default": "", "multiline": True}),
                "custom_background": ("STRING", {"default": "", "multiline": True}),
                "custom_lighting": ("STRING", {"default": "", "multiline": True}),
                "shot_suffix": ("STRING", {"default": "", "multiline": True}),
            },
        }

    def build_shot_plan(
        self, character_blueprint, planner_mode, shot_type, camera_view, camera_height, lens, pose,
        expression, extreme_closeup_focus, closeup_region, background, lighting, photo_style,
        aspect_ratio, distortion_guard, full_custom_shot_prompt="", custom_framing="",
        custom_camera="", custom_pose="", custom_expression="", custom_extreme_focus="",
        custom_closeup_region="", custom_background="", custom_lighting="", shot_suffix="",
    ):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        warnings: list[str] = []
        ignored: list[str] = []
        focus_mode = "Inactive"
        focus_region = ""

        expression_prompt = (
            custom_expression.strip() if expression == "Custom" and custom_expression.strip()
            else EXPRESSION_PROMPTS_V2.get(expression, expression.lower() + " expression")
        )
        if expression == "Custom" and not custom_expression.strip():
            warnings.append("Expression is Custom but Custom Expression is blank.")

        background_prompt = (
            custom_background.strip() if background == "Custom" and custom_background.strip()
            else BACKGROUND_PROMPTS_V2.get(background, background.lower() + " background")
        )
        lighting_prompt = (
            custom_lighting.strip() if lighting == "Custom" and custom_lighting.strip()
            else LIGHTING_PROMPTS_V2.get(lighting, lighting.lower())
        )
        environment_prompt = _join(background_prompt, lighting_prompt, photo_style.lower())

        if planner_mode == "Full Custom Shot Text":
            framing_prompt = (full_custom_shot_prompt or "").strip()
            if not framing_prompt:
                warnings.append("Full Custom Shot Text is selected but the custom shot text is blank.")
                framing_prompt = "custom camera framing and pose"
            camera_prompt = ""
            pose_prompt = ""
            ignored.extend([
                "shot type", "camera view", "camera height", "lens", "pose",
                "extreme close-up focus", "close-up region",
            ])
        else:
            if shot_type == "Extreme Close-Up — Single Detail":
                focus_mode = "Extreme Close-Up"
                focus_region = custom_extreme_focus.strip() if extreme_closeup_focus == "Custom" else extreme_closeup_focus
                if extreme_closeup_focus == "Custom" and not custom_extreme_focus.strip():
                    warnings.append("Extreme Close-Up Focus is Custom but Custom Extreme Focus is blank.")
                framing_prompt = _extreme_focus_prompt_v2(extreme_closeup_focus, custom_extreme_focus)
                ignored.append("close-up region")
            elif shot_type == "Close-Up — Regional Documentation":
                focus_mode = "Regional Close-Up"
                focus_region = custom_closeup_region.strip() if closeup_region == "Custom" else closeup_region
                if closeup_region == "Custom" and not custom_closeup_region.strip():
                    warnings.append("Close-Up Region is Custom but Custom Close-Up Region is blank.")
                framing_prompt = _regional_focus_prompt_v2(closeup_region, custom_closeup_region)
                ignored.append("extreme close-up focus")
            elif shot_type == "Custom Framing":
                framing_prompt = custom_framing.strip()
                if not framing_prompt:
                    warnings.append("Custom Framing is selected but Custom Framing is blank.")
                    framing_prompt = "custom framing"
                ignored.extend(["extreme close-up focus", "close-up region"])
            else:
                framing_prompt = SHOT_PROMPTS_V2[shot_type]
                ignored.extend(["extreme close-up focus", "close-up region"])

            view_prompt = CAMERA_PROMPTS.get(camera_view, camera_view.lower())
            height_prompt = custom_camera.strip() if camera_height == "Custom" and custom_camera.strip() else CAMERA_HEIGHT_PROMPTS_V2.get(camera_height, "")
            lens_prompt = custom_camera.strip() if lens == "Custom" and custom_camera.strip() else LENS_PROMPTS_V2.get(lens, "")
            camera_prompt = _join(view_prompt, height_prompt, lens_prompt)
            pose_prompt = custom_pose.strip() if pose == "Custom" and custom_pose.strip() else POSE_PROMPTS_V2.get(pose, pose.lower())
            if pose == "Custom" and not custom_pose.strip():
                warnings.append("Pose is Custom but Custom Pose is blank.")

        distortion_prompt = ""
        close_or_portrait = shot_type in {
            "Extreme Close-Up — Single Detail", "Close-Up — Regional Documentation",
            "Face Close-Up", "Head and Shoulders", "Chest-Up",
        }
        if distortion_guard == "On — Natural Rectilinear":
            distortion_prompt = (
                "natural rectilinear perspective with no fisheye distortion, no cramped ultra-wide framing, "
                "no oversized face or body part caused by a camera placed too close, and no unintended overhead compression"
            )
        if close_or_portrait and lens == "35mm Environmental" and planner_mode != "Full Custom Shot Text":
            warnings.append("35mm Environmental can exaggerate close subjects; 85mm or 105mm is safer for identity documentation.")
        if camera_height in {"High Angle", "Overhead"} and close_or_portrait and planner_mode != "Full Custom Shot Text":
            warnings.append("High or overhead camera angles can compress close documentation images.")
        if shot_type == "Extreme Close-Up — Single Detail" and lens not in {"85mm Portrait — Recommended", "105mm Macro", "Custom"}:
            warnings.append("Extreme Close-Up works best with 85mm or 105mm Macro to avoid feature distortion.")

        final_shot_prompt = _join(
            framing_prompt, camera_prompt, distortion_prompt, pose_prompt,
            expression_prompt, environment_prompt, shot_suffix,
        )
        width, height = _aspect_dimensions_v2(aspect_ratio)
        warning_text = " ".join(warnings)
        character_id = profile.get("character_id", "unlinked-character")
        character_gender = profile.get("gender", "Unspecified")
        presentation_mode = profile.get("presentation_mode", "Unspecified")
        summary = "\n".join([
            "UNIVERSAL SHOT CONTROL V2.1 — ACTIVE SETTINGS",
            f"Character received: {character_id}",
            f"Character gender: {character_gender}",
            f"Character presentation: {presentation_mode}",
            f"Mode: {planner_mode}",
            f"Shot type: {shot_type}",
            f"Framing: {framing_prompt}",
            f"Camera: {camera_prompt or '[defined by full custom text]'}",
            f"Pose: {pose_prompt or '[defined by full custom text]'}",
            f"Expression: {expression_prompt}",
            f"Focus mode: {focus_mode}",
            f"Focus region: {focus_region or '[inactive for this shot type]'}",
            f"Environment: {environment_prompt}",
            f"Aspect: {aspect_ratio} ({width} × {height})",
            f"Distortion guard: {distortion_guard}",
            f"Ignored controls: {', '.join(ignored) if ignored else 'None'}",
            f"Warnings: {warning_text or 'None'}",
        ])
        plan = {
            "schema": "FCC_SHOT_PLAN_V2",
            "schema_version": 3,
            "character_id": character_id,
            "character_gender": character_gender,
            "character_presentation_mode": presentation_mode,
            "planner_mode": planner_mode,
            "shot_type": shot_type,
            "camera_view": camera_view,
            "camera_height": camera_height,
            "lens": lens,
            "pose": pose,
            "expression": expression,
            "focus_mode": focus_mode,
            "focus_region": focus_region,
            "extreme_closeup_focus": extreme_closeup_focus,
            "closeup_region": closeup_region,
            "background": background,
            "lighting": lighting,
            "photo_style": photo_style,
            "aspect_ratio": aspect_ratio,
            "distortion_guard": distortion_guard,
            "framing_prompt": framing_prompt,
            "camera_prompt": camera_prompt,
            "pose_prompt": pose_prompt,
            "expression_prompt": expression_prompt,
            "environment_prompt": environment_prompt,
            "final_shot_prompt": final_shot_prompt,
            "ignored_controls": ignored,
            "warnings": warning_text,
            "recommended_width": width,
            "recommended_height": height,
            "active_settings_summary": summary,
        }
        return (
            plan, final_shot_prompt, framing_prompt, camera_prompt, pose_prompt,
            expression_prompt, environment_prompt, summary,
            json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True),
            width, height, warning_text,
        )


class CharacterPromptAssemblerV2:
    CATEGORY = "character creation/v2"
    FUNCTION = "assemble_prompt"
    DESCRIPTION = (
        "Combines the full Character Creator V2.1 blueprint with Shot Control V2.1. Freestyle Controls never requires retyping identity, anatomy, marks, or clothing."
    )
    RETURN_TYPES = (
        "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING",
        "INT", "INT", "STRING", "STRING", "STRING", "STRING", "STRING",
    )
    RETURN_NAMES = (
        "krea_prompt", "qwen_prompt", "shot_prompt", "presentation_prompt", "marks_prompt",
        "reference_required", "shot_id", "recommended_width", "recommended_height",
        "profile_character_id", "planner_notes", "active_presentation_mode",
        "active_settings_summary", "final_prompt",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character_blueprint": ("CHARACTER_BLUEPRINT",),
                "shot_plan": ("FCC_SHOT_PLAN",),
                "generation_purpose": (GENERATION_PURPOSES_V2, {"default": "Krea — First Identity Image"}),
                "reference_label": ("STRING", {"default": "Image 1", "multiline": False}),
            },
            "optional": {
                "trigger_word": ("STRING", {"default": "", "multiline": False}),
                "custom_prefix": ("STRING", {"default": "", "multiline": True}),
                "custom_suffix": ("STRING", {"default": "", "multiline": True}),
            },
        }

    def assemble_prompt(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan = shot_plan if isinstance(shot_plan, dict) else {}
        gender_authority = profile.get("gender_authority_prompt", _gender_authority_prompt_v2(profile.get("gender", "Adult Nonbinary")))
        face = profile.get("face_identity", "adult subject")
        marks = profile.get("marks_prompt", "")
        presentation = profile.get("active_presentation_prompt", profile.get("default_clothing_prompt", ""))
        body = profile.get("active_body_prompt", _join(profile.get("clothed_upper_body", ""), profile.get("clothed_lower_body", "")))
        character_id = profile.get("character_id", "character")
        presentation_mode = profile.get("presentation_mode", "Legacy / Unspecified")
        shot_prompt = plan.get("final_shot_prompt", "custom camera framing and pose")
        width = int(plan.get("recommended_width", 1024))
        height = int(plan.get("recommended_height", 1280))
        focus_region = plan.get("focus_region", "")
        warnings: list[str] = []

        qwen = generation_purpose.startswith("Qwen")
        krea = generation_purpose.startswith("Krea")
        if generation_purpose == "Qwen — Anatomy Documentation" and presentation_mode != "Clinical Anatomy":
            warnings.append("Qwen Anatomy Documentation is selected while Character Creator presentation is not Clinical Anatomy; the creator setting remains authoritative.")
        if generation_purpose == "Qwen — Clothed Action / Lifestyle" and presentation_mode != "Clothed Character":
            warnings.append("Qwen Clothed Action / Lifestyle is selected while Character Creator presentation is not Clothed Character; the creator setting remains authoritative.")

        if generation_purpose == "Krea — First Identity Image":
            purpose_prefix = "Create a realistic camera photograph of the exact adult character defined below"
            reference = "None — text-to-image"
        elif generation_purpose == "Krea — LoRA Expansion":
            purpose_prefix = "Create a realistic camera photograph using the loaded identity LoRA and the exact character specification below"
            reference = "Mini or final identity LoRA loaded in the Krea model lane"
        elif generation_purpose == "Qwen — Identity Documentation":
            purpose_prefix = _join(
                f"Edit {reference_label} into identity documentation of the same adult person",
                f"preserve the exact recognizable facial identity, hairline, skin characteristics, tattoos, piercings, and permanent marks from {reference_label}",
                "replace the old framing and pose with the current Shot Control settings",
                "follow every active Character Creator setting exactly",
            )
            reference = reference_label
        elif generation_purpose == "Qwen — Anatomy Documentation":
            purpose_prefix = _join(
                f"Edit {reference_label} into neutral adult body documentation of the same person",
                f"preserve the exact recognizable identity, body proportions, tattoos, piercings, and permanent marks from {reference_label}",
                "replace the old framing and pose with the current Shot Control settings",
                "follow every active Character Creator anatomy and presentation setting exactly",
            )
            reference = reference_label
        elif generation_purpose == "Qwen — Clothed Action / Lifestyle":
            purpose_prefix = _join(
                f"Edit {reference_label} into a realistic action or lifestyle photograph of the same adult person",
                f"preserve the exact recognizable identity and permanent markings from {reference_label}",
                "replace the old pose, framing, and wardrobe with the current Character Creator and Shot Control settings",
            )
            reference = reference_label
        else:
            purpose_prefix = _join(
                f"Edit {reference_label} into a realistic camera photograph of the same adult person",
                f"preserve the exact recognizable identity and permanent markings from {reference_label}",
                "replace the old framing, pose, and wardrobe with the current Character Creator and Shot Control settings",
            )
            reference = reference_label

        focus_lock = ""
        if focus_region:
            focus_lock = _join(
                f"documentation focus authority: {focus_region}",
                "all permanent marks and jewelry within the focused region must remain exact and readable",
            )

        final_prompt = _join(
            trigger_word if krea else "",
            custom_prefix,
            purpose_prefix,
            gender_authority,
            presentation,
            shot_prompt,
            face,
            marks,
            body,
            focus_lock,
            "keep the requested framing, camera angle, pose, expression, gender, anatomy, markings, and character presentation internally consistent",
            custom_suffix,
        )
        krea_prompt = final_prompt if krea else ""
        qwen_prompt = final_prompt if qwen else ""
        shot_id = _slug(_join(
            character_id, generation_purpose, plan.get("planner_mode", ""), plan.get("shot_type", ""),
            plan.get("focus_region", ""), plan.get("camera_view", ""), plan.get("pose", ""),
        ))
        notes = "\n".join([
            f"Purpose: {generation_purpose}",
            f"Reference: {reference}",
            "Identity/body/clothing authority: Character Creator V2.1",
            "Camera/pose/focus authority: Universal Shot Control V2.1",
            "Freestyle Controls uses all selected controls and never requires identity to be retyped.",
            f"Warnings: {' '.join(warnings) if warnings else 'None'}",
        ])
        active_summary = "\n\n".join([
            profile.get("presentation_summary", f"Presentation mode: {presentation_mode}"),
            plan.get("active_settings_summary", "Shot settings unavailable"),
            notes,
        ])
        return (
            krea_prompt, qwen_prompt, shot_prompt, presentation, marks, reference, shot_id,
            width, height, character_id, notes, presentation_mode, active_summary, final_prompt,
        )

# -----------------------------------------------------------------------------
# V2.2 architecture: conclusive, source-gated Character Creator controls.
# - Presentation mode owns whether clothing, clinical anatomy, or a custom
#   presentation is active.
# - Only the selected outfit source contributes to the prompt.
# - Tattoo and piercing counts are explicit and duplication-resistant.
# - Multiple piercings always use the descriptor list; structured piercing is
#   intentionally single-entry only.
# - Extreme close-ups are true macro/detail crops rather than context images.
# -----------------------------------------------------------------------------

PIERCING_INPUT_MODES_V22 = [
    "Descriptor List",
    "Structured Single Piercing",
]


def _mark_prompt_v22(kind: str, status: str, description: str) -> tuple[str, list[str], str, str]:
    """Build a count-locked mark prompt.

    Returns (prompt, entries, warning, count_lock).
    For status One, only the first non-empty line is authoritative; extra lines
    are explicitly ignored to keep the UI setting conclusive.
    """
    if status == "None":
        return "", [], "", f"exactly zero {kind.lower()}s anywhere on the body"

    entries = _split_lines(description)
    warnings: list[str] = []
    if not entries:
        warnings.append(f"{kind} status is {status} but no descriptor was provided.")
        return "", [], " ".join(warnings), ""

    singular = kind.lower()
    plural = singular + "s"

    if status == "One":
        if len(entries) > 1:
            warnings.append(
                f"One {singular} is selected; only the first descriptor is active and {len(entries) - 1} extra line(s) are ignored."
            )
        active = entries[:1]
        item = active[0]
        prompt = (
            f"exactly one permanent identity {singular} total on the entire body, appearing once only: {item}; "
            f"no other {plural} anywhere; do not duplicate, repeat, mirror, relocate, merge, or invent this {singular}"
        )
        count_lock = (
            f"{kind} count lock: exactly one {singular} total, one occurrence only, and zero additional {plural}"
        )
        return prompt, active, " ".join(warnings), count_lock

    # Multiple: every non-empty line is one distinct authoritative entry.
    if len(entries) < 2:
        warnings.append(
            f"Multiple {plural} is selected but fewer than two descriptor lines were supplied."
        )
    numbered = "; ".join(
        f"{singular} {i}: {entry}" for i, entry in enumerate(entries, 1)
    )
    prompt = (
        f"exactly {len(entries)} separate permanent identity {plural} total on the entire body, "
        f"one occurrence of each listed item only: {numbered}; no additional {plural}; "
        f"do not duplicate, repeat, mirror, relocate, merge, or invent any {singular}"
    )
    count_lock = (
        f"{kind} count lock: exactly {len(entries)} {plural} total, each listed item appears once, and zero additional {plural}"
    )
    return prompt, entries, " ".join(warnings), count_lock


def _structured_single_piercing_prompt_v22(
    location: str,
    piercing_type: str,
    material: str,
    visibility: str,
    custom: str,
) -> tuple[str, list[str], str, str]:
    """Build exactly one structured piercing with a strict count lock."""
    location = (location or "").strip()
    piercing_type = (piercing_type or "").strip()
    material = (material or "").strip()
    visibility = (visibility or "").strip()
    custom = (custom or "").strip()
    warnings: list[str] = []

    if not any((location, piercing_type, material, custom)):
        warnings.append("Structured Single Piercing is active but its location/type/custom description is blank.")
        return "", [], " ".join(warnings), ""
    if (location == "Other" or piercing_type == "Custom" or material == "Custom") and not custom:
        warnings.append(
            "Structured Single Piercing uses Other/Custom but Structured Piercing Custom is blank; "
            "enter the exact location and jewelry description."
        )

    if location.lower() in {"septum", "nasal septum", "center septum"}:
        placement = (
            "centered through the nasal septum in the middle area directly below the nose, "
            "not through either nostril and not on the upper lip"
        )
    else:
        placement = f"at the exact {location}" if location else "at the explicitly specified location"

    item = custom or " ".join(x for x in (material, piercing_type) if x) or "piercing jewelry"
    visibility_text = f"{visibility.lower()} visibility" if visibility else "clearly visible"
    descriptor = f"{item}, positioned {placement}, {visibility_text}"
    prompt = (
        f"exactly one permanent identity piercing total on the entire body, appearing once only: {descriptor}; "
        "no other piercings anywhere; do not duplicate, mirror, relocate, or invent piercing jewelry"
    )
    count_lock = "Piercing count lock: exactly one piercing total, one occurrence only, and zero additional piercings"
    return prompt, [descriptor], " ".join(warnings), count_lock


def _mark_anatomy_integrity_lock_v22(
    gender: str,
    tattoo_entries: list[str],
    piercing_entries: list[str],
) -> str:
    text = " ".join(tattoo_entries + piercing_entries).lower()
    locks: list[str] = []

    if any(token in text for token in ("breast", "chest", "nipple", "areola")):
        locks.append(
            "anatomy integrity: the adult subject has exactly two anatomical nipples total, one left and one right; "
            "no third or additional nipple, no duplicated areola, and no anatomy formed from a tattoo or piece of jewelry"
        )
    if tattoo_entries:
        locks.append(
            "tattoos are flat pigment within the skin only; a tattoo is never a nipple, areola, opening, wound, raised organ, or piercing jewelry"
        )
    if any("nipple" in entry.lower() for entry in piercing_entries):
        locks.append(
            "each nipple piercing passes only through the already-existing left or right anatomical nipple named in its descriptor; "
            "piercing jewelry cannot create an extra nipple or areola"
        )
    return _join(*locks)


def _focus_specific_integrity_lock_v22(focus_region: str) -> str:
    focus = (focus_region or "").lower()
    if "left nipple" in focus:
        return (
            "focus anatomy lock: show exactly one left nipple and one surrounding left areola in this crop; "
            "do not create a second left nipple, a third nipple, or a nipple inside any tattoo"
        )
    if "right nipple" in focus:
        return (
            "focus anatomy lock: show exactly one right nipple and one surrounding right areola in this crop; "
            "do not create a second right nipple, a third nipple, or a nipple inside any tattoo"
        )
    if "both nipples" in focus:
        return (
            "focus anatomy lock: show exactly two nipples total in the image, one left and one right, with one areola around each; "
            "do not create any third nipple or duplicate areola"
        )
    return ""


EXTREME_FOCUS_DETAIL_PROMPTS_V22 = {
    "Complete Face": (
        "true extreme close-up of the complete face from hairline to chin; the face occupies approximately 85 percent of the frame; "
        "crop away the shoulders and most of the neck; this is not a head-and-shoulders portrait"
    ),
    "Left Eye and Eyebrow": (
        "true macro extreme close-up of only the left eye, eyelids, eyelashes, eyebrow, and immediately surrounding skin; "
        "the selected eye region occupies approximately 80 to 90 percent of the frame; do not show the full face"
    ),
    "Right Eye and Eyebrow": (
        "true macro extreme close-up of only the right eye, eyelids, eyelashes, eyebrow, and immediately surrounding skin; "
        "the selected eye region occupies approximately 80 to 90 percent of the frame; do not show the full face"
    ),
    "Both Eyes and Nose Bridge": (
        "true macro extreme close-up containing only both eyes, both eyebrows, and the nose bridge; "
        "this eye band occupies approximately 80 to 90 percent of the frame; crop away the mouth, chin, and most of the forehead"
    ),
    "Nose and Septum": (
        "true macro extreme close-up of only the nose, nostrils, columella, septum, and immediately surrounding skin; "
        "the nose region occupies approximately 80 to 90 percent of the frame; do not show the full face"
    ),
    "Mouth and Lips": (
        "true macro extreme close-up of only the mouth, lips, philtrum, lower-nose edge, and immediately surrounding skin; "
        "the mouth region occupies approximately 80 to 90 percent of the frame; do not show the complete face"
    ),
    "Nose and Mouth": (
        "true macro extreme close-up containing only the complete nose and complete mouth from the lower nose bridge through the chin edge; "
        "the nose-and-mouth region occupies approximately 80 to 90 percent of the frame; crop away the eyes and most of the cheeks"
    ),
    "Forehead and Hairline": (
        "true macro extreme close-up of only the forehead, hairline, both temples, and eyebrows; "
        "the selected upper-face region occupies approximately 80 to 90 percent of the frame; crop away the mouth and chin"
    ),
    "Left Facial Profile": (
        "true extreme close-up of the true left facial profile from forehead and nose through lips, chin, jawline, and left ear edge; "
        "the profile occupies approximately 85 percent of the frame; no shoulders or torso"
    ),
    "Right Facial Profile": (
        "true extreme close-up of the true right facial profile from forehead and nose through lips, chin, jawline, and right ear edge; "
        "the profile occupies approximately 85 percent of the frame; no shoulders or torso"
    ),
    "Chin Jawline and Beard": (
        "true macro extreme close-up of only the lower face, moustache boundary, lips, chin, jawline, and beard density; "
        "the selected lower-face region occupies approximately 80 to 90 percent of the frame; crop away the eyes and torso"
    ),
    "Left Ear": (
        "true macro extreme close-up of only the complete left ear and immediately surrounding hairline and skin; "
        "the ear occupies approximately 80 to 90 percent of the frame"
    ),
    "Right Ear": (
        "true macro extreme close-up of only the complete right ear and immediately surrounding hairline and skin; "
        "the ear occupies approximately 80 to 90 percent of the frame"
    ),
    "Left Nipple and Areola": (
        "true macro extreme close-up of exactly one left nipple and its complete left areola; "
        "the nipple-and-areola complex occupies approximately 75 to 85 percent of the frame; show only minimal surrounding breast skin; "
        "do not show the full breast, chest, torso, face, or a context image"
    ),
    "Right Nipple and Areola": (
        "true macro extreme close-up of exactly one right nipple and its complete right areola; "
        "the nipple-and-areola complex occupies approximately 75 to 85 percent of the frame; show only minimal surrounding breast skin; "
        "do not show the full breast, chest, torso, face, or a context image"
    ),
    "Both Nipples and Chest Center": (
        "tight symmetrical close documentation crop of both nipples, both areolae, and the center chest only; "
        "the selected chest center occupies approximately 85 percent of the frame; crop away the face, abdomen, and most outer torso context"
    ),
    "Navel": (
        "true macro extreme close-up of only the navel and immediately surrounding abdominal skin; "
        "the navel region occupies approximately 75 to 85 percent of the frame; do not show the complete abdomen or torso"
    ),
    "Pubic Mons": (
        "true macro extreme close-up of only the pubic mons and immediately surrounding lower-abdominal skin in neutral clinical documentation; "
        "the selected region occupies approximately 75 to 85 percent of the frame; no full-body or broad pelvis context"
    ),
    "External Genital Anatomy": (
        "true macro extreme close-up of only the specified neutral non-aroused adult external genital anatomy and immediately surrounding skin; "
        "the selected anatomy occupies approximately 75 to 85 percent of the frame; no full-body or broad pelvis context"
    ),
    "Left Hand": (
        "true macro extreme close-up of the complete left hand from wrist through fingertips; the hand occupies approximately 85 percent of the frame"
    ),
    "Right Hand": (
        "true macro extreme close-up of the complete right hand from wrist through fingertips; the hand occupies approximately 85 percent of the frame"
    ),
    "Left Foot": (
        "true macro extreme close-up of the complete left foot from ankle through toes; the foot occupies approximately 85 percent of the frame"
    ),
    "Right Foot": (
        "true macro extreme close-up of the complete right foot from ankle through toes; the foot occupies approximately 85 percent of the frame"
    ),
}


def _extreme_focus_prompt_v22(focus: str, custom: str) -> str:
    focus_value = (custom or "").strip() if focus == "Custom" else focus
    if not focus_value:
        focus_value = "the selected single anatomical or identity detail"
    detail = EXTREME_FOCUS_DETAIL_PROMPTS_V22.get(
        focus,
        (
            f"true macro extreme close-up focused only on {focus_value.lower()}; "
            "the selected single detail occupies approximately 75 to 90 percent of the frame; "
            "do not produce a portrait, full-body image, or broad context image"
        ),
    )
    return _join(
        "macro documentation authority: one selected detail only",
        detail,
        "use close-focus macro-level magnification with sharp local surface detail and minimal surrounding context",
        "the selected detail must remain complete and uncropped even though unrelated surrounding anatomy may be cropped away",
        _focus_preservation_lock_v2(),
        _focus_specific_integrity_lock_v22(focus_value),
    )


def _regional_focus_prompt_v22(region: str, custom: str) -> str:
    region_value = (custom or "").strip() if region == "Custom" else region
    if not region_value:
        region_value = "the selected anatomical region"
    return _join(
        f"regional close-up documentation of {region_value.lower()}",
        f"the complete {region_value.lower()} region and only the immediately adjacent anatomical landmarks are visible",
        "the selected regional area occupies approximately 65 to 80 percent of the frame",
        "this is a context close-up of one region, not a full-body image and not an unrelated portrait",
        "neutral documentation framing with no important edge of the selected region cropped off",
        _focus_preservation_lock_v2(),
        _focus_specific_integrity_lock_v22(region_value),
    )


class CharacterBlueprintCreatorV22:
    CATEGORY = "character creation/v2"
    FUNCTION = "build_blueprint_v22"
    DESCRIPTION = (
        "V2.2 Character Creator with conclusive presentation/outfit/mark source controls. "
        "Inactive stored values are hidden and ignored. Tattoo and piercing counts are explicit and duplication-resistant."
    )

    RETURN_TYPES = CharacterBlueprintCreatorV2.RETURN_TYPES + ("STRING", "STRING", "STRING")
    RETURN_NAMES = CharacterBlueprintCreatorV2.RETURN_NAMES + (
        "tattoo_count_lock",
        "piercing_count_lock",
        "anatomy_integrity_lock",
    )

    @classmethod
    def INPUT_TYPES(cls):
        preset_outfits = [x for x in DEFAULT_CLOTHING if x not in {"Clinical Unclothed Documentation", "Custom"}]
        # All related controls are intentionally kept adjacent in one ordered
        # required block. The browser extension hides inactive branches.
        return {
            "required": {
                "gender": (GENDERS, {"default": "Adult Female"}),
                "age_range": (AGE_RANGES, {"default": "25–34"}),
                "heritage": (HERITAGES, {"default": "Unspecified"}),
                "custom_heritage": ("STRING", {"default": "", "multiline": False}),
                "skin_tone": (SKIN_TONES, {"default": "Medium"}),
                "complexion": (COMPLEXIONS, {"default": "Natural Skin Texture"}),
                "face_shape": (FACE_SHAPES, {"default": "Oval"}),
                "jaw_shape": (JAW_SHAPES, {"default": "Defined"}),
                "chin_shape": (CHIN_SHAPES, {"default": "Rounded"}),
                "eye_color": (EYE_COLORS, {"default": "Brown"}),
                "eye_shape": (EYE_SHAPES, {"default": "Almond"}),
                "eyebrow_shape": (EYEBROWS, {"default": "Soft Arch"}),
                "nose_shape": (NOSES, {"default": "Straight"}),
                "lip_shape": (LIPS, {"default": "Balanced Medium"}),
                "hair_color": (HAIR_COLORS, {"default": "Dark Brown"}),
                "custom_hair_color": ("STRING", {"default": "", "multiline": False}),
                "hair_length": (HAIR_LENGTHS, {"default": "Shoulder-Length"}),
                "custom_hair_length": ("STRING", {"default": "", "multiline": False}),
                "hair_texture": (HAIR_TEXTURES, {"default": "Slightly Wavy"}),
                "custom_hair_texture": ("STRING", {"default": "", "multiline": False}),
                "hair_style": (HAIR_STYLES, {"default": "Loose Natural"}),
                "custom_hair_style": ("STRING", {"default": "", "multiline": False}),
                "facial_hair": (FACIAL_HAIR, {"default": "None"}),
                "custom_facial_hair": ("STRING", {"default": "", "multiline": True}),
                "male_chest": (MALE_CHEST, {"default": "Average Male Chest"}),
                "custom_male_chest": ("STRING", {"default": "", "multiline": False}),
                "male_genital_size": (MALE_GENITAL_SIZES, {"default": "Unspecified"}),
                "height": (HEIGHTS, {"default": "Average"}),
                "body_type": (BODY_TYPES, {"default": "Average"}),
                "bust_size": (BUST_SIZES, {"default": "Unspecified"}),
                "bust_shape": (BUST_SHAPES, {"default": "Unspecified"}),
                "bust_position": (BUST_POSITIONS, {"default": "Unspecified"}),
                "bust_firmness": (BUST_FIRMNESS, {"default": "Unspecified"}),
                "bust_augmentation": (BUST_AUGMENTATION, {"default": "Unspecified"}),
                "buttocks": (BUTTOCKS, {"default": "Average"}),

                "presentation_mode": (PRESENTATION_MODES_V2, {"default": "Clothed Character"}),
                "custom_presentation_body_basis": (CUSTOM_BODY_BASES_V2, {"default": "Clothed Silhouette"}),
                "custom_presentation_prompt": ("STRING", {"default": "", "multiline": True}),

                "outfit_source": (OUTFIT_SOURCES_V2, {"default": "Exact Outfit Text"}),
                "outfit_preset": (preset_outfits, {"default": "Casual Jeans and T-Shirt"}),
                "exact_outfit_text": ("STRING", {"default": "casual fitted T-shirt, well-fitted jeans, and casual sneakers", "multiline": True}),
                "structured_outfit_type": (STRUCTURED_OUTFIT_TYPES_V2, {"default": "Complete Outfit"}),
                "structured_top": ("STRING", {"default": "", "multiline": False}),
                "structured_bottom": ("STRING", {"default": "", "multiline": False}),
                "structured_footwear": ("STRING", {"default": "", "multiline": False}),
                "structured_outerwear": ("STRING", {"default": "", "multiline": False}),
                "structured_one_piece": ("STRING", {"default": "", "multiline": False}),
                "structured_swimwear_top": ("STRING", {"default": "", "multiline": False}),
                "structured_swimwear_bottom": ("STRING", {"default": "", "multiline": False}),
                "lingerie_style": (LINGERIE_STYLES_V2, {"default": "Matching Bra and Brief Set"}),
                "custom_lingerie_description": ("STRING", {"default": "", "multiline": True}),
                "outfit_notes": ("STRING", {"default": "", "multiline": True}),

                "jewelry_level": (JEWELRY_LEVELS, {"default": "Minimal"}),
                "jewelry_description": ("STRING", {"default": "", "multiline": True}),

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
                "lower_body_notes": ("STRING", {"default": "", "multiline": True}),
            }
        }

    def build_blueprint_v22(
        self,
        gender, age_range, heritage, custom_heritage, skin_tone, complexion, face_shape, jaw_shape,
        chin_shape, eye_color, eye_shape, eyebrow_shape, nose_shape, lip_shape, hair_color,
        custom_hair_color, hair_length, custom_hair_length, hair_texture, custom_hair_texture,
        hair_style, custom_hair_style, facial_hair, custom_facial_hair, male_chest,
        custom_male_chest, male_genital_size, height, body_type, bust_size, bust_shape,
        bust_position, bust_firmness, bust_augmentation, buttocks, presentation_mode,
        custom_presentation_body_basis, custom_presentation_prompt, outfit_source, outfit_preset,
        exact_outfit_text, structured_outfit_type, structured_top, structured_bottom,
        structured_footwear, structured_outerwear, structured_one_piece, structured_swimwear_top,
        structured_swimwear_bottom, lingerie_style, custom_lingerie_description, outfit_notes,
        jewelry_level, jewelry_description, tattoo_status, tattoo_descriptors, piercing_status,
        piercing_input_mode, piercing_descriptors, piercing_location, piercing_type,
        piercing_material, piercing_visibility, structured_piercing_custom, custom_identity_notes,
        lower_body_notes,
    ):
        # Generate base identity/body branches with all mark and wardrobe fields
        # disabled. V2.2 then applies its own authoritative source-gated logic.
        base = CharacterBlueprintCreator().build_blueprint(
            gender=gender, age_range=age_range, heritage=heritage, skin_tone=skin_tone,
            complexion=complexion, face_shape=face_shape, jaw_shape=jaw_shape, chin_shape=chin_shape,
            eye_color=eye_color, eye_shape=eye_shape, eyebrow_shape=eyebrow_shape,
            nose_shape=nose_shape, lip_shape=lip_shape, hair_color=hair_color,
            hair_length=hair_length, hair_texture=hair_texture, hair_style=hair_style,
            height=height, body_type=body_type, bust_size=bust_size, bust_shape=bust_shape,
            bust_position=bust_position, bust_firmness=bust_firmness,
            bust_augmentation=bust_augmentation, buttocks=buttocks,
            default_clothing=outfit_preset, jewelry_level="None",
            tattoo_status="None", piercing_status="None",
            custom_heritage=custom_heritage, custom_hair_color=custom_hair_color,
            custom_hair_length=custom_hair_length, custom_hair_texture=custom_hair_texture,
            custom_hair_style=custom_hair_style, jewelry_description="",
            tattoo_descriptors="", piercing_descriptors="",
            lower_body_notes=lower_body_notes, custom_identity_notes=custom_identity_notes,
            piercing_location="", piercing_type="", piercing_material="",
            piercing_visibility="", structured_piercing_custom="",
            facial_hair=facial_hair, custom_facial_hair=custom_facial_hair,
            male_chest=male_chest, custom_male_chest=custom_male_chest,
            male_genital_size=male_genital_size,
        )
        profile = dict(base[8])
        gender_authority = _gender_authority_prompt_v2(gender)
        identity_detail_prompt = base[0]
        face_identity = _join(gender_authority, identity_detail_prompt)
        anatomy_upper = base[11]
        anatomy_lower = base[13]
        clothed_upper = base[10]
        clothed_lower = base[12]
        bust_prompt = base[3]

        tattoo_prompt, tattoo_entries, tattoo_warning, tattoo_count_lock = _mark_prompt_v22(
            "Tattoo", tattoo_status, tattoo_descriptors
        )

        piercing_warnings: list[str] = []
        if piercing_status == "None":
            piercing_prompt, piercing_entries, piercing_warning, piercing_count_lock = (
                "", [], "", "exactly zero piercings anywhere on the body"
            )
        elif piercing_status == "Multiple":
            # Multiple is conclusively descriptor-list based. Structured values
            # are ignored even if old serialized values remain populated.
            piercing_prompt, piercing_entries, piercing_warning, piercing_count_lock = _mark_prompt_v22(
                "Piercing", "Multiple", piercing_descriptors
            )
            if piercing_input_mode == "Structured Single Piercing" or any(
                (piercing_location, piercing_type, piercing_material, structured_piercing_custom)
            ):
                piercing_warnings.append(
                    "Multiple piercings uses Descriptor List only; all structured single-piercing fields are ignored."
                )
        elif piercing_input_mode == "Structured Single Piercing":
            piercing_prompt, piercing_entries, piercing_warning, piercing_count_lock = _structured_single_piercing_prompt_v22(
                piercing_location, piercing_type, piercing_material,
                piercing_visibility, structured_piercing_custom,
            )
            if (piercing_descriptors or "").strip():
                piercing_warnings.append(
                    "Structured Single Piercing is active; Piercing Descriptors is ignored."
                )
        else:
            piercing_prompt, piercing_entries, piercing_warning, piercing_count_lock = _mark_prompt_v22(
                "Piercing", "One", piercing_descriptors
            )
            if any((piercing_location, piercing_type, piercing_material, structured_piercing_custom)):
                piercing_warnings.append(
                    "Descriptor List is active; structured single-piercing fields are ignored."
                )

        marks_prompt = _join(tattoo_prompt, piercing_prompt)
        anatomy_integrity_lock = _mark_anatomy_integrity_lock_v22(
            gender, tattoo_entries, piercing_entries
        )

        outfit_prompt, outfit_components, outfit_warnings = _build_authoritative_outfit_v2(
            outfit_source, outfit_preset, exact_outfit_text, structured_outfit_type,
            lingerie_style, structured_top, structured_bottom, structured_footwear,
            structured_outerwear, structured_one_piece, structured_swimwear_top,
            structured_swimwear_bottom, custom_lingerie_description, outfit_notes,
        )
        jewelry_prompt = "" if jewelry_level == "None" else _join(
            f"{jewelry_level.lower()} removable jewelry", jewelry_description
        )
        clothed_presentation = _join(outfit_prompt, jewelry_prompt)
        clinical_presentation = (
            "unclothed adult subject in neutral non-aroused clinical anatomy documentation; "
            "only the explicitly documented permanent identity piercings remain; all removable jewelry and clothing are absent"
        )

        warnings_list: list[str] = []
        warnings_list.extend(outfit_warnings)
        for item in (tattoo_warning, piercing_warning, *piercing_warnings):
            if item:
                warnings_list.append(item)
        if gender == "Adult Male" and any(
            x != "Unspecified" for x in
            (bust_size, bust_shape, bust_position, bust_firmness, bust_augmentation)
        ):
            warnings_list.append(
                "Adult Male is selected; all female bust controls are hidden, ignored, and excluded from every generated prompt."
            )
        if gender != "Adult Male" and facial_hair not in {"None", "Clean-Shaven"}:
            warnings_list.append(
                "Facial Hair is only authoritative for Adult Male in this version."
            )

        custom_presentation_prompt = (custom_presentation_prompt or "").strip()
        inactive_summary: list[str] = []
        if presentation_mode == "Clinical Anatomy":
            active_presentation = clinical_presentation
            active_body = _join(anatomy_upper, anatomy_lower)
            inactive_summary.extend([
                "Outfit Source", "Outfit Preset", "Exact Outfit Text",
                "Structured Outfit Type", "Lingerie Style", "Removable Jewelry",
                "Custom Presentation Prompt", "Custom Presentation Body Basis",
            ])
        elif presentation_mode == "Custom Presentation":
            active_presentation = custom_presentation_prompt
            if not active_presentation:
                warnings_list.append(
                    "Presentation Mode is Custom Presentation but Custom Presentation Prompt is blank."
                )
            if custom_presentation_body_basis == "Clinical Anatomy":
                active_body = _join(anatomy_upper, anatomy_lower)
            elif custom_presentation_body_basis == "Identity Only":
                active_body = ""
            else:
                active_body = _join(clothed_upper, clothed_lower)
            inactive_summary.extend([
                "Outfit Source", "Outfit Preset", "Exact Outfit Text",
                "Structured Outfit Type", "Lingerie Style", "Removable Jewelry",
            ])
        else:
            active_presentation = clothed_presentation
            active_body = _join(clothed_upper, clothed_lower)
            if not outfit_prompt:
                warnings_list.append(
                    "Clothed Character is selected but no authoritative outfit prompt was produced."
                )
            inactive_summary.extend([
                "Custom Presentation Prompt", "Custom Presentation Body Basis",
            ])

        # Use gender exactly once in the profile. The V2.2 assembler consumes
        # identity_detail_prompt separately to avoid the old duplicated lock.
        active_character = _join(
            gender_authority, active_presentation, identity_detail_prompt,
            marks_prompt, active_body, tattoo_count_lock, piercing_count_lock,
            anatomy_integrity_lock,
        )
        clothed_character = _join(
            gender_authority, clothed_presentation, identity_detail_prompt,
            marks_prompt, clothed_upper, clothed_lower, tattoo_count_lock,
            piercing_count_lock, anatomy_integrity_lock,
        )
        clinical_character = _join(
            gender_authority, clinical_presentation, identity_detail_prompt,
            marks_prompt, anatomy_upper, anatomy_lower, tattoo_count_lock,
            piercing_count_lock, anatomy_integrity_lock,
        )

        identity_hash_source = _join(
            gender_authority, identity_detail_prompt, marks_prompt,
            anatomy_upper, anatomy_lower,
        )
        stable_base = _join(gender, age_range, heritage, face_shape, hair_color, body_type)
        character_id = _slug(stable_base) + "_" + hashlib.sha1(
            identity_hash_source.encode("utf-8")
        ).hexdigest()[:8]
        warnings = " ".join(x.strip() for x in warnings_list if x and x.strip())

        if presentation_mode != "Clothed Character":
            active_outfit_summary = "[inactive — presentation mode does not use outfit controls]"
        elif outfit_source == "Preset Outfit":
            active_outfit_summary = f"Preset Outfit → {outfit_preset}"
        elif outfit_source == "Exact Outfit Text":
            active_outfit_summary = f"Exact Outfit Text → {exact_outfit_text or '[blank]'}"
        elif structured_outfit_type == "Lingerie Set":
            active_outfit_summary = f"Structured Components → Lingerie Set → {lingerie_style}"
        else:
            active_outfit_summary = f"Structured Components → {structured_outfit_type}"

        if piercing_status == "None":
            active_piercing_summary = "None — all piercing entry controls inactive"
        elif piercing_status == "Multiple":
            active_piercing_summary = f"Multiple → Descriptor List → {len(piercing_entries)} active entries"
        else:
            active_piercing_summary = f"One → {piercing_input_mode} → {len(piercing_entries)} active entry"

        presentation_summary = "\n".join([
            "CHARACTER CREATOR V2.2 — CONCLUSIVE ACTIVE AUTHORITY",
            f"Gender lock: {gender_authority}",
            f"Presentation Mode: {presentation_mode}",
            f"Active Presentation: {active_presentation or '[blank]'}",
            f"Active Body Basis: {active_body or '[identity only]'}",
            f"Active Outfit Path: {active_outfit_summary}",
            f"Tattoo Path: {tattoo_status} → {len(tattoo_entries)} active descriptor(s)",
            f"Piercing Path: {active_piercing_summary}",
            f"Tattoo Count Lock: {tattoo_count_lock or '[not available]'}",
            f"Piercing Count Lock: {piercing_count_lock or '[not available]'}",
            f"Anatomy Integrity Lock: {anatomy_integrity_lock or '[not required]'}",
            f"Inactive stored controls ignored: {', '.join(inactive_summary) if inactive_summary else 'None'}",
            f"Warnings: {warnings or 'None'}",
        ])

        profile.update({
            "schema": "CHARACTER_BLUEPRINT_V22",
            "schema_version": 6,
            "character_id": character_id,
            "gender": gender,
            "gender_authority_prompt": gender_authority,
            "identity_detail_prompt": identity_detail_prompt,
            "face_identity": face_identity,
            "presentation_mode": presentation_mode,
            "outfit_source": outfit_source,
            "outfit_preset": outfit_preset,
            "structured_outfit_type": structured_outfit_type,
            "lingerie_style": lingerie_style,
            "custom_presentation_body_basis": custom_presentation_body_basis,
            "outfit_components": outfit_components,
            "structured_outfit_prompt": outfit_prompt,
            "default_clothing_prompt": clothed_presentation,
            "active_presentation_prompt": active_presentation,
            "active_body_prompt": active_body,
            "active_character_prompt": active_character,
            "clothed_character_prompt": clothed_character,
            "clinical_character_prompt": clinical_character,
            "full_profile_prompt": active_character,
            "marks_prompt": marks_prompt,
            "tattoo_status": tattoo_status,
            "tattoo_entries": tattoo_entries,
            "tattoo_count_lock": tattoo_count_lock,
            "piercing_status": piercing_status,
            "piercing_input_mode": piercing_input_mode,
            "piercing_entries": piercing_entries,
            "piercing_count_lock": piercing_count_lock,
            "anatomy_integrity_lock": anatomy_integrity_lock,
            "warnings": warnings,
            "presentation_summary": presentation_summary,
        })
        blueprint_json = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        return (
            face_identity, anatomy_upper, anatomy_lower, bust_prompt, marks_prompt,
            clothed_presentation, active_character, character_id, profile, warnings,
            clothed_upper, anatomy_upper, clothed_lower, anatomy_lower,
            outfit_prompt, blueprint_json, active_presentation, active_body,
            active_character, clothed_character, clinical_character, presentation_summary,
            tattoo_count_lock, piercing_count_lock, anatomy_integrity_lock,
        )


class CharacterShotControlV22(CharacterShotControlV2):
    CATEGORY = "character creation/v2"
    FUNCTION = "build_shot_plan_v22"
    DESCRIPTION = (
        "Universal V2.2 shot control. Extreme Close-Up is a true macro/detail crop, not a context image. "
        "Pose is ignored for extreme single-detail crops and focus controls remain source-gated."
    )

    def build_shot_plan_v22(
        self, character_blueprint, planner_mode, shot_type, camera_view, camera_height, lens, pose,
        expression, extreme_closeup_focus, closeup_region, background, lighting, photo_style,
        aspect_ratio, distortion_guard, full_custom_shot_prompt="", custom_framing="",
        custom_camera="", custom_pose="", custom_expression="", custom_extreme_focus="",
        custom_closeup_region="", custom_background="", custom_lighting="", shot_suffix="",
    ):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        warnings: list[str] = []
        ignored: list[str] = []
        focus_mode = "Inactive"
        focus_region = ""

        expression_prompt = (
            custom_expression.strip() if expression == "Custom" and custom_expression.strip()
            else EXPRESSION_PROMPTS_V2.get(expression, expression.lower() + " expression")
        )
        if expression == "Custom" and not custom_expression.strip():
            warnings.append("Expression is Custom but Custom Expression is blank.")

        background_prompt = (
            custom_background.strip() if background == "Custom" and custom_background.strip()
            else BACKGROUND_PROMPTS_V2.get(background, background.lower() + " background")
        )
        lighting_prompt = (
            custom_lighting.strip() if lighting == "Custom" and custom_lighting.strip()
            else LIGHTING_PROMPTS_V2.get(lighting, lighting.lower())
        )
        environment_prompt = _join(background_prompt, lighting_prompt, photo_style.lower())

        extreme = planner_mode != "Full Custom Shot Text" and shot_type == "Extreme Close-Up — Single Detail"
        regional = planner_mode != "Full Custom Shot Text" and shot_type == "Close-Up — Regional Documentation"

        if planner_mode == "Full Custom Shot Text":
            framing_prompt = (full_custom_shot_prompt or "").strip()
            if not framing_prompt:
                warnings.append("Full Custom Shot Text is selected but the custom shot text is blank.")
                framing_prompt = "custom camera framing and pose"
            camera_prompt = ""
            pose_prompt = ""
            ignored.extend([
                "shot type", "camera view", "camera height", "lens", "pose",
                "extreme close-up focus", "close-up region",
            ])
        else:
            if extreme:
                focus_mode = "Extreme Close-Up"
                focus_region = custom_extreme_focus.strip() if extreme_closeup_focus == "Custom" else extreme_closeup_focus
                if extreme_closeup_focus == "Custom" and not custom_extreme_focus.strip():
                    warnings.append("Extreme Close-Up Focus is Custom but Custom Extreme Focus is blank.")
                framing_prompt = _extreme_focus_prompt_v22(extreme_closeup_focus, custom_extreme_focus)
                ignored.extend(["close-up region", "pose"])
            elif regional:
                focus_mode = "Regional Close-Up"
                focus_region = custom_closeup_region.strip() if closeup_region == "Custom" else closeup_region
                if closeup_region == "Custom" and not custom_closeup_region.strip():
                    warnings.append("Close-Up Region is Custom but Custom Close-Up Region is blank.")
                framing_prompt = _regional_focus_prompt_v22(closeup_region, custom_closeup_region)
                ignored.append("extreme close-up focus")
            elif shot_type == "Custom Framing":
                framing_prompt = custom_framing.strip()
                if not framing_prompt:
                    warnings.append("Custom Framing is selected but Custom Framing is blank.")
                    framing_prompt = "custom framing"
                ignored.extend(["extreme close-up focus", "close-up region"])
            else:
                framing_prompt = SHOT_PROMPTS_V2[shot_type]
                ignored.extend(["extreme close-up focus", "close-up region"])

            view_prompt = CAMERA_PROMPTS.get(camera_view, camera_view.lower())
            height_prompt = custom_camera.strip() if camera_height == "Custom" and custom_camera.strip() else CAMERA_HEIGHT_PROMPTS_V2.get(camera_height, "")
            lens_prompt = custom_camera.strip() if lens == "Custom" and custom_camera.strip() else LENS_PROMPTS_V2.get(lens, "")
            if extreme:
                lens_prompt = _join(
                    lens_prompt,
                    "macro close-focus magnification with the camera positioned far enough away to avoid perspective enlargement",
                )
            camera_prompt = _join(view_prompt, height_prompt, lens_prompt)
            if extreme:
                pose_prompt = ""
            else:
                pose_prompt = custom_pose.strip() if pose == "Custom" and custom_pose.strip() else POSE_PROMPTS_V2.get(pose, pose.lower())
                if pose == "Custom" and not custom_pose.strip():
                    warnings.append("Pose is Custom but Custom Pose is blank.")

        distortion_prompt = ""
        close_or_portrait = shot_type in {
            "Extreme Close-Up — Single Detail", "Close-Up — Regional Documentation",
            "Face Close-Up", "Head and Shoulders", "Chest-Up",
        }
        if distortion_guard == "On — Natural Rectilinear":
            distortion_prompt = (
                "natural rectilinear perspective with no fisheye distortion, no cramped ultra-wide framing, "
                "no oversized face or body part caused by perspective distortion, and no unintended overhead compression"
            )
        if close_or_portrait and lens == "35mm Environmental" and planner_mode != "Full Custom Shot Text":
            warnings.append("35mm Environmental can exaggerate close subjects; 85mm or 105mm is safer for identity documentation.")
        if camera_height in {"High Angle", "Overhead"} and close_or_portrait and planner_mode != "Full Custom Shot Text":
            warnings.append("High or overhead camera angles can compress close documentation images.")
        if extreme and lens not in {"85mm Portrait — Recommended", "105mm Macro", "Custom"}:
            warnings.append("Extreme Close-Up works best with 85mm or 105mm Macro to avoid feature distortion.")
        if extreme and lens != "105mm Macro":
            warnings.append("For the tightest true macro crop, select 105mm Macro; V2.2 still adds macro close-focus authority to the current lens.")

        # Expression is useful for facial extreme close-ups but unrelated to
        # body-part macro documentation. Ignore it for non-facial detail crops.
        facial_focus_tokens = (
            "face", "eye", "eyebrow", "nose", "septum", "mouth", "lip",
            "forehead", "hairline", "chin", "jawline", "beard", "ear",
        )
        if extreme and focus_region and not any(token in focus_region.lower() for token in facial_focus_tokens):
            expression_for_prompt = ""
            ignored.append("expression")
        else:
            expression_for_prompt = expression_prompt

        final_shot_prompt = _join(
            framing_prompt, camera_prompt, distortion_prompt, pose_prompt,
            expression_for_prompt, environment_prompt, shot_suffix,
        )
        width, height = _aspect_dimensions_v2(aspect_ratio)
        warning_text = " ".join(warnings)
        character_id = profile.get("character_id", "unlinked-character")
        character_gender = profile.get("gender", "Unspecified")
        presentation_mode = profile.get("presentation_mode", "Unspecified")
        summary = "\n".join([
            "UNIVERSAL SHOT CONTROL V2.2 — ACTIVE SETTINGS",
            f"Character received: {character_id}",
            f"Character gender: {character_gender}",
            f"Character presentation: {presentation_mode}",
            f"Mode: {planner_mode}",
            f"Shot type: {shot_type}",
            f"Framing: {framing_prompt}",
            f"Camera: {camera_prompt or '[defined by full custom text]'}",
            f"Pose: {pose_prompt or '[inactive/defined by custom text]'}",
            f"Expression: {expression_for_prompt or '[inactive for this focus]'}",
            f"Focus mode: {focus_mode}",
            f"Focus region: {focus_region or '[inactive for this shot type]'}",
            f"Environment: {environment_prompt}",
            f"Aspect: {aspect_ratio} ({width} × {height})",
            f"Distortion guard: {distortion_guard}",
            f"Ignored controls: {', '.join(ignored) if ignored else 'None'}",
            f"Warnings: {warning_text or 'None'}",
        ])
        plan = {
            "schema": "FCC_SHOT_PLAN_V22",
            "schema_version": 4,
            "character_id": character_id,
            "character_gender": character_gender,
            "character_presentation_mode": presentation_mode,
            "planner_mode": planner_mode,
            "shot_type": shot_type,
            "camera_view": camera_view,
            "camera_height": camera_height,
            "lens": lens,
            "pose": pose,
            "expression": expression,
            "focus_mode": focus_mode,
            "focus_region": focus_region,
            "extreme_closeup_focus": extreme_closeup_focus,
            "closeup_region": closeup_region,
            "background": background,
            "lighting": lighting,
            "photo_style": photo_style,
            "aspect_ratio": aspect_ratio,
            "distortion_guard": distortion_guard,
            "framing_prompt": framing_prompt,
            "camera_prompt": camera_prompt,
            "pose_prompt": pose_prompt,
            "expression_prompt": expression_for_prompt,
            "environment_prompt": environment_prompt,
            "final_shot_prompt": final_shot_prompt,
            "ignored_controls": ignored,
            "warnings": warning_text,
            "recommended_width": width,
            "recommended_height": height,
            "active_settings_summary": summary,
        }
        return (
            plan, final_shot_prompt, framing_prompt, camera_prompt, pose_prompt,
            expression_for_prompt, environment_prompt, summary,
            json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True),
            width, height, warning_text,
        )


class CharacterPromptAssemblerV22(CharacterPromptAssemblerV2):
    CATEGORY = "character creation/v2"
    FUNCTION = "assemble_prompt_v22"
    DESCRIPTION = (
        "V2.2 assembler. Uses one gender authority statement, exact mark-count locks, anatomy-integrity locks, "
        "and true macro focus authority without duplicating the Character Creator gender prompt."
    )

    def assemble_prompt_v22(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan = shot_plan if isinstance(shot_plan, dict) else {}
        gender_authority = profile.get(
            "gender_authority_prompt",
            _gender_authority_prompt_v2(profile.get("gender", "Adult Nonbinary")),
        )
        identity_details = profile.get("identity_detail_prompt") or profile.get("face_identity", "adult subject")
        # Remove a serialized leading gender authority from legacy face identity
        # to prevent duplicate statements if a V2.1 blueprint is connected.
        if identity_details.startswith(gender_authority):
            identity_details = identity_details[len(gender_authority):].lstrip(" ,;")

        marks = profile.get("marks_prompt", "")
        presentation = profile.get("active_presentation_prompt", profile.get("default_clothing_prompt", ""))
        body = profile.get(
            "active_body_prompt",
            _join(profile.get("clothed_upper_body", ""), profile.get("clothed_lower_body", "")),
        )
        tattoo_count_lock = profile.get("tattoo_count_lock", "")
        piercing_count_lock = profile.get("piercing_count_lock", "")
        anatomy_integrity_lock = profile.get("anatomy_integrity_lock", "")
        character_id = profile.get("character_id", "character")
        presentation_mode = profile.get("presentation_mode", "Legacy / Unspecified")
        shot_prompt = plan.get("final_shot_prompt", "custom camera framing and pose")
        width = int(plan.get("recommended_width", 1024))
        height = int(plan.get("recommended_height", 1280))
        focus_region = plan.get("focus_region", "")
        warnings: list[str] = []

        qwen = generation_purpose.startswith("Qwen")
        krea = generation_purpose.startswith("Krea")
        if generation_purpose == "Qwen — Anatomy Documentation" and presentation_mode != "Clinical Anatomy":
            warnings.append(
                "Qwen Anatomy Documentation is selected while Character Creator presentation is not Clinical Anatomy; the creator setting remains authoritative."
            )
        if generation_purpose == "Qwen — Clothed Action / Lifestyle" and presentation_mode != "Clothed Character":
            warnings.append(
                "Qwen Clothed Action / Lifestyle is selected while Character Creator presentation is not Clothed Character; the creator setting remains authoritative."
            )

        if generation_purpose == "Krea — First Identity Image":
            purpose_prefix = "Create a realistic camera photograph of the exact adult character defined below"
            reference = "None — text-to-image"
        elif generation_purpose == "Krea — LoRA Expansion":
            purpose_prefix = "Create a realistic camera photograph using the loaded identity LoRA and the exact character specification below"
            reference = "Mini or final identity LoRA loaded in the Krea model lane"
        elif generation_purpose == "Qwen — Identity Documentation":
            purpose_prefix = _join(
                f"Edit {reference_label} into identity documentation of the same adult person",
                f"preserve the exact recognizable facial identity, hairline, skin characteristics, tattoos, piercings, and permanent marks from {reference_label}",
                "replace the old framing and pose with the current Shot Control settings",
                "follow every active Character Creator setting exactly",
            )
            reference = reference_label
        elif generation_purpose == "Qwen — Anatomy Documentation":
            purpose_prefix = _join(
                f"Edit {reference_label} into neutral adult body documentation of the same person",
                f"preserve the exact recognizable identity, body proportions, tattoos, piercings, and permanent marks from {reference_label}",
                "replace the old framing and pose with the current Shot Control settings",
                "follow every active Character Creator anatomy and presentation setting exactly",
            )
            reference = reference_label
        elif generation_purpose == "Qwen — Clothed Action / Lifestyle":
            purpose_prefix = _join(
                f"Edit {reference_label} into a realistic action or lifestyle photograph of the same adult person",
                f"preserve the exact recognizable identity and permanent markings from {reference_label}",
                "replace the old pose, framing, and wardrobe with the current Character Creator and Shot Control settings",
            )
            reference = reference_label
        else:
            purpose_prefix = _join(
                f"Edit {reference_label} into a realistic camera photograph of the same adult person",
                f"preserve the exact recognizable identity and permanent markings from {reference_label}",
                "replace the old framing, pose, and wardrobe with the current Character Creator and Shot Control settings",
            )
            reference = reference_label

        focus_lock = ""
        if focus_region:
            focus_lock = _join(
                f"documentation focus authority: {focus_region}",
                "all permanent marks and jewelry within the focused region must remain exact and readable",
                _focus_specific_integrity_lock_v22(focus_region),
            )

        final_prompt = _join(
            trigger_word if krea else "",
            custom_prefix,
            purpose_prefix,
            gender_authority,
            presentation,
            shot_prompt,
            identity_details,
            marks,
            body,
            tattoo_count_lock,
            piercing_count_lock,
            anatomy_integrity_lock,
            focus_lock,
            "keep the requested framing, camera angle, pose, expression, gender, anatomy, markings, and character presentation internally consistent",
            custom_suffix,
        )
        krea_prompt = final_prompt if krea else ""
        qwen_prompt = final_prompt if qwen else ""
        shot_id = _slug(_join(
            character_id, generation_purpose, plan.get("planner_mode", ""),
            plan.get("shot_type", ""), plan.get("focus_region", ""),
            plan.get("camera_view", ""), plan.get("pose", ""),
        ))
        notes = "\n".join([
            f"Purpose: {generation_purpose}",
            f"Reference: {reference}",
            "Identity/body/clothing authority: Character Creator V2.2",
            "Camera/pose/focus authority: Universal Shot Control V2.2",
            "Inactive Character Creator branches are hidden and ignored.",
            "Extreme Close-Up uses macro/detail crop authority rather than regional context framing.",
            f"Warnings: {' '.join(warnings) if warnings else 'None'}",
        ])
        active_summary = "\n\n".join([
            profile.get("presentation_summary", f"Presentation mode: {presentation_mode}"),
            plan.get("active_settings_summary", "Shot settings unavailable"),
            notes,
        ])
        return (
            krea_prompt, qwen_prompt, shot_prompt, presentation, marks, reference, shot_id,
            width, height, character_id, notes, presentation_mode, active_summary, final_prompt,
        )


# ---------------------------------------------------------------------------
# V2.2.1 body-proportion and clothed-bust authority patch
# ---------------------------------------------------------------------------

BODY_TYPE_AUTHORITY_PROMPTS_V221 = {
    "Very Slim": (
        "body-proportion authority: a distinctly very slim adult build with narrow shoulders, a narrow torso, "
        "a small waist, slim hips, slender arms, and slender legs; preserve this clearly low-mass silhouette "
        "independently of clothing and do not normalize it toward an average build"
    ),
    "Slim": (
        "body-proportion authority: a clearly slim adult build with lean shoulders, a lean torso, a defined narrow waist, "
        "slim hips, and lean limbs; preserve the selected slim silhouette independently of clothing"
    ),
    "Average": (
        "body-proportion authority: an ordinary average adult build with balanced shoulders, torso, waist, hips, arms, "
        "and legs; neither unusually slim, muscular, curvy, full-figured, nor heavyset"
    ),
    "Athletic": (
        "body-proportion authority: a clearly athletic adult build with visibly trained shoulders and upper arms, "
        "a firm athletic torso, a defined waist, athletic hips and thighs, and moderate realistic muscle definition; "
        "the athletic build must remain visible through the outfit and must not collapse into a generic average or purely curvy silhouette"
    ),
    "Curvy": (
        "body-proportion authority: a distinctly curvy adult build with a clearly defined waist and visibly fuller bust, "
        "hips, and thighs in balanced proportion; preserve the selected hourglass or curving silhouette through clothing"
    ),
    "Full-Figured": (
        "body-proportion authority: a clearly full-figured adult build with substantial natural body volume across the torso, "
        "waist, hips, thighs, and limbs; preserve realistic weight distribution and do not normalize the body to average"
    ),
    "Muscular": (
        "body-proportion authority: a distinctly muscular adult build with broad trained shoulders, visibly developed arms, "
        "defined chest and torso musculature, a strong waist, muscular hips, thighs, and calves; preserve muscular development "
        "independently of clothing"
    ),
    "Heavyset": (
        "body-proportion authority: a clearly heavyset adult build with substantial body mass, a broad torso and waist, "
        "full hips and thighs, and realistically heavier arms and legs; preserve the selected heavyset proportions and do not slim the subject"
    ),
}

CLOTHED_BUST_SIZE_AUTHORITY_V221 = {
    "Very Small": "very-small bust silhouette with minimal chest projection and clearly low garment volume, visibly smaller than the Small setting",
    "Small": "small bust silhouette with gentle low-volume projection, clearly smaller than Medium",
    "Small-Medium": "small-to-medium bust silhouette with modest projection between the Small and Medium settings",
    "Medium": "clearly medium bust silhouette with balanced visible projection, distinctly fuller than Small and distinctly less full than Full",
    "Medium-Full": "medium-full bust silhouette with clearly noticeable projection and volume while remaining below the Full setting",
    "Full": "full bust silhouette with pronounced visible volume and forward projection through the garment",
    "Large": "large bust silhouette with substantial visible volume, broad garment contour, and strong forward projection",
    "Very Large": "very-large bust silhouette with heavy visible volume, substantial garment displacement, and strong projection",
    "Overly Large": "extremely large bust silhouette with unmistakably exaggerated volume, strong projection, and substantial natural weight",
}

CLOTHED_BUST_SHAPE_AUTHORITY_V221 = {
    "Bell Shape": "garment contour showing a narrower upper pole and distinctly fuller rounded lower-bust curve",
    "Teardrop": "garment contour showing a gentle upper slope and naturally fuller lower-bust curve",
    "Round": "garment contour showing balanced upper-pole and lower-pole fullness with a rounded profile",
    "Asymmetrical Natural": "garment contour preserving subtle realistic left-right asymmetry rather than perfectly mirrored volume",
    "East-West": "garment contour showing the bust projecting slightly outward toward both sides",
    "Side-Set": "garment contour showing a wider natural center gap and fuller outer-chest placement",
    "Slender": "garment contour showing a narrow base and elongated gentle vertical profile",
}

CLOTHED_BUST_POSITION_AUTHORITY_V221 = {
    "Natural Average-Set": "natural average-set placement at an ordinary adult chest height",
    "High-Set / Perky": "clearly high-set placement with visible upward presentation",
    "High and Tight": "high and compact placement with minimal lower drop",
    "Low-Set": "clearly low-set placement with realistic gravitational weight",
    "Downward-Sloping": "downward-sloping placement with visible lower-pole weight",
    "Pendulous Natural": "naturally pendulous lower-set placement with visible gravitational drop and lower fullness",
}

CLOTHED_BUST_FIRMNESS_AUTHORITY_V221 = {
    "Firm": "firm stable garment contour with minimal settling",
    "Naturally Firm": "naturally firm contour with stable shape and slight realistic softness",
    "Balanced Natural": "balanced natural contour with moderate softness and realistic weight",
    "Soft": "soft natural contour with gentle settling and realistic gravity",
    "Very Soft / Natural Movement": "very soft contour with pronounced settling, weight, and natural movement",
}

CLOTHED_BUST_AUGMENTATION_AUTHORITY_V221 = {
    "Natural / Unaugmented": "natural unaugmented garment contour without implant-like upper-pole fullness",
    "Subtle Natural-Looking Augmentation": "subtle augmented contour with moderate projection while preserving a natural slope",
    "Round High-Profile Implants": "round high-profile augmented contour with clearly increased upper-pole fullness and forward projection",
    "Teardrop / Anatomical Implants": "anatomical augmented contour with a sloped upper pole and fuller lower pole",
    "Very Firm Augmented Projection": "very firm augmented contour with high upper-pole fullness, strong projection, and minimal natural drop",
}


def _body_type_authority_v221(body_type: str) -> str:
    return BODY_TYPE_AUTHORITY_PROMPTS_V221.get(body_type, "")


def _female_bust_authority_v221(
    presentation_mode: str,
    size: str,
    shape: str,
    position: str,
    firmness: str,
    augmentation: str,
) -> tuple[str, str]:
    if presentation_mode == "Clinical Anatomy":
        anatomy = _join(
            "bust anatomy authority: preserve the selected bust size, shape, placement, firmness, and augmentation as independent anatomical traits",
            BUST_SIZE_PROMPTS.get(size, ""),
            BUST_SHAPE_PROMPTS.get(shape, ""),
            BUST_POSITION_PROMPTS.get(position, ""),
            BUST_FIRMNESS_PROMPTS.get(firmness, ""),
            BUST_AUGMENTATION_PROMPTS.get(augmentation, ""),
            "do not normalize the selected bust to a generic average size or shape",
        )
        return anatomy, anatomy

    clothed = _join(
        "clothed bust-silhouette authority: the selected bust traits must remain visibly distinct through the garment",
        CLOTHED_BUST_SIZE_AUTHORITY_V221.get(size, ""),
        CLOTHED_BUST_SHAPE_AUTHORITY_V221.get(shape, ""),
        CLOTHED_BUST_POSITION_AUTHORITY_V221.get(position, ""),
        CLOTHED_BUST_FIRMNESS_AUTHORITY_V221.get(firmness, ""),
        CLOTHED_BUST_AUGMENTATION_AUTHORITY_V221.get(augmentation, ""),
        "the garment follows the selected bust contour and does not flatten, minimize, enlarge, or normalize it unless the outfit explicitly specifies compression or support shaping",
    )
    anatomy = _join(
        "bust anatomy authority: preserve the selected bust size, shape, placement, firmness, and augmentation as independent anatomical traits",
        BUST_SIZE_PROMPTS.get(size, ""),
        BUST_SHAPE_PROMPTS.get(shape, ""),
        BUST_POSITION_PROMPTS.get(position, ""),
        BUST_FIRMNESS_PROMPTS.get(firmness, ""),
        BUST_AUGMENTATION_PROMPTS.get(augmentation, ""),
        "do not normalize the selected bust to a generic average size or shape",
    )
    return clothed, anatomy


def _body_visibility_advisory_v221(profile: dict, plan: dict) -> str:
    shot_type = plan.get("shot_type", "")
    pose = plan.get("pose", "")
    presentation = profile.get("presentation_mode", "")
    notes = []
    if shot_type in {"Face Close-Up", "Head and Shoulders", "Extreme Close-Up — Single Detail"}:
        notes.append("Body type, lower-body proportions, buttocks, and most bust-shape differences cannot be reliably evaluated in this framing.")
    elif shot_type in {"Chest-Up", "Close-Up — Regional Documentation"}:
        notes.append("Only the selected upper-body or regional traits can be evaluated; lower-body and buttocks settings are outside the frame.")
    elif shot_type == "Waist-Up Midshot":
        notes.append("Upper-body build and bust contour can be evaluated, but hips, buttocks, thighs, and full-body proportions are only partially or not visible.")
    if pose in {"Heart Shape with Both Hands", "Arms Loosely Crossed"}:
        notes.append("The selected arm/hand pose can partially cover the chest and reduce visible bust-shape evidence.")
    outfit = (profile.get("active_presentation_prompt") or "").lower()
    if any(token in outfit for token in ("compression", "sports bra", "binding", "shapewear")):
        notes.append("The selected garment is compressive or shaping, so anatomical bust size, shape, and position may be intentionally masked.")
    if presentation == "Clothed Character":
        notes.append("For strongest bust validation, use a fitted opaque non-compression top and compare outputs with the same seed, framing, and pose.")
    return " ".join(notes)


class CharacterBlueprintCreatorV221(CharacterBlueprintCreatorV22):
    CATEGORY = "character creation/v2"
    FUNCTION = "build_blueprint_v221"
    DESCRIPTION = (
        "V2.2.1 Character Creator. Adds explicit body-proportion authority and clothed-bust silhouette authority so body type, bust size, shape, placement, firmness, and augmentation remain distinct."
    )
    RETURN_TYPES = CharacterBlueprintCreatorV22.RETURN_TYPES + ("STRING", "STRING")
    RETURN_NAMES = CharacterBlueprintCreatorV22.RETURN_NAMES + (
        "body_type_authority_prompt", "bust_authority_prompt",
    )

    def build_blueprint_v221(self, *args, **kwargs):
        import inspect
        bound = inspect.signature(CharacterBlueprintCreatorV22.build_blueprint_v22).bind(self, *args, **kwargs)
        bound.apply_defaults()
        values = bound.arguments
        result = list(super().build_blueprint_v22(*args, **kwargs))
        profile = dict(result[8])

        gender = values["gender"]
        presentation_mode = values["presentation_mode"]
        body_type = values["body_type"]
        body_authority = _body_type_authority_v221(body_type)
        bust_clothed = ""
        bust_anatomy = ""
        if gender == "Adult Female":
            bust_clothed, bust_anatomy = _female_bust_authority_v221(
                presentation_mode,
                values["bust_size"], values["bust_shape"], values["bust_position"],
                values["bust_firmness"], values["bust_augmentation"],
            )

        # Replace weak legacy body phrases with explicit authority blocks.
        clothed_upper = _join(body_authority, bust_clothed if gender == "Adult Female" else result[10])
        anatomy_upper = _join(body_authority, bust_anatomy if gender == "Adult Female" else result[11])
        clothed_lower = result[12]
        anatomy_lower = result[13]

        if presentation_mode == "Clinical Anatomy":
            active_body = _join(anatomy_upper, anatomy_lower)
        elif presentation_mode == "Custom Presentation" and values["custom_presentation_body_basis"] == "Clinical Anatomy":
            active_body = _join(anatomy_upper, anatomy_lower)
        elif presentation_mode == "Custom Presentation" and values["custom_presentation_body_basis"] == "Identity Only":
            active_body = ""
        else:
            active_body = _join(clothed_upper, clothed_lower)

        gender_authority = profile.get("gender_authority_prompt", _gender_authority_prompt_v2(gender))
        identity_details = profile.get("identity_detail_prompt", "")
        presentation = profile.get("active_presentation_prompt", "")
        marks = profile.get("marks_prompt", "")
        locks = _join(profile.get("tattoo_count_lock", ""), profile.get("piercing_count_lock", ""), profile.get("anatomy_integrity_lock", ""))
        active_character = _join(gender_authority, body_authority, bust_clothed if presentation_mode != "Clinical Anatomy" else bust_anatomy, presentation, identity_details, marks, clothed_lower if presentation_mode != "Clinical Anatomy" else anatomy_lower, locks)
        clothed_character = _join(gender_authority, body_authority, bust_clothed, profile.get("default_clothing_prompt", ""), identity_details, marks, clothed_lower, locks)
        clinical_character = _join(gender_authority, body_authority, bust_anatomy, "unclothed adult subject in neutral non-aroused clinical anatomy documentation", identity_details, marks, anatomy_lower, locks)

        summary = profile.get("presentation_summary", "") + "\n" + f"Body Type Authority: {body_authority or '[unspecified]'}" + "\n" + f"Bust Authority: {(bust_anatomy if presentation_mode == 'Clinical Anatomy' else bust_clothed) or '[not applicable or unspecified]'}"

        profile.update({
            "schema": "CHARACTER_BLUEPRINT_V221",
            "schema_version": 7,
            "body_type_authority_prompt": body_authority,
            "bust_clothed_authority_prompt": bust_clothed,
            "bust_anatomy_authority_prompt": bust_anatomy,
            "clothed_upper_body": clothed_upper,
            "anatomy_upper_body": anatomy_upper,
            "active_body_prompt": active_body,
            "active_character_prompt": active_character,
            "clothed_character_prompt": clothed_character,
            "clinical_character_prompt": clinical_character,
            "full_profile_prompt": active_character,
            "presentation_summary": summary,
        })

        result[1] = anatomy_upper
        result[3] = bust_anatomy if presentation_mode == "Clinical Anatomy" else bust_clothed
        result[6] = active_character
        result[8] = profile
        result[10] = clothed_upper
        result[11] = anatomy_upper
        result[15] = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        result[17] = active_body
        result[18] = active_character
        result[19] = clothed_character
        result[20] = clinical_character
        result[21] = summary
        return tuple(result) + (body_authority, bust_anatomy if presentation_mode == "Clinical Anatomy" else bust_clothed)


class CharacterPromptAssemblerV221(CharacterPromptAssemblerV22):
    CATEGORY = "character creation/v2"
    FUNCTION = "assemble_prompt_v221"
    DESCRIPTION = (
        "V2.2.1 assembler. Places body and bust authority before wardrobe and shot instructions, removes duplicate gender locks, and reports framing/pose limits that can hide body traits."
    )
    RETURN_TYPES = CharacterPromptAssemblerV22.RETURN_TYPES + ("STRING",)
    RETURN_NAMES = CharacterPromptAssemblerV22.RETURN_NAMES + ("body_visibility_advisory",)

    def assemble_prompt_v221(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan = shot_plan if isinstance(shot_plan, dict) else {}
        gender_authority = profile.get("gender_authority_prompt", _gender_authority_prompt_v2(profile.get("gender", "Adult Nonbinary")))
        identity_details = profile.get("identity_detail_prompt") or profile.get("face_identity", "adult subject")
        # Robustly strip any serialized duplicate gender-authority prefix.
        while identity_details.startswith(gender_authority):
            identity_details = identity_details[len(gender_authority):].lstrip(" ,;")

        body_authority = profile.get("body_type_authority_prompt", "")
        if profile.get("presentation_mode") == "Clinical Anatomy":
            bust_authority = profile.get("bust_anatomy_authority_prompt", "")
        else:
            bust_authority = profile.get("bust_clothed_authority_prompt", "")
        presentation = profile.get("active_presentation_prompt", profile.get("default_clothing_prompt", ""))
        body_remainder = _join(profile.get("clothed_lower_body", "") if profile.get("presentation_mode") != "Clinical Anatomy" else profile.get("anatomy_lower_body", ""))
        marks = profile.get("marks_prompt", "")
        tattoo_count_lock = profile.get("tattoo_count_lock", "")
        piercing_count_lock = profile.get("piercing_count_lock", "")
        anatomy_integrity_lock = profile.get("anatomy_integrity_lock", "")
        character_id = profile.get("character_id", "character")
        presentation_mode = profile.get("presentation_mode", "Legacy / Unspecified")
        shot_prompt = plan.get("final_shot_prompt", "custom camera framing and pose")
        width = int(plan.get("recommended_width", 1024))
        height = int(plan.get("recommended_height", 1280))
        focus_region = plan.get("focus_region", "")
        advisory = _body_visibility_advisory_v221(profile, plan)

        qwen = generation_purpose.startswith("Qwen")
        krea = generation_purpose.startswith("Krea")
        if generation_purpose == "Krea — First Identity Image":
            purpose_prefix = "Create a realistic camera photograph of the exact adult character defined below"
            reference = "None — text-to-image"
        elif generation_purpose == "Krea — LoRA Expansion":
            purpose_prefix = "Create a realistic camera photograph using the loaded identity LoRA and the exact character specification below"
            reference = "Mini or final identity LoRA loaded in the Krea model lane"
        elif generation_purpose == "Qwen — Identity Documentation":
            purpose_prefix = _join(f"Edit {reference_label} into identity documentation of the same adult person", f"preserve the exact recognizable facial identity, hairline, skin characteristics, tattoos, piercings, and permanent marks from {reference_label}", "replace the old framing and pose with the current Shot Control settings", "follow every active Character Creator setting exactly")
            reference = reference_label
        elif generation_purpose == "Qwen — Anatomy Documentation":
            purpose_prefix = _join(f"Edit {reference_label} into neutral adult body documentation of the same person", f"preserve the exact recognizable identity, body proportions, tattoos, piercings, and permanent marks from {reference_label}", "replace the old framing and pose with the current Shot Control settings", "follow every active Character Creator anatomy and presentation setting exactly")
            reference = reference_label
        elif generation_purpose == "Qwen — Clothed Action / Lifestyle":
            purpose_prefix = _join(f"Edit {reference_label} into a realistic action or lifestyle photograph of the same adult person", f"preserve the exact recognizable identity and permanent markings from {reference_label}", "replace the old pose, framing, and wardrobe with the current Character Creator and Shot Control settings")
            reference = reference_label
        else:
            purpose_prefix = _join(f"Edit {reference_label} into a realistic camera photograph of the same adult person", f"preserve the exact recognizable identity and permanent markings from {reference_label}", "replace the old framing, pose, and wardrobe with the current Character Creator and Shot Control settings")
            reference = reference_label

        focus_lock = ""
        if focus_region:
            focus_lock = _join(f"documentation focus authority: {focus_region}", "all permanent marks and jewelry within the focused region must remain exact and readable", _focus_specific_integrity_lock_v22(focus_region))

        final_prompt = _join(
            trigger_word if krea else "", custom_prefix, purpose_prefix,
            gender_authority,
            body_authority,
            bust_authority,
            presentation,
            shot_prompt,
            identity_details,
            marks,
            body_remainder,
            tattoo_count_lock,
            piercing_count_lock,
            anatomy_integrity_lock,
            focus_lock,
            "keep the requested framing, camera angle, pose, expression, gender, body type, bust traits, anatomy, markings, and character presentation internally consistent",
            custom_suffix,
        )
        krea_prompt = final_prompt if krea else ""
        qwen_prompt = final_prompt if qwen else ""
        shot_id = _slug(_join(character_id, generation_purpose, plan.get("planner_mode", ""), plan.get("shot_type", ""), plan.get("focus_region", ""), plan.get("camera_view", ""), plan.get("pose", "")))
        notes = "\n".join([
            f"Purpose: {generation_purpose}",
            f"Reference: {reference}",
            "Identity/body/clothing authority: Character Creator V2.2.1",
            "Camera/pose/focus authority: Universal Shot Control V2.2",
            f"Body visibility advisory: {advisory or 'None'}",
        ])
        active_summary = "\n\n".join([profile.get("presentation_summary", f"Presentation mode: {presentation_mode}"), plan.get("active_settings_summary", "Shot settings unavailable"), notes])
        return (
            krea_prompt, qwen_prompt, shot_prompt, presentation, marks, reference, shot_id,
            width, height, character_id, notes, presentation_mode, active_summary, final_prompt,
            advisory,
        )

# ---------------------------------------------------------------------------
# V2.2.2 crop-compliance, crop-aware wardrobe, and resolution authority patch
# ---------------------------------------------------------------------------

UPPER_BODY_CROP_AUTHORITY_V222 = {
    "Very Slim": "visible upper-body authority: distinctly very slim shoulders, narrow upper torso, and slender upper arms",
    "Slim": "visible upper-body authority: lean shoulders, lean upper torso, and slim upper arms",
    "Average": "visible upper-body authority: balanced average shoulders, upper torso, and upper arms",
    "Athletic": "visible upper-body authority: visibly trained shoulders and upper arms with a firm athletic upper torso",
    "Curvy": "visible upper-body authority: balanced shoulders with a distinctly curvy upper-torso silhouette",
    "Full-Figured": "visible upper-body authority: fuller upper arms and substantial natural upper-torso volume",
    "Muscular": "visible upper-body authority: broad trained shoulders, developed upper arms, and a muscular upper torso",
    "Heavyset": "visible upper-body authority: broad shoulders, fuller upper arms, and substantial upper-torso mass",
    "Custom / Unspecified": "visible upper-body authority: preserve the selected custom body build only within the visible crop",
}

WAIST_UP_CROP_AUTHORITY_V222 = {
    "Very Slim": "visible torso authority: distinctly very slim shoulders, narrow torso, slender arms, and a narrow waist",
    "Slim": "visible torso authority: lean shoulders, lean torso, slim arms, and a defined narrow waist",
    "Average": "visible torso authority: balanced average shoulders, torso, arms, and waist",
    "Athletic": "visible torso authority: trained shoulders and arms, a firm athletic torso, and a defined athletic waist",
    "Curvy": "visible torso authority: balanced shoulders, a clearly defined waist, and a distinctly curvy torso silhouette",
    "Full-Figured": "visible torso authority: fuller arms, substantial natural torso volume, and a fuller waist silhouette",
    "Muscular": "visible torso authority: broad trained shoulders, developed arms, a muscular torso, and a strong waist",
    "Heavyset": "visible torso authority: broad shoulders, fuller arms, substantial torso mass, and a broad waist",
    "Custom / Unspecified": "visible torso authority: preserve the selected custom body build only within the visible crop",
}


def _infer_body_type_v222(profile: dict) -> str:
    body_type = str(profile.get("body_type", "") or "").strip()
    if body_type:
        return body_type
    authority = str(profile.get("body_type_authority_prompt", "") or "").lower()
    for candidate in BODY_TYPES:
        token = candidate.lower().replace("custom / unspecified", "custom")
        if token and token in authority:
            return candidate
    return "Custom / Unspecified"


def _focus_scope_v222(plan: dict) -> str:
    focus = str(plan.get("focus_region", "") or "").lower()
    if not focus:
        return ""
    if any(x in focus for x in ("face", "eye", "eyebrow", "nose", "septum", "mouth", "lip", "forehead", "hairline", "chin", "jaw", "beard", "ear", "head", "neck")):
        return "face"
    if any(x in focus for x in ("chest", "breast", "nipple", "areola", "ribcage", "shoulder", "upper back", "arm")):
        return "upper"
    if any(x in focus for x in ("abdomen", "waist", "navel", "side torso", "lower back")):
        return "waist"
    if any(x in focus for x in ("groin", "pelvis", "pubic", "genital", "hip", "butt", "glute", "thigh", "leg", "foot", "feet")):
        return "lower"
    if "hand" in focus:
        return "hand"
    return "regional"


def _crop_authority_v222(plan: dict) -> str:
    shot_type = str(plan.get("shot_type", "") or "")
    focus_mode = str(plan.get("focus_mode", "") or "")
    focus_region = str(plan.get("focus_region", "") or "")
    if focus_mode == "Extreme Close-Up" or shot_type == "Extreme Close-Up — Single Detail":
        return _join(
            "mandatory framing authority: true macro extreme close-up only",
            f"the selected detail {focus_region or 'must'} occupies approximately 80 to 90 percent of the frame",
            "do not widen into a portrait, torso image, regional context image, or full-body image",
        )
    if focus_mode == "Regional Close-Up" or shot_type == "Close-Up — Regional Documentation":
        return _join(
            "mandatory framing authority: regional close-up only",
            f"center the complete selected region {focus_region or ''} with only nearby anatomical context",
            "do not widen into a three-quarter-body or full-body image",
        )
    mapping = {
        "Face Close-Up": (
            "mandatory crop authority: face close-up only; the face occupies most of the frame from the complete hairline through the upper shoulders; "
            "do not show the chest, waist, hips, legs, shoes, or full body; do not zoom out"
        ),
        "Head and Shoulders": (
            "mandatory crop authority: head-and-shoulders only; frame from above the complete head through the shoulders and upper chest; "
            "do not show the waist, hips, legs, shoes, or full body; do not zoom out"
        ),
        "Chest-Up": (
            "mandatory crop authority: chest-up only; the subject fills the frame from above the complete head to just below the chest or bust line; "
            "both shoulders and upper arms remain visible; the crop must end before the natural waist; do not show the abdomen, hips, jeans, legs, knees, shoes, or full body; do not zoom out"
        ),
        "Waist-Up Midshot": (
            "mandatory crop authority: waist-up only; frame from above the complete head through the natural waist and lower abdomen; "
            "do not show thighs, knees, lower legs, shoes, or full body; do not zoom out"
        ),
        "Three-Quarter Body": (
            "mandatory crop authority: three-quarter-body only; frame from above the complete head to below the knees while keeping the feet outside the image"
        ),
        "Full Body": (
            "mandatory crop authority: full body only; show the entire subject from head to feet with balanced margin around the body"
        ),
        "Body Close-Up": (
            "mandatory crop authority: body-region close-up only; center the selected body region and do not widen into a full-body image"
        ),
    }
    return mapping.get(shot_type, "")


def _split_raw_outfit_v222(raw: str) -> tuple[str, str, str]:
    text = re.sub(r"\s+", " ", str(raw or "")).strip(" ,")
    if not text:
        return "", "", ""
    normalized = re.sub(r"\s*,?\s+and\s+", ", ", text, flags=re.IGNORECASE)
    parts = [p.strip(" ,") for p in normalized.split(",") if p.strip(" ,")]
    top = parts[0] if parts else text
    bottom = parts[1] if len(parts) > 1 else ""
    footwear = parts[2] if len(parts) > 2 else ""
    return top, bottom, footwear


def _visible_outfit_prompt_v222(profile: dict, plan: dict) -> str:
    presentation_mode = profile.get("presentation_mode", "Clothed Character")
    active = profile.get("active_presentation_prompt", profile.get("default_clothing_prompt", ""))
    if presentation_mode != "Clothed Character":
        return active

    shot_type = str(plan.get("shot_type", "") or "")
    scope = _focus_scope_v222(plan)
    components = profile.get("outfit_components", {}) if isinstance(profile.get("outfit_components"), dict) else {}
    kind = str(components.get("kind", "") or "")
    raw = str(components.get("raw", "") or "")
    top = str(components.get("top", "") or "")
    bottom = str(components.get("bottom", "") or "")
    footwear = str(components.get("footwear", "") or "")
    one_piece = str(components.get("one_piece", "") or "")
    swim_top = str(components.get("swimwear_top", "") or "")
    swim_bottom = str(components.get("swimwear_bottom", "") or "")
    outerwear = str(components.get("outerwear", "") or "")
    notes = str(components.get("notes", "") or "")
    if raw and not any((top, bottom, footwear, one_piece, swim_top, swim_bottom)):
        top, bottom, footwear = _split_raw_outfit_v222(raw)

    upper = _join(outerwear, one_piece or swim_top or top)
    lower = _join(one_piece or swim_bottom or bottom)
    jewelry = profile.get("jewelry_prompt", "")
    continuity = (
        "wardrobe continuity authority: keep the exact same selected outfit, colors, materials, fit, and garment construction across variations; "
        "do not substitute, redesign, remove, lift, lower, roll, open, or displace garments"
    )

    if shot_type in {"Full Body", "Three-Quarter Body", "Custom Framing"}:
        return _join(active, continuity)
    if shot_type == "Waist-Up Midshot" or scope == "waist":
        visible = _join(
            f"wearing the same selected outfit with {upper or 'the exact selected upper garment'} fully visible",
            f"only the upper edge or waistband of {lower or 'the selected lower garment'} may appear at the bottom of the frame",
            "footwear remains outside the frame",
            notes,
            jewelry,
            continuity,
        )
        return visible
    if scope == "lower":
        return _join(
            f"wearing the same selected outfit with {lower or 'the exact selected lower garment'} visible in the selected lower-body crop",
            f"{footwear} visible only if the selected region includes the feet" if footwear else "",
            "the upper garment remains unchanged outside the crop",
            notes,
            jewelry,
            continuity,
        )
    if scope == "hand":
        return _join(
            "the exact selected outfit remains unchanged outside this hand-focused crop",
            jewelry,
            continuity,
        )
    if shot_type in {"Face Close-Up", "Head and Shoulders", "Chest-Up"} or scope in {"face", "upper"}:
        crop_wording = {
            "Face Close-Up": "only the neckline and small shoulder edges of the upper garment may be visible",
            "Head and Shoulders": "only the neckline, shoulders, and upper-chest portion of the upper garment are visible",
            "Chest-Up": "only the upper garment from neckline through just below the chest is visible",
        }.get(shot_type, "only the garment covering the selected upper-body region is visible")
        return _join(
            f"wearing the same selected outfit with {upper or 'the exact selected upper garment'}",
            crop_wording,
            "lower garments and footwear remain outside the frame and must not cause the camera to zoom out",
            notes,
            jewelry,
            continuity,
        )
    return _join(active, continuity)


def _visible_body_prompts_v222(profile: dict, plan: dict) -> tuple[str, str, str]:
    shot_type = str(plan.get("shot_type", "") or "")
    scope = _focus_scope_v222(plan)
    body_type = _infer_body_type_v222(profile)
    full_body = profile.get("body_type_authority_prompt", "")
    presentation_mode = profile.get("presentation_mode", "Clothed Character")
    bust = profile.get("bust_anatomy_authority_prompt", "") if presentation_mode == "Clinical Anatomy" else profile.get("bust_clothed_authority_prompt", "")
    lower = profile.get("anatomy_lower_body", "") if presentation_mode == "Clinical Anatomy" else profile.get("clothed_lower_body", "")

    if shot_type == "Face Close-Up" or scope == "face":
        return "", "", ""
    if shot_type == "Head and Shoulders":
        return UPPER_BODY_CROP_AUTHORITY_V222.get(body_type, ""), "", ""
    if shot_type == "Chest-Up" or scope == "upper":
        return UPPER_BODY_CROP_AUTHORITY_V222.get(body_type, full_body), bust, ""
    if shot_type == "Waist-Up Midshot" or scope == "waist":
        return WAIST_UP_CROP_AUTHORITY_V222.get(body_type, full_body), bust, ""
    if scope == "lower":
        return "", "", lower
    if shot_type in {"Three-Quarter Body", "Full Body", "Custom Framing"}:
        return full_body, bust, lower
    return full_body, bust, ""


def _resolution_authority_v222(plan: dict) -> str:
    width = int(plan.get("recommended_width", 1024))
    height = int(plan.get("recommended_height", 1280))
    aspect = str(plan.get("aspect_ratio", "") or "")
    return _join(
        f"canvas authority: render natively at {width} by {height} pixels",
        f"use the selected {aspect} composition" if aspect else "",
        "fit the mandatory crop to this canvas rather than widening the shot",
    )


class CharacterBlueprintCreatorV222(CharacterBlueprintCreatorV221):
    CATEGORY = "character creation/v2"
    FUNCTION = "build_blueprint_v222"
    DESCRIPTION = (
        "V2.2.2 Character Creator. Preserves the conclusive V2.2.1 behavior and serializes the raw body and bust selections for crop-aware downstream prompt assembly."
    )

    def build_blueprint_v222(self, *args, **kwargs):
        import inspect
        bound = inspect.signature(CharacterBlueprintCreatorV22.build_blueprint_v22).bind(self, *args, **kwargs)
        bound.apply_defaults()
        values = bound.arguments
        result = list(super().build_blueprint_v221(*args, **kwargs))
        profile = dict(result[8])
        profile.update({
            "schema": "CHARACTER_BLUEPRINT_V222",
            "schema_version": 8,
            "height": values.get("height", ""),
            "body_type": values.get("body_type", ""),
            "buttocks": values.get("buttocks", ""),
            "bust_size": values.get("bust_size", ""),
            "bust_shape": values.get("bust_shape", ""),
            "bust_position": values.get("bust_position", ""),
            "bust_firmness": values.get("bust_firmness", ""),
            "bust_augmentation": values.get("bust_augmentation", ""),
        })
        result[8] = profile
        result[15] = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        return tuple(result)


class CharacterPromptAssemblerV222(CharacterPromptAssemblerV221):
    CATEGORY = "character creation/v2"
    FUNCTION = "assemble_prompt_v222"
    DESCRIPTION = (
        "V2.2.2 assembler. Enforces crop compliance, removes off-frame body and wardrobe details, preserves the same outfit across variations, and emits the actual shot-controlled resolution authority."
    )
    RETURN_TYPES = CharacterPromptAssemblerV221.RETURN_TYPES + ("STRING", "STRING", "STRING")
    RETURN_NAMES = CharacterPromptAssemblerV221.RETURN_NAMES + (
        "crop_authority_prompt", "visible_outfit_prompt", "resolution_authority_prompt",
    )

    def assemble_prompt_v222(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan = shot_plan if isinstance(shot_plan, dict) else {}
        gender_authority = profile.get("gender_authority_prompt", _gender_authority_prompt_v2(profile.get("gender", "Adult Nonbinary")))
        identity_details = profile.get("identity_detail_prompt") or profile.get("face_identity", "adult subject")
        while identity_details.startswith(gender_authority):
            identity_details = identity_details[len(gender_authority):].lstrip(" ,;")
        identity_details = re.sub(
            r"^adult subject\s*,\s*adult (?:female|male|nonbinary)\s*,\s*",
            "",
            identity_details,
            flags=re.IGNORECASE,
        )

        crop_authority = _crop_authority_v222(plan)
        resolution_authority = _resolution_authority_v222(plan)
        visible_presentation = _visible_outfit_prompt_v222(profile, plan)
        visible_body, visible_bust, visible_lower = _visible_body_prompts_v222(profile, plan)
        marks = profile.get("marks_prompt", "")
        tattoo_count_lock = profile.get("tattoo_count_lock", "")
        piercing_count_lock = profile.get("piercing_count_lock", "")
        anatomy_integrity_lock = profile.get("anatomy_integrity_lock", "")
        character_id = profile.get("character_id", "character")
        presentation_mode = profile.get("presentation_mode", "Legacy / Unspecified")
        shot_prompt = plan.get("final_shot_prompt", "custom camera framing and pose")
        width = int(plan.get("recommended_width", 1024))
        height = int(plan.get("recommended_height", 1280))
        focus_region = plan.get("focus_region", "")
        advisory = _body_visibility_advisory_v221(profile, plan)

        qwen = generation_purpose.startswith("Qwen")
        krea = generation_purpose.startswith("Krea")
        if generation_purpose == "Krea — First Identity Image":
            purpose_prefix = "Create a realistic camera photograph of the exact adult character defined below"
            reference = "None — text-to-image"
        elif generation_purpose == "Krea — LoRA Expansion":
            purpose_prefix = "Create a realistic camera photograph using the loaded identity LoRA and the exact character specification below"
            reference = "Mini or final identity LoRA loaded in the Krea model lane"
        elif generation_purpose == "Qwen — Identity Documentation":
            purpose_prefix = _join(
                f"Edit {reference_label} into identity documentation of the same adult person",
                f"preserve the exact recognizable facial identity, hairline, skin characteristics, tattoos, piercings, and permanent marks from {reference_label}",
                "replace the old framing and pose with the current Shot Control settings",
                "keep the exact selected outfit unchanged unless the Character Creator explicitly changes it",
            )
            reference = reference_label
        elif generation_purpose == "Qwen — Anatomy Documentation":
            purpose_prefix = _join(
                f"Edit {reference_label} into neutral adult body documentation of the same person",
                f"preserve the exact recognizable identity, body proportions, tattoos, piercings, and permanent marks from {reference_label}",
                "replace the old framing and pose with the current Shot Control settings",
            )
            reference = reference_label
        elif generation_purpose == "Qwen — Clothed Action / Lifestyle":
            purpose_prefix = _join(
                f"Edit {reference_label} into a realistic action or lifestyle photograph of the same adult person",
                f"preserve the exact recognizable identity and permanent markings from {reference_label}",
                "change the pose and framing while keeping the exact selected Character Creator outfit unchanged",
            )
            reference = reference_label
        else:
            purpose_prefix = _join(
                f"Edit {reference_label} into a realistic camera photograph of the same adult person",
                f"preserve the exact recognizable identity and permanent markings from {reference_label}",
                "replace the old framing and pose with the current Shot Control settings",
                "keep the exact selected outfit unchanged unless the Character Creator explicitly changes it",
            )
            reference = reference_label

        focus_lock = ""
        if focus_region:
            focus_lock = _join(
                f"documentation focus authority: {focus_region}",
                "all permanent marks and jewelry within the focused region must remain exact and readable",
                _focus_specific_integrity_lock_v22(focus_region),
            )

        final_prompt = _join(
            trigger_word if krea else "",
            custom_prefix,
            purpose_prefix,
            gender_authority,
            crop_authority,
            resolution_authority,
            visible_body,
            visible_bust,
            visible_presentation,
            shot_prompt,
            identity_details,
            marks,
            visible_lower,
            tattoo_count_lock,
            piercing_count_lock,
            anatomy_integrity_lock,
            focus_lock,
            "keep the requested crop, camera angle, pose, expression, gender, visible body traits, anatomy, markings, and character presentation internally consistent",
            custom_suffix,
        )
        krea_prompt = final_prompt if krea else ""
        qwen_prompt = final_prompt if qwen else ""
        shot_id = _slug(_join(
            character_id, generation_purpose, plan.get("planner_mode", ""),
            plan.get("shot_type", ""), plan.get("focus_region", ""),
            plan.get("camera_view", ""), plan.get("pose", ""),
        ))
        notes = "\n".join([
            f"Purpose: {generation_purpose}",
            f"Reference: {reference}",
            "Identity/body/clothing authority: Character Creator V2.2.2",
            "Camera/pose/focus authority: Universal Shot Control V2.2",
            "Crop-aware assembly: off-frame lower-body and footwear descriptors are removed from portrait crops.",
            "Resolution routing: Shot Control recommended width and height drive the workflow latent size in Studio v2.6.2.",
            f"Body visibility advisory: {advisory or 'None'}",
        ])
        active_summary = "\n\n".join([
            profile.get("presentation_summary", f"Presentation mode: {presentation_mode}"),
            plan.get("active_settings_summary", "Shot settings unavailable"),
            f"CROP AUTHORITY\n{crop_authority or '[custom/unspecified]'}",
            f"VISIBLE WARDROBE\n{visible_presentation or '[none]'}",
            f"RESOLUTION AUTHORITY\n{resolution_authority}",
            notes,
        ])
        return (
            krea_prompt, qwen_prompt, shot_prompt, visible_presentation, marks, reference, shot_id,
            width, height, character_id, notes, presentation_mode, active_summary, final_prompt,
            advisory, crop_authority, visible_presentation, resolution_authority,
        )

# -----------------------------------------------------------------------------
# V2.2.4 current production patch: explicit pubic-hair authority, compact Krea
# prompts, and positive unmarked-skin authority when Tattoo Status is None.
# -----------------------------------------------------------------------------

PUBIC_HAIR_STYLES_V224 = [
    "Unspecified",
    "Hairless / Fully Removed",
    "Fine Natural",
    "Fine Trimmed",
    "Neatly Trimmed Short",
    "Natural Average",
    "Full Natural",
    "Custom",
]


def _pubic_hair_prompt_v224(gender: str, style: str, custom: str = "") -> str:
    style = (style or "Unspecified").strip()
    custom = (custom or "").strip()
    if style == "Unspecified":
        return ""
    if style == "Custom":
        return custom

    anatomy = {
        "Adult Female": "female pubic hair",
        "Adult Male": "male pubic hair",
        "Adult Nonbinary": "adult pubic hair",
    }.get(gender, "adult pubic hair")
    area = "over the mons pubis and natural groin hair-bearing region"
    prompts = {
        "Hairless / Fully Removed": (
            "pubic-hair grooming authority: fully removed pubic hair with smooth natural skin "
            "across the mons pubis and groin hair-bearing region"
        ),
        "Fine Natural": (
            f"pubic-hair grooming authority: fine sparse natural {anatomy} with light even coverage {area}"
        ),
        "Fine Trimmed": (
            f"pubic-hair grooming authority: fine neatly trimmed {anatomy}, short and even, with precise light coverage {area}"
        ),
        "Neatly Trimmed Short": (
            f"pubic-hair grooming authority: neatly trimmed short {anatomy} with even maintained coverage {area}"
        ),
        "Natural Average": (
            f"pubic-hair grooming authority: average natural {anatomy} with realistic moderate coverage {area}"
        ),
        "Full Natural": (
            f"pubic-hair grooming authority: full natural {anatomy} with dense realistic untrimmed coverage {area}"
        ),
    }
    return prompts.get(style, custom)


def _clean_mark_negations_v224(text: str, tattoo_status: str, piercing_status: str) -> tuple[str, list[str]]:
    """Remove redundant mark-negation clauses from Custom Identity Notes.

    Status controls are authoritative. Keeping phrases such as "No tattoos" in a
    positive-only prompt repeatedly activates the unwanted concept and can cause
    Krea-family models to draw it. The dedicated status authority replaces them.
    """
    original = str(text or "").strip()
    if not original:
        return "", []

    removed: list[str] = []
    clauses = [c.strip() for c in re.split(r"[\n;,]+", original) if c.strip()]
    kept: list[str] = []
    tattoo_pattern = re.compile(
        r"^(?:no\s+tattoos?|without\s+tattoos?|tattoo[-\s]?free|no\s+body\s+art|unmarked\s+skin)$",
        re.IGNORECASE,
    )
    piercing_pattern = re.compile(
        r"^(?:no\s+piercings?|without\s+piercings?|piercing[-\s]?free)$",
        re.IGNORECASE,
    )
    for clause in clauses:
        if tattoo_status == "None" and tattoo_pattern.match(clause):
            removed.append(clause)
            continue
        if piercing_status == "None" and piercing_pattern.match(clause):
            removed.append(clause)
            continue
        kept.append(clause)
    return _join(*kept), removed


def _skin_surface_authority_v224(profile: dict, qwen: bool) -> str:
    if profile.get("tattoo_status") != "None":
        return ""
    if qwen:
        return (
            "skin-surface authority: keep naturally unmarked skin across every visible area; "
            "remove any decorative pigment, lettering, symbols, or body art not defined by the Character Creator"
        )
    # Krea is positive-prompt only. Avoid repeating the token "tattoo" because
    # merely naming an unwanted concept can increase its probability.
    return (
        "skin-surface authority: naturally unmarked skin across every visible area, "
        "with clean continuous natural skin texture on the face, neck, arms, torso, abdomen, back, hips, and legs"
    )


def _body_jewelry_authority_v224(profile: dict, qwen: bool) -> str:
    if profile.get("piercing_status") != "None":
        return ""
    if qwen:
        return (
            "body-jewelry authority: keep the face and body free of attached jewelry; "
            "remove any unlisted studs, rings, bars, hoops, or decorative metal"
        )
    return (
        "body-jewelry authority: jewelry-free face and body, with clean uninterrupted eyebrows, "
        "nostrils, septum, lips, ears, chest, navel, and other visible skin surfaces"
    )


def _crop_shows_pubic_region_v224(plan: dict) -> bool:
    shot_type = str(plan.get("shot_type", "") or "")
    focus = str(plan.get("focus_region", "") or "").lower()
    framing = str(plan.get("framing_prompt", "") or "").lower()
    if any(token in focus for token in ("pubic", "groin", "pelvis", "genital")):
        return True
    if shot_type in {"Three-Quarter Body", "Full Body"}:
        return True
    if shot_type == "Custom Framing" and any(
        token in framing for token in ("pubic", "groin", "pelvis", "genital", "below the waist")
    ):
        return True
    return False


def _compact_shot_prompt_v224(plan: dict) -> str:
    if plan.get("planner_mode") == "Full Custom Shot Text":
        return str(plan.get("final_shot_prompt", "") or "")

    focus_mode = str(plan.get("focus_mode", "") or "")
    detail_framing = str(plan.get("framing_prompt", "") or "") if focus_mode in {
        "Extreme Close-Up", "Regional Close-Up"
    } else ""
    distortion = ""
    if plan.get("distortion_guard") == "On — Natural Rectilinear":
        distortion = "natural rectilinear perspective; no fisheye, ultra-wide distortion, or overhead compression"
    return _join(
        detail_framing,
        plan.get("camera_prompt", ""),
        distortion,
        plan.get("pose_prompt", ""),
        plan.get("expression_prompt", ""),
        plan.get("environment_prompt", ""),
    )


def _replace_exact_phrase_v224(text: str, phrase: str, replacement: str = "") -> str:
    value = str(text or "")
    phrase = str(phrase or "").strip()
    if not phrase:
        return value
    value = value.replace(phrase, replacement)
    value = re.sub(r"\s*,\s*,+", ", ", value)
    return value.strip(" ,")


class CharacterBlueprintCreatorV224(CharacterBlueprintCreatorV222):
    CATEGORY = "character creation/v2"
    FUNCTION = "build_blueprint_v224"
    DESCRIPTION = (
        "Current Character Creator. Adds a dedicated pubic-hair grooming authority, "
        "keeps advanced lower-body notes separate, and removes redundant mark-negation text from identity notes."
    )

    @classmethod
    def INPUT_TYPES(cls):
        old = CharacterBlueprintCreatorV22.INPUT_TYPES()["required"]
        required = {}
        for name, spec in old.items():
            if name == "buttocks":
                required[name] = spec
                required["pubic_hair_style"] = (PUBIC_HAIR_STYLES_V224, {"default": "Unspecified"})
                required["custom_pubic_hair_style"] = ("STRING", {"default": "", "multiline": False})
                required["use_advanced_lower_body_notes"] = (["Off", "On"], {"default": "Off"})
                continue
            if name == "lower_body_notes":
                required["advanced_lower_body_notes"] = (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "placeholder": "Optional advanced lower-body anatomy details. Pubic-hair grooming belongs in the dedicated selector above.",
                    },
                )
                continue
            required[name] = spec
        return {"required": required}

    def build_blueprint_v224(
        self,
        gender, age_range, heritage, custom_heritage, skin_tone, complexion, face_shape, jaw_shape,
        chin_shape, eye_color, eye_shape, eyebrow_shape, nose_shape, lip_shape, hair_color,
        custom_hair_color, hair_length, custom_hair_length, hair_texture, custom_hair_texture,
        hair_style, custom_hair_style, facial_hair, custom_facial_hair, male_chest,
        custom_male_chest, male_genital_size, height, body_type, bust_size, bust_shape,
        bust_position, bust_firmness, bust_augmentation, buttocks, pubic_hair_style,
        custom_pubic_hair_style, use_advanced_lower_body_notes, presentation_mode,
        custom_presentation_body_basis, custom_presentation_prompt, outfit_source, outfit_preset,
        exact_outfit_text, structured_outfit_type, structured_top, structured_bottom,
        structured_footwear, structured_outerwear, structured_one_piece, structured_swimwear_top,
        structured_swimwear_bottom, lingerie_style, custom_lingerie_description, outfit_notes,
        jewelry_level, jewelry_description, tattoo_status, tattoo_descriptors, piercing_status,
        piercing_input_mode, piercing_descriptors, piercing_location, piercing_type,
        piercing_material, piercing_visibility, structured_piercing_custom, custom_identity_notes,
        advanced_lower_body_notes,
    ):
        cleaned_identity_notes, removed_mark_clauses = _clean_mark_negations_v224(
            custom_identity_notes, tattoo_status, piercing_status
        )
        lower_notes = advanced_lower_body_notes if use_advanced_lower_body_notes == "On" else ""
        pubic_prompt = _pubic_hair_prompt_v224(gender, pubic_hair_style, custom_pubic_hair_style)

        result = list(super().build_blueprint_v222(
            gender=gender, age_range=age_range, heritage=heritage, custom_heritage=custom_heritage,
            skin_tone=skin_tone, complexion=complexion, face_shape=face_shape, jaw_shape=jaw_shape,
            chin_shape=chin_shape, eye_color=eye_color, eye_shape=eye_shape,
            eyebrow_shape=eyebrow_shape, nose_shape=nose_shape, lip_shape=lip_shape,
            hair_color=hair_color, custom_hair_color=custom_hair_color,
            hair_length=hair_length, custom_hair_length=custom_hair_length,
            hair_texture=hair_texture, custom_hair_texture=custom_hair_texture,
            hair_style=hair_style, custom_hair_style=custom_hair_style,
            facial_hair=facial_hair, custom_facial_hair=custom_facial_hair,
            male_chest=male_chest, custom_male_chest=custom_male_chest,
            male_genital_size=male_genital_size, height=height, body_type=body_type,
            bust_size=bust_size, bust_shape=bust_shape, bust_position=bust_position,
            bust_firmness=bust_firmness, bust_augmentation=bust_augmentation,
            buttocks=buttocks, presentation_mode=presentation_mode,
            custom_presentation_body_basis=custom_presentation_body_basis,
            custom_presentation_prompt=custom_presentation_prompt,
            outfit_source=outfit_source, outfit_preset=outfit_preset,
            exact_outfit_text=exact_outfit_text, structured_outfit_type=structured_outfit_type,
            structured_top=structured_top, structured_bottom=structured_bottom,
            structured_footwear=structured_footwear, structured_outerwear=structured_outerwear,
            structured_one_piece=structured_one_piece,
            structured_swimwear_top=structured_swimwear_top,
            structured_swimwear_bottom=structured_swimwear_bottom,
            lingerie_style=lingerie_style,
            custom_lingerie_description=custom_lingerie_description,
            outfit_notes=outfit_notes, jewelry_level=jewelry_level,
            jewelry_description=jewelry_description, tattoo_status=tattoo_status,
            tattoo_descriptors=tattoo_descriptors, piercing_status=piercing_status,
            piercing_input_mode=piercing_input_mode, piercing_descriptors=piercing_descriptors,
            piercing_location=piercing_location, piercing_type=piercing_type,
            piercing_material=piercing_material, piercing_visibility=piercing_visibility,
            structured_piercing_custom=structured_piercing_custom,
            custom_identity_notes=cleaned_identity_notes, lower_body_notes=lower_notes,
        ))

        profile = dict(result[8])
        old_lower = str(profile.get("anatomy_lower_body", "") or "")
        new_lower = _join(pubic_prompt, old_lower)
        if pubic_prompt:
            result[2] = new_lower
            result[13] = new_lower
            profile["lower_body_identity"] = new_lower
            profile["anatomy_lower_body"] = new_lower
            for idx, key in (
                (6, "full_profile_prompt"),
                (17, "active_body_prompt"),
                (18, "active_character_prompt"),
                (20, "clinical_character_prompt"),
            ):
                current = str(result[idx] or "")
                if old_lower and old_lower in current:
                    current = current.replace(old_lower, new_lower)
                elif key in {"active_body_prompt", "active_character_prompt", "clinical_character_prompt"} and presentation_mode == "Clinical Anatomy":
                    current = _join(current, pubic_prompt)
                result[idx] = current
                profile[key] = current

        # Krea positive prompts should not repeatedly name an unwanted mark.
        # The assembler emits positive surface/jewelry authority instead.
        old_tattoo_lock = str(result[22] or "")
        old_piercing_lock = str(result[23] or "")
        if tattoo_status == "None":
            profile["tattoo_count_lock"] = ""
            result[22] = ""
        if piercing_status == "None":
            profile["piercing_count_lock"] = ""
            result[23] = ""
        if tattoo_status == "None" or piercing_status == "None":
            for idx, key in (
                (6, "full_profile_prompt"),
                (18, "active_character_prompt"),
                (19, "clothed_character_prompt"),
                (20, "clinical_character_prompt"),
            ):
                current = str(result[idx] or "")
                if tattoo_status == "None":
                    current = _replace_exact_phrase_v224(current, old_tattoo_lock)
                if piercing_status == "None":
                    current = _replace_exact_phrase_v224(current, old_piercing_lock)
                result[idx] = current
                profile[key] = current
        if removed_mark_clauses:
            warning = (
                "Redundant custom identity mark-negation text was ignored because Tattoo/Piercing Status is authoritative: "
                + "; ".join(removed_mark_clauses)
            )
            result[9] = _join(result[9], warning)
            profile["warnings"] = result[9]

        profile.update({
            "schema": "CHARACTER_BLUEPRINT_V224",
            "schema_version": 9,
            "pubic_hair_style": pubic_hair_style,
            "pubic_hair_prompt": pubic_prompt,
            "use_advanced_lower_body_notes": use_advanced_lower_body_notes,
            "advanced_lower_body_notes": lower_notes,
            "tattoo_status": tattoo_status,
            "piercing_status": piercing_status,
        })
        summary = str(result[21] or "")
        if tattoo_status == "None":
            summary = summary.replace(
                f"Tattoo Count Lock: {old_tattoo_lock}",
                "Tattoo Path: None → positive naturally-unmarked-skin authority in the assembler",
            )
        if piercing_status == "None":
            summary = summary.replace(
                f"Piercing Count Lock: {old_piercing_lock}",
                "Piercing Path: None → positive jewelry-free authority in the assembler",
            )
        summary += "\n" + "\n".join([
            f"Pubic Hair Path: {pubic_hair_style} → {pubic_prompt or '[unspecified/inactive]'}",
            f"Advanced Lower-Body Notes: {'active' if lower_notes else 'inactive'}",
            f"Skin Marking Path: {'naturally unmarked skin authority' if tattoo_status == 'None' else tattoo_status}",
        ])
        result[21] = summary
        profile["presentation_summary"] = summary
        result[8] = profile
        result[15] = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        return tuple(result)


class CharacterPromptAssemblerV224(CharacterPromptAssemblerV222):
    CATEGORY = "character creation/v2"
    FUNCTION = "assemble_prompt_v224"
    DESCRIPTION = (
        "Current compact assembler. Places active pubic-hair grooming beside lower-body anatomy, "
        "uses positive unmarked-skin authority for tattoo-free Krea generation, and removes prompt-only canvas clutter."
    )

    def assemble_prompt_v224(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan = shot_plan if isinstance(shot_plan, dict) else {}
        gender_authority = profile.get(
            "gender_authority_prompt",
            _gender_authority_prompt_v2(profile.get("gender", "Adult Nonbinary")),
        )
        identity_details = profile.get("identity_detail_prompt") or profile.get("face_identity", "adult subject")
        while identity_details.startswith(gender_authority):
            identity_details = identity_details[len(gender_authority):].lstrip(" ,;")
        identity_details = re.sub(
            r"^adult subject\s*,\s*adult (?:female|male|nonbinary)\s*,\s*",
            "",
            identity_details,
            flags=re.IGNORECASE,
        )

        crop_authority = _crop_authority_v222(plan)
        # Dimensions are wired to the latent. Keep this only as a debug output,
        # not as extra prose in the model prompt.
        resolution_authority = _resolution_authority_v222(plan)
        visible_presentation = _visible_outfit_prompt_v222(profile, plan)
        visible_body, visible_bust, visible_lower = _visible_body_prompts_v222(profile, plan)
        pubic_prompt = str(profile.get("pubic_hair_prompt", "") or "")
        if pubic_prompt:
            visible_lower = _replace_exact_phrase_v224(visible_lower, pubic_prompt)
        active_pubic = pubic_prompt if (
            profile.get("presentation_mode") == "Clinical Anatomy" and _crop_shows_pubic_region_v224(plan)
        ) else ""

        qwen = generation_purpose.startswith("Qwen")
        krea = generation_purpose.startswith("Krea")
        presentation_mode = profile.get("presentation_mode", "Legacy / Unspecified")
        skin_surface_authority = _skin_surface_authority_v224(profile, qwen)
        body_jewelry_authority = _body_jewelry_authority_v224(profile, qwen)
        if presentation_mode == "Clinical Anatomy" and profile.get("piercing_status") == "None":
            visible_presentation = (
                "unclothed adult subject in neutral non-aroused clinical anatomy documentation; "
                "all clothing and removable accessories are absent"
            )
        marks = profile.get("marks_prompt", "") if profile.get("tattoo_status") != "None" or profile.get("piercing_status") != "None" else ""
        tattoo_count_lock = profile.get("tattoo_count_lock", "") if profile.get("tattoo_status") != "None" else ""
        piercing_count_lock = profile.get("piercing_count_lock", "") if profile.get("piercing_status") != "None" else ""
        anatomy_integrity_lock = profile.get("anatomy_integrity_lock", "")
        character_id = profile.get("character_id", "character")
        compact_shot = _compact_shot_prompt_v224(plan)
        width = int(plan.get("recommended_width", 1024))
        height = int(plan.get("recommended_height", 1280))
        focus_region = plan.get("focus_region", "")
        advisory = _body_visibility_advisory_v221(profile, plan)

        if generation_purpose == "Krea — First Identity Image":
            purpose_prefix = "realistic camera photograph of the exact adult character"
            reference = "None — text-to-image"
        elif generation_purpose == "Krea — LoRA Expansion":
            purpose_prefix = "realistic camera photograph using the loaded identity LoRA and exact character specification"
            reference = "Mini or final identity LoRA loaded in the Krea model lane"
        elif generation_purpose == "Qwen — Identity Documentation":
            purpose_prefix = _join(
                f"edit {reference_label} into identity documentation of the same adult person",
                f"preserve the exact recognizable identity and all defined permanent marks from {reference_label}",
                "replace the original framing and pose with the active Shot Control settings",
            )
            reference = reference_label
        elif generation_purpose == "Qwen — Anatomy Documentation":
            purpose_prefix = _join(
                f"edit {reference_label} into neutral clinical anatomy documentation of the same adult person",
                f"preserve the exact recognizable identity and defined permanent marks from {reference_label}",
                "replace the original framing and pose with the active Shot Control settings",
            )
            reference = reference_label
        elif generation_purpose == "Qwen — Clothed Action / Lifestyle":
            purpose_prefix = _join(
                f"edit {reference_label} into a realistic action or lifestyle photograph of the same adult person",
                f"preserve the exact recognizable identity and defined permanent marks from {reference_label}",
                "use the active Character Creator outfit and Shot Control pose",
            )
            reference = reference_label
        else:
            purpose_prefix = _join(
                f"edit {reference_label} into a realistic camera photograph of the same adult person",
                f"preserve the exact recognizable identity and defined permanent marks from {reference_label}",
                "use the active Character Creator and Shot Control settings",
            )
            reference = reference_label

        focus_lock = ""
        if focus_region:
            focus_lock = _join(
                f"documentation focus: {focus_region}",
                "keep only the defined permanent marks that belong inside this crop at their exact location",
                _focus_specific_integrity_lock_v22(focus_region),
            )

        final_prompt = _join(
            trigger_word if krea else "",
            custom_prefix,
            purpose_prefix,
            gender_authority,
            skin_surface_authority,
            body_jewelry_authority,
            crop_authority,
            visible_body,
            visible_bust,
            active_pubic,
            visible_presentation,
            compact_shot,
            identity_details,
            marks,
            visible_lower,
            tattoo_count_lock,
            piercing_count_lock,
            anatomy_integrity_lock,
            focus_lock,
            custom_suffix,
        )
        krea_prompt = final_prompt if krea else ""
        qwen_prompt = final_prompt if qwen else ""
        shot_id = _slug(_join(
            character_id, generation_purpose, plan.get("planner_mode", ""),
            plan.get("shot_type", ""), plan.get("focus_region", ""),
            plan.get("camera_view", ""), plan.get("pose", ""),
        ))
        notes = "\n".join([
            f"Purpose: {generation_purpose}",
            f"Reference: {reference}",
            "Identity/anatomy/clothing authority: FCC Character Creator current",
            "Camera/pose/focus authority: FCC Universal Shot Control current",
            "Actual resolution is routed to the latent; canvas dimensions are omitted from the text prompt.",
            "Tattoo Status None uses positive naturally-unmarked-skin language instead of repeating the unwanted tattoo token.",
            f"Body visibility advisory: {advisory or 'None'}",
        ])
        active_summary = "\n\n".join([
            profile.get("presentation_summary", f"Presentation mode: {presentation_mode}"),
            plan.get("active_settings_summary", "Shot settings unavailable"),
            f"CROP AUTHORITY\n{crop_authority or '[custom/unspecified]'}",
            f"ACTIVE PUBIC-HAIR AUTHORITY\n{active_pubic or '[inactive for this crop/presentation]'}",
            f"SKIN-SURFACE AUTHORITY\n{skin_surface_authority or '[defined tattoo path active]'}",
            f"BODY-JEWELRY AUTHORITY\n{body_jewelry_authority or '[defined piercing path active]'}",
            f"VISIBLE WARDROBE\n{visible_presentation or '[none]'}",
            f"RESOLUTION ROUTING (debug only)\n{resolution_authority}",
            notes,
        ])
        return (
            krea_prompt, qwen_prompt, compact_shot, visible_presentation, marks, reference, shot_id,
            width, height, character_id, notes, presentation_mode, active_summary, final_prompt,
            crop_authority, visible_presentation, resolution_authority,
        )
