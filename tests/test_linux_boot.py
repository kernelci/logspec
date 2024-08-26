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


LOG_DIR = 'tests/logs/linux_boot'


@pytest.mark.parametrize('log_file, parser_id, expected',[
    # Not even reached the kernel loading stage
    ('linux_boot_001.log',
     'generic_linux_boot',
     {
         "bootloader.done": False,
         "errors": [],
     }),

    # Kernel panic before reaching the command line prompt.
    #
    # Example:
    #
    # Kernel panic - not syncing: VFS: Unable to mount root fs on "/dev/ram0" or unknown-block(1,0)
    ('linux_boot_002.log',
     'generic_linux_boot',
     {
         "bootloader.done": True,
         "errors": [
            {
                "call_trace": [
                    "unwind_backtrace from show_stack+0x10/0x14",
                    "show_stack from dump_stack_lvl+0x50/0x64",
                    "dump_stack_lvl from panic+0x104/0x364",
                    "panic from mount_root_generic+0x270/0x278",
                    "mount_root_generic from prepare_namespace+0x1f8/0x248",
                    "prepare_namespace from kernel_init+0x1c/0x12c",
                    "kernel_init from ret_from_fork+0x14/0x28"
                ],
                "error_summary": "VFS: Unable to mount root fs on \"/dev/ram0\" or unknown-block(1,0)",
                "error_type": "linux.kernel.panic",
                "hardware": "BCM2835"
            },
            {
                "call_trace": [
                    "unwind_backtrace from show_stack+0x10/0x14",
                    "show_stack from dump_stack_lvl+0x50/0x64",
                    "dump_stack_lvl from panic+0x104/0x364",
                    "panic from mount_root_generic+0x270/0x278",
                    "mount_root_generic from prepare_namespace+0x1f8/0x248",
                    "prepare_namespace from kernel_init+0x1c/0x12c",
                    "kernel_init from ret_from_fork+0x14/0x28"
                ],
                "error_summary": "VFS: Unable to mount root fs on \"/dev/ram0\" or unknown-block(1,0)",
                "error_type": "linux.kernel.panic",
                "hardware": "BCM2835"
            },
            {
                "call_trace": [
                    "unwind_backtrace from show_stack+0x10/0x14",
                    "show_stack from dump_stack_lvl+0x50/0x64",
                    "dump_stack_lvl from panic+0x104/0x364",
                    "panic from mount_root_generic+0x270/0x278",
                    "mount_root_generic from prepare_namespace+0x1f8/0x248",
                    "prepare_namespace from kernel_init+0x1c/0x12c",
                    "kernel_init from ret_from_fork+0x14/0x28"
                ],
                "error_summary": "VFS: Unable to mount root fs on \"/dev/ram0\" or unknown-block(1,0)",
                "error_type": "linux.kernel.panic",
                "hardware": "BCM2835"
            },
        ],
        "linux.boot.prompt": False,
     }),

    # Kernel started loading but didn't reach a cmdline prompt. No errors found.
    ('linux_boot_003.log',
     'generic_linux_boot',
     {
         "bootloader.done": True,
         "errors": [],
         "linux.boot.prompt": False,
     }),

    # Command-line prompt reached, no errors found.
    ('linux_boot_004.log',
     'generic_linux_boot',
     {
        "bootloader.done": True,
        "errors": [],
         "linux.boot.prompt": True,
     }),

    # Command-line prompt found, multiple errors found (WARNINGs and BUGs)
    #
    # Examples:
    #
    # ------------[ cut here ]------------
    # missing return thunk: 0xffffffff9e445838-0xffffffff9e44583d: e9 00 00 00 00
    # WARNING: CPU: 0 PID: 0 at arch/x86/kernel/alternative.c:730 apply_returns+0xc0/0x241
    #
    # BUG: unable to handle page fault for address: 0000000000200286
    ('linux_boot_005.log',
     'generic_linux_boot',
    {
        "bootloader.done": True,
        "errors": [
            {
                "call_trace": [
                    "? __warn+0x98/0xda",
                    "? apply_returns+0xc0/0x241",
                    "? report_bug+0x96/0xda",
                    "? handle_bug+0x3c/0x65",
                    "? exc_invalid_op+0x14/0x65",
                    "? asm_exc_invalid_op+0x12/0x20",
                    "? apply_returns+0xc0/0x241",
                    "alternative_instructions+0x7d/0x143",
                    "arch_cpu_finalize_init+0x23/0x42",
                    "start_kernel+0x4da/0x58c",
                    "secondary_startup_64_no_verify+0xac/0xbb"
                ],
                "error_summary": "WARNING at arch/x86/kernel/alternative.c:730 apply_returns+0xc0/0x241",
                "error_type": "linux.kernel.warning",
                "hardware": "Google Coral/Coral, BIOS  09/29/2020",
                "location": "arch/x86/kernel/alternative.c:730 apply_returns+0xc0/0x241",
                "modules": []
            },
            {
                "call_trace": [
                    "? __die_body+0x1b/0x5e",
                    "? no_context+0x36d/0x422",
                    "? mutex_lock+0x1c/0x3b",
                    "? exc_page_fault+0x249/0x3f0",
                    "? asm_exc_page_fault+0x1e/0x30",
                    "? string_nocheck+0x19/0x3d",
                    "string+0x42/0x4b",
                    "vsnprintf+0x21c/0x427",
                    "devm_kvasprintf+0x4a/0x9e",
                    "devm_kasprintf+0x4e/0x69",
                    "? __radix_tree_lookup+0x3a/0xba",
                    "__devm_ioremap_resource+0x7c/0x12d",
                    "intel_pmc_get_resources+0x97/0x29c [intel_pmc_bxt]",
                    "? devres_add+0x2f/0x40",
                    "intel_pmc_probe+0x81/0x176 [intel_pmc_bxt]",
                    "platform_drv_probe+0x2f/0x74",
                    "really_probe+0x15c/0x34e",
                    "driver_probe_device+0x9c/0xd0",
                    "device_driver_attach+0x3c/0x59",
                    "__driver_attach+0xa2/0xaf",
                    "? device_driver_attach+0x59/0x59",
                    "bus_for_each_dev+0x73/0xad",
                    "bus_add_driver+0xd8/0x1d4",
                    "driver_register+0x9e/0xdb",
                    "? 0xffffffffc00b7000",
                    "do_one_initcall+0x90/0x1ae",
                    "? slab_pre_alloc_hook.constprop.0+0x31/0x47",
                    "? kmem_cache_alloc_trace+0xfb/0x111",
                    "do_init_module+0x4b/0x1fd",
                    "__do_sys_finit_module+0x94/0xbf",
                    "__do_fast_syscall_32+0x71/0x86",
                    "do_fast_syscall_32+0x2f/0x6f",
                    "entry_SYSENTER_compat_after_hwframe+0x65/0x77"
                ],
                "error_summary": "unable to handle page fault for address: 0000000000200286",
                "error_type": "linux.kernel.bug",
                "hardware": "Google Coral/Coral, BIOS  09/29/2020",
                "modules": [
                    "ecdh_generic",
                    "elan_i2c",
                    "int340x_thermal_zone"
                    # "acpi_thermal_rel",
                    # "chromeos_pstore",
                    # "coreboot_table",
                    # "ecc",
                    # "ecdh_generic",
                    # "elan_i2c",
                    # "i2c_hid",
                    # "int340x_thermal_zone",
                    # "intel_pmc_bxt(+)",
                    # "pinctrl_broxton"
                ]
            },
            {
                "call_trace": [
                    "? __warn+0x98/0xda",
                    "? apply_returns+0xc0/0x241",
                    "? report_bug+0x96/0xda",
                    "? handle_bug+0x3c/0x65",
                    "? exc_invalid_op+0x14/0x65",
                    "? asm_exc_invalid_op+0x12/0x20",
                    "? apply_returns+0xc0/0x241",
                    "alternative_instructions+0x7d/0x143",
                    "arch_cpu_finalize_init+0x23/0x42",
                    "start_kernel+0x4da/0x58c",
                    "secondary_startup_64_no_verify+0xac/0xbb"
                ],
                "error_summary": "WARNING at arch/x86/kernel/alternative.c:730 apply_returns+0xc0/0x241",
                "error_type": "linux.kernel.warning",
                "hardware": "Google Coral/Coral, BIOS  09/29/2020",
                "location": "arch/x86/kernel/alternative.c:730 apply_returns+0xc0/0x241",
                "modules": []
            },
            {
                "call_trace": [
                    "? __warn+0x98/0xda",
                    "? apply_returns+0xc0/0x241",
                    "? report_bug+0x96/0xda",
                    "? handle_bug+0x3c/0x65",
                    "? exc_invalid_op+0x14/0x65",
                    "? asm_exc_invalid_op+0x12/0x20",
                    "? apply_returns+0xc0/0x241",
                    "alternative_instructions+0x7d/0x143",
                    "arch_cpu_finalize_init+0x23/0x42",
                    "start_kernel+0x4da/0x58c",
                    "secondary_startup_64_no_verify+0xac/0xbb"
                ],
                "error_summary": "WARNING at arch/x86/kernel/alternative.c:730 apply_returns+0xc0/0x241",
                "error_type": "linux.kernel.warning",
                "hardware": "Google Coral/Coral, BIOS  09/29/2020",
                "location": "arch/x86/kernel/alternative.c:730 apply_returns+0xc0/0x241",
                "modules": []
            }
        ],
        "linux.boot.prompt": True,
    }),

    # UBSAN error
    ('linux_boot_006.log',
     'generic_linux_boot',
     {
         "bootloader.done": True,
         "errors": [
             {
                 "error_summary": "shift-out-of-bounds: shift exponent 32 is too large for 32-bit type 'long unsigned int'",
                 "error_type": "linux.kernel.ubsan",
                 "hardware": "Google Shuboz/Shuboz, BIOS Google_Shuboz.13434.780.2022_10_13_1418 09/12/2022",
                 "location": "./include/linux/log2.h:57:13"
             }
         ],
         "linux.boot.prompt": True,
     }),
])
def test_linux_boot(log_file, parser_id, expected):
    log_file = os.path.join(LOG_DIR, log_file)
    parsed_data = load_parser_and_parse_log(log_file, parser_id, tests.setup.PARSER_DEFS_FILE)
    expected_as_str = json.dumps(expected, indent=4, sort_keys=True, ensure_ascii=False)
    parsed_data_as_str = format_data_output(parsed_data)
    assert expected_as_str == parsed_data_as_str
