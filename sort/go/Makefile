.PHONY: all clean

GO = $(LANGBENCH)/runtimes/go/go-1.14.1-vanilla/go

all: sort.o

sort.o: sort.go
	$(GO) build -o sort.o

clean:
	rm sort.o
