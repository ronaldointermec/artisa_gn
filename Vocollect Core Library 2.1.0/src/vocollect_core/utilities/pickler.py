#
# Copyright (c) 2010 Vocollect, Inc.
# Pittsburgh, PA 15235
# All rights reserved.
#
# This source code contains confidential information that is owned by
# Vocollect, Inc. and may not be copied, disclosed or otherwise used without
# the express written consent of Vocollect, Inc.
# 
# Module is used for saving and restoring the state of a voice application
# that is based on the TaskRunner/Task architecture

import pickle
import os
import voice.atunload
from voice import log_message

name = ""
pickle_obj = None
save_state = False
try:
    save_state = voice.get_voice_application_property('SaveState') == 'true'
except Exception as err:
    log_message('PICKLER: Set Save State Error, setting to false: ' + str(err))   

log_message('PICKLER: State Saving set to: ' + str(save_state))

def pickle_object():
    ''' Pickles the registered object '''
    global name, pickle_obj, save_state

    if (save_state 
        and name != "" 
        and pickle_obj != None):
    
        try:
            output = open(name + ".pkl", 'wb')
            pickle.dump(pickle_obj, output)
            output.close()
            log_message('PICKLER: Saved state of application')
        except Exception as err:
            log_message('PICKLER: Failed to save state of application: '+ str(err))

def deletePickle():
    ''' deletes the pickled file '''
    global name
    if (save_state and name != ""):
        os.remove(name + '.pkl')
    
def register_pickle_obj(app_name, obj):
    ''' register object to be pickled, also returns obj if it can be restored, 
    otherwise returns obj passed in'''
    global name
    global pickle_obj

    tempObj = obj
    name = os.path.join(voice.get_persistent_store_path(), app_name)
    
    if save_state:
        try:
            if os.access(name+'.pkl', os.R_OK):
                pkl_file = open(name + '.pkl', 'rb')
                tempObj = pickle.load(pkl_file)
                pkl_file.close()
                deletePickle()
            else:
                log_message('PICKLER: No state file found, starting application from beginning')
            
        except Exception as err:
            log_message('PICKLER: could not restore state: ' + str(err))
            tempObj = obj
        
    pickle_obj = tempObj
    voice.atunload.register(pickle_object)
        
    return tempObj
