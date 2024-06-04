# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

from logspec.fsm_classes import State
from logspec.fsm_loader import register_state
from logspec.utils.kbuild_errors import find_kbuild_error

MODULE_NAME = 'kbuild'


# State functions

def detect_kbuild_start(text):
    """Processes a kernel build log output and searches for errors in
    the process.

    Parameters:
      text (str): the log or text fragment to parse

    Returns a dict containing the extracted info from the log:
      'errors': list of errors found, if any.
          See utils.kbuild_errors.find_build_error().
    """
    data = {}
    # TODO: detection of log structure and definition of `done' (if
    # applicable)

    # Check for errors
    data['errors'] = []
    error = find_kbuild_error(text)
    if error:
        data['errors'].append(error)
    return data


# Create and register states

register_state(
    MODULE_NAME,
    State(
        name="Kernel build start",
        description="Initial state for a kernel build",
        function=detect_kbuild_start),
    'kbuild_start')
