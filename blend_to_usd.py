import bpy
import os
import sys
import subprocess

# ==============================================================================
# 1. WORKER SCRIPT (Runs inside the Blender file)
# ==============================================================================
worker_script_code = """
import bpy
import os

target_folder = "{target_folder}"

print("=" * 60)
print(f"PROCESSING: {{bpy.data.filepath}}")
print("=" * 60)

# ------------------------------------------------------------------------
# STEP 1: RECONSTRUCT MATERIALS (The Logic that worked!)
# ------------------------------------------------------------------------
print("Scanning Materials...")

for obj in bpy.data.objects:
    if obj.type != 'MESH':
        continue
        
    for slot in obj.material_slots:
        mat = slot.material
        if not mat:
            continue
            
        # Ensure Nodes are ON
        mat.use_nodes = True
        tree = mat.node_tree
        nodes = tree.nodes
        links = tree.links
        
        # FIND THE TEXTURE
        texture_node = None
        candidates = []
        for node in nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                candidates.append(node)
        
        if candidates:
            # Pick first found, or prefer one with 'diff'/'col'
            texture_node = candidates[0]
            for c in candidates:
                if any(x in c.name.lower() for x in ['diff', 'col', 'albedo']):
                    texture_node = c
                    break
        
        if not texture_node:
            continue

        # ENSURE PRINCIPLED BSDF EXISTS
        principled = None
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                principled = node
                break
        
        if not principled:
            print(f"  [FIX] {{mat.name}}: Creating missing Principled BSDF")
            principled = nodes.new('ShaderNodeBsdfPrincipled')
            principled.location = (0, 300)

        # ENSURE OUTPUT EXISTS
        output_node = None
        for node in nodes:
            if node.type == 'OUTPUT_MATERIAL':
                output_node = node
                break
        
        if not output_node:
            print(f"  [FIX] {{mat.name}}: Creating missing Output")
            output_node = nodes.new('ShaderNodeOutputMaterial')
            output_node.location = (300, 300)

        # FORCE CONNECTIONS
        try:
            # Clean old links
            if principled.inputs['Base Color'].is_linked:
                for l in principled.inputs['Base Color'].links: links.remove(l)
            if output_node.inputs['Surface'].is_linked:
                 for l in output_node.inputs['Surface'].links: links.remove(l)

            # Link Texture -> Shader -> Output
            links.new(texture_node.outputs['Color'], principled.inputs['Base Color'])
            links.new(principled.outputs['BSDF'], output_node.inputs['Surface'])
            
            # Link Alpha if present
            if texture_node.image.alpha_mode != 'NONE':
                if principled.inputs.get('Alpha') and not principled.inputs['Alpha'].is_linked:
                    links.new(texture_node.outputs['Alpha'], principled.inputs['Alpha'])
                    # Set blend mode so transparency works in AR
                    mat.blend_method = 'BLEND'
            
        except Exception as e:
            print(f"  [ERROR] Linking failed: {{e}}")

# ------------------------------------------------------------------------
# STEP 2: RENAME UVs to 'st' (Critical for USDZ/Apple)
# ------------------------------------------------------------------------
print("\\nRenaming UV Maps to 'st' for USD compatibility...")
for mesh in bpy.data.meshes:
    if mesh.uv_layers:
        mesh.uv_layers[0].name = "st"

# ------------------------------------------------------------------------
# STEP 3: EXPORT USDZ
# ------------------------------------------------------------------------
filename = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
# Extension .usdz signals Blender to ZIP the textures
usdz_path = f"{{target_folder}}/{{filename}}.usdz"

print(f"\\nExporting to: {{usdz_path}}")

try:
    # BLENDER 5.0 SPECIFIC SETTINGS
    bpy.ops.wm.usd_export(
        filepath=usdz_path,
        selected_objects_only=False,
        export_materials=True,
        # 'NEW' creates local texture files so they can be zipped into the USDZ
        export_textures_mode='NEW', 
        relative_paths=True,
        overwrite_textures=True
    )
    print("USDZ Export SUCCESS.")
except Exception as e:
    print(f"USDZ Export FAILED: {{e}}")
"""

# ==============================================================================
# 2. LAUNCHER
# ==============================================================================

# Setup Paths
if bpy.data.filepath:
    scan_folder = os.path.dirname(bpy.data.filepath)
else:
    scan_folder = os.getcwd()

scan_folder = os.path.abspath(scan_folder)
export_folder = os.path.join(scan_folder, "export_usdz")
os.makedirs(export_folder, exist_ok=True)

print(f"\n--- SCANNING: {scan_folder} ---")

blend_files = [f for f in os.listdir(scan_folder) if f.lower().endswith(".blend")]

if not blend_files:
    print("No .blend files found.")
    sys.exit()

print(f"Found {len(blend_files)} files:")
print("-" * 30)
for i, f in enumerate(blend_files):
    print(f"  [{i}] {f}")
print("-" * 30)

try:
    choice = input(f"\n>>> ENTER ID (0-{len(blend_files)-1}): ")
    selected_index = int(choice) if choice.strip() else 0
except:
    selected_index = 0

selected_file = blend_files[selected_index]
selected_abs_path = os.path.join(scan_folder, selected_file)

print(f"\n---> PROCESSING: {selected_file}")

# Create temp worker
worker_path = os.path.join(scan_folder, "temp_usdz_worker.py")
clean_export_folder = export_folder.replace("\\", "/")

with open(worker_path, "w") as f:
    f.write(worker_script_code.format(target_folder=clean_export_folder))

# Launch Blender
blender_exe = bpy.app.binary_path
subprocess.call([blender_exe, selected_abs_path, "--background", "--python", worker_path])

# Cleanup
if os.path.exists(worker_path):
    os.remove(worker_path)

print("\n[DONE] Check 'export_usdz' folder.")