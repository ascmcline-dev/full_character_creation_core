from __future__ import annotations

import copy
import json
import re
from typing import Any

from .nodes import (
    FCCDatasetDirector,
    FCCQueueItemRouter,
    PRESET_OUTFITS,
    _dataset_specs,
    _slug,
)
from .nodes_v230 import (
    CAMERA_HEIGHT_PROMPTS_V2,
    CAMERA_PROMPTS,
    LENS_PROMPTS_V2,
    POSES_V2,
    POSE_PROMPTS_V2,
    CharacterPromptAssemblerV230,
    _clean_phrase,
    _crop_prompt_v230,
    _extreme_macro_sections_v231,
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
    CharacterBlueprintCreatorV240,
    CharacterPromptAssemblerV240,
    CharacterShotControlV240,
    QwenDatasetQueueV240,
    _article,
    _group_piercing_records,
    _location_from_text,
    _parse_piercing_record,
    _pubic_prompt_with_color,
    _tattoo_phrase,
    _upper_body_shape,
)

# -----------------------------------------------------------------------------
# V2.4.1 / Studio V2.8.1
# - strict rear-view orientation and prone routing
# - body-shot camera targeting that avoids accidental overhead portraits
# - pose suppression in regional documentation crops
# - explicit swimwear coverage and micro-string-bikini preset wording
# - combined tan profile control with crop-specific pattern language
# - structured single-tattoo locations and orientation-aware mark visibility
# - positive-boundary nose/septum macro wording to avoid gray cutout regions
# -----------------------------------------------------------------------------

PRESET_OUTFITS["Opaque Fitted Tank Top"] = {
    "kind": "complete",
    "top": "solid opaque non-sheer fitted tank top with a normal neckline and complete chest coverage",
    "bottom": "high-waisted fitted jeans",
    "footwear": "casual low-profile shoes",
}
PRESET_OUTFITS["Swimwear"] = {
    "kind": "swimwear",
    "swimwear_top": "micro string bikini top with small triangle cups and thin halter and back ties",
    "swimwear_bottom": "matching low-coverage high-cut V-front tie-side string bikini bottoms",
}

TAN_PROFILES_V241 = [
    "None",
    "Light Tan — Even",
    "Light Tan — With Tan Lines",
    "Medium Tan — Even",
    "Medium Tan — With Tan Lines",
    "Dark Tan — Even",
    "Dark Tan — With Tan Lines",
    "Custom",
]

TAN_LINE_PATTERNS_V241 = [
    "String Bikini — Minimal Triangle and Tight V",
    "Standard Bikini Top and Bottom",
    "One-Piece Swimsuit",
    "Bra and Brief",
    "Tank Top",
    "T-Shirt",
    "Shorts",
    "Socks / Footwear",
    "Mixed Clothing Tan Lines",
    "Custom",
]

TAN_PATTERN_REGIONS_V241 = {
    "String Bikini — Minimal Triangle and Tight V": {"chest", "upper_back", "hips", "groin", "buttocks", "upper_thighs"},
    "Standard Bikini Top and Bottom": {"chest", "upper_back", "hips", "groin", "buttocks", "upper_thighs"},
    "One-Piece Swimsuit": {"shoulders", "chest", "upper_back", "lower_back", "abdomen", "hips", "groin", "buttocks"},
    "Bra and Brief": {"chest", "upper_back", "hips", "groin", "buttocks"},
    "Tank Top": {"shoulders", "upper_chest", "upper_back", "upper_arms"},
    "T-Shirt": {"neck", "upper_arms", "forearms"},
    "Shorts": {"upper_thighs", "thighs", "legs"},
    "Socks / Footwear": {"ankles", "feet"},
    "Mixed Clothing Tan Lines": {"chest", "upper_back", "lower_back", "abdomen", "hips", "groin", "buttocks", "thighs", "legs", "ankles", "feet"},
    "Custom": {"custom"},
}

TATTOO_INPUT_MODES_V241 = ["Descriptor List", "Structured Single Tattoo"]
TATTOO_LOCATIONS_V241 = [
    "Unspecified",
    "Full Back",
    "Upper Back",
    "Lower Back / Tramp Stamp",
    "Full Abdomen",
    "Cleavage / Center Chest",
    "Upper Left Chest",
    "Upper Right Chest",
    "Left Upper Arm",
    "Right Upper Arm",
    "Left Forearm",
    "Right Forearm",
    "Full Left Arm Sleeve",
    "Full Right Arm Sleeve",
    "Full Left Leg Sleeve",
    "Full Right Leg Sleeve",
    "Left Hand",
    "Right Hand",
    "Left Hip",
    "Right Hip",
    "Pubic Mons",
    "Left Buttock",
    "Right Buttock",
    "Left Thigh",
    "Right Thigh",
    "Left Calf",
    "Right Calf",
    "Left Foot",
    "Right Foot",
    "Custom / Describe in Tattoo Description",
]

POSES_V241 = list(POSES_V2)[:-1] + [
    "Lying Prone / On Stomach",
    "Middle Finger Gesture",
    "Index Finger Lightly Between Lips",
    "Licking a Popsicle",
    "Blowing a Kiss",
    "Finger Heart Near Face",
    "Hand Under Chin",
    "Both Hands Framing Face",
    "Custom",
]

POSE_PROMPTS_V241 = dict(POSE_PROMPTS_V2)
POSE_PROMPTS_V241.update({
    "Lying Prone / On Stomach": "lying flat face-down on the stomach with the torso, pelvis, and legs naturally aligned",
    "Middle Finger Gesture": "one hand raised clearly toward the camera with the middle finger extended and the remaining fingers naturally folded, the other arm relaxed",
    "Index Finger Lightly Between Lips": "one index fingertip resting lightly between the lips in a playful social-media gesture, with the hand and mouth clearly visible",
    "Licking a Popsicle": "holding one popsicle near the mouth while the tongue lightly touches the popsicle, with the hand, object, and face clearly visible",
    "Blowing a Kiss": "one hand raised near the lips while blowing a kiss toward the camera",
    "Finger Heart Near Face": "one hand beside the cheek forming a small finger-heart gesture with the thumb and index finger",
    "Hand Under Chin": "one hand placed lightly beneath the chin in a casual beauty-pose gesture",
    "Both Hands Framing Face": "both open hands placed near the cheeks to frame the face in a playful social-media pose",
})

# Ensure the inherited planner recognizes the additional pose names before the
# context-sensitive V2.4.1 pass refines them.
POSE_PROMPTS_V2.update(POSE_PROMPTS_V241)

V241_LOCATION_RULES: list[tuple[tuple[str, ...], str, set[str]]] = [
    (("full back", "entire back", "whole back"), "Full Back", {"upper_back", "lower_back", "shoulders"}),
    (("full left arm sleeve", "left full arm sleeve", "left arm sleeve"), "Full Left Arm Sleeve", {"arms", "upper_arms", "forearms", "left_upper_arm", "left_forearm"}),
    (("full right arm sleeve", "right full arm sleeve", "right arm sleeve"), "Full Right Arm Sleeve", {"arms", "upper_arms", "forearms", "right_upper_arm", "right_forearm"}),
    (("full left leg sleeve", "left full leg sleeve", "left leg sleeve"), "Full Left Leg Sleeve", {"legs", "thighs", "knees", "shins", "calves", "left_thigh", "left_knee", "left_leg", "left_calf"}),
    (("full right leg sleeve", "right full leg sleeve", "right leg sleeve"), "Full Right Leg Sleeve", {"legs", "thighs", "knees", "shins", "calves", "right_thigh", "right_knee", "right_leg", "right_calf"}),
    (("full abdominal", "full abdomen", "entire abdomen", "whole abdomen"), "Full Abdomen", {"abdomen", "waist"}),
    (("cleavage", "between both breasts", "between the breasts", "center chest", "sternum"), "Cleavage / Center Chest", {"chest", "upper_chest", "cleavage", "sternum"}),
    (("tramp stamp", "lower back"), "Lower Back / Tramp Stamp", {"lower_back", "waist"}),
    (("left calf",), "Left Calf", {"legs", "left_calf"}),
    (("right calf",), "Right Calf", {"legs", "right_calf"}),
]


def _mapping_insert_after(mapping: dict, after_key: str, additions: list[tuple[str, Any]]) -> dict:
    out: dict = {}
    for key, value in mapping.items():
        out[key] = value
        if key == after_key:
            for name, spec in additions:
                out[name] = spec
    return out


def _tan_profile_parts(value: str) -> tuple[str, str]:
    value = str(value or "None")
    if value == "None":
        return "None", "Even Tan — No Defined Lines"
    if value == "Custom":
        return "Custom", "Custom"
    level = value.split(" — ", 1)[0]
    state = "Defined Tan Lines" if "With Tan Lines" in value else "Even Tan — No Defined Lines"
    return level, state


def _location_from_text_v241(text: str) -> tuple[str, set[str]]:
    value = str(text or "").lower()
    for tokens, label, tags in V241_LOCATION_RULES:
        if any(token in value for token in tokens):
            return label, set(tags)
    return _location_from_text(text)


def _structured_tattoo_text(location: str, description: str) -> str:
    location = _clean_phrase(location)
    description = _clean_phrase(description)
    if location in {"", "Unspecified", "Custom / Describe in Tattoo Description"}:
        return description
    if not description:
        return f"{location} tattoo"
    return f"{location}: {description}"


def _parse_tattoo_record_v241(entry: str) -> dict[str, Any]:
    raw = _clean_phrase(entry)
    location, tags = _location_from_text_v241(raw)
    return {
        "kind": "tattoo",
        "raw": raw,
        "location": location,
        "region_tags": sorted(tags),
        "quantity": 1,
    }


def _tattoo_phrase_v241(record: dict[str, Any]) -> str:
    raw = _clean_phrase(record.get("raw", ""))
    return raw[:1].lower() + raw[1:] if raw else ""


def _camera_view(plan: dict) -> str:
    return str(plan.get("camera_view", "") or "")


def _is_direct_back(plan: dict) -> bool:
    return _camera_view(plan) == "Back View"


def _is_rear_three_quarter(plan: dict) -> bool:
    return _camera_view(plan) in {"Rear Three-Quarter Left", "Rear Three-Quarter Right"}


def _is_rear_orientation(plan: dict) -> bool:
    return _is_direct_back(plan) or _is_rear_three_quarter(plan)


def _shot_is_face_scale(plan: dict) -> bool:
    shot = str(plan.get("shot_type", "")).lower()
    return any(x in shot for x in ("face close", "head and shoulders", "chest-up", "extreme close-up"))


def _shot_is_body_scale(plan: dict) -> bool:
    shot = str(plan.get("shot_type", "")).lower()
    return any(x in shot for x in ("waist-up", "midshot", "three-quarter", "full body"))


def _strict_view_prompt(plan: dict) -> str:
    view = _camera_view(plan)
    pose = str(plan.get("pose", ""))
    shot = str(plan.get("shot_type", ""))
    if view == "Back View":
        if pose == "Lying Prone / On Stomach":
            return _sentences(
                "dorsal rear view of the primary character lying face-down on the stomach",
                "the back of the head, shoulders, spine, waist, hips, and backs of the legs are presented to the camera",
                "the torso and pelvis remain aligned without a twisting pose",
                "camera moderately elevated above and behind the subject to document the back surface",
            )
        if pose == "Walking":
            return _sentences(
                "strict direct rear view from behind",
                "the primary character is walking away from the camera",
                "the back of the head, shoulders, back, waist, hips, and backs of the legs face the lens",
                "the head, shoulders, torso, and pelvis remain aligned in the walking direction",
            )
        if pose == "Over-the-Shoulder Blogger Pose":
            return "rear three-quarter blogger view with the torso facing away and only a controlled partial face turn toward the camera"
        return _sentences(
            "strict direct rear view from behind",
            "the back of the head, shoulders, spine, waist, hips, and backs of the legs face the camera",
            "the head and torso remain aligned facing away from the lens",
        )
    if view == "Front View" and _shot_is_body_scale(plan):
        return _sentences(
            "strict straight-on front view",
            "the face, shoulders, torso, pelvis, and knees are aligned toward the camera",
            "the lens axis remains level and perpendicular to the front of the body",
        )
    if view == "Rear Three-Quarter Left":
        return "rear three-quarter-left view with most of the back visible and the torso turned only slightly left"
    if view == "Rear Three-Quarter Right":
        return "rear three-quarter-right view with most of the back visible and the torso turned only slightly right"
    return CAMERA_PROMPTS.get(view, view.lower())


def _height_prompt_for_plan(plan: dict) -> str:
    height = str(plan.get("camera_height", ""))
    if _is_direct_back(plan) and plan.get("pose") == "Lying Prone / On Stomach":
        return "moderately elevated camera angle directed toward the subject's back"
    if _shot_is_body_scale(plan):
        if height == "Eye Level":
            return "camera placed at upper-torso height with a level horizon and sufficient distance for the complete selected body crop"
        if height == "Slightly Below Eye Level":
            return "camera placed slightly below upper-torso height with only a mild upward angle and a level body composition"
        if height == "Slightly Above Eye Level":
            return "camera placed slightly above upper-torso height with only a mild downward angle and a level body composition"
    return CAMERA_HEIGHT_PROMPTS_V2.get(height, "")


def _regional_pose_should_be_suppressed(plan: dict) -> bool:
    return str(plan.get("focus_mode", "")) == "Regional Close-Up" or str(plan.get("shot_type", "")) == "Close-Up — Regional Documentation"


def _rebuild_shot_summary(plan: dict, ignored_extra: list[str] | None = None) -> str:
    ignored = list(plan.get("ignored_controls", []) or [])
    for item in ignored_extra or []:
        if item not in ignored:
            ignored.append(item)
    plan["ignored_controls"] = ignored
    return "\n".join([
        "FCC UNIVERSAL SHOT CONTROL — ACTIVE PATH",
        f"Mode: {plan.get('planner_mode', '')}",
        f"Scene cast: {plan.get('scene_cast', '')}",
        f"Scene direction: {plan.get('scene_direction') or '[blank]'}",
        f"Shot type: {plan.get('shot_type', '')}",
        f"Framing: {plan.get('framing_prompt', '')}",
        f"Camera: {plan.get('camera_prompt', '')}",
        f"Pose: {plan.get('pose_prompt') or '[inactive for this crop]'}",
        f"Expression: {plan.get('expression_prompt') or '[inactive for this view/crop]'}",
        f"Focus: {plan.get('focus_region') or '[inactive]'}",
        f"Environment: {plan.get('environment_prompt', '')}",
        f"Aspect: {plan.get('aspect_ratio', '')} ({plan.get('recommended_width', 1024)} × {plan.get('recommended_height', 1280)})",
        f"Ignored controls: {', '.join(ignored) if ignored else 'None'}",
        f"Warnings: {plan.get('warnings') or 'None'}",
    ])


def _identity_for_view(profile: dict, plan: dict) -> str:
    if _is_direct_back(plan) or (_is_rear_three_quarter(plan) and plan.get("pose") != "Over-the-Shoulder Blogger Pose"):
        primary_gender = str(profile.get("primary_character_gender", ""))
        gender = {
            "Adult Woman": "the primary character is an adult woman with a clearly feminine overall body presentation",
            "Adult Man": "the primary character is an adult man with a clearly masculine overall body presentation",
            "Adult Nonbinary": "the primary character is an adult nonbinary person with the selected overall body presentation",
        }.get(primary_gender, "the primary adult character is viewed from behind")
        age = f"age range {profile.get('age_range')}" if profile.get("age_range") else ""
        heritage = f"{str(profile.get('heritage_prompt', '')).strip()}" if profile.get("heritage_prompt") else ""
        skin = str(profile.get("skin_tone", "") or "").strip()
        complexion = str(profile.get("complexion", "") or "").strip()
        hair = _clean_phrase(profile.get("hair_prompt", ""))
        return _sentences(
            gender,
            age,
            heritage,
            f"{skin.lower()} skin tone" if skin and skin not in {"Unspecified", "Custom / Unspecified"} else "",
            complexion.lower() if complexion and complexion not in {"Unspecified", "Custom / Unspecified"} else "",
            hair,
            "the back of the head and hairstyle are visible from behind",
        )
    return _sentences(_clean_phrase(profile.get("gender_authority_prompt", "")), _clean_phrase(profile.get("identity_detail_prompt", "")))


def _visible_tags_v241(plan: dict) -> set[str]:
    # Start with a crop-derived set similar to V2.4, then apply camera orientation.
    if _is_extreme_closeup_v231(plan):
        from .nodes_v240 import _focus_tags
        tags = _focus_tags(_focus_value_v231(plan))
    else:
        shot = str(plan.get("shot_type", "")).lower()
        focus = str(plan.get("focus_region", "")).lower()
        if "regional" in shot:
            from .nodes_v240 import _focus_tags
            tags = _focus_tags(focus)
            if tags == {"unknown"}:
                if "face" in focus or "head" in focus:
                    tags = set(FACE_TAGS)
                elif "chest" in focus or "ribcage" in focus:
                    tags = set(UPPER_TAGS) | {"neck"}
                elif "abdomen" in focus or "waist" in focus:
                    tags = set(MID_TAGS) | {"chest"}
                elif any(x in focus for x in ("groin", "pelvis", "hip", "butt", "thigh", "feet", "foot")):
                    tags = set(LOWER_TAGS) | set(MID_TAGS)
                elif "arm" in focus:
                    tags = {"arms", "upper_arms", "forearms", "hands"}
        elif "face close" in shot:
            tags = set(FACE_TAGS) | {"shoulders"}
        elif "head and shoulders" in shot:
            tags = set(FACE_TAGS) | {"shoulders", "upper_chest"}
        elif "chest-up" in shot or "chest up" in shot:
            tags = set(FACE_TAGS) | set(UPPER_TAGS) | {"neck"}
        elif "waist-up" in shot or "midshot" in shot:
            tags = set(FACE_TAGS) | set(UPPER_TAGS) | set(MID_TAGS) | {"neck"}
        elif "three-quarter" in shot:
            tags = set(FACE_TAGS) | set(UPPER_TAGS) | set(MID_TAGS) | {"hips", "thighs", "knees", "neck"}
        elif "full body" in shot:
            tags = set(FACE_TAGS) | set(UPPER_TAGS) | set(MID_TAGS) | set(LOWER_TAGS) | {"neck"}
        else:
            tags = set(FACE_TAGS) | set(UPPER_TAGS) | set(MID_TAGS) | set(LOWER_TAGS)

    if _is_direct_back(plan):
        front_only = set(FACE_TAGS) | {"upper_chest", "chest", "breast", "nipple", "areola", "abdomen", "navel", "groin", "pubic", "genital", "cleavage", "sternum"}
        tags -= front_only
        shot = str(plan.get("shot_type", "")).lower()
        tags |= {"upper_back", "shoulders"}
        if any(x in shot for x in ("waist", "midshot", "three-quarter", "full body")):
            tags |= {"lower_back", "waist", "arms", "forearms"}
        if any(x in shot for x in ("three-quarter", "full body")):
            tags |= {"buttocks", "hips", "thighs", "legs", "knees"}
    elif _camera_view(plan) == "Front View":
        tags -= {"upper_back", "lower_back", "buttocks"}
    return tags


def _coverage_tags_v241(profile: dict) -> set[str]:
    if profile.get("presentation_mode") != "Clothed Character":
        return set()
    components = profile.get("outfit_components") if isinstance(profile.get("outfit_components"), dict) else {}
    kind = str(components.get("kind", "complete"))
    covered: set[str] = set()
    if kind == "swimwear":
        return {"breast", "nipple", "areola", "groin", "pubic", "genital"}
    if kind == "one_piece":
        return {"chest", "breast", "nipple", "areola", "abdomen", "waist", "groin", "pubic", "genital", "upper_back", "lower_back"}
    if kind == "lingerie":
        return {"breast", "nipple", "areola", "groin", "pubic", "genital"}
    top = " ".join(str(components.get(k, "")) for k in ("top", "outerwear", "raw")).lower()
    bottom = " ".join(str(components.get(k, "")) for k in ("bottom", "raw")).lower()
    footwear = str(components.get("footwear", "")).lower()
    if top:
        covered |= {"chest", "breast", "nipple", "areola", "abdomen", "upper_back", "lower_back"}
        if any(x in top for x in ("long sleeve", "long-sleeve", "jacket", "hoodie", "sweater", "coat")):
            covered |= {"upper_arms", "forearms", "arms"}
        elif any(x in top for x in ("t-shirt", "tee", "short sleeve", "short-sleeve")):
            covered |= {"upper_arms"}
    if bottom:
        covered |= {"hips", "groin", "pubic", "genital", "buttocks", "upper_thighs"}
        if any(x in bottom for x in ("jeans", "pants", "trousers", "leggings")):
            covered |= {"thighs", "legs", "knees"}
    if footwear:
        covered |= {"feet"}
    return covered


def _record_visible_v241(record: dict[str, Any], visible: set[str], covered: set[str], plan: dict | None = None) -> bool:
    location = str(record.get("location", ""))
    if plan is not None:
        rear_only = {"Full Back", "Upper Back", "Lower Back", "Lower Back / Tramp Stamp", "Buttocks", "Left Buttock", "Right Buttock"}
        front_only = {"Full Abdomen", "Abdomen", "Navel", "Cleavage / Center Chest", "Upper Left Chest", "Upper Right Chest", "Chest", "Pubic Mons", "Groin"}
        if location in rear_only and not _is_rear_orientation(plan):
            return False
        if location in front_only and _is_direct_back(plan):
            return False
    tags = set(record.get("region_tags", []))
    if "unknown" in tags:
        return len(visible & (UPPER_TAGS | MID_TAGS | LOWER_TAGS)) > 8
    overlap = tags & visible
    if not overlap:
        return False
    return bool(overlap - covered)


def _record_matches_extreme_v241(record: dict[str, Any], focus: str) -> bool:
    f = str(focus or "").lower()
    location = str(record.get("location", ""))
    tags = set(record.get("region_tags", []))
    if "complete face" in f or "facial profile" in f:
        return bool(tags & FACE_TAGS)
    if "left eye" in f:
        return location == "Left Eyebrow"
    if "right eye" in f:
        return location == "Right Eyebrow"
    if "both eyes" in f:
        return location in {"Left Eyebrow", "Right Eyebrow", "Bridge"}
    if "nose" in f or "septum" in f:
        return location in {"Left Nostril", "Right Nostril", "Septum", "Bridge"}
    if "mouth" in f or "lip" in f:
        return location in {"Left Lip", "Right Lip", "Center Lip"}
    if "forehead" in f or "hairline" in f:
        return location in {"Left Eyebrow", "Right Eyebrow"} or bool(tags & {"forehead", "hairline"})
    from .nodes_v240 import _focus_tags
    return bool(tags & _focus_tags(focus))


def _piercing_phrase_v241(record: dict[str, Any]) -> str:
    quantity = int(record.get("quantity", 1))
    location = str(record.get("location", "Unspecified"))
    material = str(record.get("material", "")).lower()
    jewelry = str(record.get("jewelry_type", "")).lower()
    custom = str(record.get("custom_detail", "")).strip()
    item = " ".join(x for x in (material, jewelry) if x).strip() or "piercing jewelry"
    if location == "Septum":
        if quantity == 1:
            return f"one {item} through the central nasal septum"
        return f"{quantity} closely arranged {item}s through the central nasal septum"
    anatomical = f"the primary character's anatomical {location.lower()}"
    if quantity == 1:
        phrase = f"one {item} on {anatomical}"
    elif quantity == 2:
        phrase = f"two small closely spaced {item}s on {anatomical}"
    else:
        phrase = f"{quantity} closely grouped {item}s on {anatomical}"
    if custom and custom.lower() not in phrase.lower():
        phrase += f", {custom}"
    return phrase


def _visible_marks_v241(profile: dict, plan: dict) -> tuple[str, list[dict], list[dict]]:
    visible = _visible_tags_v241(plan)
    covered = _coverage_tags_v241(profile)
    extreme = _is_extreme_closeup_v231(plan)
    focus = _focus_value_v231(plan) if extreme else ""
    tattoos = [r for r in profile.get("tattoo_records", []) if _record_visible_v241(r, visible, covered, plan) and (not extreme or _record_matches_extreme_v241(r, focus))]
    piercings = [r for r in profile.get("piercing_records", []) if _record_visible_v241(r, visible, covered, plan) and (not extreme or _record_matches_extreme_v241(r, focus))]
    tattoo_phrases = [_tattoo_phrase_v241(r) for r in tattoos if _tattoo_phrase_v241(r)]
    piercing_phrases = [_piercing_phrase_v241(r) for r in piercings if _piercing_phrase_v241(r)]
    return _sentences(
        "visible permanent skin marking: " + "; ".join(tattoo_phrases) if tattoo_phrases else "",
        "visible permanent jewelry: " + "; ".join(piercing_phrases) if piercing_phrases else "",
    ), tattoos, piercings


def _tan_strength_words(strength: str) -> str:
    return {
        "Subtle": "faint low-contrast softly blended",
        "Moderate": "clearly visible naturally blended",
        "Distinct": "sharp high-contrast",
    }.get(strength, "clearly visible naturally blended")


def _tan_base_v241(profile: dict) -> str:
    level = str(profile.get("tan_level", "None"))
    state = str(profile.get("tan_line_state", "Even Tan — No Defined Lines"))
    if level == "None":
        return ""
    if level == "Custom":
        return _clean_phrase(profile.get("custom_tan_description", ""))
    if state == "Even Tan — No Defined Lines":
        return f"uniform {level.lower()} with even consistent coloration across all visible skin"
    return f"{level.lower()} across the visible skin"


def _tan_pattern_phrase_v241(pattern: str, visible: set[str], strength: str, rear: bool) -> str:
    words = _tan_strength_words(strength)
    chest = bool(visible & {"chest", "upper_chest", "breast", "upper_back", "shoulders"})
    lower = bool(visible & {"hips", "groin", "buttocks", "upper_thighs", "lower_back"})
    abdomen = bool(visible & {"abdomen", "waist"})
    parts: list[str] = []
    if pattern == "String Bikini — Minimal Triangle and Tight V":
        if chest:
            if rear:
                parts.append(f"{words} narrow lighter string-bikini strap and small triangle-top back-coverage lines across the visible upper back")
            else:
                parts.append(f"{words} small triangular lighter string-bikini coverage centered over the breast and nipple areas with thin strap lines")
        if lower:
            if rear:
                parts.append(f"{words} narrow V-shaped lighter string-bikini-bottom coverage across the high hips and upper buttock area with thin side-tie lines")
            else:
                parts.append(f"{words} tight V-shaped lighter string-bikini-bottom coverage around the groin and high hips with thin side-tie lines")
    elif pattern == "Standard Bikini Top and Bottom":
        if chest:
            parts.append(f"{words} lighter standard bikini-top coverage and strap boundaries across the visible {'upper back' if rear else 'chest'}")
        if lower:
            if rear:
                parts.append(f"{words} lighter standard bikini-bottom coverage across the visible hips and upper buttock area")
            else:
                parts.append(f"{words} lighter standard bikini-bottom coverage across the visible hips and groin area")
    elif pattern == "One-Piece Swimsuit":
        if chest or abdomen or lower:
            region = "rear torso and hips" if rear else "chest, abdomen, hips, and groin"
            parts.append(f"{words} lighter one-piece-swimsuit coverage boundaries across the visible {region}")
    elif pattern == "Bra and Brief":
        if chest:
            parts.append(f"{words} lighter bra coverage and strap boundaries across the visible {'upper back' if rear else 'chest'}")
        if lower:
            parts.append(f"{words} lighter brief coverage around the visible hips, groin, and buttock area")
    elif pattern == "Tank Top":
        parts.append(f"{words} lighter tank-top neckline, shoulder, and armhole boundaries across the visible upper body")
    elif pattern == "T-Shirt":
        parts.append(f"{words} lighter T-shirt neckline and sleeve boundaries across the visible neck and arms")
    elif pattern == "Shorts":
        parts.append(f"{words} lighter shorts hem boundaries across the visible thighs")
    elif pattern == "Socks / Footwear":
        parts.append(f"{words} lighter sock or footwear boundaries across the visible ankles and feet")
    elif pattern == "Mixed Clothing Tan Lines":
        parts.append(f"{words} natural mixed clothing-coverage boundaries limited to the visible body regions")
    return _sentences(*parts)


def _tan_prompt_for_plan_v241(profile: dict, plan: dict) -> str:
    base = _tan_base_v241(profile)
    if not base:
        return ""
    state = profile.get("tan_line_state", "Even Tan — No Defined Lines")
    if state == "Even Tan — No Defined Lines":
        return base
    if state == "Custom":
        return _sentences(base, _clean_phrase(profile.get("custom_tan_description", "")))
    visible = _visible_tags_v241(plan)
    pattern = str(profile.get("tan_line_pattern", "String Bikini — Minimal Triangle and Tight V"))
    regions = set(profile.get("tan_line_regions", [])) or TAN_PATTERN_REGIONS_V241.get(pattern, set())
    if "custom" not in regions and not (visible & regions):
        return base
    phrase = _tan_pattern_phrase_v241(pattern, visible, str(profile.get("tan_line_visibility", "Moderate")), _is_rear_orientation(plan))
    return _sentences(base, phrase)


def _visible_body_and_presentation_v241(profile: dict, plan: dict) -> tuple[str, str, str]:
    visible = _visible_tags_v241(plan)
    presentation_mode = profile.get("presentation_mode", "Clothed Character")
    clinical = presentation_mode == "Clinical Anatomy"
    face_only = visible.issubset(FACE_TAGS | {"shoulders", "upper_chest", "neck"})
    upper_visible = bool(visible & (UPPER_TAGS | MID_TAGS | {"upper_back", "lower_back", "shoulders"}))
    lower_visible = bool(visible & LOWER_TAGS)
    groin_visible = bool(visible & {"groin", "pubic", "genital"})
    rear = _is_rear_orientation(plan)
    body_parts: list[str] = []

    if not face_only:
        if clinical:
            if upper_visible:
                if rear:
                    body_parts.append(_sentences(_upper_body_shape(profile), "the back, shoulders, spine, and waist retain the selected body build"))
                else:
                    body_parts.append(_clean_phrase(profile.get("anatomy_upper_body", "")))
            if lower_visible:
                lower = _clean_phrase(profile.get("anatomy_lower_body", ""))
                pubic = _clean_phrase(profile.get("pubic_hair_prompt", "")) if groin_visible and not rear else ""
                groin = _clean_phrase(profile.get("groin_anatomy_prompt", "")) if groin_visible and not rear else ""
                if groin and groin in lower:
                    lower = lower.replace(groin, "").strip(" ,.;")
                if pubic and pubic in lower:
                    lower = lower.replace(pubic, "").strip(" ,.;")
                body_parts.extend([lower, groin, pubic])
        else:
            if upper_visible:
                body_parts.append(_upper_body_shape(profile))
                if not rear and profile.get("resolved_chest_anatomy") == "Bust Anatomy — Use Bust Controls":
                    size = str(profile.get("bust_size", "Unspecified"))
                    if size != "Unspecified":
                        body_parts.append(f"the selected {size.lower()} bust size subtly shapes the fitted upper garment while the garment keeps normal coverage")
            if lower_visible:
                body_parts.append(_clean_phrase(profile.get("clothed_lower_body", "")))

    if presentation_mode == "Clothed Character":
        components = profile.get("outfit_components") if isinstance(profile.get("outfit_components"), dict) else {}
        kind = str(components.get("kind", "complete"))
        top = _clean_phrase(components.get("top") or components.get("one_piece") or components.get("swimwear_top") or components.get("raw") or "")
        bottom = _clean_phrase(components.get("bottom") or components.get("one_piece") or components.get("swimwear_bottom") or components.get("raw") or "")
        footwear = _clean_phrase(components.get("footwear", ""))
        if kind == "swimwear":
            if rear:
                rear_top = top or "a secure string-bikini top with visible back straps and ties"
                rear_bottom = bottom or "matching tie-side string-bikini bottoms with narrow rear coverage"
                rear_bottom = rear_bottom.replace("V-front", "narrow rear").replace("v-front", "narrow rear")
                presentation = _sentences(
                    f"wearing {rear_top}",
                    f"with {rear_bottom}",
                    "both swimwear pieces are clearly present from behind with visible fabric, straps, ties, seams, and normal secure coverage",
                )
            else:
                presentation = _sentences(
                    f"wearing {top}" if top else "wearing a secure fitted swimwear top",
                    f"with {bottom}" if bottom else "with matching secure fitted swimwear bottoms",
                    "both swimwear pieces are clearly present with visible fabric, straps, seams, and normal secure coverage",
                )
        elif face_only:
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
    return _sentences(*body_parts), presentation, "clinical" if clinical else "clothed"


def _macro_sections_v241(profile: dict, plan: dict) -> dict[str, str]:
    macro = dict(_extreme_macro_sections_v231(profile, plan))
    focus = _focus_value_v231(plan)
    f = focus.lower()
    if "nose" in f or "septum" in f:
        macro["crop"] = _sentences(
            "single continuous clinical macro photograph centered on the nose, nostrils, columella, and septum",
            "the nose and immediately adjacent cheek skin fill approximately eighty-five percent of the image",
            "the top edge of the crop passes across the lower nose bridge below the eyes and the bottom edge includes the philtrum and upper lip",
        )
        macro["camera"] = _sentences(
            "camera centered directly on the nose and septum",
            "rectilinear 105mm macro-lens perspective with precise close-focus detail",
            "natural local proportions and continuous surrounding facial skin",
        )
        macro["exclusion"] = "one uninterrupted macro photograph with one continuous natural crop"
    return macro


class CharacterBlueprintCreatorV241(CharacterBlueprintCreatorV240):
    FUNCTION = "build_blueprint_v241"
    DESCRIPTION = (
        "Current Character Creator with combined tan profiles, structured tattoo locations, crop-aware marks, explicit swimwear, "
        "and pubic-hair color matched to the selected head-hair color."
    )

    @classmethod
    def INPUT_TYPES(cls):
        base = copy.deepcopy(super().INPUT_TYPES())
        required = base["required"]
        out: dict = {}
        for key, spec in required.items():
            if key == "complexion":
                out[key] = spec
                out["tan_profile"] = (TAN_PROFILES_V241, {"default": "None"})
                continue
            if key in {"tan_level", "tan_line_state"}:
                continue
            if key == "tan_line_pattern":
                out[key] = (TAN_LINE_PATTERNS_V241, {"default": "String Bikini — Minimal Triangle and Tight V"})
                continue
            if key == "tattoo_status":
                out[key] = spec
                out["tattoo_input_mode"] = (TATTOO_INPUT_MODES_V241, {"default": "Descriptor List"})
                continue
            if key == "tattoo_descriptors":
                out[key] = spec
                out["structured_tattoo_location"] = (TATTOO_LOCATIONS_V241, {"default": "Unspecified"})
                out["structured_tattoo_description"] = ("STRING", {"default": "", "multiline": True, "placeholder": "Design, color, scale, and exact placement details"})
                continue
            out[key] = spec
        base["required"] = out
        return base

    def build_blueprint_v241(self, **kwargs):
        tan_profile = kwargs.pop("tan_profile")
        tattoo_input_mode = kwargs.pop("tattoo_input_mode")
        structured_tattoo_location = kwargs.pop("structured_tattoo_location")
        structured_tattoo_description = kwargs.pop("structured_tattoo_description")
        tan_level, tan_state = _tan_profile_parts(tan_profile)
        kwargs["tan_level"] = tan_level
        kwargs["tan_line_state"] = tan_state

        warnings: list[str] = []
        tattoo_status = kwargs.get("tattoo_status")
        descriptor_filled = bool(str(kwargs.get("tattoo_descriptors", "")).strip())
        structured_filled = structured_tattoo_location not in {"", "Unspecified"} or bool(str(structured_tattoo_description).strip())
        if tattoo_status == "Multiple":
            tattoo_input_mode = "Descriptor List"
        elif tattoo_status == "One":
            if tattoo_input_mode == "Descriptor List" and not descriptor_filled and structured_filled:
                tattoo_input_mode = "Structured Single Tattoo"
                warnings.append("Single tattoo source automatically switched to Structured Single Tattoo because the descriptor list was blank.")
            elif tattoo_input_mode == "Structured Single Tattoo" and not structured_filled and descriptor_filled:
                tattoo_input_mode = "Descriptor List"
                warnings.append("Single tattoo source automatically switched to Descriptor List because the structured tattoo fields were blank.")
        if tattoo_status == "One" and tattoo_input_mode == "Structured Single Tattoo":
            structured_text = _structured_tattoo_text(structured_tattoo_location, structured_tattoo_description)
            kwargs["tattoo_descriptors"] = structured_text
            if not structured_text:
                warnings.append("Structured Single Tattoo is active but no tattoo location or description was supplied.")

        result = list(super().build_blueprint_v240(**kwargs))
        profile = copy.deepcopy(result[8])

        tattoo_records = [_parse_tattoo_record_v241(x) for x in profile.get("tattoo_entries", [])]
        piercing_records = profile.get("piercing_records", [])
        concise_tattoos = [_tattoo_phrase_v241(r) for r in tattoo_records if _tattoo_phrase_v241(r)]
        concise_piercings = [_piercing_phrase_v241(r) for r in piercing_records if _piercing_phrase_v241(r)]
        concise_marks = _sentences(
            "permanent skin marking: " + "; ".join(concise_tattoos) if concise_tattoos else "",
            "permanent jewelry: " + "; ".join(concise_piercings) if concise_piercings else "",
        )

        profile.update({
            "schema": "CHARACTER_BLUEPRINT_V241",
            "schema_version": 13,
            "tan_profile": tan_profile,
            "tan_level": tan_level,
            "tan_line_state": tan_state,
            "tan_line_regions": sorted(TAN_PATTERN_REGIONS_V241.get(profile.get("tan_line_pattern"), set())),
            "tattoo_input_mode": tattoo_input_mode,
            "structured_tattoo_location": structured_tattoo_location,
            "structured_tattoo_description": structured_tattoo_description,
            "tattoo_records": tattoo_records,
            "marks_prompt": concise_marks,
        })
        profile["tan_base_prompt"] = _tan_base_v241(profile)
        if warnings:
            profile["warnings"] = _sentences(profile.get("warnings", ""), *warnings)

        active_character = _sentences(
            profile.get("gender_authority_prompt", ""), profile.get("identity_detail_prompt", ""),
            profile.get("active_body_prompt", ""), profile.get("active_presentation_prompt", ""), concise_marks,
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
        summary = re.sub(r"^Tan / skin variation:.*\n", "", str(profile.get("presentation_summary", "")), flags=re.M)
        tan_summary = tan_profile if tan_profile != "Custom" else f"Custom — {_clean_phrase(profile.get('custom_tan_description', '')) or '[blank]'}"
        profile["presentation_summary"] = summary.replace("Warnings:", f"Tan / skin variation: {tan_summary}\nWarnings:")

        result[4] = concise_marks
        result[6] = active_character
        result[8] = profile
        result[9] = profile.get("warnings", "")
        result[15] = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        result[18] = active_character
        result[19] = profile["clothed_character_prompt"]
        result[20] = profile["clinical_character_prompt"]
        result[21] = profile["presentation_summary"]
        return tuple(result)


class CharacterShotControlV241(CharacterShotControlV240):
    FUNCTION = "build_shot_plan_v241"
    DESCRIPTION = (
        "Current Shot Control with strict front/rear orientation, prone and social-media gestures, body-scale camera targeting, "
        "and regional-documentation pose suppression."
    )

    @classmethod
    def INPUT_TYPES(cls):
        base = copy.deepcopy(super().INPUT_TYPES())
        base["required"]["pose"] = (POSES_V241, {"default": "Neutral Standing"})
        return base

    def build_shot_plan_v241(self, **kwargs):
        result = list(super().build_shot_plan_v240(**kwargs))
        plan = copy.deepcopy(result[0])
        plan["schema"] = "FCC_SHOT_PLAN_V241"
        plan["schema_version"] = 8

        custom_direction = plan.get("planner_mode") == "Custom Shot Direction — Keep Character Settings"
        if not custom_direction and not _is_extreme_closeup_v231(plan):
            view_prompt = _strict_view_prompt(plan)
            height_prompt = _height_prompt_for_plan(plan)
            lens = str(plan.get("lens", ""))
            lens_prompt = LENS_PROMPTS_V2.get(lens, "")
            if plan.get("camera_height") == "Custom" or lens == "Custom":
                custom_camera = _clean_phrase(kwargs.get("custom_camera", ""))
                if custom_camera:
                    height_prompt = custom_camera
                    lens_prompt = ""
            plan["camera_prompt"] = _sentences(view_prompt, height_prompt, lens_prompt)

        if kwargs.get("pose") == "Custom":
            plan["pose_prompt"] = _clean_phrase(kwargs.get("custom_pose", ""))
        else:
            plan["pose_prompt"] = POSE_PROMPTS_V241.get(kwargs.get("pose"), plan.get("pose_prompt", ""))

        ignored_extra: list[str] = []
        if _regional_pose_should_be_suppressed(plan):
            plan["pose_prompt"] = ""
            focus = str(plan.get("focus_region", "")).lower()
            if not any(x in focus for x in ("face", "head", "mouth", "eye", "nose")):
                plan["expression_prompt"] = ""
            ignored_extra.append("pose for regional documentation")
            if not plan.get("expression_prompt"):
                ignored_extra.append("expression outside facial regional crop")

        if _is_direct_back(plan) and kwargs.get("pose") != "Over-the-Shoulder Blogger Pose":
            plan["expression_prompt"] = ""
            ignored_extra.append("facial expression in strict back view")

        if kwargs.get("pose") == "Walking":
            if _camera_view(plan) == "Front View":
                plan["pose_prompt"] = "walking naturally toward the camera with believable opposite arm-and-leg movement"
            elif _is_direct_back(plan):
                plan["pose_prompt"] = "walking naturally away from the camera with believable opposite arm-and-leg movement"
        elif kwargs.get("pose") == "Lying Prone / On Stomach" and _is_direct_back(plan):
            plan["pose_prompt"] = "lying flat face-down on the stomach with the back, waist, hips, and backs of the legs presented to the camera and the body aligned without twisting"
        elif kwargs.get("pose") == "Blowing a Kiss":
            plan["expression_prompt"] = "lips gently pursed in a natural blowing-kiss expression"
        elif kwargs.get("pose") == "Index Finger Lightly Between Lips":
            plan["expression_prompt"] = "playful relaxed expression with the lips lightly around the fingertip"
        elif kwargs.get("pose") == "Licking a Popsicle":
            plan["expression_prompt"] = "playful natural expression while the tongue lightly touches the popsicle"

        plan["final_shot_prompt"] = _sentences(
            plan.get("framing_prompt", ""), plan.get("camera_prompt", ""), plan.get("pose_prompt", ""),
            plan.get("expression_prompt", ""), plan.get("scene_prompt", ""), plan.get("environment_prompt", ""),
            _clean_phrase(kwargs.get("shot_suffix", "")),
        )
        plan["active_settings_summary"] = _rebuild_shot_summary(plan, ignored_extra)
        result[0] = plan
        result[1] = plan["final_shot_prompt"]
        result[3] = plan.get("camera_prompt", "")
        result[4] = plan.get("pose_prompt", "")
        result[5] = plan.get("expression_prompt", "")
        result[7] = plan["active_settings_summary"]
        result[8] = json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True)
        return tuple(result)


class CharacterPromptAssemblerV241(CharacterPromptAssemblerV240):
    FUNCTION = "assemble_prompt_v241"
    DESCRIPTION = (
        "Visibility compiler with camera-orientation awareness, explicit swimwear, pattern-specific tan lines, strict rear views, "
        "and positive-boundary nose/septum macro routing."
    )

    def assemble_prompt_v241(
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

        tan = _tan_prompt_for_plan_v241(profile, plan)
        marks, visible_tattoos, visible_piercings = _visible_marks_v241(profile, plan)

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
            routing_mode = "extreme_closeup_visibility_compiled_v241"
            scene = ""
        else:
            crop = _crop_prompt_v230(plan)
            custom_direction = _clean_phrase(plan.get("framing_prompt", "")) if plan.get("planner_mode") == "Custom Shot Direction — Keep Character Settings" else ""
            visible_scope = _visible_tags_v241(plan)
            face_or_headshot = visible_scope.issubset(FACE_TAGS | {"shoulders", "upper_chest", "neck"})
            shot_section = _sentences(
                custom_direction or crop,
                "" if custom_direction else _clean_phrase(plan.get("camera_prompt", "")),
                "" if custom_direction or face_or_headshot or _regional_pose_should_be_suppressed(plan) else _clean_phrase(plan.get("pose_prompt", "")),
                _clean_phrase(plan.get("expression_prompt", "")),
                _clean_phrase(plan.get("scene_prompt", "")),
                _clean_phrase(plan.get("environment_prompt", "")),
            )
            character_section = _sentences(_identity_for_view(profile, plan), tan)
            body_section, presentation, _ = _visible_body_and_presentation_v241(profile, plan)
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
            routing_mode = "standard_visibility_compiled_v241"

        width = int(plan.get("recommended_width", 1024))
        height = int(plan.get("recommended_height", 1280))
        character_id = profile.get("character_id", "character")
        focus = plan.get("focus_region", "")
        shot_id = _slug(_sentences(character_id, generation_purpose, plan.get("shot_type", ""), _camera_view(plan), focus, plan.get("pose", "")))
        presentation_mode = profile.get("presentation_mode", "Unspecified")
        advisory = (
            f"Visibility compiler included {len(visible_tattoos)} tattoo record(s) and {len(visible_piercings)} piercing record(s). "
            "Off-frame, rear/front-incompatible, and clothing-covered anatomy and marks were omitted."
        )
        notes = "\n".join([
            f"Purpose: {generation_purpose}",
            f"Reference: {reference}",
            "Visibility Compiler V2.4.1: ACTIVE",
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
            f"{width} × {height} from {plan.get('aspect_ratio', 'selected aspect ratio')}",
            json.dumps(sections, indent=2, ensure_ascii=False),
            character_section,
            scene,
        )


class QwenDatasetQueueV241(QwenDatasetQueueV240):
    FUNCTION = "build_queue"
    DESCRIPTION = "Qwen dataset queue using V2.4.1 camera-direction and visibility routing."

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
                        "focus_mode": "Extreme Close-Up", "focus_region": focus,
                        "selected_extreme_closeup_focus": focus, "shot_type": "Extreme Close-Up — Single Detail",
                        "lens": "105mm Macro", "environment_prompt": "plain clinical documentation background with flat even lighting",
                        "recommended_width": 1024, "recommended_height": 1024, "aspect_ratio": "Square 1:1",
                    }
                else:
                    shot_type = "Face Close-Up" if cat == "closeup" else "Waist-Up Midshot" if cat == "midshot" else "Full Body"
                    if cat in {"anatomy", "anatomy_focus"}:
                        shot_type = "Close-Up — Regional Documentation" if cat == "anatomy_focus" else "Full Body"
                    plan = {
                        "shot_type": shot_type,
                        "focus_mode": "Regional Close-Up" if cat == "anatomy_focus" else "Inactive",
                        "focus_region": desc,
                        "camera_view": "Front View",
                        "camera_prompt": "standard rectilinear camera perspective",
                        "pose_prompt": "", "expression_prompt": "neutral expression",
                        "scene_prompt": "only the primary character is visible",
                        "environment_prompt": "plain neutral background with even realistic lighting",
                        "recommended_width": 1024,
                        "recommended_height": 1280 if cat in {"closeup", "midshot", "anatomy_focus"} else 1536,
                        "aspect_ratio": "Portrait 4:5" if cat in {"closeup", "midshot", "anatomy_focus"} else "Portrait 2:3",
                        "framing_prompt": desc,
                    }
                assembled = CharacterPromptAssemblerV241().assemble_prompt_v241(
                    profile, plan,
                    "Qwen — Anatomy Documentation" if cat in {"anatomy", "anatomy_focus"} else "Qwen — Identity Documentation",
                    reference_label,
                    custom_suffix=prompt_suffix,
                )
                prompt = assembled[1]
                seed = int(starting_seed) + idx
                sid = f"{spec['shot_id']}_v{variation+1:02d}"
                prefix = f"{output_root}/{cat}/{idx+1:04d}_{sid}"
                w = int(plan.get("recommended_width", 1024)); h = int(plan.get("recommended_height", 1280))
                item = {"index":idx+1,"shot_id":sid,"category":cat,"seed":seed,"filename_prefix":prefix,"width":w,"height":h,"prompt":prompt}
                prompts.append(prompt); seeds.append(seed); ids.append(sid); cats.append(cat); prefixes.append(prefix); widths.append(w); heights.append(h); manifest.append(item)
                idx += 1
        total = len(manifest)
        progress = [f"{x['index']} of {total} | {x['category']} | {x['shot_id']}" for x in manifest]
        plan_json = json.dumps({
            "schema":"FCC_QWEN_DATASET_PLAN_V241", "schema_version":6, "character_id":character_id,
            "plan":dataset_plan, "images_per_group":images_per_group, "variations_per_shot":variations_per_shot,
            "total_images":total, "items":manifest,
        }, indent=2, ensure_ascii=False)
        return prompts,seeds,ids,cats,prefixes,widths,heights,[plan_json for _ in prompts],progress


__all__ = [
    "QwenDatasetQueueV241",
    "FCCDatasetDirector",
    "FCCQueueItemRouter",
    "CharacterBlueprintCreatorV241",
    "CharacterShotControlV241",
    "CharacterPromptAssemblerV241",
]
