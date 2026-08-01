from __future__ import annotations

import json
import re
from typing import Any

from .nodes_v230 import _clean_phrase, _sentences
from .nodes_v253 import _piercing_geometry, _piercing_location, _tattoo_record_prompt_v253


KREA_BLUEPRINT_PLANS = [
    "Anchors Only — 2",
    "Face Detail Documentation — 10",
    "Body Regions Clothed",
    "Body Regions Clinical Unclothed",
    "Canonical Midshots — Clothed and Clinical",
    "Canonical Full Body — Clothed and Clinical",
    "Complete Blueprint Documentation",
]

QWEN_FACE_TARGETS = [
    "Approved Face-Visible Identity Angles — Core 8",
    "Approved Face-Visible Identity Angles — Extended 12",
]


# -----------------------------------------------------------------------------
# Shared prompt helpers
# -----------------------------------------------------------------------------

def _slug(text: str) -> str:
    value = str(text or "").lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "item"


def _record_visible(record: dict[str, Any], region_tokens: set[str]) -> bool:
    tags = {str(tag).lower() for tag in record.get("region_tags", [])}
    return bool(tags & region_tokens)


def _side_from_location(location: str) -> str:
    match = re.match(r"^(left|right)\b", str(location or "").strip().lower())
    return match.group(1) if match else ""


def _region_marks(profile: dict[str, Any], region_tokens: set[str]) -> str:
    """Compile only marks physically relevant to the current Krea body region."""
    phrases: list[str] = []
    tattoo_records = profile.get("tattoo_records", [])
    if not isinstance(tattoo_records, list):
        tattoo_records = []
    for record in tattoo_records:
        if not isinstance(record, dict) or not _record_visible(record, region_tokens):
            continue
        location = str(record.get("location", "")).strip().lower()
        desc = _clean_phrase(record.get("description") or record.get("raw") or "tattoo")
        quantity = int(record.get("quantity", 1) or 1)
        if "full back" in location or re.match(r"^full\s+(left|right)\s+(arm|leg)\s+sleeve$", location):
            phrases.append(_tattoo_record_prompt_v253(record, None))
        else:
            side = _side_from_location(location)
            side_lock = f" on the anatomical {side} side only" if side else ""
            phrases.append(_sentences(
                f"exactly {quantity} configured permanent tattoo appears at {location}{side_lock}, depicting {desc}",
                "preserve the configured scale, count, anatomical side, and exact body location",
                "do not mirror, duplicate, ghost, split, invent, or relocate the tattoo",
            ))

    piercing_records = profile.get("piercing_records", [])
    if not isinstance(piercing_records, list):
        piercing_records = []
    for record in piercing_records:
        if not isinstance(record, dict) or not _record_visible(record, region_tokens):
            continue
        location = str(record.get("location", "")).strip()
        material = str(record.get("material", "")).strip().lower()
        jewelry = str(record.get("jewelry_type", "piercing jewelry")).strip().lower()
        quantity = int(record.get("quantity", 1) or 1)
        phrases.append(_sentences(
            f"exactly {quantity} healed permanent {material} {jewelry} piercing is present at the exact configured {location.lower()}",
            _piercing_location(location),
            _piercing_geometry(jewelry),
            "the jewelry passes through living tissue with a healed entry point and an exit point when the selected jewelry requires one",
            "it is not floating, glued on, clipped on, painted on, or resting across the skin as a surface ornament",
            "do not add detached beads, extra holes, extra jewelry ends, duplicates, or jewelry on the opposite side",
        ))
    return _sentences(*phrases)


def _face_core(profile: dict[str, Any]) -> str:
    return _sentences(
        profile.get("gender_authority_prompt", ""),
        profile.get("identity_detail_prompt", "") or profile.get("face_identity", ""),
        profile.get("hair_prompt", ""),
    )


def _nonface_identity(profile: dict[str, Any]) -> str:
    return _sentences(
        profile.get("gender_authority_prompt", ""),
        profile.get("age_range", "") and f"age range {profile.get('age_range')}",
        profile.get("heritage_prompt", ""),
    )


def _skin(profile: dict[str, Any]) -> str:
    return _sentences(
        profile.get("base_complexion_stability_prompt", ""),
        profile.get("tan_base_prompt", ""),
        "natural pores, fine skin texture, realistic small asymmetries, and no plastic smoothing",
    )


def _all_outfit(profile: dict[str, Any]) -> str:
    return _sentences(
        profile.get("default_clothing_prompt", "complete simple fitted clothing"),
        profile.get("clothed_upper_body", ""),
        profile.get("clothed_lower_body", ""),
    )


def _regional_outfit(profile: dict[str, Any], region_tokens: set[str]) -> str:
    """Use only garments intersecting the requested regional crop."""
    components = profile.get("outfit_components")
    if not isinstance(components, dict):
        return profile.get("default_clothing_prompt", "complete simple fitted clothing")

    upper_regions = {
        "upper_torso", "chest", "breast", "shoulders", "back", "upper_back",
        "arms", "left_arm", "right_arm", "forearms", "left_forearm", "right_forearm",
        "elbows", "left_elbow", "right_elbow", "hands", "left_hand", "right_hand",
        "wrists", "left_wrist", "right_wrist", "abdomen", "waist",
    }
    lower_regions = {
        "pelvis", "groin", "pubic", "hips", "buttocks", "legs", "thighs", "knees",
        "shins", "calves", "ankles", "feet", "left_foot", "right_foot",
    }
    foot_regions = {"feet", "left_foot", "right_foot", "left_sole", "right_sole"}

    wants_upper = bool(region_tokens & upper_regions)
    wants_lower = bool(region_tokens & lower_regions)
    wants_feet = bool(region_tokens & foot_regions)
    kind = str(components.get("kind", ""))

    parts: list[str] = []
    if kind == "one_piece" and (wants_upper or wants_lower):
        one_piece = _clean_phrase(components.get("one_piece"))
        if one_piece:
            parts.append(f"the selected complete {one_piece} remains normally worn across only the visible crop")
    else:
        top = _clean_phrase(components.get("top") or components.get("swimwear_top"))
        bottom = _clean_phrase(components.get("bottom") or components.get("swimwear_bottom"))
        if wants_upper and top:
            parts.append(f"the selected complete {top} remains normally worn across the visible upper-body region")
        if wants_lower and bottom:
            parts.append(f"the selected complete {bottom} remains normally worn across the visible lower-body region")
    footwear = _clean_phrase(components.get("footwear"))
    if wants_feet and footwear:
        parts.append(f"the selected complete {footwear} remains worn on the documented foot or feet")
    outerwear = _clean_phrase(components.get("outerwear"))
    if wants_upper and outerwear:
        parts.append(f"the selected {outerwear} remains present only where it physically overlaps this crop")
    if not parts:
        parts.append("the selected outfit remains worn outside the crop; only physically intersecting garment edges may enter the frame")
    parts.extend([
        "do not widen the regional crop to display the complete outfit",
        "the visible garment does not change category, disappear, become skin, or transform into leggings or another unselected garment",
    ])
    return _sentences(*parts)


def _clinical(profile: dict[str, Any], region_tokens: set[str], global_body: bool = False) -> str:
    upper = bool(region_tokens & {
        "upper_torso", "chest", "breast", "back", "shoulders", "arms", "forearms", "hands",
        "abdomen", "waist", "left_breast", "right_breast",
    }) or global_body
    lower = bool(region_tokens & {
        "pelvis", "groin", "pubic", "hips", "buttocks", "legs", "thighs", "knees", "shins",
        "calves", "feet", "left_foot", "right_foot",
    }) or global_body
    parts: list[str] = [
        "neutral non-aroused adult clinical anatomy documentation",
        "unclothed only where the documented body region requires direct anatomical visibility",
        "ordinary relaxed posture, hands outside the documented region, no sensual posing, and no hand contact with anatomy",
    ]
    if upper:
        parts.extend([
            profile.get("anatomy_upper_body", ""),
            profile.get("chest_anatomy_prompt", ""),
            profile.get("bust_anatomy_authority_prompt", ""),
        ])
    if lower:
        parts.extend([
            profile.get("anatomy_lower_body", ""),
            profile.get("groin_anatomy_prompt", "") if bool(region_tokens & {"pelvis", "groin", "pubic"}) or global_body else "",
            profile.get("pubic_hair_prompt", "") if bool(region_tokens & {"pelvis", "groin", "pubic"}) or global_body else "",
        ])
    parts.append(profile.get("anatomy_integrity_lock", ""))
    return _sentences(*parts)


def _targeted_body(profile: dict[str, Any], region_tokens: set[str], presentation: str) -> str:
    upper = bool(region_tokens & {
        "upper_torso", "chest", "breast", "back", "shoulders", "arms", "forearms", "hands",
        "abdomen", "waist", "left_breast", "right_breast",
    })
    lower = bool(region_tokens & {
        "pelvis", "groin", "pubic", "hips", "buttocks", "legs", "thighs", "knees", "shins",
        "calves", "feet", "left_foot", "right_foot",
    })
    parts: list[str] = []
    if upper:
        parts.extend([
            profile.get("body_type_authority_prompt", ""),
            profile.get("clothed_upper_body", "") if presentation == "clothed" else profile.get("anatomy_upper_body", ""),
            profile.get("chest_clothed_prompt", "") if presentation == "clothed" else profile.get("chest_anatomy_prompt", ""),
            profile.get("bust_clothed_authority_prompt", "") if presentation == "clothed" else profile.get("bust_anatomy_authority_prompt", ""),
        ])
    if lower:
        parts.extend([
            profile.get("clothed_lower_body", "") if presentation == "clothed" else profile.get("anatomy_lower_body", ""),
        ])
    return _sentences(*parts)


def _photo_base() -> str:
    return _sentences(
        "realistic consumer-camera documentation photograph",
        "plain neutral background and even soft daylight",
        "rectilinear perspective, believable adult proportions, natural skin texture, and no glamour retouching",
        "one adult primary subject only",
    )


def _regional_integrity(shot_id: str, region_tokens: set[str], category: str) -> str:
    sid = str(shot_id).lower()
    phrases: list[str] = []
    left_only = "left" in sid and "right" not in sid
    right_only = "right" in sid and "left" not in sid

    if "hand" in sid or "palm" in sid:
        side = "left" if left_only else "right" if right_only else "selected"
        phrases.extend([
            f"show exactly one anatomically normal {side} hand when this is a single-hand detail",
            "the hand has one palm, one wrist, and exactly five naturally separated fingers with no extra, fused, duplicated, or missing digits",
        ])
    if "foot" in sid or "sole" in sid:
        side = "left" if left_only else "right" if right_only else "selected"
        phrases.extend([
            f"show exactly one anatomically normal {side} foot when this is a single-foot detail",
            "the foot has one heel, one arch, one ball, and exactly five naturally formed toes with no extra, fused, duplicated, or missing digits",
        ])
    if any(token in sid for token in ("arm", "forearm", "elbow")) and (left_only or right_only):
        side = "left" if left_only else "right"
        phrases.append(f"document only the anatomical {side} limb; the opposite arm remains outside the crop")
    if any(token in sid for token in ("chest", "breast")) and (left_only or right_only):
        side = "left" if left_only else "right"
        phrases.append(f"document only the anatomical {side} chest or breast region; do not mirror it or add a second breast inside this tight regional crop")
    if any(token in sid for token in ("thigh", "shin", "calf", "knee")) and (left_only or right_only):
        side = "left" if left_only else "right"
        phrases.append(f"document only the anatomical {side} leg region; the opposite leg remains outside the crop")
    if category == "canonical_full_body":
        phrases.extend([
            "one single connected adult body is present",
            "exactly two arms, two hands, two legs, and two feet remain anatomically connected and fully inside the frame",
            "no duplicated torso, missing limb, extra limb, merged legs, or cropped crown",
        ])
    if category == "canonical_midshot":
        phrases.extend([
            "the complete crown and requested waist boundary are both visible",
            "both arms remain anatomically connected without duplication or truncation",
        ])
    return _sentences(*phrases)


def _spec(
    shot_id: str,
    category: str,
    description: str,
    presentation: str,
    regions: set[str],
    width: int,
    height: int,
    role: str,
) -> dict[str, Any]:
    return {
        "shot_id": shot_id,
        "category": category,
        "description": description,
        "presentation": presentation,
        "regions": regions,
        "width": width,
        "height": height,
        "identity_training_role": role,
    }


# -----------------------------------------------------------------------------
# Krea pre-LoRA Blueprint Documentation shot manifest
# -----------------------------------------------------------------------------

def _anchor_specs() -> list[dict[str, Any]]:
    return [
        _spec(
            "00_approved_face_anchor_candidate",
            "face_anchor",
            _sentences(
                "tight direct frontal facial identity portrait",
                "small clear margin above the complete crown; complete hairline, both sides of the head, and visible ear edges remain inside frame",
                "lower center ends exactly at the base of the neck before the clavicles; no chest, shoulders as broad forms, garment straps, or garment body",
                "neutral or soft closed-mouth expression, eye-level 85mm portrait perspective",
                "the face occupies approximately seventy to eighty percent of image height",
            ),
            "anchor",
            {"face", "forehead", "eyebrow", "nose", "mouth", "ears", "hair", "neck"},
            1024,
            1280,
            "APPROVE THIS IMAGE FOR QWEN IMAGE 1",
        ),
        _spec(
            "01_head_shoulders_support",
            "head_shoulders",
            _sentences(
                "direct frontal head-and-shoulders portrait",
                "complete crown, hair, face, neck, both shoulders, and only modest upper-chest context remain visible",
                "eye-level 85mm portrait perspective and neutral or soft closed-mouth expression",
            ),
            "clothed",
            {"face", "forehead", "eyebrow", "nose", "mouth", "ears", "hair", "neck", "shoulders", "upper_torso"},
            1024,
            1280,
            "SUPPORTING FACE REFERENCE — NOT THE QWEN ANGLE SOURCE UNLESS APPROVED",
        ),
    ]


def _face_detail_specs() -> list[dict[str, Any]]:
    rows = [
        ("face_complete_documentation", "complete face centered with forehead, eyebrows, eyes, nose, mouth, jawline, and chin visible", {"face", "forehead", "eyebrow", "eyes", "nose", "mouth", "jaw", "chin"}),
        ("eyes_nose_bridge", "tight crop of both eyes, both eyebrows, complete nose bridge, and upper cheeks", {"face", "eyes", "eyebrow", "nose", "forehead"}),
        ("nose_septum", "tight centered crop of the complete nose, nostrils, septum, nasal tip, and nearby cheeks", {"face", "nose"}),
        ("mouth_lips", "tight centered crop of the complete mouth, upper and lower lips, philtrum, mouth corners, and chin edge", {"face", "mouth", "lips", "chin"}),
        ("left_ear", "clinical close documentation of the anatomical left ear and adjacent side hairline", {"face", "ears", "left_ear", "hair"}),
        ("right_ear", "clinical close documentation of the anatomical right ear and adjacent side hairline", {"face", "ears", "right_ear", "hair"}),
        ("forehead_hairline", "tight crop of complete forehead, both eyebrows, temples, and the full frontal hairline", {"face", "forehead", "eyebrow", "hair"}),
        ("jaw_chin_neck", "tight lower-face crop showing mouth, jawline, chin, and upper neck", {"face", "mouth", "chin", "jaw", "neck"}),
    ]
    return [
        _spec(
            f"02_{sid}",
            "face_detail",
            desc,
            "anchor",
            regions,
            1024,
            1024,
            "BLUEPRINT FACIAL DETAIL — DO NOT SUBSTITUTE FOR APPROVED IDENTITY ANCHOR",
        )
        for sid, desc, regions in rows
    ]


def _clothed_region_specs() -> list[dict[str, Any]]:
    rows: list[tuple[str, str, set[str], int, int]] = [
        ("upper_torso_front", "front regional documentation from shoulders through natural waist; complete upper garment and both arms visible", {"upper_torso", "chest", "shoulders", "arms", "waist"}, 1024, 1280),
        ("upper_torso_back", "direct rear regional documentation from shoulders through natural waist", {"upper_torso", "back", "shoulders", "arms", "waist"}, 1024, 1280),
        ("chest_garment_front", "tight front documentation of the selected upper garment across the chest and upper ribs; preserve selected covered chest or bust silhouette", {"upper_torso", "chest", "breast"}, 1024, 1024),
        ("left_chest_garment_profile", "anatomical left profile documentation of the selected upper garment and covered chest contour", {"upper_torso", "chest", "breast", "left_breast"}, 1024, 1024),
        ("right_chest_garment_profile", "anatomical right profile documentation of the selected upper garment and covered chest contour", {"upper_torso", "chest", "breast", "right_breast"}, 1024, 1024),
        ("abdomen_waist_front", "front crop centered on abdomen, natural waist, upper hips, garment hem, and waistband", {"abdomen", "waist", "hips", "pelvis"}, 1024, 1024),
        ("abdomen_waist_back", "rear crop centered on lower back, natural waist, upper hips, garment hem, and waistband", {"back", "lower_back", "waist", "hips", "pelvis"}, 1024, 1024),
        ("lower_garment_front", "front close documentation of the selected lower garment across waistband, pelvis, hips, and upper thighs", {"pelvis", "hips", "thighs", "groin"}, 1024, 1024),
        ("lower_garment_back", "rear close documentation of the selected lower garment across waistband, hips, buttocks, and upper thighs", {"pelvis", "hips", "buttocks", "thighs"}, 1024, 1024),
        ("left_upper_arm", "complete anatomical left upper arm from shoulder through elbow, separated from torso", {"arms", "left_arm", "left_elbow"}, 1024, 1280),
        ("right_upper_arm", "complete anatomical right upper arm from shoulder through elbow, separated from torso", {"arms", "right_arm", "right_elbow"}, 1024, 1280),
        ("left_forearm", "tight anatomical left forearm documentation including elbow edge, forearm surfaces, and wrist", {"arms", "forearms", "left_forearm", "left_arm", "left_wrist"}, 1024, 1280),
        ("right_forearm", "tight anatomical right forearm documentation including elbow edge, forearm surfaces, and wrist", {"arms", "forearms", "right_forearm", "right_arm", "right_wrist"}, 1024, 1280),
        ("left_elbow", "tight anatomical left elbow documentation with upper-arm and forearm context", {"arms", "left_arm", "left_elbow", "left_forearm"}, 1024, 1024),
        ("right_elbow", "tight anatomical right elbow documentation with upper-arm and forearm context", {"arms", "right_arm", "right_elbow", "right_forearm"}, 1024, 1024),
        ("left_hand_dorsal", "anatomical left hand dorsal surface, wrist, all five separated fingers, and natural nails", {"hands", "left_hand", "left_wrist"}, 1024, 1024),
        ("right_hand_dorsal", "anatomical right hand dorsal surface, wrist, all five separated fingers, and natural nails", {"hands", "right_hand", "right_wrist"}, 1024, 1024),
        ("left_palm", "anatomical left palm facing camera with wrist and all five fingers separated and fully visible", {"hands", "left_hand", "left_wrist"}, 1024, 1024),
        ("right_palm", "anatomical right palm facing camera with wrist and all five fingers separated and fully visible", {"hands", "right_hand", "right_wrist"}, 1024, 1024),
        ("legs_front", "front documentation of both complete clothed legs from hips through both feet", {"hips", "legs", "thighs", "knees", "shins", "feet"}, 1024, 1280),
        ("legs_back", "rear documentation of both complete clothed legs from hips through both feet", {"hips", "buttocks", "legs", "thighs", "knees", "calves", "feet"}, 1024, 1280),
        ("left_thigh_knee", "anatomical left clothed thigh and knee from hip crease through upper shin", {"legs", "thighs", "left_thigh", "knees", "left_knee"}, 1024, 1280),
        ("right_thigh_knee", "anatomical right clothed thigh and knee from hip crease through upper shin", {"legs", "thighs", "right_thigh", "knees", "right_knee"}, 1024, 1280),
        ("left_lower_leg", "anatomical left clothed lower leg showing knee edge, shin, calf, ankle, and footwear transition", {"legs", "shins", "calves", "left_leg", "left_ankle", "left_foot"}, 1024, 1280),
        ("right_lower_leg", "anatomical right clothed lower leg showing knee edge, shin, calf, ankle, and footwear transition", {"legs", "shins", "calves", "right_leg", "right_ankle", "right_foot"}, 1024, 1280),
        ("left_footwear", "anatomical left foot and selected footwear from ankle through toe box, complete inside frame", {"feet", "left_foot", "left_ankle"}, 1024, 1024),
        ("right_footwear", "anatomical right foot and selected footwear from ankle through toe box, complete inside frame", {"feet", "right_foot", "right_ankle"}, 1024, 1024),
    ]
    return [
        _spec(
            f"clothed_{sid}",
            "body_region_clothed",
            desc,
            "clothed",
            regions,
            width,
            height,
            "BODY BLUEPRINT REFERENCE — EXCLUDE FROM FACE IDENTITY ANGLE TRAINING",
        )
        for sid, desc, regions, width, height in rows
    ]


def _clinical_region_specs() -> list[dict[str, Any]]:
    rows: list[tuple[str, str, set[str], int, int]] = [
        ("upper_torso_front", "neutral front upper-torso documentation from shoulders through upper abdomen", {"upper_torso", "chest", "shoulders", "arms"}, 1024, 1280),
        ("upper_torso_back", "neutral direct rear upper-back documentation from shoulders through lower ribs", {"upper_torso", "back", "shoulders"}, 1024, 1280),
        ("chest_front", "neutral centered front clinical documentation of the complete adult chest or breasts with natural spacing, position, and contour", {"chest", "breast", "left_breast", "right_breast"}, 1024, 1024),
        ("left_chest_profile", "anatomical left chest or breast profile with natural side contour and no hand contact", {"chest", "left_chest", "breast", "left_breast"}, 1024, 1024),
        ("right_chest_profile", "anatomical right chest or breast profile with natural side contour and no hand contact", {"chest", "right_chest", "breast", "right_breast"}, 1024, 1024),
        ("left_chest_close", "tight neutral clinical close documentation of the anatomical left chest or breast region only", {"chest", "left_chest", "breast", "left_breast"}, 1024, 1024),
        ("right_chest_close", "tight neutral clinical close documentation of the anatomical right chest or breast region only", {"chest", "right_chest", "breast", "right_breast"}, 1024, 1024),
        ("abdomen_front", "front abdomen documentation from lower ribs through navel and natural waist", {"abdomen", "navel", "waist"}, 1024, 1024),
        ("lower_back", "direct rear lower-back and waist documentation", {"back", "lower_back", "waist"}, 1024, 1024),
        ("full_back", "direct rear documentation of the complete back from shoulders through lower back and waist", {"back", "upper_back", "lower_back", "shoulders", "waist"}, 1024, 1280),
        ("pelvis_front", "neutral front lower-abdomen, pelvis, groin, and upper-thigh documentation", {"pelvis", "groin", "pubic", "hips", "thighs"}, 1024, 1024),
        ("pelvis_back", "neutral rear pelvis, buttocks, and upper-thigh documentation", {"pelvis", "buttocks", "hips", "thighs"}, 1024, 1024),
        ("pelvis_left_profile", "neutral anatomical left profile of pelvis, hip, groin contour, buttock, and upper thigh", {"pelvis", "groin", "hips", "buttocks", "thighs"}, 1024, 1024),
        ("pelvis_right_profile", "neutral anatomical right profile of pelvis, hip, groin contour, buttock, and upper thigh", {"pelvis", "groin", "hips", "buttocks", "thighs"}, 1024, 1024),
        ("left_upper_arm", "uncovered anatomical left upper arm from shoulder to elbow", {"arms", "left_arm", "left_elbow"}, 1024, 1280),
        ("right_upper_arm", "uncovered anatomical right upper arm from shoulder to elbow", {"arms", "right_arm", "right_elbow"}, 1024, 1280),
        ("left_elbow", "tight uncovered anatomical left elbow with upper-arm and forearm context", {"arms", "left_arm", "left_elbow", "left_forearm"}, 1024, 1024),
        ("right_elbow", "tight uncovered anatomical right elbow with upper-arm and forearm context", {"arms", "right_arm", "right_elbow", "right_forearm"}, 1024, 1024),
        ("left_forearm", "uncovered anatomical left forearm from elbow through wrist", {"arms", "forearms", "left_forearm", "left_wrist"}, 1024, 1280),
        ("right_forearm", "uncovered anatomical right forearm from elbow through wrist", {"arms", "forearms", "right_forearm", "right_wrist"}, 1024, 1280),
        ("left_hand_dorsal", "anatomical left hand dorsal surface with wrist, natural nails, and all five fingers", {"hands", "left_hand", "left_wrist"}, 1024, 1024),
        ("right_hand_dorsal", "anatomical right hand dorsal surface with wrist, natural nails, and all five fingers", {"hands", "right_hand", "right_wrist"}, 1024, 1024),
        ("left_palm", "anatomical left palm with wrist and all five fingers naturally separated", {"hands", "left_hand", "left_wrist"}, 1024, 1024),
        ("right_palm", "anatomical right palm with wrist and all five fingers naturally separated", {"hands", "right_hand", "right_wrist"}, 1024, 1024),
        ("left_thigh_knee", "anatomical left thigh and knee from hip crease through upper shin", {"legs", "thighs", "left_thigh", "knees", "left_knee"}, 1024, 1280),
        ("right_thigh_knee", "anatomical right thigh and knee from hip crease through upper shin", {"legs", "thighs", "right_thigh", "knees", "right_knee"}, 1024, 1280),
        ("left_shin_calf", "anatomical left lower leg showing shin, calf, ankle, and Achilles region", {"legs", "shins", "calves", "left_leg", "left_ankle"}, 1024, 1280),
        ("right_shin_calf", "anatomical right lower leg showing shin, calf, ankle, and Achilles region", {"legs", "shins", "calves", "right_leg", "right_ankle"}, 1024, 1280),
        ("left_foot_top", "anatomical left foot top and three-quarter view with heel, arch contour, and all five toes visible", {"feet", "left_foot", "left_ankle"}, 1024, 1024),
        ("right_foot_top", "anatomical right foot top and three-quarter view with heel, arch contour, and all five toes visible", {"feet", "right_foot", "right_ankle"}, 1024, 1024),
        ("left_sole", "seated or reclined neutral clinical view of the complete anatomical left sole, heel, arch, ball, and five toes", {"feet", "left_foot", "left_sole"}, 1024, 1024),
        ("right_sole", "seated or reclined neutral clinical view of the complete anatomical right sole, heel, arch, ball, and five toes", {"feet", "right_foot", "right_sole"}, 1024, 1024),
    ]
    return [
        _spec(
            f"clinical_{sid}",
            "body_region_clinical",
            desc,
            "clinical",
            regions,
            width,
            height,
            "BODY/ANATOMY BLUEPRINT REFERENCE — EXCLUDE FROM FACE IDENTITY ANGLE TRAINING",
        )
        for sid, desc, regions, width, height in rows
    ]


def _canonical_specs(kind: str) -> list[dict[str, Any]]:
    views = [
        ("front", "direct front view"),
        ("front_left", "front-left three-quarter view"),
        ("left_profile", "true anatomical left profile"),
        ("rear_left", "rear-left three-quarter view"),
        ("back", "direct rear view"),
        ("rear_right", "rear-right three-quarter view"),
        ("right_profile", "true anatomical right profile"),
        ("front_right", "front-right three-quarter view"),
    ]
    specs: list[dict[str, Any]] = []
    for presentation in ("clothed", "clinical"):
        for key, view in views:
            if kind == "midshot":
                description = _sentences(
                    f"{view} complete-head waist-up body-proportion documentation",
                    "clear margin above the complete crown and lower boundary through natural waist and waistband",
                    "both arms visible and separated enough to document torso width",
                    "camera distance is widened before capture so the complete head and waist remain in the same frame",
                )
                width, height = 1024, 1280
                category = "canonical_midshot"
            else:
                description = _sentences(
                    f"{view} complete standing full-body body-proportion documentation",
                    "entire head, torso, both arms, both hands, both legs, and both feet inside frame with clear margins",
                    "neutral symmetrical posture with arms slightly separated from torso and both feet independently visible",
                    "camera distance is established before capture and the crown is never cropped",
                )
                width, height = 1024, 1536
                category = "canonical_full_body"
            specs.append(_spec(
                f"{presentation}_{kind}_{key}",
                category,
                description,
                presentation,
                {
                    "face", "hair", "upper_torso", "chest", "breast", "back", "abdomen", "waist",
                    "pelvis", "groin", "pubic", "hips", "buttocks", "arms", "forearms", "hands",
                    "legs", "thighs", "knees", "shins", "calves", "feet",
                },
                width,
                height,
                "BODY-PROPORTION REFERENCE — FACE IS NOT THE QWEN IDENTITY SOURCE",
            ))
    return specs


def _select_specs(plan: str) -> list[dict[str, Any]]:
    anchors = _anchor_specs()
    faces = _face_detail_specs()
    clothed = _clothed_region_specs()
    clinical = _clinical_region_specs()
    mids = _canonical_specs("midshot")
    fulls = _canonical_specs("full")
    if plan == KREA_BLUEPRINT_PLANS[0]:
        return anchors
    if plan == KREA_BLUEPRINT_PLANS[1]:
        return anchors + faces
    if plan == KREA_BLUEPRINT_PLANS[2]:
        return clothed
    if plan == KREA_BLUEPRINT_PLANS[3]:
        return clinical
    if plan == KREA_BLUEPRINT_PLANS[4]:
        return mids
    if plan == KREA_BLUEPRINT_PLANS[5]:
        return fulls
    return anchors + faces + clothed + clinical + mids + fulls


def _build_krea_prompt(profile: dict[str, Any], spec: dict[str, Any], suffix: str) -> str:
    regions = set(spec["regions"])
    presentation = str(spec["presentation"])
    face_visible = bool(regions & {"face", "forehead", "eyebrow", "eyes", "nose", "mouth", "ears", "hair", "chin", "jaw"})
    global_body = spec["category"] in {"canonical_midshot", "canonical_full_body"}

    if face_visible or global_body:
        identity = _face_core(profile)
    else:
        identity = _sentences(
            _nonface_identity(profile),
            "the head and face remain outside this regional crop; do not invent an additional face, second head, or portrait composition",
        )

    if presentation == "clinical":
        presentation_text = _clinical(profile, regions, global_body=global_body)
    elif presentation == "clothed":
        presentation_text = _all_outfit(profile) if global_body else _regional_outfit(profile, regions)
    else:
        presentation_text = _sentences(
            "a simple opaque neutral identity-documentation top may appear only where the selected crop permits it",
            "clothing must not cause the camera to widen or crop the crown",
        )

    if global_body:
        if presentation == "clothed":
            body_scope = _sentences(profile.get("active_body_prompt", ""), profile.get("clothed_upper_body", ""), profile.get("clothed_lower_body", ""))
        else:
            body_scope = _sentences(profile.get("active_body_prompt", ""), profile.get("anatomy_upper_body", ""), profile.get("anatomy_lower_body", ""))
    else:
        body_scope = _targeted_body(profile, regions, presentation)

    purpose = _sentences(
        "FCC Krea2 Blueprint Documentation Run",
        "construct the adult subject directly from the connected Character Blueprint",
        "this is an original Krea2 blueprint render, not an edit of another image",
        spec["identity_training_role"],
    )

    return _sentences(
        purpose,
        spec["description"],
        _photo_base(),
        identity,
        body_scope,
        presentation_text,
        _skin(profile),
        _region_marks(profile, regions),
        _regional_integrity(spec["shot_id"], regions, spec["category"]),
        "show only the body regions required by this shot and keep unrelated regions outside the crop",
        _clean_phrase(suffix),
    )


class FCCKreaBlueprintDatasetDirector:
    CATEGORY = "character creation/studio"
    FUNCTION = "direct"
    DESCRIPTION = (
        "One-click pre-LoRA Krea2 Blueprint Documentation Director. It generates the approved face-anchor candidate, one head-and-shoulders support portrait, focused face details, isolated clothed and clinical-unclothed body regions, eight-view midshots, and eight-view full-body proportions directly from the Character Blueprint."
    )
    RETURN_TYPES = ("STRING", "INT", "STRING", "STRING", "STRING", "INT", "INT", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("krea_prompts", "seeds", "shot_ids", "categories", "filename_prefixes", "widths", "heights", "dataset_plan_json", "queue_preview", "dashboard", "progress_labels")
    OUTPUT_IS_LIST = (True, True, True, True, True, True, True, False, False, False, True)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character_blueprint": ("CHARACTER_BLUEPRINT",),
                "dataset_plan": (KREA_BLUEPRINT_PLANS, {"default": "Complete Blueprint Documentation"}),
                "project_name": ("STRING", {"default": "FCC_Character"}),
                "starting_seed": ("INT", {"default": 2000, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
                "variations_per_shot": ("INT", {"default": 1, "min": 1, "max": 3}),
            },
            "optional": {
                "prompt_suffix": ("STRING", {"default": "", "multiline": True}),
            },
        }

    def direct(self, character_blueprint, dataset_plan, project_name, starting_seed, variations_per_shot, prompt_suffix=""):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        specs = _select_specs(str(dataset_plan))
        prompts: list[str] = []
        seeds: list[int] = []
        shot_ids: list[str] = []
        categories: list[str] = []
        prefixes: list[str] = []
        widths: list[int] = []
        heights: list[int] = []
        manifest: list[dict[str, Any]] = []
        index = 0
        root = f"{str(project_name).strip() or 'FCC_Character'}/Krea_Blueprint_Documentation"

        for spec in specs:
            for variation in range(int(variations_per_shot)):
                index += 1
                sid = f"{spec['shot_id']}_v{variation + 1:02d}"
                prompt = _build_krea_prompt(profile, spec, prompt_suffix)
                seed = int(starting_seed) + index - 1
                prefix = f"{root}/{spec['category']}/{index:04d}_{sid}"
                prompts.append(prompt)
                seeds.append(seed)
                shot_ids.append(sid)
                categories.append(spec["category"])
                prefixes.append(prefix)
                widths.append(int(spec["width"]))
                heights.append(int(spec["height"]))
                manifest.append({
                    "index": index,
                    "shot_id": sid,
                    "category": spec["category"],
                    "seed": seed,
                    "filename_prefix": prefix,
                    "width": spec["width"],
                    "height": spec["height"],
                    "presentation": spec["presentation"],
                    "regions": sorted(spec["regions"]),
                    "identity_training_role": spec["identity_training_role"],
                    "face_identity_source": spec["category"] == "face_anchor",
                    "prompt": prompt,
                })

        total = len(manifest)
        progress = [f"{item['index']} of {total} | {item['category']} | {item['shot_id']}" for item in manifest]
        plan_json = json.dumps({
            "schema": "FCC_KREA_BLUEPRINT_DATASET_PLAN_V253",
            "schema_version": 2,
            "character_id": profile.get("character_id", "character"),
            "plan": dataset_plan,
            "total_images": total,
            "qwen_handoff": "Approve item 1, then load that exact portrait as Qwen Image 1. Body and anatomy images never feed the Qwen angle lane.",
            "training_guidance": "Use the approved Krea anchor plus Qwen face angles as facial identity authority. Other Krea images document the connected Blueprint's body, anatomy, clothing, marks, and proportions.",
            "items": manifest,
        }, indent=2, ensure_ascii=False)
        preview = "\n".join(
            f"{item['index']:03d} | {item['category']} | {item['shot_id']} | {item['width']}x{item['height']} | {item['filename_prefix']}"
            for item in manifest
        )
        dashboard = "\n".join([
            "FCC KREA2 BLUEPRINT DOCUMENTATION — PRE-LORA",
            f"Character: {profile.get('character_id', 'character')}",
            f"Plan: {dataset_plan}",
            f"Total queued images: {total}",
            "Item 1: approved face-anchor candidate",
            "Item 2: supporting head-and-shoulders portrait",
            "Face detail items: nose, eyes, mouth, ears, hairline, jaw, and complete face",
            "Body items: isolated clothed and clinical-unclothed regions plus eight-view midshots and full bodies",
            "HANDOFF: approve one Krea face portrait, load it as Qwen Image 1, and use Qwen only for facial camera angles.",
        ])
        return prompts, seeds, shot_ids, categories, prefixes, widths, heights, plan_json, preview, dashboard, progress


class FCCKreaQueueItemRouter:
    CATEGORY = "character creation/studio"
    FUNCTION = "route"
    DESCRIPTION = "Maps one Krea Blueprint Dataset Director list item at a time into the existing no-identity-LoRA Krea documentation generator lane."
    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT", "STRING", "STRING", "INT", "INT")
    RETURN_NAMES = ("krea_prompt", "filename_prefix", "progress_label", "seed", "shot_id", "category", "width", "height")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "krea_prompt": ("STRING", {"forceInput": True}),
                "filename_prefix": ("STRING", {"forceInput": True}),
                "progress_label": ("STRING", {"forceInput": True}),
                "seed": ("INT", {"forceInput": True}),
                "shot_id": ("STRING", {"forceInput": True}),
                "category": ("STRING", {"forceInput": True}),
                "width": ("INT", {"forceInput": True}),
                "height": ("INT", {"forceInput": True}),
            }
        }

    def route(self, krea_prompt, filename_prefix, progress_label, seed, shot_id, category, width, height):
        return krea_prompt, filename_prefix, progress_label, seed, shot_id, category, width, height


# -----------------------------------------------------------------------------
# Qwen approved-face angle manifest. No body/Blueprint prose reaches encoder.
# -----------------------------------------------------------------------------

_FACE_ANGLES_CORE = [
    # Face-visible identity views only. Rear and direct-back head views are
    # intentionally excluded because they do not contribute facial identity.
    ("front", "eye_level", "close_up"),
    ("front_left", "eye_level", "close_up"),
    ("left_side", "eye_level", "close_up"),
    ("front_right", "eye_level", "close_up"),
    ("right_side", "eye_level", "close_up"),
    ("front", "low_angle", "close_up"),
    ("front", "elevated", "close_up"),
    ("front", "high_angle", "close_up"),
]
_FACE_ANGLES_ELEVATION = [
    ("front_left", "low_angle", "close_up"),
    ("front_left", "elevated", "close_up"),
    ("front_right", "low_angle", "close_up"),
    ("front_right", "elevated", "close_up"),
]


class FCCFaceAngleDatasetDirector:
    CATEGORY = "character creation/studio"
    FUNCTION = "direct"
    DESCRIPTION = (
        "Face-only Qwen angle director. It uses one approved Krea face portrait as Image 1 and emits only exact camera-angle metadata. Body, anatomy, clothing, tattoos, piercings, and Character Blueprint prose never reach the Qwen angle encoder."
    )
    RETURN_TYPES = ("STRING", "INT", "STRING", "STRING", "STRING", "INT", "INT", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("qwen_prompts", "seeds", "shot_ids", "categories", "filename_prefixes", "widths", "heights", "dataset_plan_json", "queue_preview", "dashboard", "progress_labels")
    OUTPUT_IS_LIST = (True, True, True, True, True, True, True, False, False, False, True)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character_blueprint": ("CHARACTER_BLUEPRINT",),
                "target": (QWEN_FACE_TARGETS, {"default": "Approved Face-Visible Identity Angles — Core 8"}),
                "approved_headshot_label": ("STRING", {"default": "Image 1"}),
                "project_name": ("STRING", {"default": "FCC_Character"}),
                "starting_seed": ("INT", {"default": 1000, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
                "variations_per_shot": ("INT", {"default": 1, "min": 1, "max": 2}),
                "images_per_group": ("INT", {"default": 8, "min": 5, "max": 10}),
                "lora_available": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "prompt_suffix": ("STRING", {"default": "", "multiline": True}),
                "complete_outfit_override": ("STRING", {"default": "", "multiline": True}),
            },
        }

    def direct(
        self,
        character_blueprint,
        target,
        approved_headshot_label,
        project_name,
        starting_seed,
        variations_per_shot,
        images_per_group,
        lora_available,
        prompt_suffix="",
        complete_outfit_override="",
    ):
        del images_per_group, lora_available, complete_outfit_override
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        angles = list(_FACE_ANGLES_CORE)
        if str(target) == QWEN_FACE_TARGETS[1]:
            angles += _FACE_ANGLES_ELEVATION

        prompts: list[str] = []
        seeds: list[int] = []
        shot_ids: list[str] = []
        categories: list[str] = []
        prefixes: list[str] = []
        widths: list[int] = []
        heights: list[int] = []
        items: list[dict[str, Any]] = []
        index = 0
        root = f"{str(project_name).strip() or 'FCC_Character'}/Qwen_Approved_Face_Angles"

        for azimuth, elevation, distance in angles:
            for variation in range(int(variations_per_shot)):
                index += 1
                sid = f"face__{azimuth}__{elevation}__{distance}_v{variation + 1:02d}"
                legacy = _sentences(
                    f"camera-only facial identity angle from {approved_headshot_label}",
                    "preserve the same approved face and do not redesign the person",
                    _clean_phrase(prompt_suffix),
                )
                seed = int(starting_seed) + index - 1
                prefix = f"{root}/{index:04d}_{sid}"
                category = "face_identity_angle"
                prompts.append(legacy)
                seeds.append(seed)
                shot_ids.append(sid)
                categories.append(category)
                prefixes.append(prefix)
                widths.append(1024)
                heights.append(1024)
                items.append({
                    "index": index,
                    "shot_id": sid,
                    "azimuth": azimuth,
                    "elevation": elevation,
                    "distance": distance,
                    "seed": seed,
                    "filename_prefix": prefix,
                })

        total = len(items)
        progress = [f"{item['index']} of {total} | approved face angle | {item['shot_id']}" for item in items]
        plan_json = json.dumps({
            "schema": "FCC_QWEN_APPROVED_FACE_ANGLES_V253",
            "schema_version": 2,
            "character_id": profile.get("character_id", "character"),
            "target": target,
            "approved_reference": approved_headshot_label,
            "qwen_scope": "facial camera angles only",
            "forbidden_scope": ["body blueprint", "clothing", "anatomy", "tattoos", "piercings", "full-body poses"],
            "clean_lane_requirement": "Use a matching Qwen Image Edit 2511 base plus the 2511 Multiple-Angles LoRA for <sks> mode. Keep unrelated image-edit LoRAs bypassed during diagnosis.",
            "items": items,
        }, indent=2, ensure_ascii=False)
        preview = "\n".join(
            f"{item['index']:03d} | {item['shot_id']} | {item['azimuth']} | {item['elevation']} | {item['distance']}"
            for item in items
        )
        dashboard = "\n".join([
            "FCC QWEN — APPROVED FACE ANGLES ONLY",
            f"Character: {profile.get('character_id', 'character')}",
            f"Approved reference: {approved_headshot_label}",
            f"Target: {target}",
            f"Total queued angles: {total}",
            "ENCODER SCOPE: exact camera-angle prompt only.",
            "DO NOT use a body, regional anatomy, or non-approved Krea image as Image 1.",
            "Qwen does not invent the body dataset in v2.8.13; Krea Blueprint Documentation owns that work.",
        ])
        return prompts, seeds, shot_ids, categories, prefixes, widths, heights, plan_json, preview, dashboard, progress
