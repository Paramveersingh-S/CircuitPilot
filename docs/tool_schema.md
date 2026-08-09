# Tool Schema

CircuitPilot agents interact with the EDA engine using the following tools:

- `ato_search_package(query: str) -> list[PackageMatch]`
- `ato_add_module(target_file: str, module_name: str, package_ref: str | None, inline_spec: str | None) -> str`
- `ato_set_parameter(module_id: str, param: str, value: float, unit: str, tolerance: float | None) -> None`
- `ato_connect(a: str, b: str) -> None`
- `ato_build(target_file: str) -> BuildResult`
- `kicad_get_board_state(session_id: str) -> BoardSnapshot`
- `kicad_place_footprint(session_id: str, ref: str, x_mm: float, y_mm: float, rotation_deg: float, layer: str) -> None`
- `kicad_auto_place(session_id: str, strategy: str = "hierarchical_cluster") -> None`
- `kicad_route_net_interactive(session_id: str, net: str, mode: str, waypoints: list[tuple[float, float]] | None) -> RouteResult`
- `kicad_run_drc(session_id: str) -> DRCResult`
- `kicad_run_erc(session_id: str) -> ERCResult`
- `kicad_autoroute(session_id: str, engine: str = "freerouting", nets: list[str] | None = None) -> RouteResult`
- `kicad_export_fab(session_id: str, formats: list[str]) -> list[str]`
- `dfm_check(session_id: str) -> DFMReport`
