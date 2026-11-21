import math
import os
import bpy
import bmesh
from mathutils import Matrix, Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORTS_DIR = os.path.dirname(SCRIPT_DIR)
SNES_STL = os.path.join(EXPORTS_DIR, "snes-ports.stl")
BOTTOM_PNG = os.path.join(SCRIPT_DIR, "pcb-bottom.png")
OUT_GLB = os.path.join(SCRIPT_DIR, "lupi-pcb.glb")


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_mat(name, color, roughness=0.45, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def add_box(bm, cx, cy, z0, sx, sy, sz, mat_idx, bevel=0.0):
    mat = Matrix.Translation((cx, cy, z0 + sz * 0.5)) @ Matrix.Diagonal((sx, sy, sz, 1.0))
    res = bmesh.ops.create_cube(bm, size=1.0, matrix=mat)
    verts = res["verts"]
    faces = list({f for v in verts for f in v.link_faces})
    for f in faces:
        f.material_index = mat_idx
    if bevel > 0.0:
        edges = list({e for f in faces for e in f.edges})
        bmesh.ops.bevel(
            bm,
            geom=edges,
            offset=bevel,
            segments=2,
            affect="EDGES",
            clamp_overlap=True,
        )
        for v in bm.verts:
            for f in v.link_faces:
                if f.material_index == 0 and mat_idx != 0:
                    pass
    return faces


def add_cyl(bm, cx, cy, z0, radius, height, mat_idx, segs=20, rot_x=0.0, rot_y=0.0):
    rot = Matrix.Rotation(rot_x, 4, "X") @ Matrix.Rotation(rot_y, 4, "Y")
    trans = Matrix.Translation((cx, cy, z0 + height * 0.5)) if (rot_x == 0 and rot_y == 0) else Matrix.Translation((cx, cy, z0))
    res = bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=segs,
        radius1=radius,
        radius2=radius,
        depth=height,
        matrix=trans @ rot,
    )
    verts = res["verts"]
    for f in {f for v in verts for f in v.link_faces}:
        f.material_index = mat_idx


def create_rounded_board_mesh(name, cx, cy, z0, sx, sy, sz, radius, mat_main, mat_edge, holes=()):
    bm = bmesh.new()
    # Perfil 2D com cantos arredondados
    hw, hd = sx * 0.5, sy * 0.5
    r = min(radius, hw * 0.5, hd * 0.5)
    segs = 6
    pts = []
    corners = [
        (hw - r, hd - r, 0.0),
        (-hw + r, hd - r, math.pi * 0.5),
        (-hw + r, -hd + r, math.pi),
        (hw - r, -hd + r, math.pi * 1.5),
    ]
    for ox, oy, a0 in corners:
        for i in range(segs + 1):
            a = a0 + (math.pi * 0.5) * (i / segs)
            pts.append((cx + ox + math.cos(a) * r, cy + oy + math.sin(a) * r))

    bot_v = [bm.verts.new((x, y, z0)) for x, y in pts]
    top_v = [bm.verts.new((x, y, z0 + sz)) for x, y in pts]
    bm.verts.ensure_lookup_table()

    # A face inferior (z0) é criada separadamente com UV planar exato para a textura pcb-bottom.png
    f_top = bm.faces.new(top_v)
    f_top.material_index = 0

    n = len(pts)
    for i in range(n):
        ni = (i + 1) % n
        f_side = bm.faces.new((bot_v[i], bot_v[ni], top_v[ni], top_v[i]))
        f_side.material_index = 1

    bmesh.ops.triangulate(bm, faces=bm.faces[:])

    # Anéis metálicos nos furos de montagem (com folga Z suficiente para zero z-fighting)
    for hx, hy, hr in holes:
        add_cyl(bm, hx, hy, z0 - 0.10, hr + 0.85, sz + 0.20, 2, segs=18)
        add_cyl(bm, hx, hy, z0 - 0.16, hr, sz + 0.32, 3, segs=16)

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat_main)
    mesh.materials.append(mat_edge)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def create_pcb_bottom_textured(cx, cy, z0, sx, sy, radius, img_path):
    # Cria a face inferior da placa (voltada para -Z) com UV planar 1:1 para pcb-bottom.png
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    hw, hd = sx * 0.5, sy * 0.5
    x_min, x_max = cx - hw, cx + hw
    y_min, y_max = cy - hd, cy + hd
    r = min(radius, hw * 0.5, hd * 0.5)
    segs = 6
    pts = []
    corners = [
        (hw - r, hd - r, 0.0),
        (-hw + r, hd - r, math.pi * 0.5),
        (-hw + r, -hd + r, math.pi),
        (hw - r, -hd + r, math.pi * 1.5),
    ]
    for ox, oy, a0 in corners:
        for i in range(segs + 1):
            a = a0 + (math.pi * 0.5) * (i / segs)
            pts.append((cx + ox + math.cos(a) * r, cy + oy + math.sin(a) * r))

    bot_v = [bm.verts.new((x, y, z0)) for x, y in pts]
    f_bot = bm.faces.new(list(reversed(bot_v)))
    f_bot.material_index = 0

    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    for f in bm.faces:
        for loop in f.loops:
            vx, vy = loop.vert.co.x, loop.vert.co.y
            # Visto de baixo (-Z olhando para +Z com +Y para cima): +X fica à esquerda (U=0), -X à direita (U=1)
            u = (x_max - vx) / (x_max - x_min)
            v = (vy - y_min) / (y_max - y_min)
            loop[uv_layer].uv = (u, v)

    mesh = bpy.data.meshes.new("main_pcb_bottom")
    bm.to_mesh(mesh)
    bm.free()

    mat = make_mat("pcb_bottom_tex", (1.0, 1.0, 1.0), roughness=0.34, metallic=0.05)
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    img = bpy.data.images.load(img_path)
    img.pack()
    tex_node = nt.nodes.new("ShaderNodeTexImage")
    tex_node.image = img
    nt.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])

    mesh.materials.append(mat)
    obj = bpy.data.objects.new("main_pcb_bottom", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def build_resistors(mats):
    bm = bmesh.new()
    cols = [112.0, 127.0, 142.0]
    rows = [-44.0, -47.0, -50.0, -53.0, -56.0, -59.0, -62.0, -65.0]

    for cx in cols:
        for cy in rows:
            # Corpo cerâmico azul-claro horizontal (ao longo de X)
            add_cyl(bm, cx, cy, 1.25, 1.05, 5.4, 0, segs=14, rot_y=math.pi * 0.5)
            # Extremidades ligeiramente mais grossas do resistor axial
            add_cyl(bm, cx - 2.2, cy, 1.25, 1.15, 1.0, 0, segs=14, rot_y=math.pi * 0.5)
            add_cyl(bm, cx + 2.2, cy, 1.25, 1.15, 1.0, 0, segs=14, rot_y=math.pi * 0.5)
            # Faixas de cor sutis
            for dx, m_band in [(-1.2, 2), (-0.4, 3), (0.4, 2), (1.3, 4)]:
                add_cyl(bm, cx + dx, cy, 1.25, 1.12, 0.35, m_band, segs=14, rot_y=math.pi * 0.5)
            # Terminais metálicos dobrados
            add_cyl(bm, cx, cy, 1.25, 0.28, 9.6, 1, segs=8, rot_y=math.pi * 0.5)
            add_cyl(bm, cx - 4.8, cy, -1.2, 0.28, 2.55, 1, segs=8)
            add_cyl(bm, cx + 4.8, cy, -1.2, 0.28, 2.55, 1, segs=8)
            # Pads de solda na placa
            add_cyl(bm, cx - 4.8, cy, 0.02, 0.72, 0.16, 1, segs=12)
            add_cyl(bm, cx + 4.8, cy, 0.02, 0.72, 0.16, 1, segs=12)

    mesh = bpy.data.meshes.new("resistors")
    bm.to_mesh(mesh)
    bm.free()
    for m in mats:
        mesh.materials.append(m)
    obj = bpy.data.objects.new("resistors", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def build_capacitors(mats):
    bm = bmesh.new()
    positions = [
        (88.53, -41.00),
        (42.53, -41.00),
        (88.53, -29.00),
        (42.53, -29.00),
    ]
    for cx, cy in positions:
        # Corpo cilíndrico azul-petróleo
        add_cyl(bm, cx, cy, 0.1, 3.85, 11.2, 0, segs=24)
        # Faixa lateral de polaridade (cinza claro)
        add_box(bm, cx + 3.55, cy, 0.5, 0.65, 1.8, 10.4, 1)
        # Topo metálico de alumínio escovado (acima do corpo para evitar z-fighting)
        add_cyl(bm, cx, cy, 11.30, 3.45, 0.28, 2, segs=24)
        # Terminais inferiores
        add_cyl(bm, cx - 1.5, cy, -1.4, 0.35, 1.6, 2, segs=8)
        add_cyl(bm, cx + 1.5, cy, -1.4, 0.35, 1.6, 2, segs=8)

    mesh = bpy.data.meshes.new("capacitors")
    bm.to_mesh(mesh)
    bm.free()
    for m in mats:
        mesh.materials.append(m)
    obj = bpy.data.objects.new("capacitors", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def build_pico_module(mats):
    # mats: [green_pcb, gold, dark_ic, silver, white_btn, smd_dark]
    bm = bmesh.new()
    cx, cy, z0 = 122.66, -29.60, 1.0
    w, d, h = 51.0, 21.0, 1.0

    # Placa verde principal
    add_box(bm, cx, cy, z0, w, d, h, 0)

    # 20 pads dourados castelados em cada lado (passo 2.54mm)
    for i in range(20):
        px = cx - 24.13 + i * 2.54
        for py in (cy - d * 0.5 + 0.6, cy + d * 0.5 - 0.6):
            add_cyl(bm, px, py, z0 - 0.10, 0.85, h + 0.20, 1, segs=12)
            # Pino de conexão até a placa mãe
            add_cyl(bm, px, py, -0.4, 0.32, 1.5, 1, segs=8)

    # Chip central QFN (RP2040-style, sem logo)
    add_box(bm, cx - 0.4, cy, z0 + h, 7.0, 7.0, 0.9, 2)
    # Cristal e memória flash ao lado do chip
    add_box(bm, cx - 9.5, cy + 3.2, z0 + h, 3.2, 2.5, 0.7, 3)
    add_box(bm, cx - 9.5, cy - 3.5, z0 + h, 4.0, 3.0, 0.8, 2)
    # Regulador e indutor próximo ao USB
    add_box(bm, cx + 11.0, cy + 4.0, z0 + h, 3.0, 3.0, 1.2, 2)
    add_box(bm, cx + 11.0, cy - 4.0, z0 + h, 2.5, 2.5, 0.8, 2)

    # Botão tátil branco (BOOTSEL)
    add_box(bm, cx + 12.5, cy + 0.2, z0 + h, 4.2, 3.2, 1.1, 3)
    add_cyl(bm, cx + 12.5, cy + 0.2, z0 + h + 1.0, 1.05, 0.6, 4, segs=14)

    # Conector Micro-USB metálico na borda direita
    add_box(bm, cx + 23.2, cy, z0 + h, 5.6, 7.6, 2.6, 3)
    add_box(bm, cx + 25.8, cy, z0 + h + 0.5, 0.8, 5.8, 1.6, 5)

    # Pequenos passivos SMD (0603)
    smd_offsets = [
        (-16.0, 2.0), (-16.0, -2.0), (-13.0, 0.0),
        (5.5, 4.2), (5.5, -4.2), (7.5, 0.0),
        (17.5, 3.5), (17.5, -3.5),
    ]
    for ox, oy in smd_offsets:
        add_box(bm, cx + ox, cy + oy, z0 + h, 1.3, 0.88, 0.55, 5)
        add_box(bm, cx + ox - 0.82, cy + oy, z0 + h, 0.34, 0.96, 0.62, 3)
        add_box(bm, cx + ox + 0.82, cy + oy, z0 + h, 0.34, 0.96, 0.62, 3)

    mesh = bpy.data.meshes.new("pico_module")
    bm.to_mesh(mesh)
    bm.free()
    for m in mats:
        mesh.materials.append(m)
    obj = bpy.data.objects.new("pico_module", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def build_esp32_module(mats):
    # mats: [black_pcb, silver, gold, dark_ic, copper_ant, white_led, smd_brown]
    bm = bmesh.new()
    # Montado sobre barras paralelas de socket 2.54mm (z0=12.40 alinha os USB-C no centro do recorte traseiro)
    cx, cy, z0 = 63.13, -52.60, 12.40
    w, d, h = 27.94, 57.15, 1.02

    # Placa preta do DevKit
    add_box(bm, cx, cy, z0, w, d, h, 0)

    # 2 barras paralelas de socket fêmea (22 pinos cada) + pinos macho encaixados
    for side_x in (cx - 12.7, cx + 12.7):
        # Soquete fêmea preto soldado na placa mãe (altura 8.5mm)
        add_box(bm, side_x, cy, 0.0, 2.54, 55.8, 8.5, 3)
        # Base plástica do header macho sob o ESP32
        add_box(bm, side_x, cy, z0 - 2.5, 2.54, 55.8, 2.5, 3)
        for i in range(22):
            py = cy - 26.67 + i * 2.54
            # Pino dourado atravessando do header macho para o soquete fêmea
            add_cyl(bm, side_x, py, 8.2, 0.30, 1.8, 2, segs=6)
            add_cyl(bm, side_x, py, z0 + h + 0.02, 0.72, 0.18, 2, segs=10)
            add_cyl(bm, side_x, py, -1.2, 0.28, 1.3, 2, segs=6)

    # Módulo RF superior: substrato + blindagem metálica prateada + antena impressa
    add_box(bm, cx, cy + 21.8, z0 + h + 0.02, 18.0, 25.4, 0.8, 0)
    # Blindagem metálica prateada (18 x 18 x 2.3 mm)
    add_box(bm, cx, cy + 18.2, z0 + h + 0.84, 17.6, 17.6, 2.3, 1)
    # Trilha da antena PCB (segmentos encostados sem sobreposição coplanar)
    ant_y = cy + 29.0
    ant_z = z0 + h + 0.84
    add_box(bm, cx - 6.0, ant_y + 1.2, ant_z, 1.0, 3.4, 0.16, 4)
    add_box(bm, cx - 3.0, ant_y + 3.4, ant_z, 7.0, 1.0, 0.16, 4)
    add_box(bm, cx, ant_y + 1.8, ant_z, 1.0, 2.2, 0.16, 4)
    add_box(bm, cx + 3.0, ant_y + 0.2, ant_z, 7.0, 1.0, 0.16, 4)
    add_box(bm, cx + 6.0, ant_y + 2.1, ant_z, 1.0, 2.8, 0.16, 4)

    # 2 conectores USB-C fêmea metálicos na traseira do DevKit (com cavidade escura e lingueta interna)
    for ux in (cx - 5.8, cx + 5.8):
        add_box(bm, ux, cy - 25.2, z0 + h, 8.9, 7.3, 3.16, 1)
        # Cavidade fêmea escura na face traseira (-Y)
        add_box(bm, ux, cy - 28.75, z0 + h + 0.45, 7.4, 0.5, 2.26, 3)
        # Lingueta interna central horizontal do USB-C fêmea
        add_box(bm, ux, cy - 28.85, z0 + h + 1.33, 6.2, 0.45, 0.50, 2)

    # 2 botões táteis (RST / BOOT)
    for bx in (cx - 4.2, cx + 4.2):
        add_box(bm, bx, cy - 5.2, z0 + h, 3.8, 3.0, 1.1, 1)
        add_cyl(bm, bx, cy - 5.2, z0 + h + 1.0, 0.95, 0.55, 3, segs=12)

    # Regulador SOT-223 e cristal
    add_box(bm, cx - 5.0, cy - 16.5, z0 + h, 6.5, 3.5, 1.4, 3)
    add_box(bm, cx - 5.0, cy - 18.4, z0 + h, 3.2, 1.0, 0.35, 1)
    add_box(bm, cx - 5.1, cy - 9.6, z0 + h, 4.8, 3.6, 0.8, 1)

    # LED RGB branco + passivos SMD
    add_box(bm, cx + 5.2, cy - 11.5, z0 + h, 4.6, 4.6, 1.3, 5)
    for ox, oy in [(4.5, -17.0), (7.0, -17.0), (-2.0, -12.0), (1.0, -12.0), (5.5, -1.5), (-5.5, -1.5)]:
        add_box(bm, cx + ox, cy + oy, z0 + h, 1.4, 0.96, 0.6, 6)
        add_box(bm, cx + ox - 0.88, cy + oy, z0 + h, 0.36, 1.06, 0.66, 1)
        add_box(bm, cx + ox + 0.88, cy + oy, z0 + h, 0.36, 1.06, 0.66, 1)

    mesh = bpy.data.meshes.new("esp32_module")
    bm.to_mesh(mesh)
    bm.free()
    for m in mats:
        mesh.materials.append(m)
    obj = bpy.data.objects.new("esp32_module", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def build_daughterboards(mats):
    # mats: [cyan_pcb, silver, dark_header, dark_ic]
    bm = bmesh.new()
    for cx in (92.00, 34.00):
        # Comprimento ajustado (35mm) para ficar totalmente contido dentro da tampa traseira (y_case = -77.8)
        cy = -64.91
        w, d, h = 23.0, 35.0, 1.4
        z0 = 3.0
        # Placa azul-ciano do leitor de SD
        add_box(bm, cx, cy, z0, w, d, h, 0)
        # 4 furos de canto com anel metálico (com folga Z para zero z-fighting)
        for dx in (-9.3, 9.3):
            for dy in (-15.3, 15.3):
                add_cyl(bm, cx + dx, cy + dy, z0 - 0.12, 1.3, h + 0.24, 1, segs=14)
        # Barra de pinos frontal (6 pinos)
        hdr_y = -49.5
        add_box(bm, cx, hdr_y, 0.0, 15.4, 2.6, 3.0, 2)
        for i in range(6):
            px = cx - 6.35 + i * 2.54
            add_cyl(bm, px, hdr_y, z0 + h + 0.02, 0.85, 0.18, 1, segs=12)
            add_cyl(bm, px, hdr_y, -1.2, 0.3, 1.3, 1, segs=8)
        # Slot metálico de cartão SD sob a placa (alinhado às janelas A e B sem vazar)
        add_box(bm, cx, cy - 2.0, 0.4, 15.2, 26.0, 2.55, 1)

    mesh = bpy.data.meshes.new("daughterboards")
    bm.to_mesh(mesh)
    bm.free()
    for m in mats:
        mesh.materials.append(m)
    obj = bpy.data.objects.new("daughterboards", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def build_db15_connector(mats):
    # mats: [blue_body, silver, dark_face, gold]
    bm = bmesh.new()
    # Centralizado na janela VGA (cx=124.2 -> X_case=+36.06) e recuado para não avançar sobre a tampa
    cx, cy = 124.20, -78.35

    # Corpo azul traseiro
    add_box(bm, cx, cy + 2.5, 0.0, 30.2, 14.0, 12.2, 0)
    # Flange metálico frontal (virado para -Y, rente ao recorte interno)
    add_box(bm, cx, cy - 4.8, 0.2, 30.4, 1.2, 11.8, 1)
    # Blindagem metálica em D projetada para trás (-Y)
    add_box(bm, cx, cy - 7.6, 2.0, 17.5, 4.8, 8.2, 1)
    # Miolo fêmea azul/escuro com 15 furos (3 fileiras de 5) com anel de contato dourado
    add_box(bm, cx, cy - 9.8, 2.5, 15.6, 0.8, 7.0, 0)
    for row in (-1, 0, 1):
        for col in range(5):
            px = cx - 4.6 + col * 2.3 + (0.6 if row == 0 else 0.0)
            pz = 6.0 + row * 2.0
            # Anel metálico dourado do contato fêmea
            add_cyl(bm, px, cy - 10.22, pz, 0.58, 0.14, 3, segs=12, rot_x=math.pi * 0.5)
            # Furo escuro central (female pinhole)
            add_cyl(bm, px, cy - 10.30, pz, 0.38, 0.14, 2, segs=10, rot_x=math.pi * 0.5)
    # 2 parafusos sextavados laterais
    for dx in (-12.2, 12.2):
        add_cyl(bm, cx + dx, cy - 7.2, 6.0, 2.0, 4.2, 1, segs=6, rot_x=math.pi * 0.5)
        add_cyl(bm, cx + dx, cy - 9.0, 6.0, 1.05, 1.0, 2, segs=10, rot_x=math.pi * 0.5)

    mesh = bpy.data.meshes.new("db15_connector")
    bm.to_mesh(mesh)
    bm.free()
    for m in mats:
        mesh.materials.append(m)
    obj = bpy.data.objects.new("db15_connector", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def build_audio_dac_module(mats):
    # Módulo DAC I2S (estilo PCM5102A) com saída P2 3.5mm apontada para o recorte lateral (-X)
    # mats: [black_pcb, silver, dark_ic, smd_tan, smd_dark, dark_bore]
    bm = bmesh.new()

    # Posição alinhada ao recorte lateral de áudio em parts/audio.scad (Y_case=-36 -> Y_pcb=-40.65, Z_case=0 -> Z_pcb=8.06)
    cx, cy = 27.5, -31.5
    w, d, h = 17.0, 27.5, 1.2
    z0 = 4.4
    top_z = z0 + h  # 5.6

    # Placa preta do módulo de áudio
    add_box(bm, cx, cy, z0, w, d, h, 0)

    # Header de 6 pinos (passo 2.54mm) na extremidade +Y sustentando o módulo na placa mãe
    hdr_y = cy + d * 0.5 - 2.2
    add_box(bm, cx, hdr_y, 0.0, 15.6, 2.54, z0, 2)
    for i in range(6):
        px = cx - 6.35 + i * 2.54
        # Pad oval prateado no topo da placa preta
        add_box(bm, px, hdr_y, top_z + 0.02, 1.5, 2.4, 0.16, 1)
        add_cyl(bm, px, hdr_y, -1.2, 0.30, z0 + h + 1.45, 1, segs=8)

    # Chip DAC central (TSSOP/SOIC) com pernas laterais prateadas
    ic_x, ic_y = cx, cy + 1.5
    add_box(bm, ic_x, ic_y, top_z + 0.02, 4.6, 5.2, 1.15, 2)
    for i in range(5):
        py = ic_y - 1.6 + i * 0.8
        add_box(bm, ic_x - 2.7, py, top_z + 0.02, 0.9, 0.32, 0.25, 1)
        add_box(bm, ic_x + 2.7, py, top_z + 0.02, 0.9, 0.32, 0.25, 1)

    # Capacitores MLCC bege/marrom (como no print) + terminais prateados
    tan_caps = [
        (cx - 4.8, cy + 5.8, 1.8, 3.2, 1.3),
        (cx - 1.8, cy + 5.8, 1.8, 3.2, 1.3),
        (cx + 2.0, cy + 6.4, 1.2, 2.2, 0.9),
        (cx + 4.8, cy + 3.2, 1.2, 2.2, 0.9),
        (cx - 4.8, cy - 2.6, 1.4, 2.4, 1.0),
        (cx - 1.6, cy - 2.8, 1.4, 2.4, 1.0),
        (cx - 4.5, cy - 6.2, 3.0, 1.8, 1.2),
    ]
    for tx, ty, tw, td, th in tan_caps:
        add_box(bm, tx, ty, top_z + 0.02, tw, td, th, 3)
        if td >= tw:
            add_box(bm, tx, ty - td * 0.5 - 0.15, top_z + 0.02, tw + 0.1, 0.35, th + 0.06, 1)
            add_box(bm, tx, ty + td * 0.5 + 0.15, top_z + 0.02, tw + 0.1, 0.35, th + 0.06, 1)
        else:
            add_box(bm, tx - tw * 0.5 - 0.15, ty, top_z + 0.02, 0.35, td + 0.1, th + 0.06, 1)
            add_box(bm, tx + tw * 0.5 + 0.15, ty, top_z + 0.02, 0.35, td + 0.1, th + 0.06, 1)

    # Resistores SMD escuros
    for rx, ry in [(cx + 2.5, cy - 4.0), (cx + 2.5, cy - 6.4), (cx - 1.5, cy + 9.2)]:
        add_box(bm, rx, ry, top_z + 0.02, 2.0, 1.1, 0.6, 4)
        add_box(bm, rx - 1.1, ry, top_z + 0.02, 0.36, 1.18, 0.66, 1)
        add_box(bm, rx + 1.1, ry, top_z + 0.02, 0.36, 1.18, 0.66, 1)

    # Conector P2 3.5mm (PJ-320A) na extremidade -Y, com bocal voltado para -X (saída lateral do case)
    jack_y = -40.65
    jack_z = top_z + 0.02  # 5.62; centro do cilindro em 5.62 + 2.45 = 8.07 (alinhado a Z_case = 0.0)
    # Corpo preto do conector P2 (12 x 6 x 4.9 mm)
    add_box(bm, 25.0, jack_y, jack_z, 12.0, 6.0, 4.9, 2)
    # 3 contatos metálicos quadrados no topo (característicos do PJ-320A da foto)
    for jx in (21.5, 25.0, 28.5):
        add_box(bm, jx, jack_y, jack_z + 4.92, 1.8, 1.8, 0.18, 1)
        add_box(bm, jx, jack_y + 3.25, top_z + 0.02, 1.1, 0.7, 0.35, 1)
    # Bocal cilíndrico do P2 apontado para -X (alinhado ao recorte lateral)
    barrel_z = jack_z + 2.45
    add_cyl(bm, 17.8, jack_y, barrel_z, 2.5, 2.6, 2, segs=20, rot_y=math.pi * 0.5)
    # Furo interno escuro de 3.5mm
    add_cyl(bm, 16.45, jack_y, barrel_z, 1.75, 0.4, 5, segs=18, rot_y=math.pi * 0.5)

    mesh = bpy.data.meshes.new("audio_dac_module")
    bm.to_mesh(mesh)
    bm.free()
    for m in mats:
        mesh.materials.append(m)
    obj = bpy.data.objects.new("audio_dac_module", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def import_own_snes_ports(mat_ports):
    # Reutiliza o próprio snes-ports.stl gerado do snes_port.scad do usuário
    verts = []
    faces = []
    with open(SNES_STL, "r", encoding="utf-8", errors="replace") as f:
        tri = []
        for line in f:
            s = line.lstrip()
            if s.startswith("vertex "):
                parts = s.split()
                # Alinha o snes-ports.stl (centro -3.5, -0.1, 0.235) à borda frontal da PCB (84.64, -4.75, 8.30)
                verts.append((
                    float(parts[1]) + 88.14,
                    float(parts[2]) - 4.65,
                    float(parts[3]) + 8.06,
                ))
                tri.append(len(verts) - 1)
                if len(tri) == 3:
                    faces.append(tuple(tri))
                    tri = []

    mesh = bpy.data.meshes.new("snes_ports")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat_ports)
    mesh.update()

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("snes_ports", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def attach_ao_node(mat, ao_image):
    nt = mat.node_tree
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


def bake_ao(objects, resolution=1024, samples=48):
    ao_img = bpy.data.images.new("pcb_ao", width=resolution, height=resolution)
    ao_img.colorspace_settings.name = "Non-Color"

    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.006)
    bpy.ops.object.mode_set(mode="OBJECT")

    seen_mats = set()
    for obj in objects:
        for mat in obj.data.materials:
            if mat and mat.name not in seen_mats:
                attach_ao_node(mat, ao_img)
                seen_mats.add(mat.name)

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.world = bpy.data.worlds.new("PCB_AO_World")
    scene.world.light_settings.ao_factor = 1.0
    scene.world.light_settings.distance = 12.0

    bpy.ops.object.bake(type="AO", margin=2, use_clear=True)
    ao_img.pack()
    return ao_img


def main():
    clear_scene()

    # Paleta PBR Clean Room
    mat_pcb_blue = make_mat("pcb_solder_mask", (0.015, 0.16, 0.38), roughness=0.34, metallic=0.05)
    mat_fr4_edge = make_mat("pcb_fr4_edge", (0.58, 0.56, 0.34), roughness=0.55, metallic=0.10)
    mat_gold = make_mat("pcb_gold", (0.85, 0.72, 0.22), roughness=0.28, metallic=0.82)
    mat_silver = make_mat("pcb_silver", (0.82, 0.83, 0.85), roughness=0.24, metallic=0.85)
    mat_dark_hole = make_mat("pcb_hole", (0.05, 0.06, 0.08), roughness=0.85, metallic=0.0)
    mat_res_body = make_mat("resistor_body", (0.28, 0.68, 0.88), roughness=0.42, metallic=0.02)
    mat_band_red = make_mat("band_red", (0.72, 0.14, 0.12), roughness=0.5, metallic=0.0)
    mat_band_blk = make_mat("band_black", (0.08, 0.08, 0.09), roughness=0.5, metallic=0.0)
    mat_cap_blue = make_mat("cap_sleeve", (0.04, 0.52, 0.72), roughness=0.32, metallic=0.06)
    mat_cap_stripe = make_mat("cap_stripe", (0.75, 0.84, 0.90), roughness=0.4, metallic=0.05)
    mat_pico_green = make_mat("pico_green", (0.04, 0.46, 0.22), roughness=0.38, metallic=0.04)
    mat_dark_ic = make_mat("ic_epoxy", (0.11, 0.11, 0.12), roughness=0.68, metallic=0.0)
    mat_white_btn = make_mat("white_plastic", (0.94, 0.94, 0.92), roughness=0.45, metallic=0.0)
    mat_smd_dark = make_mat("smd_dark", (0.18, 0.16, 0.15), roughness=0.55, metallic=0.05)
    mat_esp_black = make_mat("esp_black_pcb", (0.08, 0.085, 0.095), roughness=0.38, metallic=0.05)
    mat_copper = make_mat("copper_trace", (0.78, 0.50, 0.22), roughness=0.30, metallic=0.82)
    mat_smd_brown = make_mat("smd_brown", (0.48, 0.32, 0.18), roughness=0.48, metallic=0.02)
    mat_cyan_pcb = make_mat("daughter_cyan", (0.04, 0.52, 0.84), roughness=0.35, metallic=0.04)
    mat_db15_blue = make_mat("db15_blue", (0.02, 0.42, 0.78), roughness=0.45, metallic=0.02)
    mat_snes_gray = make_mat("snes_port_gray", (0.39, 0.40, 0.43), roughness=0.72, metallic=0.08)

    # 1. Placa principal azul (130 x 74 x 1.6 mm)
    holes = [
        (23.0, -12.0, 1.6),
        (145.0, -12.0, 1.6),
        (23.0, -78.0, 1.6),
        (145.0, -78.0, 1.6),
    ]
    obj_board = create_rounded_board_mesh(
        "main_pcb", 84.0, -45.0, -1.6, 130.0, 74.0, 1.6, 2.2,
        mat_pcb_blue, mat_fr4_edge, holes=holes,
    )
    obj_board.data.materials.append(mat_gold)
    obj_board.data.materials.append(mat_dark_hole)
    obj_bottom = create_pcb_bottom_textured(84.0, -45.0, -1.6, 130.0, 74.0, 2.2, BOTTOM_PNG)

    # 2. Componentes Clean Room
    obj_res = build_resistors([mat_res_body, mat_silver, mat_band_red, mat_band_blk, mat_gold])
    obj_cap = build_capacitors([mat_cap_blue, mat_cap_stripe, mat_silver])
    obj_pico = build_pico_module([mat_pico_green, mat_gold, mat_dark_ic, mat_silver, mat_white_btn, mat_smd_dark])
    obj_esp = build_esp32_module([mat_esp_black, mat_silver, mat_gold, mat_dark_ic, mat_copper, mat_white_btn, mat_smd_brown])
    obj_db = build_daughterboards([mat_cyan_pcb, mat_silver, mat_dark_ic, mat_smd_dark])
    obj_db15 = build_db15_connector([mat_db15_blue, mat_silver, mat_dark_ic, mat_gold])
    obj_audio = build_audio_dac_module([mat_esp_black, mat_silver, mat_dark_ic, mat_smd_brown, mat_smd_dark, mat_dark_hole])
    obj_snes = import_own_snes_ports(mat_snes_gray)

    ao_objects = [obj_board, obj_res, obj_cap, obj_pico, obj_esp, obj_db, obj_db15, obj_audio, obj_snes]
    objects = ao_objects + [obj_bottom]

    # Suaviza normais por ângulo + Weighted Normal
    for obj in ao_objects:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(32.0))
        wn = obj.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")
        wn.keep_sharp = True
        wn.weight = 50

    # Bake de Ambient Occlusion (Cycles) nos componentes/topo (preservando o UV planar da face inferior)
    bake_ao(ao_objects, resolution=1024, samples=48)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(
        filepath=OUT_GLB,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_normals=True,
        export_materials="EXPORT",
        export_draco_mesh_compression_enable=False,
    )

    total_tris = sum(len(o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh().polygons) for o in objects)
    size_kb = os.path.getsize(OUT_GLB) / 1024
    print(f"Exported Clean-Room {os.path.basename(OUT_GLB)}: {total_tris} tris, {size_kb:.1f} KB")


if __name__ == "__main__":
    main()

