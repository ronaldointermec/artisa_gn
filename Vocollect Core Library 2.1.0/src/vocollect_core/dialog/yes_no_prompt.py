#
# Copyright (c) 2010-2011 Vocollect, Inc.
# Pittsburgh, PA 15235
# All rights reserved.
#
# This source code contains confidential information that is owned by
# Vocollect, Inc. and may not be copied, disclosed or otherwise used without
# the express written consent of Vocollect, Inc.
# 

from vocollect_core.dialog.ready_prompt import ReadyPrompt
from vocollect_core import class_factory
from vocollect_core.dialog.base_dialog import BaseDialogExecutor
from vocollect_core.utilities import obj_factory

#----------------------------------------------------------------------------
# Yes/No wrapper class
#----------------------------------------------------------------------------
class YesNoPrompt(class_factory.get(ReadyPrompt)):
    
    def __init__(self, prompt, priority = False, include_cancel = False):
        super().__init__(prompt, priority)
        if include_cancel:
            self.set_additional_vocab({'yes' : False, 'no' : False, 'cancel' : False})
        else:
            self.set_additional_vocab({'yes' : False, 'no' : False})
        self.remove_ready()

    def _get_task_dynamic_vocab(self):
        ''' not included for simple yes no prompts '''
        pass 
        
#----------------------------------------------------------------------------
#Helper Class used for executing dialogs 
#----------------------------------------------------------------------------
class YesNoPromptExecutor(BaseDialogExecutor):
    def __init__(self, 
                 prompt, 
                 priority_prompt = True,
                 help_message = None, 
                 additional_vocab = {},
                 include_cancel = False,
                 time_out = None):
        ''' Base helper class for creating, configuring, and executing a YesNo dialog
            this classes are intended to make it easier for end users to configure
            dialogs beyond the basic function provided
        '''
        super().__init__(prompt=prompt,
                         priority_prompt = priority_prompt,
                         help_message=help_message,
                         additional_vocab=additional_vocab)

        self.include_cancel = include_cancel
        self.time_out = time_out
        
        #Working variables
        self._dialog = None
        
        #result variables
        self.result = None
    
    def _create_dialog(self):
        ''' Creates a dialog object and saves it to the dialog member variable.
            This class is not intended to be called directly. retrieve
            the class's dialog property to get the instance of the dialog.
        '''
        self._dialog = obj_factory.get(YesNoPrompt, 
                                       self.prompt, 
                                       self.priority_prompt,
                                       self.include_cancel)
    def _configure_dialog(self):    
        ''' Configures dialog object based on additional settings
            This method is not intended to be called directly. retrieve
            the class's dialog property to get the instance of the dialog.
        '''
        self.dialog.remove_ready()
        if self.time_out != None:
            self.dialog.dialog_time_out_value = self.time_out
