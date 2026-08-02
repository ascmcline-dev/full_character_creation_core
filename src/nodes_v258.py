from __future__ import annotations

import copy
import json
import re
from typing import Any

from .nodes_v230 import _clean_phrase, _sentences
from .nodes_v243 import _record_visible_v243, _visible_tags_v243
from .nodes_v245 import _coverage_tags_v245
from .nodes_v246 import _rebuild_active_summary_v246
from .nodes_v253 import _image_plane_side, _piercing_geometry, _tattoo_record_prompt_v253
from .nodes_v256 import _merge_unique
from .nodes_v257 import (
    CharacterBlueprintCreatorV257,
    CharacterPromptAssemblerV257,
    CharacterShotControlV257,
    QwenDatasetQueueV257,
    SCAR_MARK_FIELD,
    _canonical_character_prompts,
    _canonicalize_chest,
    _insert_after,
    _prune_summary,
    _replace_profile_and_outputs,
)

# -----------------------------------------------------------------------------
# V2.4.18 / Studio V2.8.18
# - hard presentation-state authority: Clinical can never inherit a stored outfit
# - Daisy coverage is evaluated only while the active route is Clothed
# - crop-aware Face Close / Waist-Up camera, body, and final frame authorities
# - full-body final framing survives long garment and mark prompts
# - Front View remains square after relaxed-pose wording
# - Raw Instagram defaults to natural readable background focus, not portrait bokeh
# - Daisy preset no longer silently adds footwear and receives stronger opacity
# - structured tattoo coverage adds leg+buttock and front pelvic-bone locations
# - center-lip ring terminology avoids nasal/septum bias
# - scars/moles/beauty marks receive stronger one-location exclusivity
# -----------------------------------------------------------------------------

CORE_VERSION = "2.4.18"
STUDIO_VERSION = "2.8.18"

BACKGROUND_FOCUS_OPTIONS = [
    "Natural Snapshot Focus — No Artificial Bokeh",
    "Mostly In Focus",
    "Mild Natural Separation",
    "Strong Portrait Bokeh",
    "Custom",
]

NEW_TATTOO_LOCATIONS = [
    "Full Left Leg + Left Buttock",
    "Full Right Leg + Right Buttock",
    "Both Full Legs + Both Buttocks",
    "Left Front Pelvic Bone / Groin Line",
    "Right Front Pelvic Bone / Groin Line",
    "Both Front Pelvic Bones / Groin Lines",
]

TATTOO_LOCATION_DATA: dict[str, tuple[str, set[str]]] = {
    "Full Left Leg + Left Buttock": (
        "large continuous {description} tattoo forming one integrated full anatomical left-side lower-body coverage design across the left buttock, gluteal fold, upper thigh, knee, shin, calf, and ankle",
        {"buttocks", "left_buttock", "upper_thighs", "thighs", "knees", "shins", "calves", "ankles", "legs", "left_thigh", "left_knee", "left_leg", "left_calf"},
    ),
    "Full Right Leg + Right Buttock": (
        "large continuous {description} tattoo forming one integrated full anatomical right-side lower-body coverage design across the right buttock, gluteal fold, upper thigh, knee, shin, calf, and ankle",
        {"buttocks", "right_buttock", "upper_thighs", "thighs", "knees", "shins", "calves", "ankles", "legs", "right_thigh", "right_knee", "right_leg", "right_calf"},
    ),
    "Both Full Legs + Both Buttocks": (
        "one coordinated continuous {description} tattoo system covering both buttocks and both complete anatomical legs from the gluteal folds through both thighs, knees, shins, calves, and ankles",
        {"buttocks", "left_buttock", "right_buttock", "upper_thighs", "thighs", "knees", "shins", "calves", "ankles", "legs", "left_thigh", "left_knee", "left_leg", "left_calf", "right_thigh", "right_knee", "right_leg", "right_calf"},
    ),
    "Left Front Pelvic Bone / Groin Line": (
        "{description} tattoo following the anatomical left front pelvic-bone and inguinal groin line beside the genital region, below the lower abdomen and above the upper thigh, without crossing onto genital tissue",
        {"abdomen", "waist", "hips", "pelvis", "groin", "left_hip", "left_groin", "upper_thighs", "left_thigh"},
    ),
    "Right Front Pelvic Bone / Groin Line": (
        "{description} tattoo following the anatomical right front pelvic-bone and inguinal groin line beside the genital region, below the lower abdomen and above the upper thigh, without crossing onto genital tissue",
        {"abdomen", "waist", "hips", "pelvis", "groin", "right_hip", "right_groin", "upper_thighs", "right_thigh"},
    ),
    "Both Front Pelvic Bones / Groin Lines": (
        "one coordinated {description} tattoo design following both front pelvic-bone and inguinal groin lines beside the genital region, below the lower abdomen and above both upper thighs, without crossing onto genital tissue",
        {"abdomen", "waist", "hips", "pelvis", "groin", "left_hip", "right_hip", "left_groin", "right_groin", "upper_thighs", "left_thigh", "right_thigh"},
    ),
}

DAISY_OPACITY_AUTHORITY = _sentences(
    "the crop top is ordinary casual fashion clothing made from dense double-layer matte fabric",
    "no skin tone, nipple contour, areola detail, translucent light patch, or see-through area is visible through the fabric",
    "the top is not a sports bra, workout garment, compression garment, shaping garment, or thin undershirt",
)


def _presentation_mode(profile: dict[str, Any]) -> str:
    return str(profile.get("presentation_mode", ""))


def _is_clothed(profile: dict[str, Any]) -> bool:
    return _presentation_mode(profile) == "Clothed Character"


def _is_clinical(profile: dict[str, Any]) -> bool:
    return _presentation_mode(profile) == "Clinical Anatomy"


def _daisy_active(profile: dict[str, Any]) -> bool:
    return _is_clothed(profile) and str(profile.get("outfit_preset", "")) == "High-Hem Crop Top and Daisy Dukes"


def _canonical_presentation(profile: dict[str, Any], fallback: str = "") -> str:
    mode = _presentation_mode(profile)
    if mode == "Clinical Anatomy":
        return _clean_phrase(profile.get("active_presentation_prompt", "")) or "unclothed adult subject in neutral clinical anatomy documentation"
    if mode == "Custom Presentation":
        return _clean_phrase(profile.get("active_presentation_prompt", "")) or _clean_phrase(fallback)
    if mode == "Clothed Character":
        if _daisy_active(profile):
            return _daisy_presentation_v258(profile)
        return _clean_phrase(profile.get("active_presentation_prompt", "")) or _clean_phrase(fallback)
    return _clean_phrase(fallback)


def _daisy_presentation_v258(profile: dict[str, Any]) -> str:
    if not _daisy_active(profile):
        return ""
    components = profile.get("outfit_components") if isinstance(profile.get("outfit_components"), dict) else {}
    top = _clean_phrase(components.get("top", ""))
    bottom = _clean_phrase(components.get("bottom", ""))
    return _sentences(
        f"wearing {top}" if top else "",
        DAISY_OPACITY_AUTHORITY,
        f"wearing {bottom}" if bottom else "",
        "the selected crop top and rigid woven denim cutoff shorts remain the complete outfit; no unlisted footwear or additional garments are introduced",
        "the complete selected crop-top and rigid woven denim cutoff outfit retains the same fashion-garment construction throughout every visible view",
    )


def _coverage_v258(profile: dict[str, Any]) -> set[str]:
    # The parent coverage compiler is already presentation-aware. This wrapper
    # adds the exact Daisy short-hem correction only when Daisy is actively clothed.
    covered = set(_coverage_tags_v245(profile))
    if not _daisy_active(profile):
        return covered
    covered -= {"thighs", "legs", "knees", "shins", "calves", "ankles", "abdomen", "navel", "waist"}
    covered |= {"hips", "groin", "pubic", "genital", "buttocks", "upper_thighs"}
    return covered


def _new_tattoo_raw(location: str, description: str) -> tuple[str, set[str]]:
    template, tags = TATTOO_LOCATION_DATA[location]
    description = _clean_phrase(description) or "permanent tattoo artwork"
    return template.format(description=description), set(tags)


def _rewrite_structured_tattoo(profile: dict[str, Any], result: list[Any], kwargs: dict[str, Any]) -> None:
    if str(kwargs.get("tattoo_status", "")) != "One":
        return
    if str(kwargs.get("tattoo_input_mode", "")) != "Structured Single Tattoo":
        return
    location = str(kwargs.get("structured_tattoo_location", ""))
    if location not in TATTOO_LOCATION_DATA:
        return
    raw, tags = _new_tattoo_raw(location, str(kwargs.get("structured_tattoo_description", "")))
    records = profile.get("tattoo_records") if isinstance(profile.get("tattoo_records"), list) else []
    old_raw = ""
    if records and isinstance(records[0], dict):
        old_raw = _clean_phrase(records[0].get("raw", ""))
        records[0].update({
            "raw": raw,
            "description": _clean_phrase(kwargs.get("structured_tattoo_description", "")),
            "location": location,
            "region_tags": sorted(tags),
            "quantity": 1,
            "source": "structured",
        })
    else:
        profile["tattoo_records"] = [{
            "kind": "tattoo",
            "raw": raw,
            "description": _clean_phrase(kwargs.get("structured_tattoo_description", "")),
            "location": location,
            "region_tags": sorted(tags),
            "quantity": 1,
            "source": "structured",
        }]
    if old_raw:
        _replace_profile_and_outputs(profile, result, old_raw, raw)
    profile["tattoo_entries"] = [raw]
    profile["structured_tattoo_location"] = location
    profile["marks_prompt"] = re.sub(r"permanent tattoo:.*?(?=(?:one permanent|one healed|Tattoo count lock:|Piercing count lock:|$))", "", str(profile.get("marks_prompt", "")), flags=re.I | re.S).strip(" .")
    profile["marks_prompt"] = _merge_unique(f"permanent tattoo: {raw}", profile.get("scar_mole_beauty_mark_prompt", ""))


def _visible_tattoos_v258(profile: dict[str, Any], plan: dict[str, Any]) -> list[dict[str, Any]]:
    visible = _visible_tags_v243(plan)
    covered = _coverage_v258(profile)
    out: list[dict[str, Any]] = []
    for record in profile.get("tattoo_records", []) if isinstance(profile.get("tattoo_records"), list) else []:
        if not isinstance(record, dict):
            continue
        location = str(record.get("location", ""))
        tags = set(record.get("region_tags", []))
        extended = location in {
            "Full Left Leg Sleeve", "Full Right Leg Sleeve",
            "Full Left Leg + Left Buttock", "Full Right Leg + Right Buttock",
            "Both Full Legs + Both Buttocks",
        }
        if extended and visible & tags:
            # A short garment can hide the pelvis/upper thigh without suppressing
            # the exposed lower portions of an otherwise full-coverage tattoo.
            if any(tag not in covered for tag in tags if tag not in {"hips", "groin", "pubic", "genital", "buttocks", "upper_thighs"}):
                out.append(record)
                continue
        if _record_visible_v243(record, visible, covered, plan):
            out.append(record)
    return out


def _visible_piercings_v258(profile: dict[str, Any], plan: dict[str, Any]) -> list[dict[str, Any]]:
    visible = _visible_tags_v243(plan)
    covered = _coverage_v258(profile)
    return [
        record for record in profile.get("piercing_records", [])
        if isinstance(record, dict) and _record_visible_v243(record, visible, covered, plan)
    ] if isinstance(profile.get("piercing_records"), list) else []


def _visible_scars_v258(profile: dict[str, Any], plan: dict[str, Any]) -> list[dict[str, Any]]:
    visible = _visible_tags_v243(plan)
    covered = _coverage_v258(profile)
    return [
        record for record in profile.get("scar_mole_beauty_mark_records", [])
        if isinstance(record, dict) and _record_visible_v243(record, visible, covered, plan)
    ] if isinstance(profile.get("scar_mole_beauty_mark_records"), list) else []


def _tattoo_record_prompt_v258(record: dict[str, Any], plan: dict[str, Any] | None = None) -> str:
    location = str(record.get("location", ""))
    description = _clean_phrase(record.get("description") or record.get("raw") or "tattoo artwork")
    view = str((plan or {}).get("camera_view", ""))
    if location in {"Full Left Leg + Left Buttock", "Full Right Leg + Right Buttock"}:
        side = "left" if "Left" in location else "right"
        opposite = "right" if side == "left" else "left"
        plane = _image_plane_side(view, side)
        plane_note = f", appearing primarily on the {plane}" if plane else ""
        return _sentences(
            f"exactly one permanent continuous anatomical {side}-side lower-body tattoo forms one integrated artwork{plane_note}",
            f"the artwork clearly depicts {description}",
            f"it begins across the anatomical {side} buttock, continues through the gluteal fold and upper thigh, crosses the knee without breaking, wraps around the shin and calf, and ends at the ankle",
            "the visible design covers approximately eighty to ninety-five percent of every exposed configured surface and never collapses into isolated patches",
            f"the anatomical {opposite} buttock and {opposite} leg, both arms, torso, and every other unconfigured visible region remain tattoo-free",
            "do not mirror, swap sides, split, shrink, interrupt, duplicate, ghost, invent, or relocate the artwork",
        )
    if location == "Both Full Legs + Both Buttocks":
        return _sentences(
            "exactly one coordinated permanent lower-body tattoo system covers both buttocks and both complete anatomical legs",
            f"the coordinated artwork clearly depicts {description}",
            "the design continues from both buttocks through both gluteal folds, thighs, knees, shins, calves, and ankles without breaking",
            "both feet, arms, torso, chest, and all other unconfigured skin remain tattoo-free",
            "do not split the system into unrelated tattoos, omit one side, shrink it into patches, or relocate it",
        )
    if location in {"Left Front Pelvic Bone / Groin Line", "Right Front Pelvic Bone / Groin Line"}:
        side = "left" if location.startswith("Left") else "right"
        opposite = "right" if side == "left" else "left"
        plane = _image_plane_side(view, side)
        plane_note = f", appearing on the {plane}" if plane else ""
        return _sentences(
            f"exactly one permanent tattoo follows the anatomical {side} front pelvic-bone and inguinal groin line{plane_note}",
            f"the design clearly depicts {description}",
            "it lies below the lower abdomen, beside the groin, and above the upper thigh without crossing onto genital tissue",
            f"the anatomical {opposite} front pelvic line and every other unconfigured visible region remain tattoo-free",
            "do not mirror, duplicate, move to the centerline, place on genital anatomy, or relocate the tattoo",
        )
    if location == "Both Front Pelvic Bones / Groin Lines":
        return _sentences(
            "exactly one coordinated permanent tattoo design follows both front pelvic-bone and inguinal groin lines",
            f"the design clearly depicts {description}",
            "the paired design lies below the lower abdomen, beside the groin, and above both upper thighs without crossing onto genital tissue",
            "all other unconfigured visible skin remains tattoo-free",
            "do not move the design onto genital anatomy, duplicate it elsewhere, or relocate it",
        )
    base = _tattoo_record_prompt_v253(record, plan)
    if location in {"Full Left Leg Sleeve", "Full Right Leg Sleeve"}:
        base = _sentences(
            base,
            "the sleeve remains continuous around every visible front, side, inner, and rear surface of the configured leg and never jumps to the opposite leg or an arm",
        )
    return base


def _piercing_prompt_v258(record: dict[str, Any], plan: dict[str, Any]) -> str:
    location = str(record.get("location", "")).strip()
    low_location = location.lower()
    jewelry = str(record.get("jewelry_type", "piercing jewelry")).strip().lower()
    material = str(record.get("material", "")).strip().lower()
    quantity = int(record.get("quantity", 1) or 1)
    visibility = str(record.get("visibility", "Normal") or "Normal").lower()
    if "center lip" in low_location and ("ring" in jewelry or "hoop" in jewelry):
        return _sentences(
            f"exactly {quantity} healed permanent {material} small lower-lip hoop is present at the exact center of the lower lip",
            "one continuous circular hoop passes through living lower-lip vermilion tissue directly below the mouth opening",
            "the upper arc enters and exits the lower-lip edge while the lower arc remains visibly centered beneath the lip",
            "the nose and both nostrils remain completely bare with no jewelry",
            f"the selected visibility level is {visibility}",
            "the hoop is physically inserted through one healed lower-lip opening and is not floating, glued on, clipped on, painted on, or resting on the skin",
            "do not duplicate, relocate, or add any facial jewelry elsewhere",
        )
    # Keep the tested V2.4.17 geometry for every other location.
    from .nodes_v257 import _piercing_prompt
    return _piercing_prompt(record, plan)


def _scar_record_prompt_v258(record: dict[str, Any]) -> str:
    raw = _clean_phrase(record.get("raw", ""))
    location = _clean_phrase(record.get("location", ""))
    if not raw:
        return ""
    low = raw.lower()
    if "mole" in low or "beauty mark" in low:
        kind = "exactly one permanent natural mole or beauty mark"
    elif any(token in low for token in ("scar", "shrapnel", "gunshot", "stab")):
        kind = "exactly one permanent healed scar"
    else:
        kind = "exactly one permanent natural skin mark"
    fixed = f"only at the configured {location.lower()}" if location and location != "Unspecified" else "only at its explicitly described anatomical location"
    return _sentences(
        f"{kind} remains exactly as described: {raw}",
        fixed,
        "the mark follows the natural local skin surface and remains inside that configured anatomical region",
        "all other visible skin remains free of this mark",
        "do not duplicate, mirror, relocate, enlarge, multiply, convert into a tattoo, or remove the mark",
    )


def _upper_build_prompt(profile: dict[str, Any]) -> str:
    body_type = str(profile.get("body_type", "Average"))
    mapping = {
        "Very Slim": "a very slim visible upper-body build with narrow shoulders, slender arms, a very lean torso, and a defined natural waist",
        "Slim": "a lean visible upper-body build with slim shoulders and arms, a lean torso, and a defined natural waist",
        "Average": "an average visible upper-body build with balanced shoulders, arms, torso, and natural waist",
        "Athletic": "an athletic visible upper-body build with balanced shoulders, toned arms, an athletic torso, and a natural waist",
        "Curvy": "a curvy visible upper-body build with balanced shoulders, a shaped torso, and a clearly defined natural waist",
        "Full-Figured": "a full visible upper-body build with broad balanced shoulders, fuller arms, a full torso, and a natural waist",
        "Muscular": "a muscular visible upper-body build with developed shoulders, arms, and torso and a defined natural waist",
        "Heavyset": "a heavyset visible upper-body build with broad shoulders, full arms, a substantial torso, and a natural waist",
        "Custom / Unspecified": "the selected visible upper-body build with shoulders, arms, torso, and natural waist",
    }
    return mapping.get(body_type, mapping["Custom / Unspecified"])


def _selected_chest_text(profile: dict[str, Any]) -> str:
    mode = _presentation_mode(profile)
    if mode == "Clothed Character":
        return _clean_phrase(profile.get("active_chest_clothed_prompt", profile.get("chest_clothed_prompt", "")))
    if mode == "Custom Presentation" and str(profile.get("custom_presentation_body_detail", "")) == "Body Shape Only — No Explicit Anatomy":
        return ""
    if mode == "Custom Presentation" and str(profile.get("custom_presentation_body_detail", "")) == "Identity Only — No Body Description":
        return ""
    return _clean_phrase(profile.get("active_chest_anatomy_prompt", profile.get("chest_anatomy_prompt", "")))


def _crop_scoped_body(profile: dict[str, Any], plan: dict[str, Any], fallback: str) -> str:
    shot = str(plan.get("shot_type", plan.get("selected_shot_type", "")))
    if shot == "Face Close-Up":
        return ""
    if shot == "Waist-Up Midshot":
        return _merge_unique(
            _upper_build_prompt(profile),
            _selected_chest_text(profile),
            profile.get("active_chest_integrity_prompt", profile.get("chest_region_integrity_prompt", "")),
        )
    return _clean_phrase(fallback)


def _crop_scoped_presentation(profile: dict[str, Any], plan: dict[str, Any], fallback: str) -> str:
    shot = str(plan.get("shot_type", plan.get("selected_shot_type", "")))
    if shot == "Face Close-Up":
        # Face Close deliberately excludes clothing, chest, and anatomy prompts.
        return ""
    return _canonical_presentation(profile, fallback)


def _front_view_lock(plan: dict[str, Any]) -> str:
    if str(plan.get("camera_view", "")) != "Front View":
        return ""
    shot = str(plan.get("shot_type", ""))
    if shot not in {"Waist-Up Midshot", "Three-Quarter Body", "Full Body", "Wide Full Body / Environmental"}:
        return ""
    return _sentences(
        "final front-view authority: the sternum, navel, and pelvic centerline face directly toward the lens wherever visible",
        "both shoulders remain equally distant from the camera and neither shoulder rotates backward",
        "both front hip points remain equally visible wherever included by the crop",
        "a relaxed weight shift may change vertical balance but does not rotate the shoulders, ribcage, waist, or pelvis",
    )


def _final_frame_authority(profile: dict[str, Any], plan: dict[str, Any]) -> str:
    shot = str(plan.get("shot_type", plan.get("selected_shot_type", "")))
    if shot == "Face Close-Up":
        return _sentences(
            "FINAL FACE-CLOSE FRAME AUTHORITY",
            "the face occupies approximately seventy-eight to eighty-six percent of the image height",
            "clear image margin remains above the complete crown and all hair",
            "the lower image edge intersects the neck before either clavicle begins",
            "shoulder joints, broad shoulders, upper arms, armpits, chest, bust, garment straps, garment neckline, and torso remain completely outside the frame",
            "do not widen or lower the composition",
        )
    if shot == "Waist-Up Midshot":
        boundary = "the natural waist or visible waistband" if _is_clothed(profile) else "the natural waist and uppermost hip transition"
        return _sentences(
            "FINAL WAIST-UP FRAME AUTHORITY",
            "the complete crown and hair remain visible with clear margin above them",
            f"the lower image edge stops exactly at {boundary}",
            "the pelvis, groin, crotch, buttocks, thighs, knees, lower legs, and feet remain completely outside the image",
            "the camera does not widen downward to show lower-body anatomy",
            "chest dimensions, clothing, tattoos, piercings, and marks do not change the selected waist-up crop",
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


def _focus_prompt(value: str, custom: str) -> str:
    value = str(value or BACKGROUND_FOCUS_OPTIONS[0])
    if value == "Custom":
        return _clean_phrase(custom) or "ordinary natural camera focus"
    return {
        "Natural Snapshot Focus — No Artificial Bokeh": _sentences(
            "ordinary consumer-camera depth of field",
            "the surrounding environment remains naturally readable and recognizable rather than artificially isolated",
            "no synthetic portrait-mode cutout, creamy background blur, or exaggerated depth-map separation",
        ),
        "Mostly In Focus": "the subject and surrounding environment remain broadly in focus with ordinary snapshot clarity from foreground through background",
        "Mild Natural Separation": "only modest natural optical background softness occurs from ordinary camera distance and focus; the environment remains recognizable",
        "Strong Portrait Bokeh": "deliberate shallow portrait depth of field with strong optical background blur and clear subject separation",
    }.get(value, "ordinary natural camera focus")


def _replace_summary_line(summary: str, label: str, value: str) -> str:
    lines = str(summary or "").splitlines()
    prefix = f"{label}:"
    replaced = False
    out: list[str] = []
    for line in lines:
        if line.startswith(prefix):
            out.append(f"{prefix} {value or '[inactive]'}")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f"{prefix} {value or '[inactive]'}")
    return "\n".join(out)


def _remove_raw_focus_falloff(text: str) -> str:
    value = str(text or "")
    value = re.sub(r"\s*small focus falloff away from the main subject,?", "", value, flags=re.I)
    value = re.sub(r"\s*slight lens softness,?", " slight edge softness,", value, flags=re.I)
    value = re.sub(r"\s+", " ", value).strip(" ,")
    return value


class CharacterBlueprintCreatorV258(CharacterBlueprintCreatorV257):
    FUNCTION = "build_blueprint_v258"
    DESCRIPTION = (
        "Current Character Creator with hard presentation-state clearing, exclusive chest/groin authority, expanded structured tattoo coverage, stronger mark-location locks, and no hidden Daisy footwear."
    )

    @classmethod
    def INPUT_TYPES(cls):
        inherited = copy.deepcopy(super().INPUT_TYPES())
        required = inherited.get("required", {})
        spec = required.get("structured_tattoo_location")
        if isinstance(spec, tuple) and isinstance(spec[0], list):
            options = list(spec[0])
            insert_at = options.index("Custom / Describe in Tattoo Description") if "Custom / Describe in Tattoo Description" in options else len(options)
            for location in NEW_TATTOO_LOCATIONS:
                if location not in options:
                    options.insert(insert_at, location)
                    insert_at += 1
            required["structured_tattoo_location"] = (options, copy.deepcopy(spec[1]) if len(spec) > 1 else {"default": "Unspecified"})
        inherited["required"] = required
        return inherited

    def build_blueprint_v258(self, **kwargs):
        result = list(super().build_blueprint_v257(**kwargs))
        profile = copy.deepcopy(result[8])

        # A stored preset is allowed, but it never changes the active presentation.
        # Remove hidden Daisy footwear so the preset is exactly the listed top+shorts.
        if str(profile.get("outfit_preset", "")) == "High-Hem Crop Top and Daisy Dukes":
            components = copy.deepcopy(profile.get("outfit_components") or {})
            old_footwear = _clean_phrase(components.get("footwear", ""))
            components["footwear"] = ""
            profile["outfit_components"] = components
            if old_footwear:
                _replace_profile_and_outputs(profile, result, old_footwear, "")

        _rewrite_structured_tattoo(profile, result, kwargs)
        _canonicalize_chest(profile)
        _canonical_character_prompts(profile)

        mode = _presentation_mode(profile)
        profile["resolved_presentation_authority"] = {
            "mode": mode,
            "label": profile.get("presentation_mode_label", ""),
            "active_prompt": profile.get("active_presentation_prompt", ""),
            "garment_coverage": sorted(_coverage_v258(profile)),
            "stored_outfit_is_active": mode == "Clothed Character",
        }
        if mode != "Clothed Character":
            profile["active_garment_coverage"] = []
        else:
            profile["active_garment_coverage"] = sorted(_coverage_v258(profile))

        resolved = str(profile.get("resolved_chest_anatomy", ""))
        summary = _prune_summary(profile.get("presentation_summary", ""), resolved)
        summary = summary.replace("V2.4.17", CORE_VERSION)
        summary += (
            "\nPresentation V2.4.18: Clinical Anatomy hard-clears every stored top, bottom, footwear, preset, and garment-coverage field; only Clothed activates outfit controls."
            "\nTattoo V2.4.18: structured locations include full leg+buttock coverage and front pelvic-bone/groin-line placements."
            "\nDaisy V2.4.18: the preset contains only the selected crop top and rigid denim cutoffs; footwear is not silently added."
        )
        profile["presentation_summary"] = summary
        profile["schema"] = "CHARACTER_BLUEPRINT_V258"
        profile["schema_version"] = 28
        profile["fcc_core_version"] = CORE_VERSION
        profile["fcc_studio_version"] = STUDIO_VERSION

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


class CharacterShotControlV258(CharacterShotControlV257):
    FUNCTION = "build_shot_plan_v258"
    DESCRIPTION = (
        "Current Shot Control with crop-aware Face Close and Waist-Up framing, square Front View pose locks, full-body final framing support, and selectable natural background focus."
    )

    @classmethod
    def INPUT_TYPES(cls):
        inherited = copy.deepcopy(super().INPUT_TYPES())
        required = inherited.get("required", {})
        required = _insert_after(required, "photo_style", [
            ("background_focus", (BACKGROUND_FOCUS_OPTIONS, {"default": BACKGROUND_FOCUS_OPTIONS[0]})),
            ("custom_background_focus", ("STRING", {"default": "", "multiline": True})),
        ])
        inherited["required"] = required
        return inherited

    def build_shot_plan_v258(self, **kwargs):
        background_focus = str(kwargs.pop("background_focus", BACKGROUND_FOCUS_OPTIONS[0]))
        custom_background_focus = str(kwargs.pop("custom_background_focus", ""))
        result = list(super().build_shot_plan_v257(**kwargs))
        plan = copy.deepcopy(result[0])
        shot = str(plan.get("shot_type", kwargs.get("shot_type", "")))
        view = str(plan.get("camera_view", kwargs.get("camera_view", "")))

        plan["photo_style_prompt"] = _remove_raw_focus_falloff(plan.get("photo_style_prompt", ""))
        plan["environment_prompt"] = _remove_raw_focus_falloff(plan.get("environment_prompt", result[6] if len(result) > 6 else ""))
        focus_text = _focus_prompt(background_focus, custom_background_focus)
        plan["background_focus"] = background_focus
        plan["custom_background_focus"] = custom_background_focus
        plan["background_focus_prompt"] = focus_text
        plan["environment_prompt"] = _sentences(plan.get("environment_prompt", ""), focus_text)

        if shot == "Face Close-Up":
            plan["framing_prompt"] = _sentences(
                "tight facial documentation close-up with a small clear margin above the complete crown",
                "the complete crown, complete hairline, both sides of the head, visible ear edges, complete face, and chin remain inside the frame",
                "the face occupies approximately seventy-eight to eighty-six percent of the image height",
                "the lower edge intersects the neck before either clavicle begins",
                "shoulder joints, broad shoulders, upper arms, armpits, chest, bust, garment straps, neckline, and torso remain outside the frame",
            )
            plan["crop_authority_prompt"] = "do not widen or lower the face-close composition to show chest, shoulders, clothing, pose, or full hair length"
            plan["camera_prompt"] = _sentences(
                "front-facing camera centered on the facial midline" if view == "Front View" else plan.get("camera_prompt", ""),
                "eye-level camera aligned with the eyes",
                "rectilinear 85mm portrait-lens perspective with natural facial proportions",
            )
            plan["recommended_width"] = 1024
            plan["recommended_height"] = 1024
            plan["aspect_ratio"] = "Square 1:1 — Face Close"
            plan["resolution_summary"] = "1024 × 1024 | Square 1:1 — Face Close"
        elif shot == "Waist-Up Midshot":
            plan["framing_prompt"] = _sentences(
                "complete-head waist-up composition with clear margin above the complete crown",
                "the complete head, hair, neck, shoulders, torso, arms, and natural waist remain inside the frame",
                "the lower edge stops at the natural waist or visible waistband and remains above the pelvis",
                "the pelvis, groin, crotch, buttocks, thighs, knees, lower legs, and feet remain outside the image",
            )
            plan["crop_authority_prompt"] = "camera distance preserves the complete crown and waist boundary without widening downward into a three-quarter-body crop"
            if view == "Front View":
                plan["camera_prompt"] = _sentences(
                    "strict straight-on front view of the visible upper body",
                    "the face, shoulders, chest, torso, arms, and natural waist align toward the camera",
                    "the pelvis and knees are outside the crop and are not used as camera landmarks",
                    "camera centered at upper-torso height with a level horizon",
                    "rectilinear 50mm normal-lens perspective",
                )
        if view == "Front View" and shot in {"Waist-Up Midshot", "Three-Quarter Body", "Full Body", "Wide Full Body / Environmental"}:
            plan["pose_prompt"] = _sentences(plan.get("pose_prompt", ""), _front_view_lock(plan))

        plan["schema"] = "FCC_SHOT_PLAN_V258"
        plan["schema_version"] = 28
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

        summary = str(plan.get("active_settings_summary", "")).replace("V2.4.17", CORE_VERSION)
        summary = _replace_summary_line(summary, "Framing", plan.get("framing_prompt", ""))
        summary = _replace_summary_line(summary, "Camera", plan.get("camera_prompt", ""))
        summary = _replace_summary_line(summary, "Pose", plan.get("pose_prompt", ""))
        summary = _replace_summary_line(summary, "Environment", plan.get("environment_prompt", ""))
        summary = _replace_summary_line(summary, "Background focus", background_focus)
        if shot == "Face Close-Up":
            summary = _replace_summary_line(summary, "Aspect", "Square 1:1 — Face Close (1024 × 1024)")
            summary += "\nV2.4.18 Face Close: lower edge stops on the neck before the clavicles; broad shoulders and chest remain outside."
        if shot == "Waist-Up Midshot":
            summary += "\nV2.4.18 Waist-Up: the lower boundary stops at the natural waist; pelvis, groin, thighs, knees, and legs remain outside."
        if view == "Front View" and shot in {"Waist-Up Midshot", "Three-Quarter Body", "Full Body", "Wide Full Body / Environmental"}:
            summary += "\nV2.4.18 Front View: relaxed weight shift cannot rotate shoulders, torso, or pelvis away from the lens."
        summary += f"\nV2.4.18 Background Focus: {background_focus}."
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


class CharacterPromptAssemblerV258(CharacterPromptAssemblerV257):
    FUNCTION = "assemble_prompt_v258"
    DESCRIPTION = (
        "Current prompt compiler with hard presentation-state clearing, crop-scoped body authority, final frame locks, corrected tattoo/mark placement, and natural snapshot focus routing."
    )

    def assemble_prompt_v258(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        result = list(super().assemble_prompt_v257(
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

        tattoos = _visible_tattoos_v258(profile, plan)
        tattoo_text = _sentences(*(_tattoo_record_prompt_v258(record, plan) for record in tattoos))
        piercings = _visible_piercings_v258(profile, plan)
        piercing_text = _sentences(*(_piercing_prompt_v258(record, plan) for record in piercings if isinstance(record, dict)))
        scars = _visible_scars_v258(profile, plan)
        scar_text = _sentences(*(_scar_record_prompt_v258(record) for record in scars))
        marks = _merge_unique(tattoo_text, piercing_text, scar_text)

        shot = _clean_phrase(plan.get("final_shot_prompt", sections.get("shot_scene", result[2] or "")))
        purpose = str(sections.get("purpose", "A realistic camera photograph"))
        character = str(sections.get("primary_character", result[19] or ""))
        tan = str(sections.get("visible_tan_skin_variation", ""))
        final_authority = _merge_unique(_front_view_lock(plan), _final_frame_authority(profile, plan))

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
            "shot_scene": shot,
            "final_frame_authority": final_authority,
            "final_prompt": final_prompt,
            "routing_mode": str(sections.get("routing_mode", "")) + "+v258_hard_state_and_crop_scope",
            "resolved_presentation_mode": _presentation_mode(profile),
        })

        result[2] = shot
        result[3] = presentation
        result[4] = marks
        result[13] = final_prompt
        result[16] = presentation
        if str(generation_purpose).startswith("Krea"):
            result[0] = final_prompt
        else:
            result[1] = final_prompt

        notes = str(result[10] or "").replace("V2.4.17", CORE_VERSION)
        notes += (
            "\nStage 0 V2.4.18: Clinical Anatomy hard-clears stored outfits; Face Close and Waist-Up use crop-scoped body authority; final frame locks are appended after clothing and marks."
            "\nMarks V2.4.18: structured tattoos and scars/moles use exact region exclusivity; center-lip rings use lower-lip terminology without nasal jewelry bias."
        )
        result[10] = notes
        result[18] = json.dumps(sections, indent=2, ensure_ascii=False)
        result[12] = _rebuild_active_summary_v246(profile, plan, sections, notes)
        return tuple(result)


class QwenDatasetQueueV258(QwenDatasetQueueV257):
    DESCRIPTION = (
        "Compatibility queue registered to V2.4.18. Stage 3 remains deferred until the controlled Stage 0 and Stage 2 validation sets pass."
    )
