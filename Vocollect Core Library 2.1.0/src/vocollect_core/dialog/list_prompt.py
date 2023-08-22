#
# Copyright (c) 2010-2011 Vocollect, Inc.
# Pittsburgh, PA 15235
# All rights reserved.
#
# This source code contains confidential information that is owned by
# Vocollect, Inc. and may not be copied, disclosed or otherwise used without
# the express written consent of Vocollect, Inc.
# 

from vocollect_core.dialog.digits_prompt import DigitsPrompt
from vocollect_core import itext, class_factory
from vocollect_core.dialog.base_dialog import BaseDialog, BaseDialogExecutor
from vocollect_core.utilities import obj_factory
    
#----------------------------------------------------------------------------
#List Dialog class
#----------------------------------------------------------------------------
class ListPrompt(class_factory.get(DigitsPrompt)):
    ''' Wrapper class for selecting from a list
    
    returns: key_value that was selected
    '''
    def __init__(self, prompt, help, confirm=True, allow_only_one=True): #@ReservedAssignment
        ''' Constructor
        
        Parameters:
              prompt - main prompt to be spoken
              help - main help message to be spoken
              confirm (Default=True) - determines if operator confirms selection 
              allow_only_one (Default=False) - determines whether All or No More can be spoken
        
        Additional properties:
              confirm_prompt_key - resource key for confirmation prompt
              select_list - list of values in the form of [ [key_value,description], ...]
                       key_value must be numeric
              invalid_key - Resource key for prompt to be spoken when invalid value entered
              min_length - automatically set based on list if set_list methods called
              max_length - automatically set based on list if set_list methods called
        '''

        # Note: this consciously skips the DigitsPrompt __init__
        class_factory.get(BaseDialog).__init__(self, 'ListSelection')

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

        self.confirm = confirm
        self.allow_only_one = allow_only_one

        self.select_list = []
        self.invalid_key = 'generic.wrongValue.prompt'

        # As a guideline, entries over 6 digits are cumbersome to speak
        # and should be avoided.  Scanning or partial entries validated by the host
        # should be considered for these situations.  Alternately,
        # consider setting max_length to None which will allow the operator
        # to pause and resume entry.
        self.max_discrete_length = 6
        self._last_node = None

        self.allow_select_flag = False
        self.repeat_list = False
        
        self.select_iter = None
        self.rec = None
        self.help = help

        self._final_configuration()
        
    def set_list(self, list): #@ReservedAssignment
        ''' method to set the selection list

        Parameters:
              list - list of values in the form of [ [key_value,description], ...]
                       key_value must be numeric
        '''
        del self.select_list[:]
        self.min_length = 1000
        self.max_length = 0
        for elem in list:
            if len(elem[0]) > self.max_length:
                self.max_length = len(elem[0])
            if len(elem[0]) < self.min_length:
                self.min_length = len(elem[0])
            self.select_list.append(elem)
    
    def build_list_from_lut(self, lut, key_field, description_field):
        ''' method to set the selection list based on a LUT

        Parameters:
              LUT - Lut to select from
              key_field - Key ID field for selection, must be numeric values
              description_field - speakable description
        '''
        del self.select_list[:]
        self.min_length = 1000
        self.max_length = 0
        for rec in lut.lut_data:
            key_len = len(str(rec[key_field]))
            if key_len < self.min_length:
                self.min_length = key_len
            if key_len > self.max_length:
                self.max_length = key_len
            self.select_list.append([rec[key_field], rec[description_field]])    

    def set_help(self):
        super().set_help(['description'])
        
    def move_first(self):
        ''' moves to the beginning of list '''
        self.select_iter = iter(self.select_list)
        
    def move_next(self):
        ''' moves to next item in list
         
        returns: True if there is another record, false if no more records
        '''
        try:
            rec = next(self.select_iter);
            self.result = str(rec[0])
            self.nodes['ListPromptWSelect'].prompt = str(rec[0]) + ', ' + str(rec[1])    
            self.nodes['ListPromptWOSelect'].prompt = str(rec[0]) + ', ' + str(rec[1])    
            return True
        except Exception:
            if self.repeat_list:
                self.move_first()
                return self.move_next()
            else:
                return False

    def confirm_prompt(self):
        ''' Method to set confirm prompt or invalid prompt if entry not found in list
        
        returns: True if enter value in list, otherwise false
        '''
        if self.should_confirm():
            prompt_value = self.result
            
            #get value from list if in list
            for rec in self.select_list:
                if str(rec[0]) == prompt_value:
                    prompt_value = str(rec[1])
            
            #Should be either 1 or 2
            prompt = itext(self.confirm_prompt_key)
            if prompt.count('%s') + prompt.count('{') == 1:
                self.nodes['ConfirmPrompt'].prompt = itext(self.confirm_prompt_key, 
                                                                           prompt_value)
            else:
                self.nodes['ConfirmPrompt'].prompt = itext(self.confirm_prompt_key,
                                                                           self.result, 
                                                                           prompt_value)
            return True

        return False

    def is_valid_value(self):
        ''' Method to check if valid value was enter based on list or additional vocabulary
        
        returns: True if entered value in list, or in additional vocabulary
        '''
        #Value is in list
        for rec in self.select_list:
            if str(rec[0]) == self.result:
                return True
        
        #Value is additional vocabulary
        if self.result in self.additional_vocab:
            return True
        
        #not a valid entry
        self.nodes['InvalidPrompt'].prompt = itext(self.invalid_key, self.result)
        self.is_scanned = False
        return False
    
    def allow_select(self):
        ''' returns flag for whether or not user can speak "select" while 
        reviewing the list of items '''
        return self.allow_select_flag

    def http_post(self, post_value):
        ''' check and set result and http_post to true '''
        in_list = False
        for rec in self.select_list:
            if str(rec[0]) == post_value:
                in_list = True
        
        if in_list or post_value in self.additional_vocab:
            self.result = post_value
            self._http_posted = True
    
    def prompt_here(self):
        ''' code to execute when main prompt is entered '''
        super().prompt_here()
        # reset _http_posted flag
        self._http_posted = False
    
    def http_get(self):
        self.http_get_template()
        
        prompt = self.nodes['PromptHere'].prompt
        list_words = ''
        for word in self.select_list:
            list_words += '<option value="' + str(word[0]) + '">' \
                        + str(word[0]) + ' -- ' + str(word[1]) + '</option>'

        form = self.form_template.replace("${prompt}", prompt)
        form = form.replace("${help}", self.help)
        form = form.replace("${list}", list_words)
        form = form.replace("${otherActions}", self.http_other_actions_form())
        return form
    
#----------------------------------------------------------------------------
#Helper Class used for executing dialogs 
#----------------------------------------------------------------------------
class ListPromptExecutor(BaseDialogExecutor):
    
    def __init__(self, 
                 prompt, 
                 priority_prompt = True,
                 help_message = None, 
                 additional_vocab = {},
                 selection_list = None,
                 lut = None,
                 key_field = None,
                 description_field = None):
        ''' Base helper class for creating, configuring, and executing a list dialog
            this classes are intended to make it easier for end users to configure
            dialogs beyond the basic function provided
        '''
        super().__init__(prompt=prompt,
                         priority_prompt=priority_prompt,
                         help_message=help_message,
                         additional_vocab=additional_vocab)
        
        #additional properties
        self.selection_list = selection_list
        self.lut = lut
        self.key_field = key_field
        self.description_field = description_field

    def _create_dialog(self):
        ''' Creates a dialog object and saves it to the dialog member variable.
            This class is not intended to be called directly. retrieve
            the class's dialog property to get the instance of the dialog.
        '''
        self._dialog = obj_factory.get(ListPrompt, self.prompt, self.help_message)
        
    def _configure_dialog(self):    
        ''' Configures dialog object based on additional settings
            This method is not intended to be called directly. retrieve
            the class's dialog property to get the instance of the dialog.
        '''
        self.dialog.set_additional_vocab(self.additional_vocab)
        self.dialog.nodes['PromptHere'].prompt_is_priority = self.priority_prompt
        
        if self.selection_list != None:
            self.dialog.set_list(self.selection_list)
        elif self.lut != None:
            self.dialog.build_list_from_lut(self.lut, 
                                            self.key_field, 
                                            self.description_field)
