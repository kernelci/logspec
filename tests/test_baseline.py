# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

import os
import json
import pytest

import tests.setup
from logspec.main import load_parser_and_parse_log, format_data_output
from logspec.utils.defs import JsonSerialize


LOG_DIR = 'tests/logs/test_baseline'


@pytest.mark.parametrize('log_file, parser_id, expected',[
    # Linux boot OK but baseline test not detected
    ('test_baseline_001.log',
     'test_baseline',
     {
         "bootloader.done": True,
         "errors": [],
         "linux.boot.kernel_started": True,
         "linux.boot.prompt": True,
         "test.baseline.start": False,
     }),

    # Baseline test detected with no errors
    ('test_baseline_002.log',
     'test_baseline',
     {
         "bootloader.done": True,
         "errors": [],
         "linux.boot.kernel_started": True,
         "linux.boot.prompt": True,
         "test.baseline.start": True,
     }),

    # dmesg emerg errors
    ('test_baseline_003.log',
     'test_baseline',
     {
         "bootloader.done": True,
         "errors": [
             {
                 "error_summary": "emerg : call_irq_handler: 2.55 No irq handler for vector",
                 "error_type": "test.baseline.dmesg",
             },
             {
                 "error_summary": "emerg : call_irq_handler: 1.55 No irq handler for vector",
                 "error_type": "test.baseline.dmesg",
             },
             {
                 "error_summary": "emerg : call_irq_handler: 3.55 No irq handler for vector",
                 "error_type": "test.baseline.dmesg",
             }
         ],
         "linux.boot.kernel_started": True,
         "linux.boot.prompt": True,
         "test.baseline.start": True,
     }),

    # dmesg alert errors plus kernel error messages
    ('test_baseline_004.log',
     'test_baseline',
     {
         "bootloader.done": True,
         "errors": [
             {
                 "call_trace": [
                     "<TASK>",
                     "? __die_body.cold+0x1a/0x1f",
                     "? page_fault_oops+0xa9/0x1e0",
                     "? srso_return_thunk+0x5/0x10",
                     "? usleep_range_state+0x5b/0x90",
                     "? exc_page_fault+0x5d/0x110",
                     "? asm_exc_page_fault+0x22/0x30",
                     "? cros_ec_check_features+0x7/0x110",
                     "cros_typec_probe+0xd4/0x4d9 [cros_ec_typec]",
                     "? srso_return_thunk+0x5/0x10",
                     "platform_probe+0x3a/0xa0",
                     "really_probe.part.0+0xb3/0x2a0",
                     "? srso_return_thunk+0x5/0x10",
                     "__driver_probe_device+0x8c/0x130",
                     "driver_probe_device+0x19/0xe0",
                     "__driver_attach+0x81/0x170",
                     "? __device_attach_driver+0x110/0x110",
                     "bus_for_each_dev+0x73/0xc0",
                     "bus_add_driver+0x119/0x1d0",
                     "driver_register+0x86/0xe0",
                     "? 0xffffffffc04f9000",
                     "do_one_initcall+0x3f/0x1c0",
                     "? srso_return_thunk+0x5/0x10",
                     "? __cond_resched+0x11/0x40",
                     "? srso_return_thunk+0x5/0x10",
                     "? kmem_cache_alloc_trace+0x3a/0x1a0",
                     "do_init_module+0x46/0x220",
                     "__do_sys_finit_module+0xa0/0xe0",
                     "__do_fast_syscall_32+0x63/0xe0",
                     "do_fast_syscall_32+0x2f/0x70",
                     "entry_SYSCALL_compat_after_hwframe+0x6d/0x75",
                     "</TASK>",
                 ],
                 "error_summary": "kernel NULL pointer dereference, address: 00000000000002fc",
                 "error_type": "linux.kernel.bug",
                 "hardware": "Google Shuboz/Shuboz, BIOS Google_Shuboz.13434.780.2022_10_13_1418 09/12/2022",
                 "modules": [
                     "acp_audio_dma",
                     "acpi_als",
                     "chromeos_pstore",
                     "coreboot_table",
                     "cros_ec_typec(+)",
                     "cros_usbpd_notify",
                     "elan_i2c",
                     "i2c_cros_ec_tunnel",
                     "i2c_piix4",
                     "industrialio",
                     "industrialio_triggered_buffer",
                     "kfifo_buf",
                     "regmap_i2c",
                     "roles",
                     "rtw88_core",
                     "rtw88_pci",
                     "snd_compress",
                     "snd_pci_acp3x",
                     "snd_pcm_dmaengine",
                     "snd_soc_acp_da7219mx98357_mach(+)",
                     "snd_soc_core",
                     "snd_soc_cros_ec_codec",
                     "snd_soc_da7219",
                     "snd_soc_max98357a",
                     "sp5100_tco",
                     "typec",
                     "watchdog",
                 ]
             },
             {
                 "error_summary": "alert : BUG: kernel NULL pointer dereference, address: 00000000000002fc",
                 "error_type": "test.baseline.dmesg",
             },
             {
                 "error_summary": "alert : #PF: supervisor read access in kernel mode",
                 "error_type": "test.baseline.dmesg",
             },
             {
                 "error_summary": "alert : #PF: error_code(0x0000) - not-present page",
                 "error_type": "test.baseline.dmesg",
             }
         ],
         "linux.boot.kernel_started": True,
         "linux.boot.prompt": True,
         "test.baseline.start": True,
     }),
])
def test_baseline(log_file, parser_id, expected):
    log_file = os.path.join(LOG_DIR, log_file)
    parsed_data = load_parser_and_parse_log(log_file, parser_id, tests.setup.PARSER_DEFS_FILE)
    expected_as_str = json.dumps(expected, indent=4, sort_keys=True, ensure_ascii=False)
    parsed_data_as_str = format_data_output(parsed_data)
    assert expected_as_str == parsed_data_as_str
