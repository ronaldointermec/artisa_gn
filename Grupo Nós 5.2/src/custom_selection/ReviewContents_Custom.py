from vocollect_core import class_factory
from selection.ReviewContents import ReviewContents
from vocollect_core.dialog.functions import prompt_only,prompt_alpha_numeric
from vocollect_core import itext
from selection.SharedConstants import REVIEW_PROMPT_FOR_CONTAINER

class ReviewContents_Custom(ReviewContents):

#----------------------------------------------------------
    def prompt_for_container(self):
        ''' prompt for container '''
        if self._container_lut._has_open_closed_containers():
            container_id, container_scanned = prompt_alpha_numeric(itext('selection.close.container.prompt.for.container'), 
                                              itext('selection.close.container.prompt.for.container.help'), 
                                              self._region['spokenContainerLen'], self._region['spokenContainerLen'],
                                              confirm=False,scan=True)
                    
            self.container = self._container_lut._get_container(container_id, container_scanned)
            if self.container == None:
                prompt_only(itext('selection.close.container.not.valid', container_id))
                self.next_state = REVIEW_PROMPT_FOR_CONTAINER
        else:
            # get only available container
            self.container = self._container_lut._get_container_open_closed()

class_factory.set_override(ReviewContents, ReviewContents_Custom)