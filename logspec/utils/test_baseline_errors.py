# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

import re

from logspec.utils.defs import *


def find_test_baseline_error(text):
    end = 0
    match = re.search(r'kern  :(?P<message>.*)', text)
    if not match:
        return None
    return {
        'error': match.group('message'),
        '_end': match.end(),
    }
