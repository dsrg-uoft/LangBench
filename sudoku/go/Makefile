.PHONY: all clean

GO = $(LANGBENCH)/runtimes/go/go-1.14.1-vanilla/go

all: sudoku.o

sudoku.o: sudoku.go
	$(GO) build -o sudoku.o

clean:
	rm sudoku.o
