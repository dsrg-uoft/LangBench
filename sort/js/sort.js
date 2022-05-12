

const assert = require("assert");

function now() {
	let t = process.hrtime();
	return t[0] * 1e9 + t[1];
}

function swap(arr, lo, hi) {
	let tmp = arr[lo];
	arr[lo] = arr[hi];
	arr[hi] = tmp;
}

function wmerge(arr, lo1, hi1, lo2, hi2, w) {
	while ((lo1 < hi1) && (lo2 < hi2)) {
		swap(arr, w++, (arr[lo1] <= arr[lo2]) ? lo1++ : lo2++);
	}
	while (lo1 < hi1) {
		swap(arr, w++, lo1++);
	}
	while (lo2 < hi2) {
		swap(arr, w++, lo2++);
	}
}

function wsort(arr, lo, hi, w) {
	if ((hi - lo) > 1) {
		let m = Math.floor((lo + hi) / 2);
		imsort(arr, lo, m);
		imsort(arr, m, hi);
		wmerge(arr, lo, m, m, hi, w);
	} else if (lo != hi) {
		swap(arr, lo, w);
	}
}

function imsort(arr, lo, hi) {
	if ((hi - lo) > 1) {
		let m = Math.floor((lo + hi) / 2);
		let w = lo + hi - m;
		wsort(arr, lo, m, w);
		while ((w - lo) > 2) {
			let n = w;
			w = Math.floor((lo + n + 1) / 2);
			wsort(arr, w, n, lo);
			wmerge(arr, lo, lo + n - w, n, hi, w);
		}
		for (let i = w; i > lo; i--) {
			for (let j = i; (j < hi) && (arr[j] < arr[j - 1]); j++) {
				swap(arr, j, j - 1);
			}
		}
	}
}

function permute(l, n, m, pos, offset) {
	if (n == 0) {
		l[0][pos] = '\0';
		return;
	}
	let size = 1;
	for (let i = 0; i < n - 1; i++) {
		size *= m;
	}
	let z = "z".charCodeAt(0);
	for (let i = 0; i < m; i++) {
		let ch = String.fromCharCode(z - i);
		for (let j = 0; j < size; j++) {
			l[offset + i * size + j][pos] = ch;
		}
		permute(l, n - 1, m, pos + 1, offset + i * size);
	}
}

function gen_array(n, m) {
	let size = 1;
	for (let i = 0; i < n; i++) {
		size *= m;
	}
	//console.log("array size " + size);
	//let t0 = now();
	let l = new Array(size);
	//let t1 = now();
	//console.log("alloc 1 took " + (t1 - t0) + " ns");
	//t0 = now();
	for (let i = 0; i < l.length; i++) {
		l[i] = new Array(n);
	}
	//t1 = now();
	//console.log("alloc byte[]s took " + (t1 - t0) + " ns");
	let t0 = now();
	permute(l, n, m, 0, 0);
	let t1 = now();
	console.log("[info] permute: " + (t1 - t0) + " ns");
	//t0 = now();
	let l2 = new Array(size);
	//t1 = now();
	//console.log("alloc 2 took " + (t1 - t0) + " ns");
	//t0 = now();
	for (let i = 0; i < l.length; i++) {
		l2[i] = l[i].join("");
	}
	//t1 = now();
	//console.log("converting strings took " + (t1 - t0) + " ns");
	return l2;
}

function verify_array(l) {
	for (let i = 1; i < l.length; i++) {
		if (l[i - 1] > l[i]) {
			return false;
		}
	}
	return true;
}

function main(args) {
	let t0 = now();
	let l = gen_array(6, 18);
	let t1 = now();
	imsort(l, 0, l.length);
	let t2 = now();
	console.log("[info] gen_array: " + (t1 - t0) + " ns");
	console.log("[info] sort: " + (t2 - t1) + " ns");
	assert(verify_array(l));
}

if (!module.parent) {
	main(process.argv.slice(2));
}
