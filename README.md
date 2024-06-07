# logspec: the test log spectrometer

> **_Last modified:_** Jun 7, 2024

> **_NOTE:_** Work in progress. The interface and the output are still
> expected to change.

logspec is a context-sensitive parser for output logs, specifically
targeted at test output logs but usable on any kind of log.

The purpose of this tool is to extract structured data from a log to
highlight the interesting parts of it[^1] and to make that information
easy to post-process and store in a database for future reference.

## Usage

logspec expects a log file to parse and a suitable parsing model to use
for the file. These models are defined as finite state machines in
[fsm_defs.yaml](fsm_defs.yaml) by default:

    ./logspec.py tests/logs/kbuild/kbuild_001.log kbuild

where `tests/logs/kbuild/kbuild_001.log` is the file to parse and
`kbuild` is the FSM to use for this type of log.

By default, it'll print the extracted data as JSON:

    {
        "errors": [
            {
                "error_type": "Compiler error",
                "location": "1266:3",
                "script": "scripts/Makefile.build:244",
                "src_file": "drivers/gpu/drm/nouveau/nvkm/subdev/gsp/r535.c",
                "target": "drivers/gpu/drm/nouveau/nvkm/subdev/gsp/r535.o"
            }
        ]
    }

"Hidden" fields aren't printed unless the `--json-full` flag is
used. This same example looks like this with `--json-full` enabled:

    {
        "_match_end": 693999,
        "errors": [
            {
                "_report": "drivers/gpu/drm/nouveau/nvkm/subdev/gsp/r535.c:1266:3: error: label at end of compound statement\n 1266 |   default:\n      |   ^~~~~~~\n  CC [M]  drivers/net/wireless/marvell/mwifiex/ie.o\n",
                "error_type": "Compiler error",
                "location": "1266:3",
                "script": "scripts/Makefile.build:244",
                "src_file": "drivers/gpu/drm/nouveau/nvkm/subdev/gsp/r535.c",
                "target": "drivers/gpu/drm/nouveau/nvkm/subdev/gsp/r535.o"
            }
        ]
    }

To use a different yaml file for FSM specifications, use the `-d
(--fsm-defs)` argument.

## Installation

To install logspec as a library, run:

    pip install .

## Tests

To run the sanity and coverage tests, run:

    ./run_tests.sh

To get the output in TAP format, append the `--tap` option.

## Coverage

Support for different types of logs will be added incrementally. You can
check the current coverage support and the types of logs currently
supported in [tests/logs/index.txt](tests/logs/index.txt).

---

[^1]: according to the specified parsing model
