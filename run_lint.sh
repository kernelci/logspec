#!/bin/bash
# filepath: /home/gus/p/ecosystem/logspec/run_flake8.sh

echo "Running flake8..."
flake8 .
pylint logspec