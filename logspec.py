#!/usr/bin/env python3
#
# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

import argparse
import json
import logging
import sys
import yaml

import logspec.main
from logspec.utils.defs import JsonSerialize, JsonSerializeDebug
from logspec.main import load_parser_and_parse_log, format_data_output


def debug_parse_log_file(log_file):
    from utils.kbuild_errors import find_build_error
    log = log_file.read()
    error = find_build_error(log)
    if error:
        print(error['text'])
        print(json.dumps(error['info'], indent=4, cls=json_serializer))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='store_true', help="Print version info and exit",
                        default=False)
    parser.add_argument('-d', '--parser-defs',
                        help="Parser definitions yaml file (default: parser_defs.yaml)",
                        default='parser_defs.yaml')
    parser.add_argument('-o', '--output',
                        help="Output type: info (default), debug, json (json output only)",
                        default='info')
    parser.add_argument('--json-full', action='store_true',
                        help=("Enable full JSON serialization, including debug fields "
                              "(disabled by default)"),
                        default=False)
    parser.add_argument('log', help="Log file to analyze", nargs='?')
    parser.add_argument('parser', help="Parser to use for the log analysis", nargs='?')
    args = parser.parse_args()
    logging.basicConfig(format='%(levelname)s:%(message)s')
    if args.output == 'debug':
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.output == 'json':
        logging.disable(logging.INFO)
    elif args.output == 'info':
        logging.getLogger().setLevel(logging.INFO)
    else:
        print(f"Unsupported output type: {args.output}")
        sys.exit(1)

    if args.version:
        print(logspec.main.logspec_version())
        sys.exit(0)
    elif not args.log or not args.parser:
        logging.error("<log> and <parser> arguments are mandatory")
        sys.exit(1)

    data = load_parser_and_parse_log(args.log, args.parser_defs, args.parser)
    if args.json_full:
        print(format_data_output(data, full=True))
    else:
        print(format_data_output(data))
