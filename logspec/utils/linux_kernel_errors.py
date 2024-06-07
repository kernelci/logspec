# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

import re

from logspec.utils.defs import *
from logspec.errors.linux_kernel import *


def find_error_report(text):
    """Finds a kernel error report in a text log.

    Current types of error reports supported:
      - Generic "cut here" blocks
      - NULL pointer dereferences

    Parameters:
      text (str): the log or text fragment to parse

    Returns:
    If an error report was found, it returns a dict containing:
      'error': specific error object containing the structured error info
      'end': position in the text right after the parsed block
    None if no error report was found.
    """
    # Tags to look for. For every tag found, the parsing is delegated to
    # the appropriate object
    tags = {
        'cut_here': {
            'regex': f'{LINUX_TIMESTAMP} -+\[ cut here \].*',
            'error': GenericError(),
        },
        'null_pointer': {
            'regex': f'{LINUX_TIMESTAMP} Unable to handle kernel NULL pointer dereference',
            'error': NullPointerDereference(),
        },
        'bug': {
            'regex': f'{LINUX_TIMESTAMP} BUG:',
            'error': KernelBug(),
        },
        'kernel_panic': {
            'regex': f'{LINUX_TIMESTAMP} Kernel panic',
            'error': KernelPanic(),
        },
    }
    regex = '|'.join([f'(?P<{tag}>{v["regex"]})' for tag, v in tags.items()])
    match = re.search(regex, text)
    if match:
        # Detect which of the tags was found and dispatch the parsing to
        # the right function
        matched_tags = [tag for tag, value in match.groupdict().items() if value is not None]
        if matched_tags:
            tag = matched_tags[0]
            error = tags[tag]['error']
            end = match.start() + error.parse(text[match.start():])
            return {
                'error': error,
                '_end': end,
            }
    return None

def find_kernel_error(text):
    """Find kernel errors in a text segment.

    Currently supported:
      - kernel error reports (find_error_report)

    Parameters:
      text (str): the log or text fragment to parse

    Returns:
    If an error report was found, it returns a dict containing:
      'error': specific error object containing the structured error info
      'end': position in the text right after the parsed block
    None if no error report was found.
    """
    report = find_error_report(text)
    return report
