import voice

class CatalystVersion(tuple):
    ''' provide comparison operations against earlier int/float implementations '''

    # a CatalystVersion object should be used for comparing the parsed catalyst_version()
    # as running on the device to any values needed in a Voice Application
    # if mock_catalyst is present (i.e. running in the development environment),
    # raise a DeprecationWarning for now - this will be removed at a later date
    # since floats are ambiguously precisioned and it is impossible to distinguish
    # what is meant by catalyst_version() > 2.113 (for example):
    # this could mean 2.11.3, 2.1.13, or (current interpretation) 2.1.1.3
    # While this will still work on the device, without mock_catalyst present,
    # code should be updated to remove int and float comparisons
    # Until removed, this bypass is intended only for unit tests to mock up device behavior
    _bypass_version_cast_deprecation = False

    def __lt__(self, other):
        if type(other) in [CatalystVersion, tuple]:
            return super().__lt__(other)
        return self < CatalystVersion._version_cast(other)

    def __le__(self, other):
        if type(other) in [CatalystVersion, tuple]:
            return super().__le__(other)
        return self <= CatalystVersion._version_cast(other)

    def __gt__(self, other):
        if type(other) in [CatalystVersion, tuple]:
            return super().__gt__(other)
        return self > CatalystVersion._version_cast(other)

    def __ge__(self, other):
        if type(other) in [CatalystVersion, tuple]:
            return super().__ge__(other)
        return self >= CatalystVersion._version_cast(other)

    def __eq__(self, other):
        if type(other) in [CatalystVersion, tuple]:
            return super().__eq__(other)
        try:
            return self == CatalystVersion._version_cast(other)
        except Exception as e:
            voice.log_message('CORE LIB: unable to compare: ' + str(e) + " " + str(type(e)))
        return False
    def __ne__(self, other):
        return not self == other
    def __hash__(self):
        return super().__hash__()

    def __str__(self):
        return '.'.join(str(i) for i in self)

    @classmethod
    def _version_cast(cls, other):
        # intended to coerce floats and ints to CatalystVersion for legacy comparisons
        # raises a DeprecationWarning in development environment so code can be updated
        # can be overridden with _bypass_version_cast_deprecation
        # this will be removed in a future release
        raise_deprecation = False
        try:
            import mock_catalyst  # @UnresolvedImport @UnusedImport
            if not CatalystVersion._bypass_version_cast_deprecation:
                raise_deprecation = True
        except:
            pass
        if raise_deprecation:
            raise DeprecationWarning('CORE LIB: WARN: Comparison of CatalystVersion objects to float and int will be deprecated, use a CatalystVersion object')
        return CatalystVersion._version_cast_deprecated(other)

    @classmethod
    def _version_cast_deprecated(cls, other):
        # intended to coerce floats and ints to CatalystVersion for legacy comparisons
        voice.log_message('CORE LIB: WARN: legacy comparison of VoiceCatalyst: comparing CatalystVersion to ' + str(type(other)) + ' ' + str(other))
        try:
            version = str(other).split('.')
            if isinstance(other, float) and len(version) > 1:
                # split each position of the decimal
                fractional = version[1]
                version = [version[0]]
                # fractional is a string of the decimal portion, extending as an iterable this takes each character / decimal place
                version.extend(fractional)
            while len(version) < 3:
                version.append(0)
            parsed_version = []
            for v in version:
                parsed_version.append(int(v))
            voice.log_message('CORE LIB: calculated version result: ' + str(parsed_version))
            return CatalystVersion(parsed_version)
        except Exception as e:
            message = 'CORE LIB: unable to cast to CatalystVersion: ' + str(e) + " " + str(type(e))
            voice.log_message(message)
            raise TypeError(message)


MULTIPLE_SCANS_VERSION = CatalystVersion([2, 0, 0])
MULTIPLE_HINTS_VERSION = CatalystVersion([2, 0, 0])

_parsed_version = None

def catalyst_version():
    global _parsed_version
    if _parsed_version is None:
        # parse once per task run
        try:
            version = voice.getenv('SwVersion.ApplicationVersion')
            version = version.rsplit('_', 1)[1] # get version after last _
            version = version.replace('V', '') # remove the V
            version = version.split('.')
            while len(version) < 3:
                version.append(0)
            _parsed_version = []
            for v in version:
                try:
                    _parsed_version.append(int(v))
                except Exception as e:
                    voice.log_message("CORE LIB: error parsing version component " + str(v) + ": " + str(e) + " " + str(type(e)))
                    _parsed_version.append(0)
            _parsed_version = CatalystVersion(_parsed_version)
            voice.log_message("CORE LIB: parsed VoiceCatalyst_version: " + str(_parsed_version))
        except Exception as e:
            #if any errors assume it's an older version
            voice.log_message("CORE LIB: error parsing VoiceCatalyst version: " + str(e) + " " + str(type(e)))
            _parsed_version = CatalystVersion([0, 0, 0])
    return _parsed_version

def multiple_scans_supported():
    ''' Prior to VoiceCatalyst 2.0, toggling the scanner off then right back on
        caused issues; the A730 allows using the same callback without toggling
    '''
    return catalyst_version() >= MULTIPLE_SCANS_VERSION

def multiple_hints_supported():
    return catalyst_version() >= MULTIPLE_HINTS_VERSION

def event_callback_supported():
    ''' VoiceCatalyst 2.1.1 introduced support for a generic set_event_callback '''
    return hasattr(voice, "EVT_SCAN_CB")

def say_again_supported():
    ''' VoiceCatalyst 2.1.1 introduced support for overriding say again '''
    return event_callback_supported()
