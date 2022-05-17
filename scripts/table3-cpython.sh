#!/usr/bin/env bash

RUNTIME_PREFIX="$LANGBENCH/runtimes/cpython/build-opt-binarysubscr"
cd "$LANGBENCH/sudoku/python"

echo "=== cpython rdpmc"
perf stat "$RUNTIME_PREFIX-rdpmc/python" sudoku.py ../input-64.txt
echo

echo "=== cpython rdtscp"
perf stat "$RUNTIME_PREFIX-rdtscp/python" sudoku.py ../input-64.txt
echo
