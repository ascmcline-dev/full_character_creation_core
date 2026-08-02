# Full Character Creation Core V2.4.20

Current registered Creator / Shot Control / Prompt Assembler nodes use V260.

## V2.4.20 Native Clinical Macro

Stage 0 `Extreme Close-Up — Single Detail` and the Stage 2 opt-in Extreme Clinical plan use a shared local-only macro compiler.

The macro route compiles only:
- the named local target;
- target-specific 105mm macro camera geometry;
- canonical anatomy relevant to that target;
- local skin pores, contours, folds, pigmentation, and micro-shadows;
- configured permanent details whose structured regions intersect the target;
- neutral clinical illumination.

It does not compile full-character height/build, pose, wardrobe, general room context, social-photo focus language, or unrelated anatomy.

The package remains one integrated `full_character_creation_core` custom-node folder.
