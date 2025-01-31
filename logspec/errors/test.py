# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>


from logspec.errors.linux_kernel import *


class TestError(Error):
    """Models a generic test error."""
    def __init__(self):
        super().__init__()
        self.error_type = "test"

    def _parse(self, text):
        """Dummy parse function. The purpose of this is to keep the
        caller code working if it calls parse() to generate the error
        signature"""
        pass


class KselftestError(Error):
    """ Parser for kserlftest errors."""
    def __init__(self):
        super().__init__()
        self.error_type = "linux.kselftest"

    def _parse(self, text):
        """Dummy parse function. The purpose of this is to keep the
        caller code working if it calls parse() to generate the error
        signature"""
        match = re.search(r'(?P<message>not ok \d+ selftests:.*+)', text)
        if not match:
            return None
        self.error_summary = match.group('message')
        report_end = match.end()
        self._report = text[:report_end]
        return report_end
