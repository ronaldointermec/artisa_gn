import mock_catalyst #@UnusedImport
import unittest
from vocollect_core_test.base_test_case import BaseTestCaseCore
from vocollect_core.dialog.functions import prompt_digits,\
    prompt_digits_required
from vocollect_core import scanning
from vocollect_core.scanning import ScanMode

#call back method for scanning test
def parse_scan(scanned_value):
    return_value = scanned_value
    return_value = return_value.replace('1', 'A')
    return_value = return_value.replace('2', 'B')
    return_value = return_value.replace('3', 'C')
    return_value = return_value.replace('4', 'D')
    return_value = return_value.replace('5', 'E')
    return return_value
 
class TestScanning(BaseTestCaseCore):
    
    def setUp(self):
        #Make sure parsing call back is not set
        scanning.set_scan_post_process_callback(None)
        # VSCVALIB-66 - MockCatalyst does not yet implement SwVersion.ApplicationVersion
        # ScanMode.Multiple only supported in VoiceCatalyst 2.0 and later
        self._mock_catalyst_orig = None
        if 'SwVersion.ApplicationVersion' in mock_catalyst.environment_properties:
            self._mock_catalyst_orig = mock_catalyst.environment_properties['SwVersion.ApplicationVersion']
        mock_catalyst.environment_properties['SwVersion.ApplicationVersion'] = 'VCY_V2.2'
        self.clear()

    def tearDown(self):
        super().tearDown()
        if self._mock_catalyst_orig is None:
            del mock_catalyst.environment_properties['SwVersion.ApplicationVersion']
        else:
            mock_catalyst.environment_properties['SwVersion.ApplicationVersion'] = self._mock_catalyst_orig

    def test_scanning(self):
        #test a basic scan
        self.post_dialog_responses('#123456')
        
        value, scanned = prompt_digits("test scanning", 
                                       "help message", 
                                       1, None, 
                                       False, True)
        
        
        self.assertEqual('123456', value)
        self.assertTrue(scanned, "scanned flag set")
        self.validate_prompts("test scanning")
        
        #test not scanned
        self.post_dialog_responses('123','456','ready')
        
        value, scanned = prompt_digits("test scanning", 
                                       "help message", 
                                       1, None, 
                                       False, True)
        
        
        self.assertEqual('123456', value)
        self.assertFalse(scanned, "scanned flag set")
        self.validate_prompts("test scanning")
        
        #Test scanned after entering digits
        self.post_dialog_responses('123','#456')
        
        value, scanned = prompt_digits("test scanning", 
                                       "help message", 
                                       1, None, 
                                       False, True)
        
        
        self.assertEqual('456', value) #should be only the scanned value, not spoken value
        self.assertTrue(scanned, "scanned flag set")
        
        
        self.validate_prompts("test scanning")
        
    def test_scanning_off(self):
        
        #test scan ignored if scanning off
        self.post_dialog_responses('#123456', #value should be ignored 
                                   '999ready')
        
        value = prompt_digits("test scanning", 
                              "help message", 
                              1, None, 
                              False, False) #Test using False
        
        
        self.assertEqual('999', value) #spoken value not scanned value
        self.validate_prompts("test scanning")

        #Test queued up scanned responses do not get accepted if scanning off        
        scanning.scan_results = ['12345', '67890']
        self.post_dialog_responses('999ready')
        value = prompt_digits("test scanning", 
                              "help message", 
                              1, None, 
                              False, ScanMode.Off) #Test using Off
        
        self.assertEqual('999', value) #spoken value not scanned value
        self.validate_prompts("test scanning")
        self.assertEqual(len(scanning.scan_results), 0) #validate queue was erased


    def test_scanning_single(self):
        
        #Test queued up scanned responses do not get accepted if scanning single
        #queue should be cleared
        scanning.scan_results = ['12345', '67890']
        self.post_dialog_responses('999ready')
        value = prompt_digits("test scanning", 
                              "help message", 
                              1, None, 
                              False, ScanMode.Single) #Test using Off
        
        self.assertEqual(('999', False), value) #Scanned value, and scanned = True
        self.validate_prompts("test scanning")
        self.assertEqual(len(scanning.scan_results), 0) #validate queue was erased
        self.assertEqual(scanning.scan_mode, ScanMode.Off) #validate mode set to off

        #Test queued up scanned responses do not get accepted if scanning single
        #queue should be cleared, but scanning allowed
        scanning.scan_results = ['12345', '67890']
        self.post_dialog_responses('#1111')
        value = prompt_digits("test scanning", 
                              "help message", 
                              1, None, 
                              False, ScanMode.Single) #Test using Off
        
        self.assertEqual(('1111', True), value) #Scanned value, and scanned = True
        self.validate_prompts("test scanning")
        self.assertEqual(len(scanning.scan_results), 0) #validate queue was erased
        self.assertEqual(scanning.scan_mode, ScanMode.Off) #validate mode set to off


    def test_scanning_multiple(self):
        
        #test normal prompt/scan works same
        self.post_dialog_responses('#1111')
        value = prompt_digits("test scanning", 
                              "help message", 
                              1, None, 
                              False, ScanMode.Multiple) #Test using Off
        
        self.assertEqual(('1111', True), value) #Scanned value, and scanned = True
        self.validate_prompts("test scanning")
        self.assertEqual(len(scanning.scan_results), 0) #validate queue was erased
        self.assertEqual(scanning.scan_mode, ScanMode.Multiple) #validate mode still multiple
        
        #Test queued up scanned response is used
        scanning.scan_results.append('12345')
        scanning.scan_results.append('67890')
        
        value = prompt_digits("test scanning", 
                              "help message", 
                              1, None, 
                              False, ScanMode.Multiple,
                              priority_prompt=False) #Test using Off
        
        self.assertEqual(('12345', True), value) #Scanned value, and scanned = True
        self.validate_prompts()
        self.assertEqual(len(scanning.scan_results), 1) #validate queue still has scans left
        self.assertEqual(scanning.scan_mode, ScanMode.Multiple) #validate mode still multiple

        value = prompt_digits("test scanning", 
                              "help message", 
                              1, None, 
                              False, ScanMode.Multiple,
                              priority_prompt=False) #Test using Off
        
        self.assertEqual(('67890', True), value) #Scanned value, and scanned = True
        self.validate_prompts()
        self.assertEqual(len(scanning.scan_results), 0) #validate queue still has scans left
        self.assertEqual(scanning.scan_mode, ScanMode.Multiple) #validate mode still multiple

        
        #Test switching back to single erases queue, even though mode was multiple
        scanning.scan_results.append('22222')
        self.post_dialog_responses('#1111')
        
        value = prompt_digits("test scanning", 
                              "help message", 
                              1, None, 
                              False, ScanMode.Single) #Test Switch back to single
        
        self.assertEqual(('1111', True), value) #Scanned value, and scanned = True
        self.validate_prompts("test scanning")
        self.assertEqual(len(scanning.scan_results), 0) #validate queue still has scans left
        self.assertEqual(scanning.scan_mode, ScanMode.Off) #scanning should be off

    def test_scanning_parse_callback(self):
        scanning.set_scan_post_process_callback(parse_scan)
        #test scan result is converted
        self.post_dialog_responses('#1234567890')
        
        value = prompt_digits("test scanning", 
                              "help message", 
                              1, None, 
                              False, ScanMode.Single) 
        
        self.assertEqual(('ABCDE67890', True), value) #Scanned value, and scanned = True
        self.validate_prompts("test scanning")
        self.assertEqual(scanning.scan_mode, ScanMode.Off) #scanning should be off
        
        #test spoken result is not converted
        self.post_dialog_responses('1234567890ready')
        
        value = prompt_digits("test scanning", 
                              "help message", 
                              1, None, 
                              False, ScanMode.Single) 
        
        self.assertEqual(('1234567890', False), value) #Scanned value, and scanned = True
        self.validate_prompts("test scanning")
        self.assertEqual(scanning.scan_mode, ScanMode.Off) #scanning should be off

    def test_separate_required_key(self):
        # create keys for testing purposes
        from vocollect_core.utilities.localization import itext, _resources
        itext('')
        _resources["generic.wrong.scan"] = "Wrong scan"
        _resources["generic.wrong.scan.with.value"] = "Wrong scan <spell>{0}</spell>, please check your aim, and try again"

        # scans matching spoken are not accepted
        self.post_dialog_responses("#123", "654321", "#987654")
        value, is_scanned = prompt_digits_required("Prompt", "help",
                                                   ["123", "456", "000000"], # 6-digit max
                                                   ["654321", "987654"],
                                                   invalid_scan_key = "generic.wrong.scan")
        self.assertEqual(value, "987654")
        self.assertTrue(is_scanned)
        self.validate_prompts(["Prompt", True],
                              ["Wrong scan", False],
                              ["wrong 654321, try again", False],
                              ["Prompt", False])

        # single required values, key with param
        self.post_dialog_responses("#123", "#0123456789")
        value, is_scanned = prompt_digits_required("Prompt", "help",
                                                   "123", "0123456789",
                                                   invalid_scan_key = "generic.wrong.scan.with.value")
        self.validate_prompts(["Prompt", True],
                              ["Wrong scan <spell>123</spell>, please check your aim, and try again", False])

        # default wrong keys based on non-digit characters with invalid_scan_key = None 
        self.post_dialog_responses("#123", "#ABC", "#0123456789")
        value, is_scanned = prompt_digits_required("Prompt", "help",
                                                   "123", "0123456789")
        self.validate_prompts(["Prompt", True],
                              ["wrong 123, try again", False],
                              ["wrong <spell>ABC</spell>, try again", False],
                              ["Prompt", False])
if __name__ == "__main__":
    unittest.main()
