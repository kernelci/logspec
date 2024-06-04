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
        self.error_type = "Compiler"

    def parse(self, text):
        """Parses a log fragment looking for a compiler error for a
        specific file (self.target) and updates the object with the
        extracted information.

        Strategy 1: Search for lines that look like a compiler
        error/warning message (see the regex below).

        Strategy 2: Search for a line that contains the target string,
        then look for the error block starting after it, where the error
        block starts with the first unindented line and continues until
        the end of the text.

        Parameters:
          text (str): the text log containing the compiler error

        Returns the position in `text' where the error block ends (if
        found).
        """
        end = 0
        # Strategy 1
        file_pattern = os.path.splitext(self.target)[0]
        match = re.search(f'^(?P<src_file>{file_pattern}.*?):(?P<location>.*?): (?P<type>.*?):',
                          text, flags=re.MULTILINE)
        if match:
            self._report = text[match.start():]
            self.src_file = match.group('src_file')
            self.location = match.group('location')
            self.error_type += f" {match.group('type')}"
            return len(text)
        # Strategy 2
        match = re.search(self.target, text)
        if not match:
            return end
        block_start = match.end()
        match = re.search(r'^[^\s]+.*$', text[block_start:], flags=re.MULTILINE)
        if match:
            self._report += text[block_start + match.start():]
            end = len(text)
        return end


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
        self.error_type = "Kbuild/Make"
        match = re.finditer(r'\*\*\*.*', text)
        for m in match:
            self._report += f"{m.group(0)}\n"
            end = m.end()
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
        self.error_type = "Kbuild/modpost"
        match = re.finditer(r'ERROR: modpost: .*', text)
        for m in match:
            self._report += f"{m.group(0)}\n"
            end = m.end()
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
        self.error_type = "Kbuild/Other"
        end = 0
        if self.target:
            match = re.search(self.target, text)
            if not match:
                return end
            match = re.finditer(r'^[^\s]+.*$', text[match.end():], flags=re.MULTILINE)
            for m in match:
                self._report += f"{m.group(0)}\n"
                end = m.end()
        return end



class KbuildUnknownError(Error):
    def __init__(self, text):
        super().__init__()
        self.error_type = "Unknown Kbuild/Make error"
        self._report = text
