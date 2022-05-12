#!/usr/bin/env bash

set -e

CLEAR_MEM="$LANGBENCH/scripts/clear_mem/clear_mem.o"
OBS="$LANGBENCH/scripts/obs.o"
RUNTIME="$LANGBENCH/runtimes/nodejs"
cd "$LANGBENCH/sudoku/js"

FLAVOURS=(default no_objint no_shape no_bounds no_hole no_all)

for f in "${FLAVOURS[@]}"; do
	echo "=== $f"
	$OBS "$RUNTIME/js-$f/node" -krgc_filter=solve,partial_verify sudoku.js ../input-64.txt
	echo
done
