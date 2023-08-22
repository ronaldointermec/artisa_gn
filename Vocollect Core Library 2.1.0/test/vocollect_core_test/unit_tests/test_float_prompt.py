import mock_catalyst #@UnusedImport
from vocollect_core_test.base_test_case import BaseTestCaseCore
from vocollect_core.scanning import ScanMode
from vocollect_core.dialog.float_prompt import FloatPromptExecutor
from vocollect_core.utilities import util_methods, class_factory, obj_factory
from vocollect_core.dialog.functions import prompt_float

def override_catalyst_multi():
    # test multi hints
    return 2.0


class TestFloatPrompt(BaseTestCaseCore):

    def setUp(self):
        # save off original catalyst_version function
        self._original_catalyst_function = util_methods.catalyst_version

        # replace function with multi hint version
        util_methods.catalyst_version = override_catalyst_multi
        from vocollect_core.utilities.localization import itext
        itext('')
        from vocollect_core.utilities.localization import _resources
        _resources["generic.wrong.scan"] = "Wrong scan"

    def tearDown(self):
        # replace function with original version
        util_methods.catalyst_version = self._original_catalyst_function


    def test_prompt_float(self):
        ''' tests from 1.3.0's test_digits_dialogs '''

        #-----------------------------------------------------------
        #test normal entry with decimal places specified,
        #time out when not enough decimal places entered, no to confirm,
        #then yes to confirm

        self.post_dialog_responses('15.1!', '23.45', 'no', '67.89', 'yes')

        result = prompt_float('Enter value', 'Enter value with 2 decimal places',
                              2, True, False)

        self.assertEqual(result, '67.89')
        self.validate_prompts('Enter value',
                              '15.1 re enter',
                              '<spell>23.45</spell>, correct?',
                              'Enter value',
                              '<spell>67.89</spell>, correct?')

        #-----------------------------------------------------------
        #test normal entry with no decimal places specified
        self.post_dialog_responses('15.1!', '2345', 'ready', 'yes')

        result = prompt_float('Enter value', 'Enter value with 2 decimal places',
                              0, True, False)

        self.assertEqual(result, '15.12345') # ignored timeout
        self.validate_prompts('Enter value',
                              '<spell>15.12345</spell>, correct?')

        #-----------------------------------------------------------
        #test scanning
        #scanned value
        self.post_dialog_responses('#123456789')

        result, scanned = prompt_float('Enter value', 'Enter value with 2 decimal places',
                                       2, True, True)

        self.assertEqual(result, '123456789')
        self.assertEqual(scanned, True)
        self.validate_prompts('Enter value')
        #spoken value
        self.post_dialog_responses('1234567.89', 'yes')

        result, scanned = prompt_float('Enter value', 'Enter value with 2 decimal places',
                              2, True, True, max_value = None)

        self.assertEqual(result, '1234567.89')
        self.assertEqual(scanned, False)
        self.validate_prompts('Enter value',
                              '<spell>1234567.89</spell>, correct?')

    def test_help(self):
        #-----------------------------------------------------------
        #test help message
        self.post_dialog_responses('15.1!', 'talkman help', '2345', 'ready', 'yes')

        result = prompt_float('Enter value', 'Enter value then ready',
                              0, True, False)

        self.assertEqual(result, '15.12345') #ignored timeout
        self.validate_prompts('Enter value',
                              'Enter value then ready,, You entered 1 5 . 1 so far',
                              'Enter value',
                              '<spell>15.12345</spell>, correct?')
        entry = '15.12345'
        current = ''
        dialog_responses = []
        prompts = [['Enter value', True]]
        for c in entry:
            current += c
            dialog_responses.append(c + '!')
            dialog_responses.append('talkman help')
            prompts.append(['Enter value then ready,, You entered ' + ' '.join(current) + ' so far', False])
            prompts.append(['Enter value', False])
        dialog_responses.append('ready')
        dialog_responses.append('yes')
        prompts.append(['<spell>' + entry + '</spell>, correct?', False])
        self.post_dialog_responses(*dialog_responses)
        result = prompt_float('Enter value', 'Enter value then ready',
                              0, True, False)
        self.assertEqual(result, entry)
        self.validate_prompts(*prompts)

    def test_range(self):
        # test min and max values
        executor, _ = get_test_objects(decimal_places = None, min_value = '3.0', max_value = '4.0')
        self.post_dialog_responses("1.5", "4.5", "3.5", "yes")
        result = executor.get_results()
        self.assertEqual(result, "3.5")
        self.validate_prompts(["Prompt", True],
                              ["1.5 re enter", False],
                              ["4.5 re enter", False],
                              ["Prompt", False],
                              ["<spell>3.5</spell>, correct?", False])

        # test min and max range equivalent
        executor, _ = get_test_objects(min_value = '3.0', max_value = '3.00')
        self.post_dialog_responses("3.1!", "3.01", "3.00", "yes")
        result = executor.get_results()
        self.assertEqual("3.00", result)
        self.validate_prompts(["Prompt", True],
                              ["3.1 re enter", False],
                              ["3.01 re enter", False],
                              ["Prompt", False],
                              ["<spell>3.00</spell>, correct?", False])

    def test_custom_decimal_point(self):
        self.post_dialog_responses("15,25!", "yes")
        result = prompt_float_comma("Prompt", "Speak a value", decimal_places = None)
        self.assertEqual("15,25", result)
        self.validate_prompts(["Prompt", True],
                              ["<spell>15,25</spell>, correct?", False])

    def test_feedback_length(self):
        # feedback length of 2 which handles insertions but still provides reasonable feedback
        self.post_dialog_responses("1!", "15!", "15.!", "15.1!", "yes")
        result = prompt_float("Prompt", "Speak a value", decimal_places = None,
                              min_value = "0.0", max_value = "99.9")
        self.assertEqual(result, "15.1")
        self.validate_prompts(["Prompt", True],
                              # "1" treated as insertion
                              ["15 re enter", False],
                              ["15. re enter", False],
                              ["Prompt", False],
                              ["<spell>15.1</spell>, correct?", False])
        # feedback length of 1
        self.post_dialog_responses("1!", "15!", "15.!", "15.1!", "yes")
        result = prompt_float_feedback("Prompt", "Speak a value", decimal_places = None,
                                       min_value = "0.0", max_value = "99.9")
        self.assertEqual(result, "15.1")
        self.validate_prompts(["Prompt", True],
                              ["1 re enter", False], # insertion reported as wrong
                              ["15 re enter", False],
                              ["Prompt", False],
                              ["15. re enter", False],
                              ["<spell>15.1</spell>, correct?", False])
        # feedback length of 4 with total min length > 4
        self.post_dialog_responses("1.1!", "15.1!", "135.531", "yes")
        result = prompt_float_quiet("Prompt", "Speak a value", decimal_places = None,
                                    min_value = "000.000", max_value = "999.999")
        self.assertEqual(result, "135.531")
        self.validate_prompts(["Prompt", True],
                              ["15.1 re enter", False],
                              ["<spell>135.531</spell>, correct?", False])
        # feedback length of 4 with total min length < 4
        self.post_dialog_responses("1.1!", "yes")
        result = prompt_float_quiet("Prompt", "Speak a value", decimal_places = None,
                                    min_value = "0.0", max_value = "9.99")
        self.assertEqual(result, "1.1")
        self.validate_prompts(["Prompt", True],
                              ["<spell>1.1</spell>, correct?", False])

def get_test_objects(prompt = "Prompt",
                     priority_prompt = True,
                     help_message = "Help",
                     decimal_places = 2,
                     additional_vocab = {},
                     confirm=True,
                     scan=ScanMode.Off,
                     skip_prompt = False,
                     hints = None,
                     anchor_words = None,
                     min_value = None,
                     max_value = None):
    ''' retrieves an executor and dialog '''
    executor = FloatPromptExecutor(prompt, priority_prompt, help_message, decimal_places, additional_vocab, confirm,scan,skip_prompt, hints, anchor_words, min_value, max_value)
    return executor, executor.dialog


# testing ',' as decimal point char

class CommaFloatPromptExecutor(class_factory.get(FloatPromptExecutor)):
    def _configure_dialog(self):
        self.dialog.decimal_point_char = ','
        super()._configure_dialog()

def prompt_float_comma(prompt, help_message, decimal_places = 2,
                      confirm = True, scan = ScanMode.Off, additional_vocab = {},
                      skip_prompt = False, priority_prompt = True, hints = None,
                      min_value = '0,0', max_value = '9999,99'):
    # Note: min_value and max_value must use decimal_point_char
    executor = obj_factory.get(CommaFloatPromptExecutor,
                                   prompt=prompt,
                                   priority_prompt=priority_prompt,
                                   help_message=help,
                                   decimal_places=decimal_places,
                                   additional_vocab=additional_vocab,
                                   confirm=confirm,
                                   scan=scan,
                                   skip_prompt=skip_prompt,
                                   hints=hints,
                                   min_value=min_value,
                                   max_value=max_value)
    return executor.get_results()

# testing feedback after every recognition which does not handle insertions gracefully

class FeedbackFloatPromptExecutor(class_factory.get(FloatPromptExecutor)):
    def _configure_dialog(self):
        self.dialog.min_feedback_length = 1
        super()._configure_dialog()

def prompt_float_feedback(prompt, help_message, decimal_places = 2,
                          confirm = True, scan = ScanMode.Off, additional_vocab = {},
                          skip_prompt = False, priority_prompt = True, hints = None,
                          min_value = '0.0', max_value = '9999.99'):
    executor = obj_factory.get(FeedbackFloatPromptExecutor,
                                   prompt=prompt,
                                   priority_prompt=priority_prompt,
                                   help_message=help,
                                   decimal_places=decimal_places,
                                   additional_vocab=additional_vocab,
                                   confirm=confirm,
                                   scan=scan,
                                   skip_prompt=skip_prompt,
                                   hints=hints,
                                   min_value=min_value,
                                   max_value=max_value)
    return executor.get_results()

# testing too large min_feedback_length

class QuietFloatPromptExecutor(class_factory.get(FloatPromptExecutor)):
    def _configure_dialog(self):
        self.dialog.min_feedback_length = 4
        super()._configure_dialog()
def prompt_float_quiet(prompt, help_message, decimal_places = 2,
                          confirm = True, scan = ScanMode.Off, additional_vocab = {},
                          skip_prompt = False, priority_prompt = True, hints = None,
                          min_value = '0.0', max_value = '9999.99'):
    executor = obj_factory.get(QuietFloatPromptExecutor,
                                   prompt=prompt,
                                   priority_prompt=priority_prompt,
                                   help_message=help,
                                   decimal_places=decimal_places,
                                   additional_vocab=additional_vocab,
                                   confirm=confirm,
                                   scan=scan,
                                   skip_prompt=skip_prompt,
                                   hints=hints,
                                   min_value=min_value,
                                   max_value=max_value)
    return executor.get_results()