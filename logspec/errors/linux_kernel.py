# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

import re

from logspec.utils.defs import *
from logspec.errors.error import Error


class GenericError(Error):
    """Models the basic information of a generic "cut here" kernel error
    report.
    """
    def __init__(self):
        super().__init__()
        self.hardware = None
        self.location = None
        self.call_trace = []
        self.modules = []

    def parse(self, text):
        """Parses a generic "cut here" kernel error report and updates
        the object with the extracted information.

        Parameters:
          text (str): the text log from the start of the report block

        Returns the position in `text' where the report block ends (if
        found).
        """
        # Report starts on the next line after the "cut here" tag
        msg_start = text.index('\n') + 1
        match = re.search(f'{LINUX_TIMESTAMP} ---\[ end trace', text[msg_start:])
        msg_end = None
        if match:
            msg_end = match.start()
            self._report = text[msg_start:msg_end]
        text = text[msg_start:msg_end]

        match_end = 0
        # Initial line
        match = re.search(f'{LINUX_TIMESTAMP} (?P<report_type>\w+): .*? at (?P<location>.*)', text)
        if match:
            match_end = match.end()
            self.type = match.group('report_type')
            self.location = match.group('location')
        # List of modules
        match = re.search(f'{LINUX_TIMESTAMP} Modules linked in: (?P<modules>.*)', text[match_end:])
        if match:
            match_end = match.end()
            self.modules = sorted(match.group('modules').split())
        # Hardware name
        match = re.search(f'{LINUX_TIMESTAMP} Hardware name: (?P<hardware>.*)', text[match_end:])
        if match:
            match_end = match.end()
            self.hardware = match.group('hardware')
        # Registers (maybe not needed)
        # Call trace
        matches = re.findall(f'{LINUX_TIMESTAMP}  (.*)', text[match_end:])
        if matches:
            match_end = match.end()
            self.call_trace = matches

        # if not msg_end and match_end > 0:
        #     msg_end = match_end
        return msg_end


class NullPointerDereference(Error):
    """Models the basic information of NULL pointer dereference kernel
    error report.
    """
    def __init__(self):
        super().__init__()
        self.type = "Unable to handle kernel NULL pointer dereference"
        self.hardware = None
        self.address = None
        self.call_trace = []

    def parse(self, text):
        """Parses a kernel error report for a NULL pointer dereference
        and updates the object with the extracted information.

        Parameters:
          text (str): the text log from the start of the report block

        Returns the position in `text' where the report block ends (if
        found).
        """
        msg_start = 0
        match = re.search(f'{LINUX_TIMESTAMP} ---\[ end trace', text[msg_start:])
        msg_end = None
        if match:
            msg_end = match.start()
            self._report = text[msg_start:msg_end]
        text = text[msg_start:msg_end]

        match_end = 0
        # Initial line
        match = re.search(f'at virtual address (?P<address>.*)', text)
        if match:
            match_end = match.end()
            self.address = match.group('address')
        # Hardware name
        match = re.search(f'{LINUX_TIMESTAMP} Hardware name: (?P<hardware>.*)', text[match_end:])
        if match:
            match_end = match.end()
            self.hardware = match.group('hardware')
        # Call trace
        matches = re.findall(f'{LINUX_TIMESTAMP}  (.*)', text[match_end:])
        if matches:
            match_end = match.end()
            self.call_trace = matches

        # if not msg_end and match_end > 0:
        #     msg_end = match_end
        return msg_end
