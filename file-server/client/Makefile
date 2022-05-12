.PHONY: all clean

CXX = $(HOME)/crafting-bench/hottub3/prefix/bin/g++

all: client.o client-debug.o read.o

client.o: client.cpp
	$(CXX) -std=c++17 -O3 -pthread -o $@ $<

client-debug.o: client.cpp
	$(CXX) -g -std=c++17 -O3 -pthread -o $@ $<

read.o: read.cpp
	$(CXX) -std=c++17 -O3 -pthread -o $@ $<

clean:
	rm -f client.o
	rm -f client-debug.o
	rm -f read.o
