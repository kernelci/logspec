# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

import re

from logspec.utils.defs import *
from logspec.errors.test import *


def find_test_baseline_dmesg_error(text):
    end = 0
    match = re.search(r'kern  :(?P<message>.*)', text)
    if not match:
        return None
    error = TestError()
    error.error_type += ".baseline.dmesg"
    error.error_summary = match.group('message')
    # Parsing on a generic TestError object simply generates a
    # signature, we already did the parsing above
    error.parse(text)
    return {
        'error': error,
        '_end': match.end(),
    }
