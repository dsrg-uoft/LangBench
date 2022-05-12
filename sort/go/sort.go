package main

import "time"
import "fmt"

func assert(cond bool) {
	if !cond {
		panic("badness")
	}
}

func swap(arr []string, lo int, hi int) {
	var tmp string = arr[lo]
	arr[lo] = arr[hi]
	arr[hi] = tmp
}

func wmerge(arr []string, lo1 int, hi1 int, lo2 int, hi2 int, w int) {
	for ((lo1 < hi1) && (lo2 < hi2)) {
		var lo_old int
		if arr[lo1] <= arr[lo2] {
			lo_old = lo1
			lo1++
		} else {
			lo_old = lo2
			lo2++
		}
		var w_old int = w
		w++
		swap(arr, w_old, lo_old)
	}
	for (lo1 < hi1) {
		var w_old int = w
		w++
		var lo_old int = lo1
		lo1++
		swap(arr, w_old, lo_old)
	}
	for (lo2 < hi2) {
		var w_old int = w
		w++
		var lo_old int = lo2
		lo2++
		swap(arr, w_old, lo_old)
	}
}

func wsort(arr []string, lo int, hi int, w int) {
	if (hi - lo) > 1 {
		var m int = (lo + hi) / 2
		imsort(arr, lo, m)
		imsort(arr, m, hi)
		wmerge(arr, lo, m, m, hi, w)
	} else if lo != hi {
		swap(arr, lo, w)
	}
}

func imsort(arr []string, lo int, hi int) {
	if (hi - lo) > 1 {
		var m int = (lo + hi) / 2
		var w int = lo + hi - m
		wsort(arr, lo, m, w)
		for (w - lo) > 2 {
			var n int = w
			w = (lo + n + 1) / 2
			wsort(arr, w, n, lo)
			wmerge(arr, lo, lo + n - w, n, hi, w)
		}
		for i := w; i > lo; i-- {
			for j := i; (j < hi) && (arr[j] < arr[j - 1]); j++ {
				swap(arr, j, j - 1)
			}
		}
	}
}

func permute(l [][]byte, n int, m int, pos int) {
	if n == 0 {
		return
	}
	var size int = 1
	for i := 0; i < n - 1; i++ {
		size *= m
	}
	for i := 0; i < m; i++ {
		for j := 0; j < size; j++ {
			l[i * size + j][pos] = byte('z' - i)
		}
		permute(l[i * size:], n - 1, m, pos + 1);
	}
}

func gen_array(n int, m int, size *int) []string {
	*size = 1
	for i := 0; i < n; i++ {
		*size *= m
	}
	var l [][]byte = make([][]byte, *size)
	for i := 0; i < *size; i++ {
		l[i] = make([]byte, n)
	}
	var t0 time.Time = time.Now()
	permute(l, n, m, 0);
	var t1 time.Time = time.Now()
	fmt.Printf("[info] permute: %v ns\n", t1.Sub(t0).Nanoseconds())
	var result []string = make([]string, *size)
	for i := 0; i < *size; i++ {
		result[i] = string(l[i])
	}
	return result
}

func verify_array(l []string) bool {
	for i := 1; i < len(l); i++ {
		if l[i - 1] > l[i] {
			return false
		}
	}
	return true
}

func main() {
	var size int
	var t0 time.Time = time.Now()
	var l []string = gen_array(6, 18, &size)
	var t1 time.Time = time.Now()
	imsort(l, 0, size)
	var t2 time.Time = time.Now()
	fmt.Printf("[info] gen_array: %v ns\n", t1.Sub(t0).Nanoseconds())
	fmt.Printf("[info] sort: %v ns\n", t2.Sub(t1).Nanoseconds())
	assert(verify_array(l))
}
