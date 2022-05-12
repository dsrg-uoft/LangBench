#!/usr/bin/env bash

set -xe

export CC="${LANGBENCH}/prefix/bin/gcc"
export CXX="${LANGBENCH}/prefix/bin/g++"

OPTIMIZATION_LEVELS=(o2 o3)
CONTAINER_TYPES=(stl_unordered stl_ordered absl_node absl_flat)
# REGEX_TYPES=(std boost)
REGEX_TYPES=(std)

if [[ ! -d build ]]; then
	mkdir build
fi

for o in ${OPTIMIZATION_LEVELS[*]}; do
	for c in ${CONTAINER_TYPES[*]}; do
		for r in ${REGEX_TYPES[*]}; do
			echo "=== Building $o $c $r"
			touch log_parser.cpp
			pushd build
			rm -f CMakeCache.txt
			cmake "-DLP_${o^^}=ON" "-DLP_${c^^}=ON" "-DLP_REGEX_${r^^}=ON" ..
			make -j 32
			mv log_parser "../log_parser_${c}_regex_${r}-${o}.o"
			popd
		done
	done
done

cp log_parser_stl_unordered_regex_std-o2.o log_parser-o2.o
cp log_parser_stl_unordered_regex_std-o3.o log_parser-o3.o
