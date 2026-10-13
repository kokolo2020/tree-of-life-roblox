"""Tree of Life V0.5 — stylized acacia tree asset.
Run: blender --background --python blender/generate_acacia.py
Creates a Blender scene and exports a glTF mesh to assets/generated/.
"""
import bpy, math, os, random
from mathutils import Vector
random.seed(17)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
def mat(name, color, roughness=0.85):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*color,1)
    p.inputs["Roughness"].default_value=roughness
    return m
bark=mat("Warm sculpted bark",(0.32,0.17,0.09))
bark_light=mat("Bark highlights",(0.46,0.27,0.13))
leaves=[mat("Canopy olive",(0.22,0.38,0.09)),mat("Canopy green",(0.30,0.49,0.12)),mat("Canopy sunlit",(0.43,0.57,0.16))]
def branch(name,points,radii,material,verts=9):
    curve=bpy.data.curves.new(name,"CURVE"); curve.dimensions="3D"
    curve.resolution_u=16; curve.bevel_depth=1; curve.bevel_resolution=3
    spline=curve.splines.new("BEZIER"); spline.bezier_points.add(len(points)-1)
    for i,(p,r) in enumerate(zip(points,radii)):
        bp=spline.bezier_points[i]; bp.co=p; bp.radius=r; bp.handle_left_type="AUTO"; bp.handle_right_type="AUTO"
    obj=bpy.data.objects.new(name,curve); bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active=obj; obj.select_set(True)
    bpy.ops.object.convert(target="MESH"); obj.select_set(False)
    return obj
# One meter approximately maps to 3.57 Roblox studs when imported at normal scale.
branch("Organic curved trunk",[(0,0,0),(0.1,0,1.8),(0.5,0,3.6),(0.8,0,5.5)], [.55,.44,.29,.17],bark)
tips=[]
for i in range(7):
    a=i*math.tau/7
    d=Vector((math.cos(a),math.sin(a),0))
    start=Vector((.6,0,4.7))
    mid=start+d*1.6+Vector((0,0,1.5))
    tip=start+d*3.5+Vector((0,0,2.0+random.uniform(-.3,.4)))
    branch("Spreading branch %02d"%i,[start,mid,tip],[.19,.13,.055],bark)
    tips.append(tip)
# Flattened, overlapping canopy lobes with nonuniform silhouettes.
for i,tip in enumerate(tips):
    for j in range(5):
        angle=j*math.tau/5
        x=tip.x+math.cos(angle)*.9; y=tip.y+math.sin(angle)*.9
        z=tip.z+random.uniform(-.1,.3)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=(x,y,z))
        o=bpy.context.object; o.name="Leaf cluster %02d-%02d"%(i,j)
        o.scale=(1.55,1.25,.35+random.uniform(0,.12))
        o.data.materials.append(leaves[(i+j)%len(leaves)])
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
# Bark knots as small contrasting raised geometry.
for z,a in [(1.0,.8),(2.3,2.6),(3.2,4.3)]:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,location=(math.cos(a)*.4,math.sin(a)*.4,z))
    o=bpy.context.object; o.name="Bark knot"; o.scale=(.18,.16,.35); o.data.materials.append(bark_light)
# Set origin near world zero, save editable scene and export for import.
root=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
out=os.path.join(root,"assets","generated"); os.makedirs(out,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,"savanna_acacia.blend"))
bpy.ops.export_scene.gltf(filepath=os.path.join(out,"savanna_acacia.glb"),export_format="GLB")
print("Generated",out)
