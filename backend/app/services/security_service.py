
import os


def get_safe_file_path(repo_path: str, requested_path: str):

    # Get the absolute repository directory
    base_path = os.path.realpath(repo_path)

    # Resolve the requested file path
    target_path = os.path.realpath(
        os.path.join(base_path, requested_path)
    )

    # Check whether the requested path stays inside the repository
    if os.path.commonpath([base_path, target_path]) != base_path:
        raise ValueError("Access denied: File is outside the repository")

    return target_path
