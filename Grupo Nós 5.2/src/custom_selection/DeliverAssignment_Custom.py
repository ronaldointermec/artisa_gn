from vocollect_core import class_factory, itext
from selection.DeliverAssignment import DeliverAssignmentTask
from vocollect_core.dialog.functions import prompt_ready
from selection.SharedConstants import ASSIGNMENT_DELIVER_LOAD
from custom_selection.SharedConstants import POSTION_PROMPT_LIST

class DeliveryAssignmentTask_Custom(DeliverAssignmentTask):
    
    #----------------------------------------------------------
    def deliver_load(self):
        ''' Deliver/load  if direct load then load license else verify check digit and deliver'''
        # need to loop for all assignment
        #the following fields will be used for multiple assignments
        position=self._assignment["position"]
        id=self._assignment["idDescription"]
        delivery_location=self._delivery_location_lut[0]["location"]
        loading_dock_door=self._delivery_location_lut[0]["loadingDockDoor"]
        
        if self._delivery_location_lut[0]['allowOverride']:
            additional_vocab = {'override':False}
        else:
            additional_vocab = {}

        #load assignment
        if self._override:
            if self._multiple_assignments:
                prompt = itext("selection.deliver.assignment.load.multi", POSTION_PROMPT_LIST[''+ position +''], id, loading_dock_door)
            else: 
                prompt = itext("selection.deliver.assignment.load", loading_dock_door)
            self._check_digits = self._delivery_location_lut[0]["loadingDockDoorCD"]
        else:
       
            #deliver assignment
            if self._multiple_assignments:
                prompt = itext("selection.deliver.assignment.deliver.multi", POSTION_PROMPT_LIST[''+ position +''], id, delivery_location)
            else: 
                prompt = itext("selection.deliver.assignment.deliver", delivery_location)
            self._check_digits = self._delivery_location_lut[0]["checkDigit"]
        
        result = prompt_ready(prompt, priority_prompt = True, additional_vocab = additional_vocab)
        if result == 'override' :
            if self._override:
                self._override = False
            else:
                self._override = True
            self.next_state = ASSIGNMENT_DELIVER_LOAD

class_factory.set_override(DeliverAssignmentTask, DeliveryAssignmentTask_Custom)