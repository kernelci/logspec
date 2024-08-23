#!/usr/bin/env python3
#
# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>


# kcidb_logspec.py
#
# Automatically generates KCIDB issues and incidents from logspec error
# specifications
#
# Example usage:
#
#     python kcidb_logspec.py --db="db_connection_string" \
#         --password=<db_password> \
#         --type=boot_test --date-from=2024-08-18

import argparse
import concurrent.futures
from copy import deepcopy
import gzip
import hashlib
import json
import logging
import sys
from threading import Lock
from urllib.parse import urlparse

import psycopg2
import requests

import logspec.main


# Configuration tables per object type
object_types = {
    'kbuild': {
        # Query info: base string, list of columns and parameters
        'query': "SELECT id, log_url FROM builds WHERE valid=%s AND log_url IS NOT NULL",
        'query_columns': {
            'id': 0,
            'log_url': 1,
        },
        'query_parameters' : [
            'false',
        ],
        # DB table to query
        'table': 'builds',
        # logspec parser to use
        'parser': 'kbuild',
        # Object id field to match in the incidents table
        'incident_id_field': 'build_id',
        # Additional incident parameters
        'build_valid': False,
    },
    'boot_test': {
        'query': "SELECT id, log_url FROM tests WHERE path LIKE %s AND status = %s AND log_url IS NOT NULL",
        'query_columns': {
            'id': 0,
            'log_url': 1,
        },
        'query_parameters' : [
            'boot%',
            'FAIL',
        ],
        'table': 'tests',
        'parser': 'generic_linux_boot',
        'test_status': 'FAIL',
        'incident_id_field': 'test_id',
        # Additional incident parameters
        'test_status': 'FAIL',
    },
    'test': {
        'query': "SELECT id, log_url FROM tests WHERE status = %s AND log_url IS NOT NULL",
        'query_columns': {
            'id': 0,
            'log_url': 1,
        },
        'query_parameters' : [
            'FAIL',
        ],
        'table': 'tests',
        'parser': 'generic_linux_boot',
        'test_status': 'FAIL',
        'incident_id_field': 'test_id',
        # Additional incident parameters
        'test_status': 'FAIL',
    },
}


https_sessions = {}
https_sessions_lock = Lock()
log_cache = {}
log_cache_lock = Lock()

def get_log(log_url):
    """Retrieves a raw test log from a url, unzipping it if it's
    gzipped. Returns the log text, or None if the log couldn't be
    downloader or if it's empty.
    """
    global https_sessions
    if not log_url:
        return None
    logging.debug(f"get_log(): {log_url}")
    parsed_url = urlparse(log_url)
    host = f"{parsed_url.scheme}://{parsed_url.netloc}"
    with https_sessions_lock:
        if host not in https_sessions:
            https_sessions[host] = requests.Session()
    try:
        logbytes = https_sessions[host].get(log_url)
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
    """From a logspec output dict, extracts the relevant fields for a
    KCIDB issue definition (only the error definitions without "hidden"
    fields (fields that start with an underscore)) and returns the list
    of errors.
    """
    errors_list = []
    logspec_version = logspec.main.logspec_version()
    base_dict = {
        'version': logspec_version,
        'parser': parser,
    }
    errors = parsed_data.pop('errors')
    for error in errors:
        logspec_dict = {}
        logspec_dict.update(base_dict)
        logspec_dict['error'] = {k: v for k, v in vars(error).items()
                                 if v and not k.startswith('_')}
        logspec_dict['error']['signature'] = error._signature
        logspec_dict['error']['log_excerpt'] = error._report
        errors_list.append(logspec_dict)
    return errors_list


def new_issue(logspec_error, object_type):
    """Generates a new KCIDB issue object from a logspec error for a
    specific object type.

    Returns the issue as a dict.
    """
    error_copy = deepcopy(logspec_error)
    signature = error_copy['error'].pop('signature')
    comment = f"[logspec:{object_types[object_type]['parser']}] {error_copy['error']['error_type']}"
    if 'error_summary' in error_copy['error']:
        comment += f" {error_copy['error']['error_summary']}"
    if 'target' in error_copy['error']:
        comment += f" in {error_copy['error']['target']}"
        if 'src_file' in error_copy['error']:
            comment += f" ({error_copy['error']['src_file']})"
        elif 'script' in error_copy['error']:
            comment += f" ({error_copy['error']['script']})"
    issue = {
        'origin': '_',
        'id': f'_:{signature}',
        'version': 0,
        'comment': comment,
        'misc': {
            'logspec': error_copy
        }
    }
    if 'build_valid' in object_types[object_type]:
        issue['build_valid'] = object_types[object_type]['build_valid']
    if 'test_status' in object_types[object_type]:
        issue['test_status'] = object_types[object_type]['test_status']
    return issue


def new_incident(result_id, issue_id, object_type, issue_version):
    """Generates a new KCIDB incident object for a specific object type
    from an issue id.

    Returns the incident as a dict.
    """
    id_components = json.dumps([result_id, issue_id, issue_version],
                               sort_keys=True, ensure_ascii=False)
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
    """Returns a dict suitable for KCIDB submission containing a list of
    issues and a list of incidents.
    Returns None if no issues or incidents are provided.
    """
    if not issues and not incidents:
        return None
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


def process_single_result(result, object_type, start_state, db_issues):
    issues = []
    incidents = []
    result_id, result_log_url = result[0:2]
    log_cache_lock.acquire()
    if result_log_url in log_cache:
        errors = log_cache[result_log_url]
        log_cache_lock.release()
    else:
        log_cache_lock.release()
        log = get_log(result_log_url)
        if not log:
            return None, None
        parsed_data = logspec.main.parse_log(log, start_state)
        errors = get_logspec_errors(parsed_data, object_types[object_type]['parser'])
        with log_cache_lock:
            if result_log_url not in log_cache:
                log_cache[result_log_url] = errors

    if not errors:
        return None, None
    for error in errors:
        if error['error'].get('signature'):
            issue_id = f"_:{error['error']['signature']}"
            if issue_id not in db_issues:
                # Default initial version
                db_issues[issue_id] = 0
                issues.append(new_issue(error, object_type))
            incidents.append(new_incident(result_id, issue_id, object_type, db_issues[issue_id]))
        else:
            print(f"No logspec signature for: {result_id}: {result_log_url}")
            #print(json.dumps(error, indent=4, ensure_ascii=False))
    return issues, incidents


def process_results(cursor, object_type, date_from=None, date_until=None):
    """Searches for objects of type <object_type> in the database in a
    specified date range, and then for each result it processes the log
    through logspec, tries to match the error against the existing
    issues in the DB, and generates the necessary issues and incidents.

    Returns a dict containing the new issue and incident definitions, if
    any. Returns None if no new issues or incidents must be created.
    """
    # Load logspec parser
    start_state = logspec.main.load_parser(object_types[object_type]['parser'])

    # Fetch results from DB
    query = object_types[object_type]['query']
    query_params = object_types[object_type]['query_parameters']
    if date_from and date_until:
        query += " AND start_time BETWEEN %s AND %s"
        query_params += [date_from, date_until]
    elif date_from:
        query += " AND start_time >= %s"
        query_params.append(date_from)
    elif date_until:
        query += " AND start_time <= %s"
        query_params.append(date_until)
    else:
        logging.error("No date specified")
        return None
    query += " ORDER BY start_time;"
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
        db_issues[issue_id] = issue_version

    # Results processing. For each result:
    #  - Get log
    #  - Pass it through logspec
    #  - Extract the error signatures
    #  - If there isn't a KCIDB issue for a particular error yet:
    #    - Create a new KCIDB issue
    #  - Create a new incident for each error found
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_single_result, result, object_type, start_state, db_issues) for result in results]
        for future in concurrent.futures.as_completed(futures):
            result_issues, result_incidents = future.result()
            if result_issues:
                issues += result_issues
            if result_incidents:
                incidents += result_incidents
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
    if not args.date_from and not args.date_until:
        logging.error("At least one of --date-from and --date-until must "
                      "be specified")
        sys.exit(1)

    loglevel = logging.DEBUG if args.debug else logging.INFO
    logging.getLogger().setLevel(loglevel)
    logging.basicConfig(format='%(levelname)s: %(message)s')

    conn = psycopg2.connect(args.db, password=args.password)
    cursor = conn.cursor()
    data_dict = process_results(cursor, args.type, args.date_from, args.date_until)
    if data_dict:
        print(json.dumps(data_dict, indent=4, ensure_ascii=False))
