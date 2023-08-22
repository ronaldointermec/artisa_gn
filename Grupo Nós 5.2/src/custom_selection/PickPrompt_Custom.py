from vocollect_core import class_factory,obj_factory
from selection.SharedConstants import LOT_TRACKING, XMIT_PICKS, ENTER_QTY, PICK_PROMPT_TASK_NAME, INTIALIZE_PUT,PUT_PROMPT
from selection.PickPrompt import PickPromptTask
from selection.LotTracking import LotTrackingTask
from vocollect_core.dialog.functions import prompt_list_lut,prompt_only,prompt_yes_no,prompt_alpha_numeric
from common.VoiceLinkLut import VoiceLinkLut,VoiceLinkLutOdr
from vocollect_core import itext
from custom_selection.SharedConstants import GET_REASON_CODE, POSTION_PROMPT_LIST
    
class PickPromptTask_Custom(PickPromptTask):
    
    #----------------------------------------------------------
    def __init__(self, 
                 region,  
                 assignment_lut, 
                 picks, 
                 container_lut,
                 auto_short,
                 taskRunner = None, 
                 callingTask = None):
        super(PickPromptTask, self).__init__(taskRunner, callingTask)

    #Set task name
        self.name = PICK_PROMPT_TASK_NAME

        #Luts and lut records       
        self._region = region
        self._assignment_lut = assignment_lut
        self._container_lut = container_lut
        
        #Picked LUT/ODR
        self._picked_lut = VoiceLinkLutOdr('prTaskLUTPicked', 'prTaskODRPicked', self._region['useLuts'])
        
        self._reason_code_lut = obj_factory.get(VoiceLinkLut, 'prTaskLUTCoreGetReasonCodes')
        self._reason_code = ''
        #Configure Object
        self.config(picks, auto_short)
        
    #----------------------------------------------------------
    def config(self, picks, auto_short):
        self.current_state = None
        self.next_state = None
        self.previous_state = None
        
        self._picks = picks
        self.dynamic_vocab.set_pick_prompt_task(self.name)
        
        #main variables
        self._expected_quantity = 0
        self._picked_quantity = 0
        self._short_product = False
        self._partial = False
        
        for pick in self._picks:
            self._expected_quantity += (pick['qtyToPick'] - pick['qtyPicked'])
       
        #lot tracking variables
        self._lot_number = None
        self._lot_quantity = 0

        #put variables
        self._put_quantity = 0
        self._curr_assignment = None
        self._curr_container = None
        self._puts = []
        
        #weights and serial numbers
        self._weights = []
        self._serial_numbers = []
        
        #Initialize commonly used variables
        self._uom = ''
        self._message = ''
        self._description = ''
        self._id_description = ''
        self._pvid = ''
        self._set_variables()
        self._skip_prompt = False
        
        #check if auto shorting
        if auto_short:
            self.current_state = INTIALIZE_PUT
            self._set_short_product(0)
        
    
    #----------------------------------------------------------
    def initializeStates(self):
        super().initializeStates()
        self.addState(GET_REASON_CODE, self.get_reason_code, LOT_TRACKING)
        
    #----------------------------------------------------------
    def get_reason_code(self):
        ''' if exception occurred then get reason '''
        self._reason_code = ''
        if self._short_product:
            if self._picked_quantity < self._expected_quantity:
                result = self._reason_code_lut.do_transmit('6', '1')
                if result != 0:
                    self.next_state = GET_REASON_CODE
                elif len(self._reason_code_lut) == 1: #only 1 returned so use it (even if blank)
                    self._reason_code = self._reason_code_lut[0]['code']
                else:
                    self._reason_code = prompt_list_lut(self._reason_code_lut, 
                                                        'code', 'description',
                                                        itext('selection.pick.prompt.short.reason'), 
                                                        itext('selection.pick.prompt.short.reason.help'))
            self._short_product = False
            self._set_short_product(self._picked_quantity)
        
    #------------------------------------------------------------                    
    def _set_short_product(self, quantity):
        self._expected_quantity = quantity
        self._picked_quantity = quantity
        self._lot_quantity = quantity
        self._put_quantity = quantity
        self._last_quantity = quantity
        
    #----------------------------------------------------------
    def verify_entered_quantity(self):
        '''verifies the entered quantity'''
        #If the quantity verification is set prompt for quantity     
        if(self._picked_quantity > self._expected_quantity):
            prompt_only(itext("selection.pick.prompt.pick.quantity.greater", self._picked_quantity, self._expected_quantity))
            self.next_state = ENTER_QTY
        
        #check if quantity less than expected                                   
        elif self._picked_quantity <= self._expected_quantity and not self._partial:

            #if already doing a short product, then confirm spoken quantity
            if self._short_product:
                if prompt_yes_no(itext("selection.pick.prompt.short.product.verify",  self._picked_quantity)):
                    self._short_product = False
                    self._set_short_product(self._picked_quantity)
                else:
                    self.next_state = ENTER_QTY
            
            
            #not doing short, but quantity less than expected, ask if short
            elif self._picked_quantity < self._expected_quantity:
                self._short_product = prompt_yes_no(itext("selection.pick.prompt.pick.quantity.less",  
                                                          self._picked_quantity, 
                                                          self._expected_quantity ),
                                                    True, 6)
                if self._short_product:
                    self.next_state = GET_REASON_CODE                   
                else:
                    self.next_state = ENTER_QTY
                    
        #quantity 0 and partial spoken
        elif self._picked_quantity == 0 and self._partial:
            prompt_only(itext('selection.pick.prompt.pick.quantity.zero'))
            self.next_state = ENTER_QTY
            self._partial = False
    #---------------------------------------------------------   
    def lot_tracking(self):
        '''Lot tracking'''
        # 150123-000009 preserve the last pick location total quantity picked
        self._last_quantity = self._picked_quantity
        
        if self._picked_quantity > 0 and self._picks[0]['captureLot']:
            self._lot_quantity=0
            self.launch(obj_factory.get(LotTrackingTask,
                                          self._region, self._assignment_lut,
                    self._picks, self._picked_quantity, 
                    self.taskRunner, self))
        else:
            self._lot_quantity = self._picked_quantity
            
    #---------------------------------------------------------   
    def put_prompt(self):
        '''Put Prompt'''

        expected_values = []
        scan_value = ''     
        
        #Do put prompt if multiple assignment or multiple open containers
        if (self._assignment_lut.has_multiple_assignments() or 
            self._container_lut.multiple_open_containers(self._curr_assignment['assignmentID'])):

            open_containers = self._container_lut.get_open_containers(self._curr_assignment['assignmentID'])

            # determine what the expected container value is
            if (self._puts[0]['targetContainer'] != 0):
                if ((self._curr_assignment['activeTargetContainer'] == self._puts[0]['targetContainer']) or
                    (len(open_containers) == 1)):
                    expected_values.append(open_containers[0]['spokenValidation'])
                    scan_value = open_containers[0]['scannedValidation']
                    
            elif (len(open_containers) == 1):
                expected_values.append(open_containers[0]['spokenValidation'])
                scan_value = open_containers[0]['scannedValidation']
                
                
            #indicates at put prompt
            dynamic_vocab = {}
            if not self._partial and self._assignment_lut.has_multiple_assignments():
                dynamic_vocab['partial'] = False
                
            #determine prompts
            if self._container_lut.multiple_open_containers(self._curr_assignment['assignmentID']):
                prompt = itext('selection.put.prompt.for.container')
            elif self._partial:
                prompt = itext('selection.put.prompt.for.container')
            else:
                prompt = itext('selection.put.prompt.for.container.multiple', 
                                    self._put_quantity, POSTION_PROMPT_LIST[''+ self._curr_assignment['position'] + ''])
                
            spokenContainerLen = 1

            result = prompt_alpha_numeric(prompt,
                                          itext('selection.put.prompt.for.container.help'),
                                          spokenContainerLen,
                                          spokenContainerLen,
                                          confirm = False,
                                          scan = len(scan_value) > 0,
                                          additional_vocab = dynamic_vocab,
                                          priority_prompt = True,
                                          hints = expected_values)
            if len(scan_value) > 0:
                # unpack separately returned values
                result, scanned = result
            else:
                # no scan provided
                scanned = False

            if result == 'partial':
                self.next_state = PUT_PROMPT
                if self._validate_partial(self._put_quantity, True):
                    self._get_partial_quantity()
            else:
                if not self._validate_container(result, scanned):
                    self.next_state = PUT_PROMPT
        else:
            #should only be 1 open container for assignment
            self._validate_container(None, False)
            
    #----------------------------------------------------------
    def _validate_container(self, containerId, scanned):
        '''validate spoken containers or scanned container is correct'''
        
        #check for single open container
        if containerId == None:
            containers = self._container_lut.get_open_containers(self._curr_assignment['assignmentID'])
            if len(containers) > 0:
                self._curr_container = containers[0]
        
        elif self._puts[0]['targetContainer'] == 0:
            open_container = self._container_lut.match_open_container(containerId, 
                                                                      self._curr_assignment['assignmentID'], 
                                                                      scanned)
            if open_container is None:
                prompt_only(itext('selection.put.prompt.wrong.container', containerId))
                return False
            else:
                self._curr_container = open_container

        elif self._puts[0]['targetContainer'] > 0:
            open_container = self._container_lut.match_open_container(containerId, 
                                                                      self._curr_assignment['assignmentID'], 
                                                                      scanned)                                                                      
            if (open_container is None or 
                open_container['targetConatiner'] != self._curr_assignment['activeTargetContainer']):
                prompt_only(itext('selection.put.prompt.wrong.container', containerId))
                return False
            else:
                self._curr_container = open_container
            
        return True
        
    #----------------------------------------------------------
    def xmit_picks(self):
        '''Transmit Pick'''
         
        pick = None
        weight = None
        serial_number = None
        containerID = None
                
        #1. Find a pick to transmit
        for p in self._puts:
            if p['status'] != 'P':
                pick = p
                break

        #should not occur
        if pick is None:
            raise Exception('Unknown Error transmitting picks')
         
        #2. Determine quantity to apply, and weight and serial number, and container
        quantity = pick['qtyToPick'] - pick['qtyPicked']
        if quantity > self._put_quantity:
            quantity = self._put_quantity
            
        if quantity > 0 and (len(self._weights) > 0 or len(self._serial_numbers) > 0):
            quantity = 1
            if len(self._weights) > 0:
                weight = "%.2f" % self._weights[0]
            if len(self._serial_numbers) > 0:
                serial_number = self._serial_numbers[0]

        if self._curr_container is not None:
            containerID = self._curr_container['systemContainerID']
        
        #3. check if pick is complete (still more quantity to apply, but not applying all now)
        complete = True
        if self._picked_quantity > quantity and quantity < pick['qtyToPick'] - pick['qtyPicked']:
            complete = False
        elif self._partial and quantity < pick['qtyToPick'] - pick['qtyPicked']:
            complete = False

        #if pick isn't complete, and there is no quantity
        # then simply return and continue to next state
        # there is no reason to send Picked information
        if not complete and quantity <= 0:
            return
            
        #4. Transmit pick record
        result = self._picked_lut.do_transmit(self._curr_assignment['groupID'], 
                                              pick['assignmentID'], 
                                              pick['locationID'], 
                                              quantity, 
                                              int(complete), 
                                              containerID, 
                                              pick['sequence'], 
                                              self._lot_number,
                                              weight, 
                                              serial_number,
                                              self._reason_code)
    
        #5. Check results and update variables 
        if result < 0: # Error contacting host
            self.next_state = XMIT_PICKS 
        elif result > 0: # Error from host
            self.next_state = XMIT_PICKS
        else: #success
            #update pick information
            pick['qtyPicked'] = pick['qtyPicked'] + quantity
            if complete:
                pick['status'] = 'P'
                
            # 150123-000009 update last pick information
            self.dynamic_vocab.last_pick(self._curr_assignment['groupID'], 
                                              pick['assignmentID'], 
                                              pick['locationID'], 
                                              quantity, 
                                              int(complete), 
                                              containerID, 
                                              pick['sequence'], 
                                              self._lot_number,
                                              weight, 
                                              serial_number,
                                              self._last_quantity)
            
            #update pick quantities
            self._put_quantity -= quantity
            self._lot_quantity -= quantity
            self._picked_quantity -= quantity
            self._expected_quantity -= quantity
            if len(self._weights) > 0:
                self._weights.pop(0)
            if len(self._serial_numbers) > 0:
                self._serial_numbers.pop(0)
            
        
class_factory.set_override(PickPromptTask, PickPromptTask_Custom)
    