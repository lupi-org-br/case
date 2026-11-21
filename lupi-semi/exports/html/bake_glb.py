import math
import os
import re
import zipfile
import xml.etree.ElementTree as ET
import bpy
import bmesh
from mathutils import Matrix

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORTS_DIR = os.path.dirname(SCRIPT_DIR)


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def parse_bambu_3mf(path, invert_colors=False):
    with zipfile.ZipFile(path) as z:
        offset = [0.0, 0.0, 0.0]
        if "Metadata/model_settings.config" in z.namelist():
            cfg = ET.fromstring(z.read("Metadata/model_settings.config"))
            for m in cfg.iter("metadata"):
                k = m.attrib.get("key")
                v = m.attrib.get("value")
                if k == "source_offset_x":
                    offset[0] = float(v)
                elif k == "source_offset_y":
                    offset[1] = float(v)
                elif k == "source_offset_z":
                    offset[2] = float(v)

        model_key = next(
            (n for n in z.namelist() if n.startswith("3D/Objects/") and n.endswith(".model")),
            "3D/3dmodel.model",
        )
        root = ET.fromstring(z.read(model_key))
        ns = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}

        verts = [
            (
                float(v.attrib["x"]) + offset[0],
                float(v.attrib["y"]) + offset[1],
                float(v.attrib["z"]) + offset[2],
            )
            for v in root.findall(".//m:vertex", ns)
        ]

        faces = []
        mat_indices = []
        for t in root.findall(".//m:triangle", ns):
            faces.append((int(t.attrib["v1"]), int(t.attrib["v2"]), int(t.attrib["v3"])))
            is_accent = t.attrib.get("paint_color") == "8"
            if invert_colors:
                is_accent = not is_accent
            mat_indices.append(1 if is_accent else 0)

        return verts, faces, mat_indices


def parse_ascii_stl(path):
    verts = []
    faces = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        tri = []
        for line in f:
            s = line.lstrip()
            if s.startswith("vertex "):
                parts = s.split()
                verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
                tri.append(len(verts) - 1)
                if len(tri) == 3:
                    faces.append(tuple(tri))
                    tri = []
    return verts, faces


def create_mesh_object(name, verts, faces, materials, mat_indices=None):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    for mat in materials:
        mesh.materials.append(mat)
    if mat_indices is not None:
        mesh.polygons.foreach_set("material_index", mat_indices)
    mesh.update()

    # Solda vértices duplicados e garante normais apontando para fora
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def make_material(name, base_color, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = 0.0
    return mat


def attach_ao_node(mat, ao_image):
    nt = mat.node_tree
    # Cria grupo "glTF Material Output" padrão reconhecido pelo exportador glTF do Blender
    group_name = "glTF Material Output"
    if group_name not in bpy.data.node_groups:
        ng = bpy.data.node_groups.new(group_name, "ShaderNodeTree")
        ng.interface.new_socket(name="Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    else:
        ng = bpy.data.node_groups[group_name]

    tex_node = nt.nodes.new("ShaderNodeTexImage")
    tex_node.name = "AO_Bake_Target"
    tex_node.image = ao_image
    tex_node.select = True
    nt.nodes.active = tex_node

    gltf_out = nt.nodes.new("ShaderNodeGroup")
    gltf_out.node_tree = ng
    nt.links.new(tex_node.outputs["Color"], gltf_out.inputs["Occlusion"])


def apply_smooth_by_angle(obj, angle_deg=30.0):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle_deg))


def bake_ao(objects, resolution=1024, samples=32):
    ao_img = bpy.data.images.new("lupi_ao", width=resolution, height=resolution)
    ao_img.colorspace_settings.name = "Non-Color"

    # UV Smart Project compartilhado nos 3 objetos para um único atlas
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.008)
    bpy.ops.object.mode_set(mode="OBJECT")

    # Anexa o nó de imagem AO em todos os materiais
    seen_mats = set()
    for obj in objects:
        for mat in obj.data.materials:
            if mat and mat.name not in seen_mats:
                attach_ao_node(mat, ao_img)
                seen_mats.add(mat.name)

    # Configura Cycles CPU para bake de AO (sem denoiser para evitar manchas nas ilhas UV)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.world = bpy.data.worlds.new("AO_World")
    scene.world.light_settings.ao_factor = 1.0
    scene.world.light_settings.distance = 6.0

    bpy.ops.object.bake(type="AO", margin=2, use_clear=True)

    # Eleva o piso do AO (0..1 -> 0.42..1.0) para que fendas estreitas das letras (p, A, B) não escureçam demais
    pixels = list(ao_img.pixels)
    for i in range(0, len(pixels), 4):
        v = 0.42 + 0.58 * pixels[i]
        pixels[i] = v
        pixels[i + 1] = v
        pixels[i + 2] = v
    ao_img.pixels[:] = pixels
    ao_img.pack()
    return ao_img


def export_variant(objects, out_path, decimate_ratio=1.0):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        # Remove modificadores anteriores se existirem
        for mod in list(obj.modifiers):
            if mod.name in ("OptDecimate", "WeightedNormal"):
                obj.modifiers.remove(mod)
        if decimate_ratio < 0.999:
            mod = obj.modifiers.new("OptDecimate", "DECIMATE")
            mod.ratio = decimate_ratio
            mod.use_collapse_triangulate = True
        wn = obj.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")
        wn.keep_sharp = True
        wn.weight = 50
        obj.select_set(True)

    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_normals=True,
        export_materials="EXPORT",
        export_draco_mesh_compression_enable=False,
    )
    total_tris = sum(len(o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh().polygons) for o in objects)
    size_kb = os.path.getsize(out_path) / 1024
    print(f"Exported {os.path.basename(out_path)}: {total_tris} tris, {size_kb:.1f} KB")


def create_rear_screws(mat_primary):
    # Parafusos octogonais traseiros baseados em parts/screw.scad, posicionados nos furos de back.scad
    # Furos em back.scad: (-68.5, -84.0, -14.75) e (+59.5, -84.0, -14.75)
    bm = bmesh.new()
    rot_y_axis = Matrix.Rotation(math.pi * 0.5, 4, "X")

    for sx in (-68.5, 59.5):
        sy = -84.0
        sz = -14.75

        # Haste entrando no furo (+Y)
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=16,
            radius1=3.2,
            radius2=3.2,
            depth=7.0,
            matrix=Matrix.Translation((sx, sy + 2.5, sz)) @ rot_y_axis,
        )

        # Cabeça octogonal ($fn=8, r=4.7, h=5.0) projetada para trás (-Y)
        head_rot = rot_y_axis @ Matrix.Rotation(math.radians(22.5), 4, "Z")
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=8,
            radius1=4.7,
            radius2=4.7,
            depth=5.0,
            matrix=Matrix.Translation((sx, sy - 1.8, sz)) @ head_rot,
        )

    mesh = bpy.data.meshes.new("case_screws")
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat_primary)
    obj = bpy.data.objects.new("case_screws", mesh)
    bpy.context.collection.objects.link(obj)

    # Corta a fenda real (tipo chave de fenda) de fora a fora na face externa (-Y) com Boolean Difference
    slot_bm = bmesh.new()
    for sx in (-68.5, 59.5):
        bmesh.ops.create_cube(
            slot_bm,
            size=1.0,
            matrix=Matrix.Translation((sx, -88.2, -14.75)) @ Matrix.Diagonal((12.0, 2.2, 1.8, 1.0)),
        )
    slot_mesh = bpy.data.meshes.new("screw_slot_cutter")
    slot_bm.to_mesh(slot_mesh)
    slot_bm.free()
    slot_mesh.materials.append(mat_primary)
    slot_obj = bpy.data.objects.new("screw_slot_cutter", slot_mesh)
    bpy.context.collection.objects.link(slot_obj)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bool_mod = obj.modifiers.new("ScrewSlot", "BOOLEAN")
    bool_mod.operation = "DIFFERENCE"
    bool_mod.object = slot_obj
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)

    bpy.data.objects.remove(slot_obj, do_unlink=True)
    bpy.data.meshes.remove(slot_mesh, do_unlink=True)

    # Cria as 8 esferas de pega (icosphere uniforme, sem pinching nos polos) em um objeto separado
    # e faz BOOLEAN UNION para remover a metade interna enterrada (evitando vazamento de AO preto no bake)
    grips_bm = bmesh.new()
    for sx in (-68.5, 59.5):
        sy = -84.0
        sz = -14.75
        for i in range(8):
            ang = math.radians(i * 45.0)
            gx = sx + math.cos(ang) * 4.35
            gz = sz + math.sin(ang) * 4.35
            bmesh.ops.create_icosphere(
                grips_bm,
                subdivisions=2,
                radius=0.90,
                matrix=Matrix.Translation((gx, sy - 1.4, gz)),
            )
    grips_mesh = bpy.data.meshes.new("screw_grips_union")
    grips_bm.to_mesh(grips_mesh)
    grips_bm.free()
    grips_mesh.materials.append(mat_primary)
    grips_obj = bpy.data.objects.new("screw_grips_union", grips_mesh)
    bpy.context.collection.objects.link(grips_obj)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    union_mod = obj.modifiers.new("ScrewGrips", "BOOLEAN")
    union_mod.operation = "UNION"
    union_mod.object = grips_obj
    bpy.ops.object.modifier_apply(modifier=union_mod.name)

    bpy.data.objects.remove(grips_obj, do_unlink=True)
    bpy.data.meshes.remove(grips_mesh, do_unlink=True)
    return obj


def main():
    clear_scene()

    mat_primary = make_material("mat_primary", (0.957, 0.945, 0.918), 0.82)
    mat_accent = make_material("mat_accent", (1.0, 0.420, 0.102), 0.80)
    mat_ports = make_material("mat_ports", (0.388, 0.404, 0.431), 0.72)
    mat_screw = make_material("mat_screw", (0.957, 0.945, 0.918), 0.82)

    body_v, body_f, body_m = parse_bambu_3mf(os.path.join(EXPORTS_DIR, "lupi-case-body.3mf"), invert_colors=False)
    back_v, back_f, back_m = parse_bambu_3mf(os.path.join(EXPORTS_DIR, "lupi-case-back.3mf"), invert_colors=True)
    ports_v, ports_f = parse_ascii_stl(os.path.join(EXPORTS_DIR, "snes-ports.stl"))

    obj_body = create_mesh_object("case_body", body_v, body_f, [mat_primary, mat_accent], body_m)
    obj_back = create_mesh_object("case_back", back_v, back_f, [mat_primary, mat_accent], back_m)
    obj_ports = create_mesh_object("snes_ports", ports_v, ports_f, [mat_ports])
    obj_screws = create_rear_screws(mat_screw)

    bake_objects = [obj_body, obj_back, obj_ports]
    objects = [obj_body, obj_back, obj_ports, obj_screws]
    for obj in bake_objects:
        apply_smooth_by_angle(obj, 36.0)
    apply_smooth_by_angle(obj_screws, 50.0)

    # Bake AO suave e limpo no corpo/tampa/portas (sem espremer as micro-esferas dos parafusos no atlas 1024px)
    bake_ao(bake_objects, resolution=1024, samples=64)

    # Gera 3 variações de contagem de polígonos
    export_variant(objects, os.path.join(SCRIPT_DIR, "lupi-high.glb"), decimate_ratio=1.0)
    export_variant(objects, os.path.join(SCRIPT_DIR, "lupi-medium.glb"), decimate_ratio=0.45)
    export_variant(objects, os.path.join(SCRIPT_DIR, "lupi-low.glb"), decimate_ratio=0.20)


if __name__ == "__main__":
    main()
