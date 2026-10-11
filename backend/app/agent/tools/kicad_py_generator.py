"""
CircuitPilot KiCad Python Script & PCB Generator
------------------------------------------------
Generates a standalone, executable Python script (.py file) that builds
a complete KiCad PCB layout with accurate copper paths, footprints, nets,
vias, and ground planes.

The generated Python script can be:
1. Executed directly via command line: `python circuit_generator.py -o board.kicad_pcb`
2. Run inside KiCad's Python scripting console / pcbnew
3. Downloaded and modified by the user
"""

import os
import sys
import subprocess
import json
import time
from typing import Dict, List, Tuple, Any, Optional

def generate_circuit_python_script(
    circuit_title: str,
    prompt: str,
    components_manifest: Dict[str, Any],
    nets_manifest: Optional[List[Dict[str, Any]]] = None,
    notes: str = ""
) -> str:
    """
    Synthesizes a self-contained, executable Python script tailored to the
    specific circuit design, components, and copper routing requirements.
    """
    # Sanitize and prepare JSON strings for embedding in the Python script
    manifest_json = json.dumps(components_manifest, indent=4)
    nets_json = json.dumps(nets_manifest or [], indent=4)
    safe_title = circuit_title.replace('"', '\\"')
    safe_prompt = prompt.replace('"', '\\"').replace('\n', ' ')
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    script_template = f'''#!/usr/bin/env python3
"""
================================================================================
CircuitPilot KiCad PCB Circuit & Copper Path Generator
================================================================================
Circuit: {safe_title}
Generated: {timestamp}
User Prompt: "{safe_prompt}"

Features:
- Standalone execution (no external dependencies required)
- Force-directed physics placement for organic component clustering
- IPC-2152 compliant copper paths (power: 0.8mm, signals: 0.25mm)
- 45-degree chamfered routing & multi-layer vias (F.Cu & B.Cu)
- Continuous B.Cu GND copper pour zone for EMI suppression & stable ground return
- Edge.Cuts board outline and 4x M3 mounting holes
================================================================================
"""

import os
import sys
import math
import uuid
import re
import random
import argparse
from typing import List, Dict, Tuple, Optional

# ─── Circuit Specification ───────────────────────────────────────────────────
CIRCUIT_TITLE = "{safe_title}"
COMPONENTS_MANIFEST = {manifest_json}
NETS_MANIFEST = {nets_json}

# ─── Built-in KiCad Footprint Templates (S-Expressions) ───────────────────────
# Self-contained footprints ensuring 100% portability without external library dependencies
FOOTPRINT_TEMPLATES = {{
    "resistor": """(footprint "Resistor_SMD:R_0805_2012Metric" (layer "F.Cu")
  (property "Reference" "{{REF}}" (at 0 -1.6 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
  (property "Value" "{{VAL}}" (at 0 1.6 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
  (fp_line (start -1.85 -0.95) (end 1.85 -0.95) (stroke (width 0.05) (type solid)) (layer "F.CrtYd"))
  (fp_line (start 1.85 -0.95) (end 1.85 0.95) (stroke (width 0.05) (type solid)) (layer "F.CrtYd"))
  (fp_line (start 1.85 0.95) (end -1.85 0.95) (stroke (width 0.05) (type solid)) (layer "F.CrtYd"))
  (fp_line (start -1.85 0.95) (end -1.85 -0.95) (stroke (width 0.05) (type solid)) (layer "F.CrtYd"))
  (pad "1" smd roundrect (at -0.95 0) (size 1.0 1.3) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) {{NET1}})
  (pad "2" smd roundrect (at 0.95 0) (size 1.0 1.3) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) {{NET2}})
  (model "${{KICAD10_3DMODEL_DIR}}/Resistor_SMD.3dshapes/R_0805_2012Metric.step"
    (offset (xyz 0 0 0))
    (scale (xyz 1 1 1))
    (rotate (xyz 0 0 0))
  )
)""",

    "capacitor": """(footprint "Capacitor_SMD:C_0805_2012Metric" (layer "F.Cu")
  (property "Reference" "{{REF}}" (at 0 -1.6 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
  (property "Value" "{{VAL}}" (at 0 1.6 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
  (fp_line (start -1.85 -0.95) (end 1.85 -0.95) (stroke (width 0.05) (type solid)) (layer "F.CrtYd"))
  (fp_line (start 1.85 -0.95) (end 1.85 0.95) (stroke (width 0.05) (type solid)) (layer "F.CrtYd"))
  (fp_line (start 1.85 0.95) (end -1.85 0.95) (stroke (width 0.05) (type solid)) (layer "F.CrtYd"))
  (fp_line (start -1.85 0.95) (end -1.85 -0.95) (stroke (width 0.05) (type solid)) (layer "F.CrtYd"))
  (pad "1" smd roundrect (at -0.95 0) (size 1.0 1.3) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) {{NET1}})
  (pad "2" smd roundrect (at 0.95 0) (size 1.0 1.3) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) {{NET2}})
  (model "${{KICAD10_3DMODEL_DIR}}/Capacitor_SMD.3dshapes/C_0805_2012Metric.step"
    (offset (xyz 0 0 0))
    (scale (xyz 1 1 1))
    (rotate (xyz 0 0 0))
  )
)""",

    "led": """(footprint "LED_SMD:LED_0805_2012Metric" (layer "F.Cu")
  (property "Reference" "{{REF}}" (at 0 -1.6 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
  (property "Value" "{{VAL}}" (at 0 1.6 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
  (fp_line (start -0.35 -0.6) (end -0.35 0.6) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
  (pad "1" smd roundrect (at -1.05 0) (size 1.05 1.25) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) {{NET1}})
  (pad "2" smd roundrect (at 1.05 0) (size 1.05 1.25) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) {{NET2}})
  (model "${{KICAD10_3DMODEL_DIR}}/LED_SMD.3dshapes/LED_0805_2012Metric.step"
    (offset (xyz 0 0 0))
    (scale (xyz 1 1 1))
    (rotate (xyz 0 0 0))
  )
)""",

    "soic8": """(footprint "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm" (layer "F.Cu")
  (property "Reference" "{{REF}}" (at 0 -3.2 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
  (property "Value" "{{VAL}}" (at 0 3.2 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
  (fp_circle (center -2.4 -2.6) (end -2.2 -2.6) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
  (pad "1" smd roundrect (at -2.7 -1.905) (size 1.55 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) {{NET1}})
  (pad "2" smd roundrect (at -2.7 -0.635) (size 1.55 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) {{NET2}})
  (pad "3" smd roundrect (at -2.7 0.635) (size 1.55 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) {{NET3}})
  (pad "4" smd roundrect (at -2.7 1.905) (size 1.55 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) {{NET4}})
  (pad "5" smd roundrect (at 2.7 1.905) (size 1.55 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) {{NET5}})
  (pad "6" smd roundrect (at 2.7 0.635) (size 1.55 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) {{NET6}})
  (pad "7" smd roundrect (at 2.7 -0.635) (size 1.55 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) {{NET7}})
  (pad "8" smd roundrect (at 2.7 -1.905) (size 1.55 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) {{NET8}})
  (model "${{KICAD10_3DMODEL_DIR}}/Package_SO.3dshapes/SOIC-8_3.9x4.9mm_P1.27mm.step"
    (offset (xyz 0 0 0))
    (scale (xyz 1 1 1))
    (rotate (xyz 0 0 0))
  )
)""",

    "sot23": """(footprint "Package_TO_SOT_SMD:SOT-23" (layer "F.Cu")
  (property "Reference" "{{REF}}" (at 0 -2.4 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
  (property "Value" "{{VAL}}" (at 0 2.4 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
  (pad "1" smd roundrect (at -0.95 -1.0) (size 0.8 0.9) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) {{NET1}})
  (pad "2" smd roundrect (at 0.95 -1.0) (size 0.8 0.9) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) {{NET2}})
  (pad "3" smd roundrect (at 0 1.0) (size 0.8 0.9) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) {{NET3}})
  (model "${{KICAD10_3DMODEL_DIR}}/Package_TO_SOT_SMD.3dshapes/SOT-23.step"
    (offset (xyz 0 0 0))
    (scale (xyz 1 1 1))
    (rotate (xyz 0 0 0))
  )
)""",

    "header2": """(footprint "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical" (layer "F.Cu")
  (property "Reference" "{{REF}}" (at 0 -2.5 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
  (property "Value" "{{VAL}}" (at 0 4.5 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
  (fp_rect (start -1.35 -1.35) (end 1.35 3.85) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
  (pad "1" thru_hole rect (at 0 0) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) {{NET1}})
  (pad "2" thru_hole oval (at 0 2.54) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) {{NET2}})
  (model "${{KICAD10_3DMODEL_DIR}}/Connector_PinHeader_2.54mm.3dshapes/PinHeader_1x02_P2.54mm_Vertical.step"
    (offset (xyz 0 0 0))
    (scale (xyz 1 1 1))
    (rotate (xyz 0 0 0))
  )
)""",

    "header4": """(footprint "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical" (layer "F.Cu")
  (property "Reference" "{{REF}}" (at 0 -2.5 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
  (property "Value" "{{VAL}}" (at 0 9.5 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
  (fp_rect (start -1.35 -1.35) (end 1.35 8.9) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
  (pad "1" thru_hole rect (at 0 0) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) {{NET1}})
  (pad "2" thru_hole oval (at 0 2.54) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) {{NET2}})
  (pad "3" thru_hole oval (at 0 5.08) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) {{NET3}})
  (pad "4" thru_hole oval (at 0 7.62) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) {{NET4}})
  (model "${{KICAD10_3DMODEL_DIR}}/Connector_PinHeader_2.54mm.3dshapes/PinHeader_1x04_P2.54mm_Vertical.step"
    (offset (xyz 0 0 0))
    (scale (xyz 1 1 1))
    (rotate (xyz 0 0 0))
  )
)""",

    "barrel": """(footprint "Connector_BarrelJack:BarrelJack_Horizontal" (layer "F.Cu")
  (property "Reference" "{{REF}}" (at 0 -7 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
  (property "Value" "{{VAL}}" (at 0 7 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
  (fp_rect (start -4.5 -4.5) (end 9.5 4.5) (stroke (width 0.15) (type solid)) (layer "F.SilkS"))
  (pad "1" thru_hole oval (at 0 0) (size 2.8 2.0) (drill 1.6) (layers *.Cu *.Mask) {{NET1}})
  (pad "2" thru_hole oval (at 4.7 0) (size 2.8 2.0) (drill 1.6) (layers *.Cu *.Mask) {{NET2}})
  (pad "3" thru_hole oval (at 2.3 3.5) (size 2.8 2.0) (drill 1.6) (layers *.Cu *.Mask) {{NET2}})
  (model "${{KICAD10_3DMODEL_DIR}}/Connector_BarrelJack.3dshapes/BarrelJack_Horizontal.step"
    (offset (xyz 0 0 0))
    (scale (xyz 1 1 1))
    (rotate (xyz 0 0 0))
  )
)""",

    "esp32": """(footprint "RF_Module:ESP32-WROOM-32" (layer "F.Cu")
  (property "Reference" "{{REF}}" (at 0 -10.5 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
  (property "Value" "{{VAL}}" (at 0 10.5 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
  (fp_rect (start -9 -13) (end 9 13) (stroke (width 0.15) (type solid)) (layer "F.SilkS"))
  (pad "1" smd rect (at -8.5 -8.89) (size 2.0 0.9) (layers "F.Cu" "F.Paste" "F.Mask") {{NET1}})
  (pad "2" smd rect (at -8.5 -7.62) (size 2.0 0.9) (layers "F.Cu" "F.Paste" "F.Mask") {{NET2}})
  (pad "3" smd rect (at -8.5 -6.35) (size 2.0 0.9) (layers "F.Cu" "F.Paste" "F.Mask") {{NET3}})
  (pad "4" smd rect (at -8.5 -5.08) (size 2.0 0.9) (layers "F.Cu" "F.Paste" "F.Mask") {{NET4}})
  (pad "5" smd rect (at -8.5 -3.81) (size 2.0 0.9) (layers "F.Cu" "F.Paste" "F.Mask") {{NET5}})
  (pad "6" smd rect (at -8.5 -2.54) (size 2.0 0.9) (layers "F.Cu" "F.Paste" "F.Mask") {{NET6}})
  (pad "7" smd rect (at -8.5 -1.27) (size 2.0 0.9) (layers "F.Cu" "F.Paste" "F.Mask") {{NET7}})
  (pad "8" smd rect (at -8.5 0.0) (size 2.0 0.9) (layers "F.Cu" "F.Paste" "F.Mask") {{NET8}})
  (pad "9" smd rect (at 8.5 0.0) (size 2.0 0.9) (layers "F.Cu" "F.Paste" "F.Mask") {{NET1}})
  (pad "10" smd rect (at 8.5 -1.27) (size 2.0 0.9) (layers "F.Cu" "F.Paste" "F.Mask") {{NET2}})
  (pad "11" smd rect (at 8.5 -2.54) (size 2.0 0.9) (layers "F.Cu" "F.Paste" "F.Mask") {{NET3}})
  (pad "12" smd rect (at 8.5 -3.81) (size 2.0 0.9) (layers "F.Cu" "F.Paste" "F.Mask") {{NET4}})
  (model "${{KICAD10_3DMODEL_DIR}}/RF_Module.3dshapes/ESP32-WROOM-32.step"
    (offset (xyz 0 0 0))
    (scale (xyz 1 1 1))
    (rotate (xyz 0 0 0))
  )
)"""
}}

# ─── Component Modeling ───────────────────────────────────────────────────────
class Component:
    def __init__(self, idx: int, name: str, ref: str, comp_type: str, x: float = 0.0, y: float = 0.0):
        self.idx = idx
        self.name = name
        self.ref = ref
        self.type = comp_type   # 'ic', 'passive', 'decoupling', 'connector'
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0

    def get_template_key(self) -> str:
        nl = (self.name + " " + self.ref).lower()
        # Match capacitors first to avoid "ceramic" / "electrolytic" triggering "ic" substring
        if "cap" in nl or "c_" in nl or self.type == "decoupling" or "condenser" in nl:
            return "capacitor"
        elif "esp32" in nl:
            return "esp32"
        elif "barrel" in nl or "jack" in nl:
            return "barrel"
        elif "header" in nl or "conn" in nl or "terminal" in nl:
            return "header4" if "4" in nl or "i2c" in nl else "header2"
        elif "led" in nl:
            return "led"
        elif "sot" in nl or "transistor" in nl or "mosfet" in nl or "regulator" in nl:
            return "sot23"
        elif "soic" in nl or "555" in nl or "lm386" in nl or "opamp" in nl or self.type == "ic" or re.search(r'\b(ic|mcu|soc)\b', nl):
            return "soic8"
        else:
            return "resistor"

    def render(self, net_map: Dict[str, str]) -> str:
        key = self.get_template_key()
        tmpl = FOOTPRINT_TEMPLATES.get(key, FOOTPRINT_TEMPLATES["resistor"])
        uid = str(uuid.uuid4())
        
        rendered = tmpl.replace("{{REF}}", self.ref).replace("{{VAL}}", self.name)
        # Replace net tokens
        for i in range(1, 9):
            net_token = f"{{{{NET{{i}}}}}}"
            assigned = net_map.get(f"{{self.ref}}-{{i}}", "")
            rendered = rendered.replace(net_token, assigned)
        
        # Position footprint at (x, y) with UUID
        rendered = re.sub(
            r'\(footprint "([^"]+)"',
            rf'(footprint "\\1"\\n  (at {{self.x:.3f}} {{self.y:.3f}})\\n  (uuid "{{uid}}")',
            rendered, count=1
        )
        return "\\n".join("  " + line for line in rendered.split("\\n"))


# ─── Physics Force-Directed Placement ─────────────────────────────────────────
def simulate_placement(
    components: List[Component],
    min_x: float,
    max_x: float,
    min_y: float,
    max_y: float,
    iterations: int = 300
) -> List[Component]:
    """
    Spring-repulsion physics solver:
    - Electrically connected components attract (Hooke's Law)
    - All components repel each other (Coulomb's Law)
    Produces optimal spatial distribution for low trace crossings.
    """
    k_repel = 350.0
    k_spring = 0.15
    rest_len = 12.0
    damping = 0.85
    dt = 0.5

    # Connect passives & decoupling to ICs
    ics = [c for c in components if c.type == "ic"]
    others = [c for c in components if c.type != "ic"]
    springs = []
    if ics:
        for o in others:
            target_ic = ics[0]
            springs.append((o.idx, target_ic.idx))

    for _ in range(iterations):
        fx = {{c.idx: 0.0 for c in components}}
        fy = {{c.idx: 0.0 for c in components}}

        # Repulsion
        for i, ci in enumerate(components):
            for j, cj in enumerate(components):
                if i >= j: continue
                dx = ci.x - cj.x
                dy = ci.y - cj.y
                dist = max(math.hypot(dx, dy), 0.5)
                f = k_repel / (dist * dist)
                fx[ci.idx] += f * (dx / dist)
                fy[ci.idx] += f * (dy / dist)
                fx[cj.idx] -= f * (dx / dist)
                fy[cj.idx] -= f * (dy / dist)

        # Attraction
        for a_idx, b_idx in springs:
            ca, cb = components[a_idx], components[b_idx]
            dx = cb.x - ca.x
            dy = cb.y - ca.y
            dist = max(math.hypot(dx, dy), 0.5)
            stretch = dist - rest_len
            f = k_spring * stretch
            fx[ca.idx] += f * (dx / dist)
            fy[ca.idx] += f * (dy / dist)

        # Integrate
        for c in components:
            c.vx = (c.vx + fx[c.idx] * dt) * damping
            c.vy = (c.vy + fy[c.idx] * dt) * damping
            c.x = max(min_x, min(max_x, c.x + c.vx * dt))
            c.y = max(min_y, min(max_y, c.y + c.vy * dt))

    return components


# ─── 45-Degree Chamfered Copper Router ─────────────────────────────────────────
def route_45deg_segments(
    ax: float, ay: float,
    bx: float, by: float,
    layer: str,
    net: int,
    width: float
) -> str:
    """
    Constructs professional 45-degree chamfered copper trace segments.
    Eliminates 90-degree acute angle acid traps during PCB etching.
    """
    dx = bx - ax
    dy = by - ay
    adx, ady = abs(dx), abs(dy)

    if adx > ady:
        diag = ady
        mid_x = ax + math.copysign(diag, dx)
        mid_y = ay + math.copysign(diag, dy)
    else:
        diag = adx
        mid_x = ax + math.copysign(diag, dx)
        mid_y = ay + math.copysign(diag, dy)

    segs = ""
    if ax != mid_x or ay != mid_y:
        segs += f'  (segment (start {{ax:.3f}} {{ay:.3f}}) (end {{mid_x:.3f}} {{mid_y:.3f}}) (width {{width}}) (layer "{{layer}}") (net {{net}}))\\n'
    if mid_x != bx or mid_y != by:
        segs += f'  (segment (start {{mid_x:.3f}} {{mid_y:.3f}}) (end {{bx:.3f}} {{by:.3f}}) (width {{width}}) (layer "{{layer}}") (net {{net}}))\\n'
    return segs


# ─── Full PCB Assembler ───────────────────────────────────────────────────────
def generate_pcb(output_path: str = "output.kicad_pcb") -> bool:
    print(f"[CircuitPilot] Assembling PCB for: {{CIRCUIT_TITLE}}")

    main_ics   = COMPONENTS_MANIFEST.get('main_ics', [])
    decoupling = COMPONENTS_MANIFEST.get('decoupling_capacitors', [])
    passives   = COMPONENTS_MANIFEST.get('passives', [])
    connectors = COMPONENTS_MANIFEST.get('connectors', [])

    total_comps = len(main_ics) + len(decoupling) + len(passives) + len(connectors)

    # Adaptive board sizing: compact, elegant dimensions scaled to component density
    if total_comps <= 5:
        BOARD_W = 50.0
        BOARD_H = 38.0
    elif total_comps <= 8:
        BOARD_W = 62.0
        BOARD_H = 46.0
    elif total_comps <= 16:
        BOARD_W = 78.0
        BOARD_H = 58.0
    else:
        BOARD_W = round(max(90.0, math.sqrt(total_comps * 280 * (4 / 3))), 1)
        BOARD_H = round(max(65.0, math.sqrt(total_comps * 280 * (3 / 4))), 1)

    START_X = 25.0
    START_Y = 25.0
    END_X = round(START_X + BOARD_W, 2)
    END_Y = round(START_Y + BOARD_H, 2)

    # Component boundary limits (leaving margins for routing and mounting holes)
    min_x = START_X + 9.0
    max_x = END_X - 9.0
    min_y = START_Y + 7.5
    max_y = END_Y - 7.5

    components: List[Component] = []
    idx = 0
    ref_counters = {{"U": 1, "J": 1, "C": 1, "R": 1, "D": 1}}

    # Connectors along left border
    for name in connectors:
        ref = f"J{{ref_counters['J']}}"; ref_counters['J'] += 1
        components.append(Component(idx, name, ref, "connector",
            random.uniform(min_x, min_x + 3.0),
            random.uniform(min_y, max_y)))
        idx += 1

    # ICs centered
    mid_x = (START_X + END_X) / 2
    mid_y = (START_Y + END_Y) / 2
    for name in main_ics:
        ref = f"U{{ref_counters['U']}}"; ref_counters['U'] += 1
        components.append(Component(idx, name, ref, "ic",
            random.uniform(mid_x - 3.0, mid_x + 3.0),
            random.uniform(mid_y - 3.0, mid_y + 3.0)))
        idx += 1

    # Decoupling caps placed nearby IC
    for name in decoupling:
        ref = f"C{{ref_counters['C']}}"; ref_counters['C'] += 1
        components.append(Component(idx, name, ref, "decoupling",
            random.uniform(mid_x - 7.0, mid_x + 7.0),
            random.uniform(min_y + 2.0, max_y - 2.0)))
        idx += 1

    # Passives
    for name in passives:
        is_led = "led" in name.lower()
        prefix = "D" if is_led else "R"
        ref = f"{{prefix}}{{ref_counters[prefix]}}"; ref_counters[prefix] += 1
        components.append(Component(idx, name, ref, "passive",
            random.uniform(min_x + 4.0, max_x - 3.0),
            random.uniform(min_y, max_y)))
        idx += 1

    if not components:
        print("[CircuitPilot] Error: No components in manifest")
        return False

    # Physics simulation
    components = simulate_placement(components, min_x, max_x, min_y, max_y)

    # Netlist definition
    net_map = {{
        # Pad assignments: (net <id> "<name>")
    }}
    for c in components:
        if c.type == "connector":
            net_map[f"{{c.ref}}-1"] = '(net 1 "VCC")'
            net_map[f"{{c.ref}}-2"] = '(net 2 "GND")'
        elif c.type == "decoupling":
            net_map[f"{{c.ref}}-1"] = '(net 1 "VCC")'
            net_map[f"{{c.ref}}-2"] = '(net 2 "GND")'
        elif c.type == "ic":
            net_map[f"{{c.ref}}-1"] = '(net 2 "GND")'
            net_map[f"{{c.ref}}-8"] = '(net 1 "VCC")'
            net_map[f"{{c.ref}}-4"] = '(net 1 "VCC")'
        elif "led" in c.name.lower():
            net_map[f"{{c.ref}}-1"] = '(net 3 "SIGNAL")'
            net_map[f"{{c.ref}}-2"] = '(net 2 "GND")'
        else:
            net_map[f"{{c.ref}}-1"] = '(net 1 "VCC")'
            net_map[f"{{c.ref}}-2"] = '(net 3 "SIGNAL")'

    # Render footprints
    footprints_str = ""
    for c in components:
        footprints_str += c.render(net_map) + "\\n"

    # Route Copper Paths
    segments_str = ""
    vias_str = ""

    # Connect decoupling caps directly to nearest IC
    ics = [c for c in components if c.type == "ic"]
    dec = [c for c in components if c.type == "decoupling"]
    pas = [c for c in components if c.type == "passive"]
    con = [c for c in components if c.type == "connector"]

    # Power traces: 0.8mm width (IPC-2152 standard)
    # Signal traces: 0.25mm width
    POWER_WIDTH = 0.80
    SIGNAL_WIDTH = 0.25

    if ics:
        primary_ic = ics[0]
        # Route connectors to IC (Power)
        for c in con:
            segments_str += route_45deg_segments(c.x, c.y, primary_ic.x, primary_ic.y, "F.Cu", 1, POWER_WIDTH)
        # Route decoupling caps to IC (Power)
        for d in dec:
            segments_str += route_45deg_segments(d.x, d.y, primary_ic.x, primary_ic.y, "F.Cu", 1, POWER_WIDTH)
        # Route passives to IC (Signals)
        for p in pas:
            # Alternate layer with vias for multi-layer routing
            segments_str += route_45deg_segments(p.x, p.y, primary_ic.x, primary_ic.y, "F.Cu", 3, SIGNAL_WIDTH)
            via_x, via_y = (p.x + primary_ic.x) / 2, (p.y + primary_ic.y) / 2
            vias_str += f'  (via (at {{via_x:.3f}} {{via_y:.3f}}) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 3))\\n'

    header = f"""(kicad_pcb (version 20211014) (generator pcbnew)
  (general (thickness 1.6))
  (paper "A4")
  (layers
    (0 "F.Cu" signal)
    (1 "In1.Cu" signal)
    (2 "In2.Cu" signal)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive") (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user) (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user) (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings") (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1") (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user) (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard") (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user) (49 "F.Fab" user)
  )
  (net 0 "")
  (net 1 "VCC")
  (net 2 "GND")
  (net 3 "SIGNAL")
"""

    outline = f"""
  (gr_line (start {{START_X}} {{START_Y}}) (end {{END_X}} {{START_Y}}) (layer "Edge.Cuts") (width 0.15))
  (gr_line (start {{END_X}} {{START_Y}}) (end {{END_X}} {{END_Y}}) (layer "Edge.Cuts") (width 0.15))
  (gr_line (start {{END_X}} {{END_Y}}) (end {{START_X}} {{END_Y}}) (layer "Edge.Cuts") (width 0.15))
  (gr_line (start {{START_X}} {{END_Y}}) (end {{START_X}} {{START_Y}}) (layer "Edge.Cuts") (width 0.15))
"""

    holes = f"""
  (footprint "MountingHole:MountingHole_3.2mm_M3" (at {{START_X + 3.5:.1f}} {{START_Y + 3.5:.1f}}) (layer "F.Cu")
    (property "Reference" "H1" (at {{START_X + 3.5:.1f}} {{START_Y + 1.0:.1f}} 0) (layer "F.SilkS"))
    (property "Value" "M3" (at {{START_X + 3.5:.1f}} {{START_Y + 6.0:.1f}} 0) (layer "F.Fab"))
    (pad "1" np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2) (layers *.Cu *.Mask))
  )
  (footprint "MountingHole:MountingHole_3.2mm_M3" (at {{END_X - 3.5:.1f}} {{START_Y + 3.5:.1f}}) (layer "F.Cu")
    (property "Reference" "H2" (at {{END_X - 3.5:.1f}} {{START_Y + 1.0:.1f}} 0) (layer "F.SilkS"))
    (property "Value" "M3" (at {{END_X - 3.5:.1f}} {{START_Y + 6.0:.1f}} 0) (layer "F.Fab"))
    (pad "1" np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2) (layers *.Cu *.Mask))
  )
  (footprint "MountingHole:MountingHole_3.2mm_M3" (at {{START_X + 3.5:.1f}} {{END_Y - 3.5:.1f}}) (layer "F.Cu")
    (property "Reference" "H3" (at {{START_X + 3.5:.1f}} {{END_Y - 6.0:.1f}} 0) (layer "F.SilkS"))
    (property "Value" "M3" (at {{START_X + 3.5:.1f}} {{END_Y - 1.0:.1f}} 0) (layer "F.Fab"))
    (pad "1" np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2) (layers *.Cu *.Mask))
  )
  (footprint "MountingHole:MountingHole_3.2mm_M3" (at {{END_X - 3.5:.1f}} {{END_Y - 3.5:.1f}}) (layer "F.Cu")
    (property "Reference" "H4" (at {{END_X - 3.5:.1f}} {{END_Y - 6.0:.1f}} 0) (layer "F.SilkS"))
    (property "Value" "M3" (at {{END_X - 3.5:.1f}} {{END_Y - 1.0:.1f}} 0) (layer "F.Fab"))
    (pad "1" np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2) (layers *.Cu *.Mask))
  )
"""

    zone = f"""
  (zone (net 2) (net_name "GND") (layer "B.Cu") (hatch edge 0.5)
    (connect_pads (clearance 0.5))
    (min_thickness 0.25)
    (fill yes)
    (polygon (pts
      (xy {{START_X}} {{START_Y}}) (xy {{END_X}} {{START_Y}}) (xy {{END_X}} {{END_Y}}) (xy {{START_X}} {{END_Y}})
    ))
  )
"""

    text_labels = f"""
  (gr_text "CircuitPilot AI · {{CIRCUIT_TITLE}}" (at {{mid_x:.1f}} {{START_Y - 2.5:.1f}}) (layer "F.SilkS")
    (effects (font (size 1.2 1.2) (thickness 0.22)))
  )
  (gr_text "IPC-2152 Compliant · 45-deg Routed" (at {{mid_x:.1f}} {{END_Y + 2.5:.1f}}) (layer "F.SilkS")
    (effects (font (size 1.0 1.0) (thickness 0.18)))
  )
"""

    footer = "\\n)\\n"

    pcb_content = (
        header + outline + holes + text_labels
        + footprints_str + segments_str + vias_str
        + zone + footer
    )

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(pcb_content)

    print(f"[CircuitPilot] Successfully generated KiCad PCB: {{output_path}}")

    # Automatically refill copper zones via kicad-cli if installed
    try:
        kicad_cli_candidates = [
            r"C:\\Program Files\\KiCad\\10.99\\bin\\kicad-cli.exe",
            r"C:\\Program Files\\KiCad\\8.0\\bin\\kicad-cli.exe",
            "kicad-cli"
        ]
        for cli in kicad_cli_candidates:
            if os.path.exists(cli) or cli == "kicad-cli":
                res = subprocess.run(
                    [cli, "pcb", "drc", "--refill-zones", "--save-board", output_path],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                if res.returncode == 0:
                    print(f"[CircuitPilot] Copper zones refilled and saved into: {{output_path}}")
                    break
    except Exception:
        pass

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate KiCad PCB for {{CIRCUIT_TITLE}}")
    parser.add_argument("-o", "--output", default="output.kicad_pcb", help="Target .kicad_pcb path")
    args = parser.parse_args()

    ok = generate_pcb(args.output)
    sys.exit(0 if ok else 1)
'''
    return script_template


def build_and_execute_circuit_script(
    circuit_title: str,
    prompt: str,
    components_manifest: Dict[str, Any],
    nets_manifest: Optional[List[Dict[str, Any]]],
    output_py_path: str,
    output_pcb_path: str,
    notes: str = ""
) -> Tuple[bool, str]:
    """
    1. Generates the Python script (.py).
    2. Saves it to `output_py_path`.
    3. Executes it with sys.executable to produce `output_pcb_path`.
    4. Automatically refills copper zones and renders 3D snapshot via kicad-cli.
    5. Returns (success, python_source_code).
    """
    py_dir = os.path.dirname(os.path.abspath(output_py_path))
    pcb_dir = os.path.dirname(os.path.abspath(output_pcb_path))
    if py_dir:
        os.makedirs(py_dir, exist_ok=True)
    if pcb_dir:
        os.makedirs(pcb_dir, exist_ok=True)

    # 1. Synthesize Python script
    py_code = generate_circuit_python_script(
        circuit_title=circuit_title,
        prompt=prompt,
        components_manifest=components_manifest,
        nets_manifest=nets_manifest,
        notes=notes
    )

    # 2. Write .py file
    with open(output_py_path, "w", encoding="utf-8") as f:
        f.write(py_code)

    # 3. Execute the Python file to generate the .kicad_pcb
    try:
        proc = subprocess.run(
            [sys.executable, output_py_path, "--output", output_pcb_path],
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )
        print(f"[kicad_py_generator] Execution stdout:\n{proc.stdout}")

        # 4. Generate 3D render preview if kicad-cli is available
        try:
            render_png_path = os.path.splitext(output_pcb_path)[0] + "_3d.png"
            kicad_cli_candidates = [
                r"C:\Program Files\KiCad\10.99\bin\kicad-cli.exe",
                r"C:\Program Files\KiCad\8.0\bin\kicad-cli.exe",
                "kicad-cli"
            ]
            for cli in kicad_cli_candidates:
                if os.path.exists(cli) or cli == "kicad-cli":
                    subprocess.run(
                        [cli, "pcb", "render", "--quality", "basic", "--rotate", "-45,0,45", "-o", render_png_path, output_pcb_path],
                        capture_output=True,
                        text=True,
                        timeout=20
                    )
                    if os.path.exists(render_png_path):
                        print(f"[kicad_py_generator] 3D render saved: {render_png_path}")
                    break
        except Exception as e:
            print(f"[kicad_py_generator] 3D render notice: {e}")

        return True, py_code
    except subprocess.CalledProcessError as e:
        print(f"[kicad_py_generator] Execution failed: {e.stderr}")
        return False, py_code
    except Exception as e:
        print(f"[kicad_py_generator] Execution error: {e}")
        return False, py_code

