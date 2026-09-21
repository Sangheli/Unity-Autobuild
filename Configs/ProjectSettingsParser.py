"""
Utility module to parse Unity version from a project's ProjectSettings/ProjectVersion.txt file.
"""

import os


def get_unity_version_from_project(repo_path):
    """
    Read ProjectSettings/ProjectVersion.txt from the Unity project
    and extract the m_EditorVersion value.

    Args:
        repo_path: Path to the Unity project root directory.

    Returns:
        The version string (e.g., '2022.3.15f1') or None if not found.
    """
    project_version_file = os.path.join(repo_path, "ProjectSettings", "ProjectVersion.txt")

    if not os.path.isfile(project_version_file):
        return None

    try:
        with open(project_version_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("m_EditorVersion:"):
                    version = line.split(":", 1)[1].strip()
                    return version
    except (IOError, OSError):
        return None

    return None
