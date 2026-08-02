import json

from full_character_creation_core import NODE_CLASS_MAPPINGS
from full_character_creation_core.src.nodes_v256 import (
    CharacterBlueprintCreatorV256,
    CharacterShotControlV256,
    CharacterPromptAssemblerV256,
    MALE_GENITAL_STATES_V256,
)
from full_character_creation_core.src.dataset_v256 import (
    FCCKreaBlueprintDatasetDirector,
    KREA_BLUEPRINT_PLANS,
)


def _defaults(cls):
    values = {}
    for section in ("required", "optional"):
        for name, spec in cls.INPUT_TYPES().get(section, {}).items():
            if name in {"character_blueprint", "shot_plan"}:
                continue
            kind = spec[0]
            cfg = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}
            if "default" in cfg:
                values[name] = cfg["default"]
            elif isinstance(kind, list):
                values[name] = kind[0]
            elif kind == "STRING":
                values[name] = ""
            elif kind == "INT":
                values[name] = 0
            elif kind == "FLOAT":
                values[name] = 0.0
            elif kind == "BOOLEAN":
                values[name] = False
            else:
                values[name] = ""
    return values


def _profile(**updates):
    values = _defaults(CharacterBlueprintCreatorV256)
    values.update({"tattoo_status": "None", "piercing_status": "None"})
    values.update(updates)
    return CharacterBlueprintCreatorV256().build_blueprint_v256(**values)[8]


def test_v256_registry_current_only():
    assert "CharacterBlueprintCreatorV260" in NODE_CLASS_MAPPINGS
    assert "CharacterShotControlV260" in NODE_CLASS_MAPPINGS
    assert "CharacterPromptAssemblerV260" in NODE_CLASS_MAPPINGS
    assert not any(name.endswith("V255") for name in NODE_CLASS_MAPPINGS)


def test_male_genital_state_is_directly_below_foreskin_status():
    names = list(CharacterBlueprintCreatorV256.INPUT_TYPES()["required"])
    assert names.index("male_genital_state") == names.index("male_foreskin_status") + 1
    spec = CharacterBlueprintCreatorV256.INPUT_TYPES()["required"]["male_genital_state"]
    assert spec[0] == MALE_GENITAL_STATES_V256
    assert spec[1]["default"] == "Unspecified — Do Not Force"


def test_adult_man_auto_match_contains_only_male_anatomy_terms():
    profile = _profile(
        primary_character_gender="Adult Man",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
        pubic_hair_style="Fine Trimmed",
        male_genital_size="Average",
    )
    text = profile["clinical_character_prompt"].lower()
    assert profile["resolved_chest_anatomy"] == "Masculine Chest — Use Male Chest Control"
    assert profile["resolved_groin_anatomy"] == "Male External Anatomy"
    assert "one penis and one scrotum" in text
    assert "male suprapubic" in text
    assert "non-aroused" not in text
    for forbidden in ("female external", "breast", "bust", "mons pubis", "pubic mound", "vulva", "labia", "vaginal"):
        assert forbidden not in text


def test_male_genital_state_options_are_source_gated():
    unspecified = _profile(primary_character_gender="Adult Man", visible_presentation_mode="Clinical Anatomy — No Clothing")
    assert "flaccid" not in unspecified["groin_anatomy_prompt"].lower()
    assert "erect" not in unspecified["groin_anatomy_prompt"].lower()

    flaccid = _profile(
        primary_character_gender="Adult Man",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
        male_genital_state="Non-Aroused / Flaccid",
    )
    assert "natural flaccid state" in flaccid["groin_anatomy_prompt"].lower()

    erect = _profile(
        primary_character_gender="Adult Man",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
        male_genital_state="Aroused / Erect",
    )
    assert "natural erect state" in erect["groin_anatomy_prompt"].lower()

    female = _profile(
        primary_character_gender="Adult Woman",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
        male_genital_state="Aroused / Erect",
    )
    assert female["male_genital_state"] == "Not applicable"
    assert "erect" not in female["clinical_character_prompt"].lower()


def test_nonbinary_explicit_anatomy_areas_are_independently_locked():
    mixed_a = _profile(
        primary_character_gender="Adult Nonbinary",
        chest_anatomy="Masculine Chest — Use Male Chest Control",
        groin_anatomy="Female External Anatomy",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
        pubic_hair_style="Natural Average",
    )
    text_a = mixed_a["clinical_character_prompt"].lower()
    assert mixed_a["resolved_chest_anatomy"] == "Masculine Chest — Use Male Chest Control"
    assert mixed_a["resolved_groin_anatomy"] == "Female External Anatomy"
    assert "adult male pectoral anatomy" in text_a
    assert "adult female external genital anatomy" in text_a
    assert "male suprapubic" not in text_a

    mixed_b = _profile(
        primary_character_gender="Adult Nonbinary",
        chest_anatomy="Bust Anatomy — Use Bust Controls",
        groin_anatomy="Male External Anatomy",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
        pubic_hair_style="Natural Average",
        bust_size="Medium",
    )
    text_b = mixed_b["clinical_character_prompt"].lower()
    assert mixed_b["resolved_chest_anatomy"] == "Bust Anatomy — Use Bust Controls"
    assert mixed_b["resolved_groin_anatomy"] == "Male External Anatomy"
    assert "selected chest has adult bust anatomy" in text_b
    assert "one penis and one scrotum" in text_b
    assert "male suprapubic" in text_b


def test_stage2_male_extreme_manifest_is_anatomy_conditioned():
    profile = _profile(
        primary_character_gender="Adult Man",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
        pubic_hair_style="Fine Trimmed",
        male_genital_state="Non-Aroused / Flaccid",
    )
    out = FCCKreaBlueprintDatasetDirector().direct(
        profile, "Extreme Clinical Body Validation — Opt-In Only", "MaleTest", 3000, 1, ""
    )
    all_text = "\n".join(out[0]).lower()
    shot_ids = out[2]
    assert any("male_genital_front" in sid for sid in shot_ids)
    assert any("scrotal_lower" in sid for sid in shot_ids)
    assert any("male_chest_front" in sid for sid in shot_ids)
    assert not any("breast" in sid or "pubic_mound" in sid for sid in shot_ids)
    for forbidden in ("breast", "bust", "mons pubis", "pubic mound", "female external", "non-aroused"):
        assert forbidden not in all_text
    plan = json.loads(out[7])
    assert plan["schema"] == "FCC_KREA_STAGE2_REGIONAL_ATLAS_V256"
    assert plan["resolved_groin_anatomy"] == "Male External Anatomy"


def test_stage2_leg_hand_and_foot_prompts_do_not_inherit_groin_or_torso_anatomy():
    profile = _profile(
        primary_character_gender="Adult Man",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
        pubic_hair_style="Full Natural",
    )
    out = FCCKreaBlueprintDatasetDirector().direct(
        profile, "Body-Only Regional Atlas — Clinical Unclothed", "MaleTest", 2000, 1, ""
    )
    mapping = dict(zip(out[2], out[0]))
    targets = [
        next(value for key, value in mapping.items() if "left_thigh_front" in key),
        next(value for key, value in mapping.items() if "left_palm" in key),
        next(value for key, value in mapping.items() if "left_foot_dorsal" in key),
    ]
    for prompt in targets:
        low = prompt.lower()
        assert "penis" not in low
        assert "scrotum" not in low
        assert "pubic-hair" not in low
        assert "suprapubic" not in low
    palm = targets[1].lower()
    assert "pectoral" not in palm
    assert "sternum" not in palm
    foot = targets[2].lower()
    assert "masculine waist" not in foot
    assert "gluteal build" not in foot


def test_stage2_female_and_nonbinary_routes_do_not_inherit_male_state():
    female = _profile(
        primary_character_gender="Adult Woman",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
        male_genital_state="Aroused / Erect",
    )
    out = FCCKreaBlueprintDatasetDirector().direct(
        female, "Extreme Clinical Body Validation — Opt-In Only", "FemaleTest", 4000, 1, ""
    )
    text = "\n".join(out[0]).lower()
    assert "female_external" in "\n".join(out[2]).lower()
    assert "erect" not in text
    assert "one penis and one scrotum" not in text

    neutral = _profile(
        primary_character_gender="Adult Nonbinary",
        chest_anatomy="Flat / Neutral Chest",
        groin_anatomy="Unspecified — Do Not Describe",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
    )
    out2 = FCCKreaBlueprintDatasetDirector().direct(
        neutral, "Extreme Clinical Body Validation — Opt-In Only", "NeutralTest", 5000, 1, ""
    )
    assert not any("genital" in sid or "groin" in sid or "scrotal" in sid or "pubic_mound" in sid for sid in out2[2])


def test_previous_v255_floor_pose_behavior_remains_registered_through_v256():
    creator_values = _defaults(CharacterBlueprintCreatorV256)
    profile = CharacterBlueprintCreatorV256().build_blueprint_v256(**creator_values)[8]
    shot_values = _defaults(CharacterShotControlV256)
    shot_values.update({
        "shot_type": "Three-Quarter Body",
        "camera_view": "Back View",
        "camera_height": "Eye Level",
        "pose": "All Fours — Hands and Knees (Solo)",
        "lens": "50mm Normal",
        "aspect_ratio": "Auto by Shot",
    })
    plan = CharacterShotControlV256().build_shot_plan_v256(character_blueprint=profile, **shot_values)[0]
    assert "six-o'clock position directly behind the sacrum" in plan["camera_prompt"].lower()
    assert "zero downward tilt" in plan["camera_prompt"].lower()


def test_stage0_extended_puppy_male_prompt_contains_positive_male_geometry_lock():
    from full_character_creation_core.src.nodes_v245 import EXTENDED_PUPPY

    profile = _profile(
        primary_character_gender="Adult Man",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
        pubic_hair_style="Fine Trimmed",
    )
    values = _defaults(CharacterShotControlV256)
    values.update({
        "shot_type": "Three-Quarter Body",
        "camera_view": "Back View",
        "camera_height": "Eye Level",
        "pose": EXTENDED_PUPPY,
        "lens": "50mm Normal",
        "aspect_ratio": "Auto by Shot",
    })
    plan = CharacterShotControlV256().build_shot_plan_v256(character_blueprint=profile, **values)[0]
    prompt = CharacterPromptAssemblerV256().assemble_prompt_v256(
        profile, plan, "Krea — Standard Generation", "Image 1"
    )[0].lower()
    assert "one anatomically male pelvis has exactly one penis and one scrotum" in prompt
    assert "male perineal anatomy remains continuous toward the rear pelvis" in prompt
    assert "female external" not in prompt
    assert "mons pubis" not in prompt


def test_nonbinary_all_explicit_chest_groin_combinations_remain_area_locked():
    chest_options = CharacterBlueprintCreatorV256.INPUT_TYPES()["required"]["chest_anatomy"][0]
    groin_options = CharacterBlueprintCreatorV256.INPUT_TYPES()["required"]["groin_anatomy"][0]
    for chest in chest_options:
        for groin in groin_options:
            profile = _profile(
                primary_character_gender="Adult Nonbinary",
                chest_anatomy=chest,
                groin_anatomy=groin,
                custom_chest_description="a deliberately custom neutral chest configuration",
                custom_groin_anatomy="a deliberately custom adult groin configuration",
                visible_presentation_mode="Clinical Anatomy — No Clothing",
                male_genital_state="Aroused / Erect",
                pubic_hair_style="Natural Average",
            )
            text = profile["clinical_character_prompt"].lower()
            resolved_chest = profile["resolved_chest_anatomy"]
            resolved_groin = profile["resolved_groin_anatomy"]
            assert profile["primary_character_gender"] == "Adult Nonbinary"

            if resolved_chest == "Masculine Chest — Use Male Chest Control":
                assert "adult male pectoral anatomy" in text
                assert "selected chest has adult bust anatomy" not in text
            elif resolved_chest == "Bust Anatomy — Use Bust Controls":
                assert "selected chest has adult bust anatomy" in text
                assert "adult male pectoral anatomy" not in text
            elif resolved_chest == "Flat / Neutral Chest":
                assert "selected chest remains flat and neutral" in text
                assert "adult male pectoral anatomy" not in text
                assert "selected chest has adult bust anatomy" not in text
            elif resolved_chest == "Custom Chest Description":
                assert "deliberately custom neutral chest configuration" in text
                assert "preserve the explicitly configured custom chest anatomy" in text

            if resolved_groin == "Male External Anatomy":
                assert "one penis and one scrotum" in text
                assert "natural erect state" in text
                assert "adult female external genital anatomy" not in text
            elif resolved_groin == "Female External Anatomy":
                assert "adult female external genital anatomy" in text
                assert "one penis and one scrotum" not in text
                assert "natural erect state" not in text
            elif resolved_groin == "Unspecified — Do Not Describe":
                assert "one penis and one scrotum" not in text
                assert "adult female external genital anatomy" not in text
                assert "natural erect state" not in text
            elif resolved_groin == "Custom Groin Anatomy":
                assert "deliberately custom adult groin configuration" in text
                assert "preserve the explicitly configured custom groin anatomy" in text
                assert "natural erect state" not in text


def test_v256_blueprint_json_exports_selected_and_effective_male_state():
    values = _defaults(CharacterBlueprintCreatorV256)
    values.update({
        "primary_character_gender": "Adult Nonbinary",
        "groin_anatomy": "Male External Anatomy",
        "male_genital_state": "Non-Aroused / Flaccid",
        "visible_presentation_mode": "Clinical Anatomy — No Clothing",
        "tattoo_status": "None",
        "piercing_status": "None",
    })
    result = CharacterBlueprintCreatorV256().build_blueprint_v256(**values)
    exported = json.loads(result[15])
    assert exported["schema"] == "CHARACTER_BLUEPRINT_V256"
    assert exported["male_genital_state_selection"] == "Non-Aroused / Flaccid"
    assert exported["male_genital_state"] == "Non-Aroused / Flaccid"
    assert exported["resolved_anatomy_area_locks"]["identity"] == "Adult Nonbinary"
    assert exported["resolved_anatomy_area_locks"]["groin"] == "Male External Anatomy"
