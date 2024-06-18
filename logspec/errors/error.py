# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

class Error():
    def __init__(self):
        self.error_type = None
        self.error_summary = ""
        self._report = ""

    def to_json(self, full=False):
        """Returns a dict with the fields to serialize. By default, this
        excludes all fields starting with '_'. If `full' is set to True,
        all fields are included.
        """
        if full:
            return {k: v for k, v in vars(self).items()}
        return {k: v for k, v in vars(self).items() if not k.startswith('_')}

