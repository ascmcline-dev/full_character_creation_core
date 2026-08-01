from __future__ import annotations

import copy
import json
import re
from typing import Any

from .nodes import (
    FCCDatasetDirector,
    FCCQueueItemRouter,
    LENS_PROMPTS_V2,
    _slug,
)
from .nodes_v230 import _clean_phrase, _focus_value_v231, _is_extreme_closeup_v231, _sentences
from .nodes_v240 import FACE_TAGS
from .nodes_v241 import (
    _camera_view,
    _identity_for_view,
    _is_direct_back,
    _is_rear_orientation,
    _location_from_text_v241,
    _macro_sections_v241,
    _parse_tattoo_record_v241,
    _piercing_phrase_v241,
    _record_matches_extreme_v241,
    _structured_tattoo_text,
    _tattoo_phrase_v241,
)
from .nodes_v243 import (
    AUTO_ASPECT,
    ASPECT_RATIOS_V243,
    REGIONAL_CROPS,
    WIDE_FULL_BODY,
    _is_regional,
    _record_visible_v243,
    _region_identity_v243,
    _regional_body_v243,
    _regional_group,
    _regional_presentation_v243,
    _visible_body_and_presentation_v243,
    _visible_tags_v243,
)
from .nodes_v244 import (
    AUTO_LENS,
    HORIZONTAL_POSES_V244,
    LENSES_V244,
    NATURAL_SIDE_LYING,
    PHOTO_STYLES_V244,
    CharacterBlueprintCreatorV244,
    CharacterPromptAssemblerV244,
    CharacterShotControlV244,
    QwenDatasetQueueV244,
    _body_crop_prompt_v244,
    _resolve_aspect_v244,
    _style_prompt_v244,
    _style_purpose_v244,
    _tan_parts_v244,
)

# -----------------------------------------------------------------------------
# V2.4.5 / Studio V2.8.5
# - reliable structured tattoo records and garment-aware tattoo visibility
# - dedicated hair-highlight field retained across all visible identity routes
# - compact reclining language for close portraits and corrected auto lens
# - stronger amateur/social-photo texture and off-center selfie composition
# - clearer outfit/piercing UI behavior without duplicating input sources
# - improved two-hand heart gesture plus all-fours and extended puppy poses
# - visible donation / Discord buttons in the Character Creator UI
# -----------------------------------------------------------------------------

ALL_FOURS = "Doggy-Style / All Fours — Hands and Knees"
EXTENDED_PUPPY = "Extended Puppy Pose"
FLOOR_POSES_V245 = set(HORIZONTAL_POSES_V244) | {ALL_FOURS, EXTENDED_PUPPY}

POSES_V245 = [p for p in CharacterShotControlV244.INPUT_TYPES()["required"]["pose"][0] if p != "Custom"]
for _pose in (ALL_FOURS, EXTENDED_PUPPY):
    if _pose not in POSES_V245:
        POSES_V245.append(_pose)
POSES_V245.append("Custom")

FACE_SCALE_SHOTS = {"Face Close-Up", "Head and Shoulders", "Chest-Up"}
BODY_SCALE_SHOTS = {"Waist-Up Midshot", "Three-Quarter Body", "Full Body", WIDE_FULL_BODY}

PHOTO_STYLE_PROMPTS_V245 = dict({style: _style_prompt_v244(style) for style in PHOTO_STYLES_V244})
PHOTO_STYLE_PROMPTS_V245.update({
    "Raw Instagram / Unfiltered Social Snapshot": (
        "raw amateur social-media photograph with imperfect handheld composition, visible fine ISO grain, slight edge softness, "
        "small focus falloff away from the main subject, mild JPEG compression, uneven automatic white balance, occasional clipped window highlights, "
        "modest phone-camera dynamic range, subtle micro-motion softness in hair or hands, natural pores, and an unpolished everyday finish"
    ),
    "Casual Cellphone Snapshot": (
        "casual smartphone snapshot with believable automatic exposure and white balance, mild sensor noise, slight lens softness, "
        "minor motion blur, imperfect crop, compressed social-media texture, natural skin detail, and ordinary non-commercial phone processing"
    ),
    "Natural Arm's-Length Selfie": (
        "natural front-camera selfie with the phone held slightly above and to one side rather than perfectly centered, one shoulder subtly closer to the lens, "
        "a mild torso turn caused by the extended arm, slightly imperfect crop, believable front-camera perspective, mild phone sharpening, visible fine sensor grain, "
        "uneven auto white balance, and an unretouched personal social-media appearance"
    ),
    "Friend-Taken Vacation Photo": (
        "spontaneous vacation photograph taken by a friend with relaxed off-center composition, slight timing imperfection, mild motion softness, "
        "ordinary consumer-camera exposure, natural environmental color cast, modest compression, and an authentic non-commercial travel snapshot feeling"
    ),
})


def _insert_after(mapping: dict, key: str, additions: list[tuple[str, Any]]) -> dict:
    out: dict = {}
    for name, spec in mapping.items():
        out[name] = spec
        if name == key:
            for add_name, add_spec in additions:
                out[add_name] = add_spec
    return out


def _hair_with_highlights(base: str, highlights: str) -> str:
    base = _clean_phrase(base)
    highlights = _clean_phrase(highlights)
    if not highlights:
        return base
    if "highlight" in highlights.lower() or "streak" in highlights.lower() or "underlayer" in highlights.lower() or "money piece" in highlights.lower():
        accent = highlights
    else:
        accent = f"{highlights} highlights"
    return _sentences(
        base,
        f"clearly visible {accent} distributed through the front, sides, and visible lengths of the hair",
    )


def _replace_profile_phrase(profile: dict, old: str, new: str) -> None:
    if not old or old == new:
        return
    for key in (
        "identity_detail_prompt", "face_identity", "active_character_prompt",
        "full_profile_prompt", "clothed_character_prompt", "clinical_character_prompt",
    ):
        value = profile.get(key)
        if isinstance(value, str):
            profile[key] = value.replace(old, new)


def _structured_tattoo_raw(location: str, description: str) -> str:
    location = _clean_phrase(location)
    description = _clean_phrase(description) or "permanent tattoo design"
    loc = location.lower()
    if location == "Full Back":
        return f"large {description} tattoo covering the full back from the shoulder blades through the lower back"
    if location == "Full Left Arm Sleeve":
        return f"large continuous {description} tattoo forming a full anatomical left arm sleeve from shoulder cap through upper arm, elbow, and forearm to the wrist"
    if location == "Full Right Arm Sleeve":
        return f"large continuous {description} tattoo forming a full anatomical right arm sleeve from shoulder cap through upper arm, elbow, and forearm to the wrist"
    if location == "Full Left Leg Sleeve":
        return f"large continuous {description} tattoo forming a full anatomical left leg sleeve from upper thigh through knee, shin, and calf to the ankle"
    if location == "Full Right Leg Sleeve":
        return f"large continuous {description} tattoo forming a full anatomical right leg sleeve from upper thigh through knee, shin, and calf to the ankle"
    if location == "Upper Back":
        return f"{description} tattoo centered across the upper back between the shoulder blades"
    if location == "Lower Back / Tramp Stamp":
        return f"{description} tattoo centered on the lower back immediately above the waistband"
    if location == "Full Abdomen":
        return f"large {description} tattoo covering the full abdomen from just below the chest to the lower waist"
    if location == "Cleavage / Center Chest":
        return f"{description} tattoo centered vertically on the sternum between the breasts"
    if location and location not in {"Unspecified", "Custom / Describe in Tattoo Description"}:
        return f"{description} tattoo on the {loc}"
    return description


def _tattoo_records_v245(kwargs: dict, fallback: list[dict]) -> list[dict]:
    status = str(kwargs.get("tattoo_status", "None"))
    if status == "None":
        return []
    mode = str(kwargs.get("tattoo_input_mode", "Descriptor List"))
    if status == "One" and mode == "Structured Single Tattoo":
        location = str(kwargs.get("structured_tattoo_location", "Unspecified"))
        description = str(kwargs.get("structured_tattoo_description", ""))
        raw = _structured_tattoo_raw(location, description)
        _, tags = _location_from_text_v241(location if location not in {"Unspecified", "Custom / Describe in Tattoo Description"} else description)
        return [{
            "kind": "tattoo",
            "raw": raw,
            "description": _clean_phrase(description),
            "location": location,
            "region_tags": sorted(tags),
            "quantity": 1,
            "source": "structured",
        }]
    lines = [line.strip() for line in str(kwargs.get("tattoo_descriptors", "")).splitlines() if line.strip()]
    if status == "One":
        lines = lines[:1]
    records = [_parse_tattoo_record_v241(line) for line in lines]
    return records or fallback


def _coverage_tags_v245(profile: dict) -> set[str]:
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
        covered |= {"upper_chest", "chest", "breast", "nipple", "areola", "upper_back"}
        cropped = any(token in top for token in ("crop top", "cropped top", "high-hem", "bikini", "bra", "bralette"))
        if not cropped:
            covered |= {"abdomen", "lower_back"}
        if any(token in top for token in ("long sleeve", "long-sleeve", "jacket", "hoodie", "sweater", "coat", "blouse")):
            covered |= {"upper_arms", "forearms", "arms"}
        elif any(token in top for token in ("t-shirt", "tee", "short sleeve", "short-sleeve")):
            covered |= {"upper_arms"}

    if kind != "top_only" and bottom:
        covered |= {"hips", "groin", "pubic", "genital", "buttocks", "upper_thighs"}
        if any(token in bottom for token in ("jeans", "pants", "trousers", "leggings")):
            covered |= {"thighs", "legs", "knees"}
        elif "skirt" in bottom:
            covered |= {"thighs"}
    if footwear:
        covered |= {"feet"}
    return covered


def _visible_marks_v245(profile: dict, plan: dict) -> tuple[str, list[dict], list[dict]]:
    visible = _visible_tags_v243(plan)
    covered = _coverage_tags_v245(profile)
    extreme = _is_extreme_closeup_v231(plan)
    focus = _focus_value_v231(plan) if extreme else ""
    tattoos = [
        r for r in profile.get("tattoo_records", [])
        if _record_visible_v243(r, visible, covered, plan)
        and (not extreme or _record_matches_extreme_v241(r, focus))
    ]
    piercings = [
        r for r in profile.get("piercing_records", [])
        if _record_visible_v243(r, visible, covered, plan)
        and (not extreme or _record_matches_extreme_v241(r, focus))
    ]
    tattoo_phrases = [_tattoo_phrase_v241(r) for r in tattoos if _tattoo_phrase_v241(r)]
    piercing_phrases = [_piercing_phrase_v241(r) for r in piercings if _piercing_phrase_v241(r)]
    return _sentences(
        "clearly visible permanent tattoo: " + "; ".join(tattoo_phrases) if tattoo_phrases else "",
        "visible permanent jewelry: " + "; ".join(piercing_phrases) if piercing_phrases else "",
    ), tattoos, piercings


def _resolved_lens_v245(shot_type: str, pose: str, regional: bool, extreme: bool) -> str:
    if extreme:
        return "105mm Macro"
    if regional or shot_type in FACE_SCALE_SHOTS:
        return "85mm Portrait — Recommended"
    if shot_type == WIDE_FULL_BODY:
        return "35mm Environmental"
    if shot_type in BODY_SCALE_SHOTS or pose in FLOOR_POSES_V245:
        return "50mm Normal"
    return "85mm Portrait — Recommended"


def _compact_reclining_pose_v245(shot_type: str) -> str:
    if shot_type in FACE_SCALE_SHOTS:
        return _sentences(
            "naturally reclining on one side",
            "the head is lightly supported by one hand and only the nearby shoulder is visible within this close portrait",
        )
    if shot_type == "Waist-Up Midshot":
        return _sentences(
            "comfortably reclining on one side with one bent elbow supporting the upper body",
            "the other hand rests naturally near the hip while the torso follows a relaxed side curve",
        )
    return _sentences(
        "naturally reclining on one side in a comfortable social-photo pose",
        "one bent elbow supports the upper body and the lower hand rests near the head",
        "the other hand rests naturally on the hip, upper thigh, or surface",
        "the hips and legs remain together with a relaxed bend and a natural body curve",
    )


def _pose_prompt_v245(pose: str) -> str:
    if pose == "Finger Heart Near Face":
        return _sentences(
            "both hands raised near the cheek forming one clearly recognizable symmetrical heart",
            "both thumbs meet to create the lower point and both index fingers curve together to create the upper lobes",
            "the open heart shape is clearly visible between the two hands while the remaining fingers stay relaxed",
        )
    if pose == ALL_FOURS:
        return _sentences(
            "stable hands-and-knees tabletop pose on all fours",
            "both palms are flat on the surface at shoulder width with both arms supporting the upper body",
            "both knees and lower legs rest on the surface at hip width, with the hips above the knees and the spine naturally aligned",
        )
    if pose == EXTENDED_PUPPY:
        return _sentences(
            "extended puppy yoga pose on the floor",
            "both knees and lower legs remain grounded with the hips elevated directly above the knees",
            "both arms extend forward with palms flat while the chest and forehead lower toward the surface and the spine lengthens",
        )
    return ""


def _aspect_v245(plan: dict, requested: str) -> tuple[str, int, int]:
    shot = str(plan.get("shot_type", ""))
    pose = str(plan.get("pose", ""))
    if pose in {ALL_FOURS, EXTENDED_PUPPY} and shot in {"Three-Quarter Body", "Full Body", WIDE_FULL_BODY}:
        return "Landscape 3:2 — Automatic for Floor Pose", 1536, 1024
    return _resolve_aspect_v244(plan, requested)


def _body_crop_v245(plan: dict) -> str:
    shot = str(plan.get("shot_type", ""))
    pose = str(plan.get("pose", ""))
    if shot == "Full Body" and pose not in FLOOR_POSES_V245:
        return _sentences(
            "complete standing full-body composition",
            "the entire head and hair, torso, arms, hands, legs, and both feet are fully inside the frame",
            "the subject occupies about forty-five to fifty-five percent of the image height",
            "generous clear margin remains above the hair and below both feet",
            "the camera is centered at navel height with a level horizon and the optical axis parallel to the floor",
        )
    if shot == "Three-Quarter Body" and pose not in FLOOR_POSES_V245:
        return _sentences(
            "standing three-quarter-body composition from the complete head and hair through both knees and upper calves",
            "the subject occupies about fifty-five to sixty-five percent of the image height",
            "clear margin remains above the hair and both knees remain fully inside the frame",
            "the camera is centered at the natural waist with a level horizon",
        )
    return _body_crop_prompt_v244(plan)


def _selfie_camera_adjustment(plan: dict) -> str:
    if str(plan.get("photo_style")) != "Natural Arm's-Length Selfie":
        return ""
    shot = str(plan.get("shot_type", ""))
    if shot in {"Three-Quarter Body", "Full Body", WIDE_FULL_BODY}:
        return _sentences(
            "casual full-length mirror-selfie composition with the phone held slightly off-center",
            "the body is angled a few degrees and the framing is intentionally imperfect rather than rigidly symmetrical",
        )
    return _sentences(
        "phone held slightly above and to one side of the face",
        "one shoulder sits subtly closer to the lens and the composition remains naturally off-center",
    )


def _covered_macro_presentation(profile: dict, plan: dict) -> tuple[str, str]:
    if profile.get("presentation_mode") != "Clothed Character":
        return "", ""
    focus = _focus_value_v231(plan).lower()
    components = profile.get("outfit_components") if isinstance(profile.get("outfit_components"), dict) else {}
    top = _clean_phrase(components.get("swimwear_top", "")) or _clean_phrase(components.get("top", "")) or _clean_phrase(components.get("one_piece", ""))
    bottom = _clean_phrase(components.get("swimwear_bottom", "")) or _clean_phrase(components.get("bottom", "")) or _clean_phrase(components.get("one_piece", ""))
    if any(token in focus for token in ("nipple", "areola", "chest")) and top:
        return f"tight macro photograph of the garment-covered chest area, with {top} remaining visibly in place and securely covering the anatomy", "covered_upper"
    if any(token in focus for token in ("pubic", "genital", "groin")) and bottom:
        return f"tight macro photograph of the garment-covered pelvis area, with {bottom} remaining visibly in place and securely covering the anatomy", "covered_lower"
    return "", ""


class CharacterBlueprintCreatorV245(CharacterBlueprintCreatorV244):
    FUNCTION = "build_blueprint_v245"
    DESCRIPTION = (
        "Current Character Creator with dedicated hair highlights, reliable structured tattoo records, clearer outfit and piercing routing, "
        "visibility-aware anatomy, tan control, and current-only registration."
    )

    @classmethod
    def INPUT_TYPES(cls):
        base = copy.deepcopy(super().INPUT_TYPES())
        base["required"] = _insert_after(
            base["required"],
            "custom_hair_color",
            [("hair_highlights", ("STRING", {"default": "", "multiline": False, "placeholder": "Example: blue and pink face-framing streaks"}))],
        )
        return base

    def build_blueprint_v245(self, **kwargs):
        highlights = str(kwargs.pop("hair_highlights", ""))
        original = dict(kwargs)
        result = list(super().build_blueprint_v244(**kwargs))
        profile = copy.deepcopy(result[8])
        profile["schema"] = "CHARACTER_BLUEPRINT_V245"
        profile["schema_version"] = 16

        old_hair = str(profile.get("hair_prompt", ""))
        new_hair = _hair_with_highlights(old_hair, highlights)
        profile["hair_highlights"] = _clean_phrase(highlights)
        profile["hair_prompt"] = new_hair
        _replace_profile_phrase(profile, old_hair, new_hair)

        fallback_tattoos = list(profile.get("tattoo_records", []))
        tattoo_records = _tattoo_records_v245(original, fallback_tattoos)
        profile["tattoo_records"] = tattoo_records
        profile["tattoo_entries"] = [r.get("raw", "") for r in tattoo_records if r.get("raw")]
        concise_tattoos = [_tattoo_phrase_v241(r) for r in tattoo_records if _tattoo_phrase_v241(r)]
        piercing_records = list(profile.get("piercing_records", []))
        concise_piercings = [_piercing_phrase_v241(r) for r in piercing_records if _piercing_phrase_v241(r)]
        concise_marks = _sentences(
            "permanent tattoo: " + "; ".join(concise_tattoos) if concise_tattoos else "",
            "permanent jewelry: " + "; ".join(concise_piercings) if concise_piercings else "",
        )
        profile["marks_prompt"] = concise_marks

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

        if highlights:
            profile["presentation_summary"] = str(profile.get("presentation_summary", "")) + f"\nHair accents: {_clean_phrase(highlights)}"
        profile["presentation_summary"] = str(profile.get("presentation_summary", "")) + (
            "\nOutfit source guide: Preset uses only a ready-made outfit; Exact Text uses one complete description; "
            "Build Outfit activates the garment-layout selector and only its visible garment fields."
        )
        profile["presentation_summary"] += (
            "\nPiercing guide: Status is the master switch; Entry Method is shown only for one piercing; "
            "Custom Detail is used only when Location, Jewelry Type, or Material is Custom/Other."
        )

        result[0] = profile.get("face_identity", result[0])
        result[4] = concise_marks
        result[6] = active_character
        result[8] = profile
        result[15] = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        result[18] = active_character
        result[19] = profile["clothed_character_prompt"]
        result[20] = profile["clinical_character_prompt"]
        result[21] = profile["presentation_summary"]
        result[29] = new_hair
        return tuple(result)


class CharacterShotControlV245(CharacterShotControlV244):
    FUNCTION = "build_shot_plan_v245"
    DESCRIPTION = (
        "Current Shot Control with compact close-up reclining prompts, corrected Auto Lens, improved full-body camera distance, "
        "stronger amateur/selfie styles, reliable two-hand heart gesture, all-fours and extended puppy poses."
    )

    @classmethod
    def INPUT_TYPES(cls):
        base = copy.deepcopy(super().INPUT_TYPES())
        base["required"]["pose"] = (POSES_V245, {"default": "Neutral Standing"})
        return base

    def build_shot_plan_v245(self, **kwargs):
        call_kwargs = dict(kwargs)
        requested_pose = str(call_kwargs.get("pose", ""))
        requested_lens = str(call_kwargs.get("lens", AUTO_LENS))
        shot_type = str(call_kwargs.get("shot_type", ""))
        effective_lens = requested_lens
        if requested_lens == AUTO_LENS:
            effective_lens = _resolved_lens_v245(
                shot_type,
                requested_pose,
                shot_type == "Close-Up — Regional Documentation",
                shot_type == "Extreme Close-Up — Single Detail",
            )
            call_kwargs["lens"] = effective_lens

        result = list(super().build_shot_plan_v244(**call_kwargs))
        plan = copy.deepcopy(result[0])
        plan["schema"] = "FCC_SHOT_PLAN_V245"
        plan["schema_version"] = 14
        plan["pose"] = requested_pose
        plan["lens_requested"] = requested_lens
        plan["lens_effective"] = effective_lens
        plan["lens"] = effective_lens

        special_pose = _pose_prompt_v245(requested_pose)
        if special_pose and not _is_regional(plan) and not _is_extreme_closeup_v231(plan):
            plan["pose_prompt"] = special_pose

        if requested_pose == NATURAL_SIDE_LYING and not _is_regional(plan) and not _is_extreme_closeup_v231(plan):
            plan["pose_prompt"] = _compact_reclining_pose_v245(shot_type)
            if shot_type in FACE_SCALE_SHOTS:
                plan["camera_prompt"] = _sentences(
                    "close portrait camera placed beside the reclining subject at face level",
                    "the lens is centered on the eyes and upper face with a tight close-portrait composition",
                    LENS_PROMPTS_V2.get(effective_lens, ""),
                )

        if shot_type in {"Three-Quarter Body", "Full Body", WIDE_FULL_BODY} and not _is_regional(plan):
            plan["framing_prompt"] = _body_crop_v245(plan)
            center = "camera centered on the middle of the floor pose" if requested_pose in FLOOR_POSES_V245 else "camera centered at the natural waist or navel"
            plan["camera_prompt"] = _sentences(
                str(plan.get("camera_prompt", "")).replace("upper-torso height", "waist height").replace("slightly above upper-torso height", "slightly above waist height"),
                center,
                "the horizon remains level and the lens axis stays parallel to the floor",
                "the camera distance is set before capture so all required body landmarks and margins remain inside the frame",
            )

        style = str(kwargs.get("photo_style", "Raw Instagram / Unfiltered Social Snapshot"))
        plan["photo_style"] = style
        plan["photo_style_prompt"] = PHOTO_STYLE_PROMPTS_V245.get(style, _style_prompt_v244(style))
        environment_parts = [p.strip() for p in str(plan.get("environment_prompt", "")).split(".") if p.strip()]
        if environment_parts:
            # Preserve background and lighting, replace the inherited style tail.
            bg_light = environment_parts[:2]
            plan["environment_prompt"] = _sentences(*bg_light, plan["photo_style_prompt"])
        selfie_adjust = _selfie_camera_adjustment(plan)
        if selfie_adjust:
            plan["camera_prompt"] = _sentences(
                selfie_adjust,
                LENS_PROMPTS_V2.get(effective_lens, ""),
                "the phone-camera composition remains intentionally imperfect and off-center",
            )

        aspect_label, width, height = _aspect_v245(plan, str(kwargs.get("aspect_ratio", AUTO_ASPECT)))
        plan["aspect_ratio"] = aspect_label
        plan["recommended_width"] = width
        plan["recommended_height"] = height
        plan["resolution_summary"] = f"ACTIVE OUTPUT SIZE: {width} × {height} | {aspect_label} | EFFECTIVE LENS: {effective_lens}"

        plan["final_shot_prompt"] = _sentences(
            plan.get("framing_prompt", ""),
            plan.get("camera_prompt", ""),
            plan.get("pose_prompt", ""),
            plan.get("expression_prompt", ""),
            plan.get("scene_prompt", ""),
            plan.get("environment_prompt", ""),
            _clean_phrase(kwargs.get("shot_suffix", "")),
        )
        summary = str(plan.get("active_settings_summary", ""))
        summary = re.sub(r"\nACTIVE OUTPUT SIZE:.*$", "", summary, flags=re.S).rstrip()
        plan["active_settings_summary"] = summary + "\n" + plan["resolution_summary"]

        result[0] = plan
        result[1] = plan["final_shot_prompt"]
        result[2] = plan.get("framing_prompt", "")
        result[3] = plan.get("camera_prompt", "")
        result[4] = plan.get("pose_prompt", "")
        result[6] = plan.get("environment_prompt", "")
        result[7] = plan["active_settings_summary"]
        result[8] = json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True)
        result[9] = width
        result[10] = height
        return tuple(result)


class CharacterPromptAssemblerV245(CharacterPromptAssemblerV244):
    FUNCTION = "assemble_prompt_v245"
    DESCRIPTION = (
        "Visibility compiler with reliable structured tattoos, garment-aware marks, clothing-respecting body macros, "
        "tan wording after body/presentation, dedicated hair highlights, compact reclining close-ups, and style-specific Krea prompts."
    )

    def assemble_prompt_v245(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan = shot_plan if isinstance(shot_plan, dict) else {}
        krea = generation_purpose.startswith("Krea")
        qwen = generation_purpose.startswith("Qwen")
        extreme = _is_extreme_closeup_v231(plan)
        regional = _is_regional(plan)
        style = str(plan.get("photo_style", "Raw Instagram / Unfiltered Social Snapshot"))
        purpose, reference = _style_purpose_v244(style, generation_purpose, reference_label)
        if krea:
            first_sentences = {
                "Raw Instagram / Unfiltered Social Snapshot": "A raw amateur unfiltered social-media snapshot",
                "Casual Cellphone Snapshot": "A casual imperfect cellphone snapshot",
                "Natural Arm's-Length Selfie": "A natural off-center arm's-length cellphone selfie",
                "Friend-Taken Vacation Photo": "A spontaneous vacation photograph taken by a friend",
            }
            purpose = first_sentences.get(style, purpose)

        tan_base, tan_pattern = _tan_parts_v244(profile, plan)
        marks, visible_tattoos, visible_piercings = _visible_marks_v245(profile, plan)

        body_section = ""
        presentation = ""
        scene = ""
        crop = ""

        if extreme:
            macro = _macro_sections_v241(profile, plan)
            focus = _focus_value_v231(plan)
            covered_macro, covered_kind = _covered_macro_presentation(profile, plan)
            if covered_macro:
                shot_section = _sentences(covered_macro, macro["camera"], macro["environment"], macro["exclusion"])
                character_section = _sentences(profile.get("gender_authority_prompt", ""), profile.get("skin_tone", "").lower() + " skin")
                presentation = covered_macro
                body_section = ""
                marks = ""
                visible_tattoos, visible_piercings = [], []
                crop = covered_macro
                routing_mode = f"covered_macro_{covered_kind}_v245"
            else:
                shot_section = _sentences(macro["crop"], macro["camera"], macro["eye_state"], macro["environment"], macro["exclusion"])
                from .nodes_v230 import _focus_identity_prompt_v231
                character_section = _focus_identity_prompt_v231(profile, focus)
                crop = macro["crop"]
                routing_mode = "extreme_closeup_visibility_compiled_v245"
            skin_variation = _sentences(tan_base, tan_pattern)
            if qwen:
                instruction = _sentences(
                    purpose,
                    f"replace the original image with one tightly cropped macro view of {focus.lower()} only",
                    "preserve only identity characteristics and permanent marks physically belonging inside this crop",
                )
                final_prompt = _sentences(custom_prefix, instruction, shot_section, character_section, presentation, skin_variation, marks, custom_suffix)
            else:
                final_prompt = _sentences(trigger_word, custom_prefix, purpose, shot_section, character_section, presentation, skin_variation, marks, custom_suffix)
        else:
            from .nodes_v244 import REGIONAL_CROPS_V244
            from .nodes_v230 import _crop_prompt_v230
            crop = REGIONAL_CROPS_V244.get(_regional_group(plan), _crop_prompt_v230(plan)) if regional else _crop_prompt_v230(plan)
            custom_direction = _clean_phrase(plan.get("framing_prompt", "")) if plan.get("planner_mode") == "Custom Shot Direction — Keep Character Settings" else ""
            shot_section = _sentences(
                custom_direction or _clean_phrase(plan.get("framing_prompt", "")) or crop,
                "" if custom_direction else _clean_phrase(plan.get("camera_prompt", "")),
                "" if custom_direction or regional else _clean_phrase(plan.get("pose_prompt", "")),
                _clean_phrase(plan.get("expression_prompt", "")),
                _clean_phrase(plan.get("scene_prompt", "")),
                _clean_phrase(plan.get("environment_prompt", "")),
            )
            character_section = _region_identity_v243(profile, plan) if regional else _identity_for_view(profile, plan)
            body_section, presentation, _ = _visible_body_and_presentation_v243(profile, plan)

            components = profile.get("outfit_components") if isinstance(profile.get("outfit_components"), dict) else {}
            kind = str(components.get("kind", ""))
            if kind == "top_only":
                top = _clean_phrase(components.get("top", "")) or "opaque fitted upper garment"
                presentation = _sentences(
                    f"the only garment is {top}, clearly visible and securely covering the chest and upper torso",
                    "the lower body is uncovered",
                )
            elif kind == "bottom_only":
                bottom = _clean_phrase(components.get("bottom", "")) or "secure fitted lower-body garment"
                presentation = _sentences(
                    f"the only garment is {bottom}, clearly visible and securely covering the pelvis and lower body",
                    "the upper torso is uncovered",
                )

            skin_variation = _sentences(tan_base, tan_pattern)
            scene = _clean_phrase(plan.get("scene_prompt", ""))
            if qwen:
                instruction = _sentences(
                    purpose,
                    "replace the original framing, camera, pose, and scene with the active Shot Control result",
                    "apply only the visible Character Creator traits appropriate to this crop, camera direction, and clothing coverage",
                    "secondary people are not copies of the primary character unless Scene Direction explicitly requests that",
                )
                final_prompt = _sentences(
                    custom_prefix, instruction, shot_section, character_section, body_section, presentation,
                    skin_variation, marks, custom_suffix,
                )
            else:
                final_prompt = _sentences(
                    trigger_word, custom_prefix, purpose, shot_section, character_section, body_section, presentation,
                    skin_variation, marks, custom_suffix,
                )
            routing_mode = "regional_visibility_compiled_v245" if regional else "standard_visibility_compiled_v245"

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
            "Visibility Compiler V2.4.5: ACTIVE",
            f"Photo style: {style}",
            f"Output: {width} × {height}; effective lens: {plan.get('lens_effective', plan.get('lens', 'unspecified'))}",
            "Structured tattoos are stored as location-tagged records; garment coverage is evaluated per location.",
            advisory,
        ])
        active_summary = "\n\n".join([
            profile.get("presentation_summary", "Character settings unavailable"),
            plan.get("active_settings_summary", "Shot settings unavailable"),
            f"FINAL PRIMARY CHARACTER\n{character_section}",
            f"FINAL SCENE / SHOT\n{shot_section}",
            f"FINAL VISIBLE BODY\n{body_section or '[none needed for this crop]'}",
            f"FINAL VISIBLE PRESENTATION\n{presentation or '[not visible / omitted]'}",
            f"FINAL VISIBLE TAN / SKIN VARIATION\n{skin_variation or '[none / intentionally low weight]'}",
            f"FINAL VISIBLE MARKS\n{marks or '[none visible in this crop]'}",
            notes,
        ])
        sections = {
            "purpose": purpose,
            "photo_style": style,
            "photo_style_prompt": plan.get("photo_style_prompt", ""),
            "shot_scene": shot_section,
            "primary_character": character_section,
            "visible_body": body_section,
            "visible_presentation": presentation,
            "visible_tan_skin_variation": skin_variation,
            "visible_marks": marks,
            "visible_tattoo_records": visible_tattoos,
            "visible_piercing_records": visible_piercings,
            "routing_mode": routing_mode,
            "final_prompt": final_prompt,
        }
        resolution = f"ACTIVE OUTPUT SIZE: {width} × {height} | {plan.get('aspect_ratio', 'selected aspect ratio')} | EFFECTIVE LENS: {plan.get('lens_effective', plan.get('lens', 'unspecified'))}"
        return (
            final_prompt if krea else "",
            final_prompt if qwen else "",
            shot_section,
            presentation,
            marks,
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
            resolution,
            json.dumps(sections, indent=2, ensure_ascii=False),
            character_section,
            scene,
        )


class QwenDatasetQueueV245(QwenDatasetQueueV244):
    DESCRIPTION = "Current FCC Qwen dataset queue for the v2.4.5 visibility, tattoo, hair-highlight, pose, and style architecture."
