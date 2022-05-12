

public class Sort {
	public static long calls = 0;
	public static long time = 0;
	public static void swap(String[] arr, int lo, int hi) {
		//long t0 = System.nanoTime();
		String tmp = arr[lo];
		arr[lo] = arr[hi];
		arr[hi] = tmp;
		/*
		long t1 = System.nanoTime();
		time += t1 - t0;
		calls++;
		*/
	}

	public static void wmerge(String[] arr, int lo1, int hi1, int lo2, int hi2, int w) {
		while ((lo1 < hi1) && (lo2 < hi2)) {
			swap(arr, w++, (arr[lo1].compareTo(arr[lo2]) <= 0) ? lo1++ : lo2++);
		}
		while (lo1 < hi1) {
			swap(arr, w++, lo1++);
		}
		while (lo2 < hi2) {
			swap(arr, w++, lo2++);
		}
	}

	public static void wsort(String[] arr, int lo, int hi, int w) {
		if ((hi - lo) > 1) {
			int m = (lo + hi) / 2;
			imsort(arr, lo, m);
			imsort(arr, m, hi);
			wmerge(arr, lo, m, m, hi, w);
		} else if (lo != hi) {
			swap(arr, lo, w);
		}
	}

	public static void imsort(String[] arr, int lo, int hi) {
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
				for (int j = i; (j < hi) && (arr[j].compareTo(arr[j - 1]) < 0); j++) {
					swap(arr, j, j - 1);
				}
			}
		}
	}

	public static void permute(byte[][] l, int n, int m, int pos, int offset) {
		if (n == 0) {
			//l[0][pos] = '\0';
			return;
		}
		int size = 1;
		for (int i = 0; i < n - 1; i++) {
			size *= m;
		}
		for (int i = 0; i < m; i++) {
			for (int j = 0; j < size; j++) {
				l[offset + i * size + j][pos] = (byte) ('z' - i);
			}
			permute(l, n - 1, m, pos + 1, offset + i * size);
		}
	}

	public static String[] gen_array(int n, int m) {
		int size = 1;
		for (int i = 0; i < n; i++) {
			size *= m;
		}
		//System.out.print("array size " + size + "\n");
		//long t0 = System.nanoTime();
		byte[][] l = new byte[size][];
		//long t1 = System.nanoTime();
		//System.out.print("alloc 1 took " + (t1 - t0) + " ns\n");
		//t0 = System.nanoTime();
		for (int i = 0; i < l.length; i++) {
			l[i] = new byte[n];
		}
		//t1 = System.nanoTime();
		//System.out.print("alloc byte[]s took " + (t1 - t0) + " ns\n");
		long t0 = System.nanoTime();
		permute(l, n, m, 0, 0);
		long t1 = System.nanoTime();
		System.out.print("[info] permute: " + (t1 - t0) + " ns\n");
		//t0 = System.nanoTime();
		String[] l2 = new String[size];
		//t1 = System.nanoTime();
		//System.out.print("alloc 2 took " + (t1 - t0) + " ns\n");
		//t0 = System.nanoTime();
		for (int i = 0; i < l.length; i++) {
			l2[i] = new String(l[i]);
		}
		//t1 = System.nanoTime();
		//System.out.print("converting strings took " + (t1 - t0) + " ns\n");
		return l2;
	}

	public static boolean verify_array(String[] l) {
		for (int i = 1; i < l.length; i++) {
			if (l[i - 1].compareTo(l[i]) > 0) {
				return false;
			}
		}
		return true;
	}

	public static void main(String[] args) {
		long t0 = System.nanoTime();
		String[] l = gen_array(6, 18);
		long t1 = System.nanoTime();
		imsort(l, 0, l.length);
		long t2 = System.nanoTime();
		System.out.print("[info] gen_array: " + (t1 - t0) + " ns\n");
		System.out.print("[info] sort: " + (t2 - t1) + " ns\n");
		if (!verify_array(l)) {
			throw new RuntimeException("badness");
		}
		System.out.print("[debug] calls: " + calls + ", time: " + time + "\n");
	}
}
