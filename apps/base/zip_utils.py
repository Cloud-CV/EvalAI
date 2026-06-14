import os
import zipfile


class PathTraversalError(ValueError):
    """Raised when a resolved path escapes its intended root directory."""


def _is_path_under_root(root_path, candidate):
    try:
        return os.path.commonpath([root_path, candidate]) == root_path
    except ValueError:
        return False


def safe_join_under_root(root, *relative_paths):
    """
    Join path segments under root and verify the result stays within root.
    """
    root_path = os.path.realpath(root)
    candidate = os.path.realpath(os.path.join(root_path, *relative_paths))
    if not _is_path_under_root(root_path, candidate):
        raise PathTraversalError("Path escapes extraction root.")
    return candidate


def safe_extract_zip_file(zip_ref, destination):
    """
    Extract zip archive members while preventing path traversal (zip slip).
    """
    destination_path = os.path.realpath(destination)
    for member in zip_ref.namelist():
        try:
            safe_join_under_root(destination_path, member)
        except PathTraversalError:
            raise zipfile.BadZipFile("Zip archive contains unsafe file paths.")
    zip_ref.extractall(destination_path)
