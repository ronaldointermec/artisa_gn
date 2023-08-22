#
# Copyright (c) 2010 Vocollect, Inc.
# Pittsburgh, PA 15235
# All rights reserved.
#
# This source code contains confidential information that is owned by
# Vocollect, Inc. and may not be copied, disclosed or otherwise used without
# the express written consent of Vocollect, Inc.
#
# The purpose of this module is to allow for customizations of voice applications
# by providing a means of constructing custom classes in places of core
# classes. This functionality is only useful if base application uses the get() method
# to construct its objects 

__overrides = {}

def get(class_ref):
    ''' 
        Get the specified class reference.
        If an override class was defined, return the override class.
        Otherwise just return class passed in.
        @param the requested type.
     '''
    if class_ref.__name__ in __overrides:
        return __overrides[class_ref.__name__]
    
    return class_ref
        
def set_override(class_orig, class_new):
    ''' 
        Sets an override for a class so this factory returns a reference to 
        class_new when get(class_orig) is called and instances of type class_new 
        are returned when obj_factory.get(class_orig) is called.
        @param class_orig the type to override
        @param class_new the overriding type
    '''
    global __overrides
    __overrides[class_orig.__name__] = class_new
