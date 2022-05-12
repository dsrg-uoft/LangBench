#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <stdio.h>
#include <assert.h>
#include <time.h>

static long time_diff(struct timespec start, struct timespec end) {
	time_t sec = end.tv_sec - start.tv_sec;
	long nano = end.tv_nsec - start.tv_nsec;
	return (long) sec * 1000 * 1000 * 1000 + nano;
}

static void swap(char** arr, int lo, int hi) {
	char* tmp = arr[lo];
	arr[lo] = arr[hi];
	arr[hi] = tmp;
}

static void wmerge(char** arr, int lo1, int hi1, int lo2, int hi2, int w) {
	while ((lo1 < hi1) && (lo2 < hi2)) {
		swap(arr, w++, (strcmp(arr[lo1], arr[lo2]) <= 0) ? lo1++ : lo2++);
	}
	while (lo1 < hi1) {
		swap(arr, w++, lo1++);
	}
	while (lo2 < hi2) {
		swap(arr, w++, lo2++);
	}
}

static void imsort(char** arr, int lo, int hi);

static void wsort(char** arr, int lo, int hi, int w) {
	if ((hi - lo) > 1) {
		int m = (lo + hi) / 2;
		imsort(arr, lo, m);
		imsort(arr, m, hi);
		wmerge(arr, lo, m, m, hi, w);
	} else if (lo != hi) {
		swap(arr, lo, w);
	}
}

void imsort(char** arr, int lo, int hi) {
	if ((hi - lo) > 1) {
		int m = (lo + hi) / 2;
		int w = lo + hi - m;
		wsort(arr, lo, m, w);
		while ((w - lo) > 2) {
			int n = w;
			w = (lo + n + 1) / 2;
			wsort(arr, w, n, lo);
			wmerge(arr, lo, lo + n - w, n, hi, w);
		}
		for (int i = w; i > lo; i--) {
			for (int j = i; (j < hi) && (strcmp(arr[j], arr[j - 1]) < 0); j++) {
				swap(arr, j, j - 1);
			}
		}
	}
}

static void permute(char** l, int n, int m, int pos) {
	if (n == 0) {
		l[0][pos] = '\0';
		return;
	}
	int size = 1;
	for (int i = 0; i < n - 1; i++) {
		size *= m;
	}
	for (int i = 0; i < m; i++) {
		for (int j = 0; j < size; j++) {
			l[i * size + j][pos] = 'z' - i;
		}
		permute(l + i * size, n - 1, m, pos + 1);
	}
}

static char** gen_array(int n, int m, int* size) {
	struct timespec t0, t1;
	*size = 1;
	for (int i = 0; i < n; i++) {
		*size *= m;
	}
	char** l = (char**) malloc((*size) * sizeof(char*));
	for (int i = 0; i < *size; i++) {
		l[i] = (char*) malloc((n + 1) * sizeof(char));
	}
	clock_gettime(CLOCK_MONOTONIC, &t0);
	permute(l, n, m, 0);
	clock_gettime(CLOCK_MONOTONIC, &t1);
	printf("[info] permute: %ld ns\n", time_diff(t0, t1));
	return l;
}

static bool verify_array(char** l, int size) {
	for (int i = 1; i < size; i++) {
		if (strcmp(l[i - 1], l[i]) > 0) {
			return false;
		}
	}
	return true;
}

int main(int argc, char* argv[]) {
	struct timespec t0, t1, t2;
	int size;
	clock_gettime(CLOCK_MONOTONIC, &t0);
	char** l = gen_array(6, 18, &size);
	clock_gettime(CLOCK_MONOTONIC, &t1);
	imsort(l, 0, size);
	clock_gettime(CLOCK_MONOTONIC, &t2);
	printf("[info] gen_array: %ld ns\n", time_diff(t0, t1));
	printf("[info] sort: %ld ns\n", time_diff(t1, t2));
	assert(verify_array(l, size));
	for (int i = 0; i < size; i++) {
		free(l[i]);
	}
	free(l);
	return 0;
}
