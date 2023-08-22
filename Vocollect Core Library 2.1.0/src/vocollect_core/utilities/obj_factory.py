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
# by providing a means of constructing custom object classes in places of core
# classes. This functionality is only useful if base application uses the get() method
# to construct its objects 

from vocollect_core.utilities import class_factory

def get(class_ref, *args, **kwargs):
    ''' 
        Creates and returns a new instance of an object of the type specified 
        by class_ref, unless an override for the class has been defined using 
        class_factory.set_override(), in which case an instance of the
        overriding class is returned.
        @param class_ref the requested type
        @param args the arguments to pass to the class constructor.      
    '''
    return class_factory.get(class_ref)(*args, **kwargs)
       
# This function is here for back-compatibility
def set_override(class_orig, class_new): 
    ''' 
        Sets an override for a class so this factory returns instances of type class_new 
        when instances of type class_ref are requested by the get() function. 
        This method is deprecated. Use class_factory.set_override() instead in new code.
        @param class_orig the type to override
        @param class_new the overriding type
    '''
    class_factory.set_override(class_orig, class_new)
