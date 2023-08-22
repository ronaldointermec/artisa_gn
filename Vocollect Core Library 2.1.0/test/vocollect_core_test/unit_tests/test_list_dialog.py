import unittest
from vocollect_core_test.base_test_case import BaseTestCaseCore
from vocollect_core.dialog.functions import prompt_list, prompt_list_lut,\
    prompt_list_lut_auth
from vocollect_core.dialog.list_prompt import ListPromptExecutor

class FakeLut(object):
    def __init__(self):
        self.lut_data = [{'Field key' : 1, 'Fld Description' : 'option 1'},
                         {'Field key' : 2, 'Fld Description' : 'option 2'},
                         {'Field key' : 3, 'Fld Description' : 'option 3'}]


class TestListDialog(BaseTestCaseCore):

    def setUp(self):
        self.clear()

    def test_list_prompt(self):

        #test general flow of dialog, description, and confirmations
        self.post_dialog_responses('description',
                                   'ready',
                                   'ready',
                                   'description',
                                   'stop',
                                   '3',
                                   '1',
                                   'no',
                                   '2',
                                   'yes')
        result = prompt_list([['1', 'option 1'], ['2', 'option 2']],
                             'select option', '')

        self.assertEqual(result, '2')
        self.validate_prompts(['select option', True],
                              ['1, option 1', False],
                              ['2, option 2', False],
                              ['select option', False],
                              ['1, option 1', False],
                              ['select option', False],
                              ['wrong 3, try again', False],
                              ['select option', False],
                              ['option 1, correct?', False],
                              ['select option', False],
                              ['option 2, correct?', False])


        #Test using select command, not support directly through function
        self.post_dialog_responses('description',
                                   'select',
                                   'yes')
        executor = ListPromptExecutor(prompt='select option',
                                      help_message='',
                                      selection_list=[['1', 'option 1'],
                                                      ['2', 'option 2']])
        executor.dialog.allow_select_flag = True
        result = executor.get_results()

        self.assertEqual(result, '1')
        self.validate_prompts(['select option', True],
                              ['1, option 1', False],
                              ['option 1, correct?', False])

    def test_list_lut_prompt(self):

        #Test general flow that lut populates list correctly
        self.post_dialog_responses('description',
                                   'ready',
                                   'ready',
                                   'ready',
                                   'description',
                                   'ready',
                                   'stop',
                                   '3',
                                   'yes')
        result = prompt_list_lut(FakeLut(), 'Field key', 'Fld Description',
                                 'select option', '')

        self.assertEqual(result, '3')
        self.validate_prompts(['select option', True],
                              ['1, option 1', False],
                              ['2, option 2', False],
                              ['3, option 3', False],
                              ['select option', False],
                              ['1, option 1', False],
                              ['2, option 2', False],
                              ['select option', False],
                              ['option 3, correct?', False])

    def test_list_lut_prompt_auth(self):

        #Since same as prompt_list_lut only error message different, only test
        #is for an invalid entry
        self.post_dialog_responses('4',
                                   '3',
                                   'yes')
        result = prompt_list_lut_auth(FakeLut(), 'Field key', 'Fld Description',
                                      'select option', '')

        self.assertEqual(result, '3')
        self.validate_prompts(['select option', True],
                              ['Not authorized for <spell>4</spell>, Try again.', False],
                              ['select option', False],
                              ['option 3, correct?', False])

    def test_discrete_additional_vocab(self):
        executor = ListPromptExecutor("Test prompt")
        self.assertNotIn("AdditionalVocab", executor.dialog.links)
        # base_dialog._remove_existing_vocab
        executor = ListPromptExecutor("Test prompt", additional_vocab = {"description": False})
        self.assertNotIn("AdditionalVocab", executor.dialog.links)
        executor = ListPromptExecutor("Test prompt", help_message = "Speak a value",
                                      additional_vocab = {"ready": False},
                                      lut = FakeLut(), key_field = "Field key", description_field = "Fld Description")
        self.assertIn("AdditionalVocab", executor.dialog.links)
        self.assertNotIn("ready", executor.dialog.links["FirstDigit"].vocab)
        self.post_dialog_responses("ready")
        result = executor.get_results()
        self.assertEqual(result, "ready")
        self.validate_prompts("Test prompt")

if __name__ == "__main__":
    unittest.main()

