.PHONY: all clean

GO = $(LANGBENCH)/runtimes/go/go-1.14.1-vanilla/go

all: log_parser.o

log_parser.o: log_parser.go
	$(GO) build -o log_parser.o

clean:
	rm log_parser.o
