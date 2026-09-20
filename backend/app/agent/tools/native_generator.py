import os
import uuid
import re

KICAD_FOOTPRINTS_DIR = r"C:\Program Files\KiCad\10.99\share\kicad\footprints"

FOOTPRINT_MAP = {
    "ESP32": r"RF_Module.pretty\ESP32-WROOM-32.kicad_mod",
    "buck": r"Package_TO_SOT_SMD.pretty\SOT-23-5.kicad_mod",
    "555_timer": r"Package_SO.pretty\SOIC-8_3.9x4.9mm_P1.27mm.kicad_mod",
    "resistor": r"Resistor_SMD.pretty\R_0805_2012Metric.kicad_mod",
    "capacitor": r"Capacitor_SMD.pretty\C_0805_2012Metric.kicad_mod",
    "led": r"LED_SMD.pretty\LED_0805_2012Metric.kicad_mod",
    "transistor": r"Package_TO_SOT_SMD.pretty\SOT-23.kicad_mod",
    "LM386": r"Package_SO.pretty\SOIC-8_3.9x4.9mm_P1.27mm.kicad_mod",
    "hole": r"MountingHole.pretty\MountingHole_3.2mm_M3.kicad_mod",
    "dip": r"Package_DIP.pretty\DIP-40_W15.24mm.kicad_mod",
    "40-pin": r"Package_DIP.pretty\DIP-40_W15.24mm.kicad_mod",
    "18-pin": r"Package_DIP.pretty\DIP-18_W7.62mm.kicad_mod",
    "8-pin": r"Package_DIP.pretty\DIP-8_W7.62mm.kicad_mod",
    "regulator": r"Package_TO_SOT_THT.pretty\TO-220-3_Vertical.kicad_mod",
    "barrel": r"Connector_BarrelJack.pretty\BarrelJack_Horizontal.kicad_mod",
    "electrolytic": r"Capacitor_THT.pretty\CP_Radial_D8.0mm_P3.50mm.kicad_mod",
    "crystal": r"Crystal.pretty\Crystal_HC49-U_Vertical.kicad_mod",
    "header": r"Connector_PinHeader_2.54mm.pretty\PinHeader_1x06_P2.54mm_Vertical.kicad_mod",
    "eeprom": r"Package_DIP.pretty\DIP-8_W7.62mm.kicad_mod",
    "microcontroller": r"Package_DIP.pretty\DIP-40_W15.24mm.kicad_mod"
}

def get_footprint_data(comp_name: str, x: float, y: float, ref_des: str):
    comp_lower = comp_name.lower()
    fp_rel_path = FOOTPRINT_MAP["LM386"] # Default
    
    for key, path in FOOTPRINT_MAP.items():
        if key.lower() in comp_lower or comp_lower in key.lower():
            fp_rel_path = path
            break
            
    fp_path = os.path.join(KICAD_FOOTPRINTS_DIR, fp_rel_path)
    
    if not os.path.exists(fp_path):
        fp_path = os.path.join(KICAD_FOOTPRINTS_DIR, FOOTPRINT_MAP["LM386"])
        
    try:
        with open(fp_path, "r", encoding="utf-8") as f:
            fp_str = f.read()
    except Exception:
        return "", 0, 0
        
    # Inject (at X Y) and (uuid "...")
    uid = str(uuid.uuid4())
    fp_str = re.sub(r'\(footprint "([^"]+)"', rf'(footprint "\1"\n  (at {x} {y})\n  (uuid "{uid}")', fp_str, count=1)
    
    # Change Reference
    fp_str = re.sub(r'\(property "Reference" "REF\*\*?"', rf'(property "Reference" "{ref_des}"', fp_str)
    fp_str = re.sub(r'\(fp_text reference "REF\*\*?"', rf'(fp_text reference "{ref_des}"', fp_str)
    
    # Find Pad 1 offset to route it
    pad_match = re.search(r'\(pad "1".*?\(at ([\-\d\.]+) ([\-\d\.]+).*?\)', fp_str, re.DOTALL)
    pad_x, pad_y = 0.0, 0.0
    if pad_match:
        pad_x = float(pad_match.group(1))
        pad_y = float(pad_match.group(2))
        
    # Shift fp_str lines for neat indentation
    indented_fp = "\n".join("  " + line for line in fp_str.split("\n"))
    
    return indented_fp, pad_x, pad_y

def generate_kicad_pcb(target_path: str, components: list[str]) -> bool:
    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        header = """(kicad_pcb (version 20211014) (generator pcbnew)
  (general (thickness 1.6))
  (paper "A4")
  (layers
    (0 "F.Cu" signal) (31 "B.Cu" signal)
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
"""
        
        start_x, start_y = 50, 50
        current_x, current_y = start_x, start_y
        row_height = 45 # mm spacing between rows
        col_width = 45 # mm spacing between columns
        max_board_width = 250
        
        max_x_used = 100
        max_y_used = 100
        
        footprints_str = ""
        segments_str = ""
        prev_pad_abs_x = None
        prev_pad_abs_y = None
        
        for idx, comp in enumerate(components):
            fp_x = current_x
            fp_y = current_y
            
            fp_str, p1_x, p1_y = get_footprint_data(comp, fp_x, fp_y, f"U{idx+1}")
            footprints_str += fp_str + "\n"
            
            # Draw physical trace
            abs_x = fp_x + p1_x
            abs_y = fp_y + p1_y
            
            if prev_pad_abs_x is not None:
                # Manhattan Orthogonal Routing
                mid_y = prev_pad_abs_y + 22.5 # Route through the channel between rows
                segments_str += f"""
  (segment (start {prev_pad_abs_x} {prev_pad_abs_y}) (end {prev_pad_abs_x} {mid_y}) (width 0.25) (layer "F.Cu") (net 1))
  (segment (start {prev_pad_abs_x} {mid_y}) (end {abs_x} {mid_y}) (width 0.25) (layer "F.Cu") (net 1))
  (segment (start {abs_x} {mid_y}) (end {abs_x} {abs_y}) (width 0.25) (layer "F.Cu") (net 1))
"""
            prev_pad_abs_x = abs_x
            prev_pad_abs_y = abs_y
            
            if current_x > max_x_used: max_x_used = current_x
            if current_y > max_y_used: max_y_used = current_y
            
            # 2D Grid Wrap
            current_x += col_width
            if current_x > max_board_width:
                current_x = start_x
                current_y += row_height

        # Dynamic Outline
        board_w = max(150, max_x_used + 45)
        board_h = max(100, max_y_used + 45)
        
        outline = f"""
  (gr_line (start 30 30) (end {board_w} 30) (layer "Edge.Cuts") (width 0.15))
  (gr_line (start {board_w} 30) (end {board_w} {board_h}) (layer "Edge.Cuts") (width 0.15))
  (gr_line (start {board_w} {board_h}) (end 30 {board_h}) (layer "Edge.Cuts") (width 0.15))
  (gr_line (start 30 {board_h}) (end 30 30) (layer "Edge.Cuts") (width 0.15))
"""
        text_labels = f"""
  (gr_text "NATIVE AI GENERATOR 2D GRID" (at {board_w/2} 25) (layer "F.SilkS")
    (effects (font (size 2 2) (thickness 0.4)))
  )
  (gr_text "REAL COMPONENTS: {', '.join(components)}" (at {board_w/2} {board_h + 10}) (layer "F.SilkS")
    (effects (font (size 1.5 1.5) (thickness 0.3)))
  )
"""
        footer = "\n)"
        
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(header + outline + text_labels + footprints_str + segments_str + footer)
            
        return True
    except Exception as e:
        print(f"Native Generator failed: {e}")
        return False
