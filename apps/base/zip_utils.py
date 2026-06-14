import os
import zipfile


class PathTraversalError(ValueError):
    """Raised when a resolved path escapes its intended root directory."""


def safe_join_under_root(root, *relative_paths):
    """
    Join path segments under root and verify the result stays within root.
    """
    root_path = os.path.abspath(root)
    candidate = os.path.abspath(os.path.join(root_path, *relative_paths))
    if not (
        candidate == root_path or candidate.startswith(root_path + os.sep)
    ):
        raise PathTraversalError("Path escapes extraction root.")
    return candidate


def safe_extract_zip_file(zip_ref, destination):
    """
    Extract zip archive members while preventing path traversal (zip slip).
    """
    destination_path = os.path.abspath(destination)
    for member in zip_ref.namelist():
        member_path = os.path.abspath(os.path.join(destination_path, member))
        if not (
            member_path == destination_path
            or member_path.startswith(destination_path + os.sep)
        ):
            raise zipfile.BadZipFile("Zip archive contains unsafe file paths.")
    zip_ref.extractall(destination_path)
