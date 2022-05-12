

let arr = []
for (let i = 0; i < 1000 * 1000; i++) {
	let t0 = process.hrtime();
	let t1 = process.hrtime();
	arr.push((t1[0] - t0[0]) * 1000 * 1000 * 1000 + (t1[1] - t0[1]));
}

for (let i = 0; i < arr.length; i++) {
	console.log(arr[i]);
}
