#
# Copyright (c) 2010-2011 Vocollect, Inc.
# Pittsburgh, PA 15235
# All rights reserved.
#
# This source code contains confidential information that is owned by
# Vocollect, Inc. and may not be copied, disclosed or otherwise used without
# the express written consent of Vocollect, Inc.
#


from voice import Dialog, get_all_vocabulary_from_vad, open_vad_resource, \
    get_voice_application_property, log_message
from vocollect_core import itext
from vocollect_core.task.task_runner import TaskRunnerBase, Launch
from vocollect_core.data_collection import collect_data

# global dialog instance counter
# this may get moved to voice.dialog_objects Dialog class in the future (RBIRDCLI-2196 / VSCVALIB-61)
dialog_number = 1

#Get Speech Delay Values
try:
    SPEECH_DELAY_DIGITS = float(get_voice_application_property('DigitEntrySpeechDelay'))
except:
    SPEECH_DELAY_DIGITS = 0.900

try:
    SPEECH_DELAY_ALPHA = float(get_voice_application_property('AlphaEntrySpeechDelay'))
except:
    SPEECH_DELAY_ALPHA = 1.000

#############################################################################
# Base Dialog class
#############################################################################
class BaseDialog(Dialog):
    ''' Base class wrapper for dialogs to provide
    some basic and common functionality
    '''

    #Static variable to indicate whether or not to include dynamic vocabulary.
    #set to True to exclude dynamic vocab. Will only persist for 1 run of dialog
    #no need to set back to false.
    exclude_dynamic_vocab = False

    def __init__(self, dialog_name):
        ''' Constructor

        parameters:
            dialog_name - name of dialog(VID) to load
        '''
        global dialog_number
        dialog_number += 1

        super().__init__(dialog_name)

        # increment dialog number
        self.instance_id = dialog_number
        #properties to ensure functions work when called
        self.confirm = False
        self.confirm_prompt_key = 'generic.correct.confirm'
        self.result = None
        self.min_length = 1
        self.max_length = 10

        self.additional_vocab = {}
        self.local_dynamic = []
        self.dynamic_vocab = None
        self.skip_prompt=None

        # Used in DCM data collection events. Current task_name and state for dialog
        # (only applies if TaskRunner framework is in use).
        self.current_task_name = None
        self.current_task_state = None

        #default timeout of speech will be set first time through delay check (is_timedout method)
        #this left behind for legacy purposes in case user set this in a custom application
        self.speech_delay = 0.000

        #get task dynamic vocab
        self._get_task_dynamic_vocab()

        self._http_posted = False;
        self.form_template = None

        self.dialog_time_out_value = 0

    def _get_task_dynamic_vocab(self):
        ''' check the currently running task for a dynamic_vocab object
        if defined get additional vocabulary that is valid at this
        time from that object
        '''
        if ((not BaseDialog.exclude_dynamic_vocab)
             and TaskRunnerBase.get_main_runner() is not None):
            task = TaskRunnerBase.get_main_runner().get_current_task()
            if task is not None:
                self.dynamic_vocab = task.dynamic_vocab
                if self.dynamic_vocab is not None:
                    self.additional_vocab = self.dynamic_vocab.get_vocabs()

    def _final_configuration(self):
        ''' method to override for custom initialization
        called at end of initialization
        '''
        pass

    def was_scanned(self):
        if (hasattr(self, 'is_scanned')):
            return self.is_scanned
        else:
            return False

    def was_http_posted(self):
        return self._http_posted

    def http_post(self, post_value):
        ''' check and set result and http_post to true '''
        if False: #Check if post_value is valid
            self.result = post_value
            self._http_posted = True

    def http_get_template(self):
        if self.form_template is None:
            # Read it from a file
            self.form_template = open_vad_resource("dialogs/" + self.name + ".html").read()

    def http_other_actions_form(self, list_items = None):
        ''' Return an HTML form representing the list of available
            other actions that can be taken from this dialog. '''
        additional_words = ''

        if list_items == None:
            list_items = sorted(self.additional_vocab)
        else:
            list_items.sort()

        if len(list_items) > 0:
            additional_words = '<form action="' + self.name + '"><table><tr><td>' \
                + 'Or Select Other Action:</td><td><select name="otherAction">'
            for word in list_items:
                additional_words += "<option>" + word + "</option>"
            additional_words += '</select></td></tr></table></form>'
        return additional_words

    def http_get(self):
        # Override to supply behavior
        return "Not implemented"

    def prompt_here(self):
        ''' code to execute when main prompt is entered '''
        pass

    def dialog_time_out(self):
        ''' Method used to determine how long in node and exit dialog
        if over specified time. Currently only used in ready.vid
        '''
        return (self.dialog_time_out_value > 0
                and self.nodes['StartHere'].seconds_since_entry >=
                    self.dialog_time_out_value)

    def is_timedout(self, node_name):
        ''' Helper method for performing wait conditions on links

        Parameters:
                node_name - name of node link is exiting

        returns: True if number of milliseconds elapsed
        since node was entered, otherwise false
        '''

        if self.speech_delay == 0.000:
            characters = set()
            for link in self.nodes[node_name].out_links:
                characters |= link.vocab

            #check for Alpha characters, if found use alpha speech delay
            if len(set('ABCDEFGHIJKLMNOPQRSTUVWXYZ') & characters) > 0:
                self.speech_delay = SPEECH_DELAY_ALPHA
            #use digit speech delay only
            else:
                self.speech_delay = SPEECH_DELAY_DIGITS

            log_message('CORE LIB: speech delay set to %s for dialog %s' %
                        (self.speech_delay, self.name))

        return self.nodes[node_name].seconds_since_entry >= self.speech_delay

    def run(self):
        ''' Override of run method to have run return result

        returns: returns dialog's get_result method's value
        '''
        #reset inclusion of dynamic vocab
        BaseDialog.exclude_dynamic_vocab = False

        # reset the current task and state so we know what they are
        # for data collection events
        self.current_task_name = None
        self.current_task_state = None
        if TaskRunnerBase.get_main_runner() is not None:
            task = TaskRunnerBase.get_main_runner().get_current_task()
            if task is not None:
                self.current_task_name = task.name
                self.current_task_state = task.current_state

        try:
            run = True
            result = None
            while run:
                super().run()
                #check if local defined dynamic, if so just return it,
                #then check if in global dynamic, if so then process it
                #else simply return result

                result = self.get_result()
                if result in self.local_dynamic:
                    run = False
                elif self.dynamic_vocab is not None:
                    if result in self.dynamic_vocab.vocabs:
                        self.collect_data('additional_vocab')
                    run = self.dynamic_vocab.execute_vocab(result)
                    self.skip_prompt = self.dynamic_vocab.is_skip_prompt(result)
                else:
                    run = False
        except Launch:
            self.collect_data('launch')
            raise
        finally:
            #Clean up/destroy dialog when done to ensure
            #garbage collection occurs quickly.
            #Put in finally block to handle when exception raised from dialog
            #(i.e. launch exception may be thrown if using task runner/task base)
            if hasattr(self, "clean_up"): #check if method exists for backward compatibility
                self.clean_up()
        self.collect_data('normal')

        return result

    def get_result(self):
        ''' method to allow extending classes to override the result '''
        return self.result

    def should_confirm(self):
        ''' check if result value should be confirmed or
        not based on additional vocabulary and confirm flag
        '''
        if self.result in self.additional_vocab:
            if self.additional_vocab[self.result] is None:
                return self.confirm
            else:
                return self.additional_vocab[self.result]
        else:
            return self.confirm

    def confirm_prompt(self):
        ''' check if result value should be confirmed or
        not based on additional vocabulary and confirm flag

        Confirmation prompt will only use a spell tagged prompt
        when the result:
            is not additional_vocab
            and contains non digit values
        '''

        key = self.confirm_prompt_key

        # additional vocabs are never Spell tagged - so always
        # use the generic.correct.confirm
        if self.result in self.additional_vocab:
            key = 'generic.correct.confirm'
        else:
            if not set(self.result).issubset(set('0123456789')):
                key = 'generic.spell.correct.confirm'

        if self.should_confirm():
            self.nodes['ConfirmPrompt'].prompt = itext(key, self.result)
            return True

        return False

    def set_help(self, additional = []):
        '''set help text for dialog

        Parameters:
                additional - Single word, list of words, or dictionary of words.

        '''
        pass

    def _get_prompt(self):
        '''
            return the current prompt. Override in classes that store the prompt
            in a different node.
        '''
        if 'Prompt' in self.nodes:
            return self.nodes['Prompt'].prompt
        else:
            return None

    def collect_data(self, phase):
        '''
            Collect data, construct and send the data collection event for this dialog.
            
            Parameter
                phase -- the phase in the dialog process for the event
        '''                
        collect_data(self._build_dcm_data(phase))

    def _build_dcm_data(self, phase):
        '''
            Construct default collection event data for this dialog. Override
            or extend in subclasses to change this.
            
            Parameter
                phase -- the phase in the dialog process for the event
        '''                

        scanned = self.was_scanned()
        http_posted = self.was_http_posted()
        prompt = self._get_prompt()

        to_task = None
        to_state = None        
        if phase == 'launch':
            if (TaskRunnerBase.get_main_runner() is not None):
                task = TaskRunnerBase.get_main_runner().get_current_task()
                if task is not None:
                    to_task = task.name
                    to_state = task.current_state
                    
        data_to_send = {'stream' : 'dialog',
                        'dialog_name' : self.name,
                        'task_class' : self.current_task_name, 
                        'task_state' : self.current_task_state,
                        'result' : self._get_result_for_dcm(phase),
                        'prompt:' : prompt,
                        'phase' : phase
                  }
        if scanned:
            data_to_send['scanned'] = True
        if http_posted:
            data_to_send['http_posted'] = True
        if to_task is not None:
            data_to_send['to_class'] = to_task
            data_to_send['to_state'] = to_state
        
        return data_to_send
    
    def _get_result_for_dcm(self, phase):
        '''
            Return the result of the dialog for data collection event. this is just
            like get_result(), except that it can be None when launching.
            
            Parameter
                phase -- the phase in the dialog process for the event
        '''
        if phase == 'launch':
            return None
        else:
            return self.get_result()
        
    def set_additional_vocab(self, additional_vocab):
        ''' Set additional vocabulary words for Dialog

        Parameters:
                additional_vocab - Single word, list of words, or dictionary of words.

        '''
        if type(additional_vocab) == dict:
            self.additional_vocab.update(additional_vocab)
            for vocab in list(additional_vocab.keys()):
                if type(vocab) == str:
                    if vocab not in self.local_dynamic:
                        self.local_dynamic.append(vocab)

        elif type(additional_vocab) == list:
            for vocab in additional_vocab:
                if type(vocab) == str:
                    self.additional_vocab[vocab] = self.confirm
                    if vocab not in self.local_dynamic:
                        self.local_dynamic.append(vocab)

        elif type(additional_vocab) == str:
            self.additional_vocab[additional_vocab] = self.confirm
            if additional_vocab not in self.local_dynamic:
                self.local_dynamic.append(additional_vocab)

        #validate vocab is valid
        self._validate_vocab_exists()

    def _validate_vocab_exists(self):
        '''validates if the vocab exists in vad'''
        all_vocab = get_all_vocabulary_from_vad()
        vocabs = self.additional_vocab
        for vocab in list(vocabs.keys()):
            if (vocab not in all_vocab):
                self.additional_vocab.pop(vocab)

    def _remove_existing_vocab(self, node_name):
        ''' removes any additional vocab that already exist on main node

        Parameters:
                node_name - name of node to remove vocab from.
        '''
        additional_set = set(self.additional_vocab.keys())
        for link in self.nodes[node_name].out_links:
            same_set = additional_set & link.vocab
            for vocab in same_set:
                del self.additional_vocab[vocab]

    def _move_link(self, link_name, source_name, dest_name):
        ''' Use with caution.  This should be called before running the dialog.
            Invalid references will cause a KeyError attempting to access non-existent nodes or links.
        '''
        if link_name not in self.links:
            log_message("BASE DIALOG: link " + str(link_name) + " not found in dialog " + str(self.name))
        if source_name not in self.nodes:
            log_message("BASE DIALOG: node " + str(source_name) + " not found in dialog " + str(self.name))
        if dest_name not in self.nodes:
            log_message("BASE DIALOG: node " + str(dest_name) + " not found in dialog " + str(self.name))

        # get link and original source/dest nodes
        link = self.links[link_name]
        orig_source_node = self.links[link_name].source_node
        orig_dest_node = self.links[link_name].dest_node

        # determine if running mock_catalyst and set link's
        # source and dest node (name or node object)
        if type(orig_source_node) == str: # mock_catalyst
            orig_source_node = self.nodes[orig_source_node]
            orig_dest_node = self.nodes[orig_dest_node]
            link.source_node = source_name
            link.dest_node = dest_name
        else:
            link.source_node = self.nodes[source_name]
            link.dest_node = self.nodes[dest_name]

        # remove link from original source and dest nodes
        orig_source_node.out_links.remove(link)
        orig_dest_node.in_links.remove(link)

        # add to new source and dest nodes
        self.nodes[source_name].out_links.append(self.links[link_name])
        self.nodes[dest_name].in_links.append(self.links[link_name])


    def _remove_link(self, link_name):
        ''' Use with caution.  This should be called before running the dialog.
            Invalid references will cause a KeyError attempting to access non-existent links.
        '''
        if link_name not in self.links:
            log_message("BASE DIALOG: link " + str(link_name) + " not found in dialog " + str(self.name))

        # get source and destination nodes
        source_node = self.links[link_name].source_node
        dest_node = self.links[link_name].dest_node
        if type(source_node) == str: # mock_catayst
            source_node = self.nodes[source_node]
            dest_node = self.nodes[dest_node]

        # remove link
        source_node.out_links.remove(self.links[link_name])
        dest_node.in_links.remove(self.links[link_name])
        del self.links[link_name]


#----------------------------------------------------------------------------
#Helper Class used for executing dialogs
#----------------------------------------------------------------------------
class BaseDialogExecutor(object):

    def __init__(self,
                 prompt,
                 priority_prompt = True,
                 help_message = None,
                 additional_vocab = {},
                 skip_prompt = False):
        ''' Base helper class for creating, configuring, and executing a dialog
            these classes are intended to make it easier for end users to configure
            dialogs beyond the basic function provided

            This is an Abstract class and should not be instantiated directly
            see the various prompts for implemented executor classes
        '''
        #Passed in configuration properties
        self.prompt = prompt
        self.help_message = help_message
        self.priority_prompt = priority_prompt
        self.additional_vocab = additional_vocab
        self.skip_prompt = skip_prompt

        #Working variables
        self._dialog = None

        #result variables
        self.result = None

    @property
    def dialog(self):
        ''' Dialog property to get the instance of the dialog that will be ran
        '''
        if self._dialog == None:
            self._create_dialog()
            self._configure_dialog()

        return self._dialog

    def _create_dialog(self):
        ''' Creates a dialog object and saves it to the dialog member variable.
            This method is not intended to be called directly. retrieve
            the class's dialog property to get the instance of the dialog.
        '''
        pass

    def _configure_dialog(self):
        ''' Configures dialog object based on additional settings
            This method is not intended to be called directly. retrieve
            the class's dialog property to get the instance of the dialog.
        '''
        pass

    def execute_dialog(self):
        ''' Executes the dialog
        '''
        self.result = self.dialog.run()

    def get_results(self):
        ''' Gets the results of the dialog, Will execute the dialog if it has not
            already beed executed

            returns: result
        '''
        if self.result == None:
            self.execute_dialog()

        return self.result
