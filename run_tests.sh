#!/bin/bash

# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2024 Collabora Limited
# Author: Ricardo Cañuelo <ricardo.canuelo@collabora.com>

# For coverage tests, run with `--cov=logspec --cov-report html'

pytest tests "$@"
