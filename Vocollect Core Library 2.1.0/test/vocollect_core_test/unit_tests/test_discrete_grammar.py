import mock_catalyst
from vocollect_core_test.base_test_case import BaseTestCaseCore
from vocollect_core.dialog.digits_prompt import DigitsPromptExecutor
from vocollect_core.dialog.functions import NUMERIC, ALPHA, ALPHA_NUMERIC,\
    prompt_list_lut, prompt_anchor
from vocollect_core_test.unit_tests import test_float_prompt

class FakeLut(object):
    KEY = "Key"
    DESC = "Description"
    def __init__(self, keys = [], descriptions = []):
        self.lut_data = []
        for i in range(0, min(len(keys), len(descriptions))):
            self.lut_data.append({FakeLut.KEY: keys[i], FakeLut.DESC: descriptions[i]})

class TestDiscreteGrammar(BaseTestCaseCore):

    def test_discrete_digits(self):
        # test FirstDigit is redirected and no Discrete6 node
        executor, dialog = get_test_objects(2, 5)
        self.post_dialog_responses('1!', "12345")
        result = executor.get_results()
        self.assertEquals(result, "12345")
        self.validate_prompts("Test prompt")
        self.assertIn(dialog.links["FirstDigit"], dialog.nodes["Discrete1"].in_links)
        self.assertIn("Discrete5", dialog.nodes)
        self.assertIn("Digit5", dialog.links)
        self.assertNotIn("Discrete6", dialog.nodes)
        self.assertNotIn("Digit6", dialog.links)

    def test_grammar_loop(self):
        # test previous grammar loop for max_length > 6
        executor, dialog = get_test_objects(1, 10)
        self.post_dialog_responses("123!")
        result = executor.get_results()
        self.assertEquals(result, "123")
        self.validate_prompts("Test prompt")
        self.assertNotIn("Discrete1", dialog.nodes)

    def test_characters(self):
        # grammar loop
        executor, dialog = get_test_objects(1, 10, set(ALPHA))
        self.post_dialog_responses("ABC!")
        result = executor.get_results()
        self.assertEquals(result, "ABC")
        self.validate_prompts("Test prompt")
        self.assertSetEqual(dialog.links["FirstDigit"].vocab, set(ALPHA))
        self.assertSetEqual(dialog.links["AdditionalDigits"].vocab, set(ALPHA))
        self.assertNotIn("Discrete1", dialog.nodes)

        # discrete grammar
        executor, dialog = get_test_objects(2, 4, set(ALPHA_NUMERIC))
        self.post_dialog_responses("AB3D")
        result = executor.get_results()
        self.assertEquals(result, "AB3D")
        self.validate_prompts("Test prompt")
        self.assertSetEqual(dialog.links["FirstDigit"].vocab, set(ALPHA_NUMERIC))
        self.assertIn(dialog.links["FirstDigit"], dialog.nodes["Discrete1"].in_links)
        self.assertNotIn("FifthDigit", dialog.links)

        # validate non-grammar 'Z' is ignored
        for response in ["ZABCD", "AZBCD", "ABZCD", "ABCZD"]:
            executor, dialog = get_test_objects(2, 4, set("ABCDE"))
            for c in response:
                self.post_dialog_responses(c)
            result = executor.get_results()
            self.assertEquals(result, "ABCD")
            self.validate_prompts("Test prompt")

    def test_required_values(self):
        # required value
        executor, dialog = get_test_objects(0, 0, required = (["1234"], None))
        self.post_dialog_responses("4321", "1234")
        result = executor.get_results()
        self.assertEquals(result, "1234")
        self.validate_prompts("Test prompt", "wrong 4321, try again")
        self.assertIn(dialog.links["FirstDigit"], dialog.nodes["Discrete1"].in_links)
        self.assertNotIn("Discrete5", dialog.links)
        self.assertEquals(dialog.min_length, 4)
        self.assertEquals(dialog.max_length, 4)

        executor, dialog = get_test_objects(0, 0, required = (["12345678", "876543210"], None))
        self.post_dialog_responses("12345678!")
        result = executor.get_results()
        self.assertEquals(result, "12345678")
        self.validate_prompts("Test prompt")
        self.assertNotIn("Discrete1", dialog.nodes)
        self.assertEquals(dialog.min_length, 8)
        self.assertEquals(dialog.max_length, 9)

        executor, dialog = get_test_objects(0, 0, required = (["12345678", "876543210"], None))
        self.post_dialog_responses("876543210")
        result = executor.get_results()
        self.assertEquals(result, "876543210")
        self.validate_prompts("Test prompt")
        self.assertNotIn("Discrete1", dialog.nodes)
        self.assertEquals(dialog.min_length, 8)
        self.assertEquals(dialog.max_length, 9)

    def test_discrete_list(self):
        # 1-2 digits with discrete grammar
        lut = FakeLut([1, 2, 10], ["First", "Second", "Tenth"])
        self.post_dialog_responses("1!", "yes")
        result = prompt_list_lut(lut, FakeLut.KEY, FakeLut.DESC, "Choice?", "Choose one")
        self.assertEquals(result, '1')
        self.validate_prompts("Choice?", "First, correct?")

        self.post_dialog_responses("10", "yes")
        result = prompt_list_lut(lut, FakeLut.KEY, FakeLut.DESC, "Choice?", "Choose one")
        self.assertEquals(result, "10")
        self.validate_prompts("Choice?", "Tenth, correct?")

        # 2-7 digits in grammar loop
        lut = FakeLut([20, 30, 1234567, 1234568, 1234569], ["Twentieth", "Thirtieth", "Long seventh", "Long eighth", "Long ninth"])
        self.post_dialog_responses("1!", "20!", "yes")
        result = prompt_list_lut(lut, FakeLut.KEY, FakeLut.DESC, "Choice?", "Choose one")
        self.assertEquals(result, "20")
        self.validate_prompts("Choice?", "Twentieth, correct?")

        self.post_dialog_responses("1234566", "1234567", "yes")
        result = prompt_list_lut(lut, FakeLut.KEY, FakeLut.DESC, "Choice?", "Choose one")
        self.assertEquals(result, "1234567")
        self.validate_prompts("Choice?", "wrong 1234566, try again", "Choice?", "Long seventh, correct?")

    def test_anchor_words(self):
        # test prompt_anchor with lengths None, 100000
        self.post_dialog_responses("123ready", "yes")
        result = prompt_anchor("Anchored digits?", "Speak digits then ready")
        self.assertEquals(result, ("123", "ready"))
        self.validate_prompts("Anchored digits?", "<spell>123</spell> ready, correct?")

        # test discrete grammar
        executor = DigitsPromptExecutor("Anchored digits?", help_message = "Speak 6 digits or 5 and ready",
                                        additional_vocab = {"stop": False},
                                        min_length = None, max_length = 6,
                                        anchor_words = ["ready"])
        self.post_dialog_responses("456ready", "yes")
        result = executor.get_results()
        self.assertEquals(result, ("456", "ready"))
        self.validate_prompts("Anchored digits?", "<spell>456</spell> ready, correct?")

        executor = DigitsPromptExecutor("Anchored digits?", help_message = "Speak 6 digits or 5 and ready",
                                        additional_vocab = {"stop": False},
                                        min_length = None, max_length = 6,
                                        anchor_words = ["ready"])
        self.post_dialog_responses("123456", "yes")
        result = executor.get_results()
        self.assertEquals(result, ("123456", None))
        self.validate_prompts("Anchored digits?", "123456, correct?")

    def test_discrete_floats(self):
        # test float prompt

        # default whole = loop, decimal = 2
        executor, dialog = test_float_prompt.get_test_objects()
        self.post_dialog_responses("1234!", "1234.15!", "yes")
        result = executor.get_results()
        self.assertEqual(result, "1234.15")
        self.validate_prompts(["Prompt", True],
                              ["1234 re enter", False],
                              ["<spell>1234.15</spell>, correct?", False])
        self.assertIn("Initialize", dialog.nodes)
        self.assertIn(dialog.links["FirstDigit"], dialog.nodes["Initialize"].in_links)
        self.assertNotIn("Digit2", dialog.links)
        self.assertIn(dialog.links["FirstDecimal"], dialog.nodes["Decimal1"].in_links)
        self.assertIn("DecDigit2", dialog.links)
        self.assertNotIn("DecDigit3", dialog.links)
        self.assertNotIn("DecAnchor3", dialog.links)

        # whole = None, decimal = None
        has_cancel = "cancel" in mock_catalyst.all_vocab
        if not has_cancel:
            mock_catalyst.all_vocab.append("cancel")
        executor, dialog = test_float_prompt.get_test_objects(decimal_places = None, additional_vocab = {"ready": False},
                                                              min_value = None, max_value = None)
        self.post_dialog_responses("123!", "456!", ".!", "789!", "0ready", "no",
                                   "123!", "cancel", "ready")
        result = executor.get_results()
        self.assertEqual(result, "ready")
        self.validate_prompts(["Prompt", True],
                              ["<spell>123456.7890</spell>, correct?", False],
                              ["Prompt", False],
                              ["Prompt", False])
        self.assertIn(dialog.links["FirstDigit"], dialog.nodes["Initialize"].in_links)
        self.assertIn(dialog.links["FirstDecimal"], dialog.nodes["InitializeDecimal"].in_links)
        if not has_cancel:
            mock_catalyst.all_vocab.pop(mock_catalyst.all_vocab.index("cancel"))

    def test_digit_grammars(self):
        # dry run through discrete grammar
        additional_vocab = {}
        for include_additional in [True, False]:
            for length in range(1, 7):
                additional_vocab.clear()
                if include_additional:
                    additional_vocab["ready"] = False
                    additional_vocab["stop"] = True
                entry = '1' * length
                executor, dialog = get_test_objects(2 if length > 1 else 1, length,
                                                    confirm = True, additional_vocab = additional_vocab)
                self.post_dialog_responses(entry, "yes")
                result = executor.get_results()
                self.assertEqual(result, entry)
                self.validate_prompts(["Test prompt", True],
                                      [entry + ", correct?", False])
                if include_additional:
                    self.assertIn("AdditionalVocab", dialog.links)
                else:
                    self.assertNotIn("AdditionalVocab", dialog.links)
                for place in range(1, length + 1): # inclusive
                    self.assertIn("Discrete" + str(place), dialog.nodes)
                    self.assertIn(("Digit" + str(place)) if place > 1 else "FirstDigit",
                                  dialog.links)
                self.assertNotIn("Discrete" + str(length + 1), dialog.nodes)

    def test_float_grammars(self):
        # dry run through discrete grammar combinations
        additional_vocab = {}
        for include_additional in [True, False]:
            for whole_places in range(1, 7):
                for decimal_places in range(1, 7):
                    additional_vocab.clear()
                    if include_additional:
                        additional_vocab["ready"] = False
                        additional_vocab["stop"] = True

                    entry = '1' * whole_places + '.' + '1' * decimal_places
                    max_value = entry.replace('1', '9')
                    executor, dialog = test_float_prompt.get_test_objects(decimal_places = None,
                                                                          additional_vocab = additional_vocab,
                                                                          max_value = max_value)
                    self.post_dialog_responses(entry, "yes")
                    result = executor.get_results()
                    self.assertEqual(result, entry)
                    self.validate_prompts(["Prompt", True],
                                          ["<spell>" + entry + "</spell>, correct?", False])
                    if include_additional:
                        self.assertIn("AdditionalVocab", dialog.links)
                    else:
                        self.assertNotIn("AdditionalVocab", dialog.links)
                    for place in range(1, whole_places + 1): # inclusive
                        self.assertIn("Discrete" + str(place), dialog.nodes)
                        self.assertIn(("Digit" + str(place)) if place > 1 else "FirstDigit",
                                      dialog.links)
                        self.assertIn("DecimalVocab" + str(place), dialog.links)
                    self.assertNotIn("Discrete" + str(whole_places + 1), dialog.nodes)
                    for place in range(1, decimal_places + 1): # inclusive
                        self.assertIn("Decimal" + str(place), dialog.nodes)
                        self.assertIn(("DecDigit" + str(place)) if place > 1 else "FirstDecimal",
                                      dialog.links)
                    self.assertNotIn("Decimal" + str(decimal_places + 1), dialog.nodes)


#-------------------------------------------------------------------------------
def get_test_objects(min_length, max_length, characters = NUMERIC, required = (None, None),
                     confirm = False, additional_vocab = {}):
    ''' returns a convenient executor and its dialog '''
    executor = DigitsPromptExecutor("Test prompt", help_message = "Speak digits",
                                    confirm = confirm,
                                    min_length = min_length, max_length = max_length,
                                    additional_vocab = additional_vocab,
                                    characters = characters,
                                    required_spoken_values = required[0],
                                    required_scanned_values= required[1])
    return executor, executor.dialog