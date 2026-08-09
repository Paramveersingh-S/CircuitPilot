from .kicad_tools import kicad_run_drc, kicad_run_erc
from .ato_tools import ato_build

class VerificationAgent:
    def __init__(self):
        pass

    async def run_checks(self, session):
        """
        Run verification checks at the end of a sequence of operations.
        - ERC/DRC
        - atopile assertions
        """
        drc_res = kicad_run_drc(session.project_id)
        erc_res = kicad_run_erc(session.project_id)
        build_res = ato_build(f"elec/src/{session.project_id}.ato")
        
        return {
            "drc_clean": drc_res.clean,
            "erc_clean": erc_res.clean,
            "build_success": build_res.success
        }

verification_agent = VerificationAgent()
