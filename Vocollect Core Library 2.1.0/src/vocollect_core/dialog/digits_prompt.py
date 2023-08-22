#
# Copyright (c) 2010-2011 Vocollect, Inc.
# Pittsburgh, PA 15235
# All rights reserved.
#
# This source code contains confidential information that is owned by
# Vocollect, Inc. and may not be copied, disclosed or otherwise used without
# the express written consent of Vocollect, Inc.
#
from vocollect_core.dialog.base_dialog import BaseDialog, BaseDialogExecutor
from vocollect_core import itext, class_factory
from vocollect_core.scanning import ScanMode, get_scan_result, set_scan_mode,\
    scan_results_exist, get_trigger_vocab
from vocollect_core.utilities import obj_factory
from vocollect_core.utilities.util_methods import multiple_hints_supported,\
    MULTIPLE_HINTS_VERSION, say_again_supported
import voice

#----------------------------------------------------------------------------
# Digits wrapper class
#----------------------------------------------------------------------------
class DigitsPrompt(class_factory.get(BaseDialog)):
    ''' Wrapper Class for basic digit entry dialog

        returns: Digits entered by operator
    '''

    def __init__(self, prompt, help, #@ReservedAssignment
                 min_length=1, max_length=10,
                 confirm=True, scan=False):
        ''' Constructor

        Parameters:
            prompt - main prompt to be spoken
            help - main help message to be spoken
            min_length (Default=1) - minimum number of digits allowed
            max_length (Default=10) - Maximum number of digits allowed
            confirm (Default=True) - Determine whether or not entered values
                                     should be confirmed by operator
            scan (Default=False) - determines if scanning needs to be enabled

        Additional properties
            confirm_prompt_key - resource key for confirmation prompt

        '''
        super().__init__('Digits')

        self.nodes['PromptHere'].prompt = prompt
        # NPP and NPPGS are always non-priority prompts when returning
        # to the prompt within a vid. NPPGS includes a grammar stop
        self.nodes['PromptHereNPP'].prompt = prompt
        self.nodes['PromptHereNPPGS'].prompt = prompt
        self.nodes['StartHere'].help_prompt = help

        # Turn off Speak ahead when processing enters the ConfirmPrompt node
        self.nodes['ConfirmPrompt'].is_allow_speak_ahead_node = False

        # Turn off Speak ahead when processing goes back to the StartHere node
        # because dialogs.result_less_than_min_length returned True
        # meaning the user started speaking but did not enter the minimum number
        # of digits before timing out.
        self.links['Link21'].is_allow_speak_ahead_link = False
        # Turn off Speak ahead on non-priority wrong prompt
        self.nodes['InvalidPrompt'].is_allow_speak_ahead_node = False
        # Turn off Speak ahead when returning to the main prompt via vocabulary
        self.nodes['PromptHereNPPGS'].is_allow_speak_ahead_node = False

        self.help = help

        self.min_length = min_length
        self.max_length = max_length
        self.confirm = confirm
        self.scan_mode = ScanMode.convert_mode(scan)

        #properties for expected values
        self.expected = None
        self.expected_scans = None
        self.is_expected_required = False
        self.invalid_key = 'generic.wrongValue.prompt'
        self.invalid_scan_key = None
        self.invalid_count_max = 2
        self.invalid_count_curr = 0

        # As a guideline, entries over 6 digits are cumbersome to speak
        # and should be avoided.  Scanning or partial entries validated by the host
        # should be considered for these situations.  Alternately,
        # consider setting max_length to None which will allow the operator
        # to pause and resume entry.
        self.max_discrete_length = 6

        # calculated values after dialog is configured, before setting discrete grammar
        self._calc_digit_vocab = None
        self._calc_anchor_vocab = None
        self._calc_help_prompt = None

        self._last_node = None
        self.is_scanned = False
        self.anchor_result = None
        self.include_anchor = False

        self.configure_scanning()
        self._final_configuration()

    def _get_prompt(self):
        '''
            return the current prompt. Override in classes that store the prompt
            in a different node.
        '''
        if 'PromptHere' in self.nodes:
            return self.nodes['PromptHere'].prompt
        else:
            return None

    def set_help(self, additional = []):
        ''' set help includes the additional vocabulary to the help

        Parameters:
            additional - Single word, list of words, or dictionary of words.
        '''
        help_msg = self.nodes['StartHere'].help_prompt
        vocab = list(self.additional_vocab.keys())
        if vocab is None:
            vocab = []

        vocab.extend(additional)

        if (len(vocab)) == 1:
            if not vocab[0] in help_msg:
                help_msg = help_msg + ' '+itext('generic.help.dynamic.single', vocab[0])
        elif (len(vocab)) > 1:
            vocabhelp = ''
            for index in range(len(vocab)-1):
                vocabhelp = vocabhelp + str(vocab[index]) + ', '
            if not vocabhelp in help_msg:
                help_msg = help_msg + ' '+ itext('generic.help.dynamic.multiple', vocabhelp, vocab[(len(vocab)-1)])

        self.nodes['StartHere'].help_prompt = help_msg

        # To address RBIRD-255, initialize the help for Digits node to be the same as StartHere
        # if the dialog requires an anchor, set_result will override the help
        for node in self.nodes.keys() & ({'Digits'} | {'Discrete' + str(i) for i in range(1, self.max_discrete_length + 1)}):
            self.nodes[node].help_prompt = help_msg

    def set_required(self, expected, expected_scan_values = None):
        ''' configures digits VID to expect a specific value. This will also
            set the min and max digits to enter based on expected values
            and recheck if discrete grammar can be used

        Parameters:
            expected - List of expected items or single string
            expected_scan_values - List of expected values for scanning or single string

        Note:  This function expects at least one expected value.  If an
               empty string is passed (or a list of empty strings) then
               the voice dialog will still require "ready" to be spoken
               otherwise the value must be entered via barcode scanning.
        Note:  This should not be called if discrete grammar has already been set
               (for instance during __init__) to a max_length < 6
        '''

        if isinstance(expected, str):
            expected = [expected]
        if isinstance(expected_scan_values, str):
            expected_scan_values = [expected_scan_values]
        self.expected = []
        self.expected.extend(expected)
        self.max_length = 0
        self.min_length = 1000000

        for item in expected:
            if len(str(item)) > self.max_length:
                self.max_length = len(str(item))
            if len(str(item)) < self.min_length:
                self.min_length = len(str(item))

        if self.max_length == 0:
            # all expected values are empty - set max_length to a large
            # number so all voice input will be ignored except for anchor words
            self.max_length = 1000000

        if self.min_length == 0:
            self.min_length = self.max_length

        self.expected_scans = []
        if expected_scan_values is not None:
            self.expected_scans.extend(expected_scan_values)

        self.is_expected_required = True
        self.set_hints(expected)

    def set_hints(self, hints):
        ''' Adds hints to dialog to help improve recognition '''
        all_hints = []
        if isinstance(hints, str):
            hints = [hints]
        elif not isinstance(hints, (list, set)):
            voice.log_message('DIGITS PROMPT: hints expected list or string, received ' + str(type(hints)) + ': ' + str(hints))
            return

        if multiple_hints_supported():
            for hint in hints:
                if hint is not None:
                    if hint not in all_hints and len(hint) > 1:
                        all_hints.append(hint)
                    if (not self.include_anchor and len(hint) > 0
                        and (self.max_length is None or self.max_length <= 0
                             or len(hint) < self.max_length)):
                        # add ready if not doing anchor words
                        # and no max length or hint less than max length
                        hint_ready = hint + 'ready'
                        if hint_ready not in all_hints:
                            all_hints.append(hint_ready)
        else:
            # Only use first hint for versions of VoiceCatalyst earlier than 2.0
            for hint in hints:
                if hint is not None and len(hint) > 1:
                    all_hints.append(hint)
                    break

            # log warning if multiple hints given
            if len(hints) > 1:
                voice.log_message('DIGITS PROMPT: Multiple hints provided, but multiple hints not supported until version '
                                  + str(MULTIPLE_HINTS_VERSION)
                                  + ' or greater. Hint set to ' + str(all_hints))

        self.nodes['StartHere'].response_expression = all_hints

    def set_additional_vocab(self, additional_vocab):
        ''' adds additional vocab user may speak at main prompt '''
        BaseDialog.set_additional_vocab(self, additional_vocab)
        self._remove_existing_vocab('StartHere')
        # inherent truth/falsehood of [un]populated sequences
        if self.additional_vocab:
            # bypass additional digit links and validity check
            self.nodes['AdditionalVocabResult'] = voice.Node('AdditionalVocabResult',
                                                             on_entry_method = 'dialogs.set_result')
            self.nodes['AdditionalVocabResult'].dialog = self
            self.links['AdditionalVocab'] = voice.Link('AdditionalVocab',
                                                       self.nodes['StartHere'],
                                                       self.nodes['AdditionalVocabResult'],
                                                       self.additional_vocab.keys())
            self.links['AdditionalVocabDefault'] = voice.Link('AdditionalVocabDefault',
                                                              self.nodes['AdditionalVocabResult'],
                                                              self.nodes['CheckConfirm'])
        if (say_again_supported()
            and 'say again' not in self.additional_vocab
            and 'say again' in voice.get_all_vocabulary_from_vad()):
            # if say again is not specified in additional_vocab,
            # add an explicit link to the non-priority prompt with a grammar stop
            self.links['SayAgainLink'] = voice.Link('SayAgainLink',
                                                    self.nodes['StartHere'],
                                                    self.nodes['PromptHereNPPGS'],
                                                    ['say again'])

    def add_additional_digits(self, digits):
        ''' Add additional characters such as alphas to main links
            Must be set prior to configuring grammar
            Warning:  These are set directly on the link's vocab
                and must exist in voiceconfig.xml

        Parameters:
            digits - List of digits to add to links for user to speak
        '''
        self.links['FirstDigit'].vocab |= set(digits)
        self.links['AdditionalDigits'].vocab |= set(digits)

    def remove_digits(self, digits):
        ''' Remove characters from main links
            Must be configured prior to setting discrete grammar
            Warning: At least one vocabulary word must remain on the link

        Parameters:
            digits - List of digits to remove from links
        '''
        self.links['FirstDigit'].vocab -= set(digits)
        self.links['AdditionalDigits'].vocab -= set(digits)

    def set_anchors(self, anchor_words):
        ''' Configures the available anchor words
            Must be configured prior to setting discrete grammar
        '''
        orig = self.links['Link22'].vocab
        # add all new anchor words
        self.links['Link22'].vocab |= set(anchor_words)
        # remove original vocab (ready) if it is not supposed to be an anchor word
        self.links['Link22'].vocab -= (orig - set(anchor_words))
        self.include_anchor = True

    def configure_scanning(self):
        ''' Adds some additional nodes and links if a trigger_scan_vocab is set
            and scanning is on. Otherwise does nothing
        '''
        #Only create if scanning and trigger scan is valid vocab word
        if self.scan_mode != ScanMode.Off and get_trigger_vocab() != "":
            # add node to trigger a scan
            self.nodes['TriggerScan'] = voice.Node('TriggerScan',
                                                  '', '', False,
                                                  'dialogs.trigger_scan')
            # prevent infinite grammar loop
            self.nodes['TriggerScan'].is_allow_speak_ahead_node = False

            # add vocab link to go to trigger scan node
            self.links['LinkToTriggerScan'] = voice.Link('LinkToTriggerScan',
                                                         self.nodes['StartHere'],
                                                         self.nodes['TriggerScan'],
                                                         [get_trigger_vocab()])

            # add default link to return to StartHere
            self.links['LinkFromTriggerScan'] = voice.Link('LinkFromTriggerScan',
                                                           self.nodes['TriggerScan'],
                                                           self.nodes['StartHere'],
                                                           [])

    def configure_grammar(self):
        ''' checks if the dialog can utilize discrete grammar
            If so, creates nodes and links if necessary
            If max length is None or 0, adds a cancel link
        '''
        # save previously-configured digit vocab, anchor vocab, and help prompt
        self._calc_digit_vocab = self.links['AdditionalDigits'].vocab
        self._calc_anchor_vocab = None
        if 'Link22' in self.links:
            # ListPrompt does not have an anchor link
            self._calc_anchor_vocab = self.links['Link22'].vocab
        self._calc_help_prompt = self.nodes['StartHere'].help_prompt

        if self.max_length is None or self.max_length <= 0:
            if 'cancel' in voice.get_all_vocabulary_from_vad():
                self.links['link_cancel'] = voice.Link('link_cancel',
                                                       self.nodes['Digits'],
                                                       self.nodes['PromptHereNPPGS'],
                                                       existing_vocab = ['cancel'])
        elif self.max_length <= self.max_discrete_length:
            self.set_discrete_grammar()

    def set_discrete_grammar(self):
        ''' Creates discrete nodes and links according to max_length
            Note: the names are one-based due to the existing 'FirstDigit' link
        '''
        # Build the discrete nodes
        for i in range(self.max_length):
            node_name = 'Discrete' + str(i + 1)
            self.nodes[node_name] = voice.Node(node_name, help_prompt = self._calc_help_prompt,
                                               on_entry_method = 'dialogs.set_result')
            self.nodes[node_name].dialog = self

        # capture anchor word
        if self._calc_anchor_vocab is not None:
            self.nodes['DiscreteAnchor'] = voice.Node('DiscreteAnchor',
                                                      on_entry_method = 'dialogs.set_anchor_result')
            self.nodes['DiscreteAnchor'].dialog = self
            self.links['DigitAnchorDefault'] = voice.Link('DigitAnchorDefault',
                                                          self.nodes['DiscreteAnchor'],
                                                          self.nodes['CheckDigitsConfirm'])

        # re-route FirstDigit vocabulary link to first discrete node
        self._move_link('FirstDigit', 'StartHere', 'Discrete1')

        # remove existing looped digit links
        for link in self.links.keys() & {'Link22',  # anchor vocab, Digits to CheckDigitsConfirm
                                         'Link10',  # timeout, Digits to CheckDigitsConfirm
                                         'Link48',  # scan, Digits to CheckScannedValue
                                         'AdditionalDigits',
                                         'Link8',   # MoreDigits to Digits
                                         'Link29'}: # Initialize to Digits
            self._remove_link(link)

        # remove existing looped digit nodes
        for node in ['Digits', 'Initialize', 'MoreDigits']:
            del self.nodes[node]

        # add links to newly created nodes

        # create vocabulary and conditional links from discrete nodes
        for i in range(self.max_length - 1):
            self.set_additional_discrete_links(i)
        # create links from final discrete node
        self.set_final_digit_discrete_links(self.max_length - 1)

    def set_additional_discrete_links(self, index, execution_order = 1):
        ''' for each non-final discrete node, create digit links,
            anchor links if any anchor words,
            barcode links if scanning enabled, and timeout links
            index - zero-based index for one-based node and link names
            execution_order (Default=1) - starting execution order for
                one-based conditional link order of execution

            returns the next execution order available for use
        '''

        index_name = str(index + 1)
        next_name = str(index + 2)
        source_name = 'Discrete' + index_name

        # digit link - the 'FirstDigit' link is re-used, so start numbering at 'Digit2'
        link_name = 'Digit' + next_name
        self.links[link_name] = voice.Link(link_name,
                                           self.nodes[source_name],
                                           self.nodes['Discrete' + next_name],
                                           existing_vocab = self._calc_digit_vocab)
        # anchor link
        if self._calc_anchor_vocab is not None:
            link_name = 'Anchor' + index_name
            self.links[link_name] = voice.Link(link_name,
                                               self.nodes[source_name],
                                               self.nodes['DiscreteAnchor'],
                                               existing_vocab = self._calc_anchor_vocab)
        # barcode link
        if hasattr(self, 'scan_mode') and self.scan_mode != ScanMode.Off:
            # StartHere has a barcode link, use 'Barcode2'
            link_name = 'Barcode' + next_name
            self.links[link_name] = voice.Link(link_name,
                                               self.nodes[source_name],
                                               self.nodes['CheckScannedValue'],
                                               conditional_method = 'dialogs.is_barcode_scanned')
            self.links[link_name].execution_order = execution_order
            execution_order += 1
        # timeout link
        link_name = 'Timeout' + index_name
        self.links[link_name] = voice.Link(link_name,
                                           self.nodes[source_name],
                                           self.nodes['CheckDigitsConfirm'],
                                           conditional_method = 'dialogs.timeout_digit_entry')
        self.links[link_name].execution_order = execution_order
        return execution_order + 1

    def set_final_digit_discrete_links(self, index, execution_order = 1):
        ''' Create links from the final discrete node
            index - zero-based index for one-based node and link names
            execution_order (Default=1) - starting execution order for
                one-based conditional link order of execution

            returns the next execution order available for use
        '''
        self.links['DigitDefault'] = voice.Link('DigitDefault',
                                                self.nodes['Discrete' + str(index + 1)],
                                                self.nodes['CheckDigitsConfirm'])
        return execution_order

    def prompt_here(self):
        ''' code to execute when main prompt is entered '''
        super().prompt_here()
        self.invalid_count_curr = 0

    def set_scan_callback(self):
        ''' sets the scan call back
        '''
        self.anchor_result = None
        self._last_node = None
        try:
            if 'Digits' in self.nodes.keys():
                self.nodes['Digits'].last_recog = None
            set_scan_mode(self.scan_mode)
        except:
            self.result = None

    def set_result(self):
        ''' sets result value to the digits collected so far'''
        if self.result is None:
            self.result = self.nodes['StartHere'].last_recog
            # update help if operator is required to speak ready to complete entry
            if self.max_length is None or self.max_length <= 0:
                self._update_help()
        else:
            if self._last_node.name in ['MoreDigits', 'Initialize']:
                # within loop link - last node will be Initialize after first AdditionalDigit link
                self.result += self.nodes['Digits'].last_recog
                # update help if operator is required to speak ready to complete entry
                if self.max_length is None or self.max_length <= 0:
                    self._update_help()
            else:
                # discrete grammar
                self.result += self._last_node.last_recog
        self._last_node = self.current_node

    def _update_help(self, *node_names):
        ''' Updates the help message to include the value spoken so far
            when ready is required to complete entry
            only updates help at Digits node
            unless one or more node_names are specified
        '''
        help_key = 'generic.digits.help'
        if 'cancel' in voice.get_all_vocabulary_from_vad():
            help_key = 'generic.digits.help.cancel'
        help_msg = itext(help_key, self.result)
        # inherent truth/falsehood of [un]populated sequences
        if node_names:
            for node_name in node_names:
                self.nodes[node_name].help_prompt = help_msg
        else:
            self.nodes['Digits'].help_prompt = help_msg

    def set_anchor_result(self):
        ''' Sets the anchor if spoken '''
        if (self.current_node.name == 'CheckDigitsConfirm'
            and 'Digits' in self.nodes.keys()
            and self.nodes['Digits'].last_recog in self.links['Link22'].vocab):
            # vocabulary in a node's out_links must be unique
            self.anchor_result = self.nodes['Digits'].last_recog
        elif self.current_node.name == 'DiscreteAnchor':
            self.anchor_result = self.nodes['Discrete' + str(len(self.result))].last_recog

    def timeout_digit_entry(self):
        ''' Function to determine if timeout occurred or
            maximum number of digits entered

        returns: True if timeout exceeded or maximum number of
            digits entered, otherwise False
        '''
        if self.max_length is None or self.max_length <= 0:
            # Invalid or no max length, require anchor word
            return False
        elif self.is_timedout(self.current_node.name):
            return True
        else:
            return len(self.result) >= self.max_length

    def invalid_count_check(self):
        ''' check how many times an invalid entry was done since main prompt '''
        self.invalid_count_curr += 1
        return self.invalid_count_curr < self.invalid_count_max

    def is_valid_value(self):
        ''' check if expected value is required '''

        #check if required and result matches expected
        invalid_key = None
        if self.is_expected_required:
            # check expected scanned
            if self.is_scanned and self.result not in self.expected_scans:
                invalid_key = self.invalid_key
            # check expected spoken
            elif not self.is_scanned and self.result not in self.expected:
                invalid_key = self.invalid_key

            if invalid_key is not None:
                if not set(self.result).issubset(set('0123456789')):
                    invalid_key = 'generic.spell.wrongValue.prompt'
                if self.is_scanned and self.invalid_scan_key is not None:
                    invalid_key = self.invalid_scan_key

                #not a valid entry
                self.nodes['InvalidPrompt'].prompt = itext(invalid_key, self.result)
                self.is_scanned = False
        return invalid_key is None

    def result_less_than_min_length(self):
        ''' Function called from dialog to see if user entered
            at least the minimum number of digits

        returns: True if minimum entered, otherwise False
        '''
        #if no min length, then check if anchor word was spoken or maximum was reached
        if self.min_length is None:
            return self.anchor_result is None and len(self.result) < self.max_length
        return len(self.result) < self.min_length

    def scanned_result(self):
        ''' set the scan result from global scan
        '''
        if scan_results_exist():
            self.result = get_scan_result()
            self.is_scanned = True
            return True

        return False

    def http_post(self, post_value):
        ''' check and set result and http_post to true '''
        self.result = post_value
        self._http_posted = True

    def http_get(self):

        self.http_get_template()

        prompt = self.nodes['PromptHere'].prompt
        form = self.form_template.replace("${prompt}", prompt)
        form = form.replace("${help}", self.help)
        form = form.replace("${otherActions}", self.http_other_actions_form())

        return form

    def confirm_prompt(self):
        if self.should_confirm():
            if self.include_anchor and self.result not in self.additional_vocab and self.anchor_result is not None:
                key = 'generic.correct.anchor.confirm'
                self.nodes['ConfirmPrompt'].prompt = itext(key, self.result, self.anchor_result)
                return True
            else:
                return super().confirm_prompt()

        return False

    def run(self):
        ''' Override BaseDialog to turn off scanner on error or ScanMode.Single
        '''
        ret_value = None
        self.configure_grammar()

        try:
            ret_value = super().run()
        except Exception as err:
            set_scan_mode(ScanMode.Off)
            raise err

        finally:
            # Clean up - turn off scanning if mode is not multiple scanning
            if hasattr(self, 'scan_mode'):
                if (self.scan_mode == ScanMode.Single):
                    set_scan_mode(ScanMode.Off)

        return ret_value


#----------------------------------------------------------------------------
# Helper Class used for executing dialogs
#----------------------------------------------------------------------------
class DigitsPromptExecutor(BaseDialogExecutor):

    def __init__(self,
                 prompt,
                 priority_prompt = True,
                 help_message = None,
                 additional_vocab = {},
                 min_length=1,
                 max_length=10,
                 confirm=True,
                 scan=ScanMode.Off,
                 skip_prompt = False,
                 characters = None,
                 required_spoken_values = None,
                 required_scanned_values = None,
                 anchor_words = None,
                 hints = None,
                 invalid_scan_key = None):
        ''' Base helper class for creating, configuring, and executing a digits dialog
            this classes are intended to make it easier for end users to configure
            dialogs beyond the basic function provided
        '''
        super().__init__(prompt=prompt,
                         help_message=help_message,
                         priority_prompt=priority_prompt,
                         additional_vocab=additional_vocab,
                         skip_prompt=skip_prompt)

        # Additional configuration properties
        self.min_length = min_length
        self.max_length = max_length
        self.confirm = confirm
        self.scan_mode = ScanMode.convert_mode(scan)
        self.characters = characters
        self.required_spoken_values = required_spoken_values
        self.required_scanned_values = required_scanned_values
        self.anchor_words = anchor_words
        self.hints = hints
        self.invalid_scan_key = invalid_scan_key

        # additional result variables
        self.scanned = None
        self.anchor_result = None

    def _create_dialog(self):
        ''' Creates a dialog object and saves it to the dialog member variable.
            This method is not intended to be called directly. Retrieve
            the class's dialog property to get the instance of the dialog.
        '''
        self._dialog = obj_factory.get(DigitsPrompt,
                                       self.prompt,
                                       self.help_message,
                                       self.min_length,
                                       self.max_length,
                                       self.confirm,
                                       self.scan_mode)

    def _configure_dialog(self):
        ''' Configures dialog object based on additional settings
            This method is not intended to be called directly. Retrieve
            the class's dialog property to get the instance of the dialog.
        '''
        #add additional vocab to dialog and set skip prompt property
        self.dialog.set_additional_vocab(self.additional_vocab)
        self.dialog.skip_prompt = self.skip_prompt
        self.dialog.nodes['PromptHere'].prompt_is_priority = self.priority_prompt
        if not self.priority_prompt: # scanner already triggered so do not scan again
            self.dialog.trigger_scan = False
        self.dialog.invalid_scan_key = self.invalid_scan_key

        #change the speakable digits if new list is provided
        if self.characters is not None:
            self.dialog.add_additional_digits(self.characters)
            self.dialog.remove_digits(
                {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'} - set(self.characters))

        #change terminate word 'ready' to other anchor words
        if self.anchor_words is not None:
            self.dialog.set_anchors(self.anchor_words)

        #add required values if provided, this will also set hints to required spoken values
        if self.required_spoken_values is not None:
            self.dialog.set_required(self.required_spoken_values,
                                     self.required_scanned_values)

        #Add hints to dialog if provided
        if self.hints is not None:
            self.dialog.set_hints(self.hints)

    def check_scanning_result(self):
        ''' Method initializes scanning if necessary and checks if there may
            already be a result from scanning before even launching the dialog;
            this would usually only occur when doing multiple scanning

            returns: True if scan result exists, otherwise False
        '''
        # if required scanned values are provided, then dialog must be used,
        # otherwise initialize scanning and see if result exists before entering dialog
        if (self.scan_mode != ScanMode.Off
            and self.required_scanned_values is None
            and not self.priority_prompt):
            #Check for existing result, if found return it
            if scan_results_exist():
                self.result = get_scan_result()
                self.scanned = True
        if self.result is None and self.scan_mode != ScanMode.Off:
            # begin the process of turning on the scanner before entering dialog
            # to compensate for a delay in powering on
            set_scan_mode(self.scan_mode)
        return self.result is not None

    def execute_dialog(self):
        ''' Executes the dialog
        '''
        if not self.check_scanning_result():
            #No scan result yet so launch dialog
            self.result = self.dialog.run()

            #get additional results
            self.scanned = self.dialog.is_scanned

            #get anchor_used
            self.anchor_result = None
            if (self.dialog.include_anchor is not None
                and not self.dialog.is_scanned
                and set(self.result).issubset(self.dialog.links['FirstDigit'].vocab)):
                self.anchor_result = self.dialog.anchor_result

    def get_results(self):
        ''' Gets the results of the dialog
            Will execute the dialog if it has not already been executed

        returns:
            if anchor words and scanning used then tuple(result, anchor_word, scanned)
            else if anchor words then tuple(result, anchor_word)
            else if scanning then tuple(result, scanned)
            else result
        '''
        if self.result is None: # Dialog has not been executed yet
            self.execute_dialog()

        # If anchor words provided
        if self.anchor_words is not None:
            if self.scan_mode != ScanMode.Off:
                return self.result, self.anchor_result, self.scanned
            else:
                return self.result, self.anchor_result
        # standard returns
        else:
            if self.scan_mode != ScanMode.Off:
                return self.result, self.scanned
            else:
                return self.result
