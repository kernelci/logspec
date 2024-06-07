# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

"""This module manages the loading and creation of a FSM. The components
of a FSM (state classes and transition functions) are defined in
separate modules in the 'states' and 'transition_functions'
respectively, and these modules are dynamically imported by
`fsm_loader()' when a FSM is created from a definition.

These modules are expected to call the `register_state()' and
`register_transition_function()' functions in this module when
imported. All the registered states and transition functions are kept by
this module.
"""

import importlib
import os
from logspec.fsm_classes import Transition
from logspec.version import __version__


# Dicts to hold the loaded states and transition functions registered by
# external modules
states = {}
transition_functions = {}

STATE_MOD_PREFIX = 'logspec.states'
TRANSFUNC_MOD_PREFIX = 'logspec.transition_functions'


def register_state(module, state, name):
    """Registers a State class.

    Parameters:
      module: name of the module that registers the state
      state: State class to register
      name: name of the state

    Notes:
      Will raise a RuntimeError if the state is already registered
    """
    full_name = f"{module}.{name}"
    if full_name in states:
        raise RuntimeError(f"State <{full_name}> already registered")
    states[full_name] = state


def register_transition_function(module, function, name):
    """Registers a transition function.

    Parameters:
      module: name of the module that registers the function
      function: function to register
      name: name of the function

    Notes:
      Will raise a RuntimeError if the function is already registered
    """
    full_name = f"{module}.{name}"
    if full_name in transition_functions:
        raise RuntimeError(f"Transition function <{full_name}> already registered")
    transition_functions[full_name] = function


def fsm_loader(fsm_defs, name):
    """Reads a FSM definition, loads the required modules and creates
    the FSM.

    Parameters:
      fsm_defs: a dict of FSM definitions, typically loaded from a yaml
          file
      name: the name of the FSM definition to load, which must exist in
          fsm_defs

    Returns:
      The start state of the FSM.

    Notes:
      Will raise ModuleNotFoundError if any of the specified modules
      fail to load and RuntimeError if there's any problem creating the
      FSM.
    """
    if 'version' in fsm_defs:
        _, current_fsm_classes_version, _ = __version__.split('.')
        _, fsm_defs_version, _ = fsm_defs['version'].split('.')
        if int(current_fsm_classes_version) != int(fsm_defs_version):
            raise RuntimeError(f"FSM definitions version {fsm_defs['version']} may "
                               f"not be supported by logspec version {__version__}.")
    if name not in fsm_defs['fsms']:
        raise RuntimeError(f"Definition of FSM {name} not found.")
    fsm = fsm_defs['fsms'][name]
    # Load state modules
    for state_def in fsm['states']:
        module, _ = os.path.splitext(state_def['name'])
        try:
            importlib.import_module(f'{STATE_MOD_PREFIX}.{module}')
        except ModuleNotFoundError:
            msg = (f"Module states.{module} not found. "
                   f"Error loading state {state_def['name']}")
            raise ModuleNotFoundError(msg) from None
    # Load transition function modules and build the fsm
    for state_def in fsm['states']:
        if not state_def['name'] in states:
            raise RuntimeError(f"State {state_def['name']} not found.")
        states[state_def['name']].transitions = []
        if 'transitions' in state_def:
            for transition_def in state_def['transitions']:
                module, _ = os.path.splitext(transition_def['function'])
                try:
                    importlib.import_module(f'{TRANSFUNC_MOD_PREFIX}.{module}')
                except ModuleNotFoundError:
                    msg = (f"Module transition_functions.{module} not found. "
                           f"Error loading transition function {transition_def['function']}")
                    raise ModuleNotFoundError(msg) from None
                try:
                    function = transition_functions[transition_def['function']]
                    state = states[transition_def['state']]
                except KeyError as err:
                    msg = (f"Error loading transition function "
                           f"{transition_def['function']}. {str(err)} not found.")
                    raise RuntimeError(msg) from None
                states[state_def['name']].transitions.append(
                    Transition(function, transition_def['function'], state))
    if fsm['start_state'] not in states:
        raise RuntimeError(f"Start state {fsm['start_state']} not found.")
    return states[fsm['start_state']]
