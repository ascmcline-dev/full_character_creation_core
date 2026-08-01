from full_character_creation_core.src.nodes_v246 import (
    CharacterBlueprintCreatorV246,
    CharacterPromptAssemblerV246,
    CharacterShotControlV246,
)


def _defaults(cls):
    out = {}
    for name, spec in cls.INPUT_TYPES()["required"].items():
        if name == "character_blueprint":
            continue
        kind = spec[0]
        options = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}
        if "default" in options:
            out[name] = options["default"]
        elif isinstance(kind, list):
            out[name] = kind[0]
        elif kind == "STRING":
            out[name] = ""
        elif kind == "INT":
            out[name] = 0
        elif kind == "FLOAT":
            out[name] = 0.0
        elif kind == "BOOLEAN":
            out[name] = False
        else:
            out[name] = ""
    return out


def _profile(preset):
    kwargs = _defaults(CharacterBlueprintCreatorV246)
    kwargs.update({
        "visible_presentation_mode": "Clothed — Use Outfit Controls",
        "outfit_input_method": "Preset — Ready-Made Complete Outfit",
        "preset_outfit_if_selected": preset,
        "tattoo_status": "None",
        "piercing_status": "None",
    })
    return CharacterBlueprintCreatorV246().build_blueprint_v246(**kwargs)[8]


def _shot(profile, shot_type="Waist-Up Midshot"):
    kwargs = _defaults(CharacterShotControlV246)
    kwargs.update({
        "shot_type": shot_type,
        "aspect_ratio": "Auto by Shot",
        "photo_style": "Raw Instagram / Unfiltered Social Snapshot",
    })
    return CharacterShotControlV246().build_shot_plan_v246(character_blueprint=profile, **kwargs)[0]


def _assemble(profile, shot):
    return CharacterPromptAssemblerV246().assemble_prompt_v246(
        profile, shot, "Krea — First Identity Image", "Image 1"
    )


def test_high_hem_is_complete_garment():
    profile = _profile("High-Hem Crop Top and Daisy Dukes")
    result = _assemble(profile, _shot(profile))
    prompt = result[13]
    assert "complete sewn tank-style garment" in prompt
    assert "continuous front and back fabric panels" in prompt
    assert "entire bust is enclosed inside the opaque fabric panel" in prompt
    assert "lower-bust edge" not in prompt
    assert "immediately beneath the bust line" not in prompt


def test_waist_up_keeps_daisy_dukes():
    profile = _profile("High-Hem Crop Top and Daisy Dukes")
    result = _assemble(profile, _shot(profile))
    presentation = result[3]
    assert "Daisy Duke" in presentation
    assert "waistband and upper portion are clearly visible" in presentation


def test_waist_up_keeps_jeans():
    profile = _profile("Casual Jeans and T-Shirt")
    result = _assemble(profile, _shot(profile))
    presentation = result[3]
    assert "casual fitted T-shirt" in presentation
    assert "well-fitted jeans" in presentation
    assert "waistband and upper portion are clearly visible" in presentation


def test_clothing_precedes_body_language():
    profile = _profile("High-Hem Crop Top and Daisy Dukes")
    result = _assemble(profile, _shot(profile))
    prompt = result[13]
    garment_index = prompt.index("wearing a complete coordinated outfit")
    body_index = prompt.find("shoulder and upper-torso silhouette")
    assert body_index < 0 or garment_index < body_index


def test_chest_up_does_not_force_bottom():
    profile = _profile("Casual Jeans and T-Shirt")
    result = _assemble(profile, _shot(profile, "Chest-Up"))
    presentation = result[3]
    assert "casual fitted T-shirt" in presentation
    assert "well-fitted jeans" not in presentation
