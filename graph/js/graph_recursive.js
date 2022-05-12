

const assert = require("assert");
const fs = require("fs");
const readline = require("readline");
const rlimit = require("./build/Release/rlimit_set_stack");

class Vertex {
	constructor(id, colour) {
		this.id = id;
		this.colour = colour;
		this.next = null;
		this.prev = null;
		this.neighbours = new Set();
	}

	get degree() {
		return this.neighbours.size;
	}

	sudoku() {
		this.prev.next = this.next;
		if (this.next != null) {
			this.next.prev = this.prev;
		}
		for (let v of this.neighbours) {
			let b = v.neighbours.delete(this);
			assert(b);
		}
	}

	induce() {
		let induced = new Graph();
		let m = {};
		Graph.explore(this, induced, m, this.neighbours);
		return induced;
	}
}

class Graph {
	constructor() {
		this.dummy = new Vertex(null);
		this.size = 0;
	}

	get head() {
		return this.dummy.next;
	}

	set head(v) {
		this.dummy.next = v;
	}

	shift(v) {
		let h = this.head;
		if (h != null) {
			v.next = h;
			v.prev = this.dummy;
			h.prev = v;
		}
		this.head = v;
		this.size++;
	}

	duplicate() {
		let dup = new Graph();
		let m = {};
		for (let v = this.head; v != null; v = v.next) {
			Graph.explore(v, dup, m, null);
		}
		return dup;
	}

	static explore(start, g, m, valid) {
		let new_vertex = m[start.id];
		if (new_vertex != undefined) {
			return new_vertex;
		}
		new_vertex = new Vertex(start.id, start.colour);
		start.colour.value = 0;
		m[start.id] = new_vertex;
		for (let v of start.neighbours) {
			if (valid != null && !valid.has(v)) {
				continue;
			}
			let neighbour = Graph.explore(v, g, m, valid);
			new_vertex.neighbours.add(neighbour);
		}
		g.shift(new_vertex);
		return new_vertex;
	}

	static explore_iterative(start, g, m, valid) {
		let stack = [];
		stack.push([ start, null ]);
		while (stack.length > 0) {
			let tuple = stack.pop()
			start = tuple[0]
			let sibling = tuple[1]
			let new_vertex = m[start.id];
			if (new_vertex != undefined) {
				if (sibling != null) {
					sibling.neighbours.add(new_vertex);
				}
				continue;
			}
			new_vertex = new Vertex(start.id, start.colour);
			start.colour.value = 0;
			m[start.id] = new_vertex;
			for (let v of start.neighbours) {
				if (valid != null && !valid.has(v)) {
					continue;
				}
				stack.push([ v, new_vertex ])
			}
			g.shift(new_vertex);
			if (sibling != null) {
				sibling.neighbours.add(new_vertex);
			}
		}
	}

	social_credit(bad) {
		bad.sudoku();
		this.size--;
		for (let v of bad.neighbours) {
			v.sudoku();
			this.size--;
		}
	}

	verify_colouring() {
		for (let v = this.head; v != null; v = v.next) {
			if (v.colour.value == 0) {
				return false;
			}
			for (let u of v.neighbours) {
				if (v.colour.value == u.colour.value) {
					return false;
				}
			}
		}
		return true;
	}

	find_max_degree_vertex() {
		let max = 0;
		let ret = null;
		for (let v = this.head; v != null; v = v.next) {
			let d = v.degree;
			if (d > max) {
				ret = v;
				max = d;
			}
		}
		return ret;
	}

	static magic_f(k, n) {
		return Math.ceil(Math.pow(n, 1 - (1 / (k - 1))));
	}

	static k_ge_log_n(k, n) {
		let x = 1;
		for (let i = 0; i < k; i++) {
			x *= 2;
		}
		return x >= n;
	}

	colour_2(i, j) {
		for (let v = this.head; v != null; v = v.next) {
			if (v.colour.value != 0) {
				continue;
			}
			if (!Graph.colour_2_helper(v, i, j)) {
				return false;
			}
		}
		return true;
	}

	static colour_2_helper(v, i, j) {
		if (v.colour.value == j) {
			return false;
		}
		if (v.colour.value == 0) {
			v.colour.value = i;
			for (let u of v.neighbours) {
				if (!Graph.colour_2_helper(u, j, i)) {
					return false;
				}
			}
		}
		return true;
	}

	static colour_2_helper_iterative(v, i, j) {
		let stack = [];
		stack.push([ v, i, j ]);
		while (stack.length > 0) {
			let tuple = stack.pop();
			v = tuple[0];
			i = tuple[1];
			j = tuple[2];
			if (v.colour.value == j) {
				return false;
			}
			if (v.colour.value == 0) {
				v.colour.value = i;
				for (let u of v.neighbours) {
					stack.push([ u, j, i ]);
				}
			}
		}
		return true;
	}

	colour_b(k, i) {
		if (k == 2) {
			if (this.colour_2(i, i + 1)) {
				//console.log("B2: k = " + k + " ret = 2");
				return 2;
			}
			//console.log("B2: k = " + k + " ret = 0");
			return 0;
		}
		let n = this.size;
		if (Graph.k_ge_log_n(k, n)) {
			let j = 0;
			for (let v = this.head; v != null; v = v.next) {
				v.colour.value = i + j;
				j++;
			}
			//console.log("Bn: k = " + k + " ret = " + n);
			return n;
		}
		while (true) {
			let v = this.find_max_degree_vertex();
			if (v.degree < Graph.magic_f(k, n)) {
				//console.log("- breaking k = " + k + " degree = " + v.degree + " magic = " + Graph.magic_f(k, n));
				break;
			}
			let h = v.induce();
			let j = h.colour_b(k - 1, i);
			if (j == 0) {
				//console.log("Bfail: k = " + k + " ret = 0");
				return 0;
			}
			i += j;
			v.colour.value = i;
			this.social_credit(v);
		}
		let max_degree = 0;
		let max_colour = 0;
		for (let v = this.head; v != null; v = v.next) {
			let seen = new Set();
			for (let e of v.neighbours) {
				seen.add(e.colour.value);
			}
			if (max_degree < v.degree) {
				max_degree = v.degree;
			}
			for (let j = i; true; j++) {
				if (!seen.has(j)) {
					v.colour.value = j;
					if (max_colour < j) {
						max_colour = j;
					}
					break;
				}
			}
		}
		assert(max_colour < max_degree + i + 1);

		let ret = max_colour - i + 1;
		let bound = 2 * k * Graph.magic_f(k, n);
		//console.log("Bend: k = " + k + " ret = " + ret);
		return ret > bound ? 0 : ret;
	}

	colour_c() {
		let i = 1;
		while (this.duplicate().colour_b(1 << i, 1) == 0) {
			i++;
		}
		//console.log("C: i = " + i);

		let l = (1 << (i - 1)) + 1;
		let r = 1 << i;
		while (l < r) {
			let m = Math.floor((l + r) / 2);
			if (this.duplicate().colour_b(m, 1) == 0) {
				l = m + 1;
			} else {
				r = m;
			}
		}
		let k = this.duplicate().colour_b(l, 1);
		assert(k != 0);
		return k;
	}

	static from_file(path, callback) {
		let g = new Graph();
		let rl = readline.createInterface({
			input: fs.createReadStream(path, { encoding: 'utf-8' }),
			crlfDelay: Infinity,
		});
		let m = {};
		rl.on("line", function(line) {
			if (line.startsWith("#")) {
				return;
			}
			let parts = line.split(/\s+/);
			let x = parseInt(parts[0], 10);
			let y = parseInt(parts[1], 10);
			let vx = m[x];
			let vy = m[y];
			if (vx == undefined) {
				vx = new Vertex(x, { value: 0 });
				m[x] = vx;
				g.shift(vx);
			}
			if (vy == undefined) {
				vy = new Vertex(y, { value: 0 });
				m[y] = vy;
				g.shift(vy);
			}
			vx.neighbours.add(vy);
			vy.neighbours.add(vx);
		});
		rl.on("close", function() {
			callback(g);
		});
	}
}

function main(args) {
	rlimit.rlimit_set_stack();
	Graph.from_file(args[0], function(g) {
		let k = g.colour_c();
		console.log("k = " + k);
		let b = g.verify_colouring();
		assert(b);
	});
}

if (!module.parent) {
	main(process.argv.slice(2));
}
