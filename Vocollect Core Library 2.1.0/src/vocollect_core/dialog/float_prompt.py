#
# Copyright (c) 2010-2011 Vocollect, Inc.
# Pittsburgh, PA 15235
# All rights reserved.
#
# This source code contains confidential information that is owned by
# Vocollect, Inc. and may not be copied, disclosed or otherwise used without
# the express written consent of Vocollect, Inc.
#

from vocollect_core.dialog.digits_prompt import DigitsPrompt, DigitsPromptExecutor
from vocollect_core import itext, class_factory
from vocollect_core.scanning import ScanMode
from vocollect_core.utilities import obj_factory
from decimal import Decimal
import voice

#----------------------------------------------------------------------------
# Float Dialog class
#----------------------------------------------------------------------------
class FloatPrompt(class_factory.get(DigitsPrompt)):
    ''' Wrapper Class for basic numeric float entry dialog

    returns: a float value entered by operator
    '''

    def __init__(self, prompt, help, #@ReservedAssignment
                 decimal_places = 2,  confirm = True, scan = ScanMode.Off,
                 min_value = '0.0', max_value = '9999.99'):
        ''' Constructor

        Parameters:
            prompt - main prompt to be spoken
            help - main help message to be spoken
            decimal_places (Default=2) - number of digits user speaks after decimal place
                if 0, requires "ready" and will not time out
                if None, the min and max integer and decimal portion lengths
                will be calculated from min_value and max_value
            confirm (Default=True) - Determine whether or not entered values
                                     should be confirmed by operator
            scan (Default=ScanMode.Off) - determines if scanning needs to be enabled
            min_value (Default='0.0') - if specified, minimum valid value (see note)
            max_value (Default='9999.99') - if specified, maximum valid value (see note)

            Note: min_value and max_value will only be used to
                calculate discrete grammar if decimal_places is set to None,
                but will be enforced as the range of acceptable values.
                If decimal_point_char is customized,
                these must be string values, use decimal_point_char as the decimal point,
                and be valid literals for Decimal after replacing decimal_point_char
                with the Python decimal point character '.'
        '''

        super().__init__(prompt, help, confirm = confirm, scan = scan)
        self._decimal_places = decimal_places
        self._min_value = min_value
        self._max_value = max_value
        self.invalid_key = 'generic.not.valid.float.value'
        # min_value and max_value must use the same character
        self.decimal_point_char = '.'
        # used by result_less_than_min_length
        self.min_feedback_length = 2
        # min and max integer and decimal portions of entry
        # this reuses max_discrete_length, min_length, and max_length
        # for the integer portion to utilize DigitsPrompt's set_discrete_grammar
        self.max_discrete_decimal_length = 6
        self.min_decimal_length = None
        self.max_decimal_length = None

        self._final_configuration()

    def set_lengths_from_values(self):
        ''' Sets min_length, max_length, min_decimal_length, max_decimal_length
            from min_value and max_value if decimal_places is None
        '''
        if self._decimal_places is None:
            # ensure logical ordering
            if self._min_value is not None and self._max_value is not None:
                if self.to_decimal(self._min_value) > self.to_decimal(self._max_value):
                    voice.log_message('FLOAT PROMPT: Opposite ordering of values ('
                                      + self._min_value + ' > ' + self._max_value + '), adjusting')
                    self._min_value, self._max_value = self._max_value, self._min_value

            min_split = [None, None] if self._min_value is None else self._min_value.split(self.decimal_point_char)
            if len(min_split) == 1:
                # integer only portion
                min_split.append(None)
            max_split = [None, None] if self._max_value is None else self._max_value.split(self.decimal_point_char)
            if len(max_split) == 1:
                max_split.append(None)
            self.min_length = None if min_split[0] is None else len(min_split[0])
            self.max_length = None if max_split[0] is None else len(max_split[0])
            self.min_decimal_length = None if min_split[1] is None else len(min_split[1])
            self.max_decimal_length = None if max_split[1] is None else len(max_split[1])
        else:
            # decimal places were specified:
            # unbound integer entry, exact number of decimal places
            self.max_length = 10000
            self.min_decimal_length = self._decimal_places
            self.max_decimal_length = self._decimal_places

        # swap lengths if necessary, i.e. 00.00 and 9.9
        # though result >= 9.9 will never be valid, assume "00.00" was intentional
        if self.min_length is not None and self.max_length is not None:
            if self.min_length > self.max_length:
                self.min_length, self.max_length = self.max_length, self.min_length
        if self.min_decimal_length is not None and self.max_decimal_length is not None:
            if self.min_decimal_length > self.max_decimal_length:
                self.min_decimal_length, self.max_decimal_length = self.max_decimal_length, self.min_decimal_length


    def configure_grammar(self):
        ''' checks if the dialog can utilize discrete grammar
            If so, creates nodes and links if necessary
            If max_decimal_length is None or 0, adds a cancel link
        '''

        # save previously-configured digit vocab, anchor vocab, and help prompt
        self._calc_digit_vocab = self.links['AdditionalDigits'].vocab
        self._calc_anchor_vocab = None
        if 'Link22' in self.links:
            # ListPrompt does not have an anchor link
            self._calc_anchor_vocab = self.links['Link22'].vocab
        self._calc_help_prompt = self.nodes['StartHere'].help_prompt

        # create node for decimal point vocab
        self.nodes['DecimalVocab'] = voice.Node('DecimalVocab', on_entry_method = 'dialogs.set_decimal_point')
        self.nodes['DecimalVocab'].dialog = self

        # check integer portion
        if self.max_length is not None and self.max_length > 0 and self.max_length <= self.max_discrete_length:
            # decimal point char added in set_additional_discrete_links
            self.set_discrete_grammar()
        else:
            self.links['DecimalVocabLink'] = voice.Link('DecimalVocabLink',
                                                        self.nodes['Digits'],
                                                        self.nodes['DecimalVocab'],
                                                        existing_vocab = self.decimal_point_char)

        # determine if the dialog needs to wait for ready
        unbound_decimal_length = self.max_decimal_length is None or self.max_decimal_length <= 0
        if (unbound_decimal_length and not
            (self.max_length is not None and self.max_length > 0 and self.max_length <= self.max_discrete_length)):
            # cancel will get added in set_additional_discrete_links
            if 'cancel' in voice.get_all_vocabulary_from_vad():
                self.links['link_cancel'] = voice.Link('link_cancel',
                                                       self.nodes['Digits'],
                                                       self.nodes['PromptHereNPPGS'],
                                                       existing_vocab = ['cancel'])
        # check decimal portion to set grammar
        if unbound_decimal_length:
            self.set_decimal_loop_link()
            if 'cancel' in voice.get_all_vocabulary_from_vad():
                self.links['link_decimal_cancel'] = voice.Link('link_decimal_cancel',
                                                               self.nodes['Decimals'],
                                                               self.nodes['PromptHereNPPGS'],
                                                               ['cancel'])
        elif self.max_decimal_length > self.max_discrete_decimal_length:
            self.set_decimal_loop_link()
        else:
            self.set_discrete_decimal_grammar()

    def set_additional_discrete_links(self, index, execution_order = 1):
        ''' for each non-final discrete integer node,
            create digit links, decimal vocab link,
            anchor links if any anchor words,
            barcode links if scanning enabled, and timeout links
            index - zero-based index for one-based node and link names
            execution_order (Default=1) - starting execution order for
                one-based conditional link order of execution

            returns the next execution order available for use
        '''
        # decimal vocab link
        index_name = str(index + 1)
        link_name = 'DecimalVocab' + index_name
        self.links[link_name] = voice.Link(link_name,
                                           self.nodes['Discrete' + index_name],
                                           self.nodes['DecimalVocab'],
                                           existing_vocab = [self.decimal_point_char])
        # non-timeout is configured by decimal_places = 0 regardless of integer length
        if self._decimal_places == 0:
            link_name = 'Cancel' + index_name
            self.links[link_name] = voice.Link(link_name,
                                               self.nodes['Discrete' + index_name],
                                               self.nodes['PromptHereNPPGS'],
                                               existing_vocab = ['cancel'])
        return super().set_additional_discrete_links(index, execution_order)

    def set_final_digit_discrete_links(self, index, execution_order = 1):
        ''' Create links from the final discrete integer node
            index - zero-based index for one-based node and link names
            execution_order (Default=1) - starting execution order for
                one-based conditional link order of execution

            returns the next execution order available for use
        '''
        # for FloatPrompt, this is similar to other discrete integer node's links

        # decimal vocab link
        index_name = str(index + 1)
        source_name = 'Discrete' + index_name

        link_name = 'DecimalVocab' + index_name
        self.links[link_name] = voice.Link(link_name,
                                           self.nodes[source_name],
                                           self.nodes['DecimalVocab'],
                                           existing_vocab = [self.decimal_point_char])
        # non-timeout is configured by decimal_places = 0 regardless of integer length
        if self._decimal_places == 0:
            link_name = 'Cancel' + index_name
            self.links[link_name] = voice.Link(link_name,
                                               self.nodes[source_name],
                                               self.nodes['PromptHereNPPGS'],
                                               existing_vocab = ['cancel'])
        if self._calc_anchor_vocab is not None:
            # anchor link
            link_name = 'Anchor' + index_name
            self.links[link_name] = voice.Link(link_name,
                                               self.nodes[source_name],
                                               self.nodes['DiscreteAnchor'],
                                               existing_vocab = self._calc_anchor_vocab)
        # barcode link
        if hasattr(self, 'scan_mode') and self.scan_mode != ScanMode.Off:
            # StartHere has a barcode link, use 'Barcode2'
            link_name = 'Barcode' + str(index + 2)
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

    def set_discrete_decimal_grammar(self):
        ''' checks if the decimal portion of the dialog can utilize discrete grammar
            and creates nodes and links as necessary
            Note: the names are one-based due to the existing 'FirstDigit' link
        '''
        # Build the discrete nodes
        for i in range(self.max_decimal_length):
            node_name = 'Decimal' + str(i + 1)
            self.nodes[node_name] = voice.Node(node_name, help_prompt = self._calc_help_prompt,
                                               on_entry_method = "dialogs.set_result")
            self.nodes[node_name].dialog = self

        if self._calc_anchor_vocab is not None:
            self.nodes['DecimalDiscreteAnchor'] = voice.Node('DecimalDiscreteAnchor',
                                                             on_entry_method = 'dialogs.set_anchor_result')
            self.nodes['DecimalDiscreteAnchor'].dialog = self
            self.links['DecDiscreteAnchorDefault'] = voice.Link('DecDiscreteAnchorDefault',
                                                                self.nodes['DecimalDiscreteAnchor'],
                                                                self.nodes['CheckDigitsConfirm'])

        # initial decimal digit link, anchor, barcode, and timeout
        self.links['FirstDecimal'] = voice.Link('FirstDecimal',
                                                self.nodes['DecimalVocab'],
                                                self.nodes['Decimal1'],
                                                existing_vocab = self._calc_digit_vocab)
        if self._calc_anchor_vocab is not None:
            self.links['DecVocabAnchor'] = voice.Link('DecVocabAnchor',
                                                      self.nodes['DecimalVocab'],
                                                      self.nodes['DecimalDiscreteAnchor'],
                                                      existing_vocab = self._calc_anchor_vocab)
        execution_order = 1
        if hasattr(self, 'scan_mode') and self.scan_mode != ScanMode.Off:
            self.links['DecVocabBarcode'] = voice.Link('DecVocabBarcode',
                                                       self.nodes['DecimalVocab'],
                                                       self.nodes['CheckScannedValue'],
                                                       conditional_method = 'dialogs.is_barcode_scanned')
            self.links['DecVocabBarcode'].execution_order = execution_order
            execution_order += 1
        self.links['DecVocabTimeout'] = voice.Link('DecVocabTimeout',
                                                   self.nodes['DecimalVocab'],
                                                   self.nodes['CheckDigitsConfirm'],
                                                   conditional_method = 'dialogs.timeout_digit_entry')
        self.links['DecVocabTimeout'].execution_order = execution_order

        # add links to newly created nodes
        for i in range(self.max_decimal_length - 1):
            self.set_additional_discrete_decimal_links(i)
        # create final default links
        self.set_final_decimal_discrete_links(self.max_decimal_length - 1)

    def set_additional_discrete_decimal_links(self, index, execution_order = 1):
        ''' for each non-final discrete decimal node, create digit links,
            anchor links if any anchor words,
            barcode links if scanning enabled, and timeout links
            index - zero-based index for one-based node and link names
            execution_order (Default=1) - starting execution order for
                one-based conditional link order of execution

            returns the next execution order available for use
        '''
        index_name = str(index + 1)
        next_name = str(index + 2)
        source_name = 'Decimal' + index_name

        # decimal digit link - FirstDecimal matches FirstDigit, so start numbering at 'Decimal2'
        link_name = 'DecDigit' + next_name
        self.links[link_name] = voice.Link(link_name,
                                           self.nodes[source_name],
                                           self.nodes['Decimal' + next_name],
                                           existing_vocab = self._calc_digit_vocab)
        if self._calc_anchor_vocab is not None:
            # anchor link
            link_name = 'DecAnchor' + index_name
            self.links[link_name] = voice.Link(link_name,
                                               self.nodes[source_name],
                                               self.nodes['DecimalDiscreteAnchor'],
                                               existing_vocab = self._calc_anchor_vocab)
        # barcode link
        if hasattr(self, 'scan_mode') and self.scan_mode != ScanMode.Off:
            link_name = 'DecBarcode' + next_name
            self.links[link_name] = voice.Link(link_name,
                                               self.nodes[source_name],
                                               self.nodes['CheckScannedValue'],
                                               conditional_method = 'dialogs.is_barcode_scanned')
            self.links[link_name].execution_order = execution_order
            execution_order += 1
        # timeout link
        link_name = 'DecTimeout' + index_name
        self.links[link_name] = voice.Link(link_name,
                                           self.nodes[source_name],
                                           self.nodes['CheckDigitsConfirm'],
                                           conditional_method = 'dialogs.timeout_digit_entry')
        self.links[link_name].execution_order = execution_order
        return execution_order + 1

    def set_final_decimal_discrete_links(self, index, execution_order = 1):
        ''' Create links from the final discrete decimal node
            index - zero-based index for one-based node and link names
            execution_order (Default=1) - starting execution order for
                one-based conditional link order of execution

            returns the next execution order available for use
        '''
        self.links['DecimalDefault'] = voice.Link('DecimalDefault',
                                                  self.nodes['Decimal' + str(index + 1)],
                                                  self.nodes['CheckDigitsConfirm'])
        return execution_order

    def set_decimal_loop_link(self):
        ''' Adds nodes for unbound entry or
            decimal places greater than max_discrete_decimal_length
        '''
        # add nodes
        self.nodes['InitializeDecimal'] = voice.Node('InitializeDecimal',
                                                     on_entry_method = 'dialogs.set_result')
        self.nodes['InitializeDecimal'].dialog = self
        self.nodes['Decimals'] = voice.Node('Decimals')
        self.nodes['Decimals'].dialog = self
        self.nodes['MoreDecimals'] = voice.Node('MoreDecimals', on_entry_method = 'dialogs.set_result')
        self.nodes['MoreDecimals'].dialog = self

        # add digit links
        self.links['FirstDecimal'] = voice.Link('FirstDecimal',
                                                self.nodes['DecimalVocab'],
                                                self.nodes['InitializeDecimal'],
                                                existing_vocab = self._calc_digit_vocab)
        self.links['FirstDecDefault'] = voice.Link('FirstDecDefault',
                                                   self.nodes['InitializeDecimal'],
                                                   self.nodes['Decimals'])
        self.links['DecimalDigits'] = voice.Link('DecimalDigits',
                                                 self.nodes['Decimals'],
                                                 self.nodes['MoreDecimals'],
                                                 existing_vocab = self._calc_digit_vocab)
        self.links['DecDigitDefault'] = voice.Link('DecDigitDefault',
                                                   self.nodes['MoreDecimals'],
                                                   self.nodes['Decimals'])

        # add anchor node and links
        if self._calc_anchor_vocab is not None:
            self.nodes['DecimalAnchor'] = voice.Node('DecimalAnchor', on_entry_method = 'dialogs.set_anchor_result')
            self.nodes['DecimalAnchor'].dialog = self
            self.links['DecLoopAnchor'] = voice.Link('DecLoopAnchor',
                                                     self.nodes['Decimals'],
                                                     self.nodes['DecimalAnchor'],
                                                     existing_vocab = self._calc_anchor_vocab)
            self.links['DecInitAnchor'] = voice.Link('DecInitAnchor',
                                                     self.nodes['DecimalVocab'],
                                                     self.nodes['DecimalAnchor'],
                                                     existing_vocab = self._calc_anchor_vocab)
            self.links['DecAnchorDefault'] = voice.Link('DecAnchorDefault',
                                                        self.nodes['DecimalAnchor'],
                                                        self.nodes['CheckDigitsConfirm'])

        # add barcode links
        execution_order = 1
        if hasattr(self, 'scan_mode') and self.scan_mode != ScanMode.Off:
            self.links['DecVocabBarcode'] = voice.Link('DecVocabBarcode',
                                                       self.nodes['DecimalVocab'],
                                                       self.nodes['CheckScannedValue'],
                                                       conditional_method = 'dialogs.is_barcode_scanned')
            self.links['DecVocabBarcode'].execution_order = execution_order
            self.links['DecimalBarcode'] = voice.Link('DecimalBarcode',
                                                      self.nodes['Decimals'],
                                                      self.nodes['CheckScannedValue'],
                                                      conditional_method = 'dialogs.is_barcode_scanned')
            self.links['DecimalBarcode'].execution_order = execution_order
            execution_order += 1

        # add timeout links
        self.links['DecVocabTimeout'] = voice.Link('DecVocabTimeout',
                                                   self.nodes['DecimalVocab'],
                                                   self.nodes['CheckDigitsConfirm'],
                                                   conditional_method = 'dialogs.timeout_digit_entry')
        self.links['DecVocabTimeout'].execution_order = execution_order
        self.links['DecimalTimeout'] = voice.Link('DecimalTimeout',
                                                  self.nodes['Decimals'],
                                                  self.nodes['CheckDigitsConfirm'],
                                                  conditional_method = 'dialogs.timeout_digit_entry')
        self.links['DecimalTimeout'].execution_order = execution_order

    def set_result(self):
        ''' Sets result to the digits collected so far and updates help '''
        help_node = set()
        if self.current_node.name in ['InitializeDecimal', 'MoreDecimals']:
            # within loop link for decimal portion
            last_node = 'Decimals' if self.current_node.name == 'MoreDecimals' else 'DecimalVocab'
            self.result += self.nodes[last_node].last_recog
            help_node = {'Decimals'}
            self._last_node = self.current_node
        else:
            super().set_result()

        if self._last_node.name in ['Initialize', 'MoreDigits']:
            # within loop link for integer portion
            help_node = {'Digits'}
        self._update_help(*help_node)

    def _update_help(self, *node_names):
        ''' update the help message to include the value spoken so far
            only updates the help at the dialog's current_node unless
            one or more node_names are specified
        '''
        help_msg = self.nodes['StartHere'].help_prompt
        if self.result is not None:
            help_msg = itext('generic.float.help',
                             help_msg,
                             ' '.join(self.result))
        # inherent truth/falsehood of [un]populated sequences
        if node_names:
            for node_name in node_names:
                self.nodes[node_name].help_prompt = help_msg
        else:
            self.current_node.help_prompt = help_msg

    def set_decimal_point(self):
        ''' Inserts the decimal point into the result,
            can be overridden if a string value other than decimal_point_char
            should be added to the result
        '''
        if self.result is None:
            self.result = self.decimal_point_char
        else:
            self.result += self.decimal_point_char
        self._update_help()
        self._last_node = self.current_node

    def set_anchor_result(self):
        ''' Sets the anchor if spoken '''
        if self.current_node.name == 'DecimalAnchor':
            self.anchor_result = self.nodes['Decimals'].last_recog
        elif self.current_node.name == 'DecimalDiscreteAnchor':
            # cannot get to DecimalDiscreteAnchor without calling set_decimal_point
            decimal_places = self.result.split(self.decimal_point_char)[1]
            self.anchor_result = self.nodes['Decimal' + str(len(decimal_places))].last_recog
        else:
            super().set_anchor_result()

    def timeout_digit_entry(self):
        ''' Function to determine if timeout occurred or
            maximum number of digits entered

        returns: True if timeout exceeded or maximum number of
            decimal places entered, otherwise False
        '''
        '''decimal_places (Default=2) - number of digits user speaks after decimal place
                if 0, requires "ready" and will not time out
                if None, the min and max integer and decimal portion lengths
                will be calculated from min_value and max_value'''
        if self._decimal_places == 0 or self.max_decimal_length is None or self.max_decimal_length <= 0:
            # Invalid or no decimal places, require anchor word
            return False
        elif self.is_timedout(self.current_node.name):
            return True
        else:
            point = self.result.find(self.decimal_point_char)
            return point >= 0 and len(self.result[point + 1:]) >= self.max_decimal_length

    def result_less_than_min_length(self):
        ''' Function called from dialog to see if user entered
            at least the minimum number of digits before feedback should be given
            Length specifications are checked in is_valid_value
            and will provide appropriate feedback to the operator

        returns: True if minimum entered, otherwise False
        '''
        #if no min length, then check if anchor word was spoken or maximum was reached
        min_length = 0 if self.min_length is None else self.min_length
        min_length += 0 if self.min_decimal_length is None else self.min_decimal_length
        if min_length > 0:
            min_length += len(self.decimal_point_char)

        if min_length == 0 or self._decimal_places == 0 or self.max_decimal_length is None or self.max_decimal_length <= 0:
            return self.anchor_result is None and len(self.result) < self.max_length
        # do not ignore overridden min_feedback_length with shorter actual min lengths
        min_length = min(min_length, self.min_feedback_length)
        return len(self.result) < min_length

    def is_valid_value(self):
        ''' check for expected length, range, or specific values '''
        if self.is_scanned:
            return True

        lengths = self.result.split(self.decimal_point_char)
        whole_places = len(lengths[0])
        decimal_places = 0 if len(lengths) == 1 else len(lengths[1])
        # check max_length for unbound entry
        whole_place_check = self.max_length is None or self.max_length <= 0
        if not whole_place_check:
            # check for a specified min_length and overall length
            whole_place_check = ((self.min_length is None or whole_places >= self.min_length)
                                 and whole_places <= self.max_length)

        decimal_place_check = self.max_decimal_length is None or self.max_decimal_length <= 0
        if not decimal_place_check:
            decimal_place_check = ((self.min_decimal_length is None or decimal_places >= self.min_decimal_length)
                                   and decimal_places <= self.max_decimal_length)

        ret_val = whole_place_check and decimal_place_check and self.is_valid_range()
        if not ret_val:
            key = self.invalid_key if self.invalid_scan_key is None else self.invalid_scan_key
            self.nodes['InvalidPrompt'].prompt = itext(key, self.result)
        return ret_val

    def is_valid_range(self):
        ''' checks that the result is within the min and max values if specified '''
        return ((self._min_value is None or self.to_decimal(self.result) >= self.to_decimal(self._min_value)) and
                (self._max_value is None or self.to_decimal(self.result) <= self.to_decimal(self._max_value)))

    def to_decimal(self, string_value):
        ''' converts the string_value to a decimal.Decimal object
            based on decimal_point_char
            Must be valid Decimal initialization string
            after replacing decimal_point_char
        '''
        return Decimal(string_value.replace(self.decimal_point_char, '.'))


#----------------------------------------------------------------------------
# Helper Class used for executing dialogs
#----------------------------------------------------------------------------
class FloatPromptExecutor(DigitsPromptExecutor):

    def __init__(self,
                 prompt,
                 priority_prompt = True,
                 help_message = None,
                 decimal_places = 2,
                 additional_vocab = {},
                 confirm = True,
                 scan = ScanMode.Off,
                 skip_prompt = False,
                 hints = None,
                 anchor_words = None,
                 min_value = None,
                 max_value = None):
        ''' Base helper class for creating, configuring, and executing a float dialog
            this classes are intended to make it easier for end users to configure
            dialogs beyond the basic function provided
        Note: with hints, from VoiceCatalyst 2.1.1 on, * can be used for wildcards
              to specify any value, to allow '1.*' or ['1.*', '2.*']
              for variable entries within a range
        '''
        super().__init__(prompt=prompt,
                         priority_prompt = priority_prompt,
                         help_message=help_message,
                         additional_vocab=additional_vocab,
                         confirm=confirm,
                         scan=scan,
                         skip_prompt=skip_prompt,
                         hints=hints,
                         anchor_words=anchor_words)

        self.decimal_places = decimal_places
        self.min_value = min_value
        self.max_value = max_value

    def _create_dialog(self):
        ''' Creates a dialog object and saves it to the dialog member variable.
            This class is not intended to be called directly. retrieve
            the class's dialog property to get the instance of the dialog.
        Note:  The dialog is created with decimal_places and max_whole_places set to 6
            if required_spoken_values are set, _configure_dialog and set_required
            will modify the discrete grammar based on the required values
        '''
        self._dialog = obj_factory.get(FloatPrompt,
                                       self.prompt,
                                       self.help_message,
                                       self.decimal_places,
                                       self.confirm,
                                       self.scan_mode,
                                       self.min_value,
                                       self.max_value)
    def _configure_dialog(self):
        super()._configure_dialog()
        self.dialog.set_lengths_from_values()

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
            if (self.dialog.include_anchor != None
                and not self.dialog.is_scanned
                and set(self.result).issubset(self.dialog.links['FirstDigit'].vocab | {self.dialog.decimal_point_char})):
                self.anchor_result = self.dialog.anchor_result