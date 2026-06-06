import os
import zipfile


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
