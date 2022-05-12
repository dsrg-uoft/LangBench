cmake_minimum_required(VERSION 3.5)

#if(NOT CMAKE_BUILD_TYPE)
#	set(CMAKE_BUILD_TYPE Release)
#endif()
#set(CMAKE_CXX_FLAGS_RELEASE "-O2")

project(graph)

option(GRAPH_O2 "Compile with -O2" OFF)
option(GRAPH_O3 "Compile with -O3" OFF)
option(GRAPH_ITERATIVE "Iterative traversal" OFF)
option(GRAPH_RECURSIVE "Recursive traversal" OFF)
option(GRAPH_ABSL_NODE "Use Abseil node map and set" OFF)
option(GRAPH_ABSL_FLAT "Use Abseil flat map and set" OFF)
option(GRAPH_STL_ORDERED "Use stl ordered map and set" OFF)
option(GRAPH_STL_UNORDERED "Use stl unordered map and set" OFF)

if (GRAPH_O2)
	add_compile_options(-O2)
elseif(GRAPH_O3)
	add_compile_options(-O3)
endif()

# Abseil requires C++11
set(CMAKE_CXX_STANDARD 17)

# Process Abseil's CMake build system
add_subdirectory(abseil-cpp)

#add_subdirectory(hopscotch-map)
#add_subdirectory(robin-map)

add_executable(graph graph.cpp)
#target_compile_options(graph PUBLIC "-O2")

if (GRAPH_O2)
	target_compile_definitions(graph PRIVATE GRAPH_O2)
elseif(GRAPH_O3)
	target_compile_definitions(graph PRIVATE GRAPH_O3)
endif()

if (GRAPH_ITERATIVE)
	target_compile_definitions(graph PRIVATE GRAPH_ITERATIVE)
elseif (GRAPH_RECURSIVE)
	target_compile_definitions(graph PRIVATE GRAPH_RECURSIVE)
endif()

if (GRAPH_STL_UNORDERED)
	target_compile_definitions(graph PRIVATE GRAPH_STL_UNORDERED)
elseif (GRAPH_STL_ORDERED)
	target_compile_definitions(graph PRIVATE GRAPH_STL_ORDERED)
elseif (GRAPH_ABSL_NODE)
	target_compile_definitions(graph PRIVATE GRAPH_ABSL_NODE)
	target_link_libraries(graph absl::hash)
	target_link_libraries(graph absl::node_hash_map absl::node_hash_set)
elseif (GRAPH_ABSL_FLAT)
	target_compile_definitions(graph PRIVATE GRAPH_ABSL_FLAT)
	target_link_libraries(graph absl::hash)
	target_link_libraries(graph absl::flat_hash_map absl::flat_hash_set)
endif()

#target_link_libraries(graph tsl::hopscotch_map)
#target_link_libraries(graph tsl::robin_map)
