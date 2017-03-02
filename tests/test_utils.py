import unittest

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
        version = airbrake.utils.get_local_git_revision()
        self.assertEqual(40, len(version))

        rev_file = airbrake.utils._git_revision_from_file()
        self.assertEqual(40, len(rev_file))

        rev_binary = airbrake.utils._git_revision_with_binary()
        self.assertEqual(40, len(rev_binary))
        self.assertEqual(rev_binary, rev_file)
