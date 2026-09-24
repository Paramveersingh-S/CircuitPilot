"""
CircuitPilot — Gerber Export Tool
-----------------------------------
Uses kicad-cli (KiCad 7+) to export Gerber and NC Drill files from a
.kicad_pcb file, then packages everything into a ZIP ready for JLCPCB/PCBWay.

Falls back gracefully if kicad-cli is not installed in the environment.
"""
import os
import zipfile
import subprocess
import shutil
from typing import Tuple


# Layers commonly required by PCB fabs
GERBER_LAYERS = (
    "F.Cu,B.Cu,"
    "F.SilkS,B.SilkS,"
    "F.Mask,B.Mask,"
    "F.Paste,B.Paste,"
    "Edge.Cuts"
)


def export_gerbers(kicad_pcb_path: str) -> Tuple[bool, str, str]:
    """
    Generate Gerber + drill files from *kicad_pcb_path* and
    return (success, zip_path, message).

    The ZIP is placed next to the .kicad_pcb file.
    """
    if not os.path.exists(kicad_pcb_path):
        return False, "", f"PCB file not found: {kicad_pcb_path}"

    base_dir    = os.path.dirname(kicad_pcb_path)
    session_id  = os.path.splitext(os.path.basename(kicad_pcb_path))[0]
    gerber_dir  = os.path.join(base_dir, "gerbers")
    zip_path    = os.path.join(base_dir, f"{session_id}_gerbers.zip")

    os.makedirs(gerber_dir, exist_ok=True)

    # ── Try kicad-cli export ────────────────────────────────────────────────
    kicad_cli = shutil.which("kicad-cli")
    if kicad_cli:
        try:
            # Export Gerbers
            r1 = subprocess.run(
                [
                    kicad_cli, "pcb", "export", "gerbers",
                    "--output", gerber_dir,
                    "--layers", GERBER_LAYERS,
                    "--no-protel-ext",
                    kicad_pcb_path,
                ],
                capture_output=True, text=True, timeout=60
            )
            # Export drill
            r2 = subprocess.run(
                [
                    kicad_cli, "pcb", "export", "drill",
                    "--output", gerber_dir + os.sep,
                    "--format", "gerber",
                    kicad_pcb_path,
                ],
                capture_output=True, text=True, timeout=60
            )
            if r1.returncode != 0 or r2.returncode != 0:
                msg = (r1.stderr + "\n" + r2.stderr).strip()
                return False, "", f"kicad-cli failed: {msg}"

        except Exception as e:
            return False, "", f"kicad-cli error: {e}"

    else:
        # ── Fallback: package the .kicad_pcb itself so user can export manually ──
        _write_readme(gerber_dir, kicad_pcb_path)

    # ── Zip everything ──────────────────────────────────────────────────────
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname in os.listdir(gerber_dir):
                fpath = os.path.join(gerber_dir, fname)
                if os.path.isfile(fpath):
                    zf.write(fpath, fname)
        return True, zip_path, "Gerbers exported successfully"
    except Exception as e:
        return False, "", f"Failed to create ZIP: {e}"


def _write_readme(gerber_dir: str, kicad_pcb_path: str):
    """Fallback: explain how to export manually."""
    readme_path = os.path.join(gerber_dir, "README.txt")
    with open(readme_path, "w") as f:
        f.write(
            "kicad-cli is not installed in this environment.\n"
            "To export Gerbers manually:\n"
            "1. Open the .kicad_pcb file in KiCad.\n"
            "2. Go to File -> Fabrication Outputs -> Gerbers.\n"
            "3. Select all copper + mask + silkscreen + Edge.Cuts layers.\n"
            "4. Click 'Generate Drill Files' then 'Plot'.\n"
            "\nPCB file location:\n"
            f"  {kicad_pcb_path}\n"
        )
    # Also copy the PCB into the zip so user gets it
    dst = os.path.join(gerber_dir, os.path.basename(kicad_pcb_path))
    if not os.path.exists(dst):
        shutil.copy2(kicad_pcb_path, dst)
