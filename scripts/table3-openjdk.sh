#!/usr/bin/env bash

RUNTIME_PREFIX="$LANGBENCH/runtimes/openjdk/jdk-aload"
cd "$LANGBENCH/sudoku/java"

echo "=== openjdk assembly rdpmc"
perf stat "$RUNTIME_PREFIX-rdpmc-server/bin/java" -Xint Sudoku ../input-64.txt
echo

echo "=== openjdk assembly rdtscp"
perf stat "$RUNTIME_PREFIX-rdtscp-server/bin/java" -Xint Sudoku ../input-64.txt
echo

echo "=== c++ rdpmc"
perf stat "$RUNTIME_PREFIX-rdpmc-zero/bin/java" -Xint Sudoku ../input-64.txt
echo

echo "=== c++ rdtscp"
perf stat "$RUNTIME_PREFIX-rdtscp-zero/bin/java" -Xint Sudoku ../input-64.txt
echo
