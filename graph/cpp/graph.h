#include <cmath>
#include <memory>
/*
#include <tsl/hopscotch_map.h>
#include <tsl/hopscotch_set.h>
#include <tsl/robin_map.h>
#include <tsl/robin_set.h>
*/

#if defined(GRAPH_ITERATIVE)
#define GRAPH_EXPLORE Graph::explore_iterative
#define COLOUR_2_HELPER Graph::colour_2_helper_iterative
#elif defined(GRAPH_RECURSIVE)
#define GRAPH_EXPLORE Graph::explore
#define COLOUR_2_HELPER Graph::colour_2_helper
#endif

#if defined(GRAPH_STL_UNORDERED)
#include <unordered_map>
#include <unordered_set>
template <typename K, typename V> using Map = std::unordered_map<K, V>;
template <typename T> using Set = std::unordered_set<T>;
#elif defined(GRAPH_STL_ORDERED)
#include <map>
#include <set>
template <typename K, typename V> using Map = std::map<K, V>;
template <typename T> using Set = std::set<T>;
#elif defined(GRAPH_ABSL_NODE)
#include "absl/container/node_hash_map.h"
#include "absl/container/node_hash_set.h"
template <typename K, typename V> using Map = absl::node_hash_map<K, V>;
template <typename T> using Set = absl::node_hash_set<T>;
#elif defined(GRAPH_ABSL_FLAT)
#include "absl/container/flat_hash_map.h"
#include "absl/container/flat_hash_set.h"
template <typename K, typename V> using Map = absl::flat_hash_map<K, V>;
template <typename T> using Set = absl::flat_hash_set<T>;
#endif

template <typename T> class DummyPtr {
public:
	DummyPtr() : DummyPtr(nullptr) {
		return;
	}
	DummyPtr(T* p) : ptr(p) {
		return;
	}
	T* get() {
		return this->ptr;
	}
	T* operator->() {
		return this->ptr;
	}
	friend bool operator!=(DummyPtr const& a, std::nullptr_t b) {
		return a.ptr != b;
	}
private:
	T* ptr;
};
//template <typename K, typename V> using Map = tsl::hopscotch_map<K, V>;
//template <typename T> using Set = tsl::hopscotch_set<T>;
//template <typename K, typename V> using Map = tsl::robin_pg_map<K, V>;
//template <typename T> using Set = tsl::robin_pg_set<T>;

#define MAKE_UNIQUE std::make_unique
#define MAKE_SHARED std::make_shared
template <typename T> using UniquePtr = std::unique_ptr<T>;
template <typename T> using SharedPtr = std::shared_ptr<T>;
//template <typename T> using UniquePtr = DummyPtr<T>;
//template <typename T> using SharedPtr = DummyPtr<T>;

class Graph {
	class Colour {
	public:
		int value;
	};

	class Vertex {
	public:
		UniquePtr<Vertex> next;
		Vertex *prev;
		SharedPtr<Colour> colour;
		Set<Vertex *> neighbours;
		Vertex(SharedPtr<Colour> c) {
			this->colour = c;
			this->next = nullptr;
			this->prev = nullptr;
		}
		int degree() {
			return this->neighbours.size();
		}
		void sudoku();
		UniquePtr<Graph> induce();
	};

	UniquePtr<Vertex> dummy;
	static Vertex * explore(Vertex *start, Graph *g, Map<Vertex *, Vertex *> *m, const Set<Vertex *> *valid, struct timespec ta);
	static void explore_iterative(Vertex *start, Graph *g, Map<Vertex *, Vertex *> *m, const Set<Vertex *> *valid, struct timespec ta);
	long find_time;
	long setfind_time;
	long insert_time;
	long setinsert_time;
	long loop_time;
	long alloc_time;
	long shift_time;
	long call_time;
public:
	int size;
	Graph() : dummy(MAKE_UNIQUE<Vertex>(nullptr)), find_time(0), setfind_time(0), insert_time(0), setinsert_time(0), loop_time(0), alloc_time(0), shift_time(0), call_time(0), size(0) {
		return;
	}
	~Graph();
	Graph(Graph const&) = delete;
	Graph(Graph const&&) = delete;
	Graph& operator=(Graph const&) = delete;
	Graph& operator=(Graph const&&) = delete;
	Vertex* head() {
		return this->dummy->next.get();
	}
	void shift(UniquePtr<Vertex> v);
	UniquePtr<Graph> duplicate();
	void social_credit(Vertex *bad);

	static UniquePtr<Graph> from_file(const char *fname);
	bool colour_2(int i, int j);
	int colour_b(int k, int i);
	int colour_c();
	bool verify_colouring();
	void na();
	static void dump_locality2(Graph *g, std::string prefix);

private:
	static double magic_f(int k, int n);
	static bool k_ge_log_n(int k, int n);
	static bool colour_2_helper(Vertex *v, int i, int j);
	static bool colour_2_helper_iterative(Vertex *v, int i, int j);
	Vertex* find_max_degree_vertex();
	static void explore_dump(Vertex *start, Map<Vertex *, Vertex *> *m, std::string prefix);
};
