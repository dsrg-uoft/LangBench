import time
from typing import List

def swap(arr: List[str], lo: int, hi: int) -> None:
	tmp: str = arr[lo]
	arr[lo] = arr[hi]
	arr[hi] = tmp

def wmerge(arr: List[str], lo1: int, hi1: int, lo2: int, hi2: int, w: int) -> None:
	while (lo1 < hi1) and (lo2 < hi2):
		lo: int
		if arr[lo1] <= arr[lo2]:
			lo = lo1
			lo1 += 1
		else:
			lo = lo2
			lo2 += 1
		swap(arr, w, lo)
		w += 1
	while lo1 < hi1:
		swap(arr, w, lo1)
		w += 1
		lo1 += 1
	while lo2 < hi2:
		swap(arr, w, lo2)
		w += 1
		lo2 += 1

def wsort(arr: List[str], lo: int, hi: int, w: int) -> None:
	if (hi - lo) > 1:
		m: int = (lo + hi) // 2
		imsort(arr, lo, m)
		imsort(arr, m, hi)
		wmerge(arr, lo, m, m, hi, w)
	elif lo != hi:
		swap(arr, lo, w)

def imsort(arr: List[str], lo: int, hi: int) -> None:
	if (hi - lo) > 1:
		m: int = (lo + hi) // 2
		w: int = lo + hi - m
		wsort(arr, lo, m, w)
		while (w - lo) > 2:
			n: int = w
			w = (lo + n + 1) // 2
			wsort(arr, w, n, lo)
			wmerge(arr, lo, lo + n - w, n, hi, w)
		i: int = w
		while i > lo:
			j: int = i
			while (j < hi) and (arr[j] < arr[j - 1]):
				swap(arr, j, j - 1);
				j += 1
			i -= 1

def permute(l: List[bytearray], n: int, m: int, pos: int, offset: int) -> None:
	if n == 0:
		return
	size: int = 1
	for i in range(n - 1):
		size *= m
	for i in range(m):
		for j in range(size):
			l[offset + i * size + j][pos] = ord('z') - i
		permute(l, n - 1, m, pos + 1, offset + i * size)

def gen_array(n: int, m: int) -> List[str]:
	l: List[bytearray] = []
	size: int = 1
	for i in range(n):
		size *= m
	source: str = "0" * n
	for i in range(size):
		l.append(bytearray(source, encoding = "utf-8"))
	t0: float = time.time()
	permute(l, n, m, 0, 0)
	t1: float = time.time()
	print("[info] permute: {} ns".format((t1 - t0) * 1e9))
	l2: List[str] = []
	for i, word in enumerate(l):
		l2.append(word.decode())
	print(len(l2))
	return l2

def verify_array(l: List[str]) -> bool:
	for i in range(1, len(l)):
		if l[i - 1] > l[i]:
			return False
	return True

def main() -> None:
	t0: float = time.time()
	l: List[str] = gen_array(6, 18)
	t1: float = time.time()
	imsort(l, 0, len(l))
	t2: float = time.time()
	print("[info] gen_array: {} ns".format((t1 - t0) * 1e9))
	print("[info] sort: {} ns".format((t2 - t1) * 1e9))
	assert(verify_array(l))
	return

if __name__ == '__main__':
	main()
