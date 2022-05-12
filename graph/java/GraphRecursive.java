

import java.util.Map;
import java.util.HashMap;
import java.util.Set;
import java.util.HashSet;
import java.util.List;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Stack;
import java.io.File;
import java.io.FileInputStream;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class GraphRecursive {
	private Vertex dummy;
	public int size;
	public long find_time;
	public long setfind_time;
	public long insert_time;
	public long setinsert_time;
	public long loop_time;
	public long alloc_time;
	public static final boolean ITERATIVE = false;

	public GraphRecursive() {
		this.dummy = new Vertex(null);
	}

	/*
	public static void explore(Vertex start, Graph g, Map<Vertex, Vertex> m, Set<Vertex> valid) {
		if (Graph.ITERATIVE) {
			Graph.explore_iterative(start, g, m, valid);
		} else {
			Graph.explore_recursive(start, g, m, valid);
		}
	}

	public static boolean colour_2_helper(Vertex v, int i, int j) {
		if (Graph.ITERATIVE) {
			return Graph.colour_2_helper_iterative(v, i, j);
		} else {
			return Graph.colour_2_helper_recursive(v, i, j);
		}
	}
	*/

	public Vertex head() {
		return this.dummy.next;
	}

	private static class Colour {
		public int value;
	}

	public void shift(Vertex v) {
		Vertex h = this.head();
		if (h != null) {
			v.next = h;
			v.prev = this.dummy;
			h.prev = v;
		}
		this.dummy.next = v;
		this.size++;
	}

	public GraphRecursive duplicate() {
		long t0, t1;
		//t0 = System.nanoTime();
		GraphRecursive dup = new GraphRecursive();
		Map<Vertex, Vertex> m = new HashMap<>();

		for (Vertex v = this.head(); v != null; v = v.next) {
			GraphRecursive.explore_recursive(v, dup, m, null);
		}
		//t1 = System.nanoTime();
		//System.out.print("duplicate: " + (t1 - t0) + "\n");
		//System.out.print("find: " + dup.find_time + " insert: " + dup.insert_time + " setinsert: " + dup.setinsert_time + " loop: " + dup.loop_time + " alloc: " + dup.alloc_time + "\n");
		return dup;
	}

	public static Vertex explore_recursive(Vertex start, GraphRecursive g, Map<Vertex, Vertex> m, Set<Vertex> valid) {
		long t0, t1;
		//t0 = System.nanoTime();
		Vertex new_vertex = m.get(start);
		//t1 = System.nanoTime();
		//g.find_time += t1 - t0;
		if (new_vertex != null) {
			return new_vertex;
		}
		//t0 = System.nanoTime();
		new_vertex = new Vertex(start.colour);
		//t1 = System.nanoTime();
		//g.alloc_time += t1 - t0;
		start.colour.value = 0;
		//t0 = System.nanoTime();
		m.put(start, new_vertex);
		//t1 = System.nanoTime();
		//g.insert_time += t1 - t0;
		long t2, t3;
		//t2 = System.nanoTime();
		for (Vertex v : start.neighbours) {
			//t3 = System.nanoTime();
			//g.loop_time += t3 - t2;
			if (valid != null) {
				//t0 = System.nanoTime();
				boolean found = valid.contains(v);
				//t1 = System.nanoTime();
				//g.setfind_time += t1 - t0;
				if (!found) {
					//t2 = System.nanoTime();
					continue;
				}
			}
			Vertex neighbour = GraphRecursive.explore_recursive(v, g, m, valid);
			//t0 = System.nanoTime();
			new_vertex.neighbours.add(neighbour);
			//t1 = System.nanoTime();
			//g.setinsert_time += t1 - t0;
			//t2 = System.nanoTime();
		}
		//t3 = System.nanoTime();
		//g.loop_time += t3 - t2;
		g.shift(new_vertex);
		return new_vertex;
	}

	public static void explore_iterative(Vertex start, GraphRecursive g, Map<Vertex, Vertex> m, Set<Vertex> valid) {
		Stack<Vertex[]> vertex_stack = new Stack<>();
		vertex_stack.push(new Vertex[] {start, null});
		while (!vertex_stack.empty()) {
			Vertex[] tmp = vertex_stack.pop();
			Vertex v = tmp[0];
			Vertex sibling = tmp[1];

			Vertex new_vertex = m.get(v);
			if (new_vertex != null) {
				if (sibling != null) {
					sibling.neighbours.add(new_vertex);
				}
				continue;
			}

			new_vertex = new Vertex(v.colour);
			v.colour.value = 0;
			m.put(v, new_vertex);

			for (Vertex u : v.neighbours) {
				if (valid != null) {
					boolean found = valid.contains(u);
					if (!found) {
						continue;
					}
				}
				vertex_stack.push(new Vertex[] {u, new_vertex});
			}
			g.shift(new_vertex);
			if (sibling != null) {
				sibling.neighbours.add(new_vertex);
			}
		}
	}

	public void social_credit(Vertex bad) {
		//System.out.print("called social_credit\n");
		bad.sudoku();
		this.size--;
		for (Vertex v : bad.neighbours) {
			for (Vertex u : v.neighbours) {
				if (u == bad) {
					//System.out.print("u == bad\n");
				}
			}
			v.sudoku();
			this.size--;
		}
	}

	private static class Vertex {
		private Vertex next;
		private Vertex prev;
		public Colour colour;
		public Set<Vertex> neighbours;

		public Vertex() {
			this(new Colour());
		}

		public Vertex(Colour c) {
			this.colour = c;
			this.neighbours = new HashSet<>();
		}

		public int degree() {
			return this.neighbours.size();
		}

		public void sudoku() {
			this.prev.next = this.next;
			if (this.next != null) {
				this.next.prev = this.prev;
			}
			for (Vertex v : this.neighbours) {
				boolean b = v.neighbours.remove(this);
				if (!b) {
					throw new RuntimeException("failed to remove vertex from neighbour");
				}
			}
		}

		public GraphRecursive induce() {
			long t0, t1;
			//t0 = System.nanoTime();
			GraphRecursive induced = new GraphRecursive();
			Map<Vertex, Vertex> m = new HashMap<>();

			GraphRecursive.explore_recursive(this, induced, m, this.neighbours);
			//t1 = System.nanoTime();
			//System.out.print("induce: " + (t1 - t0) + "\n");
			//System.out.print("find: " + induced.find_time + " setfind: " + induced.setfind_time + " insert: " + induced.insert_time + " loop: " + induced.loop_time + "\n");
			return induced;
		}
	}

	public boolean verify_colouring() {
		for (Vertex v = this.head(); v != null; v = v.next) {
			if (v.colour.value == 0) {
				return false;
			}
			for (Vertex u : v.neighbours) {
				if (v.colour.value == u.colour.value) {
					return false;
				}
			}
		}
		return true;
	}

	public Vertex find_max_degree_vertex() {
		int max = 0;
		Vertex ret = null;
		for (Vertex v = this.head(); v != null; v = v.next) {
			int d = v.degree();
			if (d > max) {
				ret = v;
				max = d;
			}
		}
		return ret;
	}

	public static double magic_f(int k, int n) {
		return Math.ceil(Math.pow(n, 1 - (1.0 / (k - 1))));
	}

	public static boolean k_ge_log_n(int k, int n) {
		long x = 1;
		for (int i = 0; i < k; i++) {
			x *= 2;
		}
		return x >= n;
	}

	public boolean colour_2(int i, int j) {
		for (Vertex v = this.head(); v != null; v = v.next) {
			if (v.colour.value != 0) {
				continue;
			}
			if (!GraphRecursive.colour_2_helper_recursive(v, i, j)) {
				return false;
			}
		}
		return true;
	}

	public static boolean colour_2_helper_recursive(Vertex v, int i, int j) {
		if (v.colour.value == j) {
			return false;
		}
		if (v.colour.value == 0) {
			v.colour.value = i;
			for (Vertex u : v.neighbours) {
				if (!GraphRecursive.colour_2_helper_recursive(u, j, i)) {
					return false;
				}
			}
		}
		return true;
	}

	private static class C2Tuple {
		Vertex v;
		int i;
		int j;
		public C2Tuple(Vertex v, int i, int j) {
			this.v = v;
			this.i = i;
			this.j = j;
		}
	}

	public static boolean colour_2_helper_iterative(Vertex start, int i, int j) {
		Stack<C2Tuple> vertex_stack = new Stack<>();
		vertex_stack.push(new C2Tuple(start, i, j));
		while (!vertex_stack.empty()) {
			C2Tuple tmp = vertex_stack.pop();
			Vertex v = tmp.v;
			i = tmp.i;
			j = tmp.j;
			if (v.colour.value == j) {
				return false;
			}

			if (v.colour.value == 0) {
				v.colour.value = i;
				for (Vertex u : v.neighbours) {
					vertex_stack.push(new C2Tuple(u, j, i));
				}
			}
		}
		return true;
	}

	public int colour_b(int k, int i) {
		long t0, t1;
		//t0 = System.nanoTime();
		if (k == 2) {
			if (this.colour_2(i, i + 1)) {
				//System.out.print("B2: k = " + k + " ret = 2\n");
				return 2;
			}
			//System.out.print("B2: k = " + k + " ret = 0\n");
			return 0;
		}
		int n = this.size;
		if (GraphRecursive.k_ge_log_n(k, n)) {
			int j = 0;
			for (Vertex v = this.head(); v != null; v = v.next) {
				v.colour.value = i + j;
				j++;
			}
			//System.out.print("Bn: k = " + k + " ret = " + n + "\n");
			return n;
		}
		while (true) {
			Vertex v = this.find_max_degree_vertex();
			if (v.degree() < GraphRecursive.magic_f(k, n)) {
				//System.out.print("- breaking k = " + k + " degree = " + v.degree() + " magic = " + GraphRecursive.magic_f(k, n) + "\n");
				break;
			}
			/*
			if (v.degree() < (k * k)) {
				break;
			}
			*/
			//System.out.print("- looping k = " + k + " degree = " + v.degree() + " magic = " + GraphRecursive.magic_f(k, n) + "\n");
			GraphRecursive h = v.induce();
			int j = h.colour_b(k - 1, i);
			if (j == 0) {
				//System.out.print("Bfail: k = " + k + " ret = 0\n");
				return 0;
			}
			i += j;
			v.colour.value = i;
			this.social_credit(v);
		}
		int max_degree = 0;
		int max_colour = 0;
		int edge_count = 0;
		for (Vertex v = this.head(); v != null; v = v.next) {
			Set<Integer> seen = new HashSet<>();
			for (Vertex e : v.neighbours) {
				seen.add(e.colour.value);
				edge_count++;
			}
			if (max_degree < v.degree()) {
				max_degree = v.degree();
			}
			for (int j = i; true; j++) {
				if (!seen.contains(j)) {
					v.colour.value = j;
					if (max_colour < j) {
						max_colour = j;
					}
					break;
				}
			}
		}
		//System.out.print("vertices: " + this.size + " edges: " + edge_count + "\n");
		if (max_colour >= max_degree + i + 1) {
			throw new RuntimeException("max_colour("+ max_colour + ") >= max_degree("+ max_degree + ") + i("+ i + ") + 1");
		}

		int ret = max_colour - i + 1;
		double bound = 2 * k * GraphRecursive.magic_f(k, n);
		//System.out.print("Bend: k = " + k + " ret = " + ret + "\n");
		//t1 = System.nanoTime();
		//System.out.print("colour_b: " + (t1 - t0) + "\n");
		return ret > bound ? 0 : ret;
	}

	public int colour_c() {
		int i = 1;
		while (this.duplicate().colour_b(1 << i, 1) == 0) {
			i++;
		}
		//System.out.print("C: i = " + i + "\n");

		int l = (1 << (i - 1)) + 1;
		int r = 1 << i;
		while (l < r) {
			int m = (l + r) / 2;
			if (this.duplicate().colour_b(m, 1) == 0) {
				l = m + 1;
			} else {
				r = m;
			}
		}
		int k = this.duplicate().colour_b(l, 1);
		if (k == 0) {
			throw new RuntimeException("badness");
		}

		return k;
	}

	public static GraphRecursive from_file(File path) {
		GraphRecursive g = new GraphRecursive();
		try (BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(path), StandardCharsets.UTF_8))) {
			Map<Integer, Vertex> m = new HashMap<>();
			while (true) {
				String line = br.readLine();
				if (line == null) {
					break;
				}
				if (line.startsWith("#")) {
					continue;
				}
				String[] parts = line.split("\\s+");
				Integer x = Integer.valueOf(parts[0]);
				Integer y = Integer.valueOf(parts[1]);
				Vertex vx = m.get(x);
				if (vx == null) {
					vx = new Vertex();
					m.put(x, vx);
					g.shift(vx);
				}
				Vertex vy = m.get(y);
				if (vy == null) {
					vy = new Vertex();
					m.put(y, vy);
					g.shift(vy);
				}
				vx.neighbours.add(vy);
				vy.neighbours.add(vx);
			}
		} catch (IOException ex) {
			throw new RuntimeException(ex);
		}
		return g;
	}

	public static void main(String[] args) {
		long t0, t1, t2, t3;
		//t0 = System.nanoTime();
		GraphRecursive g = GraphRecursive.from_file(new File(args[0]));
		//t1 = System.nanoTime();
		int k = g.colour_c();
		//t2 = System.nanoTime();
		System.out.print("k = " + k + "\n");
		if (!g.verify_colouring()) {
			System.out.print("verify failed\n");
			System.exit(1);
		}
		//t3 = System.nanoTime();
		//System.out.print("from_file: " + (t1 - t0) + " colour_c: " + (t2 - t1) + " verify: " + (t3 - t2) + "\n");
	}
}
