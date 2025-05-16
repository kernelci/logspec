# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

import re
from logspec.parser_classes import State
from logspec.parser_loader import register_state
from logspec.utils.defs import LINUX_TIMESTAMP


MODULE_NAME = 'generic_boot'


# State functions

def detect_bootloader_end(text, start=None, end=None):
    """Detects the end of a bootloader execution in a text log and
    searches for errors during the process.

    Parameters:
      text (str): the log or text fragment to parse

    Returns a dict containing the extracted info from the log:
      'bootloader.done': True if the bootloader was detected to boot
          successfuly, False otherwise
      '_match_end': position in `text' where the parsing ended
    """
    # Patterns (tags) to search for. The regexp will be formed by or'ing
    # them
    tags = [
        "Starting kernel ...",
        "jumping to kernel",
        "Booting from ROM...",
        f"{LINUX_TIMESTAMP} Booting Linux",
    ]
    if start or end:
        text = text[start:end]
    data = {
        '_signature_fields': [
            'bootloader.done',
        ],
    }
    regex = '|'.join(tags)
    match = re.search(regex, text)
    if match:
        data['_match_end'] = match.end() + start if start else match.end()
        data['bootloader.done'] = True
        data['_summary'] = "Bootloader stage done, jump to kernel"
    else:
        data['_match_end'] = end if end else len(text)
        data['bootloader.done'] = False
        data['_summary'] = ("Bootloader stage failed, inconclusive or "
                            "couldn't detect handover to kernel")
    return data


# Create and register states

register_state(
    MODULE_NAME,
    State(
        name="Generic boot",
        description="Initial state for any target with a bootloader stage that was powered on",
        function=detect_bootloader_end),
    'generic_boot')
