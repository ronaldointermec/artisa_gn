#
# Copyright (c) 2010 Vocollect, Inc.
# Pittsburgh, PA 15235
# All rights reserved.
#
# This source code contains confidential information that is owned by
# Vocollect, Inc. and may not be copied, disclosed or otherwise used without
# the express written consent of Vocollect, Inc.
#

''' this module tests the mock catalyst functions that are not
commonly used throughout other testing
'''

import mock_catalyst
import unittest

import voice

from vocollect_core_test.base_test_case import BaseTestCaseCore #@UnusedImport - here for test framework
from vocollect_core.dialog.ready_prompt import ReadyPrompt
from vocollect_core.utilities.util_methods import catalyst_version, CatalystVersion
import vocollect_core.utilities.util_methods #@UnusedImport - used to manipulate _parsed_version

SW_KEY = 'SwVersion.ApplicationVersion'

class TestDialogs(ReadyPrompt):

    ''' test dialog for getting/setting values'''
    def prompt_here(self):
        pass
        
class TestMockFunctions(BaseTestCaseCore):

    def test_audio(self):
        voice.audio.play('test/path')
        voice.audio.stop_playing()
        voice.audio.start_recording('test/record/path', 10)
        voice.audio.stop_recording()

        self.validate_prompts('Play Called on: test/path',
                              'Stop playing called', 
                              'Play Called on: test/record/path Max Seconds: 10',
                              'Stop recording called')
    
    def test_dialog(self):
        self.post_dialog_responses('ready')
        d = TestDialogs('test prompt')
        result = d.run()
        
        self.validate_prompts('test prompt')
        self.assertEqual(result, 'ready')
        self.assertEqual(voice.last_prompt_spoken, 'test prompt')
        self.assertEqual(voice.last_prompt_is_priority, False)

        self.post_dialog_responses('ready')
        d = TestDialogs('test prompt priority', True)
        result = d.run()

        self.validate_prompts('test prompt priority')
        self.assertEqual(voice.last_prompt_spoken, 'test prompt priority')
        self.assertEqual(voice.last_prompt_is_priority, True)

    def test_catalyst_version(self):
        mock_catalyst_sw_original = None
        if SW_KEY in mock_catalyst.environment_properties:
            mock_catalyst_sw_original = mock_catalyst.environment_properties[SW_KEY]

        # test known versions of VoiceCatalyst
        self._check_catalyst_version('VIAV_VCY-20101107235830_V1.0', [1, 0, 0])
        self._check_catalyst_version('VIAV_VCY-20141029104321_V2.1.1', [2, 1, 1])
        self._check_catalyst_version('VIAV_VCY-20150809153705_V2.2', [2, 2, 0])
        self._check_catalyst_version('VIAV_VCY-20170801095909_V2.3.1 ', [2, 3, 1])
        self._check_catalyst_version('VCPV000_V1.0', [1, 0, 0])
        self._check_catalyst_version('VIAV_VMI-20150224085523_V2.1', [2, 1, 0])
        self._check_catalyst_version('VIAV_VMI-20161123142150_V2.3', [2, 3, 0])
        self._check_catalyst_version('VIAV_VMI-20171219204432_V2.3.2', [2, 3, 2])
        # VoiceCatalyst versions should generally follow x.y.z as integers,
        # check possible non-integer components - which should compare less
        self._check_catalyst_version('VIAV_VCY-20141110103537_V2.1.OA', [2, 1, 0])
        self._check_catalyst_version('VIAV_VCY-20990101000000_V99.A.B', [99, 0, 0])
        self._check_catalyst_version('VIAV_VCY-20990101000000_Vunknown', [0, 0, 0])
        self._check_catalyst_version('VIAV_VCY-20990101000000_V1.2.3.4', [1, 2, 3, 4])
        self._check_catalyst_version('VIAV_VCY-20990101000000_V3.1.4.1.5', [3, 1, 4, 1, 5])
        self._check_catalyst_version('VVC-20120521052001-S4_V3.8.2', [3, 8, 2])
        self._check_catalyst_version('VVC-20120521052001_V3.8.2-S4', [3, 8, 0])

        # reset mock_catalyst environment property
        if mock_catalyst_sw_original is not None:
            mock_catalyst.environment_properties[SW_KEY] = mock_catalyst_sw_original
        else:
            del mock_catalyst.environment_properties[SW_KEY]
        vocollect_core.utilities.util_methods._parsed_version = None

    def test_catalyst_version_list(self):
        # test comparison operators for CatalystVersions, ints, and floats
        a = CatalystVersion([2, 0, 0])
        b = CatalystVersion([2, 0, 0])
        c = CatalystVersion([2, 0, 0, 0])
        d = CatalystVersion([2, 1, 0])

        self.assertEqual(a, b, 'Not detected as equal: %s, %s' % (a, b))
        self.assertEqual(hash(a), hash(b), 'Hash not detected as equal: %s, %s' % (a, b))
        self.assertNotEqual(id(a), id(b), 'Identity detected as equal: %d, %d (%s, %s)' %\
                                           (id(a), id(b), a, b))

        # deprecation warning if running MockCatalyst
        bypass_original = CatalystVersion._bypass_version_cast_deprecation
        self.assertRaises(DeprecationWarning, self.assertLess, a, 2.1)
        self.assertRaises(DeprecationWarning, self.assertLessEqual, b, 2)
        self.assertRaises(DeprecationWarning, self.assertGreater, c, 1.5)
        self.assertRaises(DeprecationWarning, self.assertGreaterEqual, d, 2.1)
        # equal and not equal assume any exceptions in comparison are unequal
        msg = '%s not != %s'
        self.assertNotEqual(a, 2, msg % (a, 2))
        self.assertNotEqual(a, 2.0, msg % (a, 2.0))
        CatalystVersion._bypass_version_cast_deprecation = True
        msg = "%s == %s"
        self.assertTrue(a == 2, msg % (a, 2))
        self.assertTrue(2 == a, msg % (2, a))
        self.assertTrue(a == 2.0, msg % (a, 2.0))
        self.assertTrue(2.0 == a, msg % (2.0, a))
        self.assertTrue(d == 2.1, msg % (d, 2.1))
        self.assertTrue(2.1 == d, msg % (2.1, d))
        self.assertTrue(a == b, msg % (a, b))
        self.assertTrue(b == a, msg % (b, a))
        msg = "%s != %s"
        self.assertTrue(a != c, msg % (a, c))
        self.assertTrue(c != a, msg % (c, a))
        self.assertTrue(b != d, msg % (b, d))
        self.assertTrue(d != b, msg % (d, b))
        self.assertTrue(a != 1, msg % (a, 1))
        self.assertTrue(a != 2.1, msg % (a, 2.1))
        self.assertTrue(d != 2, msg % (d, 2))
        self.assertTrue(d != 2.2, msg % (d, 2.2))
        msg = "%s < %s"
        self.assertFalse(a < b, msg % (a, b))
        self.assertFalse(b < a, msg % (b, a))
        self.assertFalse(a < 2, msg % (a, 2))
        self.assertFalse(a < 2.0, msg % (a, 2.0))
        self.assertTrue(a < 2.1, msg % (a, 2.1))
        self.assertFalse(2 < a, msg % (2, a))
        self.assertFalse(2.0 < a, msg % (2.0, a))
        self.assertFalse(2.1 < a, msg % (2.1, a))
        self.assertTrue(a < c, msg % (a, c))
        self.assertFalse(c < a, msg % (c, a))
        self.assertTrue(b < c, msg % (b, c))
        self.assertFalse(c < b, msg % (c, b))
        self.assertTrue(c < d, msg % (c, d))
        self.assertFalse(d < c, msg % (d, c))
        self.assertTrue(a < d, msg % (a, d))
        self.assertFalse(d < a, msg % (d, a))
        self.assertTrue(b < d, msg % (b, d))
        self.assertFalse(d < b, msg % (d, b))
        msg = "%s >= %s"
        self.assertTrue(a >= b, msg % (a, b))
        self.assertTrue(b >= a, msg % (b, a))
        self.assertTrue(a >= 2, msg % (a, 2))
        self.assertTrue(a >= 2.0, msg % (a, 2.0))
        self.assertFalse(a >= 2.1, msg % (a, 2.1))
        self.assertFalse(a >= c, msg % (a, c))
        self.assertTrue(c >= a, msg % (c, a))
        self.assertFalse(b >= c, msg % (b, c))
        self.assertTrue(c >= b, msg % (c, b))
        self.assertFalse(c >= d, msg % (c, d))
        self.assertTrue(d >= c, msg % (d, c))
        self.assertFalse(a >= d, msg % (a, d))
        self.assertTrue(d >= a, msg % (d, a))
        self.assertFalse(b >= d, msg % (b, d))
        self.assertTrue(d >= b, msg % (d, b))
        msg = "%s > %s"
        self.assertFalse(a > b, msg % (a, b))
        self.assertFalse(b > a, msg % (b, a))
        self.assertFalse(a > 2, msg % (a, 2))
        self.assertFalse(a > 2.0, msg % (a, 2.0))
        self.assertFalse(a > 2.1, msg % (a, 2.1))
        self.assertFalse(a > c, msg % (a, c))
        self.assertTrue(c > a, msg % (c, a))
        self.assertFalse(b > c, msg % (b, c))
        self.assertTrue(c > b, msg % (c, b))
        self.assertFalse(c > d, msg % (c, d))
        self.assertTrue(d > c, msg % (d, c))
        self.assertFalse(a > d, msg % (a, d))
        self.assertTrue(d > a, msg % (d, a))
        self.assertFalse(b > d, msg % (b, d))
        self.assertTrue(d > b, msg % (d, b))
        msg = "%s <= %s"
        self.assertTrue(a <= b, msg % (a, b))
        self.assertTrue(b <= a, msg % (b, a))
        self.assertTrue(a <= 2, msg % (a, 2))
        self.assertTrue(a <= 2.0, msg % (a, 2.0))
        self.assertTrue(a <= 2.1, msg % (a, 2.1))
        self.assertTrue(a <= c, msg % (a, c))
        self.assertFalse(c <= a, msg % (c, a))
        self.assertTrue(b <= c, msg % (b, c))
        self.assertFalse(c <= b, msg % (c, b))
        self.assertTrue(c <= d, msg % (c, d))
        self.assertFalse(d <= c, msg % (d, c))
        self.assertTrue(a <= d, msg % (a, d))
        self.assertFalse(d <= a, msg % (d, a))
        self.assertTrue(b <= d, msg % (b, d))
        self.assertFalse(d <= b, msg % (d, b))
        CatalystVersion._bypass_version_cast_deprecation = bypass_original

    def _check_catalyst_version(self, sw_string, expected_version_list):
        # the device's VoiceCatalyst version cannot change without needing to reload the task
        # and therefore needing to recalculate the parsed VoiceCatalyst version;
        # manually resetting this for the test case
        vocollect_core.utilities.util_methods._parsed_version = None
        mock_catalyst.environment_properties[SW_KEY] = sw_string
        expected_catalyst_version = CatalystVersion(expected_version_list)
        error_msg = "Calculated %s, expected %s, for %s" %\
            (catalyst_version(), expected_catalyst_version, sw_string)
        self.assertEqual(catalyst_version(), expected_catalyst_version, error_msg)

if __name__ == "__main__":
    unittest.main()