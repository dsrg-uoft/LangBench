.PHONY: all clean

CXX = $(LANGBENCH)/prefix/bin/g++

all: sudoku-o2.o sudoku-o3.o sudoku_virtual-o2.o sudoku_virtual-o3.o

sudoku-o2.o: sudoku.cpp
	$(CXX) -std=c++17 -O2 -o $@ $<

sudoku-o3.o: sudoku.cpp
	$(CXX) -std=c++17 -O3 -o $@ $<

sudoku_virtual-o2.o: sudoku_virtual.cpp
	$(CXX) -std=c++17 -O2 -o $@ $<

sudoku_virtual-o3.o: sudoku_virtual.cpp
	$(CXX) -std=c++17 -O3 -o $@ $<

clean:
	rm -f sudoku-o2.o
	rm -f sudoku-o3.o
	rm -f sudoku_virtual-o2.o
	rm -f sudoku_virtual-o3.o
