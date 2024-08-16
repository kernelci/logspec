# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

#  #     #                                                      ,----.
#  #     # #  ####      ####  #    # #    # #####               |    |
#  #     # # #    #    #      #    # ##   #   #                 |    |
#  ####### # #          ####  #    # # #  #   #                 |    |
#  #     # # #              # #    # #  # #   #                 |    |
#  #     # # #    #    #    # #    # #   ##   #                 |    |
#  #     # #  ####      ####   ####  #    #   #                 |    |
#                                                               |    |
#                                                            ___|    |___
#  #####  #####    ##    ####   ####  #    # ######  ####    \          /
#  #    # #    #  #  #  #    # #    # ##   # #      #         \        /
#  #    # #    # #    # #      #    # # #  # #####   ####      \      /
#  #    # #####  ###### #      #    # #  # # #           #      \    /
#  #    # #   #  #    # #    # #    # #   ## #      #    #       \  /
#  #####  #    # #    #  ####   ####  #    # ######  ####         \/

# This code could use some refactoring, the parsing logic is really ugly
# and some parts can probably be abstracted into common functions. Then
# again, this wouldn't be a problem if the kernel authorities agreed on
# a common format for error reports.


import re

from logspec.utils.defs import *
from logspec.errors.error import Error


class GenericError(Error):
    """Models the basic information of a generic "cut here" kernel error
    report.
    """
    def __init__(self):
        super().__init__()
        self.error_type = "linux.kernel"
        self.hardware = None
        self.location = None
        self.call_trace = []
        self.modules = []
        self._signature_fields.extend([
            'location',
        ])

    def _parse(self, text):
        """Parses a generic "cut here" kernel error report and updates
        the object with the extracted information.

        Parameters:
          text (str): the text log from the start of the report block

        Returns the position in `text' where the report block ends (if
        found).
        """
        # Report starts on the next line after the "cut here" tag
        try:
            msg_start = text.index('\n') + 1
        except ValueError:
            msg_start = 0

        # Find the end of the report block, if found, narrow the text to
        # those lines
        match = re.search(fr'{LINUX_TIMESTAMP} ---\[ end trace', text[msg_start:])
        report_end = None
        if match:
            report_end = msg_start + match.start()
            self._report = text[msg_start:report_end]

        text = text[msg_start:report_end]
        # At this point, `text' starts after the `cut here' marker
        # line. If a `end trace' marker was found, `text' ends before
        # it.

        match_end = 0
        # Report banner (identifier)
        match = re.search(fr'{LINUX_TIMESTAMP}.*?(?P<report_type>[A-Z]+):?.*? at (?P<location>.*)', text)
        if match:
            match_end += match.end()
            self.error_type += f".{match.group('report_type').lower()}"
            self.location = match.group('location')
            # Search for error messages before the banner
            match = re.search(f'{LINUX_TIMESTAMP} (?P<message>.*)', text[:match.start()])
            if match:
                self.error_summary = match.group('message')

        # List of modules
        match = re.search(f'{LINUX_TIMESTAMP} Modules linked in: (?P<modules>.*)', text[match_end:])
        if match:
            match_end += match.end()
            self.modules = sorted(match.group('modules').split())
        # Hardware name
        match = re.search(f'{LINUX_TIMESTAMP} Hardware name: (?P<hardware>.*)', text[match_end:])
        if match:
            match_end += match.end()
            self.hardware = match.group('hardware')
        # Registers (maybe not needed)
        # Call trace
        match = re.search(f'{LINUX_TIMESTAMP} call trace:', text[match_end:], flags=re.IGNORECASE)
        if match:
            match_end += match.end()
            matches = re.finditer(f'{LINUX_TIMESTAMP}  (.*)', text[match_end:])
            if matches:
                for m in matches:
                    match_end += match.end()
                    self.call_trace.append(m.group(1))

        # if not report_end and match_end > 0:
        #     report_end = match_end
        return report_end


class NullPointerDereference(Error):
    """Models the basic information of a NULL pointer dereference kernel
    error report.
    """
    def __init__(self):
        super().__init__()
        self.error_type = "linux.kernel.null_pointer_dereference"
        self.hardware = None
        self.address = None
        self.call_trace = []
        self._signature_fields.extend([
            'address',
        ])

    def _parse(self, text):
        """Parses a kernel error report for a NULL pointer dereference
        and updates the object with the extracted information.

        Parameters:
          text (str): the text log from the start of the report block

        Returns the position in `text' where the report block ends (if
        found).
        """
        # Find the end of the report block, if found, narrow the text to
        # those lines
        match = re.search(fr'{LINUX_TIMESTAMP} ---\[ end trace', text)
        report_end = None
        if match:
            report_end = match.start()
            self._report = text[:report_end]
        text = text[:report_end]

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
        match = re.search(f'{LINUX_TIMESTAMP} call trace:', text[match_end:], flags=re.IGNORECASE)
        if match:
            match_end += match.end()
            matches = re.finditer(f'{LINUX_TIMESTAMP}  (.*)', text[match_end:])
            if matches:
                for m in matches:
                    match_end += match.end()
                    self.call_trace.append(m.group(1))

        # if not report_end and match_end > 0:
        #     report_end = match_end
        return report_end


class KernelBug(Error):
    """Models the basic information of a Kernel BUG report.
    """
    def __init__(self):
        super().__init__()
        self.error_type = "linux.kernel.bug"
        self.hardware = None
        self.call_trace = []

    def _parse(self, text):
        """Parses a kernel BUG report and updates the object with the
        extracted information.

        Parameters:
          text (str): the text log from the start of the report block

        Returns the position in `text' where the report block ends (if
        found).
        """
        # Find the end of the report block, if found, narrow the text to
        # those lines
        match = re.search(fr'{LINUX_TIMESTAMP} ---\[ end trace', text)
        report_end = None
        if match:
            report_end = match.start()
            self._report = text[:report_end]

        text = text[:report_end]
        # At this point, `text' starts after the `BUG' marker line. If a
        # `end trace' marker was found, `text' ends before it.

        match_end = 0
        start_of_modules_list = 0
        # Initial line
        message = ""
        match = re.search(f'{LINUX_TIMESTAMP} BUG: (?P<message>.*)', text)
        if match:
            match_end += match.end()
            message = match.group('message')
        # Extract "location" from bug message
        match = re.search(f'(?P<bug_cause>.*?) at (?P<location>.*)', message)
        if match:
            self.error_summary = match.group('bug_cause')
            self.location = match.group('location')
        else:
            self.error_summary = message
        # Hardware name
        match = re.search(f'{LINUX_TIMESTAMP} Hardware name: (?P<hardware>.*)', text[match_end:])
        if match:
            match_end += match.end()
            self.hardware = match.group('hardware')
        # List of modules
        # Format 1:
        match = re.search(f'{LINUX_TIMESTAMP} Modules linked in: *(?P<modules>.*)', text[match_end:])
        if match:
            start_of_modules_list = match.start() + match_end
            match_end += match.end()
            self.modules = sorted(match.group('modules').split())
            # Additional lines
            matches = re.findall(f'{LINUX_TIMESTAMP}  (.*)', text[match_end:])
            if matches:
                modules = ""
                for m in matches:
                    modules += f"{m} "
                self.modules += modules.split()
                self.modules.sort()
        # Call trace (before the list of modules, if found)
        match = re.search(f'{LINUX_TIMESTAMP} Call Trace:', text[:start_of_modules_list])
        if match:
            matches = re.findall(f'{LINUX_TIMESTAMP}  (.*)', text[match.end():start_of_modules_list])
            if matches:
                self.call_trace = matches

        if not report_end and match_end > 0:
            report_end = match_end
        return report_end


class KernelPanic(Error):
    """Models the basic information of a Kernel panic.
    """
    def __init__(self):
        super().__init__()
        self.error_type = "linux.kernel.panic"
        self.hardware = None
        self.call_trace = []

    def _parse(self, text):
        """Parses a kernel panic report and updates the object with the
        extracted information.

        Parameters:
          text (str): the text log from the start of the report block

        Returns the position in `text' where the report block ends (if
        found).
        """
        # Find the end of the report block, if found, narrow the text to
        # those lines
        match = re.search(fr'{LINUX_TIMESTAMP} ---\[ end Kernel panic', text)
        report_end = None
        if match:
            report_end = match.start()
            self._report = text[:report_end]
        text = text[:report_end]

        match_end = 0
        # Initial line
        match = re.search(f'{LINUX_TIMESTAMP} Kernel panic .*?: (?P<message>.*)', text)
        if match:
            match_end += match.end()
            self.error_summary = match.group('message')
        # Hardware name
        match = re.search(f'{LINUX_TIMESTAMP} Hardware name: (?P<hardware>.*)', text[match_end:])
        if match:
            match_end += match.end()
            self.hardware = match.group('hardware')
        # Call trace
        match = re.search(f'{LINUX_TIMESTAMP} call trace:', text[match_end:], flags=re.IGNORECASE)
        if match:
            match_end += match.end()
            matches = re.finditer(f'{LINUX_TIMESTAMP}  (.*)', text[match_end:])
            if matches:
                for m in matches:
                    match_end += match.end()
                    self.call_trace.append(m.group(1))

        if not report_end and match_end > 0:
            report_end = match_end
        return report_end


class UBSANError(Error):
    """Models a UBSAN error report.
    """
    def __init__(self):
        super().__init__()
        self.error_type = "linux.kernel.ubsan"
        self.location = None
        self.hardware = None
        # Not needed for now:
        #self.call_trace = []
        self._signature_fields.extend([
            'location',
        ])

    def _parse(self, text):
        """Parses a UBSAN error report and updates the object with the
        extracted information.

        Parameters:
          text (str): the text log from the start of the report block

        Returns the position in `text' where the report block ends (if
        found).
        """
        # Find the end of the report block, if found, narrow the text to
        # those lines
        match = re.search('================================================================================', text)
        report_end = None
        if match:
            report_end = match.start()
            self._report = text[:report_end]
        text = text[:report_end]

        match_end = 0
        # Initial line
        match = re.search(fr'{LINUX_TIMESTAMP} UBSAN: (?P<error_msg>.*?) in (?P<location>.*)', text)
        if match:
            match_end += match.end()
            self.error_summary = match.group('error_msg')
            self.location = match.group('location')
        # Second line: error details
        match_end += 1
        match = re.search(fr'{LINUX_TIMESTAMP} (?P<error_details>.*)', text[match_end:])
        if match:
            match_end += match.end()
            self.error_summary += f": {match.group('error_details')}"

        # Hardware name
        match = re.search(f'{LINUX_TIMESTAMP} Hardware name: (?P<hardware>.*)', text[match_end:])
        if match:
            match_end += match.end()
            self.hardware = match.group('hardware')

        return report_end
