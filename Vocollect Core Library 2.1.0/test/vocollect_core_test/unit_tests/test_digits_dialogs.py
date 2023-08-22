import mock_catalyst #@UnusedImport
import unittest
from vocollect_core_test.base_test_case import BaseTestCaseCore
from vocollect_core.dialog.functions import prompt_digits, prompt_required, prompt_anchor
from vocollect_core.dialog.digits_prompt import DigitsPrompt,\
    DigitsPromptExecutor
import collections
from vocollect_core import scanning
from vocollect_core.scanning import ScanMode, set_scan_mode
from vocollect_core.utilities import class_factory

class TestDigitsDialog(BaseTestCaseCore):

    def setUp(self):
        # VSCVALIB-66 - MockCatalyst does not yet implement SwVersion.ApplicationVersion
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

        #test scanning shut off when it should be
        #test scanning is off and not turned on if scanmode if off
        self.post_dialog_responses('123!')
        self.assertEqual(None, mock_catalyst.scan_call_back_method)
        result = prompt_digits("enter value", '',
                               scan = ScanMode.Off,
                               confirm=False)
        self.assertEqual('123', result)
        self.validate_prompts('enter value')
        self.assertEqual(None, mock_catalyst.scan_call_back_method)

        #test scanning is off and not turned on if scanmode is single and value spoken
        self.post_dialog_responses('123!')
        result = prompt_digits("enter value", '',
                               scan = ScanMode.Single,
                               confirm=False)
        self.assertEqual(('123', False), result)
        self.validate_prompts('enter value')
        self.assertEqual(None, mock_catalyst.scan_call_back_method)

        #test scanning is off and not turned on if scanmode is single and value scanned
        self.post_dialog_responses('#123')
        result = prompt_digits("enter value", '',
                               scan = ScanMode.Single,
                               confirm=False)
        self.assertEqual(('123', True), result)
        self.validate_prompts('enter value')
        self.assertEqual(None, mock_catalyst.scan_call_back_method)

        #Test scanning is turned off even when exception thrown
        self.post_dialog_responses('-')
        self.assertRaises(mock_catalyst.EndOfApplication, prompt_digits,
                                "enter value", '',
                                scan = ScanMode.Single,
                                confirm=False)
        self.assertEqual(('123', True), result)
        self.validate_prompts('enter value')
        self.assertEqual(None, mock_catalyst.scan_call_back_method)


        #test scanning is still on if multiple mode and spoken value
        self.post_dialog_responses('123!')
        result = prompt_digits("enter value", '',
                               scan = ScanMode.Multiple,
                               confirm=False)
        self.assertEqual(('123', False), result)
        self.validate_prompts('enter value')
        self.assertNotEqual(None, mock_catalyst.scan_call_back_method)

        #test scanning is still on if multiple mode and scanned value
        self.post_dialog_responses('#123')
        result = prompt_digits("enter value", '',
                               scan = ScanMode.Multiple,
                               confirm=False)
        self.assertEqual(('123', True), result)
        self.validate_prompts('enter value')
        self.assertNotEqual(None, mock_catalyst.scan_call_back_method)

        #Test scanning is off if scan mode set to off
        set_scan_mode(ScanMode.Off)
        self.assertEqual(None, mock_catalyst.scan_call_back_method)

        #Test scanning is not turned off even when exception thrown multiple mode
        self.post_dialog_responses('-')
        self.assertRaises(mock_catalyst.EndOfApplication, prompt_digits,
                                "enter value", '',
                                scan = ScanMode.Multiple,
                                confirm=False)
        self.assertEqual(('123', True), result)
        self.validate_prompts('enter value')
        self.assertEqual(None, mock_catalyst.scan_call_back_method)


    def test_prompt_required(self):

        self.post_dialog_responses('1', 'D', 'A', '4', '2!')

        #Validadate digits are removed, and unspecified vocab are ignored
        value = prompt_required('Test Required', '',
                                ['1A2'], '123ABC')

        self.assertEqual('1A2', value) #4 should be ignored since not part of speakable values
        self.validate_prompts('Test Required')

        #Validate a incorrect value spoken
        self.post_dialog_responses('1B2!',
                                   '1A3!',
                                   '1A2!')

        value = prompt_required('Test Required', '',
                                ['1A2'], '123ABC')

        self.assertEqual('1A2', value) #4 should be ignored since not part of speakable values
        self.validate_prompts('Test Required',
                              'wrong <spell>1B2</spell>, try again',
                              'wrong <spell>1A3</spell>, try again',
                              'Test Required') #Validates main prompt is spoken after 2 failures

    def test_prompt_digits(self):
        #Test both min and max values set
        self.post_dialog_responses('12!', '123!', 'no', '1234567890', 'yes')
        value = prompt_digits('prompt', 'help', 3, 10)
        self.assertEqual('1234567890', value)
        self.validate_prompts('prompt',
                              '123, correct?',
                              'prompt',
                              '1234567890, correct?')

        #Test Min Value set to none
        self.post_dialog_responses('12345!', '123ready', 'no', '1234567890', 'yes')
        value = prompt_digits('prompt', 'help', None, 10)
        self.assertEqual('1234567890', value)
        self.validate_prompts('prompt',
                              '123, correct?',
                              'prompt',
                              '1234567890, correct?')

        #Test Max Value set to none
        self.post_dialog_responses('12!', '345!', 'talkman help', 'ready', 'no', '1234567890ready', 'yes')
        value = prompt_digits('prompt', 'help', 3, None)
        self.assertEqual('1234567890', value)
        self.validate_prompts('prompt',
                              'You entered 12345, say ready if complete',
                              'prompt',
                              '12345, correct?',
                              'prompt',
                              '1234567890, correct?')

        #Test Min and Max Value set to none (result same as Max set to none)
        self.post_dialog_responses('12!', '345!', 'talkman help', 'ready', 'no', '1234567890ready', 'yes')
        value = prompt_digits('prompt', 'help', None, None)
        self.assertEqual('1234567890', value)
        self.validate_prompts('prompt',
                              'You entered 12345, say ready if complete',
                              'prompt',
                              '12345, correct?',
                              'prompt',
                              '1234567890, correct?')

    def test_prompt_anchor(self):

        #test anchor returned properly
        self.post_dialog_responses('15', 'ounces', 'yes')
        result, anchor = prompt_anchor('Speak weight',
                                       'speak weight followed by pounds or ounces',
                                       ['pounds', 'ounces'],
                                       additional_vocab = {'stop' : True})
        self.assertEqual('15', result)
        self.assertEqual('ounces', anchor)
        self.validate_prompts('Speak weight',
                              '<spell>15</spell> ounces, correct?')

        #test anchor returned properly after confirming no first time and changing
        self.post_dialog_responses('15', 'ounces', 'no', '1111', 'pounds', 'yes')
        result, anchor = prompt_anchor('Speak weight',
                                       'speak weight followed by pounds or ounces',
                                       ['pounds', 'ounces'],
                                       additional_vocab = {'stop' : True})
        self.assertEqual('1111', result)
        self.assertEqual('pounds', anchor)
        self.validate_prompts('Speak weight',
                              '<spell>15</spell> ounces, correct?',
                              'Speak weight',
                              '<spell>1111</spell> pounds, correct?')

        #Test exit word does not return any anchor value
        self.post_dialog_responses('15', 'ounces', 'no', 'stop', 'yes')
        result, anchor = prompt_anchor('Speak weight',
                                       'speak weight followed by pounds or ounces',
                                       ['pounds', 'ounces'],
                                       additional_vocab = {'stop' : True})
        self.assertEqual('stop', result)
        self.assertEqual(None, anchor)
        self.validate_prompts('Speak weight',
                              '<spell>15</spell> ounces, correct?',
                              'Speak weight',
                              'stop, correct?')

        #Test timeout does not accumulate extra digits
        self.post_dialog_responses('15', '!', '16', 'ounces', 'yes')
        result, anchor = prompt_anchor('Speak weight',
                                       'speak weight followed by pounds or ounces',
                                       ['pounds', 'ounces'],
                                       additional_vocab = {'stop' : True})
        self.assertEqual('16', result)
        self.assertEqual('ounces', anchor)
        self.validate_prompts('Speak weight',
                              '<spell>16</spell> ounces, correct?')

        #Test scanning does not return any previously entered anchors
        self.post_dialog_responses('15', '16', 'ounces', 'no', '#123456')
        result, anchor, scanned = prompt_anchor('Speak weight',
                                                'speak weight followed by pounds or ounces',
                                                ['pounds', 'ounces'],
                                                scan = True,
                                                additional_vocab = {'stop' : True})
        self.assertEqual('123456', result)
        self.assertEqual(None, anchor)
        self.assertEqual(True, scanned)
        self.validate_prompts('Speak weight',
                              '<spell>1516</spell> ounces, correct?',
                              'Speak weight')

        #Test scanning returns false correctly
        self.post_dialog_responses('stop', 'yes')
        result, anchor, scanned = prompt_anchor('Speak weight',
                                                'speak weight followed by pounds or ounces',
                                                ['pounds', 'ounces'],
                                                scan = True,
                                                additional_vocab = {'stop' : True})
        self.assertEqual('stop', result)
        self.assertEqual(None, anchor)
        self.assertEqual(False, scanned)
        self.validate_prompts('Speak weight',
                              'stop, correct?')

        self.post_dialog_responses('15', 'ounces', 'yes')
        result, anchor, scanned = prompt_anchor('Speak weight',
                                                'speak weight followed by pounds or ounces',
                                                ['pounds', 'ounces'],
                                                scan = True,
                                                additional_vocab = {'stop' : True})
        self.assertEqual('15', result)
        self.assertEqual('ounces', anchor)
        self.assertEqual(False, scanned)
        self.validate_prompts('Speak weight',
                               '<spell>15</spell> ounces, correct?')

    def test_hints(self):
        compare = lambda x, y: collections.Counter(x) == collections.Counter(y)

        dlg = DigitsPrompt('', '', 1, 10)

        #test ready is appended to each hint and duplicates, empty hints, and single length hints are ignored
        dlg.set_hints(['00', '01', '01', '0', '', None])
        expected = ['00', '01', '00ready', '01ready', '0ready']
        current = dlg.nodes['StartHere'].response_expression
        self.assertTrue(compare(current, expected),
                        'Hints not equal current: %s expected: %s' %
                        (current, expected))

        # test that only required values are set as hints and not scanned required values
        # test that ready is only appended if less than max length
        dlg.set_required(['00', '01', '0'], ['scan00', 'scan01'])
        expected = ['00', '01', '0ready']
        current = dlg.nodes['StartHere'].response_expression
        self.assertTrue(compare(current, expected),
                        'Hints not equal current: %s expected: %s' %
                        (current, expected))

        #test anchors do not get ready or any other changes to them
        dlg.set_anchors('anchor1')
        dlg.set_hints(['00', '01', '01', '0', ''])
        current = dlg.nodes['StartHere'].response_expression
        expected = ['00', '01']
        self.assertTrue(compare(current, expected),
                        'Hints not equal current: %s expected: %s' %
                        (current, expected))

        #Test Executor sets hints
        dlg = DigitsPromptExecutor('test hints',
                                   required_spoken_values = None,
                                   required_scanned_values = None,
                                   anchor_words=None,
                                   hints = ['00', '01'])
        expected = ['00', '01', '00ready', '01ready']
        current = dlg.dialog.nodes['StartHere'].response_expression
        self.assertTrue(compare(current, expected),
                        'Hints not equal current: %s expected: %s' %
                        (current, expected))

        #Test Executor Hints parameter overrides required values
        dlg = DigitsPromptExecutor('test hints',
                                   required_spoken_values = ['02', '03'],
                                   required_scanned_values = None,
                                   anchor_words=None,
                                   hints = ['00', '01'])
        expected = ['00', '01']
        current = dlg.dialog.nodes['StartHere'].response_expression
        self.assertTrue(compare(current, expected),
                        'Hints not equal current: %s expected: %s' %
                        (current, expected))


    def test_priority_prompts(self):
        #Test default is true
        self.post_dialog_responses('12!')
        value = prompt_digits('Test Priority', '', confirm=False)
        self.assertEqual(value, '12')
        self.validate_prompts(['Test Priority', True])

        self.post_dialog_responses('13!')
        value = prompt_digits('Test Priority', '', confirm=False, priority_prompt=False)
        self.assertEqual(value, '13')
        self.validate_prompts(['Test Priority', False])

    def test_executor_check_scanning(self):
        executor = DigitsPromptExecutor('Test Prompt',
                                        priority_prompt=True,
                                        scan = True,
                                        required_scanned_values = None,
                                        anchor_words = None)

        #test false returned from scan result check
        # calls set_scan_mode and clears scanning.scan_results
        self.assertFalse(executor.check_scanning_result())
        self.assertFalse(executor.scanned)
        self.assertEqual(executor.result, None)

        #test false since priority prompt is true
        scanning.scan_results = ['12345']
        # since set_scan_mode already called, does not clear scanning.scan_results
        self.assertFalse(executor.check_scanning_result())
        self.assertFalse(executor.scanned)
        self.assertEqual(executor.result, None)
        self.assertEqual(scanning.scan_results, ['12345'])

        #test scanned result picked up if dialog is executed
        scanning.set_scan_mode(scanning.ScanMode.Single)
        scanning.scan_results = ['12345']
        executor.execute_dialog()
        self.assertTrue(executor.scanned)
        self.assertEqual(executor.result, '12345')
        self.assertEqual(scanning.scan_results, [])

        #test scanning check returns true if priority prompt is false
        executor = DigitsPromptExecutor('Test Prompt',
                                        priority_prompt=False,
                                        scan = True,
                                        required_scanned_values = None,
                                        anchor_words = None)

        scanning.scan_results = ['12345']
        self.assertTrue(executor.check_scanning_result())
        self.assertTrue(executor.scanned)
        self.assertEqual(executor.result, '12345')
        self.assertEqual(scanning.scan_results, [])

        #test scanning check returns false if required scanned values exist
        executor = DigitsPromptExecutor('Test Prompt',
                                        priority_prompt=False,
                                        scan = True,
                                        required_scanned_values = ['12345'],
                                        anchor_words = None)

        scanning.scan_results = ['12345']
        # check_scanning_result calls set_scan_mode which clears scanning.scan_results
        self.assertFalse(executor.check_scanning_result())
        self.assertFalse(executor.scanned)
        self.assertEqual(executor.result, None)
        self.assertEqual(scanning.scan_results, [])

        #test scanning check returns false if scanning is off
        executor = DigitsPromptExecutor('Test Prompt',
                                        priority_prompt=False,
                                        scan = False,
                                        required_scanned_values = None,
                                        anchor_words = None)

        scanning.scan_results = ['12345']
        self.assertFalse(executor.check_scanning_result())
        self.assertFalse(executor.scanned)
        self.assertEqual(executor.result, None)
        self.assertEqual(scanning.scan_results, ['12345'])

    def test_executor_get_results(self):
        #test no scanning, no anchor word
        executor = DigitsPromptExecutor('Test Prompt',
                                        priority_prompt=False,
                                        scan = False,
                                        required_scanned_values = None,
                                        anchor_words = None)

        self.post_dialog_responses('13!', 'yes')
        results = executor.get_results()
        self.assertEqual(results, '13')

        #test scanning, spoken result, no anchor word
        executor = DigitsPromptExecutor('Test Prompt',
                                        priority_prompt=False,
                                        scan = True,
                                        required_scanned_values = None,
                                        anchor_words = None)

        self.post_dialog_responses('13!', 'yes')
        results = executor.get_results()
        self.assertEqual(results, ('13', False))

        #test scanning, scanned result, no anchor word
        executor = DigitsPromptExecutor('Test Prompt',
                                        priority_prompt=False,
                                        scan = True,
                                        required_scanned_values = None,
                                        anchor_words = None)

        scanning.set_scan_mode(scanning.ScanMode.Single)
        scanning.scan_results = ['12345']
        results = executor.get_results()
        self.assertEqual(results, ('12345', True))

        #test no scanning, anchor word
        executor = DigitsPromptExecutor('Test Prompt',
                                        priority_prompt=False,
                                        scan = False,
                                        required_scanned_values = None,
                                        anchor_words = ['inches', 'feet'])

        self.post_dialog_responses('13inches', 'yes')
        results = executor.get_results()
        self.assertEqual(results, ('13', 'inches'))

        #test scanning, anchor word, spoken result
        executor = DigitsPromptExecutor('Test Prompt',
                                        priority_prompt=False,
                                        scan = True,
                                        required_scanned_values = None,
                                        anchor_words = ['inches', 'feet'])

        self.post_dialog_responses('12feet', 'yes')
        results = executor.get_results()
        self.assertEqual(results, ('12', 'feet', False))

        #test scanning, anchor word, scanned result
        executor = DigitsPromptExecutor('Test Prompt',
                                        priority_prompt=False,
                                        scan = True,
                                        required_scanned_values = None,
                                        anchor_words = ['inches', 'feet'])

        self.post_dialog_responses('#12345')
        results = executor.get_results()
        self.assertEqual(results, ('12345', None, True))

        #test scanning, anchor word, scanned result prior to dialog
        executor = DigitsPromptExecutor('Test Prompt',
                                        priority_prompt=False,
                                        scan = True,
                                        required_scanned_values = None,
                                        anchor_words = ['inches', 'feet'])

        scanning.set_scan_mode(scanning.ScanMode.Single)
        scanning.scan_results = ['12345']
        results = executor.get_results()
        self.assertEqual(results, ('12345', None, True))


    def test_discrete_additional_vocab(self):
        # test no link between StartHere and AdditionalVocabResult
        executor = DigitsPromptExecutor("Test prompt")
        dialog = executor.dialog
        self.assertNotIn("AdditionalVocab", dialog.links)
        self.assertNotIn("AdditionalVocabResult", dialog.nodes)

        # test link between StartHere and AdditionalVocabResult
        # if additional_vocab, then reset_scan() -> set_help() assumes that StartHere has help
        self.assertRaises(TypeError, prompt_digits, "Test prompt", None, additional_vocab = {"ready": False})
        del mock_catalyst.prompts[:]

        executor = DigitsPromptExecutor("Test prompt", help_message = "Test help message",
                                        additional_vocab = {"ready": False, "stop": False})
        dialog = executor.dialog
        self.assertIn("AdditionalVocab", dialog.links)
        self.assertIn(dialog.links["AdditionalVocab"], dialog.nodes["AdditionalVocabResult"].in_links)
        self.assertIn(dialog.links["AdditionalVocab"], dialog.nodes["StartHere"].out_links)
        self.assertSameElements("0123456789", dialog.links["FirstDigit"].vocab)
        self.assertSameElements({"ready", "stop"}, dialog.links["AdditionalVocab"].vocab)
        mock_catalyst.post_dialog_responses("ready")
        result = executor.get_results()
        self.validate_prompts("Test prompt")
        self.assertEqual(result, "ready")

        # test confirmation
        executor = DigitsPromptExecutor("Test prompt", help_message = "Test help message",
                                        additional_vocab = {"ready": False, "stop": True})
        mock_catalyst.post_dialog_responses("stop", "no", "123!", "no", "ready")
        result = executor.get_results()
        self.validate_prompts("Test prompt", "stop, correct?", "Test prompt", "123, correct?", "Test prompt")
        self.assertEqual(result, "ready")

        # test list and str fallback to dialog should_confirm - default True
        executor = DigitsPromptExecutor("Test prompt", help_message = "Test help message")
        dialog = executor.dialog
        dialog.set_additional_vocab(["ready", "stop"])
        self.assertSameElements({"ready", "stop"}, dialog.links["AdditionalVocab"].vocab)
        mock_catalyst.post_dialog_responses("ready", "yes")
        result = executor.get_results()
        self.validate_prompts("Test prompt", "ready, correct?")

        executor = DigitsPromptExecutor("Test prompt", help_message = "Test help message", confirm = False)
        dialog = executor.dialog
        dialog.set_additional_vocab(["ready", "stop"])
        self.assertSameElements({"ready", "stop"}, dialog.links["AdditionalVocab"].vocab)
        mock_catalyst.post_dialog_responses("ready")
        result = executor.get_results()
        self.validate_prompts("Test prompt")

        executor = DigitsPromptExecutor("Test prompt", help_message = "Test help message")
        dialog = executor.dialog
        dialog.set_additional_vocab("ready")
        self.assertSameElements({"ready"}, dialog.links["AdditionalVocab"].vocab)
        mock_catalyst.post_dialog_responses("ready", "yes")
        result = executor.get_results()
        self.validate_prompts("Test prompt", "ready, correct?")

        executor = DigitsPromptExecutor("Test prompt", help_message = "Test help message", confirm = False)
        dialog = executor.dialog
        dialog.set_additional_vocab("ready")
        self.assertSameElements({"ready"}, dialog.links["AdditionalVocab"].vocab)
        mock_catalyst.post_dialog_responses("ready")
        result = executor.get_results()
        self.validate_prompts("Test prompt")

    def test_discrete_length_override(self):
        # 10 discrete grammar nodes
        executor = VerboseDigitsPromptExecutor("Test prompt", help_message = "Test help message",
                                               max_length = 10, confirm = False)
        self.post_dialog_responses("1234567890")
        result = executor.get_results()
        self.assertEqual(result, "1234567890")
        self.assertIn("Discrete10", executor.dialog.nodes)

        # revert to loop link after 10
        executor = VerboseDigitsPromptExecutor("Test prompt", help_message = "Test help message",
                                               max_length = 11, confirm = False)
        self.post_dialog_responses("12345678901")
        result = executor.get_results()
        self.assertEqual(result, "12345678901")
        self.assertIn("Digits", executor.dialog.nodes)
        self.assertNotIn("Discrete1", executor.dialog.nodes)

class VerboseDigitsPromptExecutor(class_factory.get(DigitsPromptExecutor)):
    def _configure_dialog(self):
        self.dialog.max_discrete_length = 10
        super()._configure_dialog()

if __name__ == "__main__":
    unittest.main()
