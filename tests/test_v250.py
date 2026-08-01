import json

from full_character_creation_core.src.nodes_v250 import (
    CharacterBlueprintCreatorV250,
    CharacterPromptAssemblerV250,
    CharacterShotControlV250,
)


def _defaults(cls):
    values = {}
    for name, spec in cls.INPUT_TYPES()["required"].items():
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


def _assemble(skin_tone="Light", tan_profile="None"):
    ckw = _defaults(CharacterBlueprintCreatorV250)
    ckw.update({
        "skin_tone": skin_tone,
        "tan_profile": tan_profile,
        "tattoo_status": "None",
        "piercing_status": "None",
        "visible_presentation_mode": "Clothed — Use Outfit Controls",
        "outfit_input_method": "Preset — Ready-Made Complete Outfit",
        "preset_outfit_if_selected": "Simple Dress",
    })
    profile = CharacterBlueprintCreatorV250().build_blueprint_v250(**ckw)[8]

    skw = _defaults(CharacterShotControlV250)
    skw.update({
        "shot_type": "Full Body",
        "camera_view": "Back View",
        "pose": "Neutral Standing",
        "lens": "Auto by Shot — Recommended",
        "aspect_ratio": "Auto by Shot",
    })
    plan = CharacterShotControlV250().build_shot_plan_v250(character_blueprint=profile, **skw)[0]
    result = CharacterPromptAssemblerV250().assemble_prompt_v250(
        profile, plan, "Krea — First Identity Image", "Image 1"
    )
    return profile, plan, result


def test_light_skin_with_no_tan_gets_positive_base_complexion_lock():
    profile, _, result = _assemble("Light", "None")
    prompt = result[0].lower()
    sections = json.loads(result[18])
    skin = sections["visible_tan_skin_variation"].lower()
    assert profile["base_complexion_stability_prompt"]
    assert "naturally light fair complexion" in skin
    assert "consistent light underlying coloration" in skin
    assert "ambient warmth or coolness affects illumination only" in skin
    assert "tan line" not in skin
    assert "tan-line" not in skin
    assert "naturally light fair complexion" in prompt


def test_very_light_skin_with_no_tan_is_distinct_from_light():
    _, _, light = _assemble("Light", "None")
    _, _, very_light = _assemble("Very Light", "None")
    assert "naturally light fair complexion" in light[0].lower()
    assert "naturally very light fair complexion" in very_light[0].lower()


def test_selected_tan_profile_keeps_existing_tan_route_without_base_lock():
    profile, _, result = _assemble("Light", "Medium Tan — Even")
    prompt = result[0].lower()
    sections = json.loads(result[18])
    assert profile["base_complexion_stability_prompt"] == ""
    assert "uniform medium tan" in sections["visible_tan_skin_variation"].lower()
    assert "ambient warmth or coolness affects illumination only" not in prompt


def test_v249_open_section_fixes_are_inherited():
    _, plan, result = _assemble("Light", "None")
    prompt = result[0].lower()
    assert plan["schema"] == "FCC_SHOT_PLAN_V250"
    assert "one complete opaque one-piece dress" in prompt
    assert "full rear fabric panels" in prompt
    assert "upper-body garment" not in prompt
