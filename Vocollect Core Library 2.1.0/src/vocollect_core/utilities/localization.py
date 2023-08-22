#
# Copyright (c) 2010 Vocollect, Inc.
# Pittsburgh, PA 15235
# All rights reserved.
#
# This source code contains confidential information that is owned by
# Vocollect, Inc. and may not be copied, disclosed or otherwise used without
# the express written consent of Vocollect, Inc.
# 

from voice import open_vad_resource, log_message, getenv
from . import property_file

_resources = None
_language_code = ''

#===========================================
#prompts
#===========================================
def itext(key, *args):
    ''' get text from resource files based on specified key 
    Parameters
            key - resource key to lookup
            *args - variable number of values to substitute
            
    returns: text from resource
    '''
    global _resources, _language_code
    
    #get current language code from client
    lan_code = getenv('SwVersion.Locale', 'en_US') 
    
    #load prompts if needed
    if _resources is None or lan_code != _language_code:
        load_prompts(lan_code)

    #lookup key, if not found, set text to key 
    text = _resources[key]
    if text == '':
        text = key

    #try to substitute tags with args
    try:
        #first try standard python type substitutions
        if len(args) == 1 and type(args[0]) == dict:
            text = text % args[0]
        else:
            text = text % args
    except:
        #Second try {i} type substitutions 
        try:
            for i in range(len(args)):
                text = text.replace('{' + str(i) + '}', str(args[i]))
        except:
            text = text
            
        #convert double percents to just a percent
        text = text.replace('%%', '%')
        
    return text


FILE_NAME = 0
FILE_DEPTH = 1
FILE_LANGUAGE =2

def load_prompts(locale = "en_us"):
    ''' loads prompts resource file based on specified language code
    Parameters:
            locale (Default=en_US) - locale to load
            
    '''
    global _resources, _language_code
    
    #initiate or clear current resources            
    if _resources is None:
        _resources = property_file.Properties()
    else:
        _resources.getPropertyDict().clear()
    _language_code = locale

    #set to lower case for matching later
    locale = locale.lower()

    #open and parse files manifest file
    manifest_file = open_vad_resource('manifest.mf')
    files = []
    for line in manifest_file:
        fields = line.split('|')
        file = fields[0]
        depth = len(fields)
        language_code = ''
        
        #check only for .properties files in translation folder
        if ((file[0:13] == 'translations\\' or file[0:13] == 'translations/')
            and file[len(file)-11:len(file)] == '.properties'):

            #determine language code of file
            first_under_score = file[len(file)-17:len(file)-16]
            second_under_score = file[len(file)-14:len(file)-13]
            
            if first_under_score == '_' and second_under_score == '_':
                language_code = file[len(file)-16:len(file)-11]
            elif second_under_score == '_':
                language_code = file[len(file)-13:len(file)-11]

            language_code = language_code.lower()
            
            #only add files that match language to be loaded
            if (language_code == '' or language_code == locale or 
                language_code == locale[0:2]):
                files.append([file, depth, language_code])


    #sort files in order that they should be read
    #   1. default, language only, language with country code
    #   2. Deepest first out to main project
    #   3. File name alphabetically
    files.sort(key = lambda i: (i[FILE_LANGUAGE], i[FILE_DEPTH] * -1, i[FILE_NAME]))
    
    #read in each file in order now specified from sort
    for file in files:
        try:
            _resources.load(open_vad_resource(file[FILE_NAME]))
        except Exception as err:
            log_message('CORE LIB: ERROR in Localization: Error reading file '
                        + file[FILE_NAME] + '   Message:'
                         + str(err))

def key_value_tag_count(key):
    ''' returns the number of tags in the value associated with the key
     
    Parameters:
            key - the key to look up
    '''
    prompt = itext(key)
    return prompt.count('%s') + prompt.count('{')
