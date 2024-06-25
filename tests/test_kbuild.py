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


LOG_DIR = 'tests/logs/kbuild'


@pytest.mark.parametrize('log_file, parser_id, expected',[
    # Compiler error in a .c source file.
    #
    # Example:
    #
    # drivers/gpu/drm/nouveau/nvkm/subdev/gsp/r535.c: In function ‘build_registry’:
    # drivers/gpu/drm/nouveau/nvkm/subdev/gsp/r535.c:1266:3: error: label at end of compound statement
    #   1266 |   default:
    #        |   ^~~~~~~
    # make[6]: *** [scripts/Makefile.build:244: drivers/gpu/drm/nouveau/nvkm/subdev/gsp/r535.o] Error 1
    ('kbuild_001.log',
     'kbuild',
     {
         'errors': [
             {
                 "error_summary": "label at end of compound statement",
                 'error_type' : "kbuild.compiler.error",
                 'location'   : "1266:3",
                 'script'     : "scripts/Makefile.build:244",
                 'src_file'   : "drivers/gpu/drm/nouveau/nvkm/subdev/gsp/r535.c",
                 'target'     : "drivers/gpu/drm/nouveau/nvkm/subdev/gsp/r535.o",
             },
         ],
     }),

    # Kbuild/Make error
    #
    # Example:
    #
    # *** The present kernel configuration has modules disabled.
    # *** To use the module feature, please run "make menuconfig" etc.
    # *** to enable CONFIG_MODULES.
    # ***
    # make: *** [Makefile:1953: modules] Error 1
    ('kbuild_002.log',
     'kbuild',
     {
         'errors': [
             {
                 "error_summary": "The present kernel configuration has modules disabled. To use the module feature, please run \"make menuconfig\" etc. to enable CONFIG_MODULES.",
                 'error_type'  : "kbuild.make",
                 'script'      : "Makefile:1953",
                 'target'      : "modules",
             },
         ],
     }),

    # Kbuild modpost error.
    #
    # Example:
    #
    # ERROR: modpost: module binfmt_misc uses symbol d_drop from namespace ANDROID_GKI_VFS_EXPORT_ONLY, but does not import it.
    # ERROR: modpost: module binfmt_misc uses symbol dentry_open from namespace ANDROID_GKI_VFS_EXPORT_ONLY, but does not import it.
    # make[2]: *** [scripts/Makefile.modpost:211: Module.symvers] Error 1
    ('kbuild_003.log',
     'kbuild',
     {
         'errors': [
             {
                 "error_summary": "module binfmt_misc uses symbol d_drop from namespace ANDROID_GKI_VFS_EXPORT_ONLY, but does not import it. module binfmt_misc uses symbol dentry_open from namespace ANDROID_GKI_VFS_EXPORT_ONLY, but does not import it.",
                 'error_type'  : "kbuild.modpost",
                 'script'      : "scripts/Makefile.modpost:211",
                 'target'      : "Module.symvers",
             },
         ],
     }),

    # vmlinux linking error.
    #
    # Example:
    #
    # arm-linux-gnueabihf-ld: kernel/rcu/update.o: in function `rcu_trc_cmpxchg_need_qs':
    # update.c:(.text+0x318): undefined reference to `__bad_cmpxchg'
    # arm-linux-gnueabihf-ld: kernel/rcu/update.o: in function `rcu_read_unlock_trace_special':
    # update.c:(.text+0x3ec): undefined reference to `__bad_cmpxchg'
    # arm-linux-gnueabihf-ld: kernel/rcu/update.o: in function `trc_read_check_handler':
    # update.c:(.text+0x480): undefined reference to `__bad_cmpxchg'
    # arm-linux-gnueabihf-ld: kernel/rcu/update.o: in function `trc_inspect_reader':
    # update.c:(.text+0x1568): undefined reference to `__bad_cmpxchg'
    # arm-linux-gnueabihf-ld: update.c:(.text+0x1598): undefined reference to `__bad_cmpxchg'
    # arm-linux-gnueabihf-ld: kernel/rcu/update.o:update.c:(.text+0x1d10): more undefined references to `__bad_cmpxchg' follow
    # make[2]: *** [scripts/Makefile.vmlinux:34: vmlinux] Error 1
    ('kbuild_004.log',
     'kbuild',
     {
         "errors": [
             {
                 "error_summary": "",
                 "error_type": "kbuild.other",
                 "script": "scripts/Makefile.vmlinux:34",
                 "target": "vmlinux",
             },
         ],
     }),

    # Make error: No rule to make target.
    #
    # Example:
    #
    # make: *** No rule to make target 'Image'.  Stop.
    ('kbuild_005.log',
     'kbuild',
     {
         "errors": [
             {
                 "error_summary": "No rule to make target 'Image'.  Stop.",
                 "error_type": "kbuild.unknown",
             },
         ],
     }),

    # Kbuild error: Can't find default configuration
    #
    # Example:
    #
    # ***
    # *** Can't find default configuration "arch/riscv/configs/nommu_k210_defconfig"!
    # ***
    # make[1]: *** [scripts/kconfig/Makefile:104: nommu_k210_defconfig] Error 1
    ('kbuild_006.log',
     'kbuild',
     {
         "errors": [
             {
                 "error_summary": "Can't find default configuration \"arch/riscv/configs/nommu_k210_defconfig\"!",
                 "error_type": "kbuild.other",
                 "script": "scripts/kconfig/Makefile:104",
                 "target": "nommu_k210_defconfig",
             },
         ],
     }),

    # Compiler error: Error in included file compiling C source to assembler.
    #
    # Example:
    #
    # In file included from ./arch/arm/include/asm/atomic.h:16,
    #                  from ./include/linux/atomic.h:7,
    #                  from ./include/asm-generic/bitops/lock.h:5,
    #                  from ./arch/arm/include/asm/bitops.h:245,
    #                  from ./include/linux/bitops.h:63,
    #                  from ./include/linux/log2.h:12,
    #                  from kernel/bounds.c:13:
    # ./arch/arm/include/asm/cmpxchg.h: In function ‘__cmpxchg’:
    # ./arch/arm/include/asm/cmpxchg.h:167:12: error: implicit declaration of function ‘cmpxchg_emu_u8’ [-Werror=implicit-function-declaration]
    #   167 |   oldval = cmpxchg_emu_u8((volatile u8 *)ptr, old, new);
    #       |            ^~~~~~~~~~~~~~
    # cc1: some warnings being treated as errors
    # make[2]: *** [scripts/Makefile.build:117: kernel/bounds.s] Error 1
    ('kbuild_007.log',
     'kbuild',
     {
         "errors": [
             {
                 "error_summary": "implicit declaration of function ‘cmpxchg_emu_u8’ [-Werror=implicit-function-declaration]",
                 "error_type": "kbuild.compiler.error",
                 "location": "13",
                 "script": "scripts/Makefile.build:117",
                 "src_file": "kernel/bounds.c",
                 "target": "kernel/bounds.s",
             },
         ],
     }),

    # Compiler error:
    #
    #  drivers/gpu/drm/amd/amdgpu/../display/dc/link/link_factory.c: In function ‘construct_phy’:
    #  drivers/gpu/drm/amd/amdgpu/../display/dc/link/link_factory.c:743:1: error: the frame size of 1040 bytes is larger than 1024 bytes [-Werror=frame-larger-than=]
    #    743 | }
    #        | ^
    #  cc1: all warnings being treated as errors
    #  make[6]: *** [scripts/Makefile.build:244: drivers/gpu/drm/amd/amdgpu/../display/dc/link/link_factory.o] Error 1
    ('kbuild_008.log',
     'kbuild',
     {
         "errors": [
             {
                 "error_summary": "the frame size of 1040 bytes is larger than 1024 bytes [-Werror=frame-larger-than=]",
                 "error_type": "kbuild.compiler.error",
                 "location": "743:1",
                 "script": "scripts/Makefile.build:244",
                 "src_file": "drivers/gpu/drm/amd/amdgpu/../display/dc/link/link_factory.c",
                 "target": "drivers/gpu/drm/amd/amdgpu/../display/dc/link/link_factory.o",
             },
         ],
     }),

    # Make error: No rule to make target.
    #
    # Example:
    #
    # make: *** No rule to make target 'tools/build/Makefile.feature'.  Stop.
    ('kbuild_009.log',
     'kbuild',
     {
         "errors": [
             {
                 "error_summary": "No rule to make target 'tools/build/Makefile.feature'.  Stop.",
                 "error_type": "kbuild.unknown",
             },
         ],
     }),
])
def test_kbuild(log_file, parser_id, expected):
    log_file = os.path.join(LOG_DIR, log_file)
    parsed_data = load_parser_and_parse_log(log_file, tests.setup.PARSER_DEFS_FILE, parser_id)
    expected_as_str = json.dumps(expected, indent=4, sort_keys=True, ensure_ascii=False)
    parsed_data_as_str = format_data_output(parsed_data)
    assert expected_as_str == parsed_data_as_str
