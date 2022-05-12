

#include <thread>
#include <vector>
#include <string>
#include <utility>
#include <fstream>
#include <iterator>
#include <optional>
#include <memory>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <cassert>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <sys/stat.h>

static std::string read_one_line(int fd) {
	char buf[256];
	int n = read(fd, buf, 256);
	int pos = 0;
	while (pos < n) {
		if (buf[pos] == '\r') {
			assert(pos + 1 < n);
			if (buf[pos + 1] == '\n') {
				break;
			}
		}
		pos++;
	}
	assert(pos > 0);
	assert(pos < n);
	return std::string(buf, pos);
}

static std::vector<std::string> string_split(std::string& str, std::string delim) {
	std::vector<std::string> ret;
	size_t pos = 0;
	while (pos <= str.length()) {
		size_t end = str.find(delim, pos);
		if (end == std::string::npos) {
			ret.emplace_back(str.c_str() + pos);
			break;
		}
		ret.emplace_back(str.c_str() + pos, end - pos);
		pos = end + delim.size();
	}
	return ret;
}

static std::optional<std::pair<std::unique_ptr<char[]>, size_t>> read_file(std::string& path, std::string& directory) {
	std::vector<std::string> parts = string_split(path, "/");
	std::string filtered = "";
	for (size_t i = 1; i < parts.size(); i++) {
		std::string& p = parts[i];
		if (p == "..") {
			continue;
		}
		filtered += "/" + p;
	}
	filtered = directory + filtered;

	int fd = open(filtered.c_str(), O_RDONLY);
	if (fd < 0) {
		printf("[error] open error: %s\n", strerror(errno));
	}

	assert(fd >= 0);
	struct stat info;
	int error = fstat(fd, &info);
	assert(error == 0);
	int n = info.st_size;

	std::unique_ptr<char[]> buf = std::make_unique<char[]>(n);
	int read_bytes = read(fd, buf.get(), n);
	assert(read_bytes == n);

	close(fd);
	return std::make_pair(std::move(buf), n);
}

static std::string build_header(int code, size_t n) {
	std::string status = "";
	switch (code) {
	case 200:
		status = "OK";
		break;
	case 404:
		status = "Not Found";
		break;
	default:
		assert(false);
	}
	std::string res = "HTTP/1.0 " + std::to_string(code) + " " + status + "\r\n";
	res += "Content-Type: text/plain; charset=UTF-8\r\n";
	res += "Content-Length: " + std::to_string(n) + "\r\n";
	res += "\r\n";
	return res;
}

void sendall(int fd, std::string& data) {
	size_t sent = 0;
	while (sent < data.length()) {
		int n = send(fd, data.c_str() + sent, data.length() - sent, 0);
		assert(n >= 0);
		sent += n;
	}
}

void sendall(int fd, char* buf, size_t len) {
	size_t sent = 0;
	while (sent < len) {
		int n = send(fd, buf + sent, len - sent, 0);
		assert(n >= 0);
		sent += n;
	}
}

void readall(int fd) {
	char buf[256];
	while (true) {
		int n = read(fd, buf, 256);
		if (n < 0) {
			printf("[error] reading from socket: %s.\n", std::strerror(errno));
			break;
		} else if (n == 0) {
			break;
		}
	}
}

static void handle_connection(int fd, std::string directory) {
	std::string line = read_one_line(fd);
	std::vector<std::string> parts = string_split(line, " ");
	/*
	for (std::string const& str : parts) {
		printf("[trace] got part %s\n", str.c_str());
	}
	*/
	assert(parts.size() > 1);
	std::string path = parts[1];
	std::optional<std::pair<std::unique_ptr<char[]>, size_t>> maybe_data = read_file(path, directory);
	std::unique_ptr<char[]> data;
	size_t len;
	std::string header = "";
	if (maybe_data.has_value()) {
		data = std::move(maybe_data.value().first);
		len = maybe_data.value().second;
		header = build_header(200, len);
	} else {
		char not_found[] = "Not found.";
		len = sizeof(not_found);
		data = std::make_unique<char[]>(len);
		memcpy(data.get(), not_found, len);
		header = build_header(404, len);
	}
	sendall(fd, header);
	sendall(fd, data.get(), len);
	readall(fd);
	//printf("[trace] closing connection.\n");
	close(fd);
}

int main(int argc, char *argv[]) {
	if (argc <= 3) {
		printf("[info] usage: ./file_server <ip> <port> <directory>\n");
		return 1;
	}
	int port = std::atoi(argv[2]);
	int server_fd = socket(AF_INET, SOCK_STREAM, 0);
	if (server_fd < 0) {
		printf("[error] unable to create socket.\n");
		return 1;
	}
	struct sockaddr_in server_addr;
	server_addr.sin_family = AF_INET;
	//server_addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
	inet_pton(AF_INET, argv[1], &server_addr.sin_addr);
	server_addr.sin_port = htons(port);

	if ((bind(server_fd, reinterpret_cast<struct sockaddr*>(&server_addr), sizeof(server_addr))) != 0) {
		printf("[error] unable to bind to %s:%d.\n", argv[1], port);
		return 1;
	}

	if (listen(server_fd, 1025) != 0) {
		printf("[error] unable to listen.\n");
		return 1;
	}

	while (true) {
		struct sockaddr_in client;
		int len = sizeof(client);
		int client_fd = accept(server_fd, reinterpret_cast<struct sockaddr*>(&client), reinterpret_cast<socklen_t*>(&len));
		if (client_fd < 0) {
			printf("[error] server accept failed.\n");
			return 1;
		}
		//printf("[info] new connection.\n");
		std::thread t(handle_connection, client_fd, argv[3]);
		t.detach();
	}
	return 0;
}
