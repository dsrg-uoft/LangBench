

#include <thread>
#include <vector>
#include <string>
#include <fstream>
#include <cstdio>
#include <cassert>
#include <memory>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

int file_size(std::string& header) {
	static char const CONTENT_LENGTH[] = "Content-Length: ";
	size_t start = 0;
	while (true) {
		size_t i = start;
		while (i < header.length()) {
			if (header[i] == '\r') {
				assert(i + 1 < header.length());
				if (header[i + 1] == '\n') {
					break;
				}
			}
			i++;
		}
		assert(i < header.length());
		std::string line(header.c_str() + start, i - start);
		start = i + 2;
		if (line.rfind(CONTENT_LENGTH, 0) != std::string::npos) {
			int length = std::atoi(line.c_str() + sizeof(CONTENT_LENGTH) - 1);
			return length - (static_cast<int>(header.length()) - static_cast<int>(start + 2));
		}
	}
}

int receive_file(int server_fd) {
	char header_buf[256];
	ssize_t bytes_recv = recv(server_fd, header_buf, 256, 0);
	if (bytes_recv <= 0) {
		printf("[error] receive_file %ld.\n", bytes_recv);
		return -1;
	}
	std::string header(header_buf, bytes_recv);
	int to_read = file_size(header);
	if (to_read <= 0) {
		return 0;
	}
	std::unique_ptr<char[]> buf = std::make_unique<char[]>(to_read);
	bytes_recv = 0;
	while (bytes_recv < to_read) {
		ssize_t n = recv(server_fd, buf.get() + bytes_recv, to_read - bytes_recv, 0);
		if (n <= 0) {
			printf("[error] receive_file %ld.\n", bytes_recv);
			return -1;
		}
		bytes_recv += n;
	}
	printf("[debug] received %ld bytes\n", (long) bytes_recv);
	return 0;
}

void sendall(int fd, std::string& data) {
	// data ends with "\r\n"
	printf("[debug] requesting %s", data.c_str());
	size_t sent = 0;
	while (sent < data.length()) {
		int n = send(fd, data.c_str() + sent, data.length() - sent, 0);
		assert(n >= 0);
		sent += n;
	}
}

int connect_and_request(size_t id, const char *ip, int port, std::string file) {
	int server_fd = socket(AF_INET, SOCK_STREAM, 0);
	if (server_fd < 0) {
		printf("[error] worker %ld unable to create socket.\n", id);
		return -1;
	}
	struct sockaddr_in server_addr;
	server_addr.sin_family = AF_INET;
	//server_addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
	inet_pton(AF_INET, ip, &server_addr.sin_addr);
	server_addr.sin_port = htons(port);
	if (connect(server_fd, reinterpret_cast<struct sockaddr*>(&server_addr), sizeof(server_addr)) != 0) {
		printf("[error] unable to connect.\n");
		return -1;
	}

	std::string request = "GET /" + file + " HTTP/1.0\r\n";
	sendall(server_fd, request);
	return server_fd;
}

void worker_thread(size_t id, size_t num_workers, const char *ip, int port,
		std::vector<std::string>* files) {

	for (size_t i = id; i < files->size(); i += num_workers) {
		int server_fd = connect_and_request(id, ip, port, (*files)[i]);
		assert(server_fd >= 0);
		//printf("[trace] receiving file: %s\n", (*files)[i].c_str());
		int error = receive_file(server_fd);
		close(server_fd);
		assert(error == 0);
	}
}

int main(int argc, char *argv[]) {
	if (argc <= 4) {
		printf("[info] usage: ./client <ip> <port> <threads> <file name file>\n");
		return 1;
	}

	int port = std::atoi(argv[2]);
	int threads = std::atoi(argv[3]);
	std::vector<std::string> files;
	std::ifstream f(argv[4]);
	{
		std::string line;
		while (std::getline(f, line)) {
			files.push_back(line);
		}
	}

	std::vector<std::unique_ptr<std::thread>> pool(threads);
	for (int i = 0; i < threads; i++) {
		pool[i] = std::make_unique<std::thread>(worker_thread, i, threads, argv[1], port, &files);
	}
	for (size_t i = 0; i < pool.size(); i++) {
		pool[i]->join();
	}
}
