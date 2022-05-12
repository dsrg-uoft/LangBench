.PHONY: all clean

GO = $(LANGBENCH)/runtimes/go/go-1.14.1-vanilla/go

all: graph_iterative.o graph_recursive.o

graph_iterative.o: iterative/graph_iterative.go
	cd iterative && $(GO) build -o ../$@

graph_recursive.o: recursive/graph_recursive.go
	cd recursive && $(GO) build -o ../$@

clean:
	rm *.o
