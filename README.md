# Blender-to-USDZ-CMD

A Python automation script for **Blender 5.0+** that exports  `.usdz` files with fully packed textures.

This tool was created to tackle common Blender export issues like missing textures, grey models, inverted normals, and broken Apple AR previews.

---

## 🚀 Why This Exists

Standard Blender exporters often fail with raw scan data or messy `.blend` files because:

* **Broken Materials:** Scans may lack a Principled BSDF node required for proper export.
* **Relative Paths:** Textures linked with `//` paths break when scripts run in background mode.
* **Apple Incompatibility:** iOS/ARKit ignores textures unless the primary UV map is named `st`.
* **Inverted Geometry:** Negative scale operations can result in inside-out meshes in USD.

This script fixes all of the above automatically before exporting.

---

## ✨ Features

* **🛡️ Launcher Architecture:** Runs a fresh Blender instance per file to ensure texture paths resolve correctly.
* **🎨 Auto-Material Reconstruction:** Detects missing Principled BSDF nodes and automatically creates a valid material connection to prevent grey clay models.
* **🍏 Apple AR Ready:** Renames the primary UV map to `st` for iOS compatibility.
* **🧼 Geometry Wash:** Applies object scale and recalculates normals to fix inverted faces.
* **📦 Smart Packing:** Uses Blender 5.0's `export_textures_mode='NEW'` to extract textures into the `.usdz` archive.
* **🖥️ Interactive CLI:** Scans folders and lets you choose which `.blend` file to process.

---

## 📋 Requirements

* **Blender 5.0 or later**

  > This script uses Blender 5.0's updated Python API (`export_textures_mode`).

---

## 🛠️ Usage

1. Place `blend_to_usd.py` in the folder containing your `.blend` files.
2. Open your terminal (PowerShell or Command Prompt).
3. Run the script using Blender’s Python interface:

```powershell
# Update the path to your Blender 5.0 installation
& "C:\Program Files\Blender Foundation\Blender 5.0\blender.exe" --background --python blend_to_usd.py
```

4. The script lists all `.blend` files in the folder.
5. Type the ID number of the file you want to process and press Enter.
6. The processed file appears in a new `./export_usdz` folder.

---

## ⚙️ How It Works

The script performs a **“Nuclear Repair”** on your file before export:

1. **Geometry:**

   * Selects all meshes
   * Applies scale
   * Recalculates normals (outside)

2. **UVs:**

   * Renames the primary UV map to `st`

3. **Material Nodes:**

   * Scans for any Image Texture node
   * Checks for Principled BSDF node
   * If missing, creates Principled BSDF and Material Output nodes
   * Connects Image Texture → Base Color → Surface Output

4. **Export:**

   * Generates a `.usdz` archive with textures physically embedded

---

## 📝 Customization

### Switching to FBX

If you prefer `.fbx` over `.usdz`:

1. Open the script.
2. Locate **STEP 4: EXPORT**.
3. Replace the USDZ export line with:

```python
bpy.ops.export_scene.fbx(
    filepath=fbx_path,
    use_selection=False,
    path_mode='COPY',
    embed_textures=True,
    mesh_smooth_type='FACE',
    apply_scale_options='FBX_SCALE_ALL'
)
```

---

## 📄 License

MIT License – free for personal and commercial use.
