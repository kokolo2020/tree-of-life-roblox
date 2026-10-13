"""Build, export, and render the Tree of Life savanna village house.

Run from the repository root with Blender 4.2 LTS or newer:
    blender --background --factory-startup --python blender/generate_village_house.py

``Asset_VillageHouse`` contains the editable game asset.  The camera, lights,
and ground live in ``Preview_Stage`` and are excluded from GLB export.
"""

from __future__ import annotations

import math
import os
import random

import bpy
from mathutils import Vector


SEED = 2405
random.seed(SEED)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GENERATED_DIR = os.path.join(ROOT, "assets", "generated")
PREVIEW_DIR = os.path.join(ROOT, "assets", "previews")
BLEND_PATH = os.path.join(GENERATED_DIR, "savanna_village_house.blend")
GLB_PATH = os.path.join(GENERATED_DIR, "savanna_village_house.glb")
PREVIEW_PATH = os.path.join(PREVIEW_DIR, "savanna_village_house_preview.png")


def reset_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (
        bpy.data.curves,
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def make_collection(name: str) -> bpy.types.Collection:
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def move_to_collection(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)


def material(
    name: str,
    color: tuple[float, float, float],
    roughness: float = 0.82,
    noise_scale: float | None = None,
    noise_strength: float = 0.1,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    principled = nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = (*color, 1.0)
    principled.inputs["Roughness"].default_value = roughness
    if noise_scale:
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = noise_scale
        noise.inputs["Detail"].default_value = 3.5
        noise.inputs["Roughness"].default_value = 0.72
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = noise_strength
        bump.inputs["Distance"].default_value = 0.1
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], principled.inputs["Normal"])
    return mat


def smooth_mesh(obj: bpy.types.Object) -> None:
    if obj.type == "MESH":
        for polygon in obj.data.polygons:
            polygon.use_smooth = True


def add_bevel(obj: bpy.types.Object, width: float, segments: int = 3) -> None:
    modifier = obj.modifiers.new("Hand-rounded edges", "BEVEL")
    modifier.width = width
    modifier.segments = segments
    modifier.limit_method = "ANGLE"


def irregular_cylinder(
    name: str,
    radius: float,
    height: float,
    z: float,
    mat: bpy.types.Material,
    collection: bpy.types.Collection,
    segments: int = 64,
    rings: int = 7,
) -> bpy.types.Object:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for ring in range(rings + 1):
        t = ring / rings
        ring_z = z - height * 0.5 + height * t
        taper = 1.0 - 0.025 * t
        for index in range(segments):
            angle = index * math.tau / segments
            wobble = 1.0 + 0.018 * math.sin(angle * 3 + t * 1.7) + 0.012 * math.sin(angle * 7 - t)
            current_radius = radius * taper * wobble
            vertices.append((current_radius * math.cos(angle), current_radius * math.sin(angle), ring_z))
    for ring in range(rings):
        for index in range(segments):
            next_index = (index + 1) % segments
            a = ring * segments + index
            b = ring * segments + next_index
            c = (ring + 1) * segments + next_index
            d = (ring + 1) * segments + index
            faces.append((a, b, c, d))
    faces.append(tuple(reversed(range(segments))))
    top_start = rings * segments
    faces.append(tuple(top_start + index for index in range(segments)))

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.data.materials.append(mat)
    smooth_mesh(obj)
    add_bevel(obj, 0.045, 3)
    return obj


def cylinder(
    name: str,
    radius: float,
    depth: float,
    location: tuple[float, float, float],
    mat: bpy.types.Material,
    collection: bpy.types.Collection,
    vertices: int = 32,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    move_to_collection(obj, collection)
    obj.data.materials.append(mat)
    smooth_mesh(obj)
    return obj


def cylinder_between(
    name: str,
    start: Vector,
    end: Vector,
    radius: float,
    mat: bpy.types.Material,
    collection: bpy.types.Collection,
    vertices: int = 10,
    taper: float = 0.82,
) -> bpy.types.Object:
    direction = end - start
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices,
        radius1=radius,
        radius2=radius * taper,
        depth=direction.length,
        location=(start + end) * 0.5,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    move_to_collection(obj, collection)
    obj.data.materials.append(mat)
    smooth_mesh(obj)
    return obj


def ico_detail(
    name: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    mat: bpy.types.Material,
    collection: bpy.types.Collection,
    subdivisions: int = 2,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    move_to_collection(obj, collection)
    obj.data.materials.append(mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    smooth_mesh(obj)
    return obj


def torus(
    name: str,
    major_radius: float,
    minor_radius: float,
    location: tuple[float, float, float],
    mat: bpy.types.Material,
    collection: bpy.types.Collection,
    major_segments: int = 48,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_segments=major_segments,
        minor_segments=8,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    move_to_collection(obj, collection)
    obj.data.materials.append(mat)
    smooth_mesh(obj)
    return obj


def cone_layer(
    name: str,
    radius_bottom: float,
    radius_top: float,
    depth: float,
    z: float,
    mat: bpy.types.Material,
    collection: bpy.types.Collection,
    phase: float,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cone_add(
        vertices=72,
        radius1=radius_bottom,
        radius2=radius_top,
        depth=depth,
        location=(0, 0, z),
    )
    obj = bpy.context.object
    obj.name = name
    for vertex in obj.data.vertices:
        radius = math.hypot(vertex.co.x, vertex.co.y)
        if radius > 0.05:
            angle = math.atan2(vertex.co.y, vertex.co.x)
            wobble = 1.0 + 0.018 * math.sin(angle * 5 + phase) + 0.009 * math.sin(angle * 11 - phase)
            vertex.co.x *= wobble
            vertex.co.y *= wobble
    move_to_collection(obj, collection)
    obj.data.materials.append(mat)
    smooth_mesh(obj)
    bevel = obj.modifiers.new("Soft thatch edge", "BEVEL")
    bevel.width = 0.035
    bevel.segments = 2
    return obj


def arched_prism(
    name: str,
    width: float,
    height: float,
    depth: float,
    y: float,
    mat: bpy.types.Material,
    collection: bpy.types.Collection,
    arch_segments: int = 16,
) -> bpy.types.Object:
    radius = width * 0.5
    spring_z = height - radius
    outline: list[tuple[float, float]] = [(-radius, 0.0), (-radius, spring_z)]
    for index in range(arch_segments + 1):
        angle = math.pi - index * math.pi / arch_segments
        outline.append((math.cos(angle) * radius, spring_z + math.sin(angle) * radius))
    outline.append((radius, 0.0))

    vertices: list[tuple[float, float, float]] = []
    for y_side in (y - depth * 0.5, y + depth * 0.5):
        vertices.extend((x, y_side, z) for x, z in outline)
    count = len(outline)
    faces: list[tuple[int, ...]] = [tuple(range(count)), tuple(reversed(range(count, count * 2)))]
    for index in range(count):
        next_index = (index + 1) % count
        faces.append((index, next_index, count + next_index, count + index))
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.data.materials.append(mat)
    add_bevel(obj, 0.035, 3)
    return obj


def pot(
    name: str,
    location: tuple[float, float, float],
    scale: float,
    clay: bpy.types.Material,
    accent: bpy.types.Material,
    collection: bpy.types.Collection,
) -> None:
    profile = [
        (0.16, 0.00),
        (0.37, 0.04),
        (0.50, 0.30),
        (0.45, 0.58),
        (0.34, 0.76),
        (0.47, 0.83),
        (0.45, 0.91),
    ]
    segments = 32
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    for ring, (radius, z) in enumerate(profile):
        for index in range(segments):
            angle = index * math.tau / segments
            vertices.append((radius * math.cos(angle), radius * math.sin(angle), z))
    for ring in range(len(profile) - 1):
        for index in range(segments):
            next_index = (index + 1) % segments
            faces.append((
                ring * segments + index,
                ring * segments + next_index,
                (ring + 1) * segments + next_index,
                (ring + 1) * segments + index,
            ))
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.location = location
    obj.scale = (scale, scale, scale)
    obj.data.materials.append(clay)
    smooth_mesh(obj)
    torus(
        f"{name} Painted Band",
        0.43 * scale,
        0.035 * scale,
        (location[0], location[1], location[2] + 0.57 * scale),
        accent,
        collection,
        major_segments=32,
    )


def wall_fixture_rotation(normal: Vector):
    return normal.to_track_quat("Z", "Y")


def look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_area_light(
    name: str,
    location: tuple[float, float, float],
    energy: float,
    color: tuple[float, float, float],
    size: float,
    target: tuple[float, float, float],
    collection: bpy.types.Collection,
) -> None:
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.color = color
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = location
    look_at(obj, target)


def build_asset(asset: bpy.types.Collection) -> None:
    ochre = material("Sunbaked Ochre Plaster", (0.80, 0.32, 0.085), 0.91, 3.6, 0.16)
    ochre_light = material("Plaster Highlights", (0.95, 0.54, 0.16), 0.89, 5.0, 0.08)
    clay_dark = material("Deep Terracotta", (0.38, 0.07, 0.025), 0.87, 4.2, 0.1)
    wood = material("Carved Dark Wood", (0.17, 0.035, 0.012), 0.82, 5.5, 0.2)
    wood_light = material("Sunlit Wood", (0.36, 0.105, 0.025), 0.84, 4.0, 0.12)
    turquoise = material("Painted Turquoise", (0.015, 0.48, 0.53), 0.72)
    coral = material("Painted Coral", (0.95, 0.17, 0.065), 0.75)
    cream = material("Painted Cream", (0.98, 0.69, 0.25), 0.79)
    window_blue = material("Cool Window Glass", (0.02, 0.16, 0.24), 0.32)
    stone_mats = [
        material("Foundation Stone - Red", (0.38, 0.105, 0.045), 0.93),
        material("Foundation Stone - Gold", (0.63, 0.275, 0.065), 0.93),
        material("Foundation Stone - Dark", (0.20, 0.065, 0.035), 0.93),
    ]
    thatch_mats = [
        material("Thatch - Deep", (0.42, 0.18, 0.025), 0.96, 7.0, 0.12),
        material("Thatch - Golden", (0.72, 0.39, 0.055), 0.95, 6.0, 0.11),
        material("Thatch - Sunlit", (0.96, 0.65, 0.14), 0.93, 5.5, 0.08),
    ]

    irregular_cylinder("Hand-Plastered Round Wall", 2.52, 3.05, 1.53, ochre, asset)
    cylinder("Turquoise Foundation Band", 2.59, 0.28, (0, 0, 0.17), turquoise, asset, 64)
    torus("Lower Painted Wall Band", 2.525, 0.065, (0, 0, 0.73), cream, asset, 64)
    torus("Upper Painted Wall Band", 2.47, 0.055, (0, 0, 2.47), coral, asset, 64)

    for index in range(22):
        angle = index * math.tau / 22 + 0.05 * math.sin(index * 1.7)
        radius = 2.51
        stone = ico_detail(
            f"Foundation Stone {index + 1:02d}",
            (radius * math.cos(angle), radius * math.sin(angle), 0.22 + 0.025 * (index % 3)),
            (0.41 + 0.06 * (index % 2), 0.25, 0.25 + 0.04 * (index % 3)),
            stone_mats[index % len(stone_mats)],
            asset,
            subdivisions=2,
        )
        stone.rotation_euler.z = angle

    # Door frame is a larger arch behind the inset wood door, producing a clean border.
    arched_prism("Turquoise Arched Door Frame", 1.62, 2.58, 0.18, -2.53, turquoise, asset)
    door = arched_prism("Carved Wooden Door", 1.28, 2.34, 0.20, -2.66, wood, asset)
    for index, x in enumerate((-0.43, -0.21, 0.0, 0.21, 0.43)):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, -2.785, 1.05))
        plank = bpy.context.object
        plank.name = f"Door Plank {index + 1:02d}"
        plank.dimensions = (0.075, 0.055, 1.76)
        move_to_collection(plank, asset)
        plank.data.materials.append(wood_light if index % 2 else clay_dark)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        add_bevel(plank, 0.022, 2)
    for z in (0.56, 1.45):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -2.82, z))
        brace = bpy.context.object
        brace.name = "Door Cross Brace"
        brace.dimensions = (1.03, 0.07, 0.10)
        move_to_collection(brace, asset)
        brace.data.materials.append(wood_light)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        add_bevel(brace, 0.025, 2)
    for index, z in enumerate((0.58, 0.92, 1.28, 1.62)):
        for x in (-0.50, 0.50):
            ico_detail(f"Door Stud {index + 1:02d}", (x, -2.86, z), (0.055, 0.035, 0.055), cream, asset, 2)

    # Circular side windows with deep turquoise frames and small wooden sun shades.
    for window_index, angle in enumerate((-0.92, 0.94)):
        normal = Vector((math.sin(angle), -math.cos(angle), 0.0))
        center = normal * 2.51 + Vector((0, 0, 1.72))
        frame = torus(
            f"Window Frame {window_index + 1:02d}",
            0.38,
            0.085,
            tuple(center + normal * 0.05),
            turquoise,
            asset,
            32,
        )
        frame.rotation_mode = "QUATERNION"
        frame.rotation_quaternion = wall_fixture_rotation(normal)
        glass = cylinder(
            f"Window Inset {window_index + 1:02d}",
            0.31,
            0.075,
            tuple(center + normal * 0.01),
            window_blue,
            asset,
            32,
        )
        glass.rotation_mode = "QUATERNION"
        glass.rotation_quaternion = wall_fixture_rotation(normal)
        shade_start = center + normal * 0.16 + Vector((0, 0, 0.48)) - Vector((0.46, 0, 0))
        shade_end = shade_start + Vector((0.92, 0, 0))
        cylinder_between(
            f"Window Shade {window_index + 1:02d}",
            shade_start,
            shade_end,
            0.055,
            wood,
            asset,
            8,
            1.0,
        )

    # Raised geometric painting remains readable after Roblox import without textures.
    motif_mats = (turquoise, cream, coral)
    motif_number = 0
    for index in range(18):
        angle = index * math.tau / 18
        if min(abs(angle), abs(math.tau - angle)) < 0.55:
            continue
        normal = Vector((math.sin(angle), -math.cos(angle), 0.0))
        for row, z in enumerate((1.0, 2.23)):
            center = normal * 2.555 + Vector((0, 0, z))
            bpy.ops.mesh.primitive_cylinder_add(vertices=4, radius=0.15, depth=0.075, location=center)
            tile = bpy.context.object
            motif_number += 1
            tile.name = f"Painted Diamond {motif_number:02d}"
            tile.rotation_mode = "QUATERNION"
            tile.rotation_quaternion = wall_fixture_rotation(normal)
            move_to_collection(tile, asset)
            tile.data.materials.append(motif_mats[(index + row) % len(motif_mats)])
            add_bevel(tile, 0.012, 2)

    # Overlapping hand-formed cones create a warm, directional thatch silhouette.
    roof_layers = 8
    for index in range(roof_layers):
        radius_bottom = 3.34 - index * 0.39
        radius_top = max(0.14, radius_bottom - 0.58)
        depth = 0.60
        z = 3.18 + index * 0.34
        cone_layer(
            f"Overlapping Thatch Layer {index + 1:02d}",
            radius_bottom,
            radius_top,
            depth,
            z,
            thatch_mats[index % len(thatch_mats)],
            asset,
            index * 0.73,
        )

    for index in range(18):
        angle = index * math.tau / 18
        direction = Vector((math.cos(angle), math.sin(angle), 0.0))
        cylinder_between(
            f"Eave Beam {index + 1:02d}",
            direction * 2.16 + Vector((0, 0, 2.94)),
            direction * 3.16 + Vector((0, 0, 3.02)),
            0.075,
            wood,
            asset,
            8,
            0.8,
        )

    for index in range(48):
        angle = index * math.tau / 48 + random.uniform(-0.018, 0.018)
        direction = Vector((math.cos(angle), math.sin(angle), 0.0))
        top = direction * 3.04 + Vector((0, 0, 3.16 + random.uniform(-0.035, 0.05)))
        bottom = direction * (3.15 + random.uniform(-0.02, 0.09)) + Vector((0, 0, 2.72 + random.uniform(-0.10, 0.07)))
        cylinder_between(
            f"Thatch Fringe {index + 1:02d}",
            top,
            bottom,
            0.022,
            thatch_mats[index % len(thatch_mats)],
            asset,
            6,
            0.55,
        )

    cylinder("Roof Finial Post", 0.12, 0.76, (0, 0, 5.89), wood, asset, 12)
    for index, (z, radius, mat) in enumerate(((5.55, 0.25, coral), (5.79, 0.20, turquoise), (6.05, 0.15, cream))):
        ico_detail(f"Roof Finial Bead {index + 1:02d}", (0, 0, z), (radius, radius, radius), mat, asset, 2)

    # Front stoop, hand-made pots, and a leaning carved staff make the house feel inhabited.
    for index, (y, sx, sy) in enumerate(((-2.95, 1.15, 0.48), (-3.45, 0.92, 0.43), (-3.84, 0.70, 0.36))):
        step = ico_detail(
            f"Entrance Step {index + 1:02d}",
            (0.0, y, 0.08 + index * 0.01),
            (sx, sy, 0.13),
            stone_mats[(index + 1) % len(stone_mats)],
            asset,
            subdivisions=2,
        )
        step.rotation_euler.z = (index - 1) * 0.08
    pot("Painted Water Pot", (-1.48, -2.56, 0.0), 0.72, clay_dark, turquoise, asset)
    pot("Golden Storage Pot", (1.52, -2.46, 0.0), 0.55, ochre_light, coral, asset)
    cylinder_between(
        "Carved Walking Staff",
        Vector((1.98, -2.32, 0.1)),
        Vector((1.73, -2.45, 2.18)),
        0.055,
        wood,
        asset,
        10,
        0.65,
    )
    for index, z in enumerate((0.65, 1.15, 1.66)):
        bead = ico_detail(
            f"Staff Bead {index + 1:02d}",
            (1.91 - 0.12 * index, -2.36 - 0.06 * index, z),
            (0.095, 0.095, 0.095),
            motif_mats[index % 3],
            asset,
            2,
        )
        bead.rotation_euler.x = 0.1


def build_preview_stage(stage: bpy.types.Collection) -> None:
    ground_mat = material("Preview Savanna Earth", (0.57, 0.135, 0.035), 0.94, 2.8, 0.07)
    path_mat = material("Preview Footpath", (0.91, 0.47, 0.12), 0.93)
    grass_mat = material("Preview Golden Grass", (0.55, 0.48, 0.06), 0.9)
    rock_mat = material("Preview Dark Rock", (0.19, 0.055, 0.035), 0.92)

    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=8.2, depth=0.36, location=(0, 0, -0.27))
    ground = bpy.context.object
    ground.name = "Preview Ground"
    move_to_collection(ground, stage)
    ground.data.materials.append(ground_mat)
    add_bevel(ground, 0.38, 4)
    smooth_mesh(ground)

    for index, (x, y, sx, sy, rot) in enumerate(
        ((0.0, -4.7, 1.15, 0.48, 0.03), (-0.2, -5.7, 0.95, 0.42, -0.08),
         (0.18, -6.5, 0.72, 0.34, 0.12), (3.8, 1.7, 1.0, 0.36, 0.6))
    ):
        patch = ico_detail(
            f"Preview Path Stone {index + 1:02d}",
            (x, y, -0.055),
            (sx, sy, 0.045),
            path_mat,
            stage,
            2,
        )
        patch.rotation_euler.z = rot

    for index, (x, y, size) in enumerate(((-3.7, -2.7, 0.28), (3.9, -1.5, 0.34), (-3.0, 2.5, 0.24))):
        rock = ico_detail(
            f"Preview Rock {index + 1:02d}",
            (x, y, size * 0.35),
            (size, size * 0.75, size * 0.58),
            rock_mat,
            stage,
            2,
        )
        rock.rotation_euler.z = index * 1.1

    for clump, (x, y) in enumerate(((-3.8, -1.4), (3.5, -2.7), (-3.3, 1.5), (3.8, 1.0))):
        for blade in range(6):
            angle = blade * math.tau / 6 + clump * 0.3
            start = Vector((x, y, -0.03))
            end = start + Vector((0.15 * math.cos(angle), 0.15 * math.sin(angle), 0.55 + 0.04 * blade))
            cylinder_between(
                f"Preview Grass {clump + 1:02d}-{blade + 1:02d}",
                start,
                end,
                0.024,
                grass_mat,
                stage,
                6,
                0.42,
            )

    scene = bpy.context.scene
    world = bpy.data.worlds.new("Savanna Preview World") if not scene.world else scene.world
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.045, 0.025, 0.12, 1.0)
    background.inputs["Strength"].default_value = 0.34

    camera_data = bpy.data.cameras.new("Village House Hero Camera")
    camera = bpy.data.objects.new("Village House Hero Camera", camera_data)
    stage.objects.link(camera)
    camera.location = (10.8, -14.8, 7.8)
    camera_data.lens = 58
    look_at(camera, (0.0, -0.15, 2.65))
    scene.camera = camera

    add_area_light("Key - Sunset", (-7.5, -8.5, 12.0), 1280, (1.0, 0.36, 0.10), 6.0, (0, 0, 2.7), stage)
    add_area_light("Fill - Evening Sky", (7.0, -3.0, 8.0), 820, (0.22, 0.46, 1.0), 5.0, (0, 0, 2.4), stage)
    add_area_light("Rim - Magenta Sun", (2.0, 7.5, 9.5), 1150, (1.0, 0.12, 0.08), 4.0, (0, 0, 3.2), stage)
    add_area_light("Bounce - Warm Front", (0.0, -8.5, 4.2), 520, (1.0, 0.58, 0.28), 4.5, (0, -0.5, 1.8), stage)
    sun_data = bpy.data.lights.new("Soft Savanna Sun", "SUN")
    sun_data.energy = 1.15
    sun_data.angle = math.radians(20)
    sun_data.color = (1.0, 0.54, 0.22)
    sun = bpy.data.objects.new("Soft Savanna Sun", sun_data)
    stage.objects.link(sun)
    sun.rotation_euler = (math.radians(25), math.radians(-20), math.radians(-42))


def configure_render() -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 20
    scene.render.filepath = PREVIEW_PATH
    scene.render.film_transparent = False
    scene.view_settings.look = "AgX - Medium High Contrast"

    scene.use_nodes = True
    nodes = scene.node_tree.nodes
    nodes.clear()
    render_layers = nodes.new("CompositorNodeRLayers")
    glare = nodes.new("CompositorNodeGlare")
    glare.glare_type = "FOG_GLOW"
    glare.quality = "HIGH"
    glare.threshold = 1.2
    glare.size = 6
    composite = nodes.new("CompositorNodeComposite")
    scene.node_tree.links.new(render_layers.outputs["Image"], glare.inputs["Image"])
    scene.node_tree.links.new(glare.outputs["Image"], composite.inputs["Image"])


def export_asset(asset: bpy.types.Collection) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [obj for obj in asset.all_objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("Asset_VillageHouse contains no exportable mesh objects")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(
        filepath=GLB_PATH,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
    )
    bpy.ops.object.select_all(action="DESELECT")


def main() -> None:
    os.makedirs(GENERATED_DIR, exist_ok=True)
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0
    reset_scene()
    asset = make_collection("Asset_VillageHouse")
    stage = make_collection("Preview_Stage")
    build_asset(asset)
    build_preview_stage(stage)
    configure_render()

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH, check_existing=False)
    export_asset(asset)
    bpy.context.scene.render.filepath = PREVIEW_PATH
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH, check_existing=False)

    mesh_count = sum(obj.type == "MESH" for obj in asset.all_objects)
    print(f"HOUSE_COMPLETE meshes={mesh_count} seed={SEED}")
    print(f"HOUSE_PATH blend={BLEND_PATH}")
    print(f"HOUSE_PATH glb={GLB_PATH}")
    print(f"HOUSE_PATH preview={PREVIEW_PATH}")


if __name__ == "__main__":
    main()
