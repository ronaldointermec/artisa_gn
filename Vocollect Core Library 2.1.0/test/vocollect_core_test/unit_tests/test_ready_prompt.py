import unittest
import mock_catalyst
from vocollect_core_test.base_test_case import BaseTestCaseCore
from vocollect_core.dialog.functions import prompt_ready, prompt_words,\
    prompt_yes_no, prompt_yes_no_cancel

class TestReadyPrompt(BaseTestCaseCore):

    def setUp(self):
        self.clear()

    def test_prompt_ready_priority(self):
        self.post_dialog_responses('ready')
        result = prompt_ready('Test prompt', priority_prompt = True)
        self.assertEqual(result, 'ready')
        self.validate_prompts(['Test prompt', True])
        
        self.post_dialog_responses('ready')
        result = prompt_ready('Test prompt', priority_prompt = False)
        self.assertEqual(result, 'ready')
        self.validate_prompts(['Test prompt', False])
        
    def test_prompt_ready_additional_vocab(self):
        #test passing in a string, no confirm
        mock_catalyst.all_vocab.append('vocab1')
        mock_catalyst.all_vocab.append('vocab2')

        self.post_dialog_responses('vocab1')
        result = prompt_ready('Test prompt', additional_vocab='vocab1')
        self.assertEqual(result, 'vocab1')
        self.validate_prompts(['Test prompt', False])
        
        #test passing in a list, no confirm, invalid vocab ignored
        self.post_dialog_responses('vocab3', 'vocab1')
        result = prompt_ready('Test prompt', additional_vocab=['vocab1', 'vocab3'])
        self.assertEqual(result, 'vocab1')
        self.validate_prompts(['Test prompt', False])
        
        #test passing in a dict, some confirm, invalid vocab ignored
        self.post_dialog_responses('vocab3', #ignored 
                                   'vocab1', 'no', #confirm with false
                                   'vocab2') #no confirm should be returned
        result = prompt_ready('Test prompt', 
                              additional_vocab={'vocab1' : True, 
                                                'vocab2' : False,
                                                'vocab3' : True})
        self.assertEqual(result, 'vocab2')
        self.validate_prompts(['Test prompt', False],
                              ['vocab1, correct?', False],
                              ['Test prompt', False])

    def test_prompt_ready_skip_prompt(self):
        self.post_dialog_responses('ready')
        result = prompt_ready('test prompt', skip_prompt=True)
        self.assertEqual(result, 'ready')
        self.validate_prompts()
        
    def test_prompt_words(self):
        #This test added here since prompt words is same as prompt ready without the ready
        self.post_dialog_responses('ready',     #should be ignored since removed
                                   'vocab3',    #should be ignored, invalid vocab
                                   'vocab2')    #result value
        result = prompt_words('Test prompt', additional_vocab=['vocab1', 'vocab2', 'vocab3'])
        
        self.assertEqual(result, 'vocab2')
        self.validate_prompts(['Test prompt', False])
        
    def test_yes_no_prompt(self):
        #Test response yes
        self.post_dialog_responses('yes')
        result = prompt_yes_no('Test prompt', False)
        self.assertEqual(result, True)
        self.validate_prompts(['Test prompt', False])
        
        #Test response No
        self.post_dialog_responses('no')
        result = prompt_yes_no('Test prompt', True)
        self.assertEqual(result, False)
        self.validate_prompts(['Test prompt', True])
        
    def test_yes_no_cancel(self):
        #Test response yes
        self.post_dialog_responses('yes')
        result = prompt_yes_no_cancel('Test prompt', False)
        self.assertEqual(result, 'yes')
        self.validate_prompts(['Test prompt', False])
        
        #Test response No
        self.post_dialog_responses('no')
        result = prompt_yes_no_cancel('Test prompt', True)
        self.assertEqual(result, 'no')
        self.validate_prompts(['Test prompt', True])
        
        #Test response Cancel not in vocab
        self.post_dialog_responses('cancel', 'no') #cancel ignored if not in vocab
        result = prompt_yes_no_cancel('Test prompt', True)
        self.assertEqual(result, 'no')
        self.validate_prompts(['Test prompt', True])

        #Test response Cancel in vocab
        mock_catalyst.all_vocab.append('cancel')
        self.post_dialog_responses('cancel') 
        result = prompt_yes_no_cancel('Test prompt', True)
        self.assertEqual(result, 'cancel')
        self.validate_prompts(['Test prompt', True])

if __name__ == "__main__":
    unittest.main()

