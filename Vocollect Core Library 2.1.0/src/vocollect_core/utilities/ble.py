###################################################################################################
##  Copyright (c) 2020 Honeywell International Inc. All Rights Reserved.
##  Honeywell and its product names are among the trademarks and/or service marks
##  owned by Honeywell International, Inc., or its subsidiaries.
##
##  For patent information, see http://www.hsmpats.com.
###################################################################################################
'''
Convenience functions for interfacing with Bluetooth Low Energy / Contact Tracing
exposed in VoiceCatalyst 4.3 and later.
'''
import voice

# VoiceCatalyst 4.3 release had these in voice namespace instead of voice.ble
# store a map of functions from their respective import
_ble_functions = None
try:
    from voice.ble import ble_advertise_register_callback, ble_advertise_unregister_callback, ble_advertise_set_search_key, ble_advertise_set_advertise_packet# @UnresolvedImport
    _ble_functions = {'register': ble_advertise_register_callback,
        'unregister': ble_advertise_unregister_callback,
        'search': ble_advertise_set_search_key,
        'advertise': ble_advertise_set_advertise_packet}
    voice.log_message('BLE: imported functions from voice.ble')
except:
    voice.log_message('BLE: unable to import BLE functions from voice.ble')
    try:
        from voice import ble_advertise_register_callback, ble_advertise_unregister_callback, ble_advertise_set_search_key, ble_advertise_set_advertise_packet  # @UnresolvedImport @Reimport
        _ble_functions = {'register': ble_advertise_register_callback,
            'unregister': ble_advertise_unregister_callback,
            'search': ble_advertise_set_search_key,
            'advertise': ble_advertise_set_advertise_packet}
        voice.log_message('BLE: imported functions from voice')
    except:
        voice.log_message('BLE: unable to import BLE functions from voice namespace, BLE support unavailable')


def has_ble(check_licensed = True):
    ''' determine if BLE is supported on current device
    check_licensed (True) - if True, return False if BLE functions are present
        but the device is not licensed to use them
    '''
    if check_licensed:
        return _ble_functions is not None and hasattr(voice, 'is_feature_licensed')\
            and voice.is_feature_licensed('CONTACTTRACING')
    return _ble_functions is not None

def register_consumer(callback):
    ''' register the callback to consume BLE advertise packets
    callback - function called when device receives an advertise packet
        the callback should accept five positional parameters:
        DeviceID - string representing Bluetooth MAC Address
        alias - string alias for the device (for A700x, "vv-<serial_number>")
        power - numeric power setting of the transmitting device
        RSSI - numeric Bluetooth RSSI
        ManufacturerDataString - up to 24 bytes of custom information
    return True if successful else False
    '''
    if has_ble():
        return _ble_functions['register'](callback)
    return False

def unregister_consumer():
    ''' unregister the callback
    return True if successful else False
    '''
    if has_ble():
        return _ble_functions['unregister']()
    return False

def set_search_key(search_key):
    ''' set the search key to use for advertise searches
    By default without setting this, this will search for A700x devices
    search_key - the Bluetooth address (or portion thereof) for which to listen
        NOTE: this should include colons, e.g. 'D4:CA:6E'
    return True if successful else False
    '''
    if has_ble():
        return _ble_functions['search'](search_key)
    return False

def set_advertise_packet(include_name, include_tx_power, manufacturer_data):
    ''' configure the contents of the BLE advertise packet
    The RSSI value is always included in the packet
    include_advertise_name - True to include the advertise name, else False
    include_tx_power - True to include transmit power, else False
    manufacturer_data - string to include in the Manufacturer's Data portion of the packet
        NOTE: this should be no more than 24 bytes
    NOTE: the RSSI is always included in the packet
    return True if successful else False
    '''
    if has_ble():
        return _ble_functions['advertise'](include_name, include_tx_power, manufacturer_data)
    return False