#
# Copyright (c) 2010-2011 Vocollect, Inc.
# Pittsburgh, PA 15235
# All rights reserved.
#
# This source code contains confidential information that is owned by
# Vocollect, Inc. and may not be copied, disclosed or otherwise used without
# the express written consent of Vocollect, Inc.
#

from voice import current_dialog
from vocollect_core import scanning

##############################################################################
# These dialog wrapper functions imported from vocollect_core.dialog.functions
# have been deprecated since the Core Library 1.1.0 release.
# While these will route to the appropriate function on a device,
# these will now raise a DeprecationWarning when running with Mock Catalyst.
# These will be completely removed in a future version.
##############################################################################
try:
    import mock_catalyst  # @UnresolvedImport @UnusedImport
    _has_mock_catalyst = True
except ImportError:
    _has_mock_catalyst = False
_allow_deprecated_prompts = False
import vocollect_core.dialog.functions
def prompt_alpha(*args, **kwargs):
    if _has_mock_catalyst and not _allow_deprecated_prompts:
        raise DeprecationWarning('Call prompt_alpha from vocollect_core.dialog.functions')
    return vocollect_core.dialog.functions.prompt_alpha(*args, **kwargs)
def prompt_alpha_numeric(*args, **kwargs):
    if _has_mock_catalyst and not _allow_deprecated_prompts:
        raise DeprecationWarning('Call prompt_alpha_numeric from vocollect_core.dialog.functions')
    return vocollect_core.dialog.functions.prompt_alpha_numeric(*args, **kwargs)
def prompt_digits(*args, **kwargs):
    if _has_mock_catalyst and not _allow_deprecated_prompts:
        raise DeprecationWarning('Call prompt_digits from vocollect_core.dialog.functions')
    return vocollect_core.dialog.functions.prompt_digits(*args, **kwargs)
def prompt_digits_required(*args, **kwargs):
    if _has_mock_catalyst and not _allow_deprecated_prompts:
        raise DeprecationWarning('Call prompt_digits_required from vocollect_core.dialog.functions')
    return vocollect_core.dialog.functions.prompt_digits_required(*args, **kwargs)
def prompt_float(*args, **kwargs):
    if _has_mock_catalyst and not _allow_deprecated_prompts:
        raise DeprecationWarning('Call prompt_float from vocollect_core.dialog.functions')
    return vocollect_core.dialog.functions.prompt_float(*args, **kwargs)
def prompt_list(*args, **kwargs):
    if _has_mock_catalyst and not _allow_deprecated_prompts:
        raise DeprecationWarning('Call prompt_list from vocollect_core.dialog.functions')
    return vocollect_core.dialog.functions.prompt_list(*args, **kwargs)
def prompt_list_lut(*args, **kwargs):
    if _has_mock_catalyst and not _allow_deprecated_prompts:
        raise DeprecationWarning('Call prompt_list_lut from vocollect_core.dialog.functions')
    return vocollect_core.dialog.functions.prompt_list_lut(*args, **kwargs)
def prompt_list_lut_auth(*args, **kwargs):
    if _has_mock_catalyst and not _allow_deprecated_prompts:
        raise DeprecationWarning('Call prompt_list_lut_auth from vocollect_core.dialog.functions')
    return vocollect_core.dialog.functions.prompt_list_lut_auth(*args, **kwargs)
def prompt_only(*args, **kwargs):
    if _has_mock_catalyst and not _allow_deprecated_prompts:
        raise DeprecationWarning('Call prompt_only from vocollect_core.dialog.functions')
    return vocollect_core.dialog.functions.prompt_only(*args, **kwargs)
def prompt_ready(*args, **kwargs):
    if _has_mock_catalyst and not _allow_deprecated_prompts:
        raise DeprecationWarning('Call prompt_ready from vocollect_core.dialog.functions')
    return vocollect_core.dialog.functions.prompt_ready(*args, **kwargs)
def prompt_required(*args, **kwargs):
    if _has_mock_catalyst and not _allow_deprecated_prompts:
        raise DeprecationWarning('Call prompt_required from vocollect_core.dialog.functions')
    return vocollect_core.dialog.functions.prompt_required(*args, **kwargs)
def prompt_words(*args, **kwargs):
    if _has_mock_catalyst and not _allow_deprecated_prompts:
        raise DeprecationWarning('Call prompt_words from vocollect_core.dialog.functions')
    return vocollect_core.dialog.functions.prompt_words(*args, **kwargs)
def prompt_yes_no(*args, **kwargs):
    if _has_mock_catalyst and not _allow_deprecated_prompts:
        raise DeprecationWarning('Call prompt_yes_no from vocollect_core.dialog.functions')
    return vocollect_core.dialog.functions.prompt_yes_no(*args, **kwargs)
def prompt_yes_no_cancel(*args, **kwargs):
    if _has_mock_catalyst and not _allow_deprecated_prompts:
        raise DeprecationWarning('Call prompt_yes_no_cancel from vocollect_core.dialog.functions')
    return vocollect_core.dialog.functions.prompt_yes_no_cancel(*args, **kwargs)
#############################################################################
# Callback methods associated with Core Dialog Links and Nodes. These are
# required to be in the default namespace because of a current limitation
# in the VoiceCatalyst runtime. This limitation may be removed in the future.
#############################################################################

#----------------------------------------------------------------------------
# General Callback Methods
#----------------------------------------------------------------------------
def confirm_entry():
    ''' Pass through method used from VID file. Calls same method in current running dialog instance '''
    return current_dialog().confirm_prompt()

def set_result():
    ''' Pass through method used from VID file. Calls same method in current running dialog instance '''
    if not was_http_posted():
        current_dialog().set_result()

def is_barcode_scanned():
    ''' Pass through method used from VID file. Calls same method in current running dialog instance '''
    return current_dialog().scanned_result()

def dialog_time_out():
    ''' Pass through method used from VID file. Calls same method in current running dialog instance '''
    return current_dialog().dialog_time_out()

def skip_prompt():
    ''' Pass through method used from VID file. Calls same method in current running dialog instance '''
    return current_dialog().skip_prompt

def prompt_here():
    ''' Pass through method used from VID file. Calls same method in current running dialog instance '''
    return current_dialog().prompt_here()

def was_http_posted():
    return current_dialog().was_http_posted()
    ''' Pass through method used from VID file. Calls same method in current running dialog instance '''

#----------------------------------------------------------------------------
# Callback methods for list and digits dialogs
#----------------------------------------------------------------------------
def is_valid_value():
    ''' Pass through method used from VID file. Calls same method in current running dialog instance '''
    return current_dialog().is_valid_value()

def result_less_than_min_length():
    ''' Pass through method used from VID file. Calls same method in current running dialog instance '''
    return current_dialog().result_less_than_min_length()

def timeout_digit_entry():
    ''' Pass through method used from VID file. Calls same method in current running dialog instance '''
    return current_dialog().timeout_digit_entry()

def invalid_count_check():
    ''' Pass through method used from VID file. Calls same method in current running dialog instance '''
    return current_dialog().invalid_count_check()

#----------------------------------------------------------------------------
# Float Dialog callback methods
#----------------------------------------------------------------------------
def set_decimal_point():
    ''' Sets the decimal point '''
    current_dialog().set_decimal_point()

#----------------------------------------------------------------------------
# List Dialog callback methods
#----------------------------------------------------------------------------

def reset():
    ''' resets current running dialog by setting result to None, and calling set_help '''
    if not was_http_posted():
        current_dialog().result = None
    current_dialog().set_help()

def list_move_first():
    ''' Pass through method used from VID file. Calls same method in current running dialog instance '''
    current_dialog().move_first()

def list_has_next():
    ''' Pass through method used from VID file. Calls same method in current running dialog instance '''
    return current_dialog().move_next()

def allow_select():
    ''' Pass through method used from VID file. Calls same method in current running dialog instance '''
    return current_dialog().allow_select()

#----------------------------------------------------------------------------
# Digits Dialog callback methods
#----------------------------------------------------------------------------
def reset_scan():
    ''' resets current running dialog by setting result to None, and resetting scan callback method '''
    reset()
    current_dialog().set_scan_callback()

def trigger_scan():
    ''' auto trigger the scanner '''
    scanning.auto_trigger_scanner()

def set_anchor_result():
    ''' sets the anchor word spoken '''
    current_dialog().set_anchor_result()
