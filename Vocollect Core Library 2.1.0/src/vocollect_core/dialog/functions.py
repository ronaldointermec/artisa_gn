#
# Copyright (c) 2010-2011 Vocollect, Inc.
# Pittsburgh, PA 15235
# All rights reserved.
#
# This source code contains confidential information that is owned by
# Vocollect, Inc. and may not be copied, disclosed or otherwise used without
# the express written consent of Vocollect, Inc.
#

from vocollect_core import obj_factory
from vocollect_core.dialog.digits_prompt import DigitsPromptExecutor
from vocollect_core.dialog.float_prompt import FloatPromptExecutor
from vocollect_core.dialog.list_prompt import ListPromptExecutor
from vocollect_core.dialog.prompt_only import PromptOnly
from vocollect_core.dialog.ready_prompt import ReadyPromptExecutor
from vocollect_core.dialog.yes_no_prompt import YesNoPromptExecutor
from vocollect_core.scanning import ScanMode

NUMERIC = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
ALPHA = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
         'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
         'U', 'V', 'W', 'X', 'Y', 'Z']
ALPHA_NUMERIC = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
                'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
                'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
                'U', 'V', 'W', 'X', 'Y', 'Z']


#############################################################################
# Wrapper methods to dialog classes
#############################################################################

#----------------------------------------------------------------------------
# Wrapper functions for PromptOnly
#----------------------------------------------------------------------------
def prompt_only(prompt, priority = False):
    ''' wrapper function for speaking a simple prompt with no vocabulary

    Parameters:
        prompt - prompt to be spoken
        priority (Default=False) - whether or not prompt is priority prompt

    returns: None
    '''
    dialog = obj_factory.get(PromptOnly, prompt, priority)
    return dialog.run()

#----------------------------------------------------------------------------
# Wrapper functions for ReadyPrompt
#----------------------------------------------------------------------------
def prompt_ready(prompt, priority_prompt = False, additional_vocab = {},
                 skip_prompt = False):
    ''' Wrapper function for prompting user and waiting for user to confirm with ready

    Parameters:
        prompt - prompt to be spoken
        priority (Default=False) - whether or not prompt is priority prompt
        additional_vocab (Default={}) - Dictionary of additional words and whether
                                        or not they should be confirmed
        skip_prompt (Default=False) - skips speaking main prompt when entering dialog

    returns: Word spoken
    '''
    executor = obj_factory.get(ReadyPromptExecutor,
                                    prompt=prompt,
                                    priority_prompt=priority_prompt,
                                    additional_vocab=additional_vocab,
                                    skip_prompt=skip_prompt)
    return executor.get_results()

def prompt_words(prompt, priority_prompt = False, additional_vocab = {}):
    ''' Wrapper function for prompting user for specified words
        (not including the word 'ready')

    Parameters:
        prompt - prompt to be spoken
        priority (Default=False) - whether or not prompt is priority prompt
        additional_vocab (Default={}) - Dictionary of additional words and whether
                                        or not they should be confirmed

    returns: Word spoken
    '''
    executor = obj_factory.get(ReadyPromptExecutor,
                                    prompt=prompt,
                                    priority_prompt=priority_prompt,
                                    additional_vocab=additional_vocab)
    executor.dialog.remove_ready()
    return executor.get_results()

#----------------------------------------------------------------------------
# Wrapper functions for YesNoPrompt
#----------------------------------------------------------------------------
def prompt_yes_no(prompt, priority_prompt = False, time_out = 0):
    ''' Wrapper function for simple yes/no dialog

    Parameters:
        prompt - prompt to be spoken
        priority (Default=False) - whether or not prompt is priority prompt
        time_out (Default=0) - time (in seconds) to wait before returning false
                 if set to 0, then dialog waits for user response
    returns: True if operator speaks 'yes' otherwise False
    '''
    executor = obj_factory.get(YesNoPromptExecutor,
                                    prompt=prompt,
                                    priority_prompt=priority_prompt,
                                    time_out=time_out)
    return executor.get_results() == 'yes'


def prompt_yes_no_cancel(prompt, priority_prompt = False):
    ''' Wrapper function for simple yes/no/cancel dialog

    Parameters:
        prompt - prompt to be spoken
        priority (Default=False) - whether or not prompt is priority prompt

    returns: yes, no, or cancel
    '''
    executor = obj_factory.get(YesNoPromptExecutor,
                                    prompt=prompt,
                                    priority_prompt=priority_prompt,
                                    include_cancel=True)
    return executor.get_results()


#----------------------------------------------------------------------------
# Wrapper functions for DigitsPrompt
#----------------------------------------------------------------------------
def prompt_digits(prompt, help, min_length=1, max_length=10, #@ReservedAssignment
                  confirm=True, scan=ScanMode.Off, additional_vocab = {},
                  skip_prompt = False,  priority_prompt = True, hints = None):
    ''' Wrapper function for basic digit entry dialog

    Parameters:
        prompt - main prompt to be spoken
        help - main help message to be spoken
        min_length (Default=1) - minimum number of digits allowed
            Should generally not be set higher than 2 so operator gets feedback
        max_length (Default=10) - Maximum number of digits allowed
        confirm (Default=True) - Determine whether or not entered values
                                 should be confirmed by operator
        scan (Default=ScanMode.Off) - determines if scanning needs to be enabled
                  and the mode of scanning (Off, Single, Multiple)
                  True/False can also be passed in True = Single, False = Off
        additional_vocab (Default={}) - Dictionary of additional words and whether
                                        or not they should be confirmed
        skip_prompt (Default=False) - skips speaking main prompt when entering dialog
        priority_prompt (Default=True) - whether or not prompt is priority prompt
        hints (Default=None) - string or list of strings of likely responses to improve recognition
            enables Adaptive Recognition on words that have been included in embedded training prompts
            see Best Practices for Speech Recognition for more information

    returns: digits entered by operator and if scanning enabled, whether or not value was scanned
    '''
    executor = obj_factory.get(DigitsPromptExecutor,
                                    prompt=prompt,
                                    help_message=help,
                                    priority_prompt=priority_prompt,
                                    additional_vocab=additional_vocab,
                                    min_length=min_length,
                                    max_length=max_length,
                                    confirm=confirm,
                                    scan=scan,
                                    skip_prompt=skip_prompt,
                                    hints=hints)
    return executor.get_results()


def prompt_alpha_numeric(prompt, help, min_length=1, max_length=10, #@ReservedAssignment
                         confirm=True, scan=ScanMode.Off, additional_vocab = {},
                         priority_prompt = True, hints = None):
    ''' Wrapper function for alpha numeric entry
        Alpha characters must be added to the final project's voiceconfig.xml

    Parameters:
        prompt - main prompt to be spoken
        help - main help message to be spoken
        min_length (Default=1) - minimum number of digits allowed
            Should generally not be set higher than 2 so operator gets feedback
        max_length (Default=10) - Maximum number of digits allowed
        confirm (Default=True) - Determine whether or not entered values
                                 should be confirmed by operator
        scan (Default=ScanMode.Off) - determines if scanning needs to be enabled
                  and the mode of scanning (Off, Single, Multiple)
                  True/False can also be passed in True = Single, False = Off
        additional_vocab (Default={}) - Dictionary of additional words and whether
                                        or not they should be confirmed
        priority_prompt (Default=True) - whether or not prompt is priority prompt
        hints (Default=None) - string or list of strings of likely responses to improve recognition
            enables Adaptive Recognition on words that have been included in embedded training prompts
            see Best Practices for Speech Recognition for more information

    returns: value entered by operator and if scanning enabled, whether or not value was scanned
    '''
    executor = obj_factory.get(DigitsPromptExecutor,
                                    prompt=prompt,
                                    help_message=help,
                                    priority_prompt=priority_prompt,
                                    additional_vocab=additional_vocab,
                                    min_length=min_length,
                                    max_length=max_length,
                                    confirm=confirm,
                                    scan=scan,
                                    hints=hints,
                                    characters=ALPHA_NUMERIC)
    return executor.get_results()


def prompt_alpha(prompt, help, min_length=1, max_length=10, #@ReservedAssignment
                 confirm=True, additional_vocab = {},
                 priority_prompt = True, hints = None):
    ''' Wrapper function for alpha only
        Alpha characters must be added to the final project's voiceconfig.xml

    Parameters:
        prompt - main prompt to be spoken
        help - main help message to be spoken
        min_length (Default=1) - minimum number of digits allowed
            Should generally not be set higher than 2 so operator gets feedback
        max_length (Default=10) - Maximum number of digits allowed
        confirm (Default=True) - Determine whether or not entered values
                                 should be confirmed by operator
        additional_vocab (Default={}) - Dictionary of additional words and whether
                                        or not they should be confirmed
        priority_prompt (Default=True) - whether or not prompt is priority prompt
        hints (Default=None) - string or list of strings of likely responses to improve recognition
            enables Adaptive Recognition on words that have been included in embedded training prompts
            see Best Practices for Speech Recognition for more information

    returns: alphas entered by operator
    '''
    executor = obj_factory.get(DigitsPromptExecutor,
                                    prompt=prompt,
                                    help_message=help,
                                    priority_prompt=priority_prompt,
                                    additional_vocab=additional_vocab,
                                    min_length=min_length,
                                    max_length=max_length,
                                    confirm=confirm,
                                    hints=hints,
                                    characters=ALPHA)
    return executor.get_results()

def prompt_anchor(prompt, help, #@ReservedAssignment
                  anchor_words = ['ready'],
                  characters = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
                  confirm=True, scan=ScanMode.Off, additional_vocab = {},
                  priority_prompt = True,
                  hints = None):
    ''' Wrapper function for collecting values requiring an anchor word

    Parameters:
        prompt - main prompt to be spoken
        help - main help message to be spoken
        anchor_words (default - ready) - list of anchor words that may be spoken
        characters (default - all digits) - list of characters that can be spoken
            must exist in voiceconfig.xml
        confirm (Default=True) - Determine whether or not entered values
                                 should be confirmed by operator
        scan (Default=ScanMode.Off) - determines if scanning needs to be enabled
                  and the mode of scanning (Off, Single, Multiple)
                  True/False can also be passed in True = Single, False = Off
        additional_vocab (Default={}) - Dictionary of additional words and whether
                                        or not they should be confirmed
        priority_prompt (Default=True) - whether or not prompt is priority prompt
        hints (Default=None) - string or list of strings of likely responses to improve recognition
            enables Adaptive Recognition on words that have been included in embedded training prompts
            see Best Practices for Speech Recognition for more information

    returns: Digits/Characters spoken, anchor word used, and if scanning enabled,
             whether or not value was scanned by operator
    '''
    executor = obj_factory.get(DigitsPromptExecutor,
                                    prompt=prompt,
                                    help_message=help,
                                    priority_prompt=priority_prompt,
                                    additional_vocab=additional_vocab,
                                    confirm=confirm,
                                    scan=scan,
                                    hints=hints,
                                    characters=characters,
                                    anchor_words=anchor_words,
                                    min_length=None,
                                    max_length=100000)
    return executor.get_results()


def prompt_digits_required(prompt, help, required_value, #@ReservedAssignment
                           scan=None, additional_vocab = {},
                           skip_prompt = False, priority_prompt = True,
                           invalid_scan_key = None):
    ''' Wrapper function for required digit entry dialog

    Parameters:
        prompt - main prompt to be spoken
        help - main help message to be spoken
        required_value - single string or a list of digit strings a operator must speak
        scan (Default=None) - single string or a list of values that can be scanned
                              None if scanning not permitted
        additional_vocab (Default={}) - Dictionary of additional words and whether
                                        or not they should be confirmed
        skip_prompt (Default = False) - skips speaking main prompt when entering dialog
        priority_prompt (Default=True) - whether or not prompt is priority prompt
        invalid_scan_key (Default=None) - wrong scan key override if specified
                                          (with result as first parameter)

    returns: digits entered by operator if they match required values,
             and if scanning enabled, whether or not value was scanned
    '''
    executor = obj_factory.get(DigitsPromptExecutor,
                                    prompt=prompt,
                                    help_message=help,
                                    priority_prompt=priority_prompt,
                                    additional_vocab=additional_vocab,
                                    skip_prompt=skip_prompt,
                                    required_scanned_values=scan,
                                    required_spoken_values=required_value,
                                    scan=(scan != None),
                                    confirm=False,
                                    invalid_scan_key=invalid_scan_key)
    return executor.get_results()


def prompt_required(prompt, help, #@ReservedAssignment
                    required_value,
                    speakable_vocab,
                    scan=None, additional_vocab = {},
                    skip_prompt = False,
                    priority_prompt = True,
                    invalid_scan_key = None):
    ''' Wrapper function for basic required entry dialog

    Parameters:
        prompt - main prompt to be spoken
        help - main help message to be spoken
        required_value - single string or a list of strings a operator must speak
        speakable_vocab - list of utterances operator can speak. if individual
            characters, then a string can be passed in (i.e. '1234567890ABC')
            must exist as vocabulary in voiceconfig.xml
        scan (Default=None) - single string or a list of values that can be scanned
                              None if scanning not permitted
        additional_vocab (Default={}) - Dictionary of additional words and whether
                                        or not they should be confirmed
        skip_prompt (Default=False) - skips speaking main prompt when entering dialog
        priority_prompt (Default=True) - whether or not prompt is priority prompt
        invalid_scan_key (Default=None) - wrong scan key override if specified
                                          (with result as first parameter)

    returns: value entered by operator if they match required values,
             and if scanning enabled, whether or not value was scanned
    '''
    executor = obj_factory.get(DigitsPromptExecutor,
                                    prompt=prompt,
                                    help_message=help,
                                    priority_prompt=priority_prompt,
                                    additional_vocab=additional_vocab,
                                    skip_prompt=skip_prompt,
                                    required_scanned_values=scan,
                                    required_spoken_values=required_value,
                                    characters=speakable_vocab,
                                    scan=(scan != None),
                                    confirm=False)
    return executor.get_results()

#----------------------------------------------------------------------------
# Wrapper functions for FloatPrompt
#----------------------------------------------------------------------------
def prompt_float(prompt, help, decimal_places = 2, #@ReservedAssignment
                 confirm = True, scan = ScanMode.Off, additional_vocab = {},
                 skip_prompt = False, priority_prompt = True, hints = None,
                 min_value = '0.0', max_value = '9999.99'):
    ''' Wrapper function for basic floating point entry dialog
        The decimal point character specified in the FloatPrompt class
        must be added to the final project's voiceconfig.xml

    Parameters:
        prompt - main prompt to be spoken
        help - main help message to be spoken
        decimal_places (Default=2) - number of required digits after decimal place
            if 0, requires "ready" and will not time out
            if None, the min and max integer and decimal portion lengths
            will be calculated from min_value and max_value
        confirm (Default=True) - Determine whether or not entered values
                                 should be confirmed by operator
        scan (Default=ScanMode.Off) - determines if scanning needs to be enabled
                  and the mode of scanning (Off, Single, Multiple)
                  True/False can also be passed in True = Single, False = Off
        additional_vocab (Default={}) - Dictionary of additional words and whether
                                        or not they should be confirmed
        skip_prompt (Default=False) - skips speaking main prompt when entering dialog
        priority_prompt (Default=True) - whether or not prompt is priority prompt
        hints (Default=None) - string or list of strings of likely responses to improve recognition
            enables Adaptive Recognition on words that have been included in embedded training prompts
            from VoiceCatalyst 2.1.1 on, * can be used for wildcards to specify any value
            to allow '1.*' or ['1.*', '2.*'] for variable entries within a range
            see Best Practices for Speech Recognition for more information
        min_value (Default='0.0') - if specified, minimum valid value (see note)
        max_value (Default='9999.99') - if specified, maximum valid value (see note)

    Note: min_value and max_value will only be used to
        calculate discrete grammar if decimal_places is set to None,
        but will be enforced as the range of acceptable values.
        These must be string values, or None

    returns: float value, as a string, entered by operator,
        if anchor_words specified, the anchor used,
        and if scanning enabled, whether or not value was scanned
    '''
    executor = obj_factory.get(FloatPromptExecutor,
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

#----------------------------------------------------------------------------
# Wrapper functions for ListPrompt
#----------------------------------------------------------------------------
def prompt_list(list, prompt, help, additional_vocab = {}): #@ReservedAssignment
    ''' Wrapper function for basic single selection from list dialog

    Parameters:
        list - list of values in the form of [ [key_value, description], ...]
                 key_value must be a numeric string
        prompt - main prompt to be spoken
        help - main help message to be spoken
        additional_vocab (Default={}) - Dictionary of additional words and whether
                                        or not they should be confirmed

    returns: key_value that was selected
    '''
    executor = obj_factory.get(ListPromptExecutor,
                                    prompt=prompt,
                                    help_message=help,
                                    additional_vocab=additional_vocab,
                                    selection_list=list)
    return executor.get_results()

def prompt_list_lut(lut, key_field, description_field, prompt, help, #@ReservedAssignment
                    additional_vocab = {}):
    ''' Wrapper function for selecting a single record from a LUT

    Parameters:
        lut - Lut to select from
        key_field - Key ID field for selection, must be numeric values
        description_field - speakable description
        prompt - main prompt to be spoken
        help - main help message to be spoken
        additional_vocab (Default={}) - Dictionary of additional words and whether
                                        or not they should be confirmed

    returns: key_value that was selected
    '''
    executor = obj_factory.get(ListPromptExecutor,
                                    prompt=prompt,
                                    help_message=help,
                                    additional_vocab=additional_vocab,
                                    lut=lut,
                                    key_field=key_field,
                                    description_field=description_field)
    return executor.get_results()

def prompt_list_lut_auth(lut, key_field, description_field, prompt, help, #@ReservedAssignment
                    additional_vocab = {}):
    ''' Wrapper function for selecting a single record from a LUT

    Parameters:
        lut - Lut to select from
        key_field - Key ID field for selection, must be numeric values
        description_field - speakable description
        prompt - main prompt to be spoken
        help - main help message to be spoken
        additional_vocab (Default={}) - Dictionary of additional words and whether
                                        or not they should be confirmed

    returns: key_value that was selected
    '''
    executor = obj_factory.get(ListPromptExecutor,
                                    prompt=prompt,
                                    help_message=help,
                                    additional_vocab=additional_vocab,
                                    lut=lut,
                                    key_field=key_field,
                                    description_field=description_field)

    executor.dialog.invalid_key = 'generic.notauthorized'
    return executor.get_results()
