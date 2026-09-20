import os
import subprocess
import re

def run_ato_build(ato_file_path: str, project_dir: str):
    """
    Runs `ato build` inside the atopile-runner Docker container.
    """
    try:
        # We need absolute path for docker volume mount
        abs_project_dir = os.path.abspath(project_dir)
        
        # Make path relative to project dir for Docker
        rel_path = os.path.relpath(ato_file_path, abs_project_dir)
        # Convert Windows backslashes to forward slashes for Linux Docker
        rel_path = rel_path.replace("\\", "/")
        
        # Read the file to find the primary module name
        with open(ato_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        match = re.search(r'module\s+([A-Za-z0-9_]+):', content)
        if not match:
            return False, "Error: Could not find a 'module <Name>:' declaration in the generated Atopile code."
            
        module_name = match.group(1)
        
        # Write the required ato.yaml project configuration file dynamically
        yaml_path = os.path.join(abs_project_dir, "ato.yaml")
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(f"ato-version: ^0.2.0\nbuilds:\n  default:\n    entry: {rel_path}:{module_name}\n")
        
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{abs_project_dir}:/workspace",
            "atopile-runner",
            "--non-interactive", "build"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        combined_logs = result.stdout.strip() + "\n" + result.stderr.strip()
        
        if result.returncode != 0:
            print(f"Atopile Build Error:\n{combined_logs}")
            return False, combined_logs
            
        return True, combined_logs
    except Exception as e:
        return False, str(e)
