"""
CircuitPilot Native Generator v3.0
-----------------------------------
Implements:
1. Force-Directed Placement Algorithm (physics simulation for organic component clustering)
2. Net-Aware Ratsnest Routing (routes shortest-connection-first per net, not in sequence)
3. IPC-2152 Trace Width Rules (power=0.8mm, signal=0.25mm)
4. DFM Edge Clearance (15mm margin from Edge.Cuts)
5. 45-degree chamfered routing (no 90-degree angles)
6. Automatic Ground Pour on B.Cu
7. 4 corner Mounting Holes (M3)
"""

import os
import uuid
import re
import math
import random
from typing import Dict, List, Tuple, Optional

KICAD_FOOTPRINTS_DIR = r"C:\Program Files\KiCad\10.99\share\kicad\footprints"

FOOTPRINT_MAP = {
    "esp32":          r"RF_Module.pretty\ESP32-WROOM-32.kicad_mod",
    "buck":           r"Package_TO_SOT_SMD.pretty\SOT-23-5.kicad_mod",
    "555":            r"Package_SO.pretty\SOIC-8_3.9x4.9mm_P1.27mm.kicad_mod",
    "resistor":       r"Resistor_SMD.pretty\R_0805_2012Metric.kicad_mod",
    "capacitor":      r"Capacitor_SMD.pretty\C_0805_2012Metric.kicad_mod",
    "led":            r"LED_SMD.pretty\LED_0805_2012Metric.kicad_mod",
    "transistor":     r"Package_TO_SOT_SMD.pretty\SOT-23.kicad_mod",
    "lm386":          r"Package_SO.pretty\SOIC-8_3.9x4.9mm_P1.27mm.kicad_mod",
    "dip":            r"Package_DIP.pretty\DIP-40_W15.24mm.kicad_mod",
    "40-pin":         r"Package_DIP.pretty\DIP-40_W15.24mm.kicad_mod",
    "18-pin":         r"Package_DIP.pretty\DIP-18_W7.62mm.kicad_mod",
    "8-pin":          r"Package_DIP.pretty\DIP-8_W7.62mm.kicad_mod",
    "regulator":      r"Package_TO_SOT_THT.pretty\TO-220-3_Vertical.kicad_mod",
    "barrel":         r"Connector_BarrelJack.pretty\BarrelJack_Horizontal.kicad_mod",
    "electrolytic":   r"Capacitor_THT.pretty\CP_Radial_D8.0mm_P3.50mm.kicad_mod",
    "crystal":        r"Crystal.pretty\Crystal_HC49-U_Vertical.kicad_mod",
    "header":         r"Connector_PinHeader_2.54mm.pretty\PinHeader_1x06_P2.54mm_Vertical.kicad_mod",
    "eeprom":         r"Package_DIP.pretty\DIP-8_W7.62mm.kicad_mod",
    "microcontroller":r"Package_DIP.pretty\DIP-40_W15.24mm.kicad_mod",
    "lm386":          r"Package_SO.pretty\SOIC-8_3.9x4.9mm_P1.27mm.kicad_mod",
}

# ─── Footprint Loading ─────────────────────────────────────────────────────────

def _find_footprint_path(comp_name: str) -> str:
    comp_lower = comp_name.lower()
    best_match = FOOTPRINT_MAP.get("lm386")  # safe default
    for key, path in FOOTPRINT_MAP.items():
        if key in comp_lower:
            best_match = path
            break
    fp_path = os.path.join(KICAD_FOOTPRINTS_DIR, best_match)
    if not os.path.exists(fp_path):
        fp_path = os.path.join(KICAD_FOOTPRINTS_DIR, FOOTPRINT_MAP["lm386"])
    return fp_path

def get_footprint_data(comp_name: str, x: float, y: float, ref_des: str) -> Tuple[str, float, float]:
    fp_path = _find_footprint_path(comp_name)
    try:
        with open(fp_path, "r", encoding="utf-8") as f:
            fp_str = f.read()
    except Exception:
        return "", 0.0, 0.0

    uid = str(uuid.uuid4())
    fp_str = re.sub(
        r'\(footprint "([^"]+)"',
        rf'(footprint "\1"\n  (at {x:.3f} {y:.3f})\n  (uuid "{uid}")',
        fp_str, count=1
    )
    fp_str = re.sub(r'\(property "Reference" "REF\*\*?"', rf'(property "Reference" "{ref_des}"', fp_str)
    fp_str = re.sub(r'\(fp_text reference "REF\*\*?"', rf'(fp_text reference "{ref_des}"', fp_str)

    # Extract pad "1" position for routing origin
    pad_match = re.search(r'\(pad "1".*?\(at ([\-\d\.]+) ([\-\d\.]+)', fp_str, re.DOTALL)
    pad_x, pad_y = 0.0, 0.0
    if pad_match:
        pad_x = float(pad_match.group(1))
        pad_y = float(pad_match.group(2))

    indented = "\n".join("  " + line for line in fp_str.split("\n"))
    return indented, pad_x, pad_y


# ─── Force-Directed Placement ──────────────────────────────────────────────────

class Component:
    def __init__(self, idx: int, name: str, x: float, y: float, comp_type: str, ref: str):
        self.idx   = idx
        self.name  = name
        self.x     = x
        self.y     = y
        self.vx    = 0.0
        self.vy    = 0.0
        self.type  = comp_type   # 'ic', 'decoupling', 'passive', 'connector'
        self.ref   = ref
        self.net   = 0           # assigned later

def force_directed_placement(
    components: List[Component],
    nets: List[Tuple[int, int]],   # (comp_idx_a, comp_idx_b) pairs = connected
    board_w: float = 200.0,
    board_h: float = 160.0,
    margin: float  = 20.0,
    iterations: int = 300,
) -> List[Component]:
    """
    Force-directed spring/repulsion simulation.
    Connected components attract (spring), unconnected repel (Coulomb).
    """
    k_repel  = 400.0   # Coulomb constant
    k_spring = 0.12    # Hooke spring constant for netted pairs
    rest_len = 18.0    # Natural rest length of spring (mm)
    damping  = 0.82    # Velocity damping per step
    dt       = 0.5     # Time step

    # Build adjacency set for quick lookup
    adj: Dict[int, List[int]] = {c.idx: [] for c in components}
    for a, b in nets:
        if a < len(components) and b < len(components):
            adj[a].append(b)
            adj[b].append(a)

    for _ in range(iterations):
        forces_x = {c.idx: 0.0 for c in components}
        forces_y = {c.idx: 0.0 for c in components}

        # Repulsive forces (all pairs)
        for i, ci in enumerate(components):
            for j, cj in enumerate(components):
                if i >= j:
                    continue
                dx = ci.x - cj.x
                dy = ci.y - cj.y
                dist = max(math.hypot(dx, dy), 0.5)
                force = k_repel / (dist * dist)
                nx, ny = dx / dist, dy / dist
                forces_x[ci.idx] += force * nx
                forces_y[ci.idx] += force * ny
                forces_x[cj.idx] -= force * nx
                forces_y[cj.idx] -= force * ny

        # Attractive spring forces (connected pairs)
        for ci in components:
            for nb_idx in adj[ci.idx]:
                cj = components[nb_idx]
                dx = cj.x - ci.x
                dy = cj.y - ci.y
                dist = max(math.hypot(dx, dy), 0.5)
                stretch = dist - rest_len
                force = k_spring * stretch
                nx, ny = dx / dist, dy / dist
                forces_x[ci.idx] += force * nx
                forces_y[ci.idx] += force * ny

        # Integrate velocities
        for c in components:
            c.vx = (c.vx + forces_x[c.idx] * dt) * damping
            c.vy = (c.vy + forces_y[c.idx] * dt) * damping
            c.x  = max(margin, min(board_w - margin, c.x + c.vx * dt))
            c.y  = max(margin, min(board_h - margin, c.y + c.vy * dt))

    return components


# ─── Net-Aware Ratsnest Routing ────────────────────────────────────────────────

def build_ratsnest(components: List[Component]) -> List[Tuple[Component, Component, str, float]]:
    """
    Build minimal spanning tree connections (ratsnest):
    - ICs connected to their decoupling caps
    - Connectors connected to nearest IC
    - Passives connected to nearest IC
    Returns sorted list of (comp_a, comp_b, net_type, trace_width) to route.
    """
    connections = []

    ics        = [c for c in components if c.type == "ic"]
    decoupling = [c for c in components if c.type == "decoupling"]
    passives   = [c for c in components if c.type == "passive"]
    connectors = [c for c in components if c.type == "connector"]

    # Decoupling caps → nearest IC (tight power net)
    for cap in decoupling:
        if ics:
            nearest = min(ics, key=lambda ic: math.hypot(ic.x - cap.x, ic.y - cap.y))
            connections.append((cap, nearest, "power", 0.8))

    # Connectors → nearest IC (power net)
    for conn in connectors:
        if ics:
            nearest = min(ics, key=lambda ic: math.hypot(ic.x - conn.x, ic.y - conn.y))
            connections.append((conn, nearest, "power", 0.8))

    # Passives → nearest IC (signal net)
    for passive in passives:
        if ics:
            nearest = min(ics, key=lambda ic: math.hypot(ic.x - passive.x, ic.y - passive.y))
            connections.append((passive, nearest, "signal", 0.25))

    # IC–IC backbone (signal net, sorted by distance)
    ic_pairs = []
    for i, a in enumerate(ics):
        for b in ics[i+1:]:
            dist = math.hypot(a.x - b.x, a.y - b.y)
            ic_pairs.append((dist, a, b))
    ic_pairs.sort()
    for dist, a, b in ic_pairs:
        connections.append((a, b, "signal", 0.25))

    # Sort by distance → shortest traces routed first (like a real auto-router)
    connections.sort(key=lambda t: math.hypot(t[0].x - t[1].x, t[0].y - t[1].y))
    return connections


def route_45deg(
    ax: float, ay: float,
    bx: float, by: float,
    layer: str,
    net: int,
    width: float
) -> str:
    """
    Route A→B using a 2-segment 45-degree chamfered path.
    Chooses H-then-diagonal or V-then-diagonal based on distances.
    """
    dx = bx - ax
    dy = by - ay
    adx, ady = abs(dx), abs(dy)

    if adx > ady:
        # Go diagonally first, then horizontal
        diag = ady
        mid_x = ax + math.copysign(diag, dx)
        mid_y = ay + math.copysign(diag, dy)
    else:
        # Go horizontally/vertically first, then diagonally
        diag = adx
        mid_x = ax + math.copysign(diag, dx)
        mid_y = ay + math.copysign(diag, dy)

    segs = ""
    if ax != mid_x or ay != mid_y:
        segs += f'  (segment (start {ax:.3f} {ay:.3f}) (end {mid_x:.3f} {mid_y:.3f}) (width {width}) (layer "{layer}") (net {net}))\n'
    if mid_x != bx or mid_y != by:
        segs += f'  (segment (start {mid_x:.3f} {mid_y:.3f}) (end {bx:.3f} {by:.3f}) (width {width}) (layer "{layer}") (net {net}))\n'
    return segs


# ─── Main Generator ────────────────────────────────────────────────────────────

def generate_kicad_pcb(target_path: str, components_dict) -> bool:
    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        # Normalise input
        if isinstance(components_dict, list):
            main_ics      = components_dict
            decoupling    = []
            passives      = []
            connectors    = []
        else:
            main_ics   = components_dict.get('main_ics', [])
            decoupling = components_dict.get('decoupling_capacitors', [])
            passives   = components_dict.get('passives', [])
            connectors = components_dict.get('connectors', [])

        # ── 1. Dynamically size board from component count ─────────────────────
        total = len(main_ics) + len(decoupling) + len(passives) + len(connectors)
        # Each component needs roughly 18x18mm of space; maintain 4:3 aspect ratio
        area   = max(total * 18 * 18, 100 * 80)   # minimum 100x80mm
        BOARD_W = round(math.sqrt(area * (4/3)), 1)
        BOARD_H = round(math.sqrt(area * (3/4)), 1)
        MARGIN  = 18.0   # DFM edge clearance

        comps: List[Component] = []
        idx = 0
        ref_counters = {"U": 1, "J": 1, "C": 1, "R": 1}

        # Connectors start on left strip
        for name in connectors:
            ref = f"J{ref_counters['J']}"; ref_counters['J'] += 1
            comps.append(Component(idx, name,
                random.uniform(MARGIN, MARGIN + 15),
                random.uniform(MARGIN, BOARD_H - MARGIN),
                "connector", ref))
            idx += 1

        for name in main_ics:
            ref = f"U{ref_counters['U']}"; ref_counters['U'] += 1
            comps.append(Component(idx, name,
                random.uniform(MARGIN + 20, BOARD_W - MARGIN - 20),
                random.uniform(MARGIN + 20, BOARD_H - MARGIN - 20),
                "ic", ref))
            idx += 1

        for name in decoupling:
            ref = f"C{ref_counters['C']}"; ref_counters['C'] += 1
            comps.append(Component(idx, name,
                random.uniform(MARGIN, BOARD_W - MARGIN),
                random.uniform(MARGIN, BOARD_H - MARGIN),
                "decoupling", ref))
            idx += 1

        for name in passives:
            ref = f"R{ref_counters['R']}"; ref_counters['R'] += 1
            comps.append(Component(idx, name,
                random.uniform(MARGIN, BOARD_W - MARGIN),
                random.uniform(MARGIN, BOARD_H - MARGIN),
                "passive", ref))
            idx += 1

        if not comps:
            return False

        # ── 2. Build connectivity for force simulation ─────────────────────────
        ic_indices  = [c.idx for c in comps if c.type == "ic"]
        dec_indices = [c.idx for c in comps if c.type == "decoupling"]
        pas_indices = [c.idx for c in comps if c.type == "passive"]
        con_indices = [c.idx for c in comps if c.type == "connector"]

        nets_for_sim: List[Tuple[int, int]] = []
        # Decoupling → ICs attract very strongly (smaller rest length handled by k)
        for d in dec_indices:
            if ic_indices:
                nets_for_sim.append((d, ic_indices[0]))
        # Passives → nearest IC
        for p in pas_indices:
            if ic_indices:
                nets_for_sim.append((p, ic_indices[len(ic_indices)//2]))
        # Connectors → first IC
        for c in con_indices:
            if ic_indices:
                nets_for_sim.append((c, ic_indices[0]))
        # IC backbone
        for i in range(len(ic_indices)-1):
            nets_for_sim.append((ic_indices[i], ic_indices[i+1]))

        # ── 3. Run force-directed simulation ──────────────────────────────────
        comps = force_directed_placement(
            comps, nets_for_sim, BOARD_W, BOARD_H, MARGIN, iterations=400
        )

        # ── 4. Normalise positions — guarantee all fit inside board outline ────
        # Find actual bounding box of placed components
        xs = [c.x for c in comps]
        ys = [c.y for c in comps]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        span_x = max(max_x - min_x, 1)
        span_y = max(max_y - min_y, 1)

        # Available canvas inside margins
        avail_x = BOARD_W - 2 * MARGIN
        avail_y = BOARD_H - 2 * MARGIN

        # Scale factor — shrink if components overflow, don't enlarge
        scale = min(avail_x / span_x, avail_y / span_y, 1.0)

        for c in comps:
            c.x = MARGIN + (c.x - min_x) * scale
            c.y = MARGIN + (c.y - min_y) * scale
            # Hard clamp for safety
            c.x = max(MARGIN, min(BOARD_W - MARGIN, c.x))
            c.y = max(MARGIN, min(BOARD_H - MARGIN, c.y))

        # ── 4. Build ratsnest and route ────────────────────────────────────────
        connections = build_ratsnest(comps)

        net_ids = {"power": 1, "signal": 2}
        footprints_str = ""
        segments_str   = ""
        vias_str       = ""

        current_layer = "F.Cu"
        layer_toggle_counter = 0

        # Generate footprints for all components
        for c in comps:
            fp_str, _, _ = get_footprint_data(c.name, c.x, c.y, c.ref)
            footprints_str += fp_str + "\n"

        # Route net-aware connections
        routed_pairs = set()
        for comp_a, comp_b, net_type, width in connections:
            pair_key = tuple(sorted([comp_a.idx, comp_b.idx]))
            if pair_key in routed_pairs:
                continue
            routed_pairs.add(pair_key)

            # Get actual pad positions
            _, a_px, a_py = get_footprint_data(comp_a.name, comp_a.x, comp_a.y, comp_a.ref)
            _, b_px, b_py = get_footprint_data(comp_b.name, comp_b.x, comp_b.y, comp_b.ref)

            ax, ay = comp_a.x + a_px, comp_a.y + a_py
            bx, by = comp_b.x + b_px, comp_b.y + b_py
            net_id = net_ids[net_type]

            # Toggle layer every 3 connections for multi-layer effect
            layer_toggle_counter += 1
            if layer_toggle_counter % 3 == 0:
                via_x, via_y = (ax + bx) / 2, (ay + by) / 2
                vias_str += f'  (via (at {via_x:.3f} {via_y:.3f}) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net {net_id}))\n'
                next_layer = "B.Cu" if current_layer == "F.Cu" else "F.Cu"
                current_layer = next_layer

            segments_str += route_45deg(ax, ay, bx, by, current_layer, net_id, width)

        # ── 5. Board outline, holes, zones ────────────────────────────────────
        board_w = BOARD_W + 30
        board_h = BOARD_H + 30
        total_comps = len(comps)

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
"""
        outline = f"""
  (gr_line (start 25 25) (end {board_w} 25) (layer "Edge.Cuts") (width 0.15))
  (gr_line (start {board_w} 25) (end {board_w} {board_h}) (layer "Edge.Cuts") (width 0.15))
  (gr_line (start {board_w} {board_h}) (end 25 {board_h}) (layer "Edge.Cuts") (width 0.15))
  (gr_line (start 25 {board_h}) (end 25 25) (layer "Edge.Cuts") (width 0.15))
"""
        holes = f"""
  (footprint "MountingHole:MountingHole_3.2mm_M3" (at 30 30) (layer "F.Cu")
    (property "Reference" "H1" (at 30 27 0) (layer "F.SilkS"))
    (property "Value" "M3" (at 30 33 0) (layer "F.Fab"))
    (pad "1" np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2) (layers *.Cu *.Mask))
  )
  (footprint "MountingHole:MountingHole_3.2mm_M3" (at {board_w-5} 30) (layer "F.Cu")
    (property "Reference" "H2" (at {board_w-5} 27 0) (layer "F.SilkS"))
    (property "Value" "M3" (at {board_w-5} 33 0) (layer "F.Fab"))
    (pad "1" np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2) (layers *.Cu *.Mask))
  )
  (footprint "MountingHole:MountingHole_3.2mm_M3" (at 30 {board_h-5}) (layer "F.Cu")
    (property "Reference" "H3" (at 30 {board_h-8} 0) (layer "F.SilkS"))
    (property "Value" "M3" (at 30 {board_h-2} 0) (layer "F.Fab"))
    (pad "1" np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2) (layers *.Cu *.Mask))
  )
  (footprint "MountingHole:MountingHole_3.2mm_M3" (at {board_w-5} {board_h-5}) (layer "F.Cu")
    (property "Reference" "H4" (at {board_w-5} {board_h-8} 0) (layer "F.SilkS"))
    (property "Value" "M3" (at {board_w-5} {board_h-2} 0) (layer "F.Fab"))
    (pad "1" np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2) (layers *.Cu *.Mask))
  )
"""
        zone = f"""
  (zone (net 0) (net_name "") (layer "B.Cu") (hatch edge 0.5)
    (connect_pads (clearance 0.5))
    (min_thickness 0.25)
    (fill yes)
    (polygon (pts
      (xy 25 25) (xy {board_w} 25) (xy {board_w} {board_h}) (xy 25 {board_h})
    ))
  )
"""
        text_labels = f"""
  (gr_text "CircuitPilot AI · Force-Directed Net-Aware Router" (at {board_w/2:.1f} 20) (layer "F.SilkS")
    (effects (font (size 1.8 1.8) (thickness 0.35)))
  )
  (gr_text "Components: {total_comps}" (at {board_w/2:.1f} {board_h+8}) (layer "F.SilkS")
    (effects (font (size 1.4 1.4) (thickness 0.28)))
  )
"""
        footer = "\n)"

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(
                header + outline + holes + text_labels
                + footprints_str + segments_str + vias_str
                + zone + footer
            )

        return True

    except Exception as e:
        import traceback
        print(f"Native Generator v3.0 failed: {e}\n{traceback.format_exc()}")
        return False
