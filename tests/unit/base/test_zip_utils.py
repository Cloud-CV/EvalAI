import os
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from base.zip_utils import (
    PathTraversalError,
    _is_path_under_root,
    safe_extract_zip_file,
    safe_join_under_root,
)


class SafeJoinUnderRootTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def test_allows_paths_under_root(self):
        resolved = safe_join_under_root(self.root, "configs", "challenge.yaml")
        expected = os.path.realpath(
            os.path.join(self.root, "configs", "challenge.yaml")
        )
        self.assertEqual(resolved, expected)

    def test_rejects_parent_directory_traversal(self):
        with self.assertRaises(PathTraversalError):
            safe_join_under_root(self.root, "..", "etc", "passwd")

    @patch("base.zip_utils.os.path.commonpath", side_effect=ValueError)
    def test_is_path_under_root_handles_commonpath_value_error(
        self, mock_commonpath
    ):
        self.assertFalse(_is_path_under_root("/tmp/root", "/other/path"))
        mock_commonpath.assert_called_once()


class SafeExtractZipFileTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def test_extracts_valid_members(self):
        zip_path = os.path.join(self.root, "valid.zip")
        extract_dir = os.path.join(self.root, "extracted")
        os.makedirs(extract_dir)

        with zipfile.ZipFile(zip_path, "w") as archive:
            archive.writestr("challenge.txt", "ok")

        with zipfile.ZipFile(zip_path, "r") as archive:
            safe_extract_zip_file(archive, extract_dir)

        self.assertTrue(
            os.path.isfile(os.path.join(extract_dir, "challenge.txt"))
        )

    def test_rejects_unsafe_members(self):
        zip_path = os.path.join(self.root, "unsafe.zip")
        extract_dir = os.path.join(self.root, "unsafe-extracted")
        os.makedirs(extract_dir)

        with zipfile.ZipFile(zip_path, "w") as archive:
            archive.writestr("../evil.txt", "bad")

        with zipfile.ZipFile(zip_path, "r") as archive:
            with self.assertRaises(zipfile.BadZipFile):
                safe_extract_zip_file(archive, extract_dir)
