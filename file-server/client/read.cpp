

#include <thread>
#include <vector>
#include <string>
#include <fstream>
#include <cstdio>
#include <cassert>
#include <memory>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <ctime>
#include <cstring>

long time_diff(struct timespec start, struct timespec end) {
	time_t sec = end.tv_sec - start.tv_sec;
	long nano = end.tv_nsec - start.tv_nsec;
	return (long) sec * 1000 * 1000 * 1000 + nano;
}

void worker_thread(size_t id, size_t num_workers, std::vector<std::string>* files) {
	for (size_t i = id; i < files->size(); i += num_workers) {
		int fd = open(files->at(i).c_str(), O_RDONLY);
		if (fd < 0) {
			printf("[error] open error: %s\n", strerror(errno));
		}
		assert(fd >= 0);
		//close(fd);
		struct stat info;
		int error = fstat(fd, &info);
		assert(error == 0);
		int size = info.st_size;
		std::unique_ptr<char[]> buf = std::make_unique<char[]>(size);
		int read_bytes = 0;
		while (read_bytes < size) {
			int n = read(fd, buf.get() + read_bytes, size - read_bytes);
			assert(n > 0);
			read_bytes += n;
		}
		{
			char buf2[256];
			int n = read(fd, buf2, sizeof(buf2));
			assert(n == 0);
		}
		error = close(fd);
		assert(error == 0);
	}
}

int main(int argc, char *argv[]) {
	if (argc <= 2) {
		printf("[info] usage: ./read <threads> <file name file>\n");
		return 1;
	}

	int threads = std::atoi(argv[1]);

	struct timespec t0;
	clock_gettime(CLOCK_MONOTONIC, &t0);
	std::vector<std::string> files;
	std::ifstream f(argv[2]);
	{
		std::string line;
		while (std::getline(f, line)) {
			files.push_back(line);
		}
	}
	struct timespec t1;
	clock_gettime(CLOCK_MONOTONIC, &t1);
	printf("[info] reading list of files took %ld ns.\n", time_diff(t0, t1));

	std::vector<std::unique_ptr<std::thread>> pool(threads);
	for (int i = 0; i < threads; i++) {
		pool[i] = std::make_unique<std::thread>(worker_thread, i, threads, &files);
	}
	for (size_t i = 0; i < pool.size(); i++) {
		pool[i]->join();
	}

	struct timespec t2;
	clock_gettime(CLOCK_MONOTONIC, &t2);
	printf("[info] reading all files took %ld ns.\n", time_diff(t1, t2));
}
