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
from vocollect_core import class_factory
from vocollect_core.utilities import obj_factory
from vocollect_core.utilities.util_methods import say_again_supported
import voice

#----------------------------------------------------------------------------
#Ready wrapper class
#----------------------------------------------------------------------------
class ReadyPrompt(class_factory.get(BaseDialog)):
    ''' Wrapper class for prompting user and waiting for user to confirm with ready

    returns: vocab spoken at main prompt
    '''

    def __init__(self, prompt, priority = False):
        ''' Constructor

        Parameters:
              prompt - prompt to be spoken
              priority (Default=False) - whether or not prompt is priority prompt
        '''
        super().__init__('Ready')

        self.nodes['ReadyPrompt'].prompt = prompt
        self.nodes['ReadyPromptNPPGS'].prompt = prompt
        self.nodes['ReadyPrompt'].prompt_is_priority = priority
        self.nodes['ConfirmPrompt'].is_allow_speak_ahead_node = False
        self.nodes['ReadyPromptNPPGS'].is_allow_speak_ahead_node = False
        self._final_configuration()

    def _get_prompt(self):
        '''
            return the current prompt. Override in classes that store the prompt
            in a different node.
        '''
        if 'ReadyPrompt' in self.nodes:
            return self.nodes['ReadyPrompt'].prompt
        else:
            return None

    def set_result(self):
        '''sets result to vocab spoken at main prompt '''
        self.result = self.nodes['StartHere'].last_recog

    def set_additional_vocab(self, additional_vocab):
        '''adds additional vocab to the main prompt '''
        super().set_additional_vocab(additional_vocab)
        self.links['main'].vocab |= set(self.additional_vocab.keys())
        if say_again_supported() and "say again" not in self.additional_vocab:
            # if say again is not specified in additional_vocab,
            # add an explicit link to the non-priority prompt with a grammar stop
            self.links["SayAgainLink"] = voice.Link("SayAgainLink",
                                                    self.nodes["StartHere"],
                                                    self.nodes["ReadyPromptNPPGS"],
                                                    ["say again"])

    def remove_ready(self):
        ''' remove the word ready from main link.
            IMPORTANT: other words have to be added first before ready
            can be removed. If all that is desired is a prompt, then call
            the prompt_only function
        '''
        self.links['main'].vocab -= set(['ready'])

    def http_post(self, post_value):
        ''' check and set result and http_post to true '''
        if post_value in self.links['main'].vocab:
            self.result = post_value
            self._http_posted = True


    def http_get(self):

        self.http_get_template()
        form = self.form_template
        prompt = self.nodes['ReadyPrompt'].prompt

        buttons = ''
        for word in self.links['main'].vocab:
            if word == 'ready':
                buttons += '<input type="submit" name="ReadySubmit" value="ready">'
            elif word == 'yes':
                buttons += '<input type="submit" name="ReadySubmit" value="yes">'
            elif word == 'no':
                buttons += '<input type="submit" name="ReadySubmit" value="no">'
            elif word == 'cancel':
                buttons += '<input type="submit" name="ReadySubmit" value="cancel">'

        additional_words = []
        for word in self.additional_vocab:
            if word != 'ready' and word != 'yes' and word != 'no' and word != 'cancel':
                additional_words.append(word)

        form = form.replace("${prompt}", prompt)
        form = form.replace("${buttons}", buttons)
        form = form.replace("${otherActions}", self.http_other_actions_form(additional_words))
        return form

#----------------------------------------------------------------------------
#Helper Class used for executing dialogs
#----------------------------------------------------------------------------
class ReadyPromptExecutor(BaseDialogExecutor):

    def _create_dialog(self):
        ''' Creates a dialog object and saves it to the dialog member variable.
            This class is not intended to be called directly. retrieve
            the class's dialog property to get the instance of the dialog.
        '''
        self._dialog = obj_factory.get(ReadyPrompt,
                                       self.prompt,
                                       self.priority_prompt)

    def _configure_dialog(self):
        ''' Configures dialog object based on additional settings
            This method is not intended to be called directly. retrieve
            the class's dialog property to get the instance of the dialog.
        '''
        self.dialog.set_additional_vocab(self.additional_vocab)
        self.dialog.skip_prompt = self.skip_prompt
