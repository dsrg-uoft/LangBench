# Running benchmarks (scripts)
These scripts will run the benchmarks as in the paper. However, they are not
strictly required to run the benchmarks as the benchmarks could be used with
different configurations and inputs to observe different properties.

## [launch.py](scripts/launch.py)
This can programmatically run any combinations of benchmarks.
You can see the `main` function at the bottom of the file for examples.

## [tester.py](scripts/tester.py)
This file controls the definition and execution of any benchmark. It can be extended by creating two new classes. The first is a configuration class that inherits `Config` and defines any options for running the application. The second is a class that inherits `Test` to build any commands and execute the benchmark/test itself.
### configuration
You may need to change the paths at the top of the file to match your structure. Specifically, the hostname for a client machine (used in file server, and key value store benchmarks) will likely need to be changed.
Defining `LANGBENCH` and following the structure can help, but all paths can be edited. The scripts expect any binary files to be built, so there is no dependency on the Makefiles.

## building/dependencies
The scripts use two small C programs.
To build `obs.o` run `make` inside scripts.
To build `clear_mem.o` you should first edit the path in `clear_mem.c` and then run `make`. `clear_mem.o` is just a hack to allow the scripts to easily clear the caches.

## figure scripts
There are also scripts to generate the figures from the paper.
Please use `pip install -r scripts/requirements.txt` to get all dependencies.

## profiling/debugging
There are many scripts for profiling and debugging, including many scripts for gdb.
They are left intact, but will need some understanding/editing to be used.

# Building benchmarks
Generally, only the cpp, java, and go versions require any building.
Simply doing `pushd <benchmark>/<language> && make && popd` will work.
i.e. `pushd sort/cpp && make && popd`

Unfortunately, the Makefiles are rather inflexible currently likely requiring you to edit them.
They expect a fairly rigid file structure and the environment variable `LANGBENCH` to be defined.
`LANGBENCH` should be the location of this repository, and inside it you can store the various runtimes under `./runtimes`.

Exceptions are listed below.

## key value store
Requires Redis (https://redis.io/) as it uses the benchmark provided. Set `REDIS_HOME` or edit [tester.py](scripts/tester.py).

## graph (iterative and recursive)
### cpp
Depends on abseil-cpp (https://abseil.io/ https://github.com/abseil/abseil-cpp).
Follow their README.md for more details.
### js
The recursive version requires a simple binding to be build. A pre-built version exists in this repository.

## log parser
### cpp
Requires CMake to build.
Depends on abseil-cpp (https://abseil.io/ https://github.com/abseil/abseil-cpp).
Follow their README.md for more details.

Not mentioned in the paper, but the use of the boost regex library creates a speedup. The make scripts support this if boost is provided.

## file server
Must also build the client located in [file-server/client](file-server/client) by running make.

# Runtime repositories
* https://github.com/dsrg-uoft/LangBench-openjdk
* https://github.com/dsrg-uoft/LangBench-nodejs
* https://github.com/dsrg-uoft/LangBench-cpython
