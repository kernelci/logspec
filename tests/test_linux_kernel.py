# SPDX-License-Identifier: LGPL-2.1-or-later

from logspec.utils.linux_kernel_errors import find_error_report


def test_bug_without_end_marker_stops_after_contiguous_call_trace():
    report_text = (
        "[    1.000000] BUG: synthetic failure\n"
        "[    1.000001] Hardware name: Test board (DT)\n"
        "[    1.000002] Call trace:\n"
        "[    1.000003]  first+0x1/0x2\n"
        "[    1.000004]  second+0x1/0x2\n"
    )
    text = report_text + (
        "[   20.000000] unrelated watchdog output\n"
        "[   20.000001] Call trace:\n"
        "[   20.000002]  unrelated+0x1/0x2\n"
    )

    result = find_error_report(text)

    assert result['_end'] == len(report_text)
    assert result['error']._report == report_text
    assert result['error'].call_trace == [
        'first+0x1/0x2',
        'second+0x1/0x2',
    ]


def test_bug_without_end_marker_stops_at_reboot_boundary():
    report_text = (
        "[    2.000000] BUG: truncated by reboot\n"
        "[    2.000001] in_atomic(): 1, irqs_disabled(): 1\n"
    )
    text = report_text + (
        "bootloader restart\n"
        "[    0.000000] Hardware name: Wrong boot (DT)\n"
    )

    result = find_error_report(text)

    assert result['_end'] == len(report_text)
    assert result['error']._report == report_text
    assert result['error'].hardware is None
