"""Build, export, and render the Tree of Life savanna acacia.

Run from the repository root with Blender 4.2 LTS or newer:
    blender --background --factory-startup --python blender/generate_acacia.py

The generated ``Asset_Acacia`` collection is the editable game asset.  The
``Preview_Stage`` collection, camera, and lights remain in the .blend for art
direction but are deliberately excluded from the GLB export.
"""

from __future__ import annotations

import math
import os
import random

import bpy
from mathutils import Vector


SEED = 1705
random.seed(SEED)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GENERATED_DIR = os.path.join(ROOT, "assets", "generated")
PREVIEW_DIR = os.path.join(ROOT, "assets", "previews")
BLEND_PATH = os.path.join(GENERATED_DIR, "savanna_acacia.blend")
GLB_PATH = os.path.join(GENERATED_DIR, "savanna_acacia.glb")
PREVIEW_PATH = os.path.join(PREVIEW_DIR, "savanna_acacia_preview.png")


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
    roughness: float = 0.8,
    noise_scale: float | None = None,
    noise_strength: float = 0.12,
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
        noise.inputs["Detail"].default_value = 3.0
        noise.inputs["Roughness"].default_value = 0.7
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = noise_strength
        bump.inputs["Distance"].default_value = 0.12
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], principled.inputs["Normal"])
    return mat


def smooth_mesh(obj: bpy.types.Object) -> None:
    if obj.type == "MESH":
        for polygon in obj.data.polygons:
            polygon.use_smooth = True


def curve_mesh(
    name: str,
    points: list[tuple[float, float, float] | Vector],
    radii: list[float],
    mat: bpy.types.Material,
    collection: bpy.types.Collection,
    resolution: int = 3,
    bevel_resolution: int = 2,
) -> bpy.types.Object:
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = resolution
    curve.bevel_depth = 1.0
    curve.bevel_resolution = bevel_resolution
    curve.use_fill_caps = True
    curve.resolution_u = resolution
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for index, (point, radius) in enumerate(zip(points, radii)):
        bezier = spline.bezier_points[index]
        bezier.co = Vector(point)
        bezier.radius = radius
        bezier.handle_left_type = "AUTO"
        bezier.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    obj.data.materials.append(mat)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    smooth_mesh(obj)
    obj.select_set(False)
    return obj


def organic_lobe(
    name: str,
    location: Vector,
    scale: tuple[float, float, float],
    rotation: float,
    mat: bpy.types.Material,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.rotation_euler.z = rotation
    move_to_collection(obj, collection)
    obj.data.materials.append(mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    texture = bpy.data.textures.new(f"{name}_surface", type="CLOUDS")
    texture.noise_scale = 0.48
    texture.noise_depth = 1
    displace = obj.modifiers.new("Gentle leaf silhouette", "DISPLACE")
    displace.texture = texture
    displace.strength = 0.10
    displace.texture_coords = "GLOBAL"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=displace.name)
    smooth_mesh(obj)
    return obj


def ico_detail(
    name: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    mat: bpy.types.Material,
    collection: bpy.types.Collection,
    subdivisions: int = 1,
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


def cylinder_between(
    name: str,
    start: Vector,
    end: Vector,
    radius: float,
    mat: bpy.types.Material,
    collection: bpy.types.Collection,
    vertices: int = 10,
) -> bpy.types.Object:
    direction = end - start
    midpoint = (start + end) * 0.5
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices,
        radius1=radius * 1.08,
        radius2=radius * 0.72,
        depth=direction.length,
        location=midpoint,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    move_to_collection(obj, collection)
    obj.data.materials.append(mat)
    smooth_mesh(obj)
    return obj


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
    bark = material("Acacia Bark", (0.30, 0.115, 0.045), 0.88, 3.8, 0.22)
    bark_light = material("Sunlit Bark", (0.53, 0.255, 0.075), 0.84, 5.0, 0.13)
    dark_bark = material("Deep Bark Creases", (0.16, 0.045, 0.018), 0.9)
    foliage = [
        material("Leaves - Deep", (0.075, 0.235, 0.045), 0.82),
        material("Leaves - Fresh", (0.18, 0.47, 0.075), 0.8),
        material("Leaves - Sunlit", (0.49, 0.68, 0.12), 0.78),
        material("Leaves - Lime Tips", (0.66, 0.78, 0.20), 0.76),
    ]
    pod_mat = material("Seed Pods", (0.29, 0.095, 0.025), 0.78)

    # Broad root buttresses make the trunk feel planted and create a strong silhouette.
    for index, angle in enumerate((0.15, 1.45, 2.75, 4.05, 5.2)):
        direction = Vector((math.cos(angle), math.sin(angle), 0.0))
        curve_mesh(
            f"Root Flare {index + 1:02d}",
            [
                direction * 1.32 + Vector((0, 0, 0.06)),
                direction * 0.72 + Vector((0, 0, 0.18)),
                direction * 0.25 + Vector((0, 0, 0.72)),
            ],
            [0.17, 0.28, 0.42],
            bark,
            asset,
            resolution=2,
        )

    trunk_points = [
        (-0.06, 0.02, 0.10),
        (0.08, -0.04, 1.35),
        (-0.14, 0.08, 2.65),
        (0.17, 0.02, 3.85),
        (0.05, -0.05, 4.75),
        (0.34, 0.02, 5.55),
    ]
    curve_mesh(
        "Hero Trunk",
        trunk_points,
        [0.62, 0.55, 0.46, 0.37, 0.27, 0.16],
        bark,
        asset,
        resolution=4,
        bevel_resolution=3,
    )

    # Warm, irregular bark plates read clearly from Roblox's normal play distance.
    for index, (angle, z, width) in enumerate(
        ((0.3, 0.75, 0.22), (2.4, 1.35, 0.18), (4.1, 2.05, 0.17),
         (1.4, 2.85, 0.15), (5.0, 3.55, 0.13), (2.8, 4.25, 0.11))
    ):
        radius = max(0.25, 0.57 - z * 0.067)
        location = (math.cos(angle) * radius, math.sin(angle) * radius, z)
        plate = ico_detail(
            f"Bark Plate {index + 1:02d}",
            location,
            (width, width * 0.45, width * 1.65),
            bark_light if index % 2 == 0 else dark_bark,
            asset,
            subdivisions=2,
        )
        plate.rotation_euler.z = angle

    hubs = [
        Vector((-0.02, 0.02, 4.15)),
        Vector((0.05, -0.02, 4.65)),
        Vector((0.28, 0.02, 5.18)),
    ]
    branch_specs = [
        (0.02, 3.95, 0.2),
        (0.72, 3.55, 0.4),
        (1.48, 3.75, 0.0),
        (2.30, 3.45, 0.3),
        (3.05, 3.95, 0.1),
        (3.80, 3.65, 0.5),
        (4.55, 3.50, 0.0),
        (5.35, 3.80, 0.35),
    ]
    tips: list[Vector] = []
    for index, (angle, reach, lift_variation) in enumerate(branch_specs):
        start = hubs[index % len(hubs)]
        direction = Vector((math.cos(angle), math.sin(angle), 0.0))
        side = Vector((-math.sin(angle), math.cos(angle), 0.0))
        middle = start + direction * (reach * 0.48) + side * (0.18 if index % 2 else -0.15)
        middle.z += 1.02 + lift_variation
        tip = start + direction * reach + side * random.uniform(-0.22, 0.22)
        tip.z += 1.55 + lift_variation + random.uniform(-0.12, 0.22)
        curve_mesh(
            f"Primary Branch {index + 1:02d}",
            [start, middle, tip],
            [0.22, 0.13, 0.045],
            bark,
            asset,
            resolution=3,
        )
        tips.append(tip)

        # A forked twig supports the characteristic wide umbrella crown.
        fork_angle = angle + (0.34 if index % 2 else -0.32)
        fork_direction = Vector((math.cos(fork_angle), math.sin(fork_angle), 0.0))
        fork_tip = middle + fork_direction * (reach * 0.56) + Vector((0, 0, 0.62))
        curve_mesh(
            f"Forked Branch {index + 1:02d}",
            [middle - direction * 0.12, middle + fork_direction * 0.8, fork_tip],
            [0.11, 0.075, 0.026],
            bark,
            asset,
            resolution=2,
            bevel_resolution=1,
        )
        tips.append(fork_tip)

    # Layered, flattened lobes form an asymmetric umbrella instead of a row of balls.
    lobe_index = 0
    for tip_index, tip in enumerate(tips):
        angle = branch_specs[(tip_index // 2) % len(branch_specs)][0]
        outward = Vector((math.cos(angle), math.sin(angle), 0.0))
        tangent = Vector((-outward.y, outward.x, 0.0))
        for layer in range(3):
            offset = tangent * ((layer - 1) * 0.72) + outward * random.uniform(-0.18, 0.35)
            offset.z = random.uniform(-0.10, 0.22) + (0.14 if layer == 1 else 0.0)
            location = tip + offset
            scale = (
                random.uniform(1.18, 1.62),
                random.uniform(0.88, 1.24),
                random.uniform(0.28, 0.43),
            )
            organic_lobe(
                f"Canopy Lobe {lobe_index + 1:02d}",
                location,
                scale,
                angle + random.uniform(-0.25, 0.25),
                foliage[(tip_index + layer) % len(foliage)],
                asset,
            )
            lobe_index += 1

    # Central crown pieces hide branch junctions and make the canopy read as one mass.
    for index, (location, scale) in enumerate(
        (
            ((0.1, 0.0, 6.25), (2.0, 1.65, 0.42)),
            ((1.15, 0.15, 6.48), (1.85, 1.35, 0.36)),
            ((-1.05, -0.25, 6.35), (1.65, 1.25, 0.34)),
            ((0.15, 1.15, 6.42), (1.75, 1.3, 0.35)),
            ((-0.05, -1.15, 6.30), (1.65, 1.25, 0.33)),
        )
    ):
        organic_lobe(
            f"Central Crown {index + 1:02d}",
            Vector(location),
            scale,
            index * 0.58,
            foliage[(index + 1) % len(foliage)],
            asset,
        )

    # A few readable seed pods add narrative detail without visual noise.
    for index, (anchor, angle) in enumerate(
        ((tips[1], 0.1), (tips[4], 1.2), (tips[7], 2.1), (tips[10], 3.2), (tips[13], 5.0))
    ):
        top = anchor + Vector((0, 0, -0.12))
        bottom = top + Vector((0.06 * math.cos(angle), 0.06 * math.sin(angle), -0.58))
        cylinder_between(f"Pod Stem {index + 1:02d}", top, bottom, 0.018, dark_bark, asset, 7)
        pod = ico_detail(
            f"Seed Pod {index + 1:02d}",
            tuple(bottom + Vector((0, 0, -0.18))),
            (0.10, 0.065, 0.30),
            pod_mat,
            asset,
            subdivisions=2,
        )
        pod.rotation_euler.x = random.uniform(-0.18, 0.18)


def build_preview_stage(stage: bpy.types.Collection) -> None:
    sand = material("Preview Sand", (0.64, 0.245, 0.055), 0.94, 2.6, 0.08)
    sand_light = material("Preview Sand Highlight", (0.92, 0.56, 0.18), 0.9)
    grass = material("Preview Dry Grass", (0.52, 0.48, 0.075), 0.9)
    rock = material("Preview Rock", (0.25, 0.105, 0.055), 0.92)

    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=7.6, depth=0.34, location=(0, 0, -0.25))
    ground = bpy.context.object
    ground.name = "Preview Ground"
    move_to_collection(ground, stage)
    ground.data.materials.append(sand)
    bevel = ground.modifiers.new("Soft Ground Edge", "BEVEL")
    bevel.width = 0.38
    bevel.segments = 4
    smooth_mesh(ground)

    # Painterly ground patches, rocks, and grass help judge the in-game palette.
    for index, (x, y, sx, sy) in enumerate(
        ((-3.2, -1.4, 1.4, 0.55), (2.6, 1.2, 1.1, 0.42), (2.2, -2.5, 0.75, 0.35))
    ):
        patch = ico_detail(
            f"Sand Patch {index + 1:02d}",
            (x, y, -0.055),
            (sx, sy, 0.045),
            sand_light,
            stage,
            subdivisions=2,
        )
        patch.rotation_euler.z = index * 0.74

    for index, (x, y, size) in enumerate(((-2.6, -2.0, 0.35), (3.1, -0.8, 0.25), (1.8, 2.8, 0.28))):
        stone = ico_detail(
            f"Preview Rock {index + 1:02d}",
            (x, y, size * 0.34),
            (size, size * 0.72, size * 0.55),
            rock,
            stage,
            subdivisions=2,
        )
        stone.rotation_euler.z = index * 1.12

    for clump, (x, y) in enumerate(((-2.1, 2.0), (2.7, 2.0), (3.55, -2.0), (-3.7, -0.4))):
        for blade in range(5):
            angle = blade * math.tau / 5 + clump * 0.4
            start = Vector((x, y, -0.02))
            end = start + Vector((math.cos(angle) * 0.16, math.sin(angle) * 0.16, 0.58 + blade * 0.035))
            cylinder_between(
                f"Preview Grass {clump + 1:02d}-{blade + 1:02d}",
                start,
                end,
                0.026,
                grass,
                stage,
                6,
            )

    scene = bpy.context.scene
    world = bpy.data.worlds.new("Savanna Preview World") if not scene.world else scene.world
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.035, 0.075, 0.14, 1.0)
    background.inputs["Strength"].default_value = 0.32

    camera_data = bpy.data.cameras.new("Acacia Hero Camera")
    camera = bpy.data.objects.new("Acacia Hero Camera", camera_data)
    stage.objects.link(camera)
    camera.location = (12.8, -14.8, 9.2)
    camera_data.lens = 58
    look_at(camera, (0.0, 0.0, 3.65))
    scene.camera = camera

    add_area_light("Key - Golden Sun", (-6.5, -7.5, 13.0), 1250, (1.0, 0.43, 0.15), 6.0, (0, 0, 3.8), stage)
    add_area_light("Fill - Sky Blue", (7.5, -2.0, 8.0), 760, (0.25, 0.55, 1.0), 5.0, (0, 0, 3.6), stage)
    add_area_light("Rim - Warm", (3.0, 7.5, 10.5), 1150, (1.0, 0.23, 0.06), 4.0, (0, 0, 4.4), stage)

    sun_data = bpy.data.lights.new("Soft Sun", "SUN")
    sun_data.energy = 1.25
    sun_data.angle = math.radians(18)
    sun_data.color = (1.0, 0.55, 0.24)
    sun = bpy.data.objects.new("Soft Sun", sun_data)
    stage.objects.link(sun)
    sun.rotation_euler = (math.radians(28), math.radians(-22), math.radians(-35))


def configure_render() -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.image_settings.color_depth = "8"
    scene.render.filepath = PREVIEW_PATH
    scene.render.use_file_extension = True
    scene.render.resolution_percentage = 100
    scene.render.image_settings.compression = 20
    scene.render.film_transparent = False
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.use_compositing = True
    scene.view_settings.look = "AgX - Medium High Contrast"

    # A restrained bloom gives bright leaf tips a polished adventure-game sparkle.
    scene.use_nodes = True
    nodes = scene.node_tree.nodes
    nodes.clear()
    render_layers = nodes.new("CompositorNodeRLayers")
    glare = nodes.new("CompositorNodeGlare")
    glare.glare_type = "FOG_GLOW"
    glare.quality = "HIGH"
    glare.threshold = 1.15
    glare.size = 6
    composite = nodes.new("CompositorNodeComposite")
    scene.node_tree.links.new(render_layers.outputs["Image"], glare.inputs["Image"])
    scene.node_tree.links.new(glare.outputs["Image"], composite.inputs["Image"])


def export_asset(asset: bpy.types.Collection) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    mesh_objects = [obj for obj in asset.all_objects if obj.type == "MESH"]
    for obj in mesh_objects:
        obj.select_set(True)
    if not mesh_objects:
        raise RuntimeError("Asset_Acacia contains no exportable mesh objects")
    bpy.context.view_layer.objects.active = mesh_objects[0]
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
    asset = make_collection("Asset_Acacia")
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
    triangle_count = sum(len(obj.data.loop_triangles) for obj in asset.all_objects if obj.type == "MESH")
    print(f"ACACIA_COMPLETE meshes={mesh_count} seed={SEED}")
    print(f"ACACIA_PATH blend={BLEND_PATH}")
    print(f"ACACIA_PATH glb={GLB_PATH}")
    print(f"ACACIA_PATH preview={PREVIEW_PATH}")


if __name__ == "__main__":
    main()
