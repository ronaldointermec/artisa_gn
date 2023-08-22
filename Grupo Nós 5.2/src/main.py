from custom_selection import PickPrompt_Custom #@UnusedImport
from custom_selection import BeginAssignment_Custom #@UnusedImport
from custom_selection import SelectionVocabulary_Custom #@UnusedImport
from custom_selection import OpenContainer_Custom #@UnusedImport
from custom_selection import DeliverAssignment_Custom #@UnusedImport
from custom_selection import SelectionLuts_Custom #@UnusedImport
from custom_selection import ReviewContents_Custom #@UnusedImport
from core.VoiceLink import VoiceLink

from vocollect_http.httpserver import server_startup
from httpserver_receiving import ReceivingVoiceAppHTTPServer


#dummy ODR to get ODR queue working on startup
from common.VoiceLinkLut import VoiceLinkOdr, lut_def_files
from vocollect_core.utilities.localization import itext
from vocollect_core.utilities import obj_factory
from vocollect_core import scanning
from voice import get_voice_application_property
import voice
from communications.async_http_request import HTTPODRThread
from vocollect_core.utilities.pickler import register_pickle_obj

#set override lut definitions
lut_def_files.append('LUTDefinition_custom.properties')

def main():
    # load all properties for the currently loaded language
    itext('')

    # Enabling triggered scanning
    use_trigger_scan_vocab = get_voice_application_property('UseTriggerScanVocab')

    voice.log_message("Use Trigger scan vocab value is : "+use_trigger_scan_vocab)
    if use_trigger_scan_vocab == 'true':
        trigger_scan_timeout = int(get_voice_application_property('TriggerScanTimeout'))
        scanning.set_trigger_vocab('VLINK_SCAN_VOCAB')
        scanning.set_trigger_timeout(trigger_scan_timeout)

    server_startup(ReceivingVoiceAppHTTPServer)
    runner = obj_factory.get(VoiceLink)
    runner = register_pickle_obj('VoiceLink', runner)

    # start up the OdrArchive or HTTPODRThread after registering the pickle object
    if get_voice_application_property('useLutOdr') == 'true':
        dummyODR = obj_factory.get(VoiceLinkOdr, 'dummy')
    else:
        HTTPODRThread.start_up()

    runner.execute()

