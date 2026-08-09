from typing import List, Optional
from pydantic import BaseModel

class PackageMatch(BaseModel):
    name: str
    description: str
    version: str

class BuildResult(BaseModel):
    success: bool
    errors: List[str]
    warnings: List[str]

def ato_search_package(query: str) -> List[PackageMatch]:
    """Search the local package cache and packages.atopile.io for a reusable
    .ato module matching the query (e.g. 'buck converter 5V to 3.3V',
    'USB-C connector'). Prefer this over ato_add_module with a from-scratch
    spec whenever a vetted match exists."""
    # Stub implementation
    return []

def ato_add_module(target_file: str, module_name: str,
                    package_ref: Optional[str], inline_spec: Optional[str]) -> str:
    """Add a module instance to an .ato file, either by referencing an
    existing package (preferred) or an inline block of new .ato source
    (only when no package match exists). Does not trigger a build."""
    # Stub implementation
    return f"{module_name}_id"

def ato_set_parameter(module_id: str, param: str, value: float,
                       unit: str, tolerance: Optional[float]) -> None:
    """Set/override a parametric value (e.g. resistance, voltage) on a
    module instance, with units and tolerance the atopile compiler will
    enforce as a constraint."""
    pass

def ato_connect(a: str, b: str) -> None:
    """Connect two pins, interfaces, or nets by name."""
    pass

def ato_build(target_file: str) -> BuildResult:
    """Compile .ato sources: solves constraints, resolves parametric part
    picks, runs built-in assertions, and updates the linked KiCad project
    in elec/layout/. Returns errors/warnings; does NOT auto-fix them."""
    # Stub implementation
    return BuildResult(success=True, errors=[], warnings=[])
