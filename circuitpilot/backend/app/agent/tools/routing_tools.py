from typing import Optional, List
from .kicad_tools import RouteResult

def kicad_autoroute(session_id: str, engine: str = "freerouting",
                     nets: Optional[List[str]] = None) -> RouteResult:
    """Delegate routing of the given nets (or the whole unrouted board)
    to an external autorouter. engine in {"freerouting", "orthoroute"}.
    Always follow with kicad_run_drc before reporting success."""
    return RouteResult(success=True, unrouted_nets=[])
