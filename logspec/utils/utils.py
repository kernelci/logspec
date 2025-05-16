# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

import hashlib
import json


def update_dict(dest_dict, new_data):
    """Updates dest_dict in place with the contents of dict
    new_data. This is equivalent to dest_dict.update(new_data) except
    that the nested lists in dest_dict are extended/appended if found in
    new_data rather than replaced.
    """
    for k, v in new_data.items():
        if k in dest_dict and isinstance(dest_dict[k], list):
            if isinstance(v, list):
                dest_dict[k].extend(v)
            else:
                dest_dict[k].append(v)
        else:
            dest_dict[k] = v


def generate_signature(data_dict):
    """Generates a hash string of the data_dict contents"""
    signature_json = json.dumps(data_dict, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(signature_json.encode('utf-8')).hexdigest()
