import os
import subprocess
import shutil

class ProjectStore:
    """
    Git-backed workspace CRUD operations.
    All paths are driven by the WORKSPACES_DIR environment variable.
    """
    def __init__(self, base_dir: str | None = None):
        if base_dir is None:
            # Default: resolve from env, fall back to project-relative path
            default = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "..", "..", "workspaces"
            )
            base_dir = os.environ.get("WORKSPACES_DIR", default)
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def get_project_path(self, project_id: str) -> str:
        return os.path.join(self.base_dir, project_id)

    def init_project(self, project_id: str):
        path = self.get_project_path(project_id)
        if not os.path.exists(path):
            os.makedirs(path)
            subprocess.run(["git", "init"], cwd=path, check=True)
            # Create a basic ato project structure if not exists
            try:
                subprocess.run(["ato", "create"], cwd=path, check=True)
                self.commit_change(project_id, "Initial atopile project creation")
            except Exception as e:
                print(f"atopile CLI missing or failed: {e}. Mocking project structure.")
                src_path = os.path.join(path, "elec", "src")
                os.makedirs(src_path, exist_ok=True)
                with open(os.path.join(src_path, f"{project_id}.ato"), "w") as f:
                    f.write(f"module {project_id}:\n")
                self.commit_change(project_id, "Mocked atopile project structure")

    def commit_change(self, project_id: str, message: str):
        """
        Commits changes to the git repository for the specified project.
        """
        path = self.get_project_path(project_id)
        if os.path.exists(path):
            try:
                subprocess.run(["git", "add", "."], cwd=path, check=True)
                subprocess.run(["git", "commit", "-m", message], cwd=path, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Git commit failed: {e}")

    def revert_change(self, project_id: str):
        """
        Reverts the last commit for the specified project.
        """
        path = self.get_project_path(project_id)
        if os.path.exists(path):
            try:
                subprocess.run(["git", "reset", "--hard", "HEAD~1"], cwd=path, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Git revert failed: {e}")

project_store = ProjectStore()
