import unittest
from vocollect_core_test.base_test_case import BaseTestCaseCore
from vocollect_core.dialog.functions import prompt_only

class TestPromptOnly(BaseTestCaseCore):

    def setUp(self):
        self.clear()

    def test_prompt_only_priority(self):
        prompt_only('Test prompt', True)
        self.validate_prompts(['Test prompt', True])

        prompt_only('Test prompt', False)
        self.validate_prompts(['Test prompt', False])


if __name__ == "__main__":
    unittest.main()

