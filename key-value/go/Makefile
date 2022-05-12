.PHONY: all clean

GO ?= $(LANGBENCH)/runtimes/go/go-1.14.1-vanilla/go

all: key_value.o

key_value.o: key_value.go hashmap.go
	$(GO) build -o $@

clean:
	rm key_value.o
