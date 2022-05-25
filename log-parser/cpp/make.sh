#!/usr/bin/env bash

set -xe

PREFIX="${LANGBENCH}/prefix"
CMAKE="${PREFIX}/bin/cmake"
export CC="${PREFIX}/bin/gcc"
export CXX="${PREFIX}/bin/g++"

CPP="${LANGBENCH}/prefix"
CBR="${LANGBENCH}/prefix/lib"

OPTIMIZATION_LEVELS=(o2 o3)
CONTAINER_TYPES=(stl_unordered stl_ordered absl_node absl_flat)
REGEX_TYPES=(std boost)

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
			$CMAKE -DCMAKE_PREFIX_PATH=$CPP -DCMAKE_BUILD_RPATH=$CBR "-DLP_${o^^}=ON" "-DLP_${c^^}=ON" "-DLP_REGEX_${r^^}=ON" ..
			make -j 32
			mv log_parser "../log_parser_${c}_regex_${r}-${o}.o"
			popd
		done
	done
done
