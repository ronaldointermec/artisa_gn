###################################################################################################
##  Copyright (c) 2020 Honeywell International Inc. All Rights Reserved.
##  Honeywell and its product names are among the trademarks and/or service marks
##  owned by Honeywell International, Inc., or its subsidiaries.
##
##  For patent information, see http://www.hsmpats.com.
###################################################################################################
'''
Convenience "enum" classes and functions for interfacing with sensors
exposed in VoiceCatalyst 4.3 and later.
'''
import voice

try:
    # json introduced in VoiceCatalyst 1.2, if sensors are present then so is json
    import json
    _has_json = True
except ImportError:
    voice.log_message('SENSOR: json module not available')
    _has_json = False

# VoiceCatalyst 4.3 release had these in voice namespace instead of voice.sensors
# store a map of functions from their respective import
_sensor_functions = None
try:
    from voice.sensors import sensor_register_consumer, sensor_unregister_consumer, sensor_read  # @UnresolvedImport
    _sensor_functions = {'register': sensor_register_consumer,
        'unregister': sensor_unregister_consumer, 'read': sensor_read}
    voice.log_message('SENSOR: imported functions from voice.sensors')
except:
    voice.log_message('SENSOR: unable to import sensor functions from voice.sensors')
    try:
        from voice import sensor_register_consumer, sensor_unregister_consumer, sensor_read  # @UnresolvedImport @Reimport
        _sensor_functions = {'register': sensor_register_consumer,
            'unregister': sensor_unregister_consumer, 'read': sensor_read}
        voice.log_message('SENSOR: imported functions from voice')
    except:
        voice.log_message('SENSOR: unable to import sensor functions from voice namespace, sensor support unavailable')

#-------------------------------------------------------------------------------
# "enum" like classes with constants for sensors and read types

class ReadType:
    ''' Available read types for sensor_register_consumer '''
    ONE_SHOT = 1
    CONTINUOUS = 2
    ON_REFRESH = 3

class A700x:
    ''' Available A700x sensors '''
    STEP_COUNT = 'A700x.StepCount'
    TEMPERATURE = 'A700x.Temperature'
    AMBIENT_TEMPERATURE = 'A700x.AmbientTemperature'
    PRESSURE = 'A700x.Pressure'
    HUMIDITY = 'A700x.Humidity'
    ORIENTATION = 'A700x.Orientation'
    ACCELEROMETER = 'A700x.Accelerometer'
    GYROSCOPE = 'A700x.Gyroscope'
    GRAVITY = 'A700x.Gravity'
    MAGNETOMETER = 'A700x.Magnetometer'
    LINEAR_ACCELERATION = 'A700x.LinearAcceleration'
    ROTATION_VECTOR = 'A700x.RotationVector'
    GAME_ROTATION_VECTOR = 'A700x.GameRotationVector'
    GEOMAGNETIC_ROTATION_VECTOR = 'A700x.GeomagneticRotationVector'
    MAGNETIC_FIELD_UNCALIBRATED = 'A700x.MagneticFieldUncalibrated'
    GYROSCOPE_UNCALIBRATED = 'A700x.GyroscopeUncalibrated'
    # On Refresh only
    DEVICE_DROP = 'A700x.DeviceDrop'
    DEVICE_PICKUP = 'A700x.DevicePickup'
    DEVICE_ACTIVITY_RECOGNITION = 'A700x.DeviceActivityRecognition'

    ALL_SENSORS = ['A700x.StepCount', 'A700x.DeviceDrop', 'A700x.DevicePickup', 'A700x.DeviceActivityRecognition', 'A700x.Temperature', 'A700x.AmbientTemperature', 'A700x.Pressure', 'A700x.Humidity', 'A700x.Orientation', 'A700x.Accelerometer', 'A700x.Gyroscope', 'A700x.Gravity', 'A700x.Magnetometer', 'A700x.LinearAcceleration', 'A700x.RotationVector', 'A700x.GameRotationVector', 'A700x.GeomagneticRotationVector', 'A700x.MagneticFieldUncalibrated', 'A700x.GyroscopeUncalibrated']
    REFRESH_ONLY = ['A700x.DeviceDrop', 'A700x.DevicePickup', 'A700x.DeviceActivityRecognition']

class SRX:
    ''' Available SRX3 sensors '''
    STEP_COUNT = 'SRX.StepCount'
    BOOM_POSITION = 'SRX.BoomPosition'

    ALL_SENSORS = ['SRX.StepCount', 'SRX.BoomPosition']

    # return data constants
    MUTED_POSITION = 0
    ACTIVE_POSITION = 1

#-------------------------------------------------------------------------------
# Exception classes raised for issues interfacing with sensors

class SensorsNotAvailableException(Exception):
    ''' Sensors are not available in the current device environment '''

class SensorNotRegisterableException(Exception):
    ''' The sensor is not able to be registered '''

class SensorDataUnreadableException(Exception):
    ''' The sensor is not readable, or returned non-JSON data '''

class SensorVersionIndeterminateException(Exception):
    ''' The sensor version could not be determined '''

#-------------------------------------------------------------------------------
# sensor interface functions

def has_sensors():
    ''' determine if sensors are supported on current device '''
    return _sensor_functions is not None

def read_sensor_version(name):
    ''' read and determine the version of a sensor's data structure
    NOTE: this could be a costly operation, call extract_version directly if possible
    name - Sensor to register from A700x or SRX enums
    Returns sensor version
    Throws SensorsNotAvailableException, SensorNotRegisterableException,
        SensorDataUnreadableException, or SensorVersionIndeterminateException
    '''
    if _sensor_functions is None:
        raise SensorsNotAvailableException('Sensors not available')
    sensor_data = read_sensor(name)
    return extract_version(sensor_data)

def extract_version(sensor_data):
    ''' determine the version of a sensor's data structure
    sensor_data should be a valid return from read_sensor
    Returns sensor version
    Throws SensorDataUnreadableException or SensorVersionIndeterminateException
    '''
    if sensor_data in (None, False):
        raise SensorDataUnreadableException('Unable to read sensor data: ' + str(sensor_data))
    if 'sensorOutputVersion' in sensor_data:
        return float(sensor_data['sensorOutputVersion'])
    elif 'sensor' in sensor_data and 'outputVersion' in sensor_data['sensor']:
        # the location of version information may change beyond VoiceCatalyst 4.3
        return float(sensor_data['sensor']['outputVersion'])
    raise SensorVersionIndeterminateException('Could not determine sensor version')

def read_sensor(name):
    ''' Convenience function for single read of a sensor
    Registers, reads, and unregisters the sensor
    name - Sensor to register from A700x or SRX enums
    Returns sensor data as JSON
    Throws SensorNotRegisterableException, SensorDataUnreadableException
    '''
    if _sensor_functions is None:
        raise SensorsNotAvailableException('Sensors not available')
    data = None
    registered = _sensor_functions['register'](name, ReadType.ONE_SHOT, None, 1)
    if not registered:
        voice.log_message('SENSOR: unable to register sensor ' + name)
        raise SensorNotRegisterableException('Unable to register sensor ' + name)
    try:
        data = _sensor_functions['read'](name)
        registered = not _sensor_functions['unregister'](name, ReadType.ONE_SHOT)
        if registered:
            voice.log_message('SENSOR: failed to unregister sensor ' + name)
    except Exception as read_exception:
        voice.log_message('SENSOR: Error reading %s: %s: %s' % (name, type(read_exception), read_exception))
    if data in (None, False, 'null'):
        # can occur for unknown sensors, SRX sensors if using wired, or on-refresh only sensors
        raise SensorDataUnreadableException('Unable to read sensor data')
    if _has_json:
        # this should be present on any VoiceCatalyst version exposing sensors
        return json.loads(data)
    return data

def register_consumer(name, read_type, callback, reads_per_minute = 1):
    ''' Convenience function to disambiguate import location
    and lack of reads_per_minute default in voice.sensors.py documentation module
    name - Sensor to register from A700x or SRX enums
    read_type - Continuous (2) or On Refresh (3) from ReadType enum
    callback - function to call based on read type
        accepting two positional string arguments (name, string of JSON data)
    reads_per_minute (1) - number of reads per minute for Continuous read type
    returns True if successful, else False
    '''
    if _sensor_functions is not None:
        return _sensor_functions['register'](name, read_type, callback, reads_per_minute)
    return False

def unregister_consumer(name, read_type):
    ''' Convenience function to disambiguate import location
    name - Sensor to unregister from A700x or SRX enums
    read_type - Continuous (2) or On Refresh (3) from ReadType enum
    returns True if successful, else False
    '''
    if _sensor_functions is not None:
        return _sensor_functions['unregister'](name, read_type)
    return False