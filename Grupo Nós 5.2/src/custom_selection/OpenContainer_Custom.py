from vocollect_core import class_factory
from vocollect_core.dialog.functions import prompt_ready, prompt_only, prompt_alpha_numeric
from selection.OpenContainer import OpenContainer
from vocollect_core import itext
from selection.SharedConstants import OPEN_CONTAINER_OPEN
from custom_selection.SharedConstants import POSTION_PROMPT_LIST

class OpenContainer_Custom(OpenContainer):
    
    #----------------------------------------------------------
    def open_container(self):
        container=''
        is_scanned = False

        if self._position == '':
            prompt = itext('selection.new.container.prompt.for.container.id')
        else:
            prompt = itext('selection.new.container.prompt.for.container', POSTION_PROMPT_LIST[''+ self._position +''])

        if self._region['promptForContainer'] == 1:
            result = prompt_alpha_numeric(prompt, 
                                          itext('selection.new.container.prompt.for.container.help'), 
                                          confirm=True,scan=True)
            container, is_scanned = result

        if self._picks[0]['targetContainer'] == 0:
            target_container = ''
        else:
            target_container = self._picks[0]['targetContainer']

        result = -1
        while result < 0:
            result = self._container_lut.do_transmit(self._assignment['groupID'], 
                                                     self._assignment['assignmentID'], target_container, '', container, 2 , '')

        if result > 0:
            self.next_state = OPEN_CONTAINER_OPEN

        if result == 0:
            if container:
                # if the operator specifies a container, make sure it exists and is not already closed
                # VoiceLink may send a closed container instead of an error
                # assuming the device is sending a duplicate transaction
                record_found = False
                for record in self._container_lut:
                    if is_scanned:
                        if record['scannedValidation'] == container:
                            record_found = True
                    else:
                        # an operator may speak more than the minimum
                        # "spoken container digits" region setting
                        # VoiceLink will send the full spoken value
                        # as the scannedValidation and truncate the spokenValidation
                        # to the right-most region setting
                        if container in [record['scannedValidation'], record['spokenValidation']]:
                            record_found = True
                    if record_found:
                        if record['status'] == 'C':
                            prompt_only(itext('selection.close.container.already.closed', container))
                            self.next_state = OPEN_CONTAINER_OPEN
                            return
                        break
                if not record_found:
                    prompt_only(itext('selection.new.container.not.found', container))
                    self.next_state = OPEN_CONTAINER_OPEN
                    return
            if self._region['promptForContainer'] != 1:
                if self._position == '':
                    prompt_last = itext('selection.new.container.prompt.open.last', self._container_lut[0]['scannedValidation'])
                    if self._picks[0]['targetContainer'] != 0:
                        self._assignment['activeTargetContainer'] = self._container_lut[0]['targetConatiner']
                else:
                    containers = self._container_lut.get_open_containers(self._assignment['assignmentID'])
                    if len(containers) == 0:
                        containers = self._container_lut.get_closed_containers(self._assignment['assignmentID'])
                    if len(containers) > 0:    
                        prompt_last = itext('selection.new.container.prompt.open.last.multiple', 
                                          containers[0]['scannedValidation'], 
                                             POSTION_PROMPT_LIST[''+ self._position +''])
                    else:
                        prompt_last = itext('selection.new.container.no.containers.returned')
                        
                prompt_ready(prompt_last)
            
            if self._region['printLabels'] == '1':
                if  self._container_lut[0]['printed']  == 0:
                    self._print_label()

class_factory.set_override(OpenContainer, OpenContainer_Custom)