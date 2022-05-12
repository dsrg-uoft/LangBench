.PHONY: all clean

CXX = $(LANGBENCH)/prefix/bin/gcc

all: obs.o

obs.o: obs.c
	$(CXX) -O3 -o $@ $<

clean:
	rm obs.o
