# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

import re
from logspec.fsm_classes import State
from logspec.utils.linux_kernel_errors import find_kernel_error
from logspec.fsm_loader import register_state

MODULE_NAME = 'linux_kernel'


# State functions

def detect_linux_prompt(text):
    """Processes a Linux initialization log until a command-line prompt
    is reached (done condition).

    Parameters:
      text (str): the log or text fragment to parse

    Returns a dict containing the extracted info from the log:
      'prompt_ok': True if the initialization reached a command-line
          prompt, False otherwise.
      'match_end': position in `text' where the parsing ended.
      'errors': list of errors found, if any (see
          utils.linux_kernel_errors.find_kernel_error()).
    """
    # Check done condition. The regexp will be formed by or'ing the tags
    # here
    tags = [
        "/ #",
    ]
    data = {}
    regex = '|'.join(tags)
    match = re.search(regex, text)
    if match:
        data['match_end'] = match.end()
        data['prompt_ok'] = True
    else:
        data['prompt_ok'] = False

    # Check for linux-specific errors in the log. If the `done'
    # condition was found, search only before it. Otherwise search in
    # the full log.
    data['errors'] = []
    if match:
        text = text[:match.start()]
    while True:
        error = find_kernel_error(text)
        if not error:
            break
        text = text[error['end']:]
        data['errors'].append(error['error'])
    return data


# Create and register states

register_state(
    MODULE_NAME,
    State(
        name="Linux kernel load",
        description="Start of Linux kernel initialization",
        function=detect_linux_prompt),
    'kernel_load')

register_state(
    MODULE_NAME,
    State(
        name="Linux kernel load (second stage)",
        description="Start of Linux kernel initialization (second stage)",
        function=detect_linux_prompt),
    'kernel_stage2_load')
