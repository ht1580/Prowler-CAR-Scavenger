"""Print RUI meshes (parent bones, local bbox) of a v53 MDL using the workbench rui_editor parser."""
import sys
sys.path.insert(0, r"D:\CodexStorage\Projects\2026-09-08\w-3\TitanfallModWorkbench")
import rui_editor

doc = rui_editor.inspect_mdl(sys.argv[1])
print("bones", len(doc["bones"]), "rui", len(doc["meshes"]))
for m in doc["meshes"]:
    pts = [v["position"] for v in m["vertices"]]
    mn = [round(min(p[i] for p in pts), 2) for i in range(3)]
    mx = [round(max(p[i] for p in pts), 2) for i in range(3)]
    print(m["index"], m["name"], "parents", m["parentNames"], "verts", len(pts), "faces", len(m["faces"]), "local min", mn, "max", mx)
