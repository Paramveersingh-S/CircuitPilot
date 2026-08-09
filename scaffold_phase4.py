with open("backend/app/agent/tools/export_tools.py", "w") as f:
    f.write("""def kicad_export_fab(session_id: str, formats: list):
    pass

def dfm_check(session_id: str):
    pass
""")
