#
# Copyright (c) 2010-2012 Vocollect, Inc.
# Pittsburgh, PA 15235
# All rights reserved.
#
# This source code contains confidential information that is owned by
# Vocollect, Inc. and may not be copied, disclosed or otherwise used without
# the express written consent of Vocollect, Inc.
#

from vocollect_core.utilities.util_methods import multiple_scans_supported
import threading
import voice

# The A730's imager supports using the same callback more than once
# Note: if VoiceCatalyst provides a method to determine
# if the scan came from the A730 imager or an external scanner,
# this could instead check the source of the scan (RBIRDCLI-2200)
try:
    DEVICE_IS_A730 = voice.getenv('Device.Subtype', '<N/A>').lower().startswith('a730')
except:
    DEVICE_IS_A730 = False
try:
    EXTERNAL_WITH_A730 = 'true' == voice.get_voice_application_property('UsingExternalScannerWithA730')
except:
    EXTERNAL_WITH_A730 = False

#Scan mode definitions
class ScanMode(object):
    Off = 0
    Single = 1
    Multiple = 2

    @classmethod
    def convert_mode(cls, value):
        ''' Checks the data type of value and converts it to and returns valid scan mode
            if type or mode is not valid, then scan mode is returned as Off
        '''
        if type(value) == bool:
            return ScanMode.Single if value else ScanMode.Off
        elif type(value) == int:
            return value if value in [ScanMode.Off, ScanMode.Single, ScanMode.Multiple] else ScanMode.Off

        return ScanMode.Off

#global variable for scan result
scan_results = []
scan_mode = ScanMode.Off
scan_data_lock = threading.RLock()
scan_mode_lock = threading.RLock()
scan_post_process_callback = None
trigger_scan_vocab = ""
trigger_scan_timeout = 5


def set_trigger_vocab(vocabulary):
    ''' sets a globally used vocab word that will trigger scanner when in a
        core dialog with scanning enabled (only works for supported scanners)
    '''
    global trigger_scan_vocab
    trigger_scan_vocab = vocabulary

def get_trigger_vocab():
    ''' gets the globally used vocab word that will trigger scanner
    '''
    global trigger_scan_vocab
    return trigger_scan_vocab

def set_trigger_timeout(timeout):
    ''' set the timeout interval for a triggered scan. This is the amount of
        time scanner will stay on trying to scan something before stopping.
    '''
    global trigger_scan_timeout
    trigger_scan_timeout = timeout

def auto_trigger_scanner(timeout = None):
    ''' Triggers the scanner if running on a catalyst version that support it
    Parameters:
        timeout - Number of second to leave scanning if no bar code is scanned
                    None - use global property
    '''
    global trigger_scan_timeout
    if hasattr(voice, "trigger_scanner"):
        #Determine whether to use local or global timeout
        local_timeout = trigger_scan_timeout
        if timeout is not None:
            local_timeout = timeout

        try:
            voice.trigger_scanner(local_timeout)
        except Exception as err:
            voice.log_message('AUTO SCAN: Error triggering scanner: ' + str(err))

def scan_callback(value):
    '''Main scan call back method. Adds value to queue for later reference
       then re-registers itself if rapid scanning to get next barcode

    Parameters:
        value - the value that was scanned in returned in this parameter
    '''
    global scan_results, scan_data_lock, scan_mode_lock, scan_mode, DEVICE_IS_A730, EXTERNAL_WITH_A730

    # prevent a race condition in rapid scanning within the same dialog
    with scan_mode_lock:
        #save value to list of scanned values
        with scan_data_lock:
            scan_results.append(value)

        if scan_mode == ScanMode.Multiple and multiple_scans_supported():
            # use the same callback for the A730 unless an external scanner is attached
            if DEVICE_IS_A730 and not EXTERNAL_WITH_A730:
                pass
            else:
                voice.set_scan_callback(None)
                voice.set_scan_callback(scan_callback)
        else:
            # treat ScanMode.Multiple as ScanMode.Single if not supported
            voice.set_scan_callback(None)
            scan_mode = ScanMode.Off

def get_scan_mode():
    ''' returns the current scanning mode '''
    global scan_mode
    return scan_mode

def set_scan_mode(requested_scan_mode, auto_trigger = False):
    ''' Turns scanning on or off based on the requested_scan_mode.

    Parameters:
        requested_scan_mode - The mode to set scanning too.
            ScanMode.Off - turns the scanning off and clears and queued up/unused scans
            ScanMode.Single - Turns scanning on and clears the queue of any previous scans
                              (legacy behavior)
            ScanMode.Multiple - If not already in Multiple mode, then the queue is
                                reset to prepare it for rapid/multiple scanning,
                                and scanning it turned on. If already turned on and
                                in Multiple mode then passing this in again has no affect
        auto_trigger - Will automatically trigger the scanner (Only works with certain scanners)
    '''
    global scan_results, scan_data_lock, scan_mode_lock, scan_mode

    # prevent a race condition in scan_callback from turning off the scanner
    # after this skips turning it on because it is already on
    with scan_mode_lock:
        #Turn off scanning
        if requested_scan_mode == ScanMode.Off:
            if scan_mode != ScanMode.Off:
                voice.set_scan_callback(None)
            scan_mode = ScanMode.Off
            with scan_data_lock:
                del scan_results[:]

        #Turn on single scanning for prompt
        elif requested_scan_mode == ScanMode.Single:
            if scan_mode != ScanMode.Single:
                if scan_mode != ScanMode.Off:
                    voice.set_scan_callback(None)
                scan_mode = ScanMode.Single
                voice.set_scan_callback(scan_callback)
                with scan_data_lock:
                    del scan_results[:]

        #Turn on multiple scanning
        elif requested_scan_mode == ScanMode.Multiple:
            #only start if not already started
            if scan_mode != ScanMode.Multiple:
                if scan_mode != ScanMode.Off:
                    voice.set_scan_callback(None)
                scan_mode = ScanMode.Multiple
                voice.set_scan_callback(scan_callback)
                with scan_data_lock:
                    del scan_results[:]

        if auto_trigger:
            auto_trigger_scanner()


def get_scan_result():
    ''' Gets the next scanned value, parses it if parsing callback function
        is registered and returns result. Returns none of no value was scanned
    '''
    global scan_results, scan_post_process_callback, scan_data_lock
    result = None

    #get a scan value from the queue if one is there
    with scan_data_lock:
        if len(scan_results) > 0:
            result = scan_results.pop(0)

    #if a parsing call back method is registered, then called it and return
    #result from that registered method
    if scan_post_process_callback != None and result != None:
        result = scan_post_process_callback(result)

    return result

def scan_results_exist():
    ''' Check if there are any queued up scan results and returns True
        if there are, otherwise returns false
    '''
    with scan_data_lock:
        result = len(scan_results) > 0
    return result

def set_scan_post_process_callback(post_process_function = None):
    ''' Set a post process call back method if scanned value require parsing before
        they are returned

        post_process_function - funtion to call with scan value to do some post
            processing on it before it is returned. None will un set the call back
    '''
    global scan_post_process_callback
    scan_post_process_callback = post_process_function
