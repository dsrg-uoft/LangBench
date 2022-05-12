

#include "hashmap.h"
#include <memory>
#include <string>
#include <string_view>
#include <optional>
#include <thread>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <cassert>
#include <unistd.h>
#include <sys/socket.h>
//#include <sys/types.h>
#include <netinet/in.h>
#include <arpa/inet.h>

class InputStream {
public:
	InputStream(int fd) : fd(fd), buf_pos(0), eof(false) {
		this->buf_len = INITIAL_BUF_LEN;
		this->buf = std::make_unique<char[]>(this->buf_len);
	}

	std::optional<std::string> read_line() {
		if (this->eof) {
			return std::nullopt;
		}
		std::optional<std::string> ret = this->find_line(0, this->buf_pos);
		if (ret.has_value()) {
			return ret;
		}
		while (true) {
			int len = this->buf_len - this->buf_pos;
			if (len == 0) {
				size_t n = this->buf_len * 2;
				std::unique_ptr<char[]> buf2 = std::make_unique<char[]>(n);
				std::memcpy(buf2.get(), this->buf.get(), this->buf_len);
				this->buf = std::move(buf2);
				this->buf_len = n;
			}
			int x = read(this->fd, this->buf.get() + this->buf_pos, this->buf_len - this->buf_pos);
			if (x <= 0) {
				if (x < 0) {
					fprintf(stderr, "[error] reading from socket returned %s\n", std::strerror(errno));
				}
				if (this->buf_pos == 0) {
					return std::nullopt;
				}
				this->eof = true;
				return std::string(this->buf.get(), this->buf_pos);
			}
			std::optional<std::string> ret = this->find_line(this->buf_pos, x);
			//std::optional<std::string> ret = this->find_line(0, x);
			if (ret.has_value()) {
				return ret;
			}
			this->buf_pos += x;
		}
	}

private:
	static size_t const INITIAL_BUF_LEN = 64;
	int fd;
	std::unique_ptr<char[]> buf;
	size_t buf_pos;
	size_t buf_len;
	bool eof;

	std::optional<std::string> find_line(size_t start, size_t len) {
		//fprintf(stderr, "[trace] find_line for %zd, %zd: %s.\n", start, len, std::string(this->buf.get(), start + len).c_str());
		size_t offset = (start > 0) ? 1 : 0;
		start -= offset;
		len += offset;
		std::string_view view(this->buf.get() + start, len);
		size_t nl = view.find("\r\n");
		if (nl == std::string::npos) {
			//fprintf(stderr, "[trace] find_line found nothing.\n");
			return std::nullopt;
		}
		size_t n = start + nl;
		std::string ret(this->buf.get(), n);
		this->buf_pos = len - nl - 2;
		std::memcpy(this->buf.get(), this->buf.get() + n + 2, this->buf_pos);
		//fprintf(stderr, "[trace] rest of the buffer is %s.\n", std::string(this->buf.get(), this->buf_pos).c_str());
		//fprintf(stderr, "[trace] find_line got: %s.\n", ret.c_str());
		return std::optional<std::string>(ret);
	}
};

void handle_connection(HashMap* map, int fd) {
	InputStream in(fd);
	while (true) {
		std::optional<std::string> cmd_len_buf = in.read_line();
		if (!cmd_len_buf.has_value()) {
			break;
		}
		assert((*cmd_len_buf)[0] == '*');
		int cmd_len = std::atoi(cmd_len_buf->c_str() + 1);
		//fprintf(stderr, "[trace] cmd_len is %d.\n", cmd_len);
		std::string parts[cmd_len];
		int i = 0;
		while (i < cmd_len) {
			std::optional<std::string> buf = in.read_line();
			if (!buf.has_value()) {
				fprintf(stderr, "[error] unable to read full array.\n");
				break;
			}
			assert((*buf)[0] == '$');
			std::optional<std::string> str = in.read_line();
			if (!str.has_value()) {
				fprintf(stderr, "[error] unable to read full array.\n");
				break;
			}
			parts[i] = str.value();
			//fprintf(stderr, "[trace] part %d got %s.\n", i, parts[i].c_str());
			i++;
		}

		std::string ret = "";
		if (parts[0] == "GET") {
			std::optional<std::string> val = map->get(parts[1]);
			if (!val.has_value()) {
				ret = "$-1\r\n";
			} else {
				std::string const& str = val.value();
				ret = "$" + std::to_string(str.length()) + "\r\n" + str + "\r\n";
			}
		} else if (parts[0] == "SET") {
			//fprintf(stderr, "[trace] setting %s to %s.\n", parts[1].c_str(), parts[2].c_str());
			map->set(parts[1], parts[2]);
			//fprintf(stderr, "[trace] done set.\n");
			ret = "+OK\r\n";
		} else {
			fprintf(stderr, "[info] unknown command %s.\n", parts[0].c_str());
			break;
		}
		if (write(fd, ret.c_str(), ret.length()) < 0) {
			fprintf(stderr, "[error] unable to write to client.\n");
			break;
		}
	}
	fprintf(stderr, "[info] closing connection.\n");
	close(fd);
}

int main(int argc, char *argv[]) {
	/*
	(void) argc;
	(void) argv;
	HashMap map(static_cast<unsigned long>(24 * 1024 * 1024));
	for (int i = 0; i < 2 * 1000 * 1000; i++) {
		std::string k = std::to_string(i);
		std::string v = "xxx";
		map.set(k, v);
	}
	return 0;
	*/
	if (argc <= 4) {
		fprintf(stderr, "[info] usage: ./server <ip> <port> <size> <rows>\n");
		return 1;
	}
	int port = std::atoi(argv[2]);
	int size = std::atoi(argv[3]);
	int rows = std::atoi(argv[4]);
	int server_fd = socket(AF_INET, SOCK_STREAM, 0);
	if (server_fd < 0) {
		fprintf(stderr, "[error] unable to create socket.\n");
		return 1;
	}
	struct sockaddr_in server_addr;
	server_addr.sin_family = AF_INET;
	server_addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
	//server_addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
	inet_pton(AF_INET, argv[1], &server_addr.sin_addr);
	server_addr.sin_port = htons(port);

	if ((bind(server_fd, reinterpret_cast<struct sockaddr*>(&server_addr), sizeof(server_addr))) != 0) {
		fprintf(stderr, "[error] unable to bind to %s:%d.\n", argv[1], port);
		return 1;
	}

	if (listen(server_fd, 1025) != 0) {
		fprintf(stderr, "[error] unable to listen.\n");
		return 1;
	}

	HashMap map(static_cast<unsigned long>(size) * 1024, rows);
	while (true) {
		struct sockaddr_in client;
		int len = sizeof(client);
		int client_fd = accept(server_fd, reinterpret_cast<struct sockaddr*>(&client), reinterpret_cast<socklen_t*>(&len));
		if (client_fd < 0) {
			fprintf(stderr, "[error] server accept failed.\n");
			return 1;
		}
		fprintf(stderr, "[info] new connection.\n");
		std::thread t(handle_connection, &map, client_fd);
		t.detach();
	}
	return 0;
}
