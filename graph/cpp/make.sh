#!/usr/bin/env bash

set -xe

export CC="${LANGBENCH}/prefix/bin/gcc"
export CXX="${LANGBENCH}/prefix/bin/g++"

OPTIMIZATION_LEVELS=(o2 o3)
TRAVERSAL_TYPES=(iterative recursive)
CONTAINER_TYPES=(stl_unordered stl_ordered absl_node absl_flat)

if [[ ! -d build ]]; then
	mkdir build
fi

for o in ${OPTIMIZATION_LEVELS[*]}; do
	for t in ${TRAVERSAL_TYPES[*]}; do
		for c in ${CONTAINER_TYPES[*]}; do
			echo "=== Building $o $t $c"
			touch graph.cpp
			pushd build
			rm -f CMakeCache.txt
			cmake "-DGRAPH_${o^^}=ON" "-DGRAPH_${t^^}=ON" "-DGRAPH_${c^^}=ON" ..
			make -j 32
			mv graph "../graph_${t}_${c}-${o}.o"
			popd
		done
	done
done

cp graph_iterative_stl_unordered-o2.o graph_iterative-o2.o
cp graph_iterative_stl_unordered-o3.o graph_iterative-o3.o
cp graph_recursive_stl_unordered-o2.o graph_recursive-o2.o
cp graph_recursive_stl_unordered-o3.o graph_recursive-o3.o
