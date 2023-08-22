from vocollect_core import class_factory
from selection.SelectionLuts import Containers
from custom_selection.SharedConstants import POSTION_PROMPT_LIST

class Containers_Custom(Containers):
    
    def match_open_container(self, container_to_match_id, assignmentId,  is_scanned):
        ''' Matches open container for assignment'''
        for container in self.lut_data:
            if container['assignmentID'] == assignmentId and container['status'] == 'O':
                if is_scanned:
                    if container_to_match_id == container['scannedValidation']:
                        return container
                else:
                    if container_to_match_id == POSTION_PROMPT_LIST[''+ container['spokenPutValidation']+'']:
                        return container
                          
        
        return None
class_factory.set_override(Containers, Containers_Custom)