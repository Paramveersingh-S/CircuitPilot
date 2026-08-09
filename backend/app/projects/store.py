import os

class ProjectStore:
    """
    Git-backed workspace CRUD operations.
    """
    def __init__(self, base_dir: str = "/projects"):
        self.base_dir = base_dir

    def get_project_path(self, project_id: str) -> str:
        return os.path.join(self.base_dir, project_id)

    def commit_change(self, project_id: str, message: str):
        """
        Commits changes to the git repository for the specified project.
        """
        # Stub implementation
        pass

    def revert_change(self, project_id: str):
        """
        Reverts the last commit for the specified project.
        """
        # Stub implementation
        pass

project_store = ProjectStore()
