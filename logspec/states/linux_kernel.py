# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

import re
from logspec.parser_classes import State
from logspec.utils.linux_kernel_errors import find_kernel_error
from logspec.parser_loader import register_state
from logspec.utils.defs import LINUX_TIMESTAMP


MODULE_NAME = 'linux_kernel'


# Utility functions
def _detect_kernel_start(text):
    """Checks if the first line of text looks like the output of a Linux
    kernel starting. Returns a Match object if it does, None if it
    doesn't.
    """
    try:
        first_line_end = text.index('\n')
    except ValueError:
        # No new line found, so no first line
        return None
    return re.match(fr'{LINUX_TIMESTAMP} .*',
                    text[:first_line_end]) or re.search(fr'{LINUX_TIMESTAMP} Linux version .*', text)


# State functions
def detect_linux_prompt(text, start=None, end=None):
    """Processes a Linux initialization log until a command-line prompt
    is reached (done condition).

    Parameters:
      text (str): the log or text fragment to parse

    Returns a dict containing the extracted info from the log:
      'linux.boot.prompt': True if the initialization reached a command-line
          prompt, False otherwise.
      '_match_end': position in `text' where the parsing ended.
      'errors': list of errors found, if any (see
          utils.linux_kernel_errors.find_kernel_error()).
    """
    # Check done condition. The regexp will be formed by or'ing the tags
    # here
    tags = [
        "/ #",
    ]
    if start or end:
        text = text[start:end]
    data = {
        '_signature_fields': [
            'linux.boot.prompt',
            'linux.boot.kernel_started',
        ],
    }
    regex = '|'.join(tags)
    match = re.search(regex, text)
    if match:
        data['_match_end'] = match.end() + start if start else match.end()
        data['linux.boot.kernel_started'] = True
        data['linux.boot.prompt'] = True
        data['_summary'] = "Linux boot prompt found"
    else:
        data['linux.boot.prompt'] = False
        kernel_first_line_start = text.index('\n') + 1
        if _detect_kernel_start(text[kernel_first_line_start:]):
            data['linux.boot.kernel_started'] = True
            data['_summary'] = "Linux boot prompt not found"
        else:
            data['linux.boot.kernel_started'] = False
            data['_summary'] = "Kernel didn't start"
        data['_match_end'] = end if end else len(text)

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
        text = text[error['_end']:]
        if error['error']:
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
