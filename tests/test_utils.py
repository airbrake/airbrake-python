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
