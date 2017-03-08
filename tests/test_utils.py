import os
import unittest
import subprocess

import airbrake.utils


class TestUtils(unittest.TestCase):
    def test_non_empty_keys(self):
        data = {
            'remove_me': None,
            'remove_me_too': 'None',
            'remove_me_nested': {'remove_me': None,
                                 'remove_me_too': 'None'},
            'valid': 'testing',
            'valid_nested': {'valid_nested': 'testing'},
            'valid_nested_mix': {'remove_me': None,
                                 'remove_me_too': 'None',
                                 'valid_nested': 'testing'}
        }
        expected_data = {
            'valid': 'testing',
            'valid_nested': {'valid_nested': 'testing'},
            'valid_nested_mix': {'valid_nested': 'testing'}
        }

        clean_data = airbrake.utils.non_empty_keys(data)

        self.assertEqual(expected_data, clean_data)

    def test_get_local_git_revision(self):
        rev = airbrake.utils.get_local_git_revision()
        self.assertIsNotNone(rev)

        has_fs_access = None
        head_ref_path_file = os.path.join(airbrake.utils._get_git_path(),
                                          "HEAD")
        with open(head_ref_path_file, 'r') as test_file:
            ref_path = test_file.read().strip()
            if ref_path:
                has_fs_access = True

        if has_fs_access:
            rev_file = airbrake.utils._git_revision_from_file()
            self.assertIsNotNone(rev_file)

        rev = subprocess.check_output(["git", "rev-parse", "HEAD"])
        if rev:
            rev_binary = airbrake.utils._git_revision_with_binary()
            self.assertIsNotNone(rev_binary)

        if has_fs_access and rev:
            self.assertTrue(rev_file, rev_binary)
