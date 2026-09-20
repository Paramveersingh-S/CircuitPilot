import subprocess
import json
from typing import List, Optional
from pydantic import BaseModel
import os

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
    .ato module matching the query."""
    try:
        # Assuming atopile CLI has a search command returning JSON, or we mock it for now
        # result = subprocess.run(["ato", "search", query, "--json"], capture_output=True, text=True)
        # return [PackageMatch(**m) for m in json.loads(result.stdout)]
        
        # Simplified Mock as atopile search might not be perfectly JSON yet
        return [PackageMatch(name="mocked_package", description="Found match for " + query, version="1.0.0")]
    except Exception as e:
        print(f"ato_search_package error: {e}")
        return []

def ato_add_module(target_file: str, module_name: str,
                    package_ref: Optional[str], inline_spec: Optional[str]) -> str:
    """Add a module instance to an .ato file. Does not trigger a build."""
    try:
        content = f"\nmodule {module_name}:\n"
        if package_ref:
            content += f"    # from {package_ref}\n"
        if inline_spec:
            content += f"    {inline_spec}\n"
            
        with open(target_file, "a") as f:
            f.write(content)
        return f"{module_name}"
    except Exception as e:
        print(f"ato_add_module error: {e}")
        return ""

def ato_set_parameter(target_file: str, module_id: str, param: str, value: float,
                       unit: str, tolerance: Optional[float]) -> None:
    """Set/override a parametric value on a module instance."""
    try:
        with open(target_file, "a") as f:
            f.write(f"\n    {module_id}.{param} = {value}{unit}")
            if tolerance:
                f.write(f" +/- {tolerance}%")
    except Exception as e:
        print(f"ato_set_parameter error: {e}")

def ato_connect(target_file: str, a: str, b: str) -> None:
    """Connect two pins, interfaces, or nets by name."""
    try:
        with open(target_file, "a") as f:
            f.write(f"\n    {a} ~ {b}")
    except Exception as e:
        print(f"ato_connect error: {e}")

def ato_build(target_file: str) -> BuildResult:
    """Compile .ato sources."""
    try:
        result = subprocess.run(["ato", "build", target_file], capture_output=True, text=True)
        success = result.returncode == 0
        errors = [line for line in result.stderr.split('\n') if "error" in line.lower()]
        warnings = [line for line in result.stderr.split('\n') if "warning" in line.lower()]
        return BuildResult(success=success, errors=errors, warnings=warnings)
    except Exception as e:
        print(f"ato_build error: {e}")
        return BuildResult(success=False, errors=[str(e)], warnings=[])
