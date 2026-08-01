import { app } from "../../scripts/app.js";

const CREATOR_LABELS = {
    primary_character_gender: "Primary Character Gender", age_range: "Age Range", custom_heritage: "Custom Heritage",
    skin_tone: "Skin Tone", tan_profile: "Tan Level / Tan-Line Mode", tan_line_pattern: "Tan-Line Pattern",
    tan_line_visibility: "Tan-Line Strength — Subtle Is Barely Visible", custom_tan_description: "Custom Tan / Tan-Line Description",
    face_shape: "Face Shape", jaw_shape: "Jaw Shape", chin_shape: "Chin Shape", eye_color: "Eye Color",
    eye_shape: "Eye Shape", eyebrow_shape: "Eyebrow Shape", nose_shape: "Nose Shape", lip_shape: "Lip Shape",
    hair_color: "Hair Color", custom_hair_color: "Custom Hair Color", hair_highlights: "Hair Highlights / Accent Colors — Optional",
    hair_length: "Hair Length / Cut", custom_hair_length: "Custom Hair Length / Cut", hair_texture: "Hair Texture",
    custom_hair_texture: "Custom Hair Texture", hair_style: "Hair Styling", custom_hair_style: "Custom Hair Styling",
    facial_hair: "Facial Hair", custom_facial_hair: "Custom Facial Hair", body_type: "Overall Body Build",
    buttocks: "Gluteal Build", chest_anatomy: "Chest Anatomy Source", male_chest: "Masculine Chest Build",
    custom_chest_description: "Custom Chest Description", bust_size: "Bust Size",
    bust_shape: "Breast Shape — Base / Projection / Spacing", bust_position: "Bust Position — Vertical Placement on Torso",
    bust_firmness: "Bust Firmness", bust_augmentation: "Bust Augmentation — Projection / Upper Fullness Effect",
    groin_anatomy: "Groin Anatomy Source", male_genital_size: "Male Genital Size", male_foreskin_status: "Circumcision / Foreskin",
    custom_groin_anatomy: "Custom Groin Anatomy", pubic_hair_style: "Pubic Hair Grooming",
    custom_pubic_hair_style: "Custom Pubic Hair Grooming", use_advanced_lower_body_notes: "Use Advanced Lower-Body Notes",
    advanced_lower_body_notes: "Advanced Lower-Body Notes", visible_presentation_mode: "Visible Presentation / Clothing State",
    custom_mode_body_detail: "Body Detail Used with Custom Presentation", custom_presentation_text: "Custom Presentation Description",
    outfit_input_method: "Outfit Source — Preset / Exact Text / Build Garments",
    preset_outfit_if_selected: "Preset Outfit — Ready-Made Clothing Only", exact_outfit_text: "Exact Complete Outfit",
    structured_outfit_layout: "Build Outfit Layout — Used Only with Build Garments", structured_top: "Top",
    structured_bottom: "Bottom", structured_footwear: "Footwear", structured_outerwear: "Outerwear",
    structured_one_piece: "One-Piece Garment", structured_swimwear_top: "Swimwear Top",
    structured_swimwear_bottom: "Swimwear Bottom", lingerie_style_if_selected: "Lingerie Style",
    custom_lingerie_description: "Custom Lingerie Description", outfit_notes: "Additional Outfit Notes",
    removable_jewelry: "Removable Jewelry Level", removable_jewelry_description: "Removable Jewelry Description",
    tattoo_status: "Tattoo Count / Status", tattoo_input_mode: "One Tattoo Entry Method",
    tattoo_descriptors: "Tattoo Descriptions — One Per Line", structured_tattoo_location: "Single Tattoo Location",
    structured_tattoo_description: "Single Tattoo Design / Details", piercing_status: "Piercings — None / One / Multiple",
    piercing_input_mode: "One Piercing Entry Method", piercing_descriptors: "Piercing Descriptions — One Per Line",
    piercing_location: "Single Piercing Location", piercing_type: "Single Piercing Jewelry Type",
    piercing_material: "Single Piercing Material", piercing_visibility: "Single Piercing Visibility",
    structured_piercing_custom: "Custom Piercing Detail — Only for Other / Custom", custom_identity_notes: "Additional Identity Notes",
};

const SHOT_LABELS = {
    planner_mode: "Shot Planning Mode", custom_shot_direction: "Complete Custom Shot Direction", scene_cast: "People in Scene",
    scene_direction: "Scene / Interaction Direction — Always Active", shot_type: "Framing / Shot Type", custom_framing: "Custom Framing",
    camera_view: "Camera View", camera_height: "Camera Height", lens: "Lens / Perspective — Auto Recommended for Body Framing",
    custom_camera: "Custom Camera Direction", pose: "Primary Character Pose", custom_pose: "Custom Pose — Used When Pose Is Custom",
    expression: "Primary Character Expression", custom_expression: "Custom Expression", extreme_closeup_focus: "Extreme Close-Up Detail",
    custom_extreme_focus: "Custom Extreme Close-Up Detail", closeup_region: "Regional Close-Up Area",
    custom_closeup_region: "Custom Regional Area", background: "Background / Location", custom_background: "Custom Background / Location",
    lighting: "Lighting", custom_lighting: "Custom Lighting", photo_style: "Photo Style — Social / Selfie / Documentation Look",
    aspect_ratio: "Output Aspect Ratio", distortion_guard: "Perspective Protection", shot_suffix: "Additional Shot Notes",
};

const ASSEMBLER_LABELS = {
    generation_purpose: "Generator / Task", reference_label: "Qwen Reference Image Label", trigger_word: "LoRA Trigger Word",
    custom_prefix: "Prompt Prefix", custom_suffix: "Prompt Suffix",
};

function widgetByName(node, name) {
    return node.widgets?.find((widget) => widget.name === name);
}

function applyFriendlyLabels(node, labels) {
    for (const [name, label] of Object.entries(labels)) {
        const widget = widgetByName(node, name);
        if (widget) widget.label = label;
    }
}

function removeLegacyCreatorSupport(node) {
    if (!node?.widgets) return;
    for (let index = node.widgets.length - 1; index >= 0; index -= 1) {
        const widget = node.widgets[index];
        if (widget?.name !== "fcc_support_panel") continue;
        try { widget.onRemove?.(); } catch (_) {}
        try { widget.element?.remove?.(); } catch (_) {}
        node.widgets.splice(index, 1);
    }
    try { delete node.__fccSupportPanelAdded; } catch (_) {}
    for (const element of document.querySelectorAll?.(".fcc-kaustorment-support-panel") || []) {
        try { element.remove(); } catch (_) {}
    }
}

function restoreCompatibilityWidgets(node, minimumHeight = 0) {
    if (!node?.widgets) return;
    removeLegacyCreatorSupport(node);
    for (const widget of node.widgets) {
        if (widget.__fccOriginalComputeSize) {
            widget.computeSize = widget.__fccOriginalComputeSize;
            try { delete widget.__fccOriginalComputeSize; } catch (_) {}
        }
        if (widget.__fccOriginalDraw) {
            widget.draw = widget.__fccOriginalDraw;
            try { delete widget.__fccOriginalDraw; } catch (_) {}
        }
        widget.hidden = false;
        if (widget.element?.style) widget.element.style.display = "";
    }
    requestAnimationFrame(() => {
        const computed = node.computeSize?.() || node.size || [820, minimumHeight];
        const width = Math.max(node.size?.[0] || computed[0] || 820, 700);
        const height = Math.max(computed[1] || 0, minimumHeight);
        node.setSize?.([width, height]);
        app.graph?.setDirtyCanvas(true, true);
    });
}

function scheduleCompatibilityRestore(node, labels, minimumHeight) {
    const run = () => {
        applyFriendlyLabels(node, labels);
        restoreCompatibilityWidgets(node, minimumHeight);
    };
    run();
    requestAnimationFrame(run);
    setTimeout(run, 75);
    setTimeout(run, 300);
    setTimeout(run, 1000);
}

function makeLink(href, text) {
    const link = document.createElement("a");
    link.href = href; link.target = "_blank"; link.rel = "noopener noreferrer"; link.textContent = text;
    link.style.cssText = "display:block;padding:9px 12px;border:1px solid rgba(255,255,255,.18);border-radius:7px;color:#f8f8f8;background:rgba(255,255,255,.07);text-decoration:none;font-size:13px;line-height:1.15;text-align:center;cursor:pointer";
    return link;
}

function addSupportPanel(node) {
    if (node.__fccV252SupportAdded) return;
    node.__fccV252SupportAdded = true;
    const coffee = "https://buymeacoffee.com/ascmclinej";
    const discord = "https://discord.gg/ufU6UcrK6";
    if (typeof node.addDOMWidget !== "function") {
        node.addWidget?.("button", "☕ Support development", null, () => window.open(coffee, "_blank", "noopener,noreferrer"));
        node.addWidget?.("button", "💬 Join the Discord community", null, () => window.open(discord, "_blank", "noopener,noreferrer"));
        return;
    }
    const container = document.createElement("div");
    container.className = "fcc-v252-support-panel";
    container.style.cssText = "width:100%;height:190px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;gap:22px;padding:12px 18px;border:1px solid rgba(255,255,255,.14);border-radius:8px;background:linear-gradient(180deg,rgba(24,24,24,.42),rgba(8,8,8,.78));overflow:hidden";
    const imageLink = document.createElement("a");
    imageLink.href = coffee; imageLink.target = "_blank"; imageLink.rel = "noopener noreferrer";
    const image = document.createElement("img");
    image.src = new URL("./assets/kaustorment_support.webp", import.meta.url).href;
    image.alt = "Thanks for your support"; image.draggable = false;
    image.style.cssText = "width:150px;height:158px;object-fit:contain;display:block;cursor:pointer;user-select:none";
    imageLink.appendChild(image);
    const right = document.createElement("div");
    right.style.cssText = "min-width:250px;max-width:520px;flex:1 1 auto;display:flex;flex-direction:column;gap:10px";
    const title = document.createElement("div");
    title.textContent = "KausTorment's Character Creation Studio";
    title.style.cssText = "color:#ffd600;font-weight:700;font-size:15px;line-height:1.2;text-align:center;margin-bottom:2px";
    right.append(title, makeLink(coffee, "☕ Support development"), makeLink(discord, "💬 Join the Discord community"));
    container.append(imageLink, right);
    const widget = node.addDOMWidget("fcc_v252_dedicated_support_panel", "div", container, {
        serialize: false, hideOnZoom: false, getValue: () => undefined, setValue: () => {},
    });
    widget.serialize = false;
    widget.computeSize = (width) => [Math.max(600, width || node.size?.[0] || 600), 198];
    requestAnimationFrame(() => node.setSize?.([Math.max(620, node.size?.[0] || 620), Math.max(230, node.size?.[1] || 230)]));
}

app.registerExtension({
    name: "full_character_creation_core.v252_compatibility_ui",
    nodeCreated(node) {
        const id = node?.comfyClass ?? node?.type;
        if (id === "CharacterBlueprintCreatorV252" || id === "CharacterBlueprintCreatorV253") scheduleCompatibilityRestore(node, CREATOR_LABELS, 4200);
        if (id === "CharacterShotControlV252" || id === "CharacterShotControlV253") scheduleCompatibilityRestore(node, SHOT_LABELS, 1850);
        if (id === "CharacterPromptAssemblerV252" || id === "CharacterPromptAssemblerV253") applyFriendlyLabels(node, ASSEMBLER_LABELS);
        if (id === "FCCSupportPanel") addSupportPanel(node);
    },
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "CharacterBlueprintCreatorV252" || nodeData.name === "CharacterBlueprintCreatorV253") {
            const original = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const result = original?.apply(this, arguments);
                scheduleCompatibilityRestore(this, CREATOR_LABELS, 4200);
                return result;
            };
        }
        if (nodeData.name === "CharacterShotControlV252" || nodeData.name === "CharacterShotControlV253") {
            const original = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const result = original?.apply(this, arguments);
                scheduleCompatibilityRestore(this, SHOT_LABELS, 1850);
                return result;
            };
        }
        if (nodeData.name === "CharacterPromptAssemblerV252" || nodeData.name === "CharacterPromptAssemblerV253") {
            const original = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const result = original?.apply(this, arguments);
                applyFriendlyLabels(this, ASSEMBLER_LABELS);
                return result;
            };
        }
        if (nodeData.name === "FCCSupportPanel") {
            const original = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const result = original?.apply(this, arguments);
                addSupportPanel(this);
                return result;
            };
        }
    },
});
