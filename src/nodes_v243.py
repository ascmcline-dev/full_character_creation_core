from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from .nodes import (
    ASPECT_RATIOS_V2,
    BACKGROUNDS_V2,
    BACKGROUND_PROMPTS_V2,
    BUST_SHAPE_PROMPTS,
    FCCDatasetDirector,
    FCCQueueItemRouter,
    PRESET_OUTFITS,
    SHOT_TYPES_V2,
    _slug,
)
from .nodes_v230 import (
    CAMERA_HEIGHT_PROMPTS_V2,
    LENS_PROMPTS_V2,
    CharacterPromptAssemblerV230,
    _clean_phrase,
    _crop_prompt_v230,
    _focus_identity_prompt_v231,
    _focus_value_v231,
    _is_extreme_closeup_v231,
    _sentences,
)
from .nodes_v240 import (
    FACE_TAGS,
    LOWER_TAGS,
    MID_TAGS,
    UPPER_TAGS,
    _focus_tags,
    _upper_body_shape,
)
from .nodes_v241 import (
    CharacterBlueprintCreatorV241,
    CharacterPromptAssemblerV241,
    CharacterShotControlV241,
    QwenDatasetQueueV241,
    TAN_LINE_PATTERNS_V241,
    _camera_view,
    _identity_for_view,
    _is_direct_back,
    _is_rear_orientation,
    _macro_sections_v241,
    _piercing_phrase_v241,
    _rebuild_shot_summary,
    _record_matches_extreme_v241,
    _tan_base_v241,
    _tattoo_phrase_v241,
)
from .nodes_v242 import (
    POSES_V242,
    SIDE_LYING_LEFT,
    SIDE_LYING_POSES,
    SIDE_LYING_RIGHT,
    CharacterBlueprintCreatorV242,
    CharacterPromptAssemblerV242,
    CharacterShotControlV242,
    QwenDatasetQueueV242,
)

# -----------------------------------------------------------------------------
# V2.4.3 / Studio V2.8.3
# - region-first prompt compilation for regional documentation crops
# - exact mark-coverage checks (covered nipple jewelry no longer leaks)
# - stronger left/right side-lying contact and vertical-stack language
# - automatic landscape framing for horizontal full-body poses
# - automatic portrait 2:3 framing for standing three-quarter/full-body shots
# - compact skin-pigment-only tan-line descriptions (no garment hallucination)
# - structured Top Only and Bottom Only hybrid presentation modes
# - Beach, Bar, Club, and Pool Hall location presets
# -----------------------------------------------------------------------------

AUTO_ASPECT = "Auto by Shot"
ASPECT_RATIOS_V243 = [AUTO_ASPECT] + list(ASPECT_RATIOS_V2)

BACKGROUNDS_V243 = [x for x in BACKGROUNDS_V2 if x != "Custom"] + [
    "Beach",
    "Bar",
    "Club",
    "Pool Hall",
    "Custom",
]
BACKGROUND_PROMPTS_V243 = dict(BACKGROUND_PROMPTS_V2)
BACKGROUND_PROMPTS_V243.update({
    "Beach": "realistic public beach with natural sand, ocean water, and an ordinary open shoreline",
    "Bar": "realistic casual bar interior with a visible counter, stools, bottles, and believable ambient room detail",
    "Club": "realistic nightlife club interior with a dance floor, practical colored lights, and believable crowd-space depth",
    "Pool Hall": "realistic pool hall with regulation billiard tables, hanging table lights, cue racks, and an ordinary social atmosphere",
})

TOP_ONLY_LAYOUT = "Top Only — Lower Body Unclothed"
BOTTOM_ONLY_LAYOUT = "Bottom Only — Upper Body Unclothed"
STRUCTURED_OUTFIT_TYPES_V243 = [
    "Top + Bottom Outfit",
    "Top Only — Lower Body Unclothed",
    "Bottom Only — Upper Body Unclothed",
    "One-Piece Outfit",
    "Two-Piece Swimwear",
    "Lingerie",
]

WIDE_FULL_BODY = "Wide Full Body / Environmental"
SHOT_TYPES_V243 = [x for x in SHOT_TYPES_V2 if x != "Custom Framing"] + [WIDE_FULL_BODY, "Custom Framing"]

# Tank-top tan-line wording repeatedly resolved as bra-like coverage.  The outfit
# preset remains available; only the tan-line pattern is removed.
TAN_LINE_PATTERNS_V243 = [x for x in TAN_LINE_PATTERNS_V241 if x != "Tank Top"]

BUST_SHAPES_V243 = [
    "Unspecified",
    "Natural Teardrop — Gentle Upper Slope",
    "Round — Even Upper and Lower Fullness",
    "Bell — Narrow Upper / Fuller Lower",
    "Shallow — Wide Base / Low Projection",
    "Projected — Narrow Base / Forward Fullness",
    "East-West — Outward Orientation",
    "Side-Set — Wider Center Space",
    "Close-Set — Narrow Center Space",
    "Pendulous — Natural Lower Hang",
    "Asymmetrical — Natural Left / Right Difference",
    "Slender — Narrow / Elongated",
]

BUST_SHAPE_PROMPTS_V243 = {
    "Natural Teardrop — Gentle Upper Slope": "natural teardrop breast shape with a soft upper slope, the fullest volume in the lower half, and a smooth rounded lower contour",
    "Round — Even Upper and Lower Fullness": "round breast shape with a broad base and evenly distributed upper and lower fullness",
    "Bell — Narrow Upper / Fuller Lower": "bell-shaped breasts with a narrower upper chest attachment and clearly fuller rounded lower volume",
    "Shallow — Wide Base / Low Projection": "shallow breast shape with a wide chest base, low forward projection, and broad gentle contour",
    "Projected — Narrow Base / Forward Fullness": "projected breast shape with a narrower chest base and clearly forward-centered volume",
    "East-West — Outward Orientation": "east-west breast orientation with each breast angled naturally outward from the centerline",
    "Side-Set — Wider Center Space": "side-set breasts with a wider natural space at the sternum and fuller outer-chest placement",
    "Close-Set — Narrow Center Space": "close-set breasts with a narrow natural space at the sternum and centered inner fullness",
    "Pendulous — Natural Lower Hang": "naturally pendulous breast shape with realistic lower hang, gravitational weight, and fuller lower contours",
    "Asymmetrical — Natural Left / Right Difference": "naturally asymmetrical breasts with a modest realistic difference in size, height, or contour between left and right",
    "Slender — Narrow / Elongated": "slender elongated breast shape with a narrow base, modest width, and gentle vertical contour",
}
BUST_SHAPE_PROMPTS.update(BUST_SHAPE_PROMPTS_V243)

REGIONAL_GROUPS: dict[str, str] = {
    "Face Portrait": "face",
    "Head and Neck": "head_neck",
    "Upper Chest": "upper_chest",
    "Chest and Ribcage": "chest",
    "Left Chest Profile": "chest",
    "Right Chest Profile": "chest",
    "Abdomen and Waist": "abdomen",
    "Groin and Pelvis": "groin",
    "Left Groin Profile": "groin",
    "Right Groin Profile": "groin",
    "Hips Front": "hips",
    "Left Hip Profile": "hips",
    "Right Hip Profile": "hips",
    "Buttocks Rear": "buttocks",
    "Left Buttock Profile": "buttocks",
    "Right Buttock Profile": "buttocks",
    "Upper Back and Shoulders": "upper_back",
    "Lower Back and Waist": "lower_back",
    "Left Arm": "arm",
    "Right Arm": "arm",
    "Both Arms": "arm",
    "Left Hand": "hand",
    "Right Hand": "hand",
    "Both Hands": "hand",
    "Left Thigh": "thigh",
    "Right Thigh": "thigh",
    "Both Thighs": "thigh",
    "Left Foot": "foot",
    "Right Foot": "foot",
    "Both Feet": "foot",
}

REGIONAL_TAGS: dict[str, set[str]] = {
    "face": set(FACE_TAGS) | {"neck"},
    "head_neck": set(FACE_TAGS) | {"neck", "shoulders"},
    "upper_chest": {"neck", "shoulders", "upper_chest", "chest", "breast", "nipple", "areola", "sternum", "cleavage"},
    "chest": {"shoulders", "upper_chest", "chest", "breast", "nipple", "areola", "sternum", "ribcage", "upper_abdomen"},
    "abdomen": {"lower_chest", "upper_abdomen", "abdomen", "navel", "waist", "hips"},
    "groin": {"lower_abdomen", "waist", "hips", "pelvis", "groin", "pubic", "genital", "upper_thighs"},
    "hips": {"lower_abdomen", "waist", "hips", "pelvis", "groin", "upper_thighs", "buttocks"},
    "buttocks": {"lower_back", "waist", "hips", "buttocks", "upper_thighs"},
    "upper_back": {"neck", "shoulders", "upper_back", "upper_arms"},
    "lower_back": {"upper_back", "lower_back", "waist", "hips"},
    "arm": {"shoulders", "upper_arms", "arms", "forearms", "hands"},
    "hand": {"forearms", "hands"},
    "thigh": {"hips", "upper_thighs", "thighs", "knees"},
    "foot": {"lower_legs", "ankles", "feet"},
}

REGIONAL_CROPS: dict[str, str] = {
    "face": "tight regional face portrait framed from the complete hairline through just below the chin, with the complete face occupying about eighty percent of the image",
    "head_neck": "tight head-and-neck documentation crop from the complete hairline through the base of the neck, with only the shoulder tops at the lower edge",
    "upper_chest": "tight regional documentation crop centered on the collarbones, sternum, and upper chest; the top edge begins at the base of the neck, the bottom edge ends below the chest line, and both shoulders remain inside the frame",
    "chest": "tight regional documentation crop centered on the chest and ribcage; both sides of the ribcage and the complete visible chest region fill about eighty percent of the frame",
    "abdomen": "tight regional documentation crop centered on the abdomen and waist; the top edge begins below the chest, the navel and natural waist remain centered, and the bottom edge reaches the upper hips",
    "groin": "tight regional documentation crop centered on the pelvis and groin; the top edge begins just below the navel, both hip bones remain inside the frame, and the bottom edge reaches the upper thighs",
    "hips": "tight regional documentation crop centered on the hips and pelvis; the natural waist, both hip contours, and upper thighs remain inside the frame",
    "buttocks": "tight rear regional documentation crop centered on the lower back, hips, and complete buttock region, with the upper thighs visible at the lower edge",
    "upper_back": "tight rear regional documentation crop centered on the upper back and shoulders, from the base of the neck through the lower shoulder blades",
    "lower_back": "tight rear regional documentation crop centered on the lower back and waist, with both waist contours and the upper hips inside the frame",
    "arm": "tight regional documentation crop centered on the selected arm, with the complete selected arm section and its nearest joint landmarks visible",
    "hand": "tight regional documentation crop centered on the selected hand, with the complete hand, fingers, wrist, and a small amount of forearm visible",
    "thigh": "tight regional documentation crop centered on the selected thigh, with the hip crease and knee landmark included where applicable",
    "foot": "tight regional documentation crop centered on the selected foot, with the complete foot, toes, ankle, and a small amount of lower leg visible",
}


def _is_regional(plan: dict) -> bool:
    return str(plan.get("focus_mode", "")) == "Regional Close-Up" or str(plan.get("shot_type", "")) == "Close-Up — Regional Documentation"


def _regional_group(plan: dict) -> str:
    focus = str(plan.get("focus_region", "") or "")
    if focus in REGIONAL_GROUPS:
        return REGIONAL_GROUPS[focus]
    f = focus.lower()
    if "face" in f or "head" in f:
        return "face"
    if "chest" in f or "ribcage" in f or "cleavage" in f:
        return "chest"
    if "abdomen" in f or "navel" in f or "waist" in f:
        return "abdomen"
    if "groin" in f or "pelvis" in f or "pubic" in f:
        return "groin"
    if "butt" in f:
        return "buttocks"
    if "hip" in f:
        return "hips"
    if "back" in f:
        return "upper_back"
    if "hand" in f:
        return "hand"
    if "arm" in f:
        return "arm"
    if "thigh" in f:
        return "thigh"
    if "foot" in f or "feet" in f:
        return "foot"
    return "custom"


def _regional_crop_prompt_v243(plan: dict) -> str:
    group = _regional_group(plan)
    focus = _clean_phrase(plan.get("focus_region", "selected region"))
    return REGIONAL_CROPS.get(
        group,
        f"tight regional documentation crop centered exclusively on {focus.lower()}, with that complete region and only its nearest anatomical landmarks filling about eighty percent of the image",
    )


def _regional_height_prompt(plan: dict) -> str:
    focus = _clean_phrase(plan.get("focus_region", "selected region")).lower()
    height = str(plan.get("camera_height", ""))
    if height == "Slightly Above Eye Level":
        return f"camera centered on the {focus} from only five to ten degrees above the region, using a minimal controlled downward angle"
    if height == "Slightly Below Eye Level":
        return f"camera centered on the {focus} from only five to ten degrees below the region, using a minimal controlled upward angle"
    if height == "High Angle":
        return f"clearly elevated camera centered directly on the {focus}"
    if height == "Low Angle":
        return f"clearly low camera centered directly on the {focus}"
    if height == "Overhead":
        return f"top-down camera centered directly on the {focus}"
    return f"camera axis centered directly on the {focus} and level with the middle of that region"


def _regional_lens_prompt_v243(plan: dict) -> str:
    lens = str(plan.get("lens", ""))
    group = _regional_group(plan)
    if group in {"face", "head_neck"}:
        return LENS_PROMPTS_V2.get(lens, "")
    return {
        "50mm Normal": "rectilinear 50mm normal-lens perspective with natural local body proportions",
        "85mm Portrait — Recommended": "rectilinear 85mm close-detail perspective with natural local proportions",
        "105mm Macro": "rectilinear 105mm macro-lens perspective with precise local surface detail",
        "35mm Environmental": "rectilinear 35mm environmental perspective with controlled local proportions",
    }.get(lens, LENS_PROMPTS_V2.get(lens, "").replace("facial", "local body"))


def _regional_camera_prompt_v243(plan: dict, custom_camera: str = "") -> str:
    if plan.get("camera_height") == "Custom" or plan.get("lens") == "Custom":
        custom = _clean_phrase(custom_camera)
        if custom:
            return custom
    view = _camera_view(plan)
    focus = _clean_phrase(plan.get("focus_region", "selected region")).lower()
    if view == "Back View":
        view_text = f"direct rear-facing documentation view of the {focus}"
    elif view == "Rear Three-Quarter Left":
        view_text = f"rear three-quarter-left documentation view of the {focus}"
    elif view == "Rear Three-Quarter Right":
        view_text = f"rear three-quarter-right documentation view of the {focus}"
    elif view == "Three-Quarter Left":
        view_text = f"front three-quarter-left documentation view of the {focus}"
    elif view == "Three-Quarter Right":
        view_text = f"front three-quarter-right documentation view of the {focus}"
    elif view == "Left Profile":
        view_text = f"left-profile documentation view of the {focus}"
    elif view == "Right Profile":
        view_text = f"right-profile documentation view of the {focus}"
    else:
        view_text = f"straight-on documentation view centered on the {focus}"
    lens = _regional_lens_prompt_v243(plan)
    return _sentences(view_text, _regional_height_prompt(plan), lens)


def _side_contact(pose: str) -> tuple[str, str]:
    return ("left", "right") if pose == SIDE_LYING_LEFT else ("right", "left")


def _side_lying_pose_prompt_v243(pose: str) -> str:
    lower, upper = _side_contact(pose)
    return _sentences(
        f"true ninety-degree lateral side-lying posture with the anatomical {lower} side against the support surface",
        f"the anatomical {lower} ear, outer shoulder, side of the ribcage, waist, outer hip, and outer thigh are the floor-side landmarks",
        f"the anatomical {upper} shoulder, side of the waist, outer hip, and outer thigh face upward and remain the ceiling-side landmarks",
        f"the {upper} shoulder is vertically above the {lower} shoulder and the {upper} hip is vertically above the {lower} hip",
        "the chest plane remains vertical, the pelvis remains vertical, and the sternum does not roll toward the ceiling",
        "the spine remains straight and the knees share a gentle relaxed bend",
        "the floor-side arm rests forward on the surface and the ceiling-side arm rests naturally along the upper side",
    )


def _side_lying_view_prompt_v243(plan: dict) -> str:
    pose = str(plan.get("pose", ""))
    lower, upper = _side_contact(pose)
    view = _camera_view(plan)
    base = _sentences(
        f"the subject's {lower} shoulder and {lower} hip remain the lower contact points",
        f"the subject's {upper} shoulder and {upper} hip remain directly uppermost",
    )
    if view == "Back View":
        return _sentences(
            "rear lateral camera position from behind the side-lying subject",
            base,
            "the spine and back plane face the lens while the sternum points horizontally away from the camera",
            "the camera moves behind the body; the body itself stays vertically stacked",
        )
    if view == "Front View":
        return _sentences(
            "front lateral camera position beside the side-lying subject",
            base,
            "the sternum and navel face horizontally toward the lens while the chest plane remains vertical",
            "the camera moves to the front side of the body; the body itself stays vertically stacked",
        )
    if view == "Rear Three-Quarter Left":
        return _sentences("rear three-quarter-left camera position around the stacked side-lying body", base, "the back remains dominant and the camera supplies the oblique angle")
    if view == "Rear Three-Quarter Right":
        return _sentences("rear three-quarter-right camera position around the stacked side-lying body", base, "the back remains dominant and the camera supplies the oblique angle")
    if view == "Three-Quarter Left":
        return _sentences("front three-quarter-left camera position around the stacked side-lying body", base, "the camera supplies the mild oblique angle while the torso remains stacked")
    if view == "Three-Quarter Right":
        return _sentences("front three-quarter-right camera position around the stacked side-lying body", base, "the camera supplies the mild oblique angle while the torso remains stacked")
    if view == "Left Profile":
        return _sentences("left-side lateral profile camera position", base, "the camera remains parallel to the long axis of the stacked body")
    if view == "Right Profile":
        return _sentences("right-side lateral profile camera position", base, "the camera remains parallel to the long axis of the stacked body")
    return _sentences("clear lateral camera position beside the side-lying subject", base)


def _side_lying_height_prompt_v243(plan: dict) -> str:
    height = str(plan.get("camera_height", ""))
    if height == "Slightly Above Eye Level":
        return "camera only slightly elevated above the side-lying torso, with a gentle five-to-ten-degree downward angle"
    if height == "Slightly Below Eye Level":
        return "camera low near the support surface, centered across the side-lying torso with a gentle upward angle"
    if height == "Eye Level":
        return "camera level with the side-lying torso midline and far enough away to include the complete requested crop"
    return CAMERA_HEIGHT_PROMPTS_V2.get(height, "camera centered on the side-lying torso")


def _body_crop_prompt_v243(plan: dict) -> str:
    shot = str(plan.get("shot_type", ""))
    pose = str(plan.get("pose", ""))
    horizontal = pose in SIDE_LYING_POSES or pose == "Lying Prone / On Stomach"
    if shot == WIDE_FULL_BODY:
        return _sentences(
            "wide environmental full-body composition",
            "the complete head, hair, torso, arms, legs, and both feet are fully inside the frame",
            "the subject occupies approximately fifty-five to sixty-five percent of the frame height",
            "generous environmental space remains around the entire body on every side",
            "the camera is far enough away to prevent cropping at the hair, hands, knees, or feet",
        )
    if shot == "Full Body":
        if horizontal:
            return _sentences(
                "wide horizontal full-body composition",
                "the complete head, hair, torso, arms, legs, and both feet are fully inside the landscape frame",
                "clear breathing room remains beyond the head and beyond the feet",
            )
        return _sentences(
            "full-body composition with the complete head, hair, torso, arms, legs, and both feet fully inside the frame",
            "clear margin remains above the hair and below both feet",
            "the camera is far enough away to preserve the entire body",
        )
    if shot == "Three-Quarter Body":
        if horizontal:
            return _sentences(
                "wide horizontal three-quarter-body composition from the complete head through below both knees",
                "the complete hairline and top of the head remain inside the frame with margin at the head end",
            )
        return _sentences(
            "three-quarter-body composition from the complete head and hair through below both knees",
            "the top of the hair remains fully inside the frame with clear margin above it",
            "the camera is far enough away to include both knees and the complete requested body crop",
        )
    return _clean_phrase(plan.get("framing_prompt", ""))


def _resolve_aspect_v243(plan: dict, requested: str) -> tuple[str, int, int]:
    shot = str(plan.get("shot_type", ""))
    pose = str(plan.get("pose", ""))
    horizontal = pose in SIDE_LYING_POSES or pose == "Lying Prone / On Stomach"
    if shot == WIDE_FULL_BODY:
        return "Landscape 3:2 — Automatic Wide Full Body", 1536, 1024
    if horizontal and shot in {"Three-Quarter Body", "Full Body"}:
        return "Landscape 3:2 — Automatic for Horizontal Pose", 1536, 1024
    if requested == AUTO_ASPECT:
        if _is_extreme_closeup_v231(plan) or _is_regional(plan):
            return "Square 1:1 — Automatic by Shot", 1024, 1024
        if shot in {"Three-Quarter Body", "Full Body"}:
            return "Portrait 2:3 — Automatic by Shot", 1024, 1536
        return "Portrait 4:5 — Automatic by Shot", 1024, 1280
    dims = {
        "Square 1:1": (1024, 1024),
        "Portrait 4:5": (1024, 1280),
        "Portrait 2:3": (1024, 1536),
        "Landscape 3:2": (1536, 1024),
    }.get(requested, (1024, 1280))
    return requested, dims[0], dims[1]


def _visible_tags_v243(plan: dict) -> set[str]:
    if _is_regional(plan):
        tags = set(REGIONAL_TAGS.get(_regional_group(plan), _focus_tags(plan.get("focus_region", ""))))
    else:
        # import lazily to keep the inheritance module compact
        from .nodes_v241 import _visible_tags_v241
        tags = set(_visible_tags_v241(plan))
    if _is_rear_orientation(plan):
        tags -= set(FACE_TAGS)
    if _is_direct_back(plan):
        tags -= {"upper_chest", "chest", "breast", "nipple", "areola", "abdomen", "navel", "groin", "pubic", "genital", "cleavage", "sternum"}
    return tags


def _coverage_tags_v243(profile: dict) -> set[str]:
    if profile.get("presentation_mode") != "Clothed Character":
        return set()
    components = profile.get("outfit_components") if isinstance(profile.get("outfit_components"), dict) else {}
    kind = str(components.get("kind", "complete"))
    if kind == "swimwear":
        return {"breast", "nipple", "areola", "groin", "pubic", "genital"}
    if kind == "one_piece":
        return {"chest", "breast", "nipple", "areola", "abdomen", "waist", "groin", "pubic", "genital", "upper_back", "lower_back", "buttocks"}
    if kind == "lingerie":
        return {"breast", "nipple", "areola", "groin", "pubic", "genital"}

    covered: set[str] = set()
    top = " ".join(str(components.get(k, "")) for k in ("top", "outerwear", "raw")).lower()
    bottom = " ".join(str(components.get(k, "")) for k in ("bottom", "raw")).lower()
    footwear = str(components.get("footwear", "")).lower()
    if kind != "bottom_only" and top:
        covered |= {"chest", "breast", "nipple", "areola", "abdomen", "upper_back", "lower_back"}
        if any(x in top for x in ("long sleeve", "long-sleeve", "jacket", "hoodie", "sweater", "coat")):
            covered |= {"upper_arms", "forearms", "arms"}
        elif any(x in top for x in ("t-shirt", "tee", "short sleeve", "short-sleeve")):
            covered |= {"upper_arms"}
    if kind != "top_only" and bottom:
        covered |= {"hips", "groin", "pubic", "genital", "buttocks", "upper_thighs"}
        if any(x in bottom for x in ("jeans", "pants", "trousers", "leggings")):
            covered |= {"thighs", "legs", "knees"}
    if footwear:
        covered |= {"feet"}
    return covered


def _record_exactly_covered(record: dict[str, Any], covered: set[str]) -> bool:
    location = str(record.get("location", "")).lower()
    rules = [
        (("nipple", "areola"), {"nipple", "areola", "breast"}),
        (("navel",), {"navel", "abdomen"}),
        (("pubic", "groin", "genital"), {"pubic", "groin", "genital"}),
        (("full abdomen", "abdomen"), {"abdomen"}),
        (("cleavage", "center chest", "upper left chest", "upper right chest"), {"chest", "breast", "upper_chest"}),
        (("full back", "upper back"), {"upper_back"}),
        (("lower back", "tramp stamp"), {"lower_back"}),
        (("forearm",), {"forearms", "arms"}),
        (("upper arm",), {"upper_arms", "arms"}),
        (("buttock",), {"buttocks"}),
        (("thigh",), {"upper_thighs", "thighs"}),
        (("foot",), {"feet"}),
    ]
    for tokens, exact in rules:
        if any(token in location for token in tokens):
            return bool(covered & exact)
    return False


def _record_visible_v243(record: dict[str, Any], visible: set[str], covered: set[str], plan: dict) -> bool:
    location = str(record.get("location", ""))
    rear_only = {"Full Back", "Upper Back", "Lower Back", "Lower Back / Tramp Stamp", "Buttocks", "Left Buttock", "Right Buttock"}
    front_only = {"Full Abdomen", "Abdomen", "Navel", "Cleavage / Center Chest", "Upper Left Chest", "Upper Right Chest", "Chest", "Pubic Mons", "Groin"}
    if location in rear_only and not _is_rear_orientation(plan):
        return False
    if location in front_only and _is_direct_back(plan):
        return False
    tags = set(record.get("region_tags", []))
    if "unknown" in tags:
        return not _is_regional(plan) and len(visible & (UPPER_TAGS | MID_TAGS | LOWER_TAGS)) > 8
    overlap = tags & visible
    if not overlap:
        return False
    if _record_exactly_covered(record, covered):
        return False
    return bool(overlap - covered) or not bool(tags & covered)


def _visible_marks_v243(profile: dict, plan: dict) -> tuple[str, list[dict], list[dict]]:
    visible = _visible_tags_v243(plan)
    covered = _coverage_tags_v243(profile)
    extreme = _is_extreme_closeup_v231(plan)
    focus = _focus_value_v231(plan) if extreme else ""
    tattoos = [r for r in profile.get("tattoo_records", []) if _record_visible_v243(r, visible, covered, plan) and (not extreme or _record_matches_extreme_v241(r, focus))]
    piercings = [r for r in profile.get("piercing_records", []) if _record_visible_v243(r, visible, covered, plan) and (not extreme or _record_matches_extreme_v241(r, focus))]
    tattoo_phrases = [_tattoo_phrase_v241(r) for r in tattoos if _tattoo_phrase_v241(r)]
    piercing_phrases = [_piercing_phrase_v241(r) for r in piercings if _piercing_phrase_v241(r)]
    return _sentences(
        "visible permanent skin marking: " + "; ".join(tattoo_phrases) if tattoo_phrases else "",
        "visible permanent jewelry: " + "; ".join(piercing_phrases) if piercing_phrases else "",
    ), tattoos, piercings


def _tan_strength_v243(strength: str) -> str:
    return {
        "Subtle": "barely perceptible softly diffused one-step tonal shift",
        "Moderate": "clearly visible naturally blended tonal contrast",
        "Distinct": "strong clean high-contrast tonal boundary",
    }.get(strength, "clearly visible naturally blended tonal contrast")


def _tan_pattern_phrase_v243(pattern: str, visible: set[str], strength: str, rear: bool) -> str:
    words = _tan_strength_v243(strength)
    subtle = strength == "Subtle"
    chest = bool(visible & {"chest", "upper_chest", "breast", "upper_back", "shoulders"})
    lower = bool(visible & {"hips", "groin", "buttocks", "upper_thighs", "lower_back"})
    abdomen = bool(visible & {"abdomen", "waist"})
    parts: list[str] = []
    skin_only = "the variation is flush skin coloration with broad natural blending into the surrounding tan"

    # Subtle mode deliberately avoids geometric garment-shaped language and
    # emits one low-weight sentence. Repeating one phrase per body region made
    # Krea exaggerate an intended faint variation.
    if subtle:
        areas: list[str] = []
        if chest:
            areas.append("upper-back and shoulder skin" if rear else "central upper-chest skin")
        if abdomen:
            areas.append("central torso skin")
        if lower:
            areas.append("high-hip and upper-buttock skin" if rear else "high-hip and central lower-torso skin")
        if areas:
            joined = ", ".join(areas[:-1]) + (" and " if len(areas) > 1 else "") + areas[-1]
            return _sentences(
                f"nearly imperceptible softly diffused sun-exposure variation across limited {joined}",
                "the edges dissolve gradually into the surrounding tan and read only as a slight natural skin-tone shift",
            )
        return ""

    if pattern == "String Bikini — Minimal Triangle and Tight V":
        if chest:
            if rear:
                parts.append(f"{words} forming narrow less-tanned skin-color zones across the upper back and shoulder line; {skin_only}")
            else:
                parts.append(f"{words} forming two small triangular less-tanned skin-color zones centered over the chest, with narrow pigment transitions extending toward the shoulders; {skin_only}")
        if lower:
            if rear:
                parts.append(f"{words} forming a narrow V-shaped less-tanned skin-color zone across the high hips and upper buttock area; {skin_only}")
            else:
                parts.append(f"{words} forming a tight V-shaped less-tanned skin-color zone over the central lower torso and high hips; {skin_only}")
    elif pattern == "Standard Bikini Top and Bottom":
        if chest:
            region = "upper-back and shoulder skin" if rear else "upper-chest skin"
            parts.append(f"{words} forming medium-size less-tanned skin-color zones across the {region}; {skin_only}")
        if lower:
            region = "high hips and upper buttock skin" if rear else "high hips and central lower-torso skin"
            parts.append(f"{words} forming a medium-size less-tanned skin-color zone across the {region}; {skin_only}")
    elif pattern == "One-Piece Swimsuit":
        if chest or abdomen or lower:
            region = "rear torso and hips" if rear else "front torso from chest through abdomen to hips"
            parts.append(f"{words} forming one continuous less-tanned torso-shaped skin-color zone across the visible {region}; {skin_only}")
    elif pattern == "Bra and Brief":
        if chest:
            region = "upper-back skin" if rear else "chest skin"
            parts.append(f"{words} forming two rounded less-tanned skin-color zones across the visible {region}; {skin_only}")
        if lower:
            region = "hips and upper buttock skin" if rear else "hips and central lower-torso skin"
            parts.append(f"{words} forming a compact less-tanned skin-color zone across the visible {region}; {skin_only}")
    elif pattern == "T-Shirt":
        parts.append(f"{words} forming a higher neckline boundary and short-sleeve-length skin-color transitions across the visible neck and upper arms; {skin_only}")
    elif pattern == "Shorts":
        parts.append(f"{words} forming horizontal less-tanned skin-color transitions across the visible thighs; {skin_only}")
    elif pattern == "Socks / Footwear":
        parts.append(f"{words} forming less-tanned skin-color transitions across the visible ankles and feet; {skin_only}")
    elif pattern == "Mixed Clothing Tan Lines":
        parts.append(f"{words} forming mixed less-tanned skin-color zones limited to the visible body regions; {skin_only}")
    return _sentences(*parts)

def _tan_prompt_for_plan_v243(profile: dict, plan: dict) -> str:
    base = _tan_base_v241(profile)
    if not base:
        return ""
    state = str(profile.get("tan_line_state", "Even Tan — No Defined Lines"))
    if state == "Even Tan — No Defined Lines":
        return base
    if state == "Custom":
        return _sentences(base, _clean_phrase(profile.get("custom_tan_description", "")))
    visible = _visible_tags_v243(plan)
    pattern = str(profile.get("tan_line_pattern", "String Bikini — Minimal Triangle and Tight V"))
    phrase = _tan_pattern_phrase_v243(pattern, visible, str(profile.get("tan_line_visibility", "Moderate")), _is_rear_orientation(plan))
    return _sentences(base, phrase)


def _region_identity_v243(profile: dict, plan: dict) -> str:
    group = _regional_group(plan)
    if group in {"face", "head_neck"}:
        return _identity_for_view(profile, plan)
    # Non-face regional crops must not receive facial-presentation language.
    # That language was repeatedly pulling the complete head into chest/groin crops.
    gender_value = str(profile.get("primary_character_gender", profile.get("gender", "")))
    gender = {
        "Adult Woman": "the primary character is an adult woman",
        "Adult Female": "the primary character is an adult woman",
        "Adult Man": "the primary character is an adult man",
        "Adult Male": "the primary character is an adult man",
        "Adult Nonbinary": "the primary character is an adult nonbinary person",
    }.get(gender_value, "the primary character is an adult person")
    age = f"age range {profile.get('age_range')}" if profile.get("age_range") else ""
    skin = str(profile.get("skin_tone", "") or "")
    complexion = str(profile.get("complexion", "") or "")
    return _sentences(
        gender,
        age,
        f"{skin.lower()} skin tone" if skin not in {"", "Unspecified", "Custom / Unspecified"} else "",
        complexion.lower() if complexion not in {"", "Unspecified", "Custom / Unspecified"} else "",
    )


def _regional_body_v243(profile: dict, plan: dict) -> str:
    group = _regional_group(plan)
    mode = str(profile.get("presentation_mode", "Clothed Character"))
    components = profile.get("outfit_components") if isinstance(profile.get("outfit_components"), dict) else {}
    kind = str(components.get("kind", "complete"))
    upper_uncovered = mode == "Clinical Anatomy" or kind == "bottom_only"
    lower_uncovered = mode == "Clinical Anatomy" or kind == "top_only"
    rear = _is_rear_orientation(plan)
    parts: list[str] = []

    if group in {"upper_chest", "chest", "upper_back"}:
        parts.append(_upper_body_shape(profile))
        if upper_uncovered and group != "upper_back" and not rear:
            parts.append(_clean_phrase(profile.get("chest_anatomy_prompt", "")))
        elif not upper_uncovered and group != "upper_back" and not rear:
            size = str(profile.get("bust_size", "Unspecified"))
            if profile.get("resolved_chest_anatomy") == "Bust Anatomy — Use Bust Controls" and size != "Unspecified":
                parts.append(f"the selected {size.lower()} bust size subtly shapes the covered upper garment")
    elif group == "abdomen":
        parts.append("the selected torso build, natural waist, and abdominal proportions remain consistent")
    elif group in {"groin", "hips", "buttocks", "thigh"}:
        parts.append(_clean_phrase(profile.get("clothed_lower_body", "")))
        if lower_uncovered and group == "groin" and not rear:
            parts.append(_clean_phrase(profile.get("groin_anatomy_prompt", "")))
            parts.append(_clean_phrase(profile.get("pubic_hair_prompt", "")))
    elif group in {"arm", "hand"}:
        parts.append("the selected arm and hand proportions remain consistent with the character's body build")
    elif group == "foot":
        parts.append("the selected foot and ankle proportions remain consistent with the character's body build")
    return _sentences(*parts)


def _regional_presentation_v243(profile: dict, plan: dict) -> str:
    mode = str(profile.get("presentation_mode", "Clothed Character"))
    if mode == "Clinical Anatomy":
        return "unclothed neutral non-aroused clinical anatomy documentation"
    if mode != "Clothed Character":
        return _clean_phrase(profile.get("active_presentation_prompt", ""))

    components = profile.get("outfit_components") if isinstance(profile.get("outfit_components"), dict) else {}
    kind = str(components.get("kind", "complete"))
    top = _clean_phrase(components.get("top") or components.get("one_piece") or components.get("swimwear_top") or components.get("raw") or "")
    bottom = _clean_phrase(components.get("bottom") or components.get("one_piece") or components.get("swimwear_bottom") or components.get("raw") or "")
    footwear = _clean_phrase(components.get("footwear", ""))
    group = _regional_group(plan)
    rear = _is_rear_orientation(plan)

    if group == "face":
        return ""
    if group == "head_neck":
        if kind == "swimwear" and top:
            return "only the thin upper shoulder or halter straps are visible at the lower edge of the crop"
        return f"only the neckline and shoulder edge of {top} are visible at the lower edge" if top and kind != "bottom_only" else ""
    if group in {"upper_chest", "chest", "upper_back", "arm"}:
        if kind == "bottom_only":
            return "the upper torso is uncovered"
        if not top:
            return ""
        if kind == "swimwear":
            rear_text = "the back straps and ties of" if rear else "the complete covered top portion of"
            return _sentences(f"{rear_text} {top} are visible", "the fabric remains securely positioned over the covered chest area")
        return f"wearing {top} with normal secure upper-body coverage"
    if group == "abdomen":
        parts = []
        if top and kind != "bottom_only":
            parts.append(f"the lower edge of {top} is visible above the abdomen")
        if bottom and kind != "top_only":
            parts.append(f"the upper waistband edge of {bottom} is visible below the abdomen")
        return _sentences(*parts)
    if group in {"groin", "hips", "buttocks", "thigh"}:
        if kind == "top_only":
            return "the lower body is uncovered"
        if not bottom:
            return ""
        if kind == "swimwear":
            rear_bottom = bottom.replace("V-front", "narrow rear").replace("v-front", "narrow rear") if rear else bottom
            return _sentences(f"wearing {rear_bottom}", "the covered lower-body fabric remains securely positioned with visible seams and ties")
        return f"wearing {bottom} with normal secure lower-body coverage"
    if group == "foot":
        return f"wearing {footwear}" if footwear else ""
    return ""


def _visible_body_and_presentation_v243(profile: dict, plan: dict) -> tuple[str, str, str]:
    if _is_regional(plan):
        return _regional_body_v243(profile, plan), _regional_presentation_v243(profile, plan), "regional"

    # Use V2.4.1 for normal shots, then correct Top Only / Bottom Only hybrids.
    from .nodes_v241 import _visible_body_and_presentation_v241
    components = profile.get("outfit_components") if isinstance(profile.get("outfit_components"), dict) else {}
    kind = str(components.get("kind", "complete"))
    if kind not in {"top_only", "bottom_only"}:
        return _visible_body_and_presentation_v241(profile, plan)

    visible = _visible_tags_v243(plan)
    upper_visible = bool(visible & (UPPER_TAGS | MID_TAGS | {"shoulders", "upper_back", "lower_back"}))
    lower_visible = bool(visible & LOWER_TAGS)
    groin_visible = bool(visible & {"groin", "pubic", "genital"}) and not _is_direct_back(plan)
    top = _clean_phrase(components.get("top", ""))
    bottom = _clean_phrase(components.get("bottom", ""))
    parts: list[str] = []
    if kind == "top_only":
        if upper_visible:
            parts.append(_upper_body_shape(profile))
        if lower_visible:
            parts.append(_clean_phrase(profile.get("clothed_lower_body", "")))
            if groin_visible:
                parts.append(_clean_phrase(profile.get("groin_anatomy_prompt", "")))
                parts.append(_clean_phrase(profile.get("pubic_hair_prompt", "")))
        presentation = _sentences(f"wearing {top} on the upper body" if top else "", "the lower body is uncovered")
    else:
        if upper_visible:
            parts.append(_upper_body_shape(profile))
            if not _is_rear_orientation(plan):
                parts.append(_clean_phrase(profile.get("chest_anatomy_prompt", "")))
        if lower_visible:
            parts.append(_clean_phrase(profile.get("clothed_lower_body", "")))
        presentation = _sentences("the upper torso is uncovered", f"wearing {bottom} on the lower body" if bottom else "")
    return _sentences(*parts), presentation, "hybrid"


class CharacterBlueprintCreatorV243(CharacterBlueprintCreatorV242):
    FUNCTION = "build_blueprint_v243"
    DESCRIPTION = (
        "Current Character Creator with visibility-aware anatomy, hybrid Top Only / Bottom Only presentation, tan routing, "
        "structured marks, explicit swimwear, and pubic-hair color matching."
    )

    @classmethod
    def INPUT_TYPES(cls):
        base = copy.deepcopy(super().INPUT_TYPES())
        base["required"]["structured_outfit_layout"] = (STRUCTURED_OUTFIT_TYPES_V243, {"default": "Top + Bottom Outfit"})
        base["required"]["tan_line_pattern"] = (TAN_LINE_PATTERNS_V243, {"default": "String Bikini — Minimal Triangle and Tight V"})
        base["required"]["bust_shape"] = (BUST_SHAPES_V243, {"default": "Unspecified"})
        return base

    def build_blueprint_v243(self, **kwargs):
        requested_layout = str(kwargs.get("structured_outfit_layout", "Top + Bottom Outfit"))
        call_kwargs = dict(kwargs)
        # Legacy workflows may still contain the removed Tank Top tan-line value.
        # Convert it to the closest supported clothing-line pattern rather than failing validation.
        if str(call_kwargs.get("tan_line_pattern", "")) == "Tank Top":
            call_kwargs["tan_line_pattern"] = "T-Shirt"
        if requested_layout in {TOP_ONLY_LAYOUT, BOTTOM_ONLY_LAYOUT}:
            call_kwargs["structured_outfit_layout"] = "Top + Bottom Outfit"
            if requested_layout == TOP_ONLY_LAYOUT:
                call_kwargs["structured_bottom"] = ""
            else:
                call_kwargs["structured_top"] = ""

        result = list(super().build_blueprint_v242(**call_kwargs))
        profile = copy.deepcopy(result[8])
        profile["schema"] = "CHARACTER_BLUEPRINT_V243"
        profile["schema_version"] = 14

        active_hybrid = (
            requested_layout in {TOP_ONLY_LAYOUT, BOTTOM_ONLY_LAYOUT}
            and str(kwargs.get("visible_presentation_mode")) == "Clothed — Use Outfit Controls"
            and str(kwargs.get("outfit_input_method")) == "Build Outfit — Separate Garment Fields"
        )
        if active_hybrid:
            top = _clean_phrase(kwargs.get("structured_top", ""))
            bottom = _clean_phrase(kwargs.get("structured_bottom", ""))
            footwear = _clean_phrase(kwargs.get("structured_footwear", ""))
            outerwear = _clean_phrase(kwargs.get("structured_outerwear", ""))
            warnings = [w for w in str(result[9] or "").split(" ") if w]
            if requested_layout == TOP_ONLY_LAYOUT:
                kind = "top_only"
                if not top:
                    top = "a fitted upper-body garment"
                    warnings.append("Top Only layout requires a Top description.")
                presentation = _sentences(f"wearing {top} as the only body garment", "the lower body is uncovered")
                active_body = _sentences(profile.get("clothed_upper_body", ""), profile.get("anatomy_lower_body", ""))
                structured_type = "Top Only"
            else:
                kind = "bottom_only"
                if not bottom:
                    bottom = "a fitted lower-body garment"
                    warnings.append("Bottom Only layout requires a Bottom description.")
                presentation = _sentences("the upper torso is uncovered", f"wearing {bottom} as the only body garment")
                active_body = _sentences(profile.get("anatomy_upper_body", ""), profile.get("clothed_lower_body", ""))
                structured_type = "Bottom Only"

            components = {
                "kind": kind,
                "top": top,
                "bottom": bottom,
                "footwear": footwear,
                "outerwear": outerwear,
                "one_piece": "",
                "swimwear_top": "",
                "swimwear_bottom": "",
                "notes": _clean_phrase(kwargs.get("outfit_notes", "")),
                "raw": "",
            }
            active_character = _sentences(
                profile.get("gender_authority_prompt", ""),
                profile.get("identity_detail_prompt", ""),
                active_body,
                presentation,
                profile.get("marks_prompt", ""),
                profile.get("tattoo_count_lock", ""),
                profile.get("piercing_count_lock", ""),
                profile.get("anatomy_integrity_lock", ""),
            )
            old_id = str(profile.get("character_id", "character"))
            base_id = old_id.rsplit("_", 1)[0] if "_" in old_id else old_id
            character_id = base_id + "_" + hashlib.sha1(active_character.encode("utf-8")).hexdigest()[:8]
            profile.update({
                "character_id": character_id,
                "structured_outfit_type": structured_type,
                "structured_outfit_type_label": requested_layout,
                "outfit_components": components,
                "structured_outfit_prompt": presentation,
                "default_clothing_prompt": presentation,
                "active_presentation_prompt": presentation,
                "active_body_prompt": active_body,
                "active_character_prompt": active_character,
                "clothed_character_prompt": active_character,
                "full_profile_prompt": active_character,
                "warnings": " ".join(warnings),
                "presentation_summary": str(profile.get("presentation_summary", "")) + f"\nOutfit garment layout: {requested_layout}",
            })
            result[5] = presentation
            result[6] = active_character
            result[7] = character_id
            result[9] = profile["warnings"]
            result[14] = presentation
            result[16] = presentation
            result[17] = active_body
            result[18] = active_character
            result[19] = active_character
            result[21] = profile["presentation_summary"]

        result[8] = profile
        result[15] = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        return tuple(result)


class CharacterShotControlV243(CharacterShotControlV242):
    FUNCTION = "build_shot_plan_v243"
    DESCRIPTION = (
        "Current Shot Control with region-centered camera targeting, strict left/right side-lying contact, automatic body-shot "
        "aspect selection, complete-head crop protection, social gestures, and expanded locations."
    )

    @classmethod
    def INPUT_TYPES(cls):
        base = copy.deepcopy(super().INPUT_TYPES())
        base["required"]["shot_type"] = (SHOT_TYPES_V243, {"default": "Head and Shoulders"})
        base["required"]["background"] = (BACKGROUNDS_V243, {"default": "Studio Solid Gray"})
        base["required"]["aspect_ratio"] = (ASPECT_RATIOS_V243, {"default": AUTO_ASPECT})
        return base

    def build_shot_plan_v243(self, **kwargs):
        requested_aspect = str(kwargs.get("aspect_ratio", AUTO_ASPECT))
        call_kwargs = dict(kwargs)
        if requested_aspect == AUTO_ASPECT:
            call_kwargs["aspect_ratio"] = "Portrait 4:5"
        result = list(super().build_shot_plan_v242(**call_kwargs))
        plan = copy.deepcopy(result[0])
        plan["schema"] = "FCC_SHOT_PLAN_V243"
        plan["schema_version"] = 12
        plan["aspect_ratio_requested"] = requested_aspect

        background = str(kwargs.get("background", "Studio Solid Gray"))
        if background == "Custom":
            background_prompt = _clean_phrase(kwargs.get("custom_background", ""))
        else:
            background_prompt = BACKGROUND_PROMPTS_V243.get(background, background.lower() + " background")
        lighting_prompt = ""
        old_environment = str(plan.get("environment_prompt", ""))
        # Preserve the inherited lighting and style by removing the inherited background prefix when possible.
        inherited_background = BACKGROUND_PROMPTS_V243.get(background, "")
        if inherited_background and old_environment.startswith(inherited_background):
            lighting_prompt = old_environment[len(inherited_background):].strip(" ,.;")
        else:
            # The super call may have used a fallback for a newly added background. Rebuild from the selected fields.
            from .nodes import LIGHTING_PROMPTS_V2
            lighting = str(kwargs.get("lighting", ""))
            if lighting == "Custom":
                light = _clean_phrase(kwargs.get("custom_lighting", ""))
            else:
                light = LIGHTING_PROMPTS_V2.get(lighting, lighting.lower())
            lighting_prompt = _sentences(light, str(kwargs.get("photo_style", "")).lower())
        plan["background"] = background
        plan["environment_prompt"] = _sentences(background_prompt, lighting_prompt)

        ignored_extra: list[str] = []
        if _is_regional(plan):
            plan["framing_prompt"] = _regional_crop_prompt_v243(plan)
            plan["camera_prompt"] = _regional_camera_prompt_v243(plan, kwargs.get("custom_camera", ""))
            plan["pose_prompt"] = ""
            if _regional_group(plan) not in {"face", "head_neck"}:
                plan["expression_prompt"] = ""
                ignored_extra.append("facial expression outside regional crop")
            ignored_extra.append("full-body pose outside regional crop")
        else:
            if str(plan.get("shot_type", "")) in {"Three-Quarter Body", "Full Body", WIDE_FULL_BODY}:
                plan["framing_prompt"] = _body_crop_prompt_v243(plan)
                # Add complete-crop distance protection without changing the user's chosen lens.
                plan["camera_prompt"] = _sentences(
                    str(plan.get("camera_prompt", "")).replace("facial proportions", "full-body proportions"),
                    "camera distance is widened enough to preserve the complete required crop and all stated frame margins",
                )

            if _is_rear_orientation(plan) and str(plan.get("shot_type", "")) in {"Three-Quarter Body", "Full Body", WIDE_FULL_BODY}:
                plan["expression_prompt"] = ""
                ignored_extra.append("facial expression in rear-oriented body view")

            if str(plan.get("pose", "")) in SIDE_LYING_POSES:
                plan["pose_prompt"] = _side_lying_pose_prompt_v243(str(plan.get("pose", "")))
                plan["camera_prompt"] = _sentences(
                    _side_lying_view_prompt_v243(plan),
                    _side_lying_height_prompt_v243(plan),
                    LENS_PROMPTS_V2.get(str(plan.get("lens", "")), "").replace("facial", "full-body"),
                    "camera distance is widened enough to include the complete requested horizontal crop",
                )
                if _is_direct_back(plan):
                    plan["expression_prompt"] = ""
                    ignored_extra.append("facial expression in rear side-lying view")

        aspect_label, width, height = _resolve_aspect_v243(plan, requested_aspect)
        plan["aspect_ratio"] = aspect_label
        plan["recommended_width"] = width
        plan["recommended_height"] = height

        plan["final_shot_prompt"] = _sentences(
            plan.get("framing_prompt", ""),
            plan.get("camera_prompt", ""),
            plan.get("pose_prompt", ""),
            plan.get("expression_prompt", ""),
            plan.get("scene_prompt", ""),
            plan.get("environment_prompt", ""),
            _clean_phrase(kwargs.get("shot_suffix", "")),
        )
        plan["active_settings_summary"] = _rebuild_shot_summary(plan, ignored_extra)

        result[0] = plan
        result[1] = plan["final_shot_prompt"]
        result[2] = plan.get("framing_prompt", "")
        result[3] = plan.get("camera_prompt", "")
        result[4] = plan.get("pose_prompt", "")
        result[5] = plan.get("expression_prompt", "")
        result[6] = plan.get("environment_prompt", "")
        result[7] = plan["active_settings_summary"]
        result[8] = json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True)
        result[9] = width
        result[10] = height
        return tuple(result)


class CharacterPromptAssemblerV243(CharacterPromptAssemblerV242):
    FUNCTION = "assemble_prompt_v243"
    DESCRIPTION = (
        "Region-first visibility compiler with exact garment coverage, concise Krea-safe tan pigmentation, local identity routing, "
        "strict rear/side views, and hybrid Top Only / Bottom Only presentation."
    )

    def assemble_prompt_v243(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan = shot_plan if isinstance(shot_plan, dict) else {}
        krea = generation_purpose.startswith("Krea")
        qwen = generation_purpose.startswith("Qwen")
        extreme = _is_extreme_closeup_v231(plan)
        regional = _is_regional(plan)

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

        tan = _tan_prompt_for_plan_v243(profile, plan)
        marks, visible_tattoos, visible_piercings = _visible_marks_v243(profile, plan)

        if extreme:
            macro = _macro_sections_v241(profile, plan)
            focus = _focus_value_v231(plan)
            shot_section = _sentences(macro["crop"], macro["camera"], macro["eye_state"], macro["environment"], macro["exclusion"])
            character_section = _sentences(_focus_identity_prompt_v231(profile, focus), tan)
            body_section = ""
            presentation = ""
            appearance_section = marks
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
            routing_mode = "extreme_closeup_visibility_compiled_v243"
            scene = ""
        else:
            crop = _regional_crop_prompt_v243(plan) if regional else _crop_prompt_v230(plan)
            custom_direction = _clean_phrase(plan.get("framing_prompt", "")) if plan.get("planner_mode") == "Custom Shot Direction — Keep Character Settings" else ""
            shot_section = _sentences(
                custom_direction or _clean_phrase(plan.get("framing_prompt", "")) or crop,
                "" if custom_direction else _clean_phrase(plan.get("camera_prompt", "")),
                "" if custom_direction or regional else _clean_phrase(plan.get("pose_prompt", "")),
                _clean_phrase(plan.get("expression_prompt", "")),
                _clean_phrase(plan.get("scene_prompt", "")),
                _clean_phrase(plan.get("environment_prompt", "")),
            )
            character_section = _sentences(_region_identity_v243(profile, plan) if regional else _identity_for_view(profile, plan), tan)
            body_section, presentation, _ = _visible_body_and_presentation_v243(profile, plan)
            appearance_section = marks
            scene = _clean_phrase(plan.get("scene_prompt", ""))
            if qwen:
                instruction = _sentences(
                    purpose,
                    "replace the original framing, camera, pose, and scene with the active Shot Control result",
                    "apply only the visible Character Creator traits appropriate to this crop, camera direction, and clothing coverage",
                    "secondary people are not copies of the primary character unless Scene Direction explicitly requests that",
                )
                final_prompt = _sentences(custom_prefix, instruction, shot_section, character_section, body_section, presentation, appearance_section, custom_suffix)
            else:
                final_prompt = _sentences(trigger_word, custom_prefix, purpose, shot_section, character_section, body_section, presentation, appearance_section, custom_suffix)
            routing_mode = "regional_visibility_compiled_v243" if regional else "standard_visibility_compiled_v243"

        width = int(plan.get("recommended_width", 1024))
        height = int(plan.get("recommended_height", 1280))
        character_id = profile.get("character_id", "character")
        focus = plan.get("focus_region", "")
        shot_id = _slug(_sentences(character_id, generation_purpose, plan.get("shot_type", ""), _camera_view(plan), focus, plan.get("pose", "")))
        presentation_mode = profile.get("presentation_mode", "Unspecified")
        advisory = (
            f"Visibility compiler included {len(visible_tattoos)} tattoo record(s) and {len(visible_piercings)} piercing record(s). "
            "Off-frame, orientation-incompatible, and garment-covered anatomy and marks were omitted."
        )
        notes = "\n".join([
            f"Purpose: {generation_purpose}",
            f"Reference: {reference}",
            "Visibility Compiler V2.4.3: ACTIVE",
            "Regional documentation uses local identity, local body, local garment, and local mark subsets only.",
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
            f"{width} × {height} from {plan.get('aspect_ratio', 'selected aspect ratio')}",
            json.dumps(sections, indent=2, ensure_ascii=False),
            character_section,
            scene,
        )


class QwenDatasetQueueV243(QwenDatasetQueueV242):
    DESCRIPTION = "Current FCC Qwen dataset queue using the v2.4.3 character blueprint and visibility rules."
