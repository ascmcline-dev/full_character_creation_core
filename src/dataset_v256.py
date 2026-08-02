from __future__ import annotations

import copy
import json
from typing import Any

from .nodes_v230 import _clean_phrase, _sentences
from .dataset_v254 import (
    QWEN_ANGLE_TARGETS,
    FCCKreaQueueItemRouter,
    _anchor_specs,
    _body_only_authority,
    _face_identity,
    _nonface_identity,
    _photo_base,
    _region_marks,
    _regional_outfit,
    _regional_specs,
    _skin,
    _slug,
    _spec,
    _unique_sentences,
)
from .dataset_v255 import FCCFaceAngleDatasetDirector as FCCFaceAngleDatasetDirectorV255


KREA_BLUEPRINT_PLANS = [
    "Identity Anchors — 3",
    "Body-Only Regional Atlas — Clothed",
    "Body-Only Regional Atlas — Clinical Unclothed",
    "Complete Body-Only Regional Atlas — Clothed and Clinical",
    "Extreme Clinical Body Validation — Opt-In Only",
    "Complete Pre-LoRA Documentation — Anchors + Body Atlas",
]


def _resolved_chest(profile: dict[str, Any]) -> str:
    return str(profile.get("resolved_chest_anatomy", "Flat / Neutral Chest"))


def _resolved_groin(profile: dict[str, Any]) -> str:
    return str(profile.get("resolved_groin_anatomy", "Unspecified — Do Not Describe"))


def _copy_specs_for_profile(specs: list[dict[str, Any]], profile: dict[str, Any]) -> list[dict[str, Any]]:
    """Make boilerplate region tags and labels follow resolved chest anatomy."""
    resolved = _resolved_chest(profile)
    out = copy.deepcopy(specs)
    for spec in out:
        regions = set(spec.get("regions", set()))
        if resolved == "Masculine Chest — Use Male Chest Control":
            regions.discard("breast")
            regions.discard("left_breast")
            regions.discard("right_breast")
            if "chest" in regions:
                regions.add("pectoral")
            if "left_chest" in str(spec.get("shot_id", "")) or "left_breast" in set(spec.get("regions", set())):
                regions.add("left_pectoral")
            if "right_chest" in str(spec.get("shot_id", "")) or "right_breast" in set(spec.get("regions", set())):
                regions.add("right_pectoral")
            desc = str(spec.get("description", ""))
            desc = desc.replace("chest or breast", "pectoral chest")
            desc = desc.replace("breast", "pectoral")
            desc = desc.replace("bust", "pectoral chest")
            spec["description"] = desc
        elif resolved == "Flat / Neutral Chest":
            regions.discard("breast")
            regions.discard("left_breast")
            regions.discard("right_breast")
            if "chest" in regions:
                regions.add("neutral_chest")
            spec["description"] = str(spec.get("description", "")).replace("chest or breast", "flat neutral chest")
        elif resolved == "Custom Chest Description":
            regions.discard("breast")
            regions.discard("left_breast")
            regions.discard("right_breast")
            if "chest" in regions:
                regions.add("custom_chest")
            spec["description"] = str(spec.get("description", "")).replace("chest or breast", "configured custom chest")
        spec["regions"] = regions
    return out


def _clinical_body(profile: dict[str, Any], regions: set[str]) -> str:
    parts: list[str] = [
        "neutral adult clinical anatomy documentation",
        "the documented region is uncovered only as required for direct anatomical visibility",
        "ordinary relaxed documentation posture with no hand contact with the documented anatomy",
    ]
    torso_regions = {
        "shoulders", "upper_torso", "chest", "pectoral", "neutral_chest", "custom_chest",
        "back", "abdomen", "waist",
    }
    arm_regions = {"arms", "upper_arm", "elbow", "forearm", "wrist", "hand"}
    pelvis_regions = {"pelvis", "hips", "buttocks"}
    leg_regions = {"thigh", "knee", "shin", "calf", "ankle", "foot", "sole", "legs"}
    groin_regions = {"groin", "pubic", "perineal", "male_genital", "female_genital", "custom_groin", "suprapubic"}

    if regions & torso_regions:
        parts.append(profile.get("body_type_authority_prompt", ""))
        parts.append(profile.get("anatomy_upper_body", ""))
    if regions & arm_regions:
        parts.append(profile.get("upper_limb_proportion_prompt", ""))
    if regions & {"chest", "pectoral", "neutral_chest", "custom_chest"}:
        parts.append(profile.get("chest_anatomy_prompt", ""))
        parts.append(profile.get("chest_region_integrity_prompt", ""))
    if regions & pelvis_regions:
        parts.append(profile.get("lower_body_silhouette_prompt", "") or profile.get("clothed_lower_body", ""))
    if regions & leg_regions:
        parts.append(profile.get("lower_limb_proportion_prompt", ""))
    if regions & groin_regions:
        parts.append(profile.get("groin_anatomy_prompt", ""))
        parts.append(profile.get("pubic_hair_prompt", ""))
        parts.append(profile.get("sex_anatomy_integrity_prompt", ""))
    if regions & ({"chest", "pectoral", "neutral_chest", "custom_chest"} | groin_regions):
        parts.append(profile.get("anatomy_integrity_lock", ""))
    return _unique_sentences(*parts)


def _clothed_body(profile: dict[str, Any], regions: set[str]) -> str:
    parts: list[str] = []
    torso = {
        "shoulders", "upper_torso", "chest", "pectoral", "neutral_chest", "custom_chest",
        "back", "abdomen", "waist",
    }
    arms = {"arms", "upper_arm", "elbow", "forearm", "wrist", "hand"}
    pelvis = {"pelvis", "hips", "buttocks"}
    legs = {"thigh", "knee", "shin", "calf", "ankle", "foot", "legs"}
    if regions & torso:
        parts.append(profile.get("body_type_authority_prompt", ""))
        parts.append(profile.get("clothed_upper_body", ""))
    if regions & arms:
        parts.append(profile.get("upper_limb_proportion_prompt", ""))
    if regions & {"chest", "pectoral", "neutral_chest", "custom_chest"}:
        parts.append(profile.get("chest_clothed_prompt", ""))
        parts.append(profile.get("chest_region_integrity_prompt", ""))
    if regions & pelvis:
        parts.append(profile.get("clothed_lower_body", ""))
    if regions & legs:
        parts.append(profile.get("lower_limb_proportion_prompt", ""))
    return _unique_sentences(*parts)


def _special_region_authority(profile: dict[str, Any], spec: dict[str, Any]) -> str:
    sid = str(spec.get("shot_id", "")).lower()
    regions = set(spec.get("regions", set()))
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
            "the lower forearm enters the frame and connects continuously through the wrist into exactly one normal hand",
            "no complete body, face, torso, opposite arm, floating hand, or oversized foreground hand appears",
        ])
    elif "hand_" in sid and "profile" in sid:
        side = "left" if "left" in sid else "right"
        parts.extend([
            f"document one anatomically {side} hand in true side profile with the lower forearm entering and connecting naturally through the wrist",
            "the hand remains normal scale and no complete body or second hand appears",
        ])

    if "foot_dorsal" in sid:
        side = "left" if "left" in sid else "right"
        parts.extend([
            f"document only the lower shin, ankle, and anatomical {side} foot",
            "the foot points naturally downward in plantar flexion while the dorsal surface faces the camera",
            "the lower shin enters and connects continuously into exactly one normal foot with five toes",
            "no upper body, pelvis, thigh, other leg, or second foot appears",
        ])
    elif "foot_" in sid and "profile" in sid:
        side = "left" if "left" in sid else "right"
        parts.extend([
            f"document only the lower shin, ankle, and anatomical {side} foot in true side profile",
            "the foot points naturally downward and remains continuously attached to the lower leg",
            "no second foot, upper body, pelvis, or thigh appears",
        ])
    elif "sole" in sid:
        side = "left" if "left" in sid else "right"
        parts.extend([
            f"the anatomical {side} lower leg extends toward the camera and the ankle flexes so the complete sole faces the lens",
            "show only the lower shin, ankle, heel, sole, and five toes of one continuously attached foot",
            "no second foot, upper body, pelvis, or other leg appears",
        ])

    if any(token in sid for token in ("chest", "pectoral", "sternum", "nipple_areola")):
        resolved = _resolved_chest(profile)
        if resolved == "Masculine Chest — Use Male Chest Control":
            parts.extend([
                "preserve the configured adult male pectoral width, sternum spacing, nipple placement, areola placement, pectoral volume, and lower pectoral boundary",
                "the crop adapts to the selected masculine chest rather than resizing the anatomy to fit the crop",
            ])
        elif resolved == "Bust Anatomy — Use Bust Controls":
            parts.extend([
                "preserve the selected bust base width, spacing, vertical placement, forward projection, upper fullness, lower fullness, natural weight, and complete lower contours",
                "increase camera distance or widen the regional crop as necessary; the selected bust anatomy is not reduced to fit the crop",
            ])
        elif resolved == "Flat / Neutral Chest":
            parts.extend([
                "preserve the configured flat neutral chest width, nipple placement, areola placement, sternum relationship, and minimal projection",
                "the crop adapts to the selected flat chest without adding unselected volume",
            ])
        else:
            parts.extend([
                "preserve the explicitly configured custom chest dimensions and surface anatomy",
                "the crop adapts to the custom anatomy without replacing it with another chest category",
            ])

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


def _build_krea_prompt(profile: dict[str, Any], spec: dict[str, Any], suffix: str) -> str:
    regions = set(spec["regions"])
    presentation = str(spec["presentation"])
    anchor = spec["category"] == "identity_anchor"

    identity = _face_identity(profile) if anchor else _nonface_identity(profile)
    body_only = "" if anchor else _body_only_authority()
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
        _special_region_authority(profile, spec),
        "keep every required boundary of the selected region inside the frame and keep unrelated regions outside the crop",
        _clean_phrase(suffix),
    )


def _common_extreme_specs() -> list[dict[str, Any]]:
    role = "OPTIONAL EXTREME CLINICAL VALIDATION ONLY — EXCLUDE FROM DEFAULT IDENTITY-LORA DATASET"
    rows = [
        ("clinical_extreme_navel_front", "extreme close direct-front clinical documentation of the existing navel and immediately surrounding abdomen", {"abdomen", "waist", "navel"}),
        ("clinical_extreme_navel_left_oblique", "extreme close left-oblique clinical documentation of the existing navel and abdominal surface transition", {"abdomen", "waist", "navel", "left_side_torso"}),
        ("clinical_extreme_navel_right_oblique", "extreme close right-oblique clinical documentation of the existing navel and abdominal surface transition", {"abdomen", "waist", "navel", "right_side_torso"}),
        ("clinical_extreme_gluteal_rear", "extreme close direct-rear clinical documentation of both buttocks, central cleft, lower-back transition, and both upper-thigh attachments", {"pelvis", "hips", "buttocks", "thigh"}),
        ("clinical_extreme_gluteal_rear_left", "extreme close rear-left three-quarter clinical documentation of the left gluteal contour and upper-thigh attachment", {"pelvis", "hips", "buttocks", "left_buttock", "left_thigh"}),
        ("clinical_extreme_gluteal_rear_right", "extreme close rear-right three-quarter clinical documentation of the right gluteal contour and upper-thigh attachment", {"pelvis", "hips", "buttocks", "right_buttock", "right_thigh"}),
        ("clinical_extreme_gluteal_left_profile", "extreme close anatomical left profile of the left gluteal contour, hip, and upper-thigh attachment", {"pelvis", "hips", "buttocks", "left_buttock", "left_thigh"}),
        ("clinical_extreme_gluteal_right_profile", "extreme close anatomical right profile of the right gluteal contour, hip, and upper-thigh attachment", {"pelvis", "hips", "buttocks", "right_buttock", "right_thigh"}),
        ("clinical_extreme_left_gluteal_fold", "neutral extreme close lower-rear documentation of the anatomical left gluteal fold and posterior upper-thigh attachment", {"buttocks", "left_buttock", "left_thigh"}),
        ("clinical_extreme_right_gluteal_fold", "neutral extreme close lower-rear documentation of the anatomical right gluteal fold and posterior upper-thigh attachment", {"buttocks", "right_buttock", "right_thigh"}),
        ("clinical_extreme_left_armpit", "neutral extreme close documentation of the anatomical left axillary fold with upper-arm and side-chest attachment", {"shoulders", "upper_arm", "left_upper_arm", "left_axilla"}),
        ("clinical_extreme_right_armpit", "neutral extreme close documentation of the anatomical right axillary fold with upper-arm and side-chest attachment", {"shoulders", "upper_arm", "right_upper_arm", "right_axilla"}),
        ("clinical_extreme_left_elbow_crease", "extreme close direct documentation of the anatomical left elbow crease and connected upper-arm and forearm surfaces", {"arms", "elbow", "left_elbow"}),
        ("clinical_extreme_right_elbow_crease", "extreme close direct documentation of the anatomical right elbow crease and connected upper-arm and forearm surfaces", {"arms", "elbow", "right_elbow"}),
        ("clinical_extreme_left_knee_joint", "extreme close direct-front clinical documentation of the anatomical left knee joint with minimum thigh and shin attachment", {"legs", "knee", "left_knee"}),
        ("clinical_extreme_right_knee_joint", "extreme close direct-front clinical documentation of the anatomical right knee joint with minimum thigh and shin attachment", {"legs", "knee", "right_knee"}),
    ]
    return [_spec(sid, "extreme_clinical_validation", desc, "clinical", regs, 1024, 1024, role) for sid, desc, regs in rows]


def _chest_extreme_specs(profile: dict[str, Any]) -> list[dict[str, Any]]:
    role = "OPTIONAL EXTREME CLINICAL VALIDATION ONLY — EXCLUDE FROM DEFAULT IDENTITY-LORA DATASET"
    resolved = _resolved_chest(profile)
    if resolved == "Masculine Chest — Use Male Chest Control":
        rows = [
            ("clinical_extreme_male_chest_front_complete", "extreme close direct-front clinical documentation of the complete adult male pectoral chest with both lateral boundaries, sternum, complete lower pectoral boundaries, and a small amount of upper abdomen", {"chest", "pectoral", "upper_torso", "sternum"}),
            ("clinical_extreme_male_chest_front_left", "extreme close front-left three-quarter clinical documentation of the adult male pectoral chest preserving pectoral volume and sternum relationship", {"chest", "pectoral", "upper_torso", "left_pectoral"}),
            ("clinical_extreme_male_chest_front_right", "extreme close front-right three-quarter clinical documentation of the adult male pectoral chest preserving pectoral volume and sternum relationship", {"chest", "pectoral", "upper_torso", "right_pectoral"}),
            ("clinical_extreme_left_pectoral_profile", "extreme close true anatomical left profile of the left pectoral chest with complete side contour and minimum rib attachment context", {"chest", "pectoral", "left_pectoral"}),
            ("clinical_extreme_right_pectoral_profile", "extreme close true anatomical right profile of the right pectoral chest with complete side contour and minimum rib attachment context", {"chest", "pectoral", "right_pectoral"}),
            ("clinical_extreme_left_pectoral_lower_boundary", "neutral extreme close lower-boundary view of the anatomical left pectoral chest with minimum upper-abdomen attachment", {"chest", "pectoral", "left_pectoral"}),
            ("clinical_extreme_right_pectoral_lower_boundary", "neutral extreme close lower-boundary view of the anatomical right pectoral chest with minimum upper-abdomen attachment", {"chest", "pectoral", "right_pectoral"}),
            ("clinical_extreme_left_male_nipple_areola_front", "neutral extreme close direct-front documentation of the existing anatomical left male nipple and surrounding areola only", {"chest", "pectoral", "left_pectoral", "left_nipple"}),
            ("clinical_extreme_right_male_nipple_areola_front", "neutral extreme close direct-front documentation of the existing anatomical right male nipple and surrounding areola only", {"chest", "pectoral", "right_pectoral", "right_nipple"}),
            ("clinical_extreme_sternum_pectoral_centerline", "extreme close direct-front clinical documentation of the sternum and central pectoral transition with both inner pectoral boundaries", {"chest", "pectoral", "sternum", "upper_torso"}),
        ]
    elif resolved == "Bust Anatomy — Use Bust Controls":
        rows = [
            ("clinical_extreme_bust_front_complete", "extreme close direct-front clinical documentation of the complete bust region with both lateral boundaries, sternum, complete lower contours, and a small amount of upper abdomen", {"chest", "breast", "upper_torso", "sternum"}),
            ("clinical_extreme_bust_front_left", "extreme close front-left three-quarter clinical documentation of the bust preserving complete projection and sternum relationship", {"chest", "breast", "upper_torso", "left_breast"}),
            ("clinical_extreme_bust_front_right", "extreme close front-right three-quarter clinical documentation of the bust preserving complete projection and sternum relationship", {"chest", "breast", "upper_torso", "right_breast"}),
            ("clinical_extreme_left_breast_profile", "extreme close true anatomical left profile of the left breast with complete side contour and minimum rib attachment context", {"chest", "breast", "left_breast"}),
            ("clinical_extreme_right_breast_profile", "extreme close true anatomical right profile of the right breast with complete side contour and minimum rib attachment context", {"chest", "breast", "right_breast"}),
            ("clinical_extreme_left_breast_lower_contour", "neutral extreme close lower-contour view of the anatomical left breast including the complete lower fold and minimum upper-abdomen attachment", {"chest", "breast", "left_breast"}),
            ("clinical_extreme_right_breast_lower_contour", "neutral extreme close lower-contour view of the anatomical right breast including the complete lower fold and minimum upper-abdomen attachment", {"chest", "breast", "right_breast"}),
            ("clinical_extreme_left_nipple_areola_front", "neutral extreme close direct-front documentation of the existing anatomical left nipple and surrounding areola only", {"chest", "breast", "left_breast", "left_nipple"}),
            ("clinical_extreme_right_nipple_areola_front", "neutral extreme close direct-front documentation of the existing anatomical right nipple and surrounding areola only", {"chest", "breast", "right_breast", "right_nipple"}),
            ("clinical_extreme_sternum_bust_centerline", "extreme close direct-front clinical documentation of the sternum and central bust transition with both inner chest boundaries", {"chest", "breast", "sternum", "upper_torso"}),
        ]
    else:
        noun = "flat neutral chest" if resolved == "Flat / Neutral Chest" else "configured custom chest"
        tag = "neutral_chest" if resolved == "Flat / Neutral Chest" else "custom_chest"
        rows = [
            ("clinical_extreme_selected_chest_front_complete", f"extreme close direct-front clinical documentation of the complete {noun} with both lateral boundaries, sternum, and lower chest boundary", {"chest", tag, "upper_torso", "sternum"}),
            ("clinical_extreme_selected_chest_left_profile", f"extreme close true anatomical left profile of the {noun} with natural rib attachment", {"chest", tag}),
            ("clinical_extreme_selected_chest_right_profile", f"extreme close true anatomical right profile of the {noun} with natural rib attachment", {"chest", tag}),
            ("clinical_extreme_left_nipple_areola_front", "neutral extreme close direct-front documentation of the existing anatomical left nipple and surrounding areola only", {"chest", tag, "left_nipple"}),
            ("clinical_extreme_right_nipple_areola_front", "neutral extreme close direct-front documentation of the existing anatomical right nipple and surrounding areola only", {"chest", tag, "right_nipple"}),
        ]
    return [_spec(sid, "extreme_clinical_validation", desc, "clinical", regs, 1024, 1024, role) for sid, desc, regs in rows]


def _groin_extreme_specs(profile: dict[str, Any]) -> list[dict[str, Any]]:
    role = "OPTIONAL EXTREME CLINICAL VALIDATION ONLY — EXCLUDE FROM DEFAULT IDENTITY-LORA DATASET"
    resolved = _resolved_groin(profile)
    if resolved == "Male External Anatomy":
        rows = [
            ("clinical_extreme_male_suprapubic_front", "neutral extreme close direct-front clinical documentation of the male suprapubic region and lower-abdomen transition", {"pelvis", "groin", "pubic", "suprapubic", "male_genital"}),
            ("clinical_extreme_male_genital_front", "neutral extreme close direct-front clinical documentation of the complete configured adult male external genital anatomy and natural pelvic attachment", {"pelvis", "groin", "male_genital"}),
            ("clinical_extreme_male_genital_front_left", "neutral extreme close front-left three-quarter clinical documentation of the configured adult male external genital anatomy and anatomical left groin transition", {"pelvis", "groin", "male_genital", "left_groin"}),
            ("clinical_extreme_male_genital_front_right", "neutral extreme close front-right three-quarter clinical documentation of the configured adult male external genital anatomy and anatomical right groin transition", {"pelvis", "groin", "male_genital", "right_groin"}),
            ("clinical_extreme_male_genital_left_profile", "neutral extreme close anatomical left profile of the configured adult male external genital anatomy and upper-inner-thigh attachment", {"pelvis", "groin", "male_genital", "left_groin", "left_thigh"}),
            ("clinical_extreme_male_genital_right_profile", "neutral extreme close anatomical right profile of the configured adult male external genital anatomy and upper-inner-thigh attachment", {"pelvis", "groin", "male_genital", "right_groin", "right_thigh"}),
            ("clinical_extreme_scrotal_lower_view", "neutral extreme close lower-angle clinical documentation of the scrotum, configured male external anatomy, and continuous upper-thigh attachment", {"pelvis", "groin", "male_genital", "perineal"}),
            ("clinical_extreme_male_perineal_rear_lower", "neutral extreme close rear-lower clinical documentation of the male perineal transition between the scrotal region and rear pelvis", {"pelvis", "groin", "male_genital", "perineal"}),
        ]
    elif resolved == "Female External Anatomy":
        rows = [
            ("clinical_extreme_female_pubic_mound_front", "neutral extreme close direct-front clinical documentation of the female pubic mound and lower-abdomen transition", {"pelvis", "groin", "pubic", "female_genital"}),
            ("clinical_extreme_female_external_front", "neutral extreme close direct-front clinical documentation of the configured adult female external genital anatomy and natural pelvic attachment", {"pelvis", "groin", "female_genital"}),
            ("clinical_extreme_female_external_front_left", "neutral extreme close front-left three-quarter clinical documentation of the configured adult female external genital anatomy and anatomical left groin transition", {"pelvis", "groin", "female_genital", "left_groin"}),
            ("clinical_extreme_female_external_front_right", "neutral extreme close front-right three-quarter clinical documentation of the configured adult female external genital anatomy and anatomical right groin transition", {"pelvis", "groin", "female_genital", "right_groin"}),
            ("clinical_extreme_female_external_left_profile", "neutral extreme close anatomical left profile of the configured adult female external genital anatomy and upper-inner-thigh attachment", {"pelvis", "groin", "female_genital", "left_groin", "left_thigh"}),
            ("clinical_extreme_female_external_right_profile", "neutral extreme close anatomical right profile of the configured adult female external genital anatomy and upper-inner-thigh attachment", {"pelvis", "groin", "female_genital", "right_groin", "right_thigh"}),
            ("clinical_extreme_female_lower_view", "neutral extreme close lower-angle clinical documentation of the configured adult female external anatomy and perineal attachment", {"pelvis", "groin", "female_genital", "perineal"}),
        ]
    elif resolved == "Custom Groin Anatomy":
        rows = [
            ("clinical_extreme_custom_groin_front", "neutral extreme close direct-front clinical documentation of the explicitly configured custom groin anatomy and natural pelvic attachment", {"pelvis", "groin", "custom_groin"}),
            ("clinical_extreme_custom_groin_front_left", "neutral extreme close front-left three-quarter clinical documentation of the explicitly configured custom groin anatomy", {"pelvis", "groin", "custom_groin", "left_groin"}),
            ("clinical_extreme_custom_groin_front_right", "neutral extreme close front-right three-quarter clinical documentation of the explicitly configured custom groin anatomy", {"pelvis", "groin", "custom_groin", "right_groin"}),
            ("clinical_extreme_custom_groin_left_profile", "neutral extreme close anatomical left profile of the explicitly configured custom groin anatomy", {"pelvis", "groin", "custom_groin", "left_groin"}),
            ("clinical_extreme_custom_groin_right_profile", "neutral extreme close anatomical right profile of the explicitly configured custom groin anatomy", {"pelvis", "groin", "custom_groin", "right_groin"}),
        ]
    else:
        rows = []
    return [_spec(sid, "extreme_clinical_validation", desc, "clinical", regs, 1024, 1024, role) for sid, desc, regs in rows]


def _extreme_specs(profile: dict[str, Any]) -> list[dict[str, Any]]:
    return _chest_extreme_specs(profile) + _groin_extreme_specs(profile) + _common_extreme_specs()


def _extreme_authority(profile: dict[str, Any], spec: dict[str, Any]) -> str:
    sid = str(spec.get("shot_id", "")).lower()
    parts = [
        "this is a neutral body-only extreme clinical validation image and not a portrait or scene photograph",
        "the selected region fills approximately sixty-five to eighty percent of the frame while retaining natural scale and rectilinear perspective",
        "increase camera distance instead of enlarging, flattening, shrinking, or distorting the anatomy",
        "the complete head, face, and all facial features remain outside the frame",
        "this optional validation record is not automatically approved for identity-LoRA training",
    ]
    if "nipple_areola" in sid:
        side = "left" if "left" in sid else "right"
        opposite = "right" if side == "left" else "left"
        parts.extend([
            f"exactly one existing anatomical {side} nipple and its surrounding areola are inside this one-sided crop",
            f"the anatomical {opposite} nipple remains outside the frame",
            "do not create an additional nipple, duplicated areola, extra opening, or mirrored second side",
        ])
    if any(token in sid for token in ("chest", "pectoral", "breast", "bust", "sternum")):
        parts.append(profile.get("chest_region_integrity_prompt", ""))
    if any(token in sid for token in ("male_genital", "female_external", "custom_groin", "pubic_mound", "suprapubic", "scrotal", "perineal")):
        parts.extend([
            profile.get("groin_anatomy_prompt", ""),
            profile.get("sex_anatomy_integrity_prompt", ""),
            profile.get("pubic_hair_prompt", ""),
        ])
    if "gluteal" in sid:
        parts.append("preserve the configured gluteal build, side, contour, fold, and natural upper-thigh attachment without exaggeration or reshaping")
    return _unique_sentences(*parts)


def _select_specs(plan: str, profile: dict[str, Any]) -> list[dict[str, Any]]:
    anchors = _anchor_specs()
    clothed = _copy_specs_for_profile(_regional_specs("clothed"), profile)
    clinical = _copy_specs_for_profile(_regional_specs("clinical"), profile)
    extreme = _extreme_specs(profile)
    if plan == KREA_BLUEPRINT_PLANS[0]:
        return anchors
    if plan == KREA_BLUEPRINT_PLANS[1]:
        return clothed
    if plan == KREA_BLUEPRINT_PLANS[2]:
        return clinical
    if plan == KREA_BLUEPRINT_PLANS[3]:
        return clothed + clinical
    if plan == KREA_BLUEPRINT_PLANS[4]:
        return extreme
    return anchors + clothed + clinical


class FCCKreaBlueprintDatasetDirector:
    CATEGORY = "character creation/studio"
    FUNCTION = "direct"
    DESCRIPTION = (
        "Stage 2 Krea2 pre-LoRA director with anatomy-conditioned regional and extreme-clinical manifests. Chest and groin items follow independently resolved selections, including Adult Nonbinary combinations; leg and foot records never inherit groin text."
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
            "optional": {"prompt_suffix": ("STRING", {"default": "", "multiline": True})},
        }

    def direct(self, character_blueprint, dataset_plan, project_name, starting_seed, variations_per_shot, prompt_suffix=""):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan_name = str(dataset_plan)
        specs = _select_specs(plan_name, profile)
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
                if spec.get("category") == "extreme_clinical_validation":
                    prompt = _unique_sentences(prompt, _extreme_authority(profile, spec))
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
                    "optional_validation_only": spec["category"] == "extreme_clinical_validation",
                    "resolved_chest_anatomy": _resolved_chest(profile),
                    "resolved_groin_anatomy": _resolved_groin(profile),
                    "male_genital_state": profile.get("male_genital_state", "Not applicable"),
                    "prompt": prompt,
                })
        total = len(manifest)
        progress = [f"{item['index']} of {total} | {item['category']} | {item['shot_id']}" for item in manifest]
        plan_json = json.dumps({
            "schema": "FCC_KREA_STAGE2_REGIONAL_ATLAS_V256",
            "schema_version": 6,
            "character_id": profile.get("character_id", "character"),
            "dataset_plan": plan_name,
            "total_items": total,
            "resolved_chest_anatomy": _resolved_chest(profile),
            "resolved_groin_anatomy": _resolved_groin(profile),
            "male_genital_state": profile.get("male_genital_state", "Not applicable"),
            "body_only_rule": "All non-anchor Stage 2 regional and extreme-clinical records exclude the complete face and facial features.",
            "anatomy_area_rule": "Chest and groin records follow their independently resolved anatomy selections; Adult Nonbinary identity does not override either selected anatomy area.",
            "lower_limb_rule": "Thigh, knee, shin, calf, ankle, foot, and sole records use lower-body silhouette only and do not receive groin or pubic-hair text.",
            "extreme_clinical_rule": "Extreme Clinical Body Validation is opt-in only, anatomy-conditioned, stored separately, and excluded from the Complete Pre-LoRA plan and default identity-LoRA selection.",
            "manual_review": "Every generated image requires manual approval.",
            "items": manifest,
        }, indent=2, ensure_ascii=False)
        preview = "\n".join(
            f"{item['index']:03d} | {item['category']} | {item['shot_id']} | {item['width']}x{item['height']}"
            for item in manifest
        )
        dashboard = "\n".join([
            "FCC STAGE 2 — KREA PRE-LORA DOCUMENTATION V2.4.16",
            f"Character: {profile.get('character_id', 'character')}",
            f"Plan: {plan_name}",
            f"Resolved chest: {_resolved_chest(profile)}",
            f"Resolved groin: {_resolved_groin(profile)}",
            f"Male genital state: {profile.get('male_genital_state', 'Not applicable')}",
            f"Total queued items: {total}",
            "IDENTITY ANCHORS: face-visible only in the dedicated anchor plan.",
            "BODY ATLAS: every regional record excludes the complete face.",
            "ANATOMY LOCKS: chest and groin follow their independent resolved selections.",
            "EXTREME CLINICAL: opt-in validation only; never silently added to LoRA training.",
        ])
        return prompts, seeds, shot_ids, categories, prefixes, widths, heights, plan_json, preview, dashboard, progress


class FCCFaceAngleDatasetDirector(FCCFaceAngleDatasetDirectorV255):
    DESCRIPTION = (
        "Stage 3 Qwen Image Edit angle-completion director registered to V2.4.16. Approved references retain the anatomy actually present in the source; every output remains manually reviewed."
    )

    def direct(self, *args, **kwargs):
        result = list(super().direct(*args, **kwargs))
        try:
            plan = json.loads(result[7]) if result[7] else {}
        except Exception:
            plan = {}
        plan["schema"] = "FCC_QWEN_STAGE3_ANGLE_EXPANSION_V256"
        plan["schema_version"] = 6
        plan["anatomy_rule"] = "Use an approved Stage 2 reference matching the intended anatomy and crop; Qwen preserves rather than invents the documented region."
        result[7] = json.dumps(plan, indent=2, ensure_ascii=False)
        return tuple(result)
