# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

import os.path
import logging
import re

from logspec.utils.defs import *
from logspec.errors.kbuild import *


def is_object_file(target):
    """Returns True if `target' looks like an object or "output" file
    according to a list of known extensions. Returns False otherwise.
    """
    known_extensions = [
        '.o',
        '.s',
    ]
    base, ext = os.path.splitext(target)
    if not ext or ext not in known_extensions:
        return False
    return True


def is_other_compiler_target(target, text):
    """Returns True if `target` can be identified to be a compiler
    target file based on its appearance in `text`. Returns False
    otherwise.
    """
    target_base = os.path.splitext(os.path.basename(target))[0]
    match = re.search(rf'{target_base}(\.\w+)?:', text)
    if match:
        return True
    else:
        return False


def is_kbuild_target(target):
    """Returns True if `target' looks like a Kbuild target. Returns
    False otherwise.
    """
    known_targets = [
        'modules',
        'Module.symvers',
    ]
    if target in known_targets:
        return True
    return False


def find_kbuild_error(text):
    """Find a kbuild error in a text segment.

    Currently supported:
      - compiler errors (C)
      - Make / Kbuild runtime errors

    Parameters:
      text (str): the log or text fragment to parse

    Returns:
    If an error report was found, it returns a dict containing:
      'error': specific error object containing the structured error info
      'end': position in the text right after the parsed block
    None if no error report was found.
    """
    end = 0
    match = re.search(r'make.*?: \*\*\* (?P<error_str>.*)', text)
    if not match:
        return None
    error_str = match.group('error_str')
    start = match.start()
    end = match.end()
    match = re.search(r'\[(?P<script>.*?): (?P<target>.*?)\] Error', error_str)
    if match:
        script = match.group('script')
        target = match.group('target')
        logging.debug(f"[find_kbuild_error] script: {script}, target: {target}")
        error = None
        # Kbuild error classification
        if is_object_file(target) or is_other_compiler_target(target, text[:start]):
            error = KbuildCompilerError(script=script, target=target)
        elif 'modpost' in script:
            error = KbuildModpostError(script=script, target=target)
        elif is_kbuild_target(target):
            error = KbuildProcessError(script=script, target=target)
        else:
            error = KbuildGenericError(script=script, target=target)
        if error:
            text = text[:start]
            error.parse(text)
            return {
                'error': error,
                '_end': end,
            }
    else:
        error = KbuildUnknownError(error_str)
        return {
            'error': error,
            '_end': end,
        }
