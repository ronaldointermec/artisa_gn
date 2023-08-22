from vocollect_core import class_factory, obj_factory
from vocollect_core.dialog.functions import prompt_ready, prompt_only, prompt_yes_no
from selection.SelectionVocabulary import SelectionVocabulary
from vocollect_core import itext
from selection.ReviewContents import ReviewContents
from selection.SelectionPrint import SelectionPrintTask
from custom_selection.SharedConstants import POSTION_PROMPT_LIST

class SelectionVocabulary_Custom(SelectionVocabulary):
    
    def _review_cluster(self):
        '''review cluster loops through assignments and reviews'''        
        if self.region_config_rec['containerType'] == 0 or self.assignment_lut.has_multiple_assignments() == False:
            prompt_only(itext('selection.review.cluster.not.valid'))
        else:
            if prompt_yes_no(itext('selection.review.cluster.confirm')):
                for assignment in self.assignment_lut:
                    prompt_ready(itext('selection.review.cluster.prompt', assignment['idDescription'], POSTION_PROMPT_LIST[''+ assignment['position'] +'']))
                    
        return True
    
    def _review_contents(self):
        '''review contents'''        
        if self.region_config_rec['containerType'] == 0:
            prompt_only(itext('selection.review.content.not.valid'))
        else: 
            if prompt_yes_no(itext('selection.review.contents.confirm')):
                current_task = self.runner.get_current_task()
                current_task.launch(obj_factory.get(ReviewContents,
                                                      self.region_config_rec,
                                                      self.assignment_lut[0], 
                                                      self.container_lut,
                                                      current_task.taskRunner, 
                                                      current_task), 
                                    current_task.current_state)
        return True
    
    def _reprint_labels(self):
        '''launch reprint label task'''
        if self.region_config_rec['printLabels'] == '0' and self.assignment_lut[0]['isChase'] == '0' or \
            self.region_config_rec['printChaseLabels'] == '0' and self.assignment_lut[0]['isChase'] == '1':
            prompt_only(itext('selection.reprintlabel.not.allowed'))
        else:
            if prompt_yes_no(itext('selection.reprint.labels.confirm')):
                current_task = self.runner.get_current_task()
                current_task.launch(obj_factory.get(SelectionPrintTask,
                                                      self.region_config_rec, 
                                                      self.assignment_lut[0], 
                                                      self.container_lut,  1,
                                                      current_task.taskRunner, current_task), 
                                    current_task.current_state)
        return True
class_factory.set_override(SelectionVocabulary, SelectionVocabulary_Custom)