# Full Character Creation Core — V2.4.14

Integrated node suite for Full Character Creation Studio V2.8.14.

## Staged workflow

- **Stage 0:** standalone Krea2 generation baseline using Character Creator + Universal Shot Control. It has its own local randomized KSampler seed and does not depend on any queue stage.
- **Stage 2:** Krea2 pre-LoRA documentation. It can generate three identity anchors plus a body-only regional atlas from crown/nape through hands, torso, anatomy, legs, and feet in every believable direct/profile/rear/three-quarter view.
- **Stage 3:** Qwen Image Edit angle expansion from any approved Stage 2 face, midshot, full-body, or regional reference. The encoder receives clean angle metadata only.
- **Stage 4:** Krea2 final dataset expansion with the trained identity LoRA, Character Blueprint, and Shot Control.

All image approval remains manual in this version. Automatic pass/reject, caption curation, saved blueprint/LoRA binding, and character-evolution controls remain future features.

Working on currently: New update pending Sunday 08/02/2026
- Qwen 2511 angle quality remains dependent on the exact base-model / angle-LoRA combination.
- The 25-step preset is for testing; 40 steps may remain useful for selected final outputs.
- The Stage 2 complete plan contains 207 images at one variation. Start with Identity Anchors — 3, then run clothed and clinical regional plans separately.
- Krea2 may still require regeneration for malformed hands, feet, complex piercings, or extreme camera angles.
- Every generated image must be manually reviewed before LoRA training.
- Automatic pass/reject, caption curation, saved Blueprint/LoRA binding, and Character Evolution Control are future features.
