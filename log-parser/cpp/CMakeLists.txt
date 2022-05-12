cmake_minimum_required(VERSION 3.5)

project(log_parser)

option(LP_O2 "Compile with -O2" OFF)
option(LP_O3 "Compile with -O3" OFF)
option(LP_ABSL_NODE "Use Abseil node map and set" OFF)
option(LP_ABSL_FLAT "Use Abseil flat map and set" OFF)
option(LP_STL_ORDERED "Use stl ordered map and set" OFF)
option(LP_STL_UNORDERED "Use stl unordered map and set" OFF)
option(LP_REGEX_STD "Use std::regex" OFF)
option(LP_REGEX_BOOST "Use boost::regex" OFF)

set(CMAKE_THREAD_PREFER_PTHREAD ON)
set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)

if (LP_REGEX_BOOST)
	find_package(Boost REQUIRED COMPONENTS regex)
endif()

if (LP_O2)
	add_compile_options(-O2)
elseif(LP_O3)
	add_compile_options(-O3)
endif()

# Abseil requires C++11
set(CMAKE_CXX_STANDARD 17)

# Process Abseil's CMake build system
add_subdirectory(abseil-cpp)

add_executable(log_parser log_parser.cpp)
target_link_libraries(log_parser Threads::Threads)

if (LP_O2)
	target_compile_definitions(log_parser PRIVATE LP_O2)
elseif(LP_O3)
	target_compile_definitions(log_parser PRIVATE LP_O3)
endif()

if (LP_STL_UNORDERED)
	target_compile_definitions(log_parser PRIVATE LP_STL_UNORDERED)
elseif (LP_STL_ORDERED)
	target_compile_definitions(log_parser PRIVATE LP_STL_ORDERED)
elseif (LP_ABSL_NODE)
	target_compile_definitions(log_parser PRIVATE LP_ABSL_NODE)
	target_link_libraries(log_parser absl::hash)
	target_link_libraries(log_parser absl::node_hash_map absl::node_hash_set)
elseif (LP_ABSL_FLAT)
	target_compile_definitions(log_parser PRIVATE LP_ABSL_FLAT)
	target_link_libraries(log_parser absl::hash)
	target_link_libraries(log_parser absl::flat_hash_map absl::flat_hash_set)
endif()


if (LP_REGEX_BOOST)
	target_compile_definitions(log_parser PRIVATE LP_REGEX_BOOST)
	target_include_directories(log_parser PRIVATE ${Boost_INCLUDE_DIRS})
	target_link_libraries(log_parser Boost::regex)
elseif (LP_REGEX_STD)
	target_compile_definitions(log_parser PRIVATE LP_REGEX_STD)
endif()
