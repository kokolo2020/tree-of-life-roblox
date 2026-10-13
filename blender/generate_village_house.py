"""Generate a stylized Savanna Village round house.
Run with Blender: blender --background --python blender/generate_village_house.py
"""
import bpy, math, os
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
def material(name,rgb):
 m=bpy.data.materials.new(name); m.diffuse_color=(*rgb,1); return m
clay=material('Sunbaked ochre plaster',(0.71,.40,.19))
thatch=material('Golden thatch',(.55,.34,.10))
wood=material('Dark carved wood',(.24,.12,.06))
trim=material('Painted turquoise trim',(.05,.43,.44))
def cyl(name,radius,depth,z,mat,vertices=48):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=(0,0,z))
 o=bpy.context.object;o.name=name;o.data.materials.append(mat);return o
cyl('Round plaster house',2.5,3,1.5,clay)
cyl('Painted foundation',2.62,.35,.18,trim)
# Roof uses tapered cones, with layered rings to create a stepped thatch silhouette.
for i in range(7):
 z=3.0+i*.35
 radius=3.2-i*.39
 bpy.ops.mesh.primitive_cone_add(vertices=64,radius1=radius,radius2=max(.06,radius-.43),depth=.48,location=(0,0,z))
 o=bpy.context.object;o.name='Overlapping thatch layer %02d'%i;o.data.materials.append(thatch)
# A door framed on the front (-Y) side.
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,-2.53,1.15))
door=bpy.context.object;door.name='Wooden entrance';door.dimensions=(1.25,.16,2.25);door.data.materials.append(wood)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
for x in (-.78,.78):
 bpy.ops.mesh.primitive_cube_add(size=1,location=(x,-2.65,1.17))
 o=bpy.context.object;o.name='Door frame';o.dimensions=(.13,.18,2.45);o.data.materials.append(trim)
for x in (-1.9,1.9):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=10,location=(x,-1.65,1.9))
 o=bpy.context.object;o.name='Decorative round window';o.scale=(.34,.15,.34);o.data.materials.append(wood)
# Detail: short radial wood beams protruding below eaves.
for i in range(16):
 a=i*math.tau/16
 bpy.ops.mesh.primitive_cube_add(size=1,location=(2.65*math.cos(a),2.65*math.sin(a),3.05))
 o=bpy.context.object;o.name='Roof support %02d'%i;o.dimensions=(.14,.75,.13);o.rotation_euler.z=a-math.pi/2;o.data.materials.append(wood)
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
out=os.path.join(root,'assets','generated');os.makedirs(out,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,'savanna_house.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(out,'savanna_house.glb'),export_format='GLB')
print('Generated village house in',out)
