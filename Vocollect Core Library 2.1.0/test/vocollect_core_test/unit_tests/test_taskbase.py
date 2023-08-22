import mock_catalyst #@UnusedImport
import unittest

from vocollect_core_test.base_test_case import BaseTestCaseCore #@UnusedImport - here for test framework
from vocollect_core.task.task import TaskBase

class TaskBaseSample(TaskBase):
    
    def func1(self):
        pass
    def func2(self):
        pass
    def func3(self):
        pass


class TestTaskBase(BaseTestCaseCore):

    def test_add_state(self):
        obj = TaskBaseSample(None, None)

        #--------------------------------------
        #test normal         
        obj.addState('1',  obj.func1)
        obj.addState('2',  obj.func2)
        obj.addState('3',  obj.func3)

        self.assertEqual(obj.state_functions[0], obj.func1.__name__)
        self.assertEqual(obj.state_functions[1], obj.func2.__name__)
        self.assertEqual(obj.state_functions[2], obj.func3.__name__)
        
        self.assertEqual(obj.states[0], '1')
        self.assertEqual(obj.states[1], '2')
        self.assertEqual(obj.states[2], '3')
        
        #--------------------------------------
        #test insert after         
        obj.addState('1a',  obj.func1, '1') #after first state
        obj.addState('2a',  obj.func2, '2') #after middle state
        obj.addState('3a',  obj.func3, '3') #after last state
        obj.addState('4',  obj.func3, '9') #after none existing state

        self.assertEqual(obj.state_functions[0], obj.func1.__name__)
        self.assertEqual(obj.state_functions[1], obj.func1.__name__)
        self.assertEqual(obj.state_functions[2], obj.func2.__name__)
        self.assertEqual(obj.state_functions[3], obj.func2.__name__)
        self.assertEqual(obj.state_functions[4], obj.func3.__name__)
        self.assertEqual(obj.state_functions[5], obj.func3.__name__)
        self.assertEqual(obj.state_functions[6], obj.func3.__name__)
        
        self.assertEqual(obj.states[0], '1')
        self.assertEqual(obj.states[1], '1a')
        self.assertEqual(obj.states[2], '2')
        self.assertEqual(obj.states[3], '2a')
        self.assertEqual(obj.states[4], '3')
        self.assertEqual(obj.states[5], '3a')
        self.assertEqual(obj.states[6], '4')
        
        #--------------------------------------
        #test remove state
        obj.removeState('1') #remove first state
        obj.removeState('2') #remove middle state
        obj.removeState('3') #remove middle state
        obj.removeState('4') #remove last state
        obj.removeState('9') #remove undefined state
        
        self.assertEqual(obj.state_functions[0], obj.func1.__name__)
        self.assertEqual(obj.state_functions[1], obj.func2.__name__)
        self.assertEqual(obj.state_functions[2], obj.func3.__name__)
        
        self.assertEqual(obj.states[0], '1a')
        self.assertEqual(obj.states[1], '2a')
        self.assertEqual(obj.states[2], '3a')
        
        #--------------------------------------
        #test insert state
        obj.insertState(0, '1', obj.func1) #insert at beggining
        obj.insertState(2, '2', obj.func2) #insert in middle
        obj.insertState(4, '3', obj.func3) #insert at end/invalid
        obj.insertState(99, '4', obj.func3) #insert at end/invalid
        
        self.assertEqual(obj.state_functions[0], obj.func1.__name__)
        self.assertEqual(obj.state_functions[1], obj.func1.__name__)
        self.assertEqual(obj.state_functions[2], obj.func2.__name__)
        self.assertEqual(obj.state_functions[3], obj.func2.__name__)
        self.assertEqual(obj.state_functions[4], obj.func3.__name__)
        self.assertEqual(obj.state_functions[5], obj.func3.__name__)
        self.assertEqual(obj.state_functions[6], obj.func3.__name__)
        
        self.assertEqual(obj.states[0], '1')
        self.assertEqual(obj.states[1], '1a')
        self.assertEqual(obj.states[2], '2')
        self.assertEqual(obj.states[3], '2a')
        self.assertEqual(obj.states[4], '3')
        self.assertEqual(obj.states[5], '3a')
        self.assertEqual(obj.states[6], '4')
        
if __name__ == "__main__":
    unittest.main()