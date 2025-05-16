# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

import os
import json
import pytest

import tests.setup
from logspec.main import load_parser_and_parse_log, format_data_output


LOG_DIR = 'tests/logs/linux_boot'


@pytest.mark.parametrize('log_file, parser_id, expected', [
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
        "linux.boot.kernel_started": True,
        "linux.boot.prompt": False,
     }),

    # Kernel started loading but didn't reach a cmdline prompt. No errors found.
    ('linux_boot_003.log',
     'generic_linux_boot',
     {
         "bootloader.done": True,
         "errors": [],
         "linux.boot.kernel_started": False,
         "linux.boot.prompt": False,
     }),

    # Command-line prompt reached, no errors found.
    ('linux_boot_004.log',
     'generic_linux_boot',
     {
        "bootloader.done": True,
        "errors": [
            {
               "error_summary": "Direct firmware load for rtl_nic/rtl8153b-2.fw failed with error -2",
               "error_type": "linux.kernel.error_return_code"
            },
            {
               "error_summary": "probe of thermal-sensor2 failed with error -22",
               "error_type": "linux.kernel.error_return_code"
            },
            {
               "error_summary": "probe of thermal-sensor1 failed with error -22",
               "error_type": "linux.kernel.error_return_code"
            },
            {
               "error_summary": "Direct firmware load for regulatory.db failed with error -2",
               "error_type": "linux.kernel.error_return_code"
            }
        ],
        "linux.boot.kernel_started": True,
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
               "error_summary": "Direct firmware load for i915/bxt_dmc_ver1_07.bin failed with error -2",
               "error_type": "linux.kernel.error_return_code"
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
                "call_trace": [],
                "error_summary": "Fatal exception",
                "error_type": "linux.kernel.panic",
                "hardware": None
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
               "error_summary": "Direct firmware load for i915/bxt_dmc_ver1_07.bin failed with error -2",
               "error_type": "linux.kernel.error_return_code"
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
                    "? 0xffffffffc0203000",
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
                    "coreboot_table",
                    "cros_usbpd_notify",
                    "industrialio",
                    "snd_timer"
                ]
            },
            {
                "call_trace": [],
                "error_summary": "Fatal exception",
                "error_type": "linux.kernel.panic",
                "hardware": None
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
               "error_summary": "Direct firmware load for i915/bxt_dmc_ver1_07.bin failed with error -2",
               "error_type": "linux.kernel.error_return_code"
            },
            {
               "error_summary": "Direct firmware load for intel/ibt-hw-37.8.10-fw-22.50.19.14.f.bseq failed with error -2",
               "error_type": "linux.kernel.error_return_code"
            },
            {
               "error_summary": "Direct firmware load for intel/ibt-hw-37.8.bseq failed with error -2",
               "error_type": "linux.kernel.error_return_code"
            },
            {
               "error_summary": "Direct firmware load for regulatory.db failed with error -2",
               "error_type": "linux.kernel.error_return_code"
            }
        ],
        "linux.boot.kernel_started": True,
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
             },
             {
               "error_summary": "Direct firmware load for regulatory.db failed with error -2",
               "error_type": "linux.kernel.error_return_code"
             },
             {
               "error_summary": "Direct firmware load for rtl_bt/rtl8822cu_fw.bin failed with error -2",
               "error_type": "linux.kernel.error_return_code"
             }
         ],
         "linux.boot.kernel_started": True,
         "linux.boot.prompt": True,
     }),

    # Special boot kernel_started
    ('linux_boot_007.log',
     'generic_linux_boot',
     {
         "bootloader.done": True,
         "errors": [
             {
                 "error_summary": "shift-out-of-bounds: shift exponent 32 is too large for 32-bit type 'long unsigned int'",
                 "error_type": "linux.kernel.ubsan",
                 "hardware": "Google Shuboz/Shuboz, BIOS Google_Shuboz.13434.780.2022_10_13_1418 09/12/2022",
                 "location": "./include/linux/log2.h:57:13"
             },
             {
                 "call_trace": [
                     "? show_trace_log_lvl+0xba/0x1f8",
                     "? show_trace_log_lvl+0xba/0x1f8",
                     "? __wake_up_common_lock+0x5f/0x90",
                     "? show_regs.part.0+0x17/0x1a",
                     "? __die_body.cold+0x7/0xc",
                     "? __die+0x1c/0x21",
                     "? no_context.constprop.0+0x8f/0xc0",
                     "? __bad_area_nosemaphore.constprop.0+0x33/0x130",
                     "? bad_area_nosemaphore+0xa/0x10",
                     "? do_user_addr_fault+0x18d/0x360",
                     "? exc_page_fault+0x42/0x160",
                     "? doublefault_shim+0x140/0x140",
                     "? handle_exception+0x133/0x133",
                     "? doublefault_shim+0x140/0x140",
                     "? __wake_up_common+0x42/0x150",
                     "? doublefault_shim+0x140/0x140",
                     "? __wake_up_common+0x42/0x150",
                     "? _raw_spin_lock_irqsave+0x35/0x50",
                     "__wake_up_common_lock+0x5f/0x90",
                     "__wake_up+0xd/0x20",
                     "amdgpu_debugfs_wait_dump+0x1c/0x40",
                     "amdgpu_device_pre_asic_reset+0x2d/0x320",
                     "amdgpu_device_gpu_recover.cold+0x3ad/0x70a",
                     "amdgpu_job_timedout+0xea/0x110",
                     "drm_sched_job_timedout+0x52/0xd0",
                     "process_one_work+0x22e/0x450",
                     "worker_thread+0x128/0x420",
                     "kthread+0x10c/0x120",
                     "? process_one_work+0x450/0x450",
                     "? kthread_park+0x90/0x90",
                     "ret_from_fork+0x1c/0x28"
                 ],
                 "error_summary": "kernel NULL pointer dereference, address: 00000000",
                 "error_type": "linux.kernel.bug",
                 "hardware": "Google Shuboz/Shuboz, BIOS Google_Shuboz.13434.780.2022_10_13_1418 09/12/2022",
                 "modules": []
             },
             {
                 "call_trace": [
                     "? show_stack+0x35/0x3b",
                     "dump_stack+0x6d/0x8b",
                     "___might_sleep.cold+0xe0/0xf1",
                     "__might_sleep+0x43/0x90",
                     "exit_signals+0x1a/0x310",
                     "do_exit+0x9c/0x560",
                     "? kthread+0x10c/0x120",
                     "make_task_dead+0x2a/0x30",
                     "rewind_stack_and_make_dead+0x11/0x18",
                     "memory used by lock dependency info: 3805 kB",
                     "memory used for stack traces: 2112 kB",
                     "per task-struct memory footprint: 1344 bytes",
                     "#2",
                     "#3",
                     "? show_stack+0x35/0x3b",
                     "dump_stack+0x6d/0x8b",
                     "create_object.isra.0.cold+0x10/0x74",
                     "kmemleak_alloc+0x1f/0x30",
                     "kmem_cache_alloc+0xc3/0x250",
                     "? getname_kernel+0x1f/0xf0",
                     "getname_kernel+0x1f/0xf0",
                     "kern_path_create+0x10/0x30",
                     "devtmpfs_work_loop+0xc3/0x270",
                     "devtmpfsd+0x6c/0x90",
                     "kthread+0x10c/0x120",
                     "? clkdev_alloc+0x20/0x20",
                     "? kthread_park+0x90/0x90",
                     "ret_from_fork+0x1c/0x28",
                     "? show_stack+0x35/0x3b",
                     "dump_stack+0x6d/0x8b",
                     "ubsan_epilogue+0x8/0x2b",
                     "__ubsan_handle_shift_out_of_bounds.cold+0x58/0xed",
                     "__roundup_pow_of_two+0x25/0x31",
                     "amdgpu_vm_adjust_size.cold+0x57/0x1f9",
                     "? amdgpu_ras_init+0x193/0x230",
                     "gmc_v9_0_sw_init+0xe8/0x3f0",
                     "amdgpu_device_ip_init+0x9c/0x56c",
                     "amdgpu_device_init.cold+0x5f1/0x8a6",
                     "amdgpu_driver_load_kms+0x13/0x130",
                     "amdgpu_pci_probe+0xe7/0x170",
                     "? amdgpu_pmops_runtime_suspend+0x140/0x140",
                     "pci_device_probe+0x9a/0x110",
                     "really_probe+0x21d/0x400",
                     "driver_probe_device+0x54/0xc0",
                     "device_driver_attach+0xc1/0xd0",
                     "__driver_attach+0x4c/0x100",
                     "? device_driver_attach+0xd0/0xd0",
                     "bus_for_each_dev+0x66/0xa0",
                     "driver_attach+0x14/0x20",
                     "? device_driver_attach+0xd0/0xd0",
                     "bus_add_driver+0xf2/0x1a0",
                     "driver_register+0x77/0xd0",
                     "? drm_sched_fence_slab_init+0x2c/0x2c",
                     "__pci_register_driver+0x4d/0x60",
                     "amdgpu_init+0x66/0x70",
                     "do_one_initcall+0x59/0x220",
                     "do_initcalls+0xf4/0x112",
                     "kernel_init_freeable+0x177/0x1a3",
                     "? rest_init+0x31b/0x31b",
                     "kernel_init+0x9/0xf5",
                     "? rest_init+0x31b/0x31b",
                     "ret_from_fork+0x1c/0x28",
                     "? show_stack+0x35/0x3b",
                     "dump_stack+0x6d/0x8b",
                     "register_lock_class+0x67d/0x690",
                     "__lock_acquire+0x45/0x920",
                     "lock_acquire+0x8c/0x230",
                     "? __wake_up_common_lock+0x47/0x90",
                     "? mark_held_locks+0x3f/0x70",
                     "? wait_task_inactive+0x134/0x1d0",
                     "_raw_spin_lock_irqsave+0x2e/0x50",
                     "? __wake_up_common_lock+0x47/0x90",
                     "__wake_up_common_lock+0x47/0x90",
                     "__wake_up+0xd/0x20",
                     "amdgpu_debugfs_wait_dump+0x1c/0x40",
                     "amdgpu_device_pre_asic_reset+0x2d/0x320",
                     "amdgpu_device_gpu_recover.cold+0x3ad/0x70a",
                     "amdgpu_job_timedout+0xea/0x110",
                     "drm_sched_job_timedout+0x52/0xd0",
                     "process_one_work+0x22e/0x450",
                     "worker_thread+0x128/0x420",
                     "kthread+0x10c/0x120",
                     "? process_one_work+0x450/0x450",
                     "? kthread_park+0x90/0x90",
                     "ret_from_fork+0x1c/0x28",
                     "? show_trace_log_lvl+0xba/0x1f8",
                     "? show_trace_log_lvl+0xba/0x1f8",
                     "? __wake_up_common_lock+0x5f/0x90",
                     "? show_regs.part.0+0x17/0x1a",
                     "? __die_body.cold+0x7/0xc",
                     "? __die+0x1c/0x21",
                     "? no_context.constprop.0+0x8f/0xc0",
                     "? __bad_area_nosemaphore.constprop.0+0x33/0x130",
                     "? bad_area_nosemaphore+0xa/0x10",
                     "? do_user_addr_fault+0x18d/0x360",
                     "? exc_page_fault+0x42/0x160",
                     "? doublefault_shim+0x140/0x140",
                     "? handle_exception+0x133/0x133",
                     "? doublefault_shim+0x140/0x140",
                     "? __wake_up_common+0x42/0x150",
                     "? doublefault_shim+0x140/0x140",
                     "? __wake_up_common+0x42/0x150",
                     "? _raw_spin_lock_irqsave+0x35/0x50",
                     "__wake_up_common_lock+0x5f/0x90",
                     "__wake_up+0xd/0x20",
                     "amdgpu_debugfs_wait_dump+0x1c/0x40",
                     "amdgpu_device_pre_asic_reset+0x2d/0x320",
                     "amdgpu_device_gpu_recover.cold+0x3ad/0x70a",
                     "amdgpu_job_timedout+0xea/0x110",
                     "drm_sched_job_timedout+0x52/0xd0",
                     "process_one_work+0x22e/0x450",
                     "worker_thread+0x128/0x420",
                     "kthread+0x10c/0x120",
                     "? process_one_work+0x450/0x450",
                     "? kthread_park+0x90/0x90",
                     "ret_from_fork+0x1c/0x28"
                 ],
                 "error_summary": "sleeping function called from invalid context at include/linux/percpu-rwsem.h:49",
                 "error_type": "linux.kernel.bug",
                 "hardware": "Google Shuboz/Shuboz, BIOS Google_Shuboz.13434.780.2022_10_13_1418 09/12/2022",
                 "location": "include/linux/percpu-rwsem.h:49",
                 "modules": []
             },
             {
                 "call_trace": [
                     "? show_stack+0x35/0x3b",
                     "dump_stack+0x6d/0x8b",
                     "___might_sleep.cold+0xe0/0xf1",
                     "__might_sleep+0x43/0x90",
                     "exit_signals+0x1a/0x310",
                     "do_exit+0x9c/0x560",
                     "? kthread+0x10c/0x120",
                     "make_task_dead+0x2a/0x30",
                     "rewind_stack_and_make_dead+0x11/0x18"
                 ],
                 "error_summary": "sleeping function called from invalid context at include/linux/percpu-rwsem.h:49",
                 "error_type": "linux.kernel.bug",
                 "hardware": "Google Shuboz/Shuboz, BIOS Google_Shuboz.13434.780.2022_10_13_1418 09/12/2022",
                 "location": "include/linux/percpu-rwsem.h:49"
             },
             {
                 "call_trace": [],
                 "error_summary": "workqueue lockup",
                 "error_type": "linux.kernel.bug",
                 "hardware": None
             },
             {
                 "call_trace": [],
                 "error_summary": "workqueue lockup",
                 "error_type": "linux.kernel.bug",
                 "hardware": None
             },
             {
                 "call_trace": [],
                 "error_summary": "workqueue lockup",
                 "error_type": "linux.kernel.bug",
                 "hardware": None
             },
             {
                 "call_trace": [],
                 "error_summary": "workqueue lockup",
                 "error_type": "linux.kernel.bug",
                 "hardware": None
             },
             {
                 "call_trace": [],
                 "error_summary": "workqueue lockup",
                 "error_type": "linux.kernel.bug",
                 "hardware": None
             },
             {
                 "call_trace": [],
                 "error_summary": "workqueue lockup",
                 "error_type": "linux.kernel.bug",
                 "hardware": None
             },
             {
                 "call_trace": [],
                 "error_summary": "workqueue lockup",
                 "error_type": "linux.kernel.bug",
                 "hardware": None
             },
             {
                 "call_trace": [],
                 "error_summary": "workqueue lockup",
                 "error_type": "linux.kernel.bug",
                 "hardware": None
             },
             {
                 "call_trace": [],
                 "error_summary": "workqueue lockup",
                 "error_type": "linux.kernel.bug",
                 "hardware": None
             },
             {
                 "call_trace": [],
                 "error_summary": "workqueue lockup",
                 "error_type": "linux.kernel.bug",
                 "hardware": None
             }
         ],
         "linux.boot.kernel_started": True,
         "linux.boot.prompt": False
     }),

    # Kernel panic incomplete due reboot
    ('linux_boot_008.log',
     'generic_linux_boot',
     {
         "bootloader.done": True,
         "errors": [
             {
                 "error_summary": "probe with driver clk-mt8186-cam failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-cam failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-cam failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-img failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-img failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-imp_iic_wrap failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-ipe failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-mdp failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-mfg failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-vdec failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-venc failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-wpe failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver coreboot_table failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for regulatory.db failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for mediatek/BT_RAM_CODE_MT7961_1_2_hdr.bin failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "call_trace": [
                     "show_stack+0x20/0x38 (C)",
                     "dump_stack_lvl+0xc8/0xf8",
                     "dump_stack+0x18/0x28",
                     "panic+0x3d0/0x438",
                     "do_exit+0x84c/0xa28",
                     "__arm64_sys_exit+0x20/0x28",
                     "invoke_syscall+0x70/0x100",
                     "el0_svc_common.constprop.0+0x48/0xf0",
                     "do_el0_svc+0x24/0x38",
                     "el0_svc+0x34/0xf0",
                     "el0t_64_sync_handler+0x10c/0x138",
                     "el0t_64_sync+0x1b0/0x1b8"
                 ],
                 "error_summary": "Attempted to kill init! exitcode=0x00000200",
                 "error_type": "linux.kernel.panic",
                 "hardware": "Google Steelix board (DT)"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-cam failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-cam failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-cam failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-img failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-img failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-imp_iic_wrap failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-ipe failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-mdp failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-mfg failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-vdec failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-venc failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver clk-mt8186-wpe failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "probe with driver coreboot_table failed with error -22",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for regulatory.db failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "error_summary": "Direct firmware load for mediatek/BT_RAM_CODE_MT7961_1_2_hdr.bin failed with error -2",
                 "error_type": "linux.kernel.error_return_code"
             },
             {
                 "call_trace": [
                     "show_stack+0x20/0x38 (C)",
                     "dump_stack_lvl+0xc8/0xf8",
                     "dump_stack+0x18/0x28",
                     "panic+0x3d0/0x438",
                     "do_exit+0x84c/0xa28",
                     "__arm64_sys_exit+0x20/0x28",
                     "invoke_syscall+0x70/0x100",
                     "el0_svc_common.constprop.0+0x48/0xf0",
                     "do_el0_svc+0x24/0x38",
                     "el0_svc+0x34/0xf0",
                     "el0t_64_sync_handler+0x10c/0x138",
                     "el0t_64_sync+0x1b0/0x1b8"
                 ],
                 "error_summary": "Attempted to kill init! exitcode=0x00000200",
                 "error_type": "linux.kernel.panic",
                 "hardware": "Google Steelix board (DT)"
             }
         ],
         "linux.boot.kernel_started": True,
         "linux.boot.prompt": False
     }),
])
def test_linux_boot(log_file, parser_id, expected):
    log_file = os.path.join(LOG_DIR, log_file)
    parsed_data = load_parser_and_parse_log(log_file, parser_id, tests.setup.PARSER_DEFS_FILE)
    expected_as_str = json.dumps(expected, indent=4, sort_keys=True, ensure_ascii=False)
    parsed_data_as_str = format_data_output(parsed_data)
    assert expected_as_str == parsed_data_as_str
