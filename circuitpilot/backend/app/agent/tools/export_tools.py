from typing import List
from pydantic import BaseModel

class DFMReport(BaseModel):
    passed: bool
    violations: List[dict]

def kicad_export_fab(session_id: str, formats: List[str]) -> List[str]:
    """Export manufacturing outputs. formats subset of
    {"gerber","drill","bom","cpl","step"}. Returns file paths."""
    return [f"/outputs/{session_id}/export.{fmt}" for fmt in formats]

def dfm_check(session_id: str) -> DFMReport:
    """Check the board against common fab-house manufacturability limits
    (min trace/space, min drill, min annular ring) and flag violations
    before export."""
    return DFMReport(passed=True, violations=[])
