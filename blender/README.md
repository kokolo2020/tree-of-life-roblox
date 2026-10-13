# Blender Assets

These deterministic Blender scripts build the stylized Africa Savanna Village
assets, save editable scenes, export gameplay-only GLBs, and render art-review
previews. The preview stage is retained in each `.blend` but excluded from its
GLB.

Tested with Blender 4.2.10 LTS:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python blender/generate_acacia.py
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python blender/generate_village_house.py
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python blender/validate_generated_assets.py
```

Generated files:

- `assets/generated/savanna_acacia.blend`
- `assets/generated/savanna_acacia.glb`
- `assets/generated/savanna_village_house.blend`
- `assets/generated/savanna_village_house.glb`
- `assets/generated/validation_report.json`
- `assets/previews/savanna_acacia_preview.png`
- `assets/previews/savanna_village_house_preview.png`

The GLBs use meters, embed their materials, and contain no preview lights,
cameras, or display ground. Validate scale, collision strategy, and material
appearance again after import into a backed-up Roblox Studio place.
