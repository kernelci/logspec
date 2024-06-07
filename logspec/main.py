# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

import json
import logging
import yaml
from logspec.fsm_loader import fsm_loader
from logspec.utils.defs import JsonSerialize, JsonSerializeDebug

def format_data_output(data, full=False):
    """Returns a string containing the JSON-serialized version of
    `data'. By default, all fields starting with '_' are not printed,
    unless `full' is set to True.
    """
    def remove_keys(data_dict, prefix):
        for key in list(data_dict):
            if key.startswith(prefix):
                del data_dict[key]
        # Remove recursively on any remaining nested dict (even inside
        # lists)
        for key in list(data_dict):
            if isinstance(data_dict[key], dict):
                remove_keys(data_dict[key], prefix)
            if isinstance(data_dict[key], list):
                for d in data_dict[key]:
                    if isinstance(d, dict):
                        remove_keys(d, prefix)
    if full:
        json_serializer = JsonSerializeDebug
    else:
        json_serializer = JsonSerialize
        remove_keys(data, '_')
    return json.dumps(data, indent=4, sort_keys=True, cls=json_serializer)


def parse_log_file(log_file_path, start_state):
    """Parses a log file using a loaded FSM that starts in
    `start_state'.

    Returns:
      The FSM data (dict) after the parsing is done.
    """
    with open(log_file_path, 'r') as log_file:
        log = log_file.read()
    state = start_state
    data = {}
    while state:
        state_data = state.run(log)
        state = state.transition()
        data.update(state_data)
        if 'match_end' in data:
            log = log[data['match_end']:]
    return data


def load_fsm(fsm_id, fsm_defs_file):
    """Reads a FSM definition file and loads and initializes the FSM
    specified by `fsm_id'.

    Returns:
      The start state of the loaded FSM.
    """
    with open(fsm_defs_file, 'r') as fsm_file:
        fsm_defs = yaml.safe_load(fsm_file)
        assert fsm_defs, f"Error loading FSM definitions: {fsm_defs_file}"
        start_state = fsm_loader(fsm_defs, fsm_id)
        assert start_state, f"Error loading FSM {fsm_id}"
        return start_state


def load_fsm_and_parse_log(log_file_path, fsm_defs_file, fsm_id):
    """Reads a FSM definition file, loads and initializes the FSM
    specified by `fsm_id' and uses it to parse a log file.

    Returns:
      The FSM data (dict) after the parsing is done.
    """
    start_state = load_fsm(fsm_id, fsm_defs_file)
    return parse_log_file(log_file_path, start_state)
