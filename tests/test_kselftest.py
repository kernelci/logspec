# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2025 Collabora Limited
# Author: Helen Koike <helen.koike@collabora.com>

import os
import json
import pytest

import tests.setup
from logspec.main import load_parser_and_parse_log, format_data_output
from logspec.utils.defs import JsonSerialize


LOG_DIR = 'tests/logs/test_kselftest'


@pytest.mark.parametrize('log_file, parser_id, expected',[
    # Kselftest with an error
    ('test_kselftest_001.log',
     'test_kselftest',
     {
         "bootloader.done": True,
         "errors": [
             {
                 "error_summary": "Direct firmware load for regulatory.db failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for iwlwifi-QuZ-a0-hr-b0-59.ucode failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for iwlwifi-QuZ-a0-hr-b0-58.ucode failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for iwlwifi-QuZ-a0-hr-b0-57.ucode failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for iwlwifi-QuZ-a0-hr-b0-56.ucode failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for iwlwifi-QuZ-a0-hr-b0-55.ucode failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for iwlwifi-QuZ-a0-hr-b0-54.ucode failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for iwlwifi-QuZ-a0-hr-b0-53.ucode failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for iwlwifi-QuZ-a0-hr-b0-52.ucode failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for iwlwifi-QuZ-a0-hr-b0-51.ucode failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for iwlwifi-QuZ-a0-hr-b0-50.ucode failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for iwlwifi-QuZ-a0-hr-b0-49.ucode failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for iwlwifi-QuZ-a0-hr-b0-48.ucode failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for iwlwifi-QuZ-a0-hr-b0-47.ucode failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for iwlwifi-QuZ-a0-hr-b0-46.ucode failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for iwlwifi-QuZ-a0-hr-b0-45.ucode failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for iwlwifi-QuZ-a0-hr-b0-44.ucode failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for iwlwifi-QuZ-a0-hr-b0-43.ucode failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for iwlwifi-QuZ-a0-hr-b0-42.ucode failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for iwlwifi-QuZ-a0-hr-b0-41.ucode failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for iwlwifi-QuZ-a0-hr-b0-40.ucode failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for iwlwifi-QuZ-a0-hr-b0-39.ucode failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for intel/ibt-19-0-4.sfi failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for rtl_nic/rtl8168h-2.fw failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "not ok 1 selftests: exec: execveat # exit=1",
                 "error_type": "linux.kselftest"
             }
         ],
         "linux.boot.kernel_started": True,
         "linux.boot.prompt": True,
         "test.kselftest.script_call": True,
         "test.kselftest.start": True
     }),
])
def test_kbuild(log_file, parser_id, expected):
    log_file = os.path.join(LOG_DIR, log_file)
    parsed_data = load_parser_and_parse_log(log_file, parser_id, tests.setup.PARSER_DEFS_FILE)
    expected_as_str = json.dumps(expected, indent=4, sort_keys=True, ensure_ascii=False)
    parsed_data_as_str = format_data_output(parsed_data)
    assert expected_as_str == parsed_data_as_str
