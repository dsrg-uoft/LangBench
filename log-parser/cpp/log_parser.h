#ifndef LOG_PARSER_H
#define LOG_PARSER_H

#include <string>
#include <vector>
#include <mutex>
#include <functional>
#include <memory>

//#define USE_DUMMY_PTR 1
//#define USE_MEMCPY 1

#if defined(USE_DUMMY_PTR)
template <typename T> class DummyPtr;
template <typename T> using UniquePtr = DummyPtr<T>;
#define MAKE_UNIQUE make_dummy
#else
template <typename T> using UniquePtr = std::unique_ptr<T>;
#define MAKE_UNIQUE std::make_unique
#endif

#if defined(LP_STL_UNORDERED)
#include <unordered_map>
#include <unordered_set>
template <typename K, typename V> using Map = std::unordered_map<K, V>;
template <typename T> using Set = std::unordered_set<T>;
#elif defined(LP_STL_ORDERED)
#include <map>
#include <set>
template <typename K, typename V> using Map = std::map<K, V>;
template <typename T> using Set = std::set<T>;
#elif defined(LP_ABSL_NODE)
#include "absl/container/node_hash_map.h"
#include "absl/container/node_hash_set.h"
template <typename K, typename V> using Map = absl::node_hash_map<K, V>;
template <typename T> using Set = absl::node_hash_set<T>;
#elif defined(LP_ABSL_FLAT)
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
	T* operator->() const {
		return this->ptr;
	}
	T& operator*() const {
		return *(this->ptr);
	}
	friend bool operator!=(DummyPtr const& a, std::nullptr_t b) {
		return a.ptr != b;
	}
private:
	T* ptr;
};

template <typename T, typename... Args> static inline UniquePtr<T> make_dummy(Args&&... args) {
	/*
	void* p = heap + heap_pos;
	heap_pos += sizeof(T);
	return DummyPtr(new (p) T(std::forward<Args>(args)...));
	*/
	return DummyPtr(new T(std::forward<Args>(args)...));
}

class LogParser {
public:
	struct SearchResult {
		size_t file;
		size_t line_number;
		std::string line;

		SearchResult(size_t file, size_t line_number, std::string line) : file(file), line_number(line_number), line(line) {
			return;
		}
	};

	std::vector<std::string> const files;

	LogParser(std::vector<std::string>& files) : files(std::move(files)) {
		this->file_tables.resize(this->files.size());
	}
	void index(size_t threads);
	void search(size_t threads, std::string pattern, std::vector<UniquePtr<SearchResult>>& results);
	template <bool spooky> void search_regex(size_t threads, std::string pattern, std::vector<UniquePtr<SearchResult>>& results);

	void process_file(size_t i, size_t worker);
	template <bool spooky> void search_regex_file(size_t i, size_t worker, std::mutex* lock, std::string pattern, std::vector<UniquePtr<SearchResult>>* results);

private:
	struct Line {
		size_t format_id;
		std::vector<size_t> variables;
	};
	enum class TokenType {
		PLAIN,
		VARIABLE,
		WILDCARD,
		PLAIN_WILDCARD,
		VARIABLE_WILDCARD,
	};
	struct PatternVariables {
		size_t format_pos;
		size_t pattern_part;
	};
	/*
	3 -> INFO abcdef 0 1
	[ 100, 101 ]
		[ (0, 1) ]
		[ (0, 0), (1, 1) ]
	0   1    2
	abc *def ghi0
		0    1 -> [ 4, 5, 6]
		[1, 2, 3]
	*/

	std::mutex lock;
	Map<std::string, size_t> format_ids;
	std::vector<std::string> formats;
	Map<std::string, size_t> variable_ids;
	std::vector<std::string> variables;
	std::vector<std::vector<Line>> file_tables;

	//template <typename... Args> void do_parallel(size_t threads, std::function<void(LogParser* log_parser, size_t id, size_t start, size_t end, Args... args)> fn, Args... args);
	template <typename... Args> void do_parallel(size_t threads, void (*fn)(LogParser* log_parser, size_t id, size_t start, size_t end, Args... args), Args... args);
	template <bool spooky> void search_regex_internal(size_t threads, std::string pattern, std::vector<UniquePtr<SearchResult>>& results);
	std::string rebuild_line(Line& line);
	void search_file(size_t i, size_t worker, std::mutex* lock, std::string pattern, std::vector<UniquePtr<SearchResult>>* results, Map<size_t, std::vector<std::vector<PatternVariables>>>* valid_formats, std::vector<Set<size_t>>* valid_variables);

	static void format_matches_pattern(std::vector<std::string>& format, std::vector<std::string>& pattern_parts, std::vector<TokenType>& pattern_types, size_t pos, size_t part, bool prev_is_wildcard, std::vector<std::vector<PatternVariables>>& results, std::vector<PatternVariables>& cur);

	static bool string_matches_wildcard(bool front_is_wildcard, std::string const& str, std::string const& pattern);
	static void search_worker(LogParser* log_parser, size_t id, size_t start, size_t end, std::mutex* lock, std::string pattern, std::vector<UniquePtr<LogParser::SearchResult>>* results, Map<size_t, std::vector<std::vector<PatternVariables>>>* valid_formats, std::vector<Set<size_t>>* valid_variables);
};

#endif // LOG_PARSER_H
