#
# Copyright (c) 2010 Vocollect, Inc.
# Pittsburgh, PA 15235
# All rights reserved.
#
# This source code contains confidential information that is owned by
# Vocollect, Inc. and may not be copied, disclosed or otherwise used without
# the express written consent of Vocollect, Inc.
# 

class RunnerTask(object):
    ''' Object that contains the task and information about the task on stack
    '''
    def __init__(self, obj, name, id): #@ReservedAssignment
        self.obj = obj
        self.name = name
        self.id = id

class Launch(Exception):
    ''' Specific exception class used to flow control of tasks '''
    def __init__(self):
        self.action="launch"

class TaskRunnerBase(object):
    ''' Main object for running tasks objects '''
    
    _main_runner = None

    @classmethod
    def get_main_runner(cls):
        return cls._main_runner
    
    ### Initialize method - Sets task stack and task ### 
    def __init__(self):
        '''Constructor'''
        self.task_stack = []
        self.run_app = True
        self.app_name = ""

        self.initialize()
        self.global_running = False
        
    def initialize(self):
        ''' Abstract method for extending classes to override. 
        Called from constructor '''
        pass
    
    def execute(self):
        ''' Main method to start running '''
        
        #if no current runner, then make this instance the main runner
        if TaskRunnerBase._main_runner is None:
            TaskRunnerBase._main_runner = self
            
        #loop while runapp variable is true
        try:
            while self.run_app:
                self.global_running = False
                try:
    
                    #check if any tasks are on the queue and run the first one
                    if len(self.task_stack) > 0:
                        task = self.task_stack[0]
                        task.obj.execute()
                        #Don't pop off until execution completes, 
                        #launch error may be throw and will need to return
                        self.task_stack.pop(0)  
                    else:
                        self.startUp()
                        
                #Catch Launch errors to 
                except Launch as err:
                    #re-raise if error is for another task runner object
                    if err.action != self.app_name:
                        raise
        finally:
            #Clear main runner, if this is main runner and exiting.
            if TaskRunnerBase._main_runner == self:
                TaskRunnerBase._main_runner = None
            
    def startUp(self):
        ''' Override this method to have runner start up properly 
        default simply shuts down runner
        '''
        self.run_app = False

    def get_current_task(self):
        ''' gets the currently running task object and returns it. 
            returns None if no running task or if global is currently running
        '''
        
        #Global word is running so return none
        if self.global_running:
            return None

        #No tasks running, so return None
        if len(self.task_stack) <= 0:
            return None

        #check if current task has a get_current_task function (a task runner object)
        #if so return it's result, otherwise return task object
        task = self.task_stack[0].obj
        if hasattr(task, 'get_current_task'):
            return task.get_current_task()
        else:
            return task
    
    def findTask(self, name, identifier = None):
        ''' Method to find and retrieve a task already running 
        
        Parameters:
            name - name of task to find
            identifier (Default=None) - optional ID of task 
            
        returns: task definition if found, otherwise None
        '''
        pos = -1
        count = 0
        for task in self.task_stack:
            if (task.name == name and identifier == task.id):
                pos = count
            count = count + 1
        
        if (pos >= 0):
            return self.task_stack[pos].obj

        return None
    
    def launch(self, task, identifer = None):
        ''' launches a task 
        
        Parameters:
            task - task object to launch
            identifier (Default=None) - ID of task if needed 
        '''
        if task is not None:
            #determine name
            name = ''
            if hasattr(task, 'name'):
                name = task.name
    
            #queue up task object
            self.task_stack.insert(0, RunnerTask(task, name, identifer))
            
        #build and raise error to stop current tasks where they are
        err = Launch()
        err.action = self.app_name
        
        raise err

    def return_to(self, task, state):
        ''' returns to the first occurrence of a task with specified name. and sets its 
        state to specified state. All tasks in stack before specified 
        task are ended and removed 
        
        Parameters:
                task - Name of task to return to
                state - state to resume in specified task
        '''

        #Remove currently running tasks until task with specified name is found
        #or all tasks removed
        while len(self.task_stack) > 0 and self.task_stack[0].name != task:
            self.task_stack.pop(0)
        
        #If task found (still on stack) pop it off and relaunch, 
        #Otherwise launch nothing
        if len(self.task_stack) > 0:
            current_task = self.task_stack.pop(0)
            if hasattr(current_task.obj, 'current_state'):
                current_task.obj.current_state = state

            self.launch(current_task.obj, 
                        current_task.id)
        else:
            self.launch(None)
    
    def _append(self, task, id = None): #@ReservedAssignment
        ''' Helper method for setting up unit tests
        NOT inteneded for normal use
        '''
        if task is not None:
            #determine name
            name = ''
            if hasattr(task, 'name'):
                name = task.name
    
            #queue up task object
            self.task_stack.append(RunnerTask(task, name, id))

    def _insert(self, task, id = None): #@ReservedAssignment
        ''' Helper method for setting up unit tests
        NOT intended for normal use
        '''
        if task is not None:
            #determine name
            name = ''
            if hasattr(task, 'name'):
                name = task.name
    
            #queue up task object
            self.task_stack.insert(0, RunnerTask(task, name, id))
        