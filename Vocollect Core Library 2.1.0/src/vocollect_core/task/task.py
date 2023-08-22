#
# Copyright (c) 2010 Vocollect, Inc.
# Pittsburgh, PA 15235
# All rights reserved.
#
# This source code contains confidential information that is owned by
# Vocollect, Inc. and may not be copied, disclosed or otherwise used without
# the express written consent of Vocollect, Inc.
# 

from vocollect_core.data_collection import collect_data

# This supports Data Collection Module (DCM) tracking
class TaskPhase(object):
    Start = 1
    Abort = 2
    Finish = 3

class TaskBase(object):
    ''' Base class to be used for a individual tasks to be ran 
    '''
    
    def __init__(self, taskRunner = None, callingTask = None):
        '''Constructor 
        
        Parameters:
            taskRunner - The parent task runner, defaults to none
            callingTask (Default=None) - the task base class that called this task if any.
        '''
        #State variables 
        self.previous_state = None
        self.current_state = None
        self.next_state = None
        self.states = []
        self.state_functions = []
        
        #Main task runner, and calling task if there is one
        self.taskRunner = taskRunner
        self.callingTask = callingTask

        #Name of task
        self.name = ''

        #Dynamic vocabulary
        self.dynamic_vocab = None
        if callingTask is not None:
            self.dynamic_vocab = callingTask.dynamic_vocab
            
        #initialize the states
        self.initializeStates()

    def addState(self, state, function, after = None):
        ''' adds a state to the task
        
        Parameters: 
            state - Name of the state
            function - function to run for state
            after (default None) - if specified inserts new state after spcified state.
                Inserts at the end if None or not found
        '''
        if after != None:
            pos = 0
            for temp in self.states:
                if temp == after:
                    break
                pos += 1
            
            pos += 1
            self.states.insert(pos, state)
            self.state_functions.insert(pos, function.__name__)
        else:   
            self.states.append(state)
            self.state_functions.append(function.__name__)
    
    def removeState(self, state):
        ''' remove a specified state from task
        
        Parameters: 
            state - Name of the state to remove
        '''
        pos = 0
        for temp in self.states:
            if temp == state:
                break
            pos += 1

        if pos < len(self.states):        
            self.states.pop(pos)
            self.state_functions.pop(pos)

    def insertState(self, pos, state, function):
        ''' insert a state to the task at a specified position.
        inserts at end if position is not valid
        
        Parameters:
            pos - position in list to insert state
            state - Name of the state
            function - function to run for state
        '''
        if pos < len(self.states):        
            self.states.insert(pos, state)
            self.state_functions.insert(pos, function.__name__)
        else:
            self.addState(state, function)
    
    def initializeStates(self):
        ''' abstract method should be overridden 
        used to define the states of the task 
        '''
        pass
    
    def runState(self, state):
        ''' runs the specified state
        
        Parameters:
                state - state to run
                
        returns: the index of the state requested
        '''
        
        index = None
        executionState = self.current_state # save since this could change during execution
        
        try:
            #Post start of state here with any data required
            self.collect_data(self._build_dcm_data(executionState, TaskPhase.Start))
            
            # Do the actual state run
            index = self.states.index(state)
            if hasattr(self, self.state_functions[index]):
                self.current_state = state
                getattr(self, self.state_functions[index])()
                
        except Exception:
            
            #Post state was aborted
            self.collect_data(self._build_dcm_data(executionState, TaskPhase.Abort))
            raise # re-raise error so it can be caught where it was supposed to be caught

        #Post that state was finished normally
        self.collect_data(self._build_dcm_data(executionState, TaskPhase.Finish))
        
            
        return index

    def execute(self):
        ''' main method to begin the execution of the task '''
        
        #Initialize to first defined state if none are defined
        if self.current_state == None:
            self.current_state = self.states[0]

        #Loop while the current state is a valid state
        while self.current_state in self.states:
            
            #execute the function associated with the current state
            index = self.runState(self.current_state)
            
            #set next state if not already set
            if (self.next_state == None):
                index = index + 1
                if (index == len(self.states)):
                    #index = 0
                    break
                self.next_state = self.states[index]

            #set states variables
            self.previous_state = self.current_state
            self.current_state = self.next_state
            self.next_state = None
                
    def launch(self, task, returnState = None, identifer = None):
        ''' launches another task from this task
        
        Parameters:
            task - task to launch
            returnState (Default=None) - state to return to when task is 
                                    finished. Defaults to next state
            identifier (Default=None) - ID of task if needed 
        '''

        #Determine what the returning state should be
        if returnState is None:
            index = self.states.index(self.current_state)
            index += 1
            if (index >= len(self.states)):
                self.current_state = ''
            else:
                self.current_state = self.states[index]
            pass
        else:
            self.current_state = returnState
        
        #Launch the new task
        if (self.taskRunner != None):
            self.taskRunner.launch(task, identifer)
    
    def return_to(self, task, state):
        ''' returns to the first occurance of a task with specified name. and sets it 
        state to specified state. All task in stack before specified 
        task are ended and removed 
        
        Parameters:
                task - Name of task to return to
                state - state to resume in specified task
        '''
        #Launch the new task
        if (self.taskRunner != None):
            self.taskRunner.return_to(task, state)

    def _build_dcm_data(self, stateName, phase):
        ''' Override in extended classes and add additional data
            to be sent with event. Return None to not send the
            event. Result is a dictionary of key value pairs. 
                key - any string
                Value - Any object that can be turned into JSON
            Default is data with StreamName, phase, ClassName, StateName. 
        ''' 
        return None

    def _default_dcm_data(self, stateName, phase):
        ''' Return default data included in all task events
        '''
        return {'stream' : 'workflow', 
                'phase' : phase, 
                'class' : self.name, 
                'state' : stateName
                }
    
    def collect_data(self, data_to_send):
        ''' Method to send DCM event data
        
        Parameters
                data_to_send - the data. If None, nothing is sent. 
        '''
        if (data_to_send is not None):
            #post data here
            collect_data(data_to_send)

        
