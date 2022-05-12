.PHONY: all clean

CXX = $(LANGBENCH)/prefix/bin/gcc

all: clear_mem.o

clear_mem.o: clear_mem.c
	$(CXX) -O3 -o $@ $<

clean:
	rm clear_mem.o
