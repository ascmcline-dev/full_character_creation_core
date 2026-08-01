from __future__ import annotations

import json
import re
from typing import Any, Iterable

from .nodes_v230 import _clean_phrase, _sentences
from .nodes_v253 import _tattoo_record_prompt_v253
from .nodes_v254 import _piercing_record_prompt_v254


KREA_BLUEPRINT_PLANS = [
    "Identity Anchors — 3",
    "Body-Only Regional Atlas — Clothed",
    "Body-Only Regional Atlas — Clinical Unclothed",
    "Complete Body-Only Regional Atlas — Clothed and Clinical",
    "Complete Pre-LoRA Documentation — Anchors + Body Atlas",
]

QWEN_ANGLE_TARGETS = [
    "Approved Face Identity Angles — Core 8",
    "Approved Face Identity Angles — Extended 12",
    "Approved Midshot Angles — Core 8",
    "Approved Full-Body Angles — Core 8",
    "Approved Regional Reference Angles — Core 8",
]


# -----------------------------------------------------------------------------
# Shared helpers
# -----------------------------------------------------------------------------

def _slug(text: str) -> str:
    value = str(text or "").lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "item"


def _unique_sentences(*parts: Any) -> str:
    seen: set[str] = set()
    out: list[str] = []
    for part in parts:
        text = _clean_phrase(part)
        if not text:
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            sentence = sentence.strip()
            key = re.sub(r"\s+", " ", sentence.lower()).strip(" .")
            if key and key not in seen:
                seen.add(key)
                out.append(sentence.rstrip(".") + ".")
    return " ".join(out).strip()


def _record_visible(record: dict[str, Any], region_tokens: set[str]) -> bool:
    tags = {str(tag).lower() for tag in record.get("region_tags", [])}
    return bool(tags & {str(token).lower() for token in region_tokens})


def _region_marks(profile: dict[str, Any], regions: set[str], presentation: str) -> str:
    phrases: list[str] = []
    tattoos = profile.get("tattoo_records")
    if not isinstance(tattoos, list):
        tattoos = []
    for record in tattoos:
        if not isinstance(record, dict) or not _record_visible(record, regions):
            continue
        prompt = _tattoo_record_prompt_v253(record, None)
        if presentation == "clothed":
            prompt = _sentences(
                prompt,
                "the tattoo remains visible wherever this regional crop exposes its configured skin surface; do not remove or redesign the selected garment merely to expose unrelated skin",
            )
        phrases.append(prompt)

    piercings = profile.get("piercing_records")
    if not isinstance(piercings, list):
        piercings = []
    for record in piercings:
        if not isinstance(record, dict) or not _record_visible(record, regions):
            continue
        phrases.append(_piercing_record_prompt_v254(record, None))
    return _unique_sentences(*phrases)


def _face_identity(profile: dict[str, Any]) -> str:
    return _unique_sentences(
        profile.get("gender_authority_prompt", ""),
        profile.get("identity_detail_prompt", "") or profile.get("face_identity", ""),
        profile.get("hair_prompt", ""),
    )


def _nonface_identity(profile: dict[str, Any]) -> str:
    return _unique_sentences(
        profile.get("gender_authority_prompt", ""),
        profile.get("age_range", "") and f"age range {profile.get('age_range')}",
        profile.get("heritage_prompt", ""),
    )


def _skin(profile: dict[str, Any]) -> str:
    return _unique_sentences(
        profile.get("base_complexion_stability_prompt", ""),
        profile.get("tan_base_prompt", ""),
        "natural pores, fine skin texture, realistic small asymmetries, and no plastic smoothing",
    )


def _regional_outfit(profile: dict[str, Any], regions: set[str]) -> str:
    components = profile.get("outfit_components")
    if not isinstance(components, dict):
        return _sentences(
            profile.get("default_clothing_prompt", "complete simple fitted clothing"),
            "show only garment sections that physically intersect this regional crop",
            "do not widen the frame to display the complete outfit",
        )

    upper = bool(regions & {
        "neck", "shoulders", "upper_torso", "chest", "breast", "back", "upper_back",
        "abdomen", "waist", "arms", "upper_arm", "elbow", "forearm", "wrist", "hand",
    })
    lower = bool(regions & {
        "pelvis", "groin", "pubic", "hips", "buttocks", "thigh", "knee", "shin", "calf",
        "ankle", "foot", "sole",
    })
    foot = bool(regions & {"foot", "sole", "ankle"})
    parts: list[str] = []
    if components.get("kind") == "one_piece" and (upper or lower):
        garment = _clean_phrase(components.get("one_piece"))
        if garment:
            parts.append(f"the selected complete {garment} remains normally worn across the visible crop")
    else:
        top = _clean_phrase(components.get("top") or components.get("swimwear_top"))
        bottom = _clean_phrase(components.get("bottom") or components.get("swimwear_bottom"))
        if upper and top:
            parts.append(f"the selected complete {top} remains normally worn across the visible upper-body region")
        if lower and bottom:
            parts.append(f"the selected complete {bottom} remains normally worn across the visible lower-body region")
    footwear = _clean_phrase(components.get("footwear"))
    if foot and footwear:
        parts.append(f"the selected complete {footwear} remains worn on the documented foot")
    if not parts:
        parts.append("only physically intersecting garment edges may enter the regional crop")
    parts.extend([
        "do not widen the frame to show the complete outfit",
        "the visible garment does not change category, disappear, become skin, or transform into an unselected garment",
    ])
    return _sentences(*parts)


def _clinical_body(profile: dict[str, Any], regions: set[str]) -> str:
    parts: list[str] = [
        "neutral non-aroused adult clinical anatomy documentation",
        "the documented region is uncovered only as required for direct anatomical visibility",
        "ordinary relaxed posture with no sensual posing and no hand contact with the documented anatomy",
    ]
    if regions & {"shoulders", "upper_torso", "chest", "breast", "back", "abdomen", "waist", "arms", "upper_arm", "elbow", "forearm", "wrist", "hand"}:
        parts.append(profile.get("body_type_authority_prompt", ""))
        parts.append(profile.get("anatomy_upper_body", ""))
    if regions & {"chest", "breast"}:
        parts.append(profile.get("bust_anatomy_authority_prompt", "") or profile.get("chest_anatomy_prompt", ""))
    if regions & {"pelvis", "groin", "pubic", "hips", "buttocks", "thigh", "knee", "shin", "calf", "ankle", "foot", "sole"}:
        parts.append(profile.get("anatomy_lower_body", ""))
    if regions & {"pelvis", "groin", "pubic"}:
        parts.append(profile.get("groin_anatomy_prompt", ""))
        parts.append(profile.get("pubic_hair_prompt", ""))
    if regions & {"chest", "breast", "pelvis", "groin", "pubic"}:
        parts.append(profile.get("anatomy_integrity_lock", ""))
    return _unique_sentences(*parts)


def _clothed_body(profile: dict[str, Any], regions: set[str]) -> str:
    parts: list[str] = []
    if regions & {"shoulders", "upper_torso", "chest", "breast", "back", "abdomen", "waist", "arms", "upper_arm", "elbow", "forearm", "wrist", "hand"}:
        parts.append(profile.get("body_type_authority_prompt", ""))
        parts.append(profile.get("clothed_upper_body", ""))
    if regions & {"chest", "breast"}:
        parts.append(profile.get("bust_clothed_authority_prompt", "") or profile.get("chest_clothed_prompt", ""))
    if regions & {"pelvis", "hips", "buttocks", "thigh", "knee", "shin", "calf", "ankle", "foot"}:
        parts.append(profile.get("clothed_lower_body", ""))
    return _unique_sentences(*parts)


def _photo_base() -> str:
    return _sentences(
        "realistic consumer-camera regional documentation photograph",
        "plain neutral background and even soft daylight",
        "rectilinear natural perspective with believable adult proportions and no glamour retouching",
        "one adult primary subject only",
    )


def _body_only_authority() -> str:
    return _sentences(
        "this is an isolated body-only regional documentation image",
        "the complete face and facial features remain outside the frame",
        "show only the selected body region and the minimum adjacent anatomy required to prove natural physical attachment",
        "do not include a complete person, distant body, portrait, second figure, or unrelated body region in the background",
    )


def _special_region_authority(shot_id: str, regions: set[str]) -> str:
    sid = str(shot_id).lower()
    parts: list[str] = []

    if "palm" in sid:
        side = "left" if "left" in sid else "right"
        parts.extend([
            f"the anatomical {side} arm extends straight forward from the unseen body",
            "the palm faces upward toward a camera positioned directly above and aimed straight downward",
            "the lower forearm enters from the bottom edge and connects continuously through the wrist into exactly one normal hand",
            "only the lower forearm, wrist, palm, thumb, and five naturally separated fingers remain inside the frame",
            "no head, torso, pelvis, opposite limb, complete body, oversized foreground hand, floating hand, or background person appears",
        ])
    elif "hand_dorsal" in sid:
        side = "left" if "left" in sid else "right"
        parts.extend([
            f"the anatomical {side} arm extends straight forward from the unseen body",
            "the palm faces downward and the natural back of the hand faces a camera positioned directly above",
            "the lower forearm, wrist, knuckles, tendons, fingernails, thumb, and five fingers form one continuous attached structure",
            "no head, torso, pelvis, opposite limb, complete body, oversized foreground hand, detached hand, or background person appears",
        ])
    elif "hand_thumb_profile" in sid or "hand_little_profile" in sid:
        side = "left" if "left" in sid else "right"
        edge = "thumb-side" if "thumb" in sid else "little-finger-side"
        parts.extend([
            f"isolated {edge} profile of the anatomical {side} hand",
            "camera level with the hand and perpendicular to the selected side surface",
            "only the lower forearm, wrist, and one continuous hand remain visible",
            "all five fingers remain naturally aligned without duplication, fusion, or detachment",
        ])
    elif any(token in sid for token in ("foot_dorsal", "foot_front")):
        side = "left" if "left" in sid else "right"
        parts.extend([
            f"isolated documentation of the anatomical {side} lower shin, ankle, and complete foot only",
            "the lower leg descends into the frame and the ankle remains straight with the foot naturally pointed downward",
            "the camera faces the front and upper surface of the foot; lower shin, ankle, instep, heel edges, and all five toes form one continuous attached structure",
            "no knee unless needed for attachment, thigh, pelvis, torso, head, opposite leg, second foot, giant foreground foot, detached foot, or background body appears",
        ])
    elif "foot_inner_profile" in sid or "foot_outer_profile" in sid:
        side = "left" if "left" in sid else "right"
        surface = "inner" if "inner" in sid else "outer"
        parts.extend([
            f"isolated anatomical {surface} side-profile documentation of the {side} lower shin, ankle, and complete foot",
            "the foot remains pointed downward from the visible lower shin",
            "heel, arch, ball, instep, and complete toe profile remain visible as one continuous attached structure",
            "camera is perpendicular to the selected side surface and the upper body remains outside the frame",
        ])
    elif "sole" in sid:
        side = "left" if "left" in sid else "right"
        parts.extend([
            f"the anatomical {side} lower leg extends toward the camera while the ankle is flexed so the complete sole faces the lens",
            "only lower calf, ankle, heel, arch, ball, and five toes remain visible",
            "the pelvis, torso, head, opposite leg, and complete body remain outside the frame",
        ])

    if regions & {"chest", "breast"}:
        parts.extend([
            "the crop adapts to the selected chest anatomy rather than resizing the anatomy to fit a fixed frame",
            "preserve the selected chest or bust base width, spacing, vertical placement, forward projection, upper fullness, lower fullness, natural weight, and complete three-dimensional volume",
            "increase camera distance or widen the regional crop as necessary; do not shrink, flatten, compress, narrow, minimize, or normalize the selected anatomy",
        ])
        if "chest_front" in sid or "breast_front" in sid:
            parts.append("include both complete lateral chest boundaries and end the lower frame below the complete lower contours with a small amount of upper abdomen")

    if "full_back" in sid:
        parts.append("the entire back surface from both shoulder blades through the lower back and waist remains available for complete full-back tattoo documentation")

    if any(token in sid for token in ("arm", "forearm", "elbow", "wrist")):
        side = "left" if "left" in sid else "right" if "right" in sid else "selected"
        parts.append(f"document only the anatomical {side} limb; the opposite arm and complete torso remain outside the regional frame")
    if any(token in sid for token in ("thigh", "knee", "shin", "calf", "ankle")):
        side = "left" if "left" in sid else "right" if "right" in sid else "selected"
        parts.append(f"document only the anatomical {side} leg region; the opposite leg and upper body remain outside the regional frame")

    if regions & {"hand"}:
        parts.append("exactly one normal hand is visible with exactly five naturally formed fingers")
    if regions & {"foot", "sole"}:
        parts.append("exactly one normal foot is visible with exactly five naturally formed toes")
    return _unique_sentences(*parts)


def _spec(
    shot_id: str,
    category: str,
    description: str,
    presentation: str,
    regions: Iterable[str],
    width: int = 1024,
    height: int = 1024,
    role: str = "BODY BLUEPRINT REFERENCE — EXCLUDE FROM FACE IDENTITY ANGLE TRAINING",
) -> dict[str, Any]:
    return {
        "shot_id": shot_id,
        "category": category,
        "description": description,
        "presentation": presentation,
        "regions": set(regions),
        "width": int(width),
        "height": int(height),
        "identity_training_role": role,
    }


# -----------------------------------------------------------------------------
# Stage 2 — Krea pre-LoRA anchors and body-only regional atlas
# -----------------------------------------------------------------------------

def _anchor_specs() -> list[dict[str, Any]]:
    return [
        _spec(
            "anchor_extreme_face_front",
            "identity_anchor",
            _sentences(
                "extreme close facial identity documentation centered on the complete face",
                "complete forehead, eyebrows, both eyes, nose, mouth, jaw, and chin remain visible with a small margin around the facial outline",
                "eye-level direct frontal view with natural 85mm facial perspective and a neutral closed-mouth expression",
            ),
            "anchor",
            {"face", "forehead", "eyebrow", "eyes", "nose", "mouth", "jaw", "chin"},
            1024,
            1024,
            "PRIMARY FACE ANCHOR CANDIDATE — APPROVE FOR STAGE 3 QWEN",
        ),
        _spec(
            "anchor_face_close_front",
            "identity_anchor",
            _sentences(
                "tight direct frontal face-close identity portrait",
                "clear margin above the complete crown; complete hairline, head sides, visible ear edges, face, and neck remain inside frame",
                "lower center ends at the base of the neck before the clavicles and the face occupies approximately seventy to eighty percent of image height",
                "eye-level 85mm portrait perspective and neutral closed-mouth expression",
            ),
            "anchor",
            {"face", "forehead", "eyebrow", "eyes", "nose", "mouth", "ears", "hair", "neck"},
            1024,
            1280,
            "PRIMARY FACE-CLOSE ANCHOR CANDIDATE — APPROVE FOR STAGE 3 QWEN",
        ),
        _spec(
            "anchor_head_shoulders_front",
            "identity_anchor",
            _sentences(
                "direct frontal head-and-shoulders support portrait",
                "complete crown, hair, face, neck, both shoulders, and modest upper-chest context remain visible",
                "eye-level 85mm portrait perspective and neutral closed-mouth expression",
            ),
            "clothed",
            {"face", "forehead", "eyebrow", "eyes", "nose", "mouth", "ears", "hair", "neck", "shoulders", "upper_torso"},
            1024,
            1280,
            "SUPPORTING IDENTITY REFERENCE — USE ONLY IF APPROVED",
        ),
    ]


def _regional_rows() -> list[tuple[str, str, set[str], int, int]]:
    rows: list[tuple[str, str, set[str], int, int]] = []

    def add(sid: str, desc: str, regions: Iterable[str], w: int = 1024, h: int = 1024):
        rows.append((sid, desc, set(regions), w, h))

    # Head-to-toe coverage without facial identity detail.
    add("hair_crown_top", "top-down documentation of the complete crown, scalp part, and hair growth pattern with the face below the frame", {"hair", "crown"})
    add("hair_nape_rear", "direct rear documentation of the lower hairstyle, rear hairline, nape, and upper neck with no face visible", {"hair", "nape", "neck"})
    add("hair_left_side", "anatomical left side-hair and temple-length documentation with all facial features outside frame", {"hair", "left_hair"})
    add("hair_right_side", "anatomical right side-hair and temple-length documentation with all facial features outside frame", {"hair", "right_hair"})

    for sid, desc in [
        ("neck_front", "front neck documentation from jaw-base boundary through collarbone boundary with the face outside frame"),
        ("neck_left_profile", "anatomical left profile of the complete neck with jaw and shoulder attachment boundaries"),
        ("neck_right_profile", "anatomical right profile of the complete neck with jaw and shoulder attachment boundaries"),
        ("neck_rear", "direct rear neck and nape documentation from rear hairline through upper trapezius"),
    ]:
        add(sid, desc, {"neck", "nape"})

    for sid, desc in [
        ("upper_torso_front", "direct front regional documentation from shoulder line through upper abdomen"),
        ("upper_torso_back", "direct rear regional documentation from both shoulders through lower ribs"),
        ("upper_torso_left_profile", "anatomical left profile of shoulder, ribcage, and upper torso"),
        ("upper_torso_right_profile", "anatomical right profile of shoulder, ribcage, and upper torso"),
        ("upper_torso_front_left", "front-left three-quarter upper-torso documentation"),
        ("upper_torso_front_right", "front-right three-quarter upper-torso documentation"),
    ]:
        add(sid, desc, {"shoulders", "upper_torso", "chest", "back", "arms"}, 1024, 1280)

    for sid, desc, regs in [
        ("chest_front", "direct frontal regional documentation of the complete chest from base of neck through both complete lower chest contours", {"chest", "breast", "upper_torso"}),
        ("chest_left_profile", "anatomical left profile of the complete chest contour with natural torso attachment", {"chest", "breast", "left_breast", "upper_torso"}),
        ("chest_right_profile", "anatomical right profile of the complete chest contour with natural torso attachment", {"chest", "breast", "right_breast", "upper_torso"}),
        ("chest_front_left", "front-left three-quarter chest documentation preserving complete volume and sternum relationship", {"chest", "breast", "left_breast", "upper_torso"}),
        ("chest_front_right", "front-right three-quarter chest documentation preserving complete volume and sternum relationship", {"chest", "breast", "right_breast", "upper_torso"}),
        ("left_chest_close", "isolated close documentation of the anatomical left chest region with minimum sternum and rib context", {"chest", "breast", "left_breast"}),
        ("right_chest_close", "isolated close documentation of the anatomical right chest region with minimum sternum and rib context", {"chest", "breast", "right_breast"}),
    ]:
        add(sid, desc, regs, 1024, 1024)

    for sid, desc, regs in [
        ("abdomen_front", "direct front abdomen documentation from lower ribs through navel and natural waist", {"abdomen", "waist", "navel"}),
        ("abdomen_left_profile", "anatomical left profile of abdomen, waist, and side torso", {"abdomen", "waist", "left_side_torso"}),
        ("abdomen_right_profile", "anatomical right profile of abdomen, waist, and side torso", {"abdomen", "waist", "right_side_torso"}),
        ("abdomen_front_left", "front-left three-quarter abdomen and waist documentation", {"abdomen", "waist", "left_side_torso"}),
        ("abdomen_front_right", "front-right three-quarter abdomen and waist documentation", {"abdomen", "waist", "right_side_torso"}),
        ("lower_back", "direct rear lower-back and waist documentation", {"back", "lower_back", "waist"}),
    ]:
        add(sid, desc, regs)

    for sid, desc in [
        ("upper_back", "direct rear upper-back and shoulder-blade documentation"),
        ("mid_back", "direct rear mid-back and spine documentation"),
        ("full_back", "direct rear documentation of the entire back from shoulder blades through lower back and waist"),
        ("full_back_rear_left", "rear-left three-quarter documentation of the entire back surface"),
        ("full_back_rear_right", "rear-right three-quarter documentation of the entire back surface"),
    ]:
        add(sid, desc, {"back", "upper_back", "lower_back", "shoulders", "waist"}, 1024, 1280)

    for sid, desc in [
        ("pelvis_front", "neutral direct front pelvis, lower abdomen, hip, and upper-thigh documentation"),
        ("pelvis_back", "neutral direct rear pelvis, buttocks, hip, and upper-thigh documentation"),
        ("pelvis_left_profile", "neutral anatomical left profile of pelvis, hip, buttock, and upper thigh"),
        ("pelvis_right_profile", "neutral anatomical right profile of pelvis, hip, buttock, and upper thigh"),
        ("pelvis_front_left", "neutral front-left three-quarter pelvis and upper-thigh documentation"),
        ("pelvis_front_right", "neutral front-right three-quarter pelvis and upper-thigh documentation"),
        ("pelvis_rear_left", "neutral rear-left three-quarter pelvis and gluteal documentation"),
        ("pelvis_rear_right", "neutral rear-right three-quarter pelvis and gluteal documentation"),
    ]:
        add(sid, desc, {"pelvis", "groin", "pubic", "hips", "buttocks", "thigh"}, 1024, 1024)

    # Arms: each side and useful surfaces.
    for side in ("left", "right"):
        for surface, desc in [
            ("upper_arm_front", "front surface of the complete upper arm from shoulder to elbow"),
            ("upper_arm_profile", "true side profile of the complete upper arm from shoulder to elbow"),
            ("upper_arm_rear", "rear surface of the complete upper arm from shoulder to elbow"),
            ("elbow_front", "front elbow with minimum upper-arm and forearm attachment context"),
            ("elbow_profile", "true side profile of the elbow joint with natural attachment context"),
            ("forearm_outer", "outer forearm surface from elbow edge through wrist"),
            ("forearm_inner", "inner forearm surface from elbow crease through wrist"),
            ("forearm_front", "direct front forearm surface from elbow edge through wrist"),
            ("forearm_rear", "direct rear forearm surface from elbow edge through wrist"),
            ("forearm_profile", "true side profile of the forearm from elbow edge through wrist"),
            ("wrist_front", "direct wrist documentation with lower forearm and hand-base attachment"),
            ("wrist_profile", "true side profile of the wrist with lower forearm and hand-base attachment"),
        ]:
            region = "upper_arm" if "upper_arm" in surface else "elbow" if "elbow" in surface else "forearm" if "forearm" in surface else "wrist"
            add(f"{side}_{surface}", f"anatomical {side} {desc}", {"arms", region, f"{side}_{region}"}, 1024, 1280 if region in {"upper_arm", "forearm"} else 1024)

        add(f"{side}_palm", f"overhead palm documentation of the anatomical {side} hand", {"hand", "palm", "wrist", f"{side}_hand", f"{side}_wrist"})
        add(f"{side}_hand_dorsal", f"overhead dorsal documentation of the anatomical {side} hand", {"hand", "wrist", f"{side}_hand", f"{side}_wrist"})
        add(f"{side}_hand_thumb_profile", f"thumb-side profile documentation of the anatomical {side} hand", {"hand", "wrist", f"{side}_hand", f"{side}_wrist"})
        add(f"{side}_hand_little_profile", f"little-finger-side profile documentation of the anatomical {side} hand", {"hand", "wrist", f"{side}_hand", f"{side}_wrist"})

    # Legs and feet: each side and useful surfaces.
    for side in ("left", "right"):
        for surface, desc in [
            ("thigh_front", "front thigh from hip crease through knee boundary"),
            ("thigh_profile", "true side profile of the thigh from hip crease through knee boundary"),
            ("thigh_rear", "rear thigh from gluteal fold through knee boundary"),
            ("knee_front", "direct front knee with minimum thigh and shin attachment context"),
            ("knee_profile", "true side profile of the knee joint with minimum attachment context"),
            ("shin_front", "direct front shin from knee boundary through ankle"),
            ("calf_rear", "direct rear calf and Achilles region from knee boundary through ankle"),
            ("lower_leg_inner", "inner side profile of lower leg from knee boundary through ankle"),
            ("lower_leg_outer", "outer side profile of lower leg from knee boundary through ankle"),
            ("ankle_front", "direct front ankle with lower shin and foot-base attachment"),
            ("ankle_profile", "true side profile of ankle with lower leg and foot attachment"),
        ]:
            region = "thigh" if "thigh" in surface else "knee" if "knee" in surface else "shin" if "shin" in surface else "calf" if "calf" in surface else "ankle" if "ankle" in surface else "calf"
            add(f"{side}_{surface}", f"anatomical {side} {desc}", {"legs", region, f"{side}_{region}"}, 1024, 1280 if region in {"thigh", "shin", "calf"} else 1024)

        add(f"{side}_foot_dorsal", f"front and dorsal documentation of the anatomical {side} foot pointed downward", {"foot", "ankle", f"{side}_foot", f"{side}_ankle"})
        add(f"{side}_foot_inner_profile", f"inner side profile documentation of the anatomical {side} foot pointed downward", {"foot", "ankle", f"{side}_foot", f"{side}_ankle"})
        add(f"{side}_foot_outer_profile", f"outer side profile documentation of the anatomical {side} foot pointed downward", {"foot", "ankle", f"{side}_foot", f"{side}_ankle"})
        add(f"{side}_sole", f"complete sole documentation of the anatomical {side} foot", {"foot", "sole", f"{side}_foot", f"{side}_sole"})

    return rows


def _regional_specs(presentation: str) -> list[dict[str, Any]]:
    category = "body_region_clothed" if presentation == "clothed" else "body_region_clinical"
    role = "BODY BLUEPRINT REFERENCE — EXCLUDE FROM FACE IDENTITY ANGLE TRAINING"
    return [
        _spec(f"{presentation}_{sid}", category, desc, presentation, regions, w, h, role)
        for sid, desc, regions, w, h in _regional_rows()
    ]


def _select_specs(plan: str) -> list[dict[str, Any]]:
    anchors = _anchor_specs()
    clothed = _regional_specs("clothed")
    clinical = _regional_specs("clinical")
    if plan == KREA_BLUEPRINT_PLANS[0]:
        return anchors
    if plan == KREA_BLUEPRINT_PLANS[1]:
        return clothed
    if plan == KREA_BLUEPRINT_PLANS[2]:
        return clinical
    if plan == KREA_BLUEPRINT_PLANS[3]:
        return clothed + clinical
    return anchors + clothed + clinical


def _build_krea_prompt(profile: dict[str, Any], spec: dict[str, Any], suffix: str) -> str:
    regions = set(spec["regions"])
    presentation = str(spec["presentation"])
    anchor = spec["category"] == "identity_anchor"

    if anchor:
        identity = _face_identity(profile)
        body_only = ""
    else:
        identity = _nonface_identity(profile)
        body_only = _body_only_authority()

    if presentation == "clinical":
        presentation_text = _clinical_body(profile, regions)
        body_scope = ""
    elif presentation == "clothed":
        presentation_text = _regional_outfit(profile, regions)
        body_scope = _clothed_body(profile, regions)
    else:
        presentation_text = _sentences(
            "a simple opaque neutral identity-documentation top may appear only where the selected anchor crop permits it",
            "clothing must not widen the crop or cover the face",
        )
        body_scope = ""

    purpose = _sentences(
        "FCC Stage 2 Krea2 pre-LoRA documentation run",
        "construct the adult subject directly from the connected Character Blueprint",
        "this is an original Krea2 blueprint render and not an edit of another image",
        spec["identity_training_role"],
    )

    return _unique_sentences(
        purpose,
        spec["description"],
        _photo_base(),
        identity,
        body_only,
        body_scope,
        presentation_text,
        _skin(profile),
        _region_marks(profile, regions, presentation),
        _special_region_authority(spec["shot_id"], regions),
        "keep every required boundary of the selected region inside the frame and keep unrelated regions outside the crop",
        _clean_phrase(suffix),
    )


class FCCKreaBlueprintDatasetDirector:
    CATEGORY = "character creation/studio"
    FUNCTION = "direct"
    DESCRIPTION = (
        "Stage 2 Krea2 pre-LoRA director. It produces three optional identity anchors plus a comprehensive body-only regional atlas from crown and nape through hands, torso, anatomy, legs, and feet in every believable direct, profile, rear, and three-quarter view. General midshots and full-body scene images are reserved for Stage 3 and Stage 4."
    )
    RETURN_TYPES = ("STRING", "INT", "STRING", "STRING", "STRING", "INT", "INT", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("krea_prompts", "seeds", "shot_ids", "categories", "filename_prefixes", "widths", "heights", "dataset_plan_json", "queue_preview", "dashboard", "progress_labels")
    OUTPUT_IS_LIST = (True, True, True, True, True, True, True, False, False, False, True)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character_blueprint": ("CHARACTER_BLUEPRINT",),
                "dataset_plan": (KREA_BLUEPRINT_PLANS, {"default": "Identity Anchors — 3"}),
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
        root = f"{str(project_name).strip() or 'FCC_Character'}/Stage_2_Krea_PreLoRA_Documentation"
        index = 0

        for spec in specs:
            for variation in range(int(variations_per_shot)):
                index += 1
                sid = f"{spec['shot_id']}_v{variation + 1:02d}"
                seed = int(starting_seed) + index - 1
                prompt = _build_krea_prompt(profile, spec, prompt_suffix)
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
                    "face_identity_source": spec["category"] == "identity_anchor",
                    "body_only": spec["category"] != "identity_anchor",
                    "prompt": prompt,
                })

        total = len(manifest)
        progress = [f"{item['index']} of {total} | {item['category']} | {item['shot_id']}" for item in manifest]
        plan_json = json.dumps({
            "schema": "FCC_KREA_STAGE2_REGIONAL_ATLAS_V254",
            "schema_version": 3,
            "character_id": profile.get("character_id", "character"),
            "plan": dataset_plan,
            "total_images": total,
            "stage_2_scope": "three optional face anchors plus body-only regional closeups; no general midshot or full-body scene matrix",
            "qwen_handoff": "Approve a Stage 2 anchor or body reference, then load that exact image into Stage 3 Qwen for additional feasible camera angles.",
            "stage_4_handoff": "Train the identity LoRA from curated Stage 2 and Stage 3 images, then use Stage 4 Krea2 for the final broad dataset.",
            "items": manifest,
        }, indent=2, ensure_ascii=False)
        preview = "\n".join(
            f"{item['index']:03d} | {item['category']} | {item['shot_id']} | {item['width']}x{item['height']}"
            for item in manifest
        )
        dashboard = "\n".join([
            "FCC STAGE 2 — KREA PRE-LORA DOCUMENTATION",
            f"Character: {profile.get('character_id', 'character')}",
            f"Plan: {dataset_plan}",
            f"Total queued images: {total}",
            "Anchors: extreme face, face-close, and head-and-shoulders candidates.",
            "Regional atlas: body-only head-to-toe close documentation with every believable direct/profile/rear/three-quarter surface.",
            "Hands and feet use isolated attached-limb geometry; regional marks are injected only when their configured body region intersects the shot.",
            "Stage 3 expands approved Stage 2 references through Qwen. Stage 4 creates final scenes and dataset diversity with the trained identity LoRA.",
        ])
        return prompts, seeds, shot_ids, categories, prefixes, widths, heights, plan_json, preview, dashboard, progress


class FCCKreaQueueItemRouter:
    CATEGORY = "character creation/studio"
    FUNCTION = "route"
    DESCRIPTION = "Routes one Stage 2 Krea regional-atlas item into the independent Stage 2 generator bundle."
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
# Stage 3 — Qwen angle expansion from an approved Stage 2 reference
# -----------------------------------------------------------------------------

_CORE_ANGLES = [
    ("front", "eye_level"),
    ("front_left", "eye_level"),
    ("left_side", "eye_level"),
    ("back_left", "eye_level"),
    ("back", "eye_level"),
    ("back_right", "eye_level"),
    ("right_side", "eye_level"),
    ("front_right", "eye_level"),
]
_FACE_CORE = [
    ("front", "eye_level"),
    ("front_left", "eye_level"),
    ("left_side", "eye_level"),
    ("front_right", "eye_level"),
    ("right_side", "eye_level"),
    ("front", "low_angle"),
    ("front", "elevated"),
    ("front", "high_angle"),
]
_FACE_EXTRA = [
    ("front_left", "low_angle"),
    ("front_left", "elevated"),
    ("front_right", "low_angle"),
    ("front_right", "elevated"),
]


def _target_config(target: str) -> tuple[list[tuple[str, str]], str, str, int, int]:
    if target == QWEN_ANGLE_TARGETS[0]:
        return list(_FACE_CORE), "close_up", "face_identity_angle", 1024, 1280
    if target == QWEN_ANGLE_TARGETS[1]:
        return list(_FACE_CORE) + list(_FACE_EXTRA), "close_up", "face_identity_angle", 1024, 1280
    if target == QWEN_ANGLE_TARGETS[2]:
        return list(_CORE_ANGLES), "medium_shot", "midshot_identity_angle", 1024, 1280
    if target == QWEN_ANGLE_TARGETS[3]:
        return list(_CORE_ANGLES), "wide_shot", "full_body_identity_angle", 1024, 1536
    return list(_CORE_ANGLES), "close_up", "regional_reference_angle", 1024, 1024


class FCCFaceAngleDatasetDirector:
    CATEGORY = "character creation/studio"
    FUNCTION = "direct"
    DESCRIPTION = (
        "Stage 3 Qwen angle-expansion director. It accepts one manually approved Stage 2 reference and emits clean camera metadata for face, midshot, full-body, or regional references. Character Blueprint prose, clothing instructions, anatomy prose, tattoos, and piercings never enter the angle encoder."
    )
    RETURN_TYPES = ("STRING", "INT", "STRING", "STRING", "STRING", "INT", "INT", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("qwen_prompts", "seeds", "shot_ids", "categories", "filename_prefixes", "widths", "heights", "dataset_plan_json", "queue_preview", "dashboard", "progress_labels")
    OUTPUT_IS_LIST = (True, True, True, True, True, True, True, False, False, False, True)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character_blueprint": ("CHARACTER_BLUEPRINT",),
                "target": (QWEN_ANGLE_TARGETS, {"default": "Approved Face Identity Angles — Extended 12"}),
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
        angles, distance, category, width, height = _target_config(str(target))
        prompts: list[str] = []
        seeds: list[int] = []
        shot_ids: list[str] = []
        categories: list[str] = []
        prefixes: list[str] = []
        widths: list[int] = []
        heights: list[int] = []
        items: list[dict[str, Any]] = []
        root = f"{str(project_name).strip() or 'FCC_Character'}/Stage_3_Qwen_Angle_Expansion/{_slug(target)}"
        index = 0

        for azimuth, elevation in angles:
            for variation in range(int(variations_per_shot)):
                index += 1
                sid = f"{category}__{azimuth}__{elevation}__{distance}_v{variation + 1:02d}"
                prompt = _sentences(
                    f"camera-only angle expansion from approved Stage 2 reference {approved_headshot_label}",
                    "preserve the same approved subject or documented region and do not redesign it",
                    _clean_phrase(prompt_suffix),
                )
                seed = int(starting_seed) + index - 1
                prefix = f"{root}/{index:04d}_{sid}"
                prompts.append(prompt)
                seeds.append(seed)
                shot_ids.append(sid)
                categories.append(category)
                prefixes.append(prefix)
                widths.append(width)
                heights.append(height)
                items.append({
                    "index": index,
                    "shot_id": sid,
                    "azimuth": azimuth,
                    "elevation": elevation,
                    "distance": distance,
                    "seed": seed,
                    "filename_prefix": prefix,
                    "reference_label": approved_headshot_label,
                })

        total = len(items)
        progress = [f"{item['index']} of {total} | {category} | {item['shot_id']}" for item in items]
        plan_json = json.dumps({
            "schema": "FCC_QWEN_STAGE3_ANGLE_EXPANSION_V254",
            "schema_version": 3,
            "character_id": profile.get("character_id", "character"),
            "target": target,
            "approved_reference": approved_headshot_label,
            "qwen_scope": "camera-angle transformation of one approved Stage 2 reference",
            "forbidden_scope": ["body blueprint prose", "clothing prose", "anatomy prose", "tattoo prose", "piercing prose", "count-lock prose"],
            "test_preset": "25 steps, CFG 4, Euler, beta57, denoise 1.0, CFGNorm 1.0, angle LoRA 0.9, blank negative",
            "manual_review": "Every image is generated for manual review; no automatic pass/reject gate is active in this version.",
            "items": items,
        }, indent=2, ensure_ascii=False)
        preview = "\n".join(
            f"{item['index']:03d} | {item['shot_id']} | {item['azimuth']} | {item['elevation']} | {item['distance']}"
            for item in items
        )
        dashboard = "\n".join([
            "FCC STAGE 3 — QWEN ANGLE EXPANSION",
            f"Character: {profile.get('character_id', 'character')}",
            f"Approved reference: {approved_headshot_label}",
            f"Target: {target}",
            f"Total queued angles: {total}",
            "ENCODER SCOPE: exact camera-angle prompt only.",
            "Use an approved Stage 2 face, midshot, full-body, or regional reference appropriate to the selected target.",
            "All results remain subject to manual approval before LoRA training.",
        ])
        return prompts, seeds, shot_ids, categories, prefixes, widths, heights, plan_json, preview, dashboard, progress
