.PHONY: all clean

GO = $(LANGBENCH)/runtimes/go/go-1.14.1-vanilla/go

all: file_server.o file_server_sendfile.o

file_server.o: default/file_server.go
	cd default && $(GO) build -o ../$@

file_server_sendfile.o: sendfile/file_server_sendfile.go
	cd sendfile && $(GO) build -o ../$@

clean:
	rm *.o
