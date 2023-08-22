#
# Copyright (c) 2010 Vocollect, Inc.
# Pittsburgh, PA 15235
# All rights reserved.
#
# This source code contains confidential information that is owned by
# Vocollect, Inc. and may not be copied, disclosed or otherwise used without
# the express written consent of Vocollect, Inc.
# 

import voice

class IOWrapper(object):
    ''' Simple class to wrap IO objects that return bytes instead 
    of strings. This class wraps that object and returns string to
    read, readline and readlines functions.  
    '''
    def __init__(self, io_object, encoding = 'utf-8'):
        self.wrapped = io_object
        self.encoding = encoding
        self.mode = 'r'
        
    def read(self, size = None):
        return self._convert(self.wrapped.read(size))
    
    def readline(self):
        return self._convert(self.wrapped.readline())
        
    def readlines(self):
        result = []
        while True:
            line = self.readline()
            if not line: break
            result.append(line)
        return result

    def __iter__(self):
        return self

    def __next__(self):
        nextline = self.readline()
        if not nextline:
            raise StopIteration()

        return nextline
    
    def _convert(self, result):
        try:
            if type(result) != str:
                return result.decode(self.encoding)
        except Exception as err:
            voice.log_message('CORE LIB: IOWrapper error in ' + self.encoding + ' conversion: ' + str(err))
        
        #does not need converted, or error converting
        return result
        
