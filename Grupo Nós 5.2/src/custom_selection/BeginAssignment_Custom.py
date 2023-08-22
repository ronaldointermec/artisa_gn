from vocollect_core import class_factory
from selection.BeginAssignment import BeginAssignment
from vocollect_core.dialog.functions import prompt_ready
from vocollect_core import itext
from custom_selection.SharedConstants import POSTION_PROMPT_LIST

class BeginAssignment_Custom(BeginAssignment):
    
    #----------------------------------------------------------
    def summmary_prompt(self):
        ''' speak the summary prompt for all the assignments '''
        
        for assignment in self._assignment_lut:
            prompt = ''
            #check if override prompt set, that one was given
            if assignment['summaryPromptType'] == 2 and assignment['overridePrompt'] == '':
                assignment['summaryPromptType'] = 0
            
            #build prompt
            if assignment['summaryPromptType'] == 0: #Default Prompt
                prompt_key = 'summary.prompt'
                prompt_values = [assignment['idDescription']]
                #check if chase
                if assignment['isChase'] == '1': 
                    prompt_key += '.chase'
                
                #check if multiple assignments
                if len(self._assignment_lut) > 1:
                    prompt_key += '.position'
                    prompt_values.insert(0, POSTION_PROMPT_LIST[''+ assignment['position'] + ''])
                
                #check if goal time
                if assignment['goalTime'] != 0:
                    prompt_values.append(assignment['goalTime'])
                    if assignment['goalTime'] == 1:
                        prompt_key += '.goaltime.single'
                    else:
                        prompt_key += '.goaltime.multi'

                prompt = itext(prompt_key, *prompt_values)

            elif assignment['summaryPromptType'] == 2: #OverridePrompt
                prompt = assignment['overridePrompt']
                
            if prompt != '': #May be blank is summaryPromptType = 1
                prompt_ready(prompt, True)
    
    
class_factory.set_override(BeginAssignment, BeginAssignment_Custom)