#!/usr/bin/env bash

RUNTIME_PREFIX="$LANGBENCH/runtimes/nodejs/js"
cd "$LANGBENCH/sudoku/js"

echo "=== nodejs rdpmc"
perf stat "$RUNTIME_PREFIX-rdpmc3/node" --no-opt sudoku.js ../input-64.txt
echo

echo "=== nodejs rdtscp"
perf stat "$RUNTIME_PREFIX-rdtscp2/node" --no-opt sudoku.js ../input-64.txt
echo
