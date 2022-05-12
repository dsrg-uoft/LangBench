#include <cstdio>
#include <cassert>
#include <fstream>
#include <sstream>
#include <iostream>
#include <cassert>
#include <stack>
#include <utility>
#include <tuple>
#include <ctime>
#include <sys/resource.h>
#include "graph.h"

long time_diff(struct timespec start, struct timespec end) {
	time_t sec = end.tv_sec - start.tv_sec;
	long nano = end.tv_nsec - start.tv_nsec;
	return (long) sec * 1000 * 1000 * 1000 + nano;
}

Graph::~Graph() {
	UniquePtr<Vertex> curr = std::move(this->dummy);
	while (curr != nullptr) {
		UniquePtr<Vertex> tmp = std::move(curr->next);
		curr = std::move(tmp);
	}
}

void Graph::shift(UniquePtr<Vertex> v) {
	Vertex *h = this->head();
	if (h != nullptr) {
		v->next = std::move(this->dummy->next);
		v->prev = this->dummy.get();
		h->prev = v.get();
	}
	this->dummy->next = std::move(v);
	this->size++;
}

UniquePtr<Graph> Graph::duplicate() {
	//struct timespec t0, t1;
	//clock_gettime(CLOCK_MONOTONIC, &t0);
	UniquePtr<Graph> dup = MAKE_UNIQUE<Graph>();
	Map<Vertex *, Vertex *> m;

	struct timespec ta;
	for (Vertex *v = this->head(); v != nullptr; v = v->next.get()) {
		//clock_gettime(CLOCK_MONOTONIC, &ta);
		GRAPH_EXPLORE(v, dup.get(), &m, nullptr, ta);
	}
	//clock_gettime(CLOCK_MONOTONIC, &t1);
	//printf("duplicate: %ld\n", time_diff(t0, t1));
	//printf("find: %ld, insert: %ld, setinsert: %ld, loop: %ld, alloc: %ld, shift: %ld, call: %ld\n", dup->find_time, dup->insert_time, dup->setinsert_time, dup->loop_time, dup->alloc_time, dup->shift_time, dup->call_time);
	return dup;
}

Graph::Vertex * Graph::explore(Vertex *start, Graph *g, Map<Vertex *, Vertex *> *m, const Set<Vertex *> *valid, struct timespec ta) {
	//struct timespec tb;
	//clock_gettime(CLOCK_MONOTONIC, &tb);
	//g->call_time += time_diff(ta, tb);
	//struct timespec t0, t1;
	//clock_gettime(CLOCK_MONOTONIC, &t0);
	auto it = m->find(start);
	//clock_gettime(CLOCK_MONOTONIC, &t1);
	//g->find_time += time_diff(t0, t1);
	if (it != m->end()) {
		return it->second;
	}
	//clock_gettime(CLOCK_MONOTONIC, &t0);
	UniquePtr<Vertex> new_vertex = MAKE_UNIQUE<Vertex>(start->colour);
	Vertex* ret = new_vertex.get();
	//clock_gettime(CLOCK_MONOTONIC, &t1);
	//g->alloc_time += time_diff(t0, t1);
	start->colour->value = 0;
	//clock_gettime(CLOCK_MONOTONIC, &t0);
	m->insert({start, new_vertex.get()});
	//clock_gettime(CLOCK_MONOTONIC, &t1);
	//g->insert_time += time_diff(t0, t1);
	//struct timespec t2, t3;
	//clock_gettime(CLOCK_MONOTONIC, &t2);
	for (Vertex *v : start->neighbours) {
		//clock_gettime(CLOCK_MONOTONIC, &t3);
		//g->loop_time += time_diff(t2, t3);
		if (valid != nullptr) {
			//clock_gettime(CLOCK_MONOTONIC, &t0);
			auto found = valid->find(v);
			//clock_gettime(CLOCK_MONOTONIC, &t1);
			//g->setfind_time += time_diff(t0, t1);
			if (found == valid->end()) {
				//clock_gettime(CLOCK_MONOTONIC, &t2);
				continue;
			}
		}
		//clock_gettime(CLOCK_MONOTONIC, &ta);
		Vertex *neighbour = Graph::explore(v, g, m, valid, ta);
		//clock_gettime(CLOCK_MONOTONIC, &t0);
		new_vertex->neighbours.insert(neighbour);
		//clock_gettime(CLOCK_MONOTONIC, &t1);
		//g->setinsert_time += time_diff(t0, t1);
		//clock_gettime(CLOCK_MONOTONIC, &t2);
	}
	//clock_gettime(CLOCK_MONOTONIC, &t3);
	//g->loop_time += time_diff(t2, t3);
	//clock_gettime(CLOCK_MONOTONIC, &t0);
	g->shift(std::move(new_vertex));
	//clock_gettime(CLOCK_MONOTONIC, &t1);
	//g->shift_time += time_diff(t0, t1);
	return ret;
}

void Graph::explore_iterative(Vertex *start, Graph *g, Map<Vertex *, Vertex *> *m, const Set<Vertex *> *valid, struct timespec ta) {
	(void) ta;
	std::stack<std::pair<Vertex *, Vertex *>> vertex_stack;
	vertex_stack.emplace(start, nullptr);
	while (!vertex_stack.empty()) {
		Vertex* v;
		Vertex* sibling;
		std::tie(v, sibling) = vertex_stack.top();
		vertex_stack.pop();
		auto it = m->find(v);
		if (it != m->end()) {
			if (sibling != nullptr) {
				sibling->neighbours.insert(it->second);
			}
			continue;
		}
		UniquePtr<Vertex> new_vertex = MAKE_UNIQUE<Vertex>(v->colour);
		Vertex *ptr = new_vertex.get();
		v->colour->value = 0;
		m->insert({ v, ptr });

		for (Vertex *u : v->neighbours) {
			if (valid != nullptr) {
				auto found = valid->find(u);
				if (found == valid->end()) {
					continue;
				}
			}
			vertex_stack.emplace(u, ptr);
		}
		g->shift(std::move(new_vertex));
		if (sibling != nullptr) {
			sibling->neighbours.insert(ptr);
		}
	}
}

UniquePtr<Graph> Graph::Vertex::induce() {
	//struct timespec t0, t1;
	//clock_gettime(CLOCK_MONOTONIC, &t0);
	UniquePtr<Graph> induced = MAKE_UNIQUE<Graph>();
	Map<Vertex *, Vertex *> m;
	struct timespec ta;
	//clock_gettime(CLOCK_MONOTONIC, &ta);
	GRAPH_EXPLORE(this, induced.get(), &m, &this->neighbours, ta);
	//clock_gettime(CLOCK_MONOTONIC, &t1);
	//printf("induce: %ld\n", time_diff(t0, t1));
	//printf("find: %ld setfind: %ld insert: %ld, loop: %ld\n", induced->find_time, induced->setfind_time, induced->insert_time, induced->loop_time);
	return induced;
}

void Graph::social_credit(Vertex *bad) {
	bad->sudoku();
	this->size--;
	for (Vertex *v : bad->neighbours) {
		v->sudoku();
		this->size--;
	}
}

void Graph::Vertex::sudoku() {
	UniquePtr<Vertex> self = std::move(this->prev->next);
	this->prev->next = std::move(this->next);
	if (this->next != nullptr) {
		this->next->prev = this->prev;
	}
	for (Vertex *v : this->neighbours) {
		int x = v->neighbours.erase(this);
		assert(x == 1);
	}
}

Graph::Vertex* Graph::find_max_degree_vertex() {
	int max = 0;
	Vertex *ret = nullptr;
	for (Vertex *v = this->head(); v != nullptr; v = v->next.get()) {
		int d = v->degree();
		if (d > max) {
			ret = v;
			max = d;
		}
	}
	return ret;
}

double Graph::magic_f(int k, int n) {
	return std::ceil(std::pow(n, 1 - (1.0 / (k - 1))));
}

bool Graph::k_ge_log_n(int k, int n) {
	long x = 1;
	for (int i = 0; i < k; i++) {
		x *= 2;
	}
	return x >= n;
}

bool Graph::colour_2(int i, int j) {
	for (Vertex *v = this->head(); v != nullptr; v = v->next.get()) {
		if (v->colour->value != 0) {
			continue;
		}
		if (!Graph::colour_2_helper(v, i, j)) {
			return false;
		}
	}
	return true;
}

bool Graph::colour_2_helper(Vertex *v, int i, int j) {
	if (v->colour->value == j) {
		return false;
	}
	if (v->colour->value == 0) {
		v->colour->value = i;
		for (Vertex *u : v->neighbours) {
			if (!Graph::colour_2_helper(u, j, i)) {
				return false;
			}
		}
	}
	return true;
}

bool Graph::colour_2_helper_iterative(Vertex *start, int i, int j) {
	std::stack<std::tuple<Vertex *, int, int>> vertex_stack;
	vertex_stack.emplace(start, i, j);
	while (!vertex_stack.empty()) {
		Vertex *v;
		std::tie(v, i, j) = vertex_stack.top();
		vertex_stack.pop();
		if (v->colour->value == j) {
			return false;
		}

		if (v->colour->value == 0) {
			v->colour->value = i;
			for (Vertex *u : v->neighbours) {
				vertex_stack.emplace(u, j, i);
			}
		}
	}
	return true;
}

int Graph::colour_b(int k, int i) {
	//struct timespec t0, t1;
	//clock_gettime(CLOCK_MONOTONIC, &t0);
	if (k == 2) {
		if (this->colour_2(i, i + 1)) {
			//printf("B2: k = %d ret = 2\n", k);
			return 2;
		}
		//printf("B2: k = %d ret = 0\n", k);
		return 0;
	}
	int n = this->size;
	if (Graph::k_ge_log_n(k, n)) {
		int j = 0;
		for (Vertex *v = this->head(); v != nullptr; v = v->next.get()) {
			v->colour->value = i + j;
			j++;
		}
		//printf("Bn: k = %d ret = %d\n", k, n);
		return n;
	}
	while (true) {
		Vertex *v = this->find_max_degree_vertex();
		if (v->degree() < Graph::magic_f(k, n)) {
			//printf("- breaking k = %d degree = %d magic = %f\n", k, v->degree(), Graph::magic_f(k, n));
			break;
		}
		/*
		if (v->degree() < (k * k)) {
			break;
		}
		*/
		UniquePtr<Graph> h = v->induce();
		int j = h->colour_b(k - 1, i);
		if (j == 0) {
			//printf("B: k = %d ret = 0\n", k);
			return 0;
		}
		i += j;
		v->colour->value = i;
		this->social_credit(v);
	}
	int max_degree = 0;
	int max_colour = 0;
	int edge_count = 0;
	for (Vertex *v = this->head(); v != nullptr; v = v->next.get()) {
		Set<int> seen;
		for (Vertex *e : v->neighbours) {
			seen.insert(e->colour->value);
			edge_count++;
		}
		if (max_degree < v->degree()) {
			max_degree = v->degree();
		}
		for (int j = i; true; j++) {
			if (seen.find(j) == seen.end()) {
				v->colour->value = j;
				if (max_colour < j) {
					max_colour = j;
				}
				break;
			}
		}
	}
	//printf("vertices: %d edges: %d\n", this->size, edge_count);
	assert(max_colour < max_degree + i + 1);

	int ret = max_colour - i + 1;
	double bound = 2 * k * Graph::magic_f(k, n);
	//printf("Bend: k = %d ret = %d\n", k, ret);
	//clock_gettime(CLOCK_MONOTONIC, &t1);
	//printf("colour_b: %ld\n", time_diff(t0, t1));
	return ret > bound ? 0 : ret;
}

int Graph::colour_c() {
	int i = 1;
	while (this->duplicate()->colour_b(1 << i, 1) == 0) {
		i++;
	}
	//printf("C: i = %d\n", i);

	int l = (1 << (i - 1)) + 1;
	int r = 1 << i;
	while (l < r) {
		int m = (l + r) / 2;
		if (this->duplicate()->colour_b(m, 1) == 0) {
			l = m + 1;
		} else {
			r = m;
		}
	}
	int k = this->duplicate()->colour_b(l, 1);
	assert(k != 0);

	return k;
}

bool Graph::verify_colouring() {
	for (Vertex *v = this->head(); v != nullptr; v = v->next.get()) {
		if (v->colour->value == 0) {
			return false;
		}
		for (Vertex *u : v->neighbours) {
			if (v->colour->value == u->colour->value) {
				return false;
			}
		}
	}
	return true;
}

void Graph::explore_dump(Vertex *start, Map<Vertex *, Vertex *> *m, std::string prefix) {
	std::stack<std::pair<Vertex *, Vertex *>> vertex_stack;
	vertex_stack.emplace(start, nullptr);
	uintptr_t last = 0;
	while (!vertex_stack.empty()) {
		Vertex* v;
		Vertex* sibling;
		std::tie(v, sibling) = vertex_stack.top();
		vertex_stack.pop();
		auto it = m->find(v);
		if (it != m->end()) {
			Vertex** z = &(it->second);
			uintptr_t a = reinterpret_cast<uintptr_t>(z);
			if (last != 0) {
				uintptr_t diff = (a >= last) ? a - last : last - a;
				printf("diff4 %s: %lu\n", prefix.c_str(), diff);
			}
			last = a;
			if (sibling != nullptr) {
				sibling->neighbours.insert(it->second);
			}
			continue;
		}
		Vertex *new_vertex = new Vertex(v->colour);
		Vertex *ptr = new_vertex;
		v->colour->value = 0;
		m->insert({ v, ptr });
		Vertex** z = &((*m)[v]);

		uintptr_t a = reinterpret_cast<uintptr_t>(z);
		if (last != 0) {
			uintptr_t diff = (a >= last) ? a - last : last - a;
			printf("diff3 %s: %lu\n", prefix.c_str(), diff);
		}
		last = a;

		uintptr_t l2 = 0;
		for (Vertex* const& u : v->neighbours) {
			uintptr_t b = reinterpret_cast<uintptr_t>(&u);
			if (l2 != 0) {
				uintptr_t diff = (b >= l2) ? b - l2 : l2 - b;
				printf("diff5 %s: %lu, %lu, %lu\n", prefix.c_str(), diff, b, l2);
			}
			l2 = b;
			vertex_stack.emplace(u, ptr);
		}
		if (sibling != nullptr) {
			sibling->neighbours.insert(ptr);
		}
	}
}

void Graph::dump_locality2(Graph *g, std::string prefix) {
	Map<Vertex *, Vertex *> m;

	for (Vertex *v = g->head(); v != nullptr; v = v->next.get()) {
		Graph::explore_dump(v, &m, prefix);
	}
}

UniquePtr<Graph> Graph::from_file(const char *fname) {
	std::ifstream f(fname);
	UniquePtr<Graph> g = MAKE_UNIQUE<Graph>();
	Map<int, Vertex*> m;
	while (true) {
		std::string line;
		if (!std::getline(f, line)) {
			break;
		}
		if (line[0] == '#') {
			continue;
		}
		std::istringstream ss(line);
		int x;
		int y;
		ss >> x;
		ss >> y;
		//std::cout << "x " << x << ", y " << y << std::endl;
		Vertex* vx = m[x];
		Vertex* vy = m[y];
		if (vx == nullptr) {
			UniquePtr<Vertex> v = MAKE_UNIQUE<Vertex>(MAKE_SHARED<Colour>());
			vx = v.get();
			m[x] = vx;
			g->shift(std::move(v));
		}
		if (vy == nullptr) {
			UniquePtr<Vertex> v = MAKE_UNIQUE<Vertex>(MAKE_SHARED<Colour>());
			vy = v.get();
			m[y] = vy;
			g->shift(std::move(v));
		}
		vx->neighbours.insert(vy);
		vy->neighbours.insert(vx);
	}
	return g;
}

int main(int argc, char *argv[]) {
#if defined(GRAPH_O2)
	printf("[config] -O2\n");
#elif defined(GRAPH_O3)
	printf("[config] -O3\n");
#else
	printf("[config] badness.\n");
	return 1;
#endif

#if defined(GRAPH_ITERATIVE)
	printf("[config] iterative.\n");
#elif defined(GRAPH_RECURSIVE)
	struct rlimit rlim;
	getrlimit(RLIMIT_STACK, &rlim);
	//printf("soft: %lu hard: %lu\n", rlim.rlim_cur, rlim.rlim_max);
	rlim.rlim_cur = 128 * 1024 * 1024;
	rlim.rlim_max = 128 * 1024 * 1024;
	setrlimit(RLIMIT_STACK, &rlim);
	getrlimit(RLIMIT_STACK, &rlim);
	//printf("soft: %lu hard: %lu\n", rlim.rlim_cur, rlim.rlim_max);
	printf("[config] recursive.\n");
#else
	printf("[config] badness.\n");
	return 1;
#endif

#if defined(GRAPH_STL_UNORDERED)
	printf("[config] stl unordered.\n");
#elif defined(GRAPH_STL_ORDERED)
	printf("[config] stl ordered.\n");
#elif defined(GRAPH_ABSL_NODE)
	printf("[config] absl node.\n");
#elif defined(GRAPH_ABSL_FLAT)
	printf("[config] absl flat.\n");
#else
	printf("[config] badness.\n");
	return 1;
#endif

	if (argc <= 1) {
		printf("[usage] ./graph <file>\n");
		return 1;
	}

	std::ios_base::sync_with_stdio(false);
	//struct timespec t0, t1, t2, t3;
	//clock_gettime(CLOCK_MONOTONIC, &t0);
	UniquePtr<Graph> g = Graph::from_file(argv[1]);
	//Graph::dump_locality2(g.get(), "start");
	//clock_gettime(CLOCK_MONOTONIC, &t1);
	int k = g->colour_c();
	printf("k: %d\n", k);
	//clock_gettime(CLOCK_MONOTONIC, &t2);
	assert(g->verify_colouring());
	//clock_gettime(CLOCK_MONOTONIC, &t3);
	//printf("from_file: %ld colour_c: %ld verify: %ld\n", time_diff(t0, t1), time_diff(t1, t2), time_diff(t2, t3));
}
