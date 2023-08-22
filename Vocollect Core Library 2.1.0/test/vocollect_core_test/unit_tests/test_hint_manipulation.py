from vocollect_core_test.base_test_case import BaseTestCaseCore
from vocollect_core.dialog.digits_prompt import DigitsPromptExecutor
import mock_catalyst
from vocollect_core.utilities import util_methods
from vocollect_core.utilities.util_methods import CatalystVersion

def override_catalyst_multi():
    # test multi hints
    return CatalystVersion([2, 0, 0])

def override_catalyst_single():
    return CatalystVersion([1, 0, 0])

# this requires mock_catalyst 1.2 or greater, with mock_catalyst.Node as subclass of voice.dialog_objects.Node
class TestHintManipulation(BaseTestCaseCore):

    def setUp(self):
        # save off original catalyst version function, which does not work with mock_catalyst
        self.original_catalyst_function = util_methods.catalyst_version

    def tearDown(self):
        # replace with original function
        util_methods.catalyst_version = self.original_catalyst_function

    def test_strlist_hint_single(self):
        if not hasattr(mock_catalyst.Node("Test"), "response_expression"):
            print("Warning: TestHintManipulation.test_strlist_hint_single:")
            print("  mock_catalyst.Node must subclass voice.dialog_objects.Node to test a node's response expressions (or implement its own),")
            print("  use at least mock_catalyst 1.2 to run this test")
            return
        util_methods.catalyst_version = override_catalyst_single
        # test hints can be string or list against old versions
        executor = DigitsPromptExecutor("Prompt", max_length = 3, hints = "123")
        self.assertSameElements(executor.dialog.nodes["StartHere"].response_expression, ["123"])
        executor = DigitsPromptExecutor("Prompt", hints = "123")
        self.assertSameElements(executor.dialog.nodes["StartHere"].response_expression, ["123"])
        executor = DigitsPromptExecutor("Prompt", max_length = 3, hints = ["123", "456"])
        self.assertSameElements(executor.dialog.nodes["StartHere"].response_expression,  ["123"])
        executor = DigitsPromptExecutor("Prompt", hints = ["123", "456"])
        self.assertSameElements(executor.dialog.nodes["StartHere"].response_expression,  ["123"])
        executor = DigitsPromptExecutor("Prompt", required_spoken_values = ["12", "456"])
        self.assertSameElements(executor.dialog.nodes["StartHere"].response_expression,  ["12"])

        # Test invalid hints do not get set
        executor = DigitsPromptExecutor("Prompt")
        executor.dialog.set_hints(Exception("This is not a valid hint"))
        self.assertSameElements(executor.dialog.nodes["StartHere"].response_expression, [])
        self.assertEqual("DIGITS PROMPT: hints expected list or string, received <class 'Exception'>: This is not a valid hint", mock_catalyst.log_messages[-1])

        executor = DigitsPromptExecutor("Prompt", hints = {"123": True, "456": False})
        self.assertSameElements(executor.dialog.nodes["StartHere"].response_expression, [])
        self.assertIn(mock_catalyst.log_messages[-1], ["DIGITS PROMPT: hints expected list or string, received <class 'dict'>: {'123': True, '456': False}",
                                                        "DIGITS PROMPT: hints expected list or string, received <class 'dict'>: {'456': False, '123': True}"])
    def test_strlist_hints(self):
        if not hasattr(mock_catalyst.Node("Test"), "response_expression"):
            print("Warning: TestHintManipulation.test_strlist_hints:")
            print("  mock_catalyst.Node must subclass voice.dialog_objects.Node to test a node's response expressions (or implement its own),")
            print("  use at least mock_catalyst 1.2 to run this test")
            return

        util_methods.catalyst_version = override_catalyst_multi

        # test hints can be string or list, and ready only appended when less than max_length
        executor = DigitsPromptExecutor("Prompt", max_length = 3, hints = "123")
        self.assertSameElements(executor.dialog.nodes["StartHere"].response_expression, ["123"])
        executor = DigitsPromptExecutor("Prompt", hints = "123")
        self.assertSameElements(executor.dialog.nodes["StartHere"].response_expression, ["123", "123ready"])
        executor = DigitsPromptExecutor("Prompt", max_length = 3, hints = ["123", "456"])
        self.assertSameElements(executor.dialog.nodes["StartHere"].response_expression,  ["123", "456"])
        executor = DigitsPromptExecutor("Prompt", hints = ["123", "456"])
        self.assertSameElements(executor.dialog.nodes["StartHere"].response_expression,  ["123", "456", "123ready", "456ready"])
        executor = DigitsPromptExecutor("Prompt", required_spoken_values = ["12", "456"])
        self.assertSameElements(executor.dialog.nodes["StartHere"].response_expression,  ["12", "456", "12ready"])

        # Test invalid hints do not get set
        executor = DigitsPromptExecutor("Prompt")
        executor.dialog.set_hints(Exception("This is not a valid hint"))
        self.assertSameElements(executor.dialog.nodes["StartHere"].response_expression, [])
        self.assertEqual("DIGITS PROMPT: hints expected list or string, received <class 'Exception'>: This is not a valid hint", mock_catalyst.log_messages[-1])

        executor = DigitsPromptExecutor("Prompt", hints = {"123": True, "456": False})
        self.assertSameElements(executor.dialog.nodes["StartHere"].response_expression, [])
        self.assertIn(mock_catalyst.log_messages[-1], ["DIGITS PROMPT: hints expected list or string, received <class 'dict'>: {'123': True, '456': False}",
                                                        "DIGITS PROMPT: hints expected list or string, received <class 'dict'>: {'456': False, '123': True}"])
