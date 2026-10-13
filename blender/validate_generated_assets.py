"""Import the generated GLBs into clean scenes and write a validation report.

Run after both generators:
    blender --background --factory-startup --python blender/validate_generated_assets.py
"""

from __future__ import annotations

import hashlib
import json
import os

import bpy
from mathutils import Vector


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GENERATED_DIR = os.path.join(ROOT, "assets", "generated")
REPORT_PATH = os.path.join(GENERATED_DIR, "validation_report.json")
TARGETS = {
    "savanna_acacia": os.path.join(GENERATED_DIR, "savanna_acacia.glb"),
    "savanna_village_house": os.path.join(GENERATED_DIR, "savanna_village_house.glb"),
}
MAX_TRIANGLES = 125_000
MAX_FILE_BYTES = 25 * 1024 * 1024


def sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(name: str, path: str) -> dict:
    if not os.path.isfile(path):
        return {"status": "FAIL", "errors": [f"Missing file: {path}"]}

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    cameras = [obj.name for obj in bpy.context.scene.objects if obj.type == "CAMERA"]
    lights = [obj.name for obj in bpy.context.scene.objects if obj.type == "LIGHT"]

    triangles = 0
    vertices = 0
    material_names: set[str] = set()
    bounds: list[Vector] = []
    for obj in meshes:
        obj.data.calc_loop_triangles()
        triangles += len(obj.data.loop_triangles)
        vertices += len(obj.data.vertices)
        material_names.update(slot.material.name for slot in obj.material_slots if slot.material)
        bounds.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)

    errors: list[str] = []
    if not meshes:
        errors.append("No mesh objects imported")
    if cameras:
        errors.append(f"Export unexpectedly contains cameras: {cameras}")
    if lights:
        errors.append(f"Export unexpectedly contains lights: {lights}")
    if triangles <= 0:
        errors.append("No triangles found")
    if triangles > MAX_TRIANGLES:
        errors.append(f"Triangle count {triangles} exceeds budget {MAX_TRIANGLES}")
    file_bytes = os.path.getsize(path)
    if file_bytes > MAX_FILE_BYTES:
        errors.append(f"File size {file_bytes} exceeds budget {MAX_FILE_BYTES}")

    if bounds:
        minimum = Vector((min(point.x for point in bounds), min(point.y for point in bounds), min(point.z for point in bounds)))
        maximum = Vector((max(point.x for point in bounds), max(point.y for point in bounds), max(point.z for point in bounds)))
        dimensions = maximum - minimum
        if min(dimensions) <= 0:
            errors.append(f"Invalid bounds: {tuple(dimensions)}")
        if max(dimensions) > 20:
            errors.append(f"Largest dimension {max(dimensions):.3f} m exceeds 20 m sanity limit")
        bounds_report = {
            "minimum_m": [round(value, 4) for value in minimum],
            "maximum_m": [round(value, 4) for value in maximum],
            "dimensions_m": [round(value, 4) for value in dimensions],
        }
    else:
        bounds_report = None

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "file": os.path.relpath(path, ROOT),
        "file_bytes": file_bytes,
        "sha256": sha256(path),
        "mesh_objects": len(meshes),
        "vertices": vertices,
        "triangles": triangles,
        "materials": sorted(material_names),
        "bounds": bounds_report,
        "cameras": cameras,
        "lights": lights,
    }


def main() -> None:
    report = {
        "blender_version": bpy.app.version_string,
        "limits": {
            "maximum_triangles": MAX_TRIANGLES,
            "maximum_file_bytes": MAX_FILE_BYTES,
        },
        "assets": {name: validate(name, path) for name, path in TARGETS.items()},
    }
    report["status"] = "PASS" if all(item["status"] == "PASS" for item in report["assets"].values()) else "FAIL"
    os.makedirs(GENERATED_DIR, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"VALIDATION_REPORT {REPORT_PATH}")
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
