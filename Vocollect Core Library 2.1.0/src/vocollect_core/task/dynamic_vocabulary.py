#
# Copyright (c) 2010 Vocollect, Inc.
# Pittsburgh, PA 15235
# All rights reserved.
#
# This source code contains confidential information that is owned by
# Vocollect, Inc. and may not be copied, disclosed or otherwise used without
# the express written consent of Vocollect, Inc.
# 
from voice import get_all_vocabulary_from_vad

class Vocabulary():
    '''Structure class that contains various properties of 
    a vocab used in a dynamic fashion
    '''
    def __init__(self, vocab, function=None, confirm=False, skip_prompt = False):
        '''Constructor
        
        Parameters:
            vocab - The vocabulary to treat as a dynamic vocab
            function - function to execute if user speaks vocab
            confirm - should the vocab be confirmed in core vid
            skip_prompt - should main prompt be skipped if 
                            returning after executing function 
        '''
        self.vocab = vocab
        self.confirm = confirm
        self.function = function.__name__
        self.skip_prompt = skip_prompt

class DynamicVocabulary(object):
    ''' Base class used to define additional vocabulary to be used in a task. 
    An instance of the class should be assigned to a TaskBase class's 
    dynamic_vocab property. 
    '''
    
    def __init__(self):
        ''' Constructor
        '''
        self.vocabs = {}
        self.word = None
        
    def get_vocabs(self):
        ''' Builds a dict of valid vocabulary defined in class. Each vocab must 
        have been trained in the application and the _valid method mut return true
        for vocab in order for the vocab to be included in the returned dict 
        and added to the dialog
        
        Returns: dict of valid vocabulary, keyed by the Vocabulary objects. The
        value of each entry is True/False, indicating whether or not the 
        vocab should be confirmed. (This structure is used so it matches
        the way it is done when adding additional vocab through the dialog
        convenience functions.
        '''
        all_vocab = get_all_vocabulary_from_vad()
        valid_vocabs = {}
        for vocab in list(self.vocabs.keys()):
            if (vocab in all_vocab  
                and self._valid(vocab)):
                valid_vocabs[vocab] = self.vocabs[vocab].confirm

        return valid_vocabs
            
    def _valid(self, vocab):
        ''' Override this method to determine if a specific vocabulary
        word that is defined is currently valid or not.
        
        Return: True if vocab is valid, otherwise false
        '''
        return True

    def execute_vocab(self, vocab):
        ''' executes function associated with word, returns 
        False if unknown word or should not return to main prompt'''
        self.word = self.vocabs.get(vocab) 
        if self.word is not None:
            if hasattr(self, self.word.function):
                return getattr(self, self.word.function)()
        
        return False
    
    def is_skip_prompt(self, vocab):
        ''' 
            Skip prompt indicates if prompt needs to be skipped. Returns the 
            skip_prompt value if defined for a word or false if none exists
        '''
        word = self.vocabs.get(vocab) 
        if word is not None:
            return word.skip_prompt
        else:
            return False 
        
    