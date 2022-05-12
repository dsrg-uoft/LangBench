#include <stdio.h>
#include <time.h>
#include <string.h>
#include <stdbool.h>
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <assert.h>
#include <sys/wait.h>
#include <sys/resource.h>

int main(int argc, char *argv[]) {
	if (argc <= 1) {
		fprintf(stderr, "[usage] ./obs [-m] <program> [args...]\n");
		return 1;
	}

	bool monitor = false;
	int arg_offset = 1;
	if (strncmp(argv[1], "-m", 2) == 0) {
		monitor = true;
		arg_offset++;
	}

	struct timespec t0;
	clock_gettime(CLOCK_MONOTONIC, &t0);

	pid_t exec_pid = fork();
	if (exec_pid == 0) {
		int err = execvp(argv[arg_offset], argv + arg_offset);
		if (err < 0) {
			fprintf(stderr, "[error] execv: %s (%d)\n", strerror(errno), errno);
			return -1;
		}
	}

	pid_t monitor_pid = 1;

	if (monitor) {
		monitor_pid = fork();
	}

	if (monitor_pid > 0) {
		int wstatus = 0;
		waitpid(exec_pid, &wstatus, 0);
		struct timespec t1;
		clock_gettime(CLOCK_MONOTONIC, &t1);
		struct rusage usage;
		getrusage(RUSAGE_CHILDREN, &usage);

		fprintf(stderr, "[time] (ns) start: %ld, end: %ld, duration: %ld\n",
				t0.tv_sec * 1000 * 1000 * 1000 + t0.tv_nsec,
				t1.tv_sec * 1000 * 1000 * 1000 + t1.tv_nsec,
				(t1.tv_sec - t0.tv_sec) * 1000 * 1000 * 1000 + (t1.tv_nsec - t0.tv_nsec));
		fprintf(stderr, "[time] (us) sys: %ld user: %ld\n",
				usage.ru_stime.tv_sec * 1000 * 1000 + usage.ru_stime.tv_usec,
				usage.ru_utime.tv_sec * 1000 * 1000 + usage.ru_utime.tv_usec);
		fprintf(stderr, "[mem] (kb) maxrss: %ld\n", usage.ru_maxrss);
		kill(monitor_pid, 9);
		return WIFEXITED(wstatus) ? WEXITSTATUS(wstatus) : 1;
	}

	assert(exec_pid < 100 * 1000);
	int n = strlen("/proc/12345/statm") + 1;
	char path[n + 1];
	snprintf(path, n + 1, "/proc/%d/statm", exec_pid);

	int fd = open(path, O_RDONLY);
	while (1) {
		char buf[256];
		ssize_t size = read(fd, buf, 256);
		if (size == 0) {
			fprintf(stderr, "[warn] read ret: 0\n");
			break;
		} else if (size < 0) {
			fprintf(stderr, "[warn] read ret: %s (%d)\n", strerror(errno), errno);
			break;
		}
		buf[size] = '\0';

		struct timespec tp;
		clock_gettime(CLOCK_MONOTONIC, &tp);
		fprintf(stderr, "[statm] %ld: %s", tp.tv_sec * 1000 * 1000 * 1000 + tp.tv_nsec, buf);
		lseek(fd, 0, SEEK_SET);

		struct timespec req = {
			.tv_sec = 0,
			.tv_nsec = 100L * 1000 * 1000,
		};
		nanosleep(&req, NULL);
	}
	close(fd);
}
