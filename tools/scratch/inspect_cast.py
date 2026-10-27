# blender -b --factory-startup? (no: need user addons) -P inspect_cast.py -- <cast> <out.json>
import bpy, sys, json, addon_utils
argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[0], argv[1]
addon_utils.enable("io_scene_cast", default_set=False)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
bpy.ops.import_scene.cast(filepath=src)
info = {"meshes": [], "armatures": []}
for o in bpy.data.objects:
    if o.type == "ARMATURE":
        bones = []
        for b in o.data.bones:
            bones.append({"name": b.name, "parent": b.parent.name if b.parent else None,
                          "head": [round(v, 3) for v in b.head_local]})
        info["armatures"].append({"name": o.name, "bones": bones})
    elif o.type == "MESH":
        me = o.data
        vg_use = {}
        for v in me.vertices:
            for g in v.groups:
                if g.weight > 0.01:
                    n = o.vertex_groups[g.group].name
                    vg_use[n] = vg_use.get(n, 0) + 1
        bb = [o.matrix_world @ __import__("mathutils").Vector(c) for c in o.bound_box]
        info["meshes"].append({"name": o.name, "verts": len(me.vertices), "faces": len(me.polygons),
                               "materials": [m.name for m in me.materials if m],
                               "groups": sorted(vg_use.items(), key=lambda x: -x[1])[:12],
                               "bbmin": [round(min(c[i] for c in bb), 2) for i in range(3)],
                               "bbmax": [round(max(c[i] for c in bb), 2) for i in range(3)]})
json.dump(info, open(out, "w"), indent=1)
print("INSPECT_OK", len(info["meshes"]), "meshes")
