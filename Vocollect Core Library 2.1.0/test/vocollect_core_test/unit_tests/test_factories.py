import mock_catalyst #@UnusedImport
import unittest
from vocollect_core_test.base_test_case import BaseTestCaseCore

# Override the DigitsPrompt class
from vocollect_core.dialog.digits_prompt import DigitsPrompt
from vocollect_core.utilities import class_factory
class MyDigitsPrompt(DigitsPrompt):
    def __init__(self, prompt, help, #@ReservedAssignment
                 min_length=1, max_length=10,
                 confirm=True, scan=False):
        super().__init__(prompt, help, min_length, max_length, confirm, scan)
        self.nodes['PromptHere'].prompt = self.nodes['PromptHere'].prompt + " override works"


class TestFactories(BaseTestCaseCore):

    def test_factories(self):
        
        class_factory.set_override(DigitsPrompt, MyDigitsPrompt)
        from vocollect_core.dialog.functions import prompt_digits
        
        self.post_dialog_responses('1')
        
        value, scanned = prompt_digits("test DigitsPrompt", #@UnusedVariable
                                       "help message", 
                                       1, 1, 
                                       False, True)
        
        
        self.assertEqual('1', value)
        # Prompt should have been the overridden prompt
        self.validate_prompts("test DigitsPrompt override works")

        # Unset the custom class
        class_factory.set_override(DigitsPrompt, DigitsPrompt)
        
if __name__ == "__main__":
    unittest.main()
