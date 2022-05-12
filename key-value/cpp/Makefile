.PHONY: all clean

CXX ?= $(LANGBENCH)/prefix/bin/g++

all: key_value-o2.o key_value-o3.o key_value-debug.o key_value-o0.o micro_hashmap.o

key_value-o2.o: key_value.cpp hashmap.cpp
	$(CXX) -std=c++17 -O2 -pthread -o $@ $^

key_value-o3.o: key_value.cpp hashmap.cpp
	$(CXX) -std=c++17 -O3 -pthread -o $@ $^

key_value-debug.o: key_value.cpp hashmap.cpp
	$(CXX) -g -std=c++17 -O2 -pthread -o $@ $^

key_value-o0.o: key_value.cpp hashmap.cpp
	$(CXX) -g -std=c++17 -O0 -pthread -o $@ $^

key_value-dummyptr.o: key_value.cpp hashmap2.cpp
	$(CXX) -g -std=c++17 -O2 -pthread -o $@ $^

micro_hashmap.o: micro_hashmap.cpp
	$(CXX) -std=c++17 -O2 -pthread -o $@ $^

clean:
	rm key_value-o2.o
	rm key_value-o3.o
	rm key_value-debug.o
	rm key_value-o0.o
	rm micro_hashmap.o
