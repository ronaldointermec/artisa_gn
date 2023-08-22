#
# Copyright (c) 2010 Vocollect, Inc.
# Pittsburgh, PA 15235
# All rights reserved.
#
# This source code contains confidential information that is owned by
# Vocollect, Inc. and may not be copied, disclosed or otherwise used without
# the express written consent of Vocollect, Inc.
#


import mock_catalyst #Should always be first
import unittest

from mock_catalyst import EndOfApplication #@UnusedImport

class BaseTestCaseCore(unittest.TestCase):
    '''This class is a base class to be used when creating test that contains common setup of test 
    as well as some helper methods for validating prompts and LUT/ODR requests''' 

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        self._obj = None

        # Initialize mock client
        mock_catalyst.use_stdin_stdout = False
        self.obj_counts = {}
        # Python 3.6.6 removed the assertSameElements from Python 3.1.2
        # assertCountEqual checks for the same elements and the count of each item,
        # use this if assertSameElements is not available
        if not hasattr(unittest.TestCase, 'assertSameElements') and hasattr(unittest.TestCase, 'assertCountEqual'):
            self.assertSameElements = self.assertCountEqual

    def tearDown(self):
        self.clear()
        super().tearDown()
    
    def clear(self):
        """ clear all data storage """
        del mock_catalyst.prompts[:]
        del mock_catalyst.response_queue[:]
        del mock_catalyst.log_messages[:]
        del mock_catalyst.input_data[:]
        del mock_catalyst.responses_to_prompts[:]

    def post_dialog_responses(self, *responses):
        mock_catalyst.post_dialog_responses(*responses)

    def validate_prompts(self, *prompts):
        '''A helper method to assist in validating a list of prompts that were encountered'''
        
        count = 0
        for prompt in prompts:
            count += 1
            recorded_prompt = None
            if len(mock_catalyst.prompts) > 0:
                try:
                    #VCE 1.2 Mock_Catalyst provides a better backward compatible pop method
                    #        but if the environment is VCE 1.1 or less, the following statement
                    #        will fail - in that case, the standard pop will work.
                    recorded_prompt = mock_catalyst.prompts.pop(0, type(prompt))
                except:
                    recorded_prompt = mock_catalyst.prompts.pop(0)
            
            if type(prompt) == str:
                self.assertEquals(recorded_prompt, prompt, 
                              "Prompt number %s: '%s' != '%s'" % (count, prompt, recorded_prompt))
            elif type(prompt) == list and type(recorded_prompt) == list:
                self.assertEquals(recorded_prompt[0], prompt[0], 
                              "Prompt number %s: '%s' != '%s'" % (count, prompt[0], recorded_prompt[0]))
                self.assertEquals(recorded_prompt[1], prompt[1], 
                              "Priority prompt number %s: '%s' != '%s'" % (count, prompt[1], recorded_prompt[1]))
            elif type(prompt) == list and type(recorded_prompt) == str:
                self.assertEquals(recorded_prompt, prompt[0], 
                              "Prompt number %s: '%s' != '%s'" % (count, prompt[0], recorded_prompt))
            else:
                self.assertTrue(False, 'Invalid prompt data type %s:' % (count))
                
        self.assertEquals(len(mock_catalyst.prompts), 0, 
                          'Still more recorded prompts: ' + str(mock_catalyst.prompts))
        self.assertEquals(len(mock_catalyst.response_queue), 0, 
                          'Not all queued responses used: ' + str(mock_catalyst.response_queue))

    def set_manual_run(self):
        ''' Called from a test case to siwtch to manual mode so test can be 
        re-recorded '''
        mock_catalyst.use_stdin_stdout = True
        #mock_catalyst.response_queue.pop()
        
