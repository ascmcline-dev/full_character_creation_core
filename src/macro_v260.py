from __future__ import annotations

import re
from typing import Any

from .nodes_v230 import _clean_phrase, _sentences
from .nodes_v256 import _merge_unique
from .nodes_v259 import _piercing_prompt_v259, _scar_prompt_v259, _tattoo_prompt_v259


def _unique(*parts: Any) -> str:
    seen: set[str] = set()
    out: list[str] = []
    for part in parts:
        text = _clean_phrase(part)
        if not text:
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            sentence = sentence.strip(" .")
            if not sentence:
                continue
            key = re.sub(r"\s+", " ", sentence.lower())
            if key in seen:
                continue
            seen.add(key)
            out.append(sentence)
    return ". ".join(out) + ("." if out else "")


def _focus_value(plan: dict[str, Any]) -> str:
    value = _clean_phrase(plan.get("focus_region", ""))
    if value:
        return value
    selected = _clean_phrase(plan.get("selected_extreme_closeup_focus", ""))
    custom = _clean_phrase(plan.get("custom_extreme_focus", ""))
    return custom if selected == "Custom" and custom else (selected or "Selected Detail")


def _focus_tags(focus: str) -> set[str]:
    f = focus.lower()
    if "left nipple" in f:
        return {"chest", "breast", "pectoral", "left_breast", "left_pectoral", "left_nipple", "areola"}
    if "right nipple" in f:
        return {"chest", "breast", "pectoral", "right_breast", "right_pectoral", "right_nipple", "areola"}
    if "both nipples" in f or "chest center" in f:
        return {"chest", "breast", "pectoral", "sternum", "nipple", "areola"}
    if "navel" in f:
        return {"abdomen", "waist", "navel"}
    if "pubic mons" in f:
        return {"pelvis", "groin", "pubic", "suprapubic", "female_genital", "male_genital"}
    if "external genital" in f or "genital anatomy" in f:
        return {"pelvis", "groin", "pubic", "suprapubic", "male_genital", "female_genital", "custom_groin", "perineal"}
    if "left hand" in f:
        return {"hand", "left_hand", "wrist", "fingers", "palm"}
    if "right hand" in f:
        return {"hand", "right_hand", "wrist", "fingers", "palm"}
    if "left foot" in f:
        return {"foot", "left_foot", "ankle", "sole", "heel", "toes"}
    if "right foot" in f:
        return {"foot", "right_foot", "ankle", "sole", "heel", "toes"}
    if "left eye" in f:
        return {"face", "eye", "eyes", "left_eye", "left_eyebrow", "left_temple"}
    if "right eye" in f:
        return {"face", "eye", "eyes", "right_eye", "right_eyebrow", "right_temple"}
    if "both eyes" in f:
        return {"face", "eye", "eyes", "eyebrow", "forehead", "nose"}
    if "left ear" in f:
        return {"face", "ear", "ears", "left_ear"}
    if "right ear" in f:
        return {"face", "ear", "ears", "right_ear"}
    if "nose" in f or "septum" in f:
        return {"face", "nose", "nostril", "septum"}
    if "mouth" in f or "lip" in f:
        return {"face", "mouth", "lip", "lips", "chin"}
    if "forehead" in f or "hairline" in f:
        return {"face", "forehead", "hairline", "temple", "eyebrow"}
    if "profile" in f or "complete face" in f or "jaw" in f or "chin" in f:
        return {"face", "eye", "eyes", "nose", "mouth", "lip", "lips", "ear", "ears", "jaw", "chin", "forehead", "hairline"}
    return {token for token in re.split(r"[^a-z0-9]+", f) if len(token) > 3}


def _record_intersects(record: dict[str, Any], tags: set[str]) -> bool:
    record_tags = {str(x).lower() for x in record.get("region_tags", [])}
    if record_tags & tags:
        return True
    raw = str(record.get("raw", "")).lower()
    return any(tag.replace("_", " ") in raw for tag in tags if len(tag) > 3)


def _local_marks(profile: dict[str, Any], tags: set[str]) -> tuple[str, dict[str, list[dict[str, Any]]]]:
    tattoos = [r for r in profile.get("tattoo_records", []) if isinstance(r, dict) and _record_intersects(r, tags)]
    scars = [r for r in profile.get("scar_mole_beauty_mark_records", []) if isinstance(r, dict) and _record_intersects(r, tags)]
    piercings = [r for r in profile.get("piercing_records", []) if isinstance(r, dict) and _record_intersects(r, tags)]
    if not tattoos and not scars and not piercings:
        return "the documented local skin is naturally unmarked and uninterrupted", {
            "tattoos": [], "scars": [], "piercings": []
        }
    text = _unique(
        *(_tattoo_prompt_v259(r, {}) for r in tattoos),
        *(_scar_prompt_v259(r) for r in scars),
        *(_piercing_prompt_v259(r, {}) for r in piercings),
        "only these configured local permanent details are present inside the macro field",
    )
    return text, {"tattoos": tattoos, "scars": scars, "piercings": piercings}


def _skin_line(profile: dict[str, Any]) -> str:
    tone = _clean_phrase(profile.get("skin_tone", ""))
    complexion = _clean_phrase(profile.get("complexion", ""))
    return _unique(
        f"the local tissue retains the selected {tone.lower()} underlying skin tone" if tone else "the local tissue retains the selected underlying complexion",
        complexion and f"local complexion: {complexion.lower()}",
        "lighting changes highlights and micro-shadows only and does not recolor the tissue",
    )


def _chest_authority(profile: dict[str, Any], focus: str) -> str:
    f = focus.lower()
    selected = _clean_phrase(profile.get("chest_anatomy_prompt", ""))
    integrity = _clean_phrase(profile.get("active_chest_integrity_prompt", profile.get("chest_region_integrity_prompt", "")))
    if "left nipple" in f:
        target = "exactly one anatomical-left nipple and its complete surrounding areola, with only a narrow ring of adjacent local chest tissue"
    elif "right nipple" in f:
        target = "exactly one anatomical-right nipple and its complete surrounding areola, with only a narrow ring of adjacent local chest tissue"
    elif "both nipples" in f:
        target = "the paired nipple-and-areola complexes and the intervening sternum only, symmetrically documented"
    else:
        target = "the named local chest surface only"
    return _unique(target, selected, integrity, "the canonical chest category and local contour remain unchanged at macro scale")


def _groin_authority(profile: dict[str, Any], focus: str) -> str:
    resolved = _clean_phrase(profile.get("resolved_groin_anatomy", ""))
    anatomy = _clean_phrase(profile.get("groin_anatomy_prompt", ""))
    pubic = _clean_phrase(profile.get("pubic_hair_prompt", ""))
    integrity = _clean_phrase(profile.get("sex_anatomy_integrity_prompt", profile.get("groin_region_integrity_prompt", "")))
    return _unique(
        resolved and f"resolved local anatomy: {resolved}",
        anatomy,
        pubic,
        integrity,
        "the selected external anatomy is documented at native macro scale with only immediate attachment tissue",
    )


def _face_authority(profile: dict[str, Any], focus: str) -> str:
    f = focus.lower()
    base = _unique(
        profile.get("gender_authority_prompt", ""),
        profile.get("age_range", "") and f"age range {profile.get('age_range')}",
        _skin_line(profile),
    )
    if "eye" in f:
        return _unique(base, profile.get("eye_color", "") and f"selected iris color: {profile.get('eye_color')}", profile.get("eye_shape", "") and f"selected eye shape: {profile.get('eye_shape')}", profile.get("eyebrow_shape", "") and f"selected eyebrow shape: {profile.get('eyebrow_shape')}")
    if "nose" in f:
        return _unique(base, profile.get("nose_shape", "") and f"selected nose shape: {profile.get('nose_shape')}")
    if "mouth" in f or "lip" in f:
        return _unique(base, profile.get("lip_shape", "") and f"selected lip shape: {profile.get('lip_shape')}")
    return _unique(base, profile.get("identity_detail_prompt", ""))


def _target_text(focus: str) -> tuple[str, str]:
    f = focus.lower()
    if "left nipple" in f:
        return "exactly one anatomical-left nipple and its complete areola", "camera optical axis perpendicular to the local left chest surface"
    if "right nipple" in f:
        return "exactly one anatomical-right nipple and its complete areola", "camera optical axis perpendicular to the local right chest surface"
    if "both nipples" in f:
        return "both nipple-and-areola complexes with the sternum between them", "strict centered frontal chest-surface view"
    if "navel" in f:
        return "the existing navel and its immediate abdominal skin transition", "camera optical axis perpendicular to the abdominal surface"
    if "pubic mons" in f:
        return "the selected pubic mound or suprapubic surface and its immediate skin transition", "strict direct frontal surface-normal view"
    if "external genital" in f or "genital anatomy" in f:
        return "the configured adult external anatomy and only its immediate attachment tissue", "anatomically appropriate direct macro view of the named external surface"
    if "left hand" in f:
        return "the anatomical-left hand surface named by the selection", "surface-normal macro view of the left hand"
    if "right hand" in f:
        return "the anatomical-right hand surface named by the selection", "surface-normal macro view of the right hand"
    if "left foot" in f:
        return "the anatomical-left foot surface named by the selection", "surface-normal macro view of the left foot"
    if "right foot" in f:
        return "the anatomical-right foot surface named by the selection", "surface-normal macro view of the right foot"
    if "left eye" in f:
        return "the anatomical-left eye, eyelids, eyelashes, eyebrow, and immediate surrounding skin", "camera centered perpendicular to the left eye surface"
    if "right eye" in f:
        return "the anatomical-right eye, eyelids, eyelashes, eyebrow, and immediate surrounding skin", "camera centered perpendicular to the right eye surface"
    return focus.lower(), f"surface-normal macro view centered only on {focus.lower()}"


def _local_authority(profile: dict[str, Any], focus: str) -> str:
    f = focus.lower()
    if any(x in f for x in ("nipple", "areola", "chest center")):
        return _chest_authority(profile, focus)
    if any(x in f for x in ("pubic mons", "external genital", "genital anatomy")):
        return _groin_authority(profile, focus)
    if any(x in f for x in ("eye", "nose", "mouth", "lip", "forehead", "hairline", "ear", "profile", "jaw", "chin", "complete face")):
        return _face_authority(profile, focus)
    return _skin_line(profile)


def build_stage0_macro(profile: dict[str, Any], plan: dict[str, Any], purpose: str, trigger_word: str = "", custom_prefix: str = "", custom_suffix: str = "") -> dict[str, Any]:
    focus = _focus_value(plan)
    target, camera = _target_text(focus)
    tags = _focus_tags(focus)
    marks_text, records = _local_marks(profile, tags)
    local_authority = _local_authority(profile, focus)
    crop = _unique(
        "native clinical macro photograph captured at source magnification rather than cropped from a wider body photograph",
        f"single target: {target}",
        "the named target fills approximately eighty-eight to ninety-five percent of the square frame",
        "only the minimum immediately adjacent tissue needed to prove natural attachment is visible",
    )
    camera_text = _unique(camera, "rectilinear 105mm macro-lens perspective", "sufficient depth of field keeps the complete target surface readable")
    surface = _unique(
        "medical-grade lifelike surface documentation",
        "visible pores, fine skin texture, vellus hair where naturally present, pigmentation variation, creases, folds, contours, edge transitions, and realistic micro-shadows",
        "natural small asymmetries remain visible without glamour retouching or plastic smoothing",
    )
    environment = _unique(
        "even neutral clinical illumination across the complete target",
        "a seamless matte neutral-gray field may appear only at the narrow outer edge beyond the local tissue",
        "no room context is needed for this local macro record",
    )
    prompt = _sentences(trigger_word, custom_prefix, purpose, crop, camera_text, local_authority, surface, marks_text, environment, custom_suffix)
    return {
        "focus": focus,
        "crop": crop,
        "camera": camera_text,
        "local_authority": local_authority,
        "surface": surface,
        "marks": marks_text,
        "environment": environment,
        "prompt": prompt,
        "records": records,
        "tags": sorted(tags),
    }


def stage2_target_from_spec(spec: dict[str, Any]) -> tuple[str, str, str]:
    sid = str(spec.get("shot_id", "")).lower()
    if "left_nipple" in sid:
        return "exactly one anatomical-left nipple and its complete areola", "camera perpendicular to the local anatomical-left chest surface", "chest"
    if "right_nipple" in sid:
        return "exactly one anatomical-right nipple and its complete areola", "camera perpendicular to the local anatomical-right chest surface", "chest"
    if "sternum" in sid or "chest_center" in sid:
        return "the named sternum and medial chest transition", "strict centered frontal surface-normal view", "chest"
    if "lower_bust" in sid or "lower_pectoral" in sid:
        return "the named lower chest contour and immediate fold or boundary", "surface-normal oblique view aligned to the named lower contour", "chest"
    if "navel" in sid:
        return "the existing navel and immediate abdominal skin transition", "camera perpendicular to the abdominal surface", "skin"
    if "palm" in sid:
        side = "left" if "left" in sid else "right"
        return f"the anatomical-{side} palm, palm lines, finger bases, and lower wrist attachment", "camera perpendicular to the palmar surface", "skin"
    if "fingertip" in sid:
        side = "left" if "left" in sid else "right"
        return f"the anatomical-{side} distal fingertips and natural fingernails", "direct macro view perpendicular to the distal finger and nail surfaces", "skin"
    if "sole" in sid:
        side = "left" if "left" in sid else "right"
        return f"the anatomical-{side} plantar sole surface from heel pad through toe pads", "camera perpendicular to the plantar surface", "skin"
    if "heel" in sid:
        side = "left" if "left" in sid else "right"
        return f"the anatomical-{side} posterior heel and Achilles-to-heel transition", "direct rear surface-normal heel view", "skin"
    if "gluteal_fold" in sid:
        side = "left" if "left" in sid else "right"
        return f"the anatomical-{side} posterior gluteal fold with buttock surface above and posterior upper-thigh attachment below", "strict direct rear lens-level view of the named fold", "gluteal"
    if any(x in sid for x in ("genital", "groin", "pubic", "suprapubic", "scrotal", "perineal")):
        return str(spec.get("description", "configured external anatomy detail")), str(spec.get("camera_view", "anatomically appropriate direct macro view")), "groin"
    return str(spec.get("description", "selected local anatomical detail")), str(spec.get("camera_view", "surface-normal macro view")), "skin"


def build_stage2_macro(profile: dict[str, Any], spec: dict[str, Any], suffix: str = "") -> tuple[str, dict[str, Any]]:
    target, camera, authority_kind = stage2_target_from_spec(spec)
    regions = {str(x).lower() for x in spec.get("regions", set())}
    marks_text, records = _local_marks(profile, regions)
    if authority_kind == "chest":
        local_authority = _chest_authority(profile, target)
    elif authority_kind == "groin":
        local_authority = _groin_authority(profile, target)
    elif authority_kind == "gluteal":
        local_authority = _unique(_skin_line(profile), profile.get("gluteal_build", "") and f"configured gluteal build: {profile.get('gluteal_build')}")
    else:
        local_authority = _skin_line(profile)
    crop = _unique(
        "native clinical macro photograph captured directly at source magnification rather than cropped from a larger body photograph",
        f"single target: {target}",
        "the named target fills approximately ninety to ninety-five percent of the square frame",
        "only the minimum immediately adjacent tissue needed to prove natural attachment and orientation is visible",
    )
    camera_text = _unique(camera, "rectilinear 105mm macro-lens perspective", "sufficient depth of field keeps the full target surface readable")
    surface = _unique(
        "lifelike medical surface documentation",
        "pores, fine skin texture, vellus hair where naturally present, pigmentation variation, creases, folds, contours, edge transitions, and realistic micro-shadows remain visible",
        "natural small asymmetries are preserved without glamour retouching or plastic smoothing",
    )
    environment = _unique(
        "even neutral clinical illumination across the complete target",
        "a seamless matte neutral-gray field may appear only at the narrow outer edge beyond the local tissue",
    )
    prompt = _sentences(
        "FCC Stage 2 native extreme clinical macro record",
        crop,
        camera_text,
        local_authority,
        surface,
        marks_text,
        environment,
        "Krea structural draft for manual review; exact same-person identity may use the approved Qwen reference-edit handoff",
        _clean_phrase(suffix),
    )
    metadata = {
        "macro_compiler": "FCC_NATIVE_CLINICAL_MACRO_V260",
        "native_macro": True,
        "target": target,
        "camera": camera_text,
        "local_authority_kind": authority_kind,
        "local_mark_records": records,
        "regions": sorted(regions),
    }
    return prompt, metadata
