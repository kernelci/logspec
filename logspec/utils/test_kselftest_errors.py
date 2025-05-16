# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

from logspec.errors.test import KselftestError


def find_test_kselftest_error(text):
    error = KselftestError()
    # Parsing on a generic TestError object simply generates a
    # signature, we already did the parsing above
    report_end = error.parse(text)
    if not report_end:
        return None
    return {
        'error': error,
        '_end': report_end,
    }
