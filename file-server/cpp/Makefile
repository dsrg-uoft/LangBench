.PHONY: all clean

CXX = $(LANGBENCH)/prefix/bin/g++

all: file_server-o2.o file_server-o3.o file_server.o file_server_ptr-o3.o file_server_empty-o3.o file_server_sendfile-o3.o

file_server-o2.o: file_server.cpp
	$(CXX) -std=c++17 -O2 -pthread -o $@ $<

file_server-o3.o: file_server.cpp
	$(CXX) -std=c++17 -O3 -pthread -o $@ $<

file_server.o: file_server.cpp
	$(CXX) -g -std=c++17 -O2 -pthread -o $@ $<

file_server_ptr-o3.o: file_server_ptr.cpp
	$(CXX) -std=c++17 -O3 -pthread -o $@ $<

file_server_empty-o3.o: file_server_empty.cpp
	$(CXX) -std=c++17 -O3 -pthread -o $@ $<

file_server_sendfile-o3.o: file_server_sendfile.cpp
	$(CXX) -std=c++17 -O3 -pthread -o $@ $<

clean:
	rm -f *.o
