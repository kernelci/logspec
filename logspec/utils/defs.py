# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

from json import JSONEncoder

# Pattern to detect a Linux kernel log timestamp
LINUX_TIMESTAMP = r'\[[ \d\.]+\]'

class JsonSerialize(JSONEncoder):
    """Default JSON serializer for custom classes. The classes are
    expected to implement a `to_json()' method."""
    def default(self, o):
        return o.to_json()

class JsonSerializeDebug(JSONEncoder):
    """Default JSON serializer for custom classes. The classes are
    expected to implement a `to_json()' method."""
    def default(self, o):
        return o.to_json(full=True)
