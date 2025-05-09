# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

from logspec.utils.utils import generate_signature


class Error():
    def __init__(self):
        self.error_type = None
        self.error_summary = ""
        self._report = ""
        # List of field names used to generate the error signature hash
        self._signature_fields = [
            'error_type',
            'error_summary',
        ]
        # Error signature hash
        self._signature = ""

    def fields_to_serialize(self, full=False):
        """Returns a dict with the fields to serialize. By default, this
        excludes all fields starting with '_'. If `full' is set to True,
        all fields are included.
        """
        if full:
            return {k: v for k, v in vars(self).items()}
        return {k: v for k, v in vars(self).items() if not k.startswith('_')}

    def parse(self, text):
        parse_ret = self._parse(text)
        self._generate_signature()
        return parse_ret

    def _generate_signature(self):
        """Uses utils.generate_signature() to generate a unique hash
        string for this error, based on a custom set of error fields.

        This method is meant to be called after the parsing has been
        done.
        """
        signature_dict = {}
        for field in self._signature_fields:
            try:
                val = getattr(self, field)
                if val:
                    signature_dict[field] = val
            except AttributeError:
                continue
        self._signature = generate_signature(signature_dict)
