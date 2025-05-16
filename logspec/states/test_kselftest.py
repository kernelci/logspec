# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Helen Koike <helen.koike@collabora.com>

import re
from logspec.parser_classes import State
from logspec.utils.test_kselftest_errors import find_test_kselftest_error
from logspec.parser_loader import register_state

MODULE_NAME = 'test_kselftest'


# State functions

def detect_test_kselftest(text, start=None, end=None):
    start_tags = [
        'kselftest.sh',
    ]
    if start or end:
        text = text[start:end]
    data = {
        '_signature_fields': [
            'test.kselftest.script_call',
            'test.kselftest.start',
        ],
    }
    regex = '|'.join(start_tags)

    # Check for test start
    match = re.search(regex, text)
    if not match:
        data['test.kselftest.script_call'] = False
        data['test.kselftest.start'] = False
        data['_match_end'] = end if end else len(text)
        data['_summary'] = "Kselftest not detected"
        return data

    test_start = match.end()
    test_end = None
    data['test.kselftest.script_call'] = True
    data['_summary'] = "Kselftest started"

    # Check for test end, consider the last line starting with "ok \d+ selftests:"
    # or "not ok \d+ selftests:"
    regex = r'(?:not )?ok \d+ selftests:'
    matches = list(re.finditer(regex, text[test_start:]))
    match = matches[-1] if matches else None
    if match:
        data['test.kselftest.start'] = True
        test_end = test_start + match.end()
        data['_match_end'] = test_end + start if start else test_end
    else:
        data['test.kselftest.start'] = False
        # TODO: check if this is correct
        data['_match_end'] = end if end else len(text)

    # Check for linux-specific errors in the log. If the `done'
    # condition was found, search only before it. Otherwise search in
    # the full log.
    data['errors'] = []
    while True:
        error = find_test_kselftest_error(text[test_start:test_end])
        if not error:
            break
        data['errors'].append(error['error'])
        test_start += error['_end']
    return data


# Create and register states

register_state(
    MODULE_NAME,
    State(
        name="Kselftest test",
        description="Search and process a kseftest test",
        function=detect_test_kselftest),
    'test_kselftest')
