#
# Copyright (c) 2010-2011 Vocollect, Inc.
# Pittsburgh, PA 15235
# All rights reserved.
#
# This source code contains confidential information that is owned by
# Vocollect, Inc. and may not be copied, disclosed or otherwise used without
# the express written consent of Vocollect, Inc.
# 

from vocollect_core.dialog.base_dialog import BaseDialog
from vocollect_core import class_factory

#----------------------------------------------------------------------------
#Prompt Only wrapper class
#----------------------------------------------------------------------------
class PromptOnly(class_factory.get(BaseDialog)):
    ''' Wrapper class for simple prompt dialog 
    
    '''
    def __init__(self, prompt, priority = False):
        '''Constructor 
        
        Parameters:
              prompt - prompt to be spoken
              priority (Default=False) - whether or not prompt is priority prompt 
        '''
        super().__init__('PromptOnly')
        self.nodes['Prompt'].prompt = prompt
        self.nodes['Prompt'].prompt_is_priority = priority
        self._final_configuration()
        
