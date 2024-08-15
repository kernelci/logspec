#!/usr/bin/env python3
#
# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

import argparse
import gzip
import hashlib
import json
import logging

import psycopg2
import requests

import logspec.main


object_types = {
    'kbuild': {
        'query': "SELECT id, log_url FROM builds WHERE valid=false AND log_url IS NOT NULL",
        'query_columns': {
            'id': 0,
            'log_url': 1,
        },
        'table': 'builds',
        'parser': 'kbuild',
        'build_valid': False,
        'incident_id_field': 'build_id',
    },
    'boot_test': {},
}


def get_log(log_url):
    if not log_url:
        return None
    logging.debug(f"get_log(): {log_url}")
    try:
        logbytes = requests.get(log_url)
        logbytes.raise_for_status()
    except Exception as e:
        return None
    if not len(logbytes.content):
        return None
    try:
        raw_bytes = gzip.decompress(logbytes.content)
        log = raw_bytes.decode('utf-8')
    except gzip.BadGzipFile:
        log = logbytes.content.decode('utf-8')
    return log


def get_logspec_errors(parsed_data, parser):
    errors_list = []
    logspec_version = logspec.main.logspec_version()
    base_dict = {
        'version': logspec_version,
        'parser': parser,
    }
    errors = parsed_data.pop('errors')
    for e in errors:
        logspec_dict = {}
        logspec_dict.update(base_dict)
        e_dict = {k: v for k, v in vars(e).items() if v and not k.startswith('_')}
        e_dict['signature'] = e._signature
        e_dict['log_excerpt'] = e._report
        logspec_dict['error'] = e_dict
        errors_list.append(logspec_dict)
    return errors_list


def new_issue(logspec_error, object_type):
    signature = logspec_error['error'].pop('signature')
    comment = f"[logspec:kbuild] {logspec_error['error']['error_type']}"
    if 'error_summary' in logspec_error['error']:
        comment += f" {logspec_error['error']['error_summary']}"
    if 'target' in logspec_error['error']:
        comment += f" in {logspec_error['error']['target']}"
        if 'src_file' in logspec_error['error']:
            comment += f" ({logspec_error['error']['src_file']})"
        elif 'script' in logspec_error['error']:
            comment += f" ({logspec_error['error']['script']})"
    issue = {
        'origin': '_',
        'id': f'_:{signature}',
        'version': 0,
        'build_valid': object_types[object_type]['build_valid'],
        'comment': comment,
        'misc': {
            'logspec': logspec_error
        }
    }
    return issue


def new_incident(result_id, issue_id, object_type, issue_version):
    id_components = json.dumps([result_id, issue_id, issue_version], sort_keys=True, ensure_ascii=False)
    incident_id = hashlib.sha1(id_components.encode('utf-8')).hexdigest()
    incident = {
        'id': f"_:{incident_id}",
        'issue_id': issue_id,
        'issue_version': issue_version,
        object_types[object_type]['incident_id_field']: result_id,
        'comment': "test incident, automatically generated",
        'origin': '_',
    }
    return incident


def generate_output_dict(issues=None, incidents=None):
    if not issues or not incidents:
        return
    output_dict = {
        'version': {
            'major': 4,
            'minor': 3,
        },
    }
    if issues:
        output_dict['issues'] = issues
    if incidents:
        output_dict['incidents'] = incidents
    return output_dict


def process_results(cursor, object_type, date_from=None, date_until=None):
    start_state = logspec.main.load_parser(object_types[object_type]['parser'])

    # Fetch results from DB
    query = object_types[object_type]['query']
    query_params = []
    if date_from and date_until:
        query += " AND start_time BETWEEN %s AND %s"
        query_params += [date_from, date_until]
    elif date_from:
        query += " AND start_time >= %s"
        query_params.append(date_from)
    elif date_until:
        query += " AND start_time <= %s"
        query_params.append(date_until)
    query += ';'
    logging.debug(f"Get results query: {query}. parameters: {query_params}")
    cursor.execute(query, query_params)
    results = cursor.fetchall()

    # Fetch issues from DB
    query = "SELECT id, version FROM issues;"
    cursor.execute(query)
    issue_results = cursor.fetchall()
    # key = issue id, value = issue version
    db_issues = {}
    issues = []
    incidents = []
    for issue in issue_results:
        issue_id, issue_version = issue[0:2]
        db_issues[issue_id] = issue[issue_version]

    # Results processing. For each result:
    #  - Get log
    #  - Pass it through logspec
    #  - Extract the error signatures
    #  - If there isn't a KCIDB issue for a particular error yet:
    #    - Create a new KCIDB issue
    #  - Create a new incident for each error found
    for result in results:
        result_id, result_log_url = result[0:2]
        print(f"result: {result_id}")
        log = get_log(result_log_url)
        if not log:
            continue
        parsed_data = logspec.main.parse_log(log, start_state)
        errors = get_logspec_errors(parsed_data, object_types[object_type]['parser'])
        for error in errors:
            if error['error'].get('signature'):
                issue_id = f"_:{error['error']['signature']}"
                if issue_id not in db_issues:
                    # Default initial version
                    db_issues[issue_id] = 0
                    issues.append(new_issue(error, object_type))
                incidents.append(new_incident(result_id, issue_id, object_type, db_issues[issue_id]))
    # Generate json output for all new issues and incidents
    if issues or incidents:
        return generate_output_dict(issues, incidents)
    return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', help="Database connection string")
    parser.add_argument('--password', help="Database connection password")
    parser.add_argument('--type',
                        choices=list(object_types),
                        help="Type of objects to analyze")
    parser.add_argument('--date-from')
    parser.add_argument('--date-until')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Enable debug traces')
    args = parser.parse_args()

    loglevel = logging.DEBUG if args.debug else logging.INFO
    logging.getLogger().setLevel(loglevel)
    logging.basicConfig(format='%(levelname)s: %(message)s')

    conn = psycopg2.connect(args.db, password=args.password)
    cursor = conn.cursor()
    data_dict = process_results(cursor, args.type, args.date_from, args.date_until)
    if data_dict:
        print(json.dumps(data_dict, indent=4, ensure_ascii=False))
