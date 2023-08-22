import voice

try:
    # collect_data was introduced in VoiceCatalyst 4.0
    from voice import collect_data as dcm_collect_data #@UnresolvedImport
except ImportError:
    # if not present on earlier versions, send data to device log
    from voice import log_message as dcm_collect_data

try:
    # json was introduced in VoiceCatalyst 1.2
    import json #@UnresolvedImport
    _has_json = True
except ImportError:
    # if not present, neither is voice.collect_data
    # any object passed in will be cast to a string and logged
    _has_json = False

# check task package setting before sending to the conditionally defined voice function
enabled = voice.get_voice_application_property('DataCollectionEnabled') == 'true'


def collect_data(json_serializable_object):
    ''' Forward data to the DCM if data collection is enabled.
    json_serializable_object: a Python object that can be json serialized
    '''
    #Only post if collection is turned on
    if enabled:
        if _has_json:
            try:
                dcm_collect_data(json.dumps(json_serializable_object))
            except Exception as e:
                # log errors if a non-JSON serializable object is passed in despite the parameter name
                voice.log_message('DCM: Unable to collect data: %s: %s' % (type(e), e))
        else:
            dcm_collect_data(str(json_serializable_object))
