# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

import os
import re

from logspec.utils.defs import *
from logspec.errors.error import Error


class KbuildCompilerError(Error):
    """Models the information extracted from a compiler error.
    """
    def __init__(self, script=None, target=None):
        """Object initializer.

        Parameters:
          script (str): Kbuild script and location where it failed
          target (str): source or object file that caused
              the compiler error
        """
        super().__init__()
        self.script = script
        self.target = target
        self.src_file = ""
        self.location = ""
        self.error_type = "kbuild.compiler"

    def _parse_compiler_error_line(self, text):
        """Searches for and parses compiler errors/warnings that are
        contained in a single line (see the regex below for details).
        """
        file_pattern = os.path.splitext(self.target)[0]
        match = re.search(f'^(?P<src_file>{file_pattern}.*?):(?P<location>.*?): (?P<type>.*?): (?P<message>.*?)\n',
                          text, flags=re.MULTILINE)
        if match:
            self._report = text[match.start():]
            self.src_file = match.group('src_file')
            self.location = match.group('location')
            self.error_type += f".{match.group('type')}"
            self.error_summary = match.group('message')
            return len(text)
        return 0

    def _parse_linker_error(self, text):
        """Parses a linker error message and saves the source file and
        error summary.
        """
        self.error_type += f".linker_error"
        match = re.search('ld: (?P<obj_file>.*?):', text)
        if match:
            src_file = os.path.basename(match.group('obj_file'))
            src_dir = os.path.dirname(match.group('obj_file'))
            src_file_name = os.path.splitext(src_file)[0]
            src_file_ext = os.path.splitext(src_file)[1].strip('.')
            match = re.search(fr'(?P<src_file>{src_file_name}\.[^{src_file_ext}]):.*?: (?P<message>.*?)\n', text)
            if match:
                self.src_file = os.path.join(src_dir, match.group('src_file'))
                self.error_summary = match.group('message')

    def _parse_compiler_error_block(self, text):
        """Parses compiler errors that are laid out in a block of lines.
        It searches for a line that contains the target string, then
        looks for the error block starting after it, where the error
        block starts with the first unindented line and continues until
        the end of the text.
        """
        end_pos = 0
        # Get the start position of the block to parse (ie. where the
        # Make target file first appears)
        match = re.search(self.target, text)
        if not match:
            return end_pos
        block_start = match.end()
        # Get the full error block
        match = re.search(r'^[^\s]+.*$', text[block_start:], flags=re.MULTILINE)
        if match:
            self._report += text[block_start + match.start():]
            end_pos = len(text)
        # Search for the compiler error line in the block
        match = re.search(r'(?P<type>error|warning): (?P<message>.*?)\n', self._report)
        if match:
            self.error_type += f".{match.group('type')}"
            self.error_summary = match.group('message')
        # Try to get the source file and location from the error message
        target_base_file = os.path.splitext(self.target)[0]
        target_file_ext = os.path.splitext(self.target)[1].strip('.')
        match = re.search(fr'(?P<src_file>{target_base_file}\.[^{target_file_ext}]):(?P<location>\d+)', self._report)
        if match:
            self.src_file = match.group('src_file')
            self.location = match.group('location')
        # Helper parser functions for specific cases:
        # Linker error
        match = re.search('ld: ', self._report)
        if match:
            self._parse_linker_error(self._report)
        return end_pos

    def parse(self, text):
        """Parses a log fragment looking for a compiler error for a
        specific file (self.target) and updates the object with the
        extracted information.

        Strategy 1: Search for lines that look like a compiler
        error/warning message.

        Strategy 2: Search for a line that contains the target string,
        then look for the error block starting after it, where the error
        block starts with the first unindented line and continues until
        the end of the text.

        Parameters:
          text (str): the text log containing the compiler error

        Returns the position in `text' where the error block ends (if
        found).
        """
        parse_end_pos = 0
        # Strategy 1
        parse_end_pos = self._parse_compiler_error_line(text)
        if parse_end_pos:
            return parse_end_pos
        # Strategy 2
        parse_end_pos = self._parse_compiler_error_block(text)
        if parse_end_pos:
            return parse_end_pos
        return parse_end_pos


class KbuildProcessError(Error):
    """Models the information extracted from a kbuild error caused by a
    script, configuration or other runtime error.
    """
    def __init__(self,  script=None, target=None):
        """Object initializer.

        Parameters:
          script (str): Kbuild script and location where it failed
          target (str): Kbuild target that failed
        """
        super().__init__()
        self.script = script
        self.target = target

    def parse(self, text):
        """Parses a log fragment looking for a generic Kbuild error
        and updates the object with the extracted information.

        Strategy: Look for lines containing "***".

        Parameters:
          text (str): the text log containing the error

        Returns the position in `text' where the error block ends (if
        found).
        """
        end = 0
        self.error_type = "kbuild.make"
        match = re.finditer(r'\*\*\*.*', text)
        summary_strings = []
        for m in match:
            self._report += f"{m.group(0)}\n"
            summary_strings.append(m.group(0).strip('*\n '))
            end = m.end()
        if summary_strings:
            self.error_summary = " ".join([string for string in summary_strings if string])
        return end


class KbuildModpostError(Error):
    """Models the information extracted from a kbuild error in the
    modpost target.
    """
    def __init__(self,  script=None, target=None):
        """Object initializer.

        Parameters:
          script (str): Kbuild script and location where it failed
          target (str): Kbuild target that failed
        """
        super().__init__()
        self.script = script
        self.target = target

    def parse(self, text):
        """Parses a log fragment looking for a modpost Kbuild error
        and updates the object with the extracted information.

        Strategy: look for lines containing "ERROR: modpost: ".

        Parameters:
          text (str): the text log containing the modpost error

        Returns the position in `text' where the error block ends (if
        found).
        """
        end = 0
        self.error_type = "kbuild.modpost"
        match = re.finditer(r'ERROR: modpost: (?P<message>.*)', text)
        summary_strings = []
        for m in match:
            self._report += f"{m.group(0)}\n"
            summary_strings.append(m.group('message'))
            end = m.end()
        if summary_strings:
            self.error_summary = " ".join(summary_strings)
        return end


class KbuildGenericError(Error):
    """Models the information extracted from a Kbuild error that doesn't
    have a known type. This is meant to be used to catch errors that
    look like a known Kbuild error but for which we don't have enough
    info to really tell which type it is.
    """
    def __init__(self,  script=None, target=None):
        """Object initializer.

        Parameters:
          script (str): Kbuild script and location where it failed
          target (str): Kbuild target that failed
        """
        super().__init__()
        self.script = script
        self.target = target

    def parse(self, text):
        """Parses a log fragment looking for a generic Kbuild error
        and updates the object with the extracted information.

        Strategy: if a target was specified, search for errors _after_
        the first appearance of the `target' string in the log. To
        search for these errors, look for unindented lines.

        Parameters:
          text (str): the text log containing the modpost error

        Returns the position in `text' where the error block ends (if
        found).
        """
        self.error_type = "kbuild.other"
        end = 0
        if self.target:
            match = re.search(self.target, text)
            if not match:
                return end
            summary_strings = []
            match = re.finditer(r'^[^\s]+.*$', text[match.end():], flags=re.MULTILINE)
            for m in match:
                self._report += f"{m.group(0)}\n"
                # Extract summary from error message if it's a
                # '***'-prefix block
                if m.group(0).startswith('***'):
                    summary_strings.append(m.group(0).strip('*\n '))
                end = m.end()
            if summary_strings:
                self.error_summary = " ".join([string for string in summary_strings if string])
        return end



class KbuildUnknownError(Error):
    def __init__(self, text):
        super().__init__()
        self.error_type = "kbuild.unknown"
        self.error_summary = text
        self._report = text
