import json

from full_character_creation_core import NODE_CLASS_MAPPINGS
from full_character_creation_core.src.nodes_v260 import (
    CharacterBlueprintCreatorV260,
    CharacterPromptAssemblerV260,
    CharacterShotControlV260,
)
from full_character_creation_core.src.dataset_v260 import (
    FCCKreaBlueprintDatasetDirector,
    KREA_BLUEPRINT_PLANS,
)


def defaults(cls):
    values = {}
    for name, spec in cls.INPUT_TYPES()["required"].items():
        kind = spec[0]
        options = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}
        if isinstance(kind, list):
            values[name] = options.get("default", kind[0])
        elif kind == "STRING":
            values[name] = options.get("default", "")
        else:
            values[name] = options.get("default", 0)
    return values


def profile(**updates):
    kwargs = defaults(CharacterBlueprintCreatorV260)
    kwargs.update(updates)
    return CharacterBlueprintCreatorV260().build_blueprint_v260(**kwargs)[8]


def plan(p=None, **updates):
    kwargs = defaults(CharacterShotControlV260)
    if p is not None:
        kwargs["character_blueprint"] = p
    kwargs.update(updates)
    return CharacterShotControlV260().build_shot_plan_v260(**kwargs)[0]


def assemble(p, s):
    return CharacterPromptAssemblerV260().assemble_prompt_v260(
        p, s, "Krea — First Identity Image", "Image 1"
    )


def test_registry_current_v260_only():
    assert "CharacterBlueprintCreatorV260" in NODE_CLASS_MAPPINGS
    assert "CharacterShotControlV260" in NODE_CLASS_MAPPINGS
    assert "CharacterPromptAssemblerV260" in NODE_CLASS_MAPPINGS
    assert "CharacterBlueprintCreatorV259" not in NODE_CLASS_MAPPINGS


def test_stage0_extreme_macro_bypasses_full_character_and_room_context():
    p = profile(
        chest_anatomy="Flat / Neutral Chest",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
        tattoo_status="None",
        piercing_status="None",
    )
    s = plan(p, shot_type="Extreme Close-Up — Single Detail", extreme_closeup_focus="Left Nipple and Areola")
    assert s["native_macro"] is True
    assert s["pose_prompt"] == ""
    assert "room context" in s["environment_prompt"].lower()
    result = assemble(p, s)
    prompt = result[0].lower()
    assert "native clinical macro photograph" in prompt
    assert "exactly one anatomical-left nipple" in prompt
    assert "source magnification" in prompt
    assert "visible pores" in prompt
    assert "documented local skin is naturally unmarked" in prompt
    assert "below average height" not in prompt
    assert "standing upright" not in prompt
    assert "surrounding environment remains" not in prompt
    assert "shelves, bottles, signs" not in prompt
    assert "full body" not in prompt


def test_stage0_macro_emits_only_intersecting_marks():
    p = profile(
        chest_anatomy="Bust Anatomy — Use Bust Controls",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
        tattoo_status="One",
        tattoo_input_mode="Structured Single Tattoo",
        structured_tattoo_location="Left Front Pelvic Bone / Groin Line",
        structured_tattoo_description="small hummingbird",
    )
    s = plan(p, shot_type="Extreme Close-Up — Single Detail", extreme_closeup_focus="Left Nipple and Areola")
    result = assemble(p, s)
    sections = json.loads(result[18])
    assert sections["visible_tattoo_records"] == []
    assert "hummingbird" not in result[0].lower()


def test_stage2_flat_chest_has_left_and_right_nipple_macros_and_native_prompts():
    p = profile(
        chest_anatomy="Flat / Neutral Chest",
        groin_anatomy="Unspecified — Do Not Describe",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
        tattoo_status="None",
        piercing_status="None",
    )
    out = FCCKreaBlueprintDatasetDirector().direct(p, KREA_BLUEPRINT_PLANS[4], "Test", 2000, 1, "")
    data = json.loads(out[7])
    assert data["schema"] == "FCC_KREA_STAGE2_CANONICAL_ATLAS_V260"
    ids = [item["shot_id"] for item in data["items"]]
    assert any("extreme_left_nipple_areola" in sid for sid in ids)
    assert any("extreme_right_nipple_areola" in sid for sid in ids)
    assert not any("groin" in sid or "genital" in sid or "pubic" in sid for sid in ids)
    left = next(item for item in data["items"] if "extreme_left_nipple_areola" in item["shot_id"])
    prompt = left["prompt"].lower()
    assert left["native_macro"] is True
    assert left["macro_compiler"] == "FCC_NATIVE_CLINICAL_MACRO_V260"
    assert "exactly one anatomical-left nipple" in prompt
    assert "source magnification" in prompt
    assert "pores" in prompt
    assert "full person" not in prompt
    assert "below average height" not in prompt
    assert "shoulder-length" not in prompt


def test_stage2_external_anatomy_macro_uses_local_only_authority_and_intersecting_marks():
    p = profile(
        groin_anatomy="Female External Anatomy",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
        tattoo_status="One",
        tattoo_input_mode="Structured Single Tattoo",
        structured_tattoo_location="Right Forearm",
        structured_tattoo_description="orchid",
    )
    out = FCCKreaBlueprintDatasetDirector().direct(p, KREA_BLUEPRINT_PLANS[4], "Test", 2000, 1, "")
    data = json.loads(out[7])
    front = next(item for item in data["items"] if "female_external_front" in item["shot_id"])
    prompt = front["prompt"].lower()
    assert "adult female external anatomy" in prompt
    assert "source magnification" in prompt
    assert "orchid" not in prompt
    assert "below average height" not in prompt
    assert "complete pelvis" not in prompt
    assert "documented local skin is naturally unmarked" in prompt


def test_stage2_gluteal_fold_is_native_single_surface_not_regional_body():
    p = profile(visible_presentation_mode="Clinical Anatomy — No Clothing")
    out = FCCKreaBlueprintDatasetDirector().direct(p, KREA_BLUEPRINT_PLANS[4], "Test", 2000, 1, "")
    data = json.loads(out[7])
    item = next(item for item in data["items"] if "left_gluteal_fold" in item["shot_id"])
    prompt = item["prompt"].lower()
    assert "posterior gluteal fold" in prompt
    assert "ninety to ninety-five percent" in prompt
    assert "source magnification" in prompt
    assert "full person" not in prompt
