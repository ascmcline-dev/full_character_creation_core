from __future__ import annotations

import copy
import json
from typing import Any

from .nodes import (
    BUST_AUGMENTATION_PROMPTS,
    BUST_POSITION_PROMPTS,
    DEFAULT_CLOTHING,
    LIGHTING_PROMPTS_V2,
    LENS_PROMPTS_V2,
    PRESET_OUTFITS,
    FCCDatasetDirector,
    FCCQueueItemRouter,
    _slug,
)
from .nodes_v230 import (
    _clean_phrase,
    _crop_prompt_v230,
    _focus_identity_prompt_v231,
    _focus_value_v231,
    _is_extreme_closeup_v231,
    _sentences,
)
from .nodes_v240 import _pubic_prompt_with_color
from .nodes_v241 import (
    CharacterBlueprintCreatorV241,
    POSES_V241,
    _camera_view,
    _identity_for_view,
    _macro_sections_v241,
    _rebuild_shot_summary,
    _tan_base_v241,
)
from .nodes_v243 import (
    ASPECT_RATIOS_V243,
    AUTO_ASPECT,
    BACKGROUNDS_V243,
    BACKGROUND_PROMPTS_V243,
    BOTTOM_ONLY_LAYOUT,
    BUST_SHAPES_V243,
    CharacterBlueprintCreatorV243,
    CharacterPromptAssemblerV243,
    CharacterShotControlV243,
    QwenDatasetQueueV243,
    REGIONAL_CROPS,
    SIDE_LYING_LEFT,
    SIDE_LYING_RIGHT,
    SHOT_TYPES_V243,
    TAN_LINE_PATTERNS_V243,
    TOP_ONLY_LAYOUT,
    WIDE_FULL_BODY,
    _is_regional,
    _region_identity_v243,
    _regional_body_v243,
    _regional_camera_prompt_v243,
    _regional_group,
    _regional_presentation_v243,
    _visible_body_and_presentation_v243,
    _visible_marks_v243,
)

# -----------------------------------------------------------------------------
# V2.4.4 / Studio V2.8.4
# - natural side-reclining pose instead of brittle anatomical left/right locks
# - automatic lens selection by shot and visible output-size reporting
# - stronger complete-body subject scale / camera-distance framing
# - distinct Krea photo-style language (social, selfie, vacation, clinical)
# - richer bust-position and augmentation behavior descriptions
# - stronger true-red hair wording
# - additional business and casual preset outfits
# - lower-weight subtle tan mode and safer partial-clothing sequencing
# -----------------------------------------------------------------------------

AUTO_LENS = "Auto by Shot — Recommended"
LENSES_V244 = [AUTO_LENS, "35mm Environmental", "50mm Normal", "85mm Portrait — Recommended", "105mm Macro", "Custom"]

NATURAL_SIDE_LYING = "Lying on Side — Natural Reclining"
POSES_V244 = [p for p in POSES_V241 if p != "Custom"] + [NATURAL_SIDE_LYING, "Custom"]
LEGACY_SIDE_POSES = {SIDE_LYING_LEFT, SIDE_LYING_RIGHT}
HORIZONTAL_POSES_V244 = {NATURAL_SIDE_LYING, "Lying Prone / On Stomach"}

PHOTO_STYLES_V244 = [
    "Raw Instagram / Unfiltered Social Snapshot",
    "Casual Cellphone Snapshot",
    "Natural Arm's-Length Selfie",
    "Friend-Taken Vacation Photo",
    "Authentic Consumer Camera",
    "Standard Camera Photo",
    "Identity Documentation",
    "Clinical Documentation",
]
PHOTO_STYLE_PROMPTS_V244 = {
    "Raw Instagram / Unfiltered Social Snapshot": (
        "raw unfiltered social-media photograph with ordinary handheld framing, natural pores and fine complexion detail, "
        "slight lens softness, mild compression, imperfect everyday exposure, and an ordinary non-commercial finish"
    ),
    "Casual Cellphone Snapshot": (
        "casual handheld smartphone snapshot with believable automatic exposure and white balance, natural ambient-light falloff, "
        "minor framing imperfection, realistic phone-camera texture, and unretouched skin"
    ),
    "Natural Arm's-Length Selfie": (
        "natural arm's-length cellphone selfie with believable front-camera perspective, casual framing, ordinary phone processing, "
        "real skin texture, and a relaxed non-commercial social-media appearance"
    ),
    "Friend-Taken Vacation Photo": (
        "casual travel photograph taken by a friend, relaxed spontaneous composition, ordinary consumer-camera handling, "
        "natural environmental light, mild motion and framing imperfections, and an unposed vacation-photo feeling"
    ),
    "Authentic Consumer Camera": (
        "ordinary unretouched consumer-camera photograph with realistic fabric, natural skin texture, believable shadows, "
        "subtle lens softness, mild compression, and non-commercial everyday color rendering"
    ),
    "Standard Camera Photo": (
        "natural standard-camera photograph with realistic optical detail, balanced exposure, ordinary color rendering, "
        "and a restrained non-commercial finish"
    ),
    "Identity Documentation": (
        "clean neutral identity-reference photography with accurate facial and body proportions, even readable detail, "
        "natural skin texture, restrained processing, and consistent documentation framing"
    ),
    "Clinical Documentation": (
        "clear neutral clinical documentation photography with precise region visibility, even unobstructed lighting, "
        "accurate local anatomy, natural surface texture, and a strict documentary presentation"
    ),
}

# Keep option labels stable for old workflows, but make the actual effects much
# stronger and easier for the image model to distinguish.
BUST_POSITION_PROMPTS.update({
    "Natural Average-Set": (
        "average-set breast placement centered on the middle chest, with a natural upper-chest gap, a normal-height lower fold, "
        "and balanced forward orientation"
    ),
    "High-Set / Perky": (
        "clearly high-set breast placement on the upper chest, with a high lower fold, short vertical chest footprint, "
        "lifted forward orientation, and limited lower drop"
    ),
    "High and Tight": (
        "very high compact breast placement close to the upper chest, with a high tight lower fold, dense upper fullness, "
        "minimal lower hang, and a short vertical footprint"
    ),
    "Low-Set": (
        "clearly low-set breast placement lower on the torso, with a longer open upper-chest area, a lower natural fold, "
        "and visible downward settling"
    ),
    "Downward-Sloping": (
        "downward-resting breast placement with a descending upper slope, lower-pole-dominant fullness, and the lowest contour "
        "sitting below the forward center"
    ),
    "Pendulous Natural": (
        "naturally pendulous breast placement with pronounced lower hang, realistic gravitational weight, a lower fold, "
        "and the fullest point resting clearly below the mid-chest line"
    ),
})

BUST_AUGMENTATION_PROMPTS.update({
    "Natural / Unaugmented": (
        "natural unaugmented breast structure; the selected base shape, spacing, softness, and vertical placement remain the primary anatomy"
    ),
    "Subtle Natural-Looking Augmentation": (
        "subtle natural-looking augmentation that gently increases forward projection and upper-pole support while preserving the selected "
        "base shape, spacing, and vertical placement"
    ),
    "Round High-Profile Implants": (
        "round high-profile augmentation with strong forward projection, a narrower implant footprint, pronounced upper-pole fullness, "
        "and firmer centered volume; the selected vertical placement still determines where the breast roots sit on the torso"
    ),
    "Teardrop / Anatomical Implants": (
        "anatomical teardrop augmentation with a smooth sloped upper pole, fuller lower pole, controlled forward projection, "
        "and the selected vertical placement preserved"
    ),
    "Very Firm Augmented Projection": (
        "very firm augmented structure with strong forward projection, dense upper-pole fullness, stable contour, minimal natural settling, "
        "and the selected vertical placement controlling the root height"
    ),
})

# New preset outfits. Mutating these shared tables before INPUT_TYPES is queried
# allows the current creator to expose them without duplicating the older builder.
for _name in ("Business Blouse and Pencil Skirt", "High-Hem Crop Top and Daisy Dukes"):
    if _name not in DEFAULT_CLOTHING:
        insert_at = DEFAULT_CLOTHING.index("Swimwear") if "Swimwear" in DEFAULT_CLOTHING else len(DEFAULT_CLOTHING)
        DEFAULT_CLOTHING.insert(insert_at, _name)

PRESET_OUTFITS["Business Blouse and Pencil Skirt"] = {
    "kind": "complete",
    "top": "opaque tailored business blouse with a proper collar, fitted waist shaping, and normal professional chest coverage",
    "bottom": "high-waisted tailored knee-length pencil skirt",
    "footwear": "simple professional pumps or closed-toe office shoes",
}
PRESET_OUTFITS["High-Hem Crop Top and Daisy Dukes"] = {
    "kind": "complete",
    "top": (
        "opaque fitted high-hem crop top ending immediately beneath the bust line, with the narrow lower-bust edge only barely visible "
        "and the chest otherwise securely covered"
    ),
    "bottom": "very short fitted Daisy Duke denim cut-off shorts with a secure high hip fit",
    "footwear": "casual low-profile sneakers or sandals",
}

# Upper-chest crop previously encouraged an elongated neck because the crop began
# too high while omitting the rest of the face. Start at the lower jaw and anchor
# normal neck length / collarbone placement.
REGIONAL_CROPS_V244 = dict(REGIONAL_CROPS)
REGIONAL_CROPS_V244["upper_chest"] = (
    "tight regional documentation crop centered on the collarbones, sternum, and complete upper chest; the top edge includes only the "
    "lower jaw and normal-length neck, the collarbones sit in the upper third of the image, the bottom edge ends just below the chest line, "
    "and both shoulders remain fully inside the frame"
)


def _resolved_lens_v244(shot_type: str, pose: str, regional: bool, extreme: bool) -> str:
    if extreme:
        return "105mm Macro"
    if regional:
        return "85mm Portrait — Recommended" if shot_type else "85mm Portrait — Recommended"
    if shot_type == WIDE_FULL_BODY:
        return "35mm Environmental"
    if shot_type in {"Three-Quarter Body", "Full Body", "Waist-Up Midshot"}:
        return "50mm Normal"
    if pose in HORIZONTAL_POSES_V244:
        return "50mm Normal"
    return "85mm Portrait — Recommended"


def _style_prompt_v244(style: str) -> str:
    return PHOTO_STYLE_PROMPTS_V244.get(style, PHOTO_STYLE_PROMPTS_V244["Authentic Consumer Camera"])


def _style_purpose_v244(style: str, generation_purpose: str, reference_label: str) -> tuple[str, str]:
    if generation_purpose == "Krea — First Identity Image":
        first = {
            "Raw Instagram / Unfiltered Social Snapshot": "A raw unfiltered social-media snapshot",
            "Casual Cellphone Snapshot": "A casual handheld cellphone snapshot",
            "Natural Arm's-Length Selfie": "A natural arm's-length cellphone selfie",
            "Friend-Taken Vacation Photo": "A casual vacation photograph taken by a friend",
            "Authentic Consumer Camera": "An ordinary unretouched consumer-camera photograph",
            "Standard Camera Photo": "A natural standard-camera photograph",
            "Identity Documentation": "A clean identity-reference photograph",
            "Clinical Documentation": "A clear neutral clinical documentation photograph",
        }.get(style, "An ordinary unretouched consumer-camera photograph")
        return first, "None — text-to-image"
    if generation_purpose == "Krea — LoRA Expansion":
        return _sentences(
            "A realistic photograph using the loaded identity LoRA",
            _style_prompt_v244(style),
        ), "Identity LoRA"
    if generation_purpose == "Qwen — Anatomy Documentation":
        return _sentences(
            f"Edit {reference_label} into neutral clinical anatomy documentation of the same primary character",
            _style_prompt_v244("Clinical Documentation"),
        ), reference_label
    if generation_purpose.startswith("Qwen"):
        return _sentences(
            f"Edit {reference_label} into a new realistic photograph while preserving the exact identity of the primary character",
            f"render the result as: {_style_prompt_v244(style)}",
        ), reference_label
    return _sentences("A realistic camera photograph", _style_prompt_v244(style)), reference_label


def _natural_side_pose_prompt_v244() -> str:
    return _sentences(
        "naturally reclining on one side in a comfortable social-photo pose",
        "the lower elbow is bent and lightly supports the upper body, with the lower hand near or gently supporting the head",
        "the upper hand rests naturally on the hip, upper thigh, or support surface",
        "the hips and legs lie together with a relaxed bend and a natural gentle body curve",
        "the torso remains side-facing rather than rolled flat onto the back, and the pose looks relaxed rather than anatomically rigid",
    )


def _natural_side_view_prompt_v244(plan: dict) -> str:
    view = _camera_view(plan)
    if view == "Back View":
        return _sentences(
            "rear lateral camera position behind the naturally side-reclining subject",
            "the back, rear waist, and rear hip remain dominant while the face is only minimally visible in profile",
            "the subject stays comfortably reclined without twisting the torso toward the lens",
        )
    if view in {"Rear Three-Quarter Left", "Rear Three-Quarter Right"}:
        return _sentences(
            f"{view.lower()} camera position around the naturally side-reclining subject",
            "the back and rear hip remain dominant, with only a restrained partial facial profile",
        )
    if view in {"Three-Quarter Left", "Three-Quarter Right"}:
        return _sentences(
            f"{view.lower()} camera position around the naturally side-reclining subject",
            "the front torso and side profile remain visible while the camera supplies the oblique angle",
        )
    if view in {"Left Profile", "Right Profile"}:
        return _sentences(f"{view.lower()} lateral camera position beside the naturally reclining subject")
    return _sentences(
        "front lateral camera position beside the naturally side-reclining subject",
        "the face, front shoulder, waist, and forward hip are naturally visible without forcing a rigid ninety-degree stack",
    )


def _natural_side_height_prompt_v244(plan: dict) -> str:
    height = str(plan.get("camera_height", ""))
    if height == "Slightly Above Eye Level":
        return "camera gently elevated above the reclining torso with a controlled ten-to-fifteen-degree downward view"
    if height == "Slightly Below Eye Level":
        return "camera low near the support surface with a mild upward view across the reclining torso"
    if height == "Eye Level":
        return "camera level with the reclining torso and far enough away to preserve the complete requested crop"
    return str(plan.get("camera_prompt", ""))


def _body_crop_prompt_v244(plan: dict) -> str:
    shot = str(plan.get("shot_type", ""))
    horizontal = str(plan.get("pose", "")) in HORIZONTAL_POSES_V244
    if shot == WIDE_FULL_BODY:
        if horizontal:
            return _sentences(
                "wide landscape environmental full-body composition",
                "the complete head, hair, torso, arms, hands, hips, legs, and both feet are fully inside the frame",
                "the reclining body occupies about sixty-five to seventy-five percent of the image width",
                "generous environment remains beyond the head, feet, and both sides of the body",
            )
        return _sentences(
            "wide environmental full-body composition",
            "the complete head, hair, torso, arms, hands, legs, and both feet are fully inside the frame",
            "the standing subject occupies only about forty-five to fifty-five percent of the image height",
            "generous environment remains above the hair, below the feet, and beside the body",
        )
    if shot == "Full Body":
        if horizontal:
            return _sentences(
                "landscape full-body composition of the complete reclining subject",
                "the entire head and hair, torso, arms, hands, hips, legs, and both feet are fully inside the frame",
                "the body occupies about seventy to eighty percent of the image width with clear margin beyond the head and feet",
            )
        return _sentences(
            "complete standing full-body composition",
            "the entire head and hair, torso, arms, hands, legs, and both feet are fully inside the frame",
            "the subject occupies about fifty-five to sixty-five percent of the image height",
            "clear empty margin remains above the hair and below both feet",
        )
    if shot == "Three-Quarter Body":
        if horizontal:
            return _sentences(
                "landscape three-quarter-body composition from the complete head and hair through below both knees",
                "the head end and both knees remain fully inside the frame with clear margin",
            )
        return _sentences(
            "standing three-quarter-body composition from the complete head and hair through both knees and upper calves",
            "the subject occupies about sixty to seventy percent of the image height",
            "the top of the hair remains fully inside the frame with clear margin, and both knees remain completely visible",
            "the camera is centered around the waist rather than the face",
        )
    return _clean_phrase(plan.get("framing_prompt", ""))


def _resolve_aspect_v244(plan: dict, requested: str) -> tuple[str, int, int]:
    shot = str(plan.get("shot_type", ""))
    horizontal = str(plan.get("pose", "")) in HORIZONTAL_POSES_V244
    if shot == WIDE_FULL_BODY:
        return "Landscape 3:2 — Automatic Wide Full Body", 1536, 1024
    if horizontal and shot in {"Three-Quarter Body", "Full Body"}:
        return "Landscape 3:2 — Automatic for Reclining Pose", 1536, 1024
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
        "Landscape 4:3": (1280, 1024),
    }.get(requested, (1024, 1280))
    return requested, dims[0], dims[1]


def _tan_parts_v244(profile: dict, plan: dict) -> tuple[str, str]:
    base = _tan_base_v241(profile)
    if not base:
        return "", ""
    state = str(profile.get("tan_line_state", "Even Tan — No Defined Lines"))
    if state == "Even Tan — No Defined Lines":
        return base, ""
    if state == "Custom":
        return base, _clean_phrase(profile.get("custom_tan_description", ""))
    strength = str(profile.get("tan_line_visibility", "Moderate"))
    if strength == "Subtle":
        # Krea consistently over-emphasized even carefully worded subtle tan lines.
        # Base tan only leaves room for a faint natural difference without activating
        # a geometric garment outline.
        return base, ""
    from .nodes_v243 import _tan_pattern_phrase_v243, _visible_tags_v243, _is_rear_orientation
    pattern = str(profile.get("tan_line_pattern", "String Bikini — Minimal Triangle and Tight V"))
    phrase = _tan_pattern_phrase_v243(pattern, _visible_tags_v243(plan), strength, _is_rear_orientation(plan))
    return base, phrase


def _update_red_profile_v244(profile: dict, result: list[Any]) -> None:
    profile["hair_color"] = "Red"
    profile["hair_color_rendering"] = "rich saturated natural auburn-copper red with unmistakable red dominance"
    # Keep the stronger generated hair prompt and matched pubic-hair color from
    # the temporary custom-color route. The display value remains Red.
    summary = str(profile.get("anatomy_configuration_summary", ""))
    summary = summary.replace(
        "Pubic hair color: matches rich saturated natural auburn-copper red with unmistakable red dominance head hair",
        "Pubic hair color: matches the selected rich red head hair",
    )
    profile["anatomy_configuration_summary"] = summary
    result[28] = summary


class CharacterBlueprintCreatorV244(CharacterBlueprintCreatorV243):
    FUNCTION = "build_blueprint_v244"
    DESCRIPTION = (
        "Current Character Creator with stronger bust position/augmentation effects, true-red hair rendering, additional outfit presets, "
        "visibility-aware anatomy, tan routing, and structured permanent marks."
    )

    @classmethod
    def INPUT_TYPES(cls):
        base = copy.deepcopy(super().INPUT_TYPES())
        base["required"]["bust_shape"] = (BUST_SHAPES_V243, {"default": "Unspecified"})
        return base

    def build_blueprint_v244(self, **kwargs):
        call_kwargs = dict(kwargs)
        selected_red = str(call_kwargs.get("hair_color", "")) == "Red"
        if selected_red:
            call_kwargs["hair_color"] = "Custom"
            call_kwargs["custom_hair_color"] = "rich saturated natural auburn-copper red with unmistakable red dominance"

        result = list(super().build_blueprint_v243(**call_kwargs))
        profile = copy.deepcopy(result[8])
        profile["schema"] = "CHARACTER_BLUEPRINT_V244"
        profile["schema_version"] = 15

        if selected_red:
            _update_red_profile_v244(profile, result)

        # Explain how augmentation modifies, rather than silently replaces, the
        # selected shape and position.
        pos = str(kwargs.get("bust_position", "Unspecified"))
        aug = str(kwargs.get("bust_augmentation", "Unspecified"))
        interaction = ""
        if pos != "Unspecified" or aug != "Unspecified":
            interaction = _sentences(
                f"Bust vertical placement effect: {BUST_POSITION_PROMPTS.get(pos, '[unspecified]')}" if pos != "Unspecified" else "",
                f"Augmentation effect: {BUST_AUGMENTATION_PROMPTS.get(aug, '[unspecified]')}" if aug != "Unspecified" else "",
                "The selected breast shape establishes the base contour; position controls root height on the torso; augmentation modifies projection, firmness, and upper-versus-lower fullness.",
            )
        profile["bust_position_augmentation_summary"] = interaction
        if interaction:
            profile["presentation_summary"] = str(profile.get("presentation_summary", "")) + "\n" + interaction
            result[21] = profile["presentation_summary"]

        warnings = str(profile.get("warnings", "") or "")
        if aug == "Very Firm Augmented Projection" and pos in {"Downward-Sloping", "Pendulous Natural"}:
            warnings = (warnings + " Selected very-firm augmentation conflicts with a strongly hanging position; root height follows Bust Position while firmness/projection follows Augmentation.").strip()
        profile["warnings"] = warnings
        result[9] = warnings

        result[8] = profile
        result[15] = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        return tuple(result)


class CharacterShotControlV244(CharacterShotControlV243):
    FUNCTION = "build_shot_plan_v244"
    DESCRIPTION = (
        "Current Shot Control with natural side reclining, automatic shot-appropriate lenses, complete-body subject scaling, "
        "distinct social/consumer/clinical photo styles, region-centered cameras, and visible output-size reporting."
    )

    @classmethod
    def INPUT_TYPES(cls):
        base = copy.deepcopy(super().INPUT_TYPES())
        base["required"]["pose"] = (POSES_V244, {"default": "Neutral Standing"})
        base["required"]["lens"] = (LENSES_V244, {"default": AUTO_LENS})
        base["required"]["photo_style"] = (PHOTO_STYLES_V244, {"default": "Raw Instagram / Unfiltered Social Snapshot"})
        base["required"]["aspect_ratio"] = (ASPECT_RATIOS_V243, {"default": AUTO_ASPECT})
        return base

    def build_shot_plan_v244(self, **kwargs):
        call_kwargs = dict(kwargs)
        requested_pose = str(call_kwargs.get("pose", ""))
        if requested_pose in LEGACY_SIDE_POSES:
            requested_pose = NATURAL_SIDE_LYING
            call_kwargs["pose"] = NATURAL_SIDE_LYING

        requested_lens = str(call_kwargs.get("lens", AUTO_LENS))
        effective_lens = requested_lens
        if requested_lens == AUTO_LENS:
            shot = str(call_kwargs.get("shot_type", ""))
            effective_lens = _resolved_lens_v244(
                shot,
                requested_pose,
                shot == "Close-Up — Regional Documentation",
                shot == "Extreme Close-Up — Single Detail",
            )
            call_kwargs["lens"] = effective_lens

        result = list(super().build_shot_plan_v243(**call_kwargs))
        plan = copy.deepcopy(result[0])
        plan["schema"] = "FCC_SHOT_PLAN_V244"
        plan["schema_version"] = 13
        plan["pose"] = requested_pose
        plan["lens_requested"] = requested_lens
        plan["lens_effective"] = effective_lens
        plan["lens"] = effective_lens

        # Replace the inherited rigid left/right recumbent wording.
        if requested_pose == NATURAL_SIDE_LYING and not _is_regional(plan):
            plan["pose_prompt"] = _natural_side_pose_prompt_v244()
            plan["camera_prompt"] = _sentences(
                _natural_side_view_prompt_v244(plan),
                _natural_side_height_prompt_v244(plan),
                LENS_PROMPTS_V2.get(effective_lens, "").replace("facial", "full-body"),
                "camera distance is wide enough to preserve the complete requested reclining crop",
            )
            if _camera_view(plan) == "Back View":
                plan["expression_prompt"] = ""

        # Stronger complete-body scale and camera targeting.
        if str(plan.get("shot_type", "")) in {"Three-Quarter Body", "Full Body", WIDE_FULL_BODY} and not _is_regional(plan):
            plan["framing_prompt"] = _body_crop_prompt_v244(plan)
            center = "camera centered around the waist and pelvis" if requested_pose not in HORIZONTAL_POSES_V244 else "camera centered on the middle of the reclining torso"
            plan["camera_prompt"] = _sentences(
                str(plan.get("camera_prompt", "")).replace("facial proportions", "complete-body proportions"),
                center,
                "the framing is established at the required distance before the photograph is taken",
            )

        # Replace inherited upper-chest crop with the shorter-neck version.
        if _is_regional(plan) and _regional_group(plan) == "upper_chest":
            plan["framing_prompt"] = REGIONAL_CROPS_V244["upper_chest"]
            plan["camera_prompt"] = _regional_camera_prompt_v243(plan, kwargs.get("custom_camera", ""))

        # Rebuild environment from explicit style mappings rather than using the
        # raw lower-cased dropdown label.
        background = str(kwargs.get("background", "Studio Solid Gray"))
        if background == "Custom":
            background_prompt = _clean_phrase(kwargs.get("custom_background", ""))
        else:
            background_prompt = BACKGROUND_PROMPTS_V243.get(background, background.lower() + " background")
        lighting = str(kwargs.get("lighting", "Soft Natural Daylight"))
        if lighting == "Custom":
            lighting_prompt = _clean_phrase(kwargs.get("custom_lighting", ""))
        else:
            lighting_prompt = LIGHTING_PROMPTS_V2.get(lighting, lighting.lower())
        style = str(kwargs.get("photo_style", "Raw Instagram / Unfiltered Social Snapshot"))
        plan["photo_style"] = style
        plan["photo_style_prompt"] = _style_prompt_v244(style)
        plan["environment_prompt"] = _sentences(background_prompt, lighting_prompt, plan["photo_style_prompt"])

        aspect_label, width, height = _resolve_aspect_v244(plan, str(kwargs.get("aspect_ratio", AUTO_ASPECT)))
        plan["aspect_ratio"] = aspect_label
        plan["recommended_width"] = width
        plan["recommended_height"] = height
        plan["resolution_summary"] = f"ACTIVE OUTPUT SIZE: {width} × {height} | {aspect_label} | effective lens: {effective_lens}"

        ignored_extra: list[str] = []
        if requested_lens == AUTO_LENS:
            ignored_extra.append(f"Auto Lens resolved to {effective_lens}")
        if requested_pose == NATURAL_SIDE_LYING:
            ignored_extra.append("Natural side reclining uses a relaxed supported pose without anatomical left/right locking")

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
        plan["active_settings_summary"] += "\n" + plan["resolution_summary"]

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


class CharacterPromptAssemblerV244(CharacterPromptAssemblerV243):
    FUNCTION = "assemble_prompt_v244"
    DESCRIPTION = (
        "Visibility compiler with style-specific Krea language, region-first crops, clothing-before-tan sequencing, low-weight subtle tan, "
        "complete-body framing, local marks, and natural side-reclining routing."
    )

    def assemble_prompt_v244(
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

        tan_base, tan_pattern = _tan_parts_v244(profile, plan)
        marks, visible_tattoos, visible_piercings = _visible_marks_v243(profile, plan)

        if extreme:
            macro = _macro_sections_v241(profile, plan)
            focus = _focus_value_v231(plan)
            shot_section = _sentences(macro["crop"], macro["camera"], macro["eye_state"], macro["environment"], macro["exclusion"])
            character_section = _sentences(_focus_identity_prompt_v231(profile, focus), tan_base)
            body_section = ""
            presentation = ""
            skin_variation = tan_pattern
            appearance_section = marks
            crop = macro["crop"]
            if qwen:
                instruction = _sentences(
                    purpose,
                    f"replace the original image with one tightly cropped macro view of {focus.lower()} only",
                    "preserve only identity characteristics and permanent marks physically belonging inside this crop",
                )
                final_prompt = _sentences(custom_prefix, instruction, shot_section, character_section, skin_variation, appearance_section, custom_suffix)
            else:
                final_prompt = _sentences(trigger_word, custom_prefix, purpose, shot_section, character_section, skin_variation, appearance_section, custom_suffix)
            routing_mode = "extreme_closeup_visibility_compiled_v244"
            scene = ""
        else:
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
            character_section = _sentences(_region_identity_v243(profile, plan) if regional else _identity_for_view(profile, plan), tan_base)
            body_section, presentation, _ = _visible_body_and_presentation_v243(profile, plan)

            # Stronger partial-clothing statement. The visible garment is named
            # before any uncovered anatomy or tan variation so Krea does not erase it.
            components = profile.get("outfit_components") if isinstance(profile.get("outfit_components"), dict) else {}
            kind = str(components.get("kind", ""))
            if kind == "top_only":
                top = _clean_phrase(components.get("top", "")) or "opaque fitted upper garment"
                presentation = _sentences(
                    f"the only garment is {top}, clearly visible and securely covering the chest and upper torso",
                    "the lower body is unclothed",
                )
            elif kind == "bottom_only":
                bottom = _clean_phrase(components.get("bottom", "")) or "secure fitted lower-body garment"
                presentation = _sentences(
                    f"the only garment is {bottom}, clearly visible and securely covering the pelvis and lower body",
                    "the upper torso is unclothed",
                )

            skin_variation = tan_pattern
            appearance_section = marks
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
                    skin_variation, appearance_section, custom_suffix,
                )
            else:
                final_prompt = _sentences(
                    trigger_word, custom_prefix, purpose, shot_section, character_section, body_section, presentation,
                    skin_variation, appearance_section, custom_suffix,
                )
            routing_mode = "regional_visibility_compiled_v244" if regional else "standard_visibility_compiled_v244"

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
        subtle_note = " Subtle tan-line strength intentionally emits no geometric line pattern for Krea." if (
            str(profile.get("tan_line_state", "")) == "Defined Tan Lines" and str(profile.get("tan_line_visibility", "")) == "Subtle"
        ) else ""
        notes = "\n".join([
            f"Purpose: {generation_purpose}",
            f"Reference: {reference}",
            "Visibility Compiler V2.4.4: ACTIVE",
            f"Photo style: {style}",
            f"Output: {width} × {height}; effective lens: {plan.get('lens_effective', plan.get('lens', 'unspecified'))}",
            "Regional documentation uses local identity, local body, local garment, and local mark subsets only.",
            advisory + subtle_note,
        ])
        active_summary = "\n\n".join([
            profile.get("presentation_summary", "Character settings unavailable"),
            plan.get("active_settings_summary", "Shot settings unavailable"),
            f"FINAL PRIMARY CHARACTER\n{character_section}",
            f"FINAL SCENE / SHOT\n{shot_section}",
            f"FINAL VISIBLE BODY\n{body_section or '[none needed for this crop]'}",
            f"FINAL VISIBLE PRESENTATION\n{presentation or '[not visible / omitted]'}",
            f"FINAL VISIBLE TAN / SKIN VARIATION\n{skin_variation or '[none / intentionally low weight]'}",
            f"FINAL VISIBLE MARKS\n{appearance_section or '[none visible in this crop]'}",
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
            "visible_marks": appearance_section,
            "visible_tattoo_records": visible_tattoos,
            "visible_piercing_records": visible_piercings,
            "routing_mode": routing_mode,
            "final_prompt": final_prompt,
        }
        resolution = f"ACTIVE OUTPUT SIZE: {width} × {height} | {plan.get('aspect_ratio', 'selected aspect ratio')} | effective lens: {plan.get('lens_effective', plan.get('lens', 'unspecified'))}"
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
            resolution,
            json.dumps(sections, indent=2, ensure_ascii=False),
            character_section,
            scene,
        )


class QwenDatasetQueueV244(QwenDatasetQueueV243):
    DESCRIPTION = "Current FCC Qwen dataset queue for the v2.4.4 character blueprint and visibility architecture."
